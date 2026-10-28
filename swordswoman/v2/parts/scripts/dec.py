# dec.py IN.glb OUT.glb [faces]  largest component + pymeshlab quadric decimation; vertex colours kept by nearest-vertex transfer
import sys, numpy as np, trimesh, pymeshlab
from scipy.spatial import cKDTree
m = trimesh.load(sys.argv[1], force='mesh'); m = max(m.split(only_watertight=False), key=lambda c: len(c.faces))
ms = pymeshlab.MeshSet(); ms.add_mesh(pymeshlab.Mesh(m.vertices, m.faces))
ms.meshing_decimation_quadric_edge_collapse(targetfacenum=int(sys.argv[3]) if len(sys.argv) > 3 else 20000, preservenormal=True, qualitythr=0.5)
k = ms.current_mesh(); o = trimesh.Trimesh(k.vertex_matrix(), k.face_matrix())
vc = getattr(m.visual, 'vertex_colors', None)
if vc is not None and len(vc) == len(m.vertices) and m.visual.kind == 'vertex':
    _, j = cKDTree(m.vertices).query(o.vertices); o.visual = trimesh.visual.ColorVisuals(o, vertex_colors=vc[j])
o.export(sys.argv[2]); print(sys.argv[2], k.face_number(), o.is_watertight)
