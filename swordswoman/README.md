# Swordswoman sprites (merged from `../test`, 2026-10-23 → 10-27)

A chibi swordswoman: red bow, dark bob with bangs and a bun, red short kimono-dress, black obi.
The goal is lively pixel sprites with a solid 3D reference. This was a separate project from
the snowpeak pipeline at the repo root, and was merged into this repo on 2026-10-28. Run scripts from
`swordswoman/`. Live strands stay under `v2/`, and dead ends are in `archive/` (see the strand table).
Team retrospective: `../docs/team_review/2026-10-28/02_swordswoman_retrospective.md`.

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
  (walk scored **Argon** 7; the Opus critique file holds only a shell error, so there is no Opus score.
  The motion scores rate the 3D preview, not pixels). See `MECHANICS.md`.
- `v2/heads96/`: layered head poses. Its second batch of rerun jobs was still in flight.
- `v2/g96/`: H2 rig calibration to the masters, with no clips rendered yet.

## Strand status
| Status | Strands |
|---|---|
| **live** | `v2/m96`, `pixelize`, `hy3d`, `g96`, `fx96`, `qc`, `animate96`, `motion`, `heads96`, `prop`, `mocap`, `throw`, `unarmed`, `REVIEW`, `_lead`, `tools`, `BRIEF.md` |
| **support**: dead or superseded, but live code reads it, so leave it in place | `v2/final`, `hair`, `anim_cut`, `face`, `face2`, `design`, `pose`, `style`, `parts`, `rigcal`, `masters`, `heads`, `anim_redraw`, `fx`, `pixel` (`v2/pixel/palette.json` is a live input of `anim_cut/tools/cm.py`) |
| **archived** | `archive/v1/` (concept, model, pixel, hybrid, renders, tools/hybrid, tools/pixel), `archive/v2/` (pixel_E, animate, mastersF, anim), `archive/scratch_heads/`, `archive/scratch/` (gitignored, old `.scratch` outputs). The v1 scripts use cwd-relative paths, so run them from `archive/v1/` if ever needed. |

## Dead ends (kept for history)
| Where | Why it was dropped |
|---|---|
| `archive/v1/{concept,model,renders,pixel}` | Cleaning hand-rigged Blender renders into sprites stayed noisy and lifeless. Judges topped out at about 6.4. |
| `archive/v1/hybrid/` S1, S2, S4, S6 | Boxy bodies, mush or drift. Merged into S3. |
| `archive/v1/hybrid/` S3, S5 | No judge passed them. The user rejected everything up to this point, which led to the `v2/BRIEF.md` restart. |
| `v2/pixel`, `archive/v2/{pixel_E,anim}`, `v2/anim_redraw` | 48 px Gemini redraws went off-model (scores 4.5–5.5). |
| `v2/anim_cut` | 48 px cutout clips were superseded. Its tools (`ff_redraw`, `lint_style`, `colorcheck`) are still used. |
| `v2/masters`, `archive/v2/mastersF`, `v2/final` (64 px) | 64 px didn't represent the source art. `final` was stopped for the size bake-off. |
| `v2/pixelize` methods A/B/D, 48/64 px | Worse face and eyes. Gemini also ignores the requested size. |
| PartCrafter (`v2/parts/C`) | Splits by material, not by joint. |
| Pixal3D single-view, Hunyuan3D 2.1 | Invented a ponytail. |
| TRELLIS | Noisy mesh that isn't watertight, with a near-black texture. |
| Hunyuan3D-Omni | Kept only as a pose-guide fallback. |

Overall review hub: `../REVIEW/index.html` (repo-wide hub; old swordswoman page in `../REVIEW/legacy/`). Each strand has its own `v2/<strand>/NOTES.md`.

## Research
`docs/`: `hunyuan3d_research.md`, `sota_image_to_3d_2026.md`, `trellis_and_hunyuan_studio.md`,
`pixal3d_experiment.md`, `pixel_art_best_practices.md`, `pixel_cleanup_guide.md`,
`pixelart_project_study.md`, `design_bible.md`, palettes, and `docs/reviews/` (v1 Gemini critiques).
`docs/ANIM_DIRECTION.md` (timing principles) and `docs/STYLE_TARGET.md` are still referenced by v2.
The generated 3D meshes are collected in `../reference/3d/`.

## Environment
- `swordswoman/.venv` (gitignored): Python 3.13 with numpy, pillow and scipy.
- `swordswoman/.scratch` is a symlink to `../.models/` (gitignored, about 41 GB). It holds the
  weights, venvs and checkouts for Hunyuan3D-Omni and 2.1 (`hy_omni`), the shared pixel-tools venv
  (`pixtools`: numpy, scipy, opencv, pillow, scikit-image), Retro Diffusion's pixel-art-fixer
  (`pixel-art-fixer`), plus the CMU, Bandai and LaFAN1 mocap data (`mocap`). All of it can be
  re-downloaded.
- Removed on 2026-10-28: Pixal3D, TRELLIS, and Hunyuan3D-2mini/2mv (weights, venv and raw outputs).
  The 2mv mesh that was used is still kept in `v2/hy3d/best`. Without the 2mv generator,
  `v2/parts/scripts/run_mv_parts.py` no longer runs.
- Scripts that need it:
  - the pixtools venv: `v2/pixelize`, `v2/m96/tools` (moved off the PixelOE venv on 2026-10-28)
  - the Omni venv (for trimesh): `v2/g96/scripts`, `v2/hy3d/scripts/make_rig.sh`, `v2/prop/tools/solveF.py`.
    These used the old Hunyuan venv. Rig H2 was verified to rebuild byte-for-byte on the Omni venv.
  - mocap data: `v2/mocap`, `v2/throw`, `v2/unarmed`
- External tools: Blender at `/Applications/Blender.app`, `tools/gemini.py` (Floodgate), and the
  `claude-as` zsh function for Opus critics.
- Absolute paths were rewritten during the merge: `…/other/test` became `…/other/pixelart/swordswoman`,
  and `…/test/.scratch` became `…/pixelart/.models`.
- `pz.py` is not bit-deterministic. Two runs of the same input differ by a few pixels in the png/txt; the json is stable.
- Removed on 2026-10-28: PartCrafter (it lost the parts test) and PixelOE (it lost the pixelize bake-off).
  `pz.py` methods B and E1, which call the PixelOE library, no longer run. The winning E2 doesn't need it.

## What's in git
Code, notes, critiques, masters, rigs, the chosen meshes and the research are committed.
Large frame dumps, mesh iterations and dead-end round outputs stay on disk only.
The full list is in the "merged from ../test" section of the root `.gitignore`.
