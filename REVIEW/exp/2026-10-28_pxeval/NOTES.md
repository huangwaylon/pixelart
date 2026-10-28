# pxeval: shared deterministic sprite/animation evaluator (2026-10-28)

Tool: `pipeline/tools/pxeval.py` (numpy, scipy and pillow only). Back-test driver: `pipeline/tools/pxeval_backtest.py`.
The full tables are in `tables.md`. The raw JSON is in `backtest_seq.json` and `backtest_still.json`. The change maps are in `viz/`.

Why this exists: team review 02 §3 found that the LLM critic scores did not predict the owner's verdicts. Measured fidelity
against the illustration, plus side-by-side boards, did. 03 §5 ranks automated pixel and motion metrics as the #1 untried idea.
pxeval gives the three running experiments (hi-res 3D → pixelize → fix for swordswoman and snowpeak, and Gemini → pixel-art-fixer)
one set of numbers that can be compared.

## Usage

Any team venv works, always with `-I`. The output is byte-identical under `.models/pixtools`, `.models/pixel-art-fixer`
and `swordswoman/.venv`.

```
PY=.models/pixtools/venv/bin/python; T=pipeline/tools/pxeval.py
# still: fidelity vs a reference sprite and/or the illustration, plus cleanliness
$PY -I $T still CAND.png --ref REF.png --illus ILLUS.png --pal palette.json [--mask-bg auto] [--align auto|cell|feet]
        [--meta auto|none|X.json] [--outline-hex 160c0d] [--save-illus-grid ref_grid.png] [--json out.json]
# seq: temporal stability and motion
$PY -I $T seq anim.gif | frames_dir/ | 'f_*.png' | sheet.png --cell W H --row R|SE|all  [--ms 100 ...] [--mask moving.png]
        [--loop auto|yes|no] [--viz viz.png] [--full]
# for snowpeak sheets, the cell, directions, durations and loop come from the sibling *_sheet.json:
$PY -I $T seq releases/S4_hd_actions_v1/walk/walk_sheet.png --row all
# board and gif
$PY -I $T board OUT.png --row "illus:a.png" --row "ours:b.png,c.gif,sheet.png@48x64rSE" [--scale 4] [--bg 808080] [--title T]
$PY -I $T gif OUT.gif f1.png f2.png ... | sheet.png --cell 48 64 --sheet-row SE   --scale 4 --ms 100
```

General behaviour:
- Every subcommand prints one JSON object (`"pxeval": 1`). Existing keys stay fixed; new keys may be added.
- Floats are rounded to 4 decimal places. There is no randomness.
- `--unscale auto` undoes integer nearest-neighbour upscaling, so review GIFs can be fed in directly. The factor is the gcd of the colour-change positions; for example, the anim96 GIFs are 4x and mocap is 6x.
- Background (`--mask-bg auto`): alpha is used if any pixel is transparent. Otherwise the most common border colour is the background, matched exactly for ≤256 colours and with tolerance 24 otherwise.
- `still --illus` places the sprite on the `h, w, ox, oy` grid from the sibling `CANDIDATE.json` when one exists, exactly like metrics.py. Otherwise it uses the alpha bbox (`bbox_source` tells you which).

## Metric definitions

### still: `vs_illus` (exact port of `swordswoman/v2/pixelize/tools/metrics.py`)
How the reference is built (as in metrics.py, including pzlib.load, seg2 and materials):
- The illustration is cropped to the figure bbox: foreground is `min<215 | range>30`, or alpha if present. Enclosed holes smaller than 0.15 % of the image are filled.
- It is area-downsampled to the sprite's figure grid (`h × w`) with PIL BOX.
- Reference alpha is cell coverage above 50 %, using integer bins.

The comparison region is the figure bbox padded by 2 on a white background.

| key | definition |
|---|---|
| `ssim` | SSIM on Lab L, window 7, data_range 100 (port of skimage `structural_similarity`) |
| `ssim_b` | `ssim` after a σ=1 gaussian blur of both images. Tolerates 1 px shifts. **This is the headline fidelity number** |
| `dE` | mean CIEDE2000 (port of skimage `deltaE_ciede2000`) over the union of the sprite and reference figures |
| `sil` | silhouette IoU |
| `bloat` | sprite area / reference area |
| `iou_*` | per-material IoU (hair, red, skin, obi, boot, socks). Needs a swordswoman char-keyed palette |
| `line_f` | F1 within 1 px between the illustration's dark-line cells and the sprite's outline colour |
| `kcomp` | number of 8-connected components of the outline colour |
| `orph` | metrics.py orphans (pixels with no same-colour 8-neighbour, inside the region) |
| `face_ssim` | SSIM on the face box (illustration skin hull, upper 42 %). `null` on back views |

