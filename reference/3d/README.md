# 3D generative-model reference outputs

These are generated meshes and renders from the image-to-3D experiments in the swordswoman project.
They were copied from `test/.scratch/*/out` during the merge. The model weights, venvs and code that
produced them are in `../../.models/` (gitignored).

| Dir | Model | Notes |
|---|---|---|
| `best/` → `swordswoman/v2/hy3d/best` | Hunyuan3D-2mv turbo, 4 views | **The mesh actually used.** `raw_mvD4_s5.glb` was cleaned into `rest_mat.glb` (the camera authority), then split into parts and built into rigs E→H2. |
| `hunyuan3d_2mini/` | Hunyuan3D-2mini (about 25 s per image) | 21 .glb files plus renders, and `inputs/` |
| `hunyuan3d_omni/` | Hunyuan3D-Omni (pose control) and 2.1 | `out/` meshes and `poses/` (the rest pose used by `v2/hy3d/scripts/make_poses.py`). Kept as a pose-guide fallback. 2.1 invented a ponytail. |
| `pixal3d/` | Pixal3D (TRELLIS.2 engine) | Logs, sheets and Gemini verdicts are in git. The raw r1/r2/smoke/mv_frontback outputs (1.8 GB) stay on disk only. Best results came from 4 consistent views. Single-view runs invented a ponytail. |
| `trellis/` | TRELLIS (trellis-mac) | Dead end: noisy mesh that isn't watertight, with a near-black texture. `out/` stays on disk only. |
| `hunyuan_studio_research/`, `sota_survey/` | — | Web research and screenshots. Summarised in `swordswoman/docs/*.md`. |

`swordswoman/v2/hy3d/out` (40 more .glb files, plus the Omni pose variants) and
`swordswoman/v2/REVIEW/3d` (.usdz files) are also on disk only.
