# model/ai_ref: AI-generated reference meshes (never shipped as sprite source)

Use these meshes as proportion and silhouette references and as shrinkwrap targets only. Keep them in a hidden `REF_*` collection in Blender, and never render them into sprites.

## Layout

```
model/ai_ref/
  hunyuan_studio/      # exports from hy3d.tencent.ai (Tencent HY 3D Global) or 3d.hunyuan.tencent.com
  hunyuan_local/       # optional: copies of .scratch/hunyuan/out/*.glb worth keeping
  trellis/             # optional: TRELLIS.2 results worth keeping
```

## File naming

`akane_<tool>_<model>_<input>_<settings>.<ext>`

- `<tool>`: `hy3d` (Hunyuan web), `hy3dlocal`, `trellis2`
- `<model>`: `v31`, `v30`, `v25`, `2mini`, ...
- `<input>`: `front` (single image), `mv3` (front+left+back), `mv4`, ...
- `<settings>`: dash-joined, e.g. `tri500k-pbr`, `lowpoly-quad`, `lowpoly-tri`, `geom50k`, `rig`, `anim-<name>`

Examples:
- `akane_hy3d_v31_front_tri500k-pbr.glb`
- `akane_hy3d_v30_mv3_lowpoly-quad.fbx`
- `akane_hy3d_v30_front_lowpoly-quad_rig.fbx`

## Each drop needs a sidecar note

Create `<same-name>.txt` next to each file, containing:
- the date, the site (CN or Global) and the input image paths used
- the settings exactly as clicked: model version, face count, triangle or quad, PBR on or off, texture style
- generation time, and credits or daily quota used
- anything that looked wrong (fused sword, missing bun, ...)

## Rules

- Generated assets carry Tencent AI-generated watermarks and metadata. Do not strip them (ToS), and label any published output as AI-generated.
- Do not use these outputs to train any model (Hunyuan ToS, and the Hunyuan Community License for local weights).
- Do not commit large binaries elsewhere in `model/`. This folder is the only drop-off.
