# 3D generative-model reference outputs

These are generated meshes from the swordswoman project's image-to-3D experiments.
The Pixal3D, TRELLIS and Hunyuan3D-2mini/2mv weights, venvs and raw outputs were deleted on
2026-10-28. Only Hunyuan3D-Omni (still installed) and the one mesh the pipeline uses are kept.

| Dir | Model | Notes |
|---|---|---|
| `best/` → `swordswoman/v2/hy3d/best` | Hunyuan3D-2mv turbo, 4 views | **The mesh actually used.** `raw_mvD4_s5.glb` was cleaned into `rest_mat.glb` (the camera authority), then split into parts (`partsAB4f`) and built into rigs E→H2. The generator itself is no longer installed. |
| `hunyuan3d_omni/` | Hunyuan3D-Omni (pose control) | `out/` meshes. `poses/` holds the rest pose used by `v2/hy3d/scripts/make_poses.py`. Kept as a pose-guide fallback. |
| `hunyuan_studio_research/`, `sota_survey/` | — | Web research and screenshots. Summarised in `swordswoman/docs/*.md`. |

More Omni outputs are in `swordswoman/v2/hy3d/out/omni*` (on disk only). The weights, venv and sources
are in `../../.models/hy_omni/`: Omni plus the Hunyuan3D-2.1 and dinov2 weights stored alongside it.
The research notes on the deleted tools are kept in `swordswoman/docs/`: `pixal3d_experiment.md`,
`trellis_and_hunyuan_studio.md` and `hunyuan3d_research.md`.