### still: `vs_ref` (sprite vs sprite, for example a candidate vs the m96 master)
- Alignment is `cell` (same canvas) when the sizes match. Otherwise it is `feet` (bbox bottom-centre).
- `ssim`, `ssim_b`, `dE`, `sil` and `bloat` are defined as above, on white.
- `same_px` is the fraction of union pixels with exactly the same colour.
- `colour_iou` is the area-weighted per-colour IoU.
- Also reported: `height_delta`, `width_delta`, `feet_delta` and `centroid_offset` [dx, dy].

### still: `clean` (pixel-art cleanliness, on the candidate)
| key | definition |
|---|---|
| `colours` | number of opaque colours |
| `off_palette_px` | pixels whose colour is not exactly in `--pal` |
| `off_palette_colours` | number of distinct colours not in `--pal` |
| `off_palette_px_dE3` | pixels more than ΔE2000 3 from every `--pal` colour |
| `orphans` | `pipeline/qa.py orphan_count`: no same-colour 8-neighbour, transparent counts as different |
| `orphans4` | pixel differs from all 4 of its neighbours |
| `jaggies` | `pipeline/render.py jaggy_count`: 1 px spikes in the row and column silhouette extents |
| `outline_hex` | the outline colour: `--outline-hex`, else the palette's `K`/`outline` entry, else the darkest used colour |
| `outline_cov` | fraction of silhouette-edge pixels drawn in the outline colour |
| `outline_gaps` | number of 8-connected runs of non-outline edge pixels. Note that sel-out styles (snowpeak) score low on purpose |
| `kcomp` | number of 8-connected components of the outline colour |
| `l_corners` | outline elbows with exactly 2 outline neighbours forming an L (pixel-perfect redundancy) |
| `doubles_2x2` | 2×2 outline blocks (thick lines) |
| `clusters`, `clusters_1px`, `clusters_le2px` | 4-connected same-colour clusters, and those of size 1 and ≤2 |
| `banding_1px` | heuristic: share of non-outline pixels that are a 1 px mid-step between two different, lightness-monotonic neighbours |
| `pillow_corr` | heuristic: correlation between L* and distance to the silhouette edge over interior pixels. Pillow shading pushes it toward +1 |

### seq (temporal)
Frames are compared on a fixed canvas, using a colour index shared across all frames. For each pair t→t+1, every pixel gets the best
local translation (|d| ≤ 2) of its 5×5 patch. Changes explained by that shift are *coherent*. Changes left over are *resid*.

| key | definition |
|---|---|
| `changed_mean` / `changed_max` | changed pixels / union figure, over pairs |
| `resid_mean` | changes no local shift explains |
| `flicker` | informational only (no gate). Pixel changes at t and reverts to its t-1 value by t+1 or t+2, per frame / figure area. Blinks and 2-key oscillation count |
| **`boil`** | an unexplained change at t on a patch that is **rigid** between t-1 and t+1 (or t+2), meaning it matches exactly under some shift. The region didn't really move or deform; the middle frame was redrawn noisily. Per frame / figure area |
| `shade_swap` | in-place, unexplained colour swaps between near colours (ΔE2000 < 12), for example a shade ramp redrawn per frame |
| `motion_px` | mean coherent displacement (px) per figure pixel |
| **`articulation`** | coherent moving pixels whose shift differs from the pair's dominant shift. This is motion that is *not* one rigid block slide. `articulation_per_s` divides by the cycle time, so a GIF with merged holds and the 1x strip agree |
| `rigid_share` | 1 − articulation / moving. Near 1 means the motion is one stamp sliding |
| `pose_range` | 1 − min silhouette IoU over all frame pairs |
| `holds` | number of identical consecutive pairs |
| silhouette jitter | `area_cv`, `centroid_std`, `feet_range` (bottom-row range = baseline), `top_range`, `height_range`, `width_range` |
| `head_range` | movement of the top-25 % centroid |
| `head_jerk`, `centroid_jerk` | mean second-difference magnitude, as an arc-smoothness proxy |
| `seam_changed`, `seam_resid` | the last→first transition |
| `seam_ratio` | seam change / largest in-cycle change |
| `static_changed` | with `--mask`: change rate outside the white "allowed to move" region |
| `flags` | see the thresholds below |

