# fix_ab4.py IN_DIR(AB3/parts) OUT_DIR : hybrid v4 = critic fixes + round-chibi-skull rule (lead panel)
# head: domed crown + temple bulge (blend hair toward a superellipsoid-free ellipsoid in the upper head, extra x bulge at the
#       temples), soft tapered chin (skin below the eyes narrows toward the centre), bangs raised ~1.5 px (front hair hem
#       strip flattened onto the forehead and painted skin).
# bow: thicker lobes (depth ~40% of lobe width); bun lifted/back so it peeks above the bow in front.
# skirt +2.5% radial; legs 10% shorter (scaled about the sole) + whole upper body dropped by the same amount; chunkier boots.
import sys, os, shutil, glob, numpy as np, trimesh
ind, od = sys.argv[1:3]; os.makedirs(od, exist_ok=True)
for f in glob.glob(f'{ind}/*.glb'): shutil.copy(f, od)
L = lambda n: trimesh.load(f'{od}/{n}.glb', force='mesh')
def save(n, m): m.export(f'{od}/{n}.glb')
def ss(a, b, x): t = np.clip((x - a) / (b - a), 0, 1); return t * t * (3 - 2 * t)
PX = 0.04  # ~1 sprite pixel at 48 px (head ~0.83 units = 20 px)
# ---------- head ----------
h = L('head'); v = h.vertices.copy(); col = h.visual.vertex_colors.copy(); c3 = col[:, :3].astype(int)
HAIR, SKIN = col[(np.abs(c3 - [12, 8, 9]).sum(1) < 6)][0], col[(np.abs(c3 - [239, 179, 138]).sum(1) < 30)][0]
skin = np.abs(c3 - [239, 179, 138]).sum(1) < 30; eye = c3[:, 2] > c3[:, 0] + 20; face = skin | eye
lo, hi = v.min(0), v.max(0); ctr = (lo + hi) / 2; ctr[1] = lo[1] + 0.47 * (hi[1] - lo[1]); rad = (hi - lo) / 2
d = (v - ctr) / rad; n = np.linalg.norm(d, axis=1)
w = 0.75 * ss(0.50, 0.80, v[:, 1]) * ~face          # crown: hair above the brow blends toward the ellipsoid -> dome, no box corners
tgt = ctr + d / n[:, None] * rad * 1.02
v = v + w[:, None] * (tgt - v)
tb = np.exp(-((v[:, 1] - 0.52) / 0.12) ** 2) * ~face  # temple bulge: hair at temple height pushed out sideways
v[:, 0] += np.sign(v[:, 0] - ctr[0]) * 0.035 * tb * (np.abs(v[:, 0] - ctr[0]) > 0.15)
v[face & (v[:, 2] > 0), 2] += 0.06                 # face plane forward so the 30deg SE camera sees past the bang overhang
ch = skin & (v[:, 1] < 0.30)                          # soft tapered chin
k = 1 - 0.22 * ss(0.30, 0.11, v[:, 1]); v[ch, 0] = ctr[0] + (v[ch, 0] - ctr[0]) * k[ch]
v[ch, 1] += 0.02 * ss(0.30, 0.11, v[ch, 1])           # chin bottom a touch rounder/higher
hem = skin[:].copy(); fy = v[skin & (np.abs(v[:, 0]) < 0.12), 1].max()   # bangs hem height
fz = np.percentile(v[skin & (v[:, 1] > fy - 0.06) & (np.abs(v[:, 0]) < 0.12), 2], 60)
band = ~face & (v[:, 1] > fy - 0.01) & (v[:, 1] < fy + 1.0 * PX) & (v[:, 2] > fz - 0.06) & (np.abs(v[:, 0]) < 0.25) & (h.vertex_normals[:, 2] > 0.2)
v[band, 2] = np.minimum(v[band, 2], fz); col[band] = SKIN   # raise the fringe ~1.5 px: strip becomes forehead
ov = ~face & ~band & (v[:, 1] > fy) & (v[:, 1] < fy + 0.28) & (v[:, 2] > fz) & (h.vertex_normals[:, 2] > -0.2)  # bang overhang -> 40%
wv = ss(fy + 0.28, fy + 0.12, v[:, 1]); v[ov, 2] = v[ov, 2] - (1 - 0.4) * wv[ov] * (v[ov, 2] - fz)
sl = ~face & (v[:, 1] < fy + 0.02) & (v[:, 1] > 0.10) & (v[:, 2] > 0.05)   # side locks framing the face: pull back so the 3/4 SE face reads
wl = ss(0.10, 0.24, np.abs(v[:, 0] - ctr[0])) * ss(0.05, 0.25, v[:, 2])
v[sl, 2] -= 0.06 * wl[sl]
h.vertices = v; h.visual = trimesh.visual.ColorVisuals(h, vertex_colors=col); trimesh.smoothing.filter_taubin(h, iterations=3)
save('head', h); print('head: fringe y', round(fy, 3), '-> +', round(1.0 * PX, 3), 'band verts', int(band.sum()), 'top', round(h.bounds[1][1], 3))
# ---------- bow + bun ----------
R = trimesh.load('../hy3d/best/rest_mat.glb', force='mesh'); RC = R.visual.vertex_colors; RID = np.load('../hy3d/best/rest_mat_ids.npy')
BOW = RC[RID == 6][0]
bb = trimesh.load('A/parts/bow.glb', force='mesh').bounds
W = bb[1][0] - bb[0][0]; cx = (bb[0][0] + bb[1][0]) / 2; cy = bb[0][1] + 0.66 * (bb[1][1] - bb[0][1]); cz = (bb[0][2] + bb[1][2]) / 2 + 0.03
parts = []
for s in (-1, 1):
    e = trimesh.creation.icosphere(3, radius=1.0); u = e.vertices; t = (u[:, 0] * s + 1) / 2
    u[:, 1] *= 0.45 + 0.55 * t; u[:, 2] *= 0.75 + 0.25 * t
    u *= [W * 0.27, (bb[1][1] - bb[0][1]) * 0.48, 0.4 * W * 0.27 * 2 / 2 * 1.0 + 0.04]   # depth ~40% of lobe width
    e.vertices = u; e.apply_transform(trimesh.transformations.rotation_matrix(np.radians(12 * s), [0, 0, 1]))
    e.apply_translation([cx + s * W * 0.25, cy, cz]); parts.append(e)
