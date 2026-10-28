# HY3D best rest mesh (round 3)
- `raw_mvD4_s5.glb`: Hunyuan3D-2mv turbo, 4 views (front/left/back/right of locked Level D, v2/design/turnD), 5 steps, octree 384, flashvdm. 523k faces, watertight.
- `rest_mat.glb`: voxel remesh 0.008 + decimate (scripts/clean_mesh.py, ~60k faces) -> scripts/matid2.py: visual-hull material IDs (front label at (x,y) AND side label at (z,y)) + height bands from turnD/front.png; bow scaled 1.3x with soft falloff; bang overhang pulled back toward the forehead.
  Vertex colours = flat palette per ID. `rest_mat_ids.npy` = per-vertex ID: 0 skin, 1 hair, 2 dress, 3 obi, 4 boots, 5 eyes, 6 bow.
- Frame: glb Y-up, faces +Z, her left = +X, height ~1.97 (feet y=-1.0). `skel.txt` = Omni-style 51-joint rest skeleton (head xyz, tail xyz per row; names in .scratch/hy_omni/poses/pose_rest.json); legs refitted in the rig (mesh leg centres x=-0.131/+0.106).
- Renders `rest_mat_{front,side,back,se,iso34}.png` (Workbench flat vertex colour, ortho).
- Known limits: bangs still sit just above the eyes (iso 30deg hides the upper eye a bit -> eyes painted 25% larger); bow wings are lumpy ribbon geometry; sleeve cuffs are slightly ragged.
