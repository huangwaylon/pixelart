# split_a.py IN.glb IDS.npy SKEL.txt OUTDIR [pitch]
# Approach A: split the watertight 2mv rest mesh into closed rigid parts.
# Voxelise the solid, assign each part a region of space (planes + bone capsules + surface labels),
# marching-cubes each part separately (so every part is closed; cut faces become caps), copy vertex colours from
# the nearest original surface vertex. Legs get a hidden thigh extension up to the hip so they can swing under the skirt.
# glb frame: Y up, faces +Z, her left = +X.
import sys, os, json, numpy as np, trimesh
from scipy import ndimage
from scipy.spatial import cKDTree
from skimage import measure
src, idp, skp, od = sys.argv[1:5]
P = float(sys.argv[5]) if len(sys.argv) > 5 else 0.007
os.makedirs(od, exist_ok=True)
m = trimesh.load(src, force='mesh'); L = np.load(idp); V = m.vertices; C = m.visual.vertex_colors[:, :3]
sk = np.loadtxt(skp)
vox = m.voxelized(P).fill()
occ = vox.matrix.copy(); T = vox.transform
pad = 3; occ = np.pad(occ, pad)
idx = np.argwhere(occ)
pts = trimesh.transform_points(idx - pad, T)
x, y, z = pts.T
tree = cKDTree(V)
_, nn = tree.query(pts, k=8)
lab = np.array([np.bincount(L[r], minlength=7).argmax() for r in nn])
NECK, OBI_B, HEM, BOOT = 0.105, -0.245, -0.505, -0.82
def segdist(p, a, b):
    ab = b - a; t = np.clip(((p - a) @ ab) / (ab @ ab), 0, 1); return np.linalg.norm(p - (a + t[:, None] * ab), axis=1), t
parts = {}
head = y > NECK
bow = head & (lab == 6) & (y > 0.66)
bun_c = np.array([0.0, 0.89, -0.33])
bun = head & ~bow & (np.linalg.norm((pts - bun_c) * [1, 1, 1], axis=1) < 0.15) & (z < -0.22) & (y > 0.76)
parts['bow'] = bow; parts['bun'] = bun; parts['head'] = head & ~bow & ~bun
# arms: shoulder joint -> hand tip; cut plane perpendicular to the upper-arm direction at the shoulder
arm = {}
for side, (s0, s1) in (('R', (7, 9)), ('L', (26, 28))):  # her right = -X
    sh = sk[s0, :3]; tip = sk[s1, 3:] + 0.6 * (sk[s1, 3:] - sk[s1, :3])
    d, t = segdist(pts, sh, tip)
    u = (sk[s0, 3:] - sh); u /= np.linalg.norm(u)
    side_ok = (x < -0.05) if side == 'R' else (x > 0.05)
    a = side_ok & (y <= NECK) & (y > HEM - 0.02) & (d < 0.17) & (((pts - sh) @ u) > 0.02) & (np.abs(x) > 0.19)
    arm[side] = a; parts['arm_' + side] = a
anyarm = arm['R'] | arm['L']
parts['torso'] = (y <= NECK) & (y > OBI_B) & ~anyarm
parts['skirt'] = (y <= OBI_B) & (y > HEM - 0.03) & ~anyarm
# legs + boots split by side; thigh extension capsule up to the hip
legsz = (y <= HEM) & (y > BOOT)
for side, sgn in (('R', -1), ('L', 1)):
    s = (x * sgn > 0)
    lv = pts[legsz & s & (y < HEM - 0.03) & (y > HEM - 0.12)]
    c = lv.mean(0); r = np.percentile(np.hypot(lv[:, 0] - c[0], lv[:, 2] - c[2]), 90)
    hip = np.array([c[0], -0.40, c[2]]); top = np.array([c[0], HEM - 0.05, c[2]])
    d, _ = segdist(pts, hip, top)
    parts['leg_' + side] = (legsz & s) | ((d < r) & (y < -0.38))
    parts['boot_' + side] = (y <= BOOT + 0.01) & s
    print('leg', side, c.round(3), 'r', round(r, 3))
# extra thigh voxels may lie outside the original solid: allocate them in a padded grid
allpts = pts; shape = occ.shape
# rebuild thigh capsule over the full grid (not only inside voxels)
gi = np.argwhere(np.ones(shape, bool)); gp = trimesh.transform_points(gi - pad, T)
info = {}
src_tree = tree
for name, msk in parts.items():
    g = np.zeros(shape, np.float32); g[tuple(idx[msk].T)] = 1
    if name.startswith('leg_'):
        sgn = -1 if name.endswith('R') else 1
        lv = pts[legsz & (x * sgn > 0) & (y < HEM - 0.03) & (y > HEM - 0.12)]; c = lv.mean(0)
        r = np.percentile(np.hypot(lv[:, 0] - c[0], lv[:, 2] - c[2]), 90)
        d, _ = segdist(gp, np.array([c[0], -0.40, c[2]]), np.array([c[0], HEM - 0.05, c[2]]))
        g.reshape(-1)[(d < r)] = 1
    g = ndimage.binary_opening(g > 0.5, iterations=1).astype(np.float32)
    lbl, n = ndimage.label(g > 0.5)
    if n > 1:  # keep the largest component
        sz = ndimage.sum(np.ones_like(lbl), lbl, range(1, n + 1)); g = (lbl == (np.argmax(sz) + 1)).astype(np.float32)
    gs = ndimage.gaussian_filter(g, 1.0)
    vv, ff, _, _ = measure.marching_cubes(gs, 0.5)
    vw = trimesh.transform_points(vv - pad, T)
    pm = trimesh.Trimesh(vw, ff[:, ::-1], process=True)
    if pm.volume < 0: pm.invert()
    trimesh.smoothing.filter_taubin(pm, iterations=6)
    _, j = src_tree.query(pm.vertices)
    col = C[j].copy()
    if name.startswith('leg_'):  # thigh extension/caps are skin
        col[:] = C[L == 0][0]
    if name.startswith('boot_'): col[:] = C[L == 4][0]
    pm.visual = trimesh.visual.ColorVisuals(pm, vertex_colors=np.c_[col, np.full(len(col), 255)].astype(np.uint8))
    pm.export(f'{od}/{name}.glb')
    info[name] = dict(faces=len(pm.faces), watertight=bool(pm.is_watertight), comps=int(n), bounds=pm.bounds.round(3).tolist())
    print(name, info[name])
json.dump(info, open(f'{od}/parts.json', 'w'), indent=1)
