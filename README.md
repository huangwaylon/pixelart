# pixelart: chibi sprite projects

Two projects share this repo.
- **Snowpeak lives at the repo root.** Run its pipeline with the repo root as the working directory.
- **Swordswoman is self-contained in `swordswoman/`.** Run its scripts from `swordswoman/`; many of them use absolute paths.

Latest team review: [`docs/team_review/2026-10-28/00_SUMMARY.md`](docs/team_review/2026-10-28/00_SUMMARY.md)
covers what worked, what didn't, the recommended pipeline, what hasn't been tried, and the decisions waiting on you.

## Projects
| Project | Where | Current best | Status |
|---|---|---|---|
| Snowpeak girl (3D → pixel pipeline + editor) | `pipeline/ data/ overrides/ art/ editor/` | `releases/S4_hd_actions_v1/` (13 clips, approved) | S4_hd2 refinement: only idle, walk and run so far, in `00_REVIEW/r21_s4_hd2/` |
| Swordswoman (illustration → 96 px pixel, Hunyuan3D rig guides) | `swordswoman/` | `swordswoman/v2/m96/` masters (M96 READY) | animation in progress, see [`swordswoman/README.md`](swordswoman/README.md) |

## Look here first
- **Reviews:** [`00_REVIEW/README.md`](00_REVIEW/README.md) (snowpeak round index, newest first). **Main review hub: `REVIEW/index.html`** (open it in a browser). It covers every attempt and test, filterable by project and status.
- **Releases:** [`releases/README.md`](releases/README.md)
- **Decisions:** [`docs/DECISIONS.md`](docs/DECISIONS.md)
- **Snowpeak pipeline manual:** [`docs/SNOWPEAK_PIPELINE.md`](docs/SNOWPEAK_PIPELINE.md)
- **3D reference meshes:** [`reference/3d/README.md`](reference/3d/README.md)
- **Archived dead ends:** [`archive/README.md`](archive/README.md)

## Run
| Task | Command | Working directory |
|---|---|---|
| Build a clip | `.venv/bin/python -m pipeline.build --variant S4_hd2 --anim idle --verify` | repo root |
| Editor | `.venv/bin/python -m pipeline.server`, then open http://127.0.0.1:8777/editor/ | repo root |
| Pixelize a view | `.scratch/pixelize/pixeloe/venv/bin/python -I v2/pixelize/tools/pz.py EC0 S 96 --pal v2/pixelize/palette.json --out DIR` | `swordswoman/` |
| Rebuild rig H2 parts | `.scratch/hy_omni/venv/bin/python -I v2/g96/scripts/repro_h.py v2/hy3d/rigs/H2/parts/spec_solved.json v2/hy3d/partsAB4f v2/hy3d/best/skel.txt OUT` | `swordswoman/` |

## Repo map
| Path | What | In git |
|---|---|---|
| `pipeline/` (`tools/`, `tools/rounds/`) | snowpeak code, current tools, and the scripts from finished rounds | yes |
| `data/` `overrides/` `art/` | snowpeak sources. They are hashed into build IDs. | yes |
| `editor/` | browser pixel editor | yes |
| `00_REVIEW/` `releases/` | review rounds r10–r21 and frozen deliverables | yes |
| `docs/` | decisions, schema, research, review history, team reviews. Data files cite paths under `docs/review/`, so don't move it. | yes |
| `reference/3d/` | 3D generator outputs (Hunyuan3D-Omni plus the 2mv mesh that was used) | yes |
| `swordswoman/` | the second project, with its own `archive/` for dead ends | yes (bulk files ignored) |
| `archive/` | snowpeak dead ends: H1 releases, old boards, r18 Blender sources, START_HERE | yes |
| `builds/` `out/` `work/` | generated output and scratch | no |
| `.venv/` `.models/` | snowpeak venv; weights and venvs (`hy_omni pixtools pixel-art-fixer mocap`, about 36 GB) | no |

## Conventions
- New directories use lowercase snake_case. Review rounds are named `rNN_topic`. Variant IDs keep their case (`S4_hd2`).
- Generated output is never committed. Dead ends go to `archive/`. Nothing is renamed inside `00_REVIEW/` or `docs/review/`.
- Don't edit `pipeline/*.py`, `data/**` or `overrides/**` for housekeeping, because that changes every build ID.
