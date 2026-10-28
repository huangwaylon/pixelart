# Swordswoman sprites (merged from `../test`, 2026-10-23 → 10-27)

A chibi swordswoman: red bow, dark bob with bangs and a bun, red short kimono-dress, black obi.
The goal is lively pixel sprites with a solid 3D reference. This was a separate project from
the snowpeak pipeline at the repo root, and was merged into this repo on 2026-10-28. The folder
layout inside `swordswoman/` is unchanged from `test/`, because the scripts reference each other
by path (`v2/...`, `hybrid/...`, `.scratch/...`).

## What worked best (start here)
The pipeline that won, from `v2/BRIEF.md` onward:

1. **Design → illustration.** Simplified design (`v2/BRIEF.md`). Gemini turnaround
   illustrations, final set at `v2/hair/turnE_final/` (SE = `iso_SE_fixed.png`).
2. **3D reference.** Hunyuan3D-2mv (turbo, 4 views of the Level D design) produced
   `v2/hy3d/best/raw_mvD4_s5.glb`. It was cleaned into `rest_mat.glb`, which became the 30° camera
   authority and the source of the `rigref` renders. It was split into parts (`v2/parts` AB3/AB4,
   then `v2/hy3d/partsAB4f`) and re-proportioned into rigs E→H2 (`v2/hy3d/rigs/`).
   **Rig H2** (calibrated in `v2/g96`) supplies the animation guides.
3. **Pixelize.** Method **E2** won the bake-off (`v2/pixelize/RESULTS.md`): k-centroid downscale,
   face pass, then lock to the palette, giving a **96 px figure in a 128 px cell**.
   Palette: `v2/pixelize/palette.json`. Re-run with `v2/pixelize/make_top.sh top1`.
4. **Masters.** `v2/m96/` polishes the E2 output (geometry targets, `FACE_SPEC.md`,
   `eye_spec.json`, region jobs, QC gates) and is marked **M96 READY**:
   - `v2/m96/masters/EC0_<S|SE|E|NE|N>_96.*`: the 5 view masters
   - `v2/m96/heads/`: 45 expression head stamps
5. **Animation.** Each frame is redrawn (`v2/anim_cut/tools/ff_redraw.py`) over the rig H2 guide,
   with the head locked by stamp, plus `v2/fx96` effects and the `v2/qc` gate.

## Status when merged: animation not finished
- `v2/animate96/`: pilot (idle_SE, walk_SE). It passes the QC gate, but motion scored only 3–5.
- `v2/motion/`: whole-body motion with springs on hair, skirt and ribbons. Stopped mid-round 3
  (walk scored Opus 7; the Argon score was never written). See `MECHANICS.md`.
- `v2/heads96/`: layered head poses. Its second batch of rerun jobs was still in flight.
- `v2/g96/`: H2 rig calibration to the masters, with no clips rendered yet.

## Dead ends (kept for history)
| Where | Why it was dropped |
|---|---|
| `concept/`, `model/`, `renders/`, `pixel/` (v1) | Cleaning hand-rigged Blender renders into sprites stayed noisy and lifeless. Judges topped out at about 6.4. |
| `hybrid/` S1, S2, S4, S6 | Boxy bodies, mush or drift. Merged into S3. |
| `hybrid/` S3, S5 | No judge passed them. The user rejected everything up to this point, which led to the `v2/BRIEF.md` restart. |
| `v2/pixel`, `pixel_E`, `anim`, `anim_redraw` | 48 px Gemini redraws went off-model (scores 4.5–5.5). |
| `v2/anim_cut` | 48 px cutout clips were superseded. Its tools (`ff_redraw`, `lint_style`, `colorcheck`) are still used. |
| `v2/masters`, `mastersF`, `final` (64 px) | 64 px didn't represent the source art. `final` was stopped for the size bake-off. |
| `v2/pixelize` methods A/B/D, 48/64 px | Worse face and eyes. Gemini also ignores the requested size. |
| PartCrafter (`v2/parts/C`) | Splits by material, not by joint. |
| Pixal3D single-view, Hunyuan3D 2.1 | Invented a ponytail. |
| TRELLIS | Noisy mesh that isn't watertight, with a near-black texture. |
| Hunyuan3D-Omni | Kept only as a pose-guide fallback. |

Overall review hub: `v2/REVIEW/index.html`. Each strand has its own `v2/<strand>/NOTES.md`.

## Research
`docs/`: `hunyuan3d_research.md`, `sota_image_to_3d_2026.md`, `trellis_and_hunyuan_studio.md`,
`pixal3d_experiment.md`, `pixel_art_best_practices.md`, `pixel_cleanup_guide.md`,
`pixelart_project_study.md`, `design_bible.md`, palettes.
`hybrid/ANIM_DIRECTION.md` (timing principles) and `hybrid/STYLE_TARGET.md` are still referenced by v2.
The generated 3D meshes are collected in `../reference/3d/`.

## Environment
- `swordswoman/.venv` (gitignored): Python 3.13 with numpy, pillow and scipy.
- `swordswoman/.scratch` is a symlink to `../.models/` (gitignored, about 85 GB). It holds the
  weights, venvs and checkouts for Hunyuan3D-2mini (`hunyuan`), Hunyuan3D-Omni and 2.1 (`hy_omni`),
  Pixal3D (`pixal3d`), TRELLIS (`trellis`), PartCrafter (`parts`), PixelOE (`pixelize`), and the
  CMU, Bandai and LaFAN1 mocap data (`mocap`). All of it can be re-downloaded.
- Scripts that need it:
  - the PixelOE venv: `v2/pixelize`, `v2/m96/tools`
  - the Hunyuan venv (for trimesh): `v2/g96/scripts`, `v2/hy3d/scripts/make_rig.sh`
  - mocap data: `v2/mocap`, `v2/throw`, `v2/unarmed`
- External tools: Blender at `/Applications/Blender.app`, `tools/gemini.py` (Floodgate), and the
  `claude-as` zsh function for Opus critics.
- Absolute paths were rewritten during the merge: `…/other/test` became `…/other/pixelart/swordswoman`,
  and `…/test/.scratch` became `…/pixelart/.models`.
- PixelOE is not bit-deterministic. Two runs of the same input differ by a few pixels.

## What's in git
Code, notes, critiques, masters, rigs, the chosen meshes and the research are committed.
Large frame dumps, mesh iterations and dead-end round outputs stay on disk only.
The full list is in the "merged from ../test" section of the root `.gitignore`.