## Back-test

### Verification against metrics.py
- **15 sprites × 15 keys are equal.** The sprites are top1 vs illustration, masters vs illustration, and masters vs geo source, each in 5 views. The max |diff| is 5e-5, which is the JSON's 4-decimal rounding; in-process the values are bit-equal.
- The SSIM and CIEDE2000 ports equal skimage 0.26 exactly (random test, max diff 0.0).
- `masters vs geo src` NE (.950 / 7.784) equals `v2/m96/crit/final_gate.txt`. The other views changed after that gate (face2 / eyefix promotions).
- **`metrics_top.json` is stale.** It was written on 10-27. `top1/` was regenerated at 11:06 today, and its content matches git HEAD. For example, current SE ssim_b is .943, versus .956 in that file. Re-run metrics.py, or `pxeval still`, before quoting it.

| ssim_b / dE / face_ssim | S | SE | E | NE | N |
|---|---|---|---|---|---|
| top1 (E2@96) vs illustration | .961 / 8.98 / .75 | .943 / 9.62 / .78 | .966 / 8.73 / .48 | .951 / 8.56 / - | .965 / 7.21 / - |
| m96 masters vs illustration (turnE_final) | .852 / 15.05 / .25 | .806 / 16.36 / .46 | .764 / 18.29 / .19 | .748 / 15.90 / .14 | .886 / 11.07 / - |
| m96 masters vs geo/ warped source | .936 / 10.58 / .58 | .916 / 11.10 / .61 | .956 / 8.78 / .42 | .950 / 7.78 / - | .961 / 7.51 / - |
| top1 vs master (`vs_ref` ssim_b / same_px) | .869 / .65 | .762 / .53 | .788 / .53 | .732 / .54 | .883 / .71 |

Reading: the accepted masters are about 0.1 ssim_b *further* from the raw illustration than top1. That is deliberate (the geo re-proportioning:
slimmer, longer legs). **So fidelity for new work should be measured against the masters (or the geo/ source), not the raw turnE_final.**
Only 47–71 % of pixels are identical between top1 and the masters.

### Temporal (SE unless noted; full table in `tables.md`)
| clip | boil | shade_swap | articulation/s | rigid_share | feet_range | flags | critics / status |
|---|---|---|---|---|---|---|---|
| pilot anim96 idle (GIF / 1x strip) | .005 / .001 | .002 | 0.10 | .94 | 0 | STIFF | motion 5, "virtually zero motion" |
| pilot anim96 walk | **.031** | **.030** | 1.78 | .63 | 0 | BOILING SHADE_SWAP | motion 3, face/hair boil, no_boiling 4 |
| snowpeak S4_hd v1 idle ×8 dirs | .003–.007 | ≤.004 | 0.01–0.06 | .86–.97 | 0 | STIFF | shipped |
| snowpeak walk ×8 | .001–.017 | ≤.013 | 0.54–1.78 | .26–.69 | 1 | none | shipped |
| snowpeak run ×8 | .007–.017 | ≤.011 | 2.8–4.3 | .30–.41 | 1–2 | none | shipped |
| sw 64 px mocap / unarmed (walk, run, dash, jump, hurt) | .06–.18 | .004–.018 | 2.6–5.4 | .25–.36 | 0–19 | BOILING (+FEET) | 3D-guide pixels; "3D shimmer" |
| sw unarmed idle | .007 | .004 | 0.39 | .39 | 1 | none | Argon ~8 |
| sw mocap idle | .020 | .007 | 0.98 | .32 | 0 | BOILING (borderline: .0202) | pose tables |
| sw 3d_motion previews (AA renders, control) | .16–.29 | .13–.39 | 0.4–1.0 | ~.3 | 15–111 | everything | not pixel art; must fail |

