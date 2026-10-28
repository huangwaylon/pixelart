# fit_c.py IN_DIR OUT_DIR : PartCrafter parts -> drop fragments (<3% of part faces), fit whole set bbox to the 2mv rest mesh bbox
# (per axis), decimate, colours = nearest vertex of rest_mat.glb.
import sys, os, glob, numpy as np, trimesh, pymeshlab
from scipy.spatial import cKDTree
ind, od = sys.argv[1:3]; os.makedirs(od, exist_ok=True)
R = trimesh.load('../hy3d/best/rest_mat.glb', force='mesh'); tree = cKDTree(R.vertices); RC = R.visual.vertex_colors
P = {}
for f in sorted(glob.glob(f'{ind}/part_*.glb')):
    m = trimesh.load(f, force='mesh'); cs = m.split(only_watertight=False); n = len(m.faces)
    cs = [c for c in cs if len(c.faces) > 0.03 * n]
    if not cs: continue
    m = trimesh.util.concatenate(cs)
    if len(m.faces) < 1500: continue
    P[os.path.basename(f)[:-4]] = m
allv = np.vstack([m.vertices for m in P.values()]); lo, hi = allv.min(0), allv.max(0); s = (R.bounds[1] - R.bounds[0]) / (hi - lo)
for n, m in P.items():
    m.vertices = (m.vertices - lo) * s + R.bounds[0]
    if len(m.faces) > 20000:
        ms = pymeshlab.MeshSet(); ms.add_mesh(pymeshlab.Mesh(m.vertices, m.faces)); ms.meshing_decimation_quadric_edge_collapse(targetfacenum=20000, preservenormal=True)
        k = ms.current_mesh(); m = trimesh.Trimesh(k.vertex_matrix(), k.face_matrix())
    _, j = tree.query(m.vertices); m.visual = trimesh.visual.ColorVisuals(m, vertex_colors=RC[j]); m.export(f'{od}/{n}.glb')
    print(n, len(m.faces), m.is_watertight)
print('scale', s.round(3))