kn = trimesh.creation.icosphere(3, radius=0.08); kn.vertices *= [1.0, 1.1, 1.1]; kn.apply_translation([cx, cy - 0.01, cz + 0.03]); parts.append(kn)
bow = trimesh.util.concatenate(parts); bow.visual = trimesh.visual.ColorVisuals(bow, vertex_colors=np.tile(BOW, (len(bow.vertices), 1)))
save('bow', bow)
bun = L('bun'); bc = bun.vertices.mean(0); r = (bun.bounds[1][0] - bun.bounds[0][0]) / 2
bun.vertices = bc + (bun.vertices - bc) * (0.105 / r); r = 0.105   # bun 0.25 H across
bow.apply_translation([0, -0.06, 0]); save('bow', bow)                       # bow sits ON the crown (front/top of the bun)
bun.apply_translation([0, (bow.bounds[1][1] + 0.06 - r) - bc[1], -0.20 - bc[2]])  # bun peeks ~0.06 above the bow, embedded in the crown
save('bun', bun); print('bow', bow.bounds.round(3).tolist(), 'bun top', round(bun.bounds[1][1], 3), 'z', round(bun.vertices.mean(0)[2], 3))
# ---------- legs / boots ----------
DROP = 0.0
for sd in ('L', 'R'):
    m = L('leg_' + sd); v = m.vertices.copy(); sole = v[:, 1].min(); top = v[:, 1].max()
    DROP = 0.10 * (top - sole)
    v[:, 1] = sole + (v[:, 1] - sole) * 0.90
    c3 = m.visual.vertex_colors[:, :3].astype(int); dark = c3.sum(1) < 60
    bt = np.percentile(v[dark, 1], 95)
    wb = ss(bt + 0.07, bt - 0.01, v[:, 1])  # taller, chunkier boot shaft
    axc = v[dark][:, [0, 2]].mean(0)
    v[:, [0, 2]] = axc + (v[:, [0, 2]] - axc) * (1 + 0.22 * wb)[:, None]
    v[:, 1] = np.where(wb > 0, v[:, 1] + 0.012 * wb, v[:, 1])
    m.vertices = v; save('leg_' + sd, m)
print('legs shortened by', round(DROP, 3))
for nme in ('head', 'bow', 'bun', 'torso', 'skirt', 'arm_L', 'arm_R'):
    m = L(nme); m.apply_translation([0, -DROP, 0])
    if nme == 'skirt':
        c = m.vertices.mean(0); m.vertices[:, [0, 2]] = c[[0, 2]] + (m.vertices[:, [0, 2]] - c[[0, 2]]) * 1.025
    save(nme, m)
print('done', sorted(os.listdir(od)))
