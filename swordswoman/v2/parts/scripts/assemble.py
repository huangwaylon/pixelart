# assemble.py RAW_DIR OUT_DIR [A_PARTS_DIR] [REST.glb]
# Fit generated parts into the proportions of the full 2mv mesh: each part's bbox is scaled per axis and moved onto the
# bbox of the matching approach-A part (A parts are cut from the 2mv mesh). Mirrors arm/leg for the other side.
# Decimates (pymeshlab, 20k faces/part), colours = nearest vertex of the 2mv rest_mat.glb (palette IDs).
import sys, os, glob, numpy as np, trimesh, pymeshlab
from scipy.spatial import cKDTree
raw, od = sys.argv[1:3]
ad = sys.argv[3] if len(sys.argv) > 3 else 'A/parts'
rest = sys.argv[4] if len(sys.argv) > 4 else '../hy3d/best/rest_mat.glb'
os.makedirs(od, exist_ok=True)
A = {os.path.basename(f)[:-4]: trimesh.load(f, force='mesh') for f in glob.glob(f'{ad}/*.glb')}
R = trimesh.load(rest, force='mesh'); RC = R.visual.vertex_colors; RID = np.load(rest[:-4] + '_ids.npy'); SKIN = RC[RID == 0][0]; tree = cKDTree(R.vertices)
def ub(*names):
    b = np.array([A[n].bounds for n in names]); return np.array([b[:, 0].min(0), b[:, 1].max(0)])
leg_b = ub('leg_R', 'boot_R'); leg_b[1, 1] = -0.40  # hip top (A thigh capsule goes higher, hidden under the skirt)
T = {'head': ('head', ub('head', 'bow', 'bun')), 'torso': ('torso', ub('torso')), 'skirt': ('skirt', ub('skirt')),
     'leg_R': ('leg', leg_b), 'arm_R': ('arm', ub('arm_R'))}
def dec(m, n=20000):
    ms = pymeshlab.MeshSet(); ms.add_mesh(pymeshlab.Mesh(m.vertices, m.faces))
    ms.meshing_decimation_quadric_edge_collapse(targetfacenum=n, preservenormal=True, qualitythr=0.5)
    k = ms.current_mesh(); return trimesh.Trimesh(k.vertex_matrix(), k.face_matrix())
out = {}
for name, (src, tb) in T.items():
    f = f'{raw}/{src}.glb'
    if not os.path.exists(f): print('missing', f); continue
    m = trimesh.load(f, force='mesh'); m = max(m.split(only_watertight=False), key=lambda c: len(c.faces))
    if not os.environ.get('KEEPCOL'): m = dec(m)
    else: m.visual.vertex_colors  # keep projected colours
    b = m.bounds; s = (tb[1] - tb[0]) / (b[1] - b[0])
    m.vertices = (m.vertices - b[0]) * s + tb[0]
    print(name, 'scale xyz', s.round(3))
    out[name] = m
for n in ('leg_R', 'arm_R'):
    if n in out:
        mm = out[n].copy(); mm.vertices[:, 0] *= -1; mm.invert(); out[n[:-1] + 'L'] = mm
for n, m in out.items():
    _, j = tree.query(m.vertices); col = RC[j].copy()
    if os.environ.get('KEEPCOL'):
        rc = col; col = m.visual.vertex_colors.copy()
        if n == 'head':  # projected skin/eyes only where the 2mv rest mesh agrees it is face -> removes side streaks
            sk = (np.abs(col[:, :3].astype(int) - SKIN[:3].astype(int)).sum(1) < 6)
            eye = (col[:, 2].astype(int) > col[:, 0].astype(int) + 20)
            bad = (sk | eye) & ~np.isin(RID[j], [0, 5]) & (m.vertex_normals[:, 2] < 0.6); col[bad] = RC[RID == 1][0]
    if n.startswith('leg'): col[m.vertices[:, 1] > -0.52] = SKIN  # thigh hidden under the skirt
    m.visual = trimesh.visual.ColorVisuals(m, vertex_colors=col)
    m.export(f'{od}/{n}.glb')
print('parts', sorted(out))