Findings:
- **`boil` separates the redrawn pilot walk (.031) from every shipped snowpeak clip (≤ .017)**, with the gate at .02.
- `shade_swap` independently flags the pilot walk (.030 vs ≤ .013).
- The ranking agrees with the critics' no_boiling 4 and with "independent redraws boil".
- **"Frozen" vs "lively but stable".** The pilot idle is not boiling. Its motion is a single rigid 1 px block shift (rigid_share .94), with 2 of 6 pairs as exact holds. The result is 0.10 articulation/s, which is below the STIFF gate of 0.15/s. Lively-but-stable clips are above 0.5/s with boil ≤ .02 (snowpeak walk/run).
- Caveat: the shipped snowpeak idles (bob + blink only) are just as stiff (0.01–0.06/s). STIFF is a **warning**, not a failure. An idle may be minimal by design; the pilot's problem was that it read as frozen *next to* its T-pose sleeves.
- `flicker` (raw revert) is high for every legitimate walk and run (.1–.3), so it has no gate. Use `boil`.

## Proposed thresholds (`THRESH` in pxeval.py; `flags` in seq output)
| gate | proposed | basis |
|---|---|---|
| **boil** ≤ 0.02 (FAIL above; WARN above .015) | `BOILING` | snowpeak shipped max .017; pilot walk .031; 3D-guide pixels ≥ .06 |
| **shade_swap** ≤ 0.015 | `SHADE_SWAP` | snowpeak max .013; pilot walk .030 |
| articulation/s ≥ 0.15 (WARN) | `STIFF` | pilot idle 0.10; unarmed idle 0.39; walks ≥ 0.5. Falls back to 0.03 per transition when timing is unknown |
| motion_px < .02 and articulation < .005 | `FROZEN` (FAIL for non-idle clips) | none of the back-test clips trip it |
| feet_range ≤ 2 px (walk, run, idle only) | `FEET_JITTER` | snowpeak walk 1, run 2. Not meaningful for jump, dash or hurt |
| seam_ratio ≤ 1.5 (loops only) | `SEAM` | every looping back-test clip ≤ 1.14 |
| still, vs master: ssim_b ≥ .95, dE ≤ 10, sil ≥ .96 (proposed) | none | m96 masters vs their own geo source: ssim_b .92–.96, dE 7.5–11.1. top1 vs illustration: .94–.97 |
| still: off_palette_px = 0, orphans ≤ 15, outline_cov ≥ .98 (outlined styles) | none | top1 / masters: orphans 0–26, outline_cov .995–1.0 |

These were calibrated on one shipped project and one rejected pilot. Treat them as provisional and re-calibrate on the first
owner-verdicted clips from the current experiments.

## Known limitations
- Motion is canvas-relative: frames must share a canvas and pivot. Root motion baked into frames (dash, jump) inflates `feet_range` and `motion_px`.
- The 5×5, ±2 px matcher can't explain rotation or large (>2 px/frame) motion, so fast limbs land in `resid`. That is why `resid`/`flicker` aren't gated and `boil` demands rigidity across the bracket. A boiling region that also moves more than 2 px/frame can be under-counted.
- GIF decoding merges identical consecutive frames, which changes per-transition numbers. Prefer the 1x strip/sheet with `--ms`, or compare `*_per_s`.
- AA / rendered images (>256 colours) are handled, with background tolerance 24, but every pixel metric then reads as noise. Pixelize first.
- `vs_illus` material IoU, `line_f` and `face_ssim` use the swordswoman colour segmentation (seg.py). On other characters only `ssim`, `ssim_b`, `dE`, `sil` and `bloat` are meaningful.
- `banding_1px` and `pillow_corr` are uncalibrated heuristics. Report them, don't gate on them.
- There are no critic correlations beyond the pilot and the snowpeak release. Nothing here has been checked against an owner verdict on a motion clip yet.

## Reproduce
`.models/pixtools/venv/bin/python -I pipeline/tools/pxeval_backtest.py` runs in about 30 s and rewrites everything in this folder.
The metrics.py cross-check runs automatically when scikit-image is importable (pixtools venv).

> **Correction (lead, 2026-10-28):** `swordswoman/v2/pixelize/top1/` was *not* regenerated today. Its content is byte-identical to the
> committed version and to tag `pre-reorg-2026-10-28`; the 11:06 mtime comes from a `git checkout` restore. `metrics_top.json`
> (2026-10-27 12:03) predates the final top1 PNGs (2026-10-27 13:10), so it has been stale since Oct 27. Quoting fresh numbers is still right.
