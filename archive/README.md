# Archive

Everything here is frozen history; nothing in `pipeline/` reads it. To get a deleted item back, run
`git show pre-reorg-2026-10-28:<path>`. Swordswoman's dead ends are in `../swordswoman/archive/`.

| Old path | New path | What |
|---|---|---|
| `releases/H1_v1`, `H1_v2_1`, `H1_v2_3`, `H1_v2_4` | `snowpeak/releases/` | jump-only H1 hero cuts (v1.1 hand-fixed, then v2.x generator rules). Superseded by `releases/S4_hd_actions_v1`. |
| `releases/HERO` (symlink to `H1_v2_4`) | deleted | stale |
| `START_HERE.md` | `snowpeak/START_HERE_2026-10-22.md` | H1 round-5 status page |
| `blender/` | `snowpeak/r18_blender_src/` | r18 independent Blender models A/B. The scripts hard-code `/tmp/indep/{A,B}`, so they can't run in place. |
| `out/boards/` | `snowpeak/boards_r04_r10/` | r4–r10 comparison boards: proportions, outfits, resolution, finalists, hero v1 vs v2 |
| `pipeline/tools/r15_*`, `r17*`, `r19_*`, `r20_*`, `make_r3_palettes.py` | `../pipeline/tools/rounds/` | finished-round scripts (still importable as `pipeline.tools.rounds.*`) |
| `swordswoman/.scratch_heads/` | `../swordswoman/archive/scratch_heads/` | one-off head scratch |
| `swordswoman/reviews/` | `../swordswoman/docs/reviews/` | v1 Gemini critiques |
| `.models/<scratch>` (qa_*, *_artist, p_gemini-*.json, …) | `../swordswoman/archive/scratch/` (gitignored) | old scratch outputs that had been sitting in the weights folder |
| `swordswoman/{concept,model,pixel,hybrid,renders}`, `tools/{hybrid,pixel}` | `../swordswoman/archive/v1/` | swordswoman v1 dead ends. Their scripts use cwd-relative paths, so run them from `archive/v1/` if ever needed. |
| `swordswoman/v2/{pixel_E,animate,mastersF,anim}` | `../swordswoman/archive/v2/` | dead v2 strands that no live code reads |
