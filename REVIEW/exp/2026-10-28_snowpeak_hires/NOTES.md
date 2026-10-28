# Snowpeak: render hi-res, then pixelate + fix (2026-10-28)

**Hypothesis (owner):** if we render the 3D model at high resolution, then pixelate it and run the fix pass, we get better pixel art than the native pixel pass.
**Verdict: rejected.** Hi-res input does not beat the shipped native pass. On the QA metrics it is the same or slightly worse. Both critics put native at 6/10, and every hi-res method scored the same as native or lower. None of the six known art problems changes, because they come from the model and the design, not from sampling.

## Method
All code is in `scripts/`. It imports `pipeline/*` read-only and edits nothing under pipeline/, data/ or overrides/.

- `hrlib.setup()` builds the Scene and palette exactly as `pipeline.build.main` does.
- `hrlib.trace_prims()` fires the same rays as `render_pixels(ss=k)` and keeps every sample as one hi-res pixel. That is k x the sprite PPU (k = 4, 8) with the same camera, light, pivot grid, `_stylize_hair` and shadow rays, and the same `lod: all` model. Buffers kept:
  - t (depth), prim, normal, lambert (raw and stylised), shadow
  - material id, group id
  - band tone (the palette's `material_bands` thresholds per sample)
  - smooth-shaded RGB (the `render_smooth` ramp interpolation) and flat-band RGB
- `hrlib.edges()` is the hi-res edge pass. Each line is marked on one side only, so it stays 1 hi-res px wide:
  - depth break > 2.2 between groups (the native inner-line rule, at hi-res)
  - normal crease > 50° inside a part, on the darker side
  - material change (visualised only)

  A native cell becomes a line if at least 0.75·k edge samples fall in it. Skin is excluded. On average 60-86 line cells are added per frame.
- **Downscale methods.** Each one produces a native PixelFrame (idx, depth, group, material). Opacity, material and group always come from the render_pixels majority rule:

| id | method |
|---|---|
| N | shipped native pass (render_pixels ss=3). Re-rendered here; it matches `out/variants/*/<clip>_sheet.png` with **0 px** different on every run |
| V | majority material + mean lambert -> band (the native rule with k² samples) |
| VM | majority material + **majority band** among that material's samples |
| KC | k-centroid per cell (port of `swordswoman/v2/pixelize/tools/pz.py:kcentroid`, 3 clusters, fg samples only) on flat-band RGB -> Lab lock to the cell material's ramp |
| KS | k-centroid on smooth RGB -> lock |
| AA | area average of smooth RGB -> lock |
| PF | Retro Diffusion pixel-art-fixer (`pipeline/tools/pixelfix.py --step k k`) on the whole smooth sheet -> lock |
| VME / KCE | VM / KC + hi-res normal/depth interior lines (the untried "normal-buffer interior lines" idea) |

- **FIX pass.** `hrlib.patched()` swaps `pipeline.frames.render_pixels` at runtime (the source file is untouched). As a result `Scene.render_base` runs the **entire shipped fix chain** on each method's PixelFrame:
  - lone-pixel removal and material-aware despeckle
  - `pixelrules.apply_rules` and `apply_post_outline`
  - face cels and face_eyes
  - outline, pixel-perfect pass, sel-out on dark (the r10 decision), kept sel-out runs
  - ring_trim, skin_edge_dark, bow_shine, final orphan pass
  - `temporal_hold` on idle, as in the build

  So the only thing that differs between rows is the resolve step. RAW boards show each method before the fix chain.
- **Coverage:**

| variant | clip | k | directions x frames |
|---|---|---|---|
| S4_hd2 | idle, walk, run | 8 | 8 x 8 |
| S4_hd2 | idle, walk | 4 | 8 x 8 |
| S4_hd2 | run | 4 | S/SE/E x 8 |
| S4_hd | idle, walk | 8 | 8 x 8 |
| S4_hd | run | 8 | S/SE/E x 8 |

  An 8x trace takes about 3 s per frame. The whole run took 8 min in parallel.
- **Metrics** (`scripts/analyze.py` -> `metrics.json`, `metrics.md`):
  - QA definitions from `pipeline/qa.py`: orphans (face and deliberate pixels protected), `jaggy_count`, colours, height delta across directions
  - motion: ABA boil (`f[t-1]==f[t+1]!=f[t]`, cyclic) and changed px per frame
  - `coat_islands`: islands of ≤ 3 px of non-coat colour fully enclosed by the coat ramp (the "teal in coat" bug)
  - diffN: % of pixels that differ from native

## Numbers: S4_hd2, k=8 (8 dirs x 8 frames; per frame unless stated)
| clip | method | orphans | jaggies/f | colours | h-delta | coat isl/f | ABA/f | diffN % |
|---|---|---|---|---|---|---|---|---|
| idle | **N** | 0 | **0.55** | 15 | 0 | **0.06** | 3.38 | - |
| idle | V | 0 | 0.92 | 15 | 0 | 0.22 | 3.14 | 9.7 |
| idle | VM | 0 | 0.92 | 15 | 0 | 0.33 | 3.09 | 12.2 |
| idle | KC | 0 | 0.92 | 15 | 0 | 0.33 | **2.98** | 12.2 |
| idle | PF | 0 | 0.92 | 15 | 0 | 0.30 | 3.42 | 20.9 |
| idle | KCE | 0 | 0.92 | 15 | 0 | 0.25 | 3.12 | 15.1 |
| walk | **N** | 0 | **1.00** | 16 | 2 | **0.00** | **53.2** | - |
| walk | KC | 0 | 1.53 | 15 | 2 | 0.06 | 53.9 | 12.6 |
| walk | PF | 0 | 1.53 | 16 | 2 | 0.09 | 58.4 | 24.2 |
| walk | KCE | 0 | 1.53 | 15 | 2 | 0.06 | 55.6 | 15.0 |
| run | **N** | 0 | **1.12** | 17 | 2 | 0.08 | 96.3 | - |
| run | KC | 0 | 1.70 | 17 | 3 | 0.09 | 97.9 | 13.6 |
| run | PF | 0 | 1.70 | 18 | 3 | 0.12 | 99.4 | 24.1 |

- **Jaggies rise by 50-70% for every hi-res method.** The silhouette uses the same majority-coverage rule at k² samples instead of 9. The truer coverage puts more 1-px steps on the outline, and the native 3x3 sampling is accidentally smoother. Jaggies are identical across hi-res methods because they share the silhouette.
- **k=4 vs k=8:** the results are almost the same (idle KC: ABA 3.48 vs 2.98, jaggies 0.88 vs 0.92). 4x is enough to know that 8x won't help.
- **S4_hd** follows the same pattern: walk N jaggies 1.41 vs 2.03; coat islands 0.12 vs 0.14-0.16; ABA 53.3 vs 52.8 (KC) to 59.3 (PF).
- **Effect of the fix chain:** RAW resolves (`boards/*raw_4x.png`) have no face and show banding staircases. Most of the final quality comes from the shipped rule chain, not from the resolve step.
- **Sensitivity:** V (the native rule with more samples) already differs from native on ~10% of pixels. Native's sampling sits at a noise floor where resolve choices only reshuffle band boundaries.

## Critiques
Both critics saw the same 3 boards: 8-dir idle at 4x and 1x, plus the SE walk strip.
- **Gemini Argon** (`critique/gemini_argon.md`): N 6, VM 5.5 worse, KC 6 same, PF 3.5 worse, KCE 4.5 worse.
  - PF: a fringe highlight streak, the ponytail splitting off, the worst walk boil.
  - KCE: interior lines read as dirt at 34 px.
  - KC: a 1-frame 3-px coat line on walk f5.
  - All 6 known issues: "No". Recommendation: keep N.
- **Opus** (`critique/opus.md`, non-empty; the first attempt failed at proxy startup and the retry worked): N 6, VM 5 worse, KC 6 same, PF 3 worse, KCE 5 worse.
  - VM/KC: a 2-px orange fringe streak (visor), the E bow becoming a 2-px horn, the SE/SW mitten island growing from a square to a plus shape.
  - PF: purple strand lines and off-ramp mint pixels.
  - KCE: broken 1-2-px dashes that flicker.
  - All 6 known issues: "no". Recommendation: keep N; the work belongs in the model.
- **My own read of the boards (agrees):**
  - The hi-res buffers (`boards/02_*`) already contain the flat beige coat with a lavender wedge, the mitten pressed against the coat front, stub boots and a small bow.
  - The SE/SW "teal islands" are the mitten silhouette over the coat, so they are geometry, not sampling. They appear in every row.
  - Smooth-RGB methods (KS, AA, PF) bring back a bright hair shine band that the material bands deliberately suppress.

## Verdict / recommendation
- **Don't adopt the hi-res-then-pixelate path for snowpeak.**
  - Best case (KC, k=8): equal to native in look, idle boil 12% lower, but jaggies +65% and coat islands up from 0.06 to 0.33 per frame.
  - PF is clearly worse.
- **The edge pass (normal-buffer interior lines) is not worth it as an automatic pass at 34 px.** Lines come out broken and boil frame to frame.
- **Spend the budget upstream**, as the retrospective and both critics say:
  - pose/arm placement so the mitten doesn't sit on the coat front, or a "no foreign islands inside coat" rule
  - a 2-tone coat with a fold line
  - re-proportioning toward the r13 canon
  - a per-direction part library for the bow and fringe
- **One cheap carry-over to test:** majority-band voting (VM/KC) lowered idle ABA boil (3.38 -> 2.98-3.09). It could replace mean-lambert banding inside the native ss=3 pass. That is a small render-rule change that needs a build-hash bump, so it was not done here.

## Paths
- `scripts/`:
  - `hrlib.py`: setup, trace, edges, resolves, chain hook
  - `run_exp.py`: per variant/clip/k
  - `analyze.py`: metrics and method boards
  - `keyboards.py`: key boards and GIFs
  - `critique.sh`
- `big/`: hi-res 8x/4x intermediates for S/SE/E idle f1 (plus N idle, walk f3, run SE f3):
  - `_a_smooth`
  - `_b_bands`, `_b_matid`, `_b_normal`, `_b_depth`
  - `_c_edges`
  - `_pf_out_*` = raw pixel-fixer sheets
- `frames/*.pkl`: every final and raw 48x64 frame per method (199 MB, deletable)
- `boards/`:
  - `00_key_<v>_idle_8dir_{4x,1x}.png`
  - `01_<v>_walk_SE_strip_4x.png`
  - `02_<v>_hires_buffers.png`
  - `03_*_8dir_top_native_bottom_KC.gif`
  - `<v>__<clip>__k<k>__methods_{4x,1x}.png`, `*raw_4x.png`
- `metrics.json`, `metrics.md`, `critique/`, `logs/`
