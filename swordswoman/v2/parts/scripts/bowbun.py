# bowbun.py OUT_DIR : clean low-poly bow (2 tapered lobes + knot) and bun (sphere) placed on the approach-A bow/bun bboxes
# (= 2mv proportions; bow x1.3 already applied in matid2). Colours = the rest mesh bow/hair IDs.
import sys, os, numpy as np, trimesh
od = sys.argv[1]; os.makedirs(od, exist_ok=True)
R = trimesh.load('../hy3d/best/rest_mat.glb', force='mesh'); RC = R.visual.vertex_colors; RID = np.load('../hy3d/best/rest_mat_ids.npy')
BOW, HAIR = RC[RID == 6][0], RC[RID == 1][0]
bb = trimesh.load('A/parts/bow.glb', force='mesh').bounds; ub = trimesh.load('A/parts/bun.glb', force='mesh').bounds
W = bb[1][0] - bb[0][0]; cx = (bb[0][0] + bb[1][0]) / 2; cy = bb[0][1] + 0.68 * (bb[1][1] - bb[0][1]); cz = (bb[0][2] + bb[1][2]) / 2 + 0.03
parts = []
for s in (-1, 1):
    e = trimesh.creation.icosphere(3, radius=1.0); v = e.vertices
    t = (v[:, 0] * s + 1) / 2                      # 0 at the knot side, 1 at the outer tip
    v[:, 1] *= 0.45 + 0.55 * t                     # lobe tapers toward the knot
    v[:, 2] *= 0.6 + 0.4 * t
    v *= [W * 0.27, (bb[1][1] - bb[0][1]) * 0.48, 0.09]
    e.vertices = v
    e.apply_transform(trimesh.transformations.rotation_matrix(np.radians(12 * s), [0, 0, 1]))
    e.apply_translation([cx + s * W * 0.25, cy, cz]); parts.append(e)
k = trimesh.creation.icosphere(3, radius=0.075); k.vertices *= [1.0, 1.1, 0.9]; k.apply_translation([cx, cy - 0.01, cz + 0.02]); parts.append(k)
bow = trimesh.util.concatenate(parts)
bow.visual = trimesh.visual.ColorVisuals(bow, vertex_colors=np.tile(BOW, (len(bow.vertices), 1)))
c = (ub[0] + ub[1]) / 2; r = 0.5 * max(ub[1][0] - ub[0][0], ub[1][1] - ub[0][1]) * 0.85
bun = trimesh.creation.icosphere(3, radius=r); bun.apply_translation([c[0], c[1], c[2] - 0.02])
bun.visual = trimesh.visual.ColorVisuals(bun, vertex_colors=np.tile(HAIR, (len(bun.vertices), 1)))
bow.export(f'{od}/bow.glb'); bun.export(f'{od}/bun.glb'); print('bow', bow.bounds.round(3).tolist(), 'bun r', round(r, 3), c.round(3))
h = trimesh.load(f'{od}/head.glb', force='mesh'); hc = h.visual.vertex_colors.copy()
red = (hc[:, 0].astype(int) > hc[:, 1].astype(int) + 60) & (hc[:, 0].astype(int) > hc[:, 2].astype(int) + 60); hc[red] = HAIR
h.visual = trimesh.visual.ColorVisuals(h, vertex_colors=hc); h.export(f'{od}/head.glb'); print('head red->hair', int(red.sum()))
