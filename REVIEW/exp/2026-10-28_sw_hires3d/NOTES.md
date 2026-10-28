# HIRES3D: render rig H2 at 8x, then pixelize and fix (swordswoman, 2026-10-28)

**Hypothesis (owner):** render the 3D models at high resolution, then pixelate and fix. This should give better pixel art than the current
m96 masters, which are E2-pixelized illustrations plus polish.

**Verdict.**
- **Stills: rejected.** Every 3D candidate is clearly worse than the m96 master. The downscaler barely matters. The gap comes from the rig (pose, sash, skirt, torso, a placeholder face), and no downscaler can close it.
- **Animation underlay: promising.** Hi-res render, then cel + outline (or material vote), then k-centroid gives frames that are visibly steadier than the hand-redrawn pilot (Opus: consistency 7 vs about 4). But design fidelity is low (3.5/10). Use it as a guide or underlay only, after the rig fixes listed below.

## What was run (scripts/ — nothing outside this folder was modified)
- `scripts/hirender.py`: a Blender 5.2 script. It execs `v2/motion/scripts/mrender.py` from its source text (rig H2 + motion-strand springs, unmodified) with:
  - the resolution patched to CELL1×8, i.e. the 192 cell at 1536 px. The in-game 128 cell is crop 256..1280 = 1024 px, so 8 px per sprite px, same 30° ortho camera, PPU 52.608×8.
  - extra passes:
    - `guide` (matid, AA off)
    - `shade` (existing EEVEE toon + hull outline)
    - `lum` (white diffuse lit by the view's camera-relative sun, Raw, 16 bit)
    - `nrm` (camera-space normal)
    - `dep` (camera depth, 16 bit)
- `scripts/render.py ACT VIEWS`: builds jobs exactly like `frames_M.py render()` (act_M.json keys + tune.json post layer).
  - `rest` = the G96 calibration pose from `rigs/H2/calib_state.json` (the same pose as `rigs/H2/check/check_SE.png`).
  - Rendered: rest SE/E/S, walk SE/E/S (8 frames), run SE (8), idle SE (11). It takes about 1 s per frame for all 5 passes. Output in `big/` (132 MB).
- `scripts/hx.py`: styles, downscalers and the fix pass. It reuses `pzlib` and `pz.py` (kcentroid, pixeloe, snap, outline_sil, clean_orphans).
  - Styles:
    - `shade`: existing pass.
    - `cel`: per-material ramps from the locked palette (hair hHg, red REe, skin Ss, obi oOQ, socks Dd, boots hHg), 3 bands from the smoothed lum (σ = 5 hi-res px, normalised per material so nothing bleeds across materials), thresholds .22/.80 with per-material bias.
    - `celo`: cel + hi-res lines, about 6 px wide: an inner silhouette band, depth discontinuities on the far side, and material-group boundaries.
    - `flat`: matid colours.
  - Downscalers:
    - `kc`: E2 k-centroid, k = 3, line-aware, bilateral prefilter.
    - `area`: 8×8 box.
    - `paf`: Retro Diffusion pixel-art-fixer through `pipeline/tools/pixelfix.py --step 8 8`.
    - `poe`: PixelOE contrast, thickness 2.
    - `matv`: majority vote of material IDs per cell, then the cell's mean lum picks the palette band.
  - Fix:
    1. palette lock constrained to the cell's rig material ramp
    2. 1 px silhouette K
    3. sprite-level depth lines (cell median depth step > .035, K on the far side) for non-outlined styles
    4. orphan cleanup
    5. outline_sil again
    6. `postfix.py`: drop bare K crumbs, keep the largest component
  - `_hs` variants: the rig head cells (hair/skin/eyes/bow above the neck row) are cleared and `v2/m96/heads/<V>_neutral.txt` is pasted at its anchor plus the rig head offset relative to rest.
- Alignment: one integer shift per view from the rest frame, applied in hi-res so the 8 px grid is kept. Soles go to the master's bottom row and the feet centre to the master's feet centre. SE dx 2 dy 2.
- `scripts/run.py` (all methods × frames), `metr.py` (metrics.py vs the illustration + direct agreement with the master), `temporal.py`, `tlock.py`, `board.py`, `strip.py`, `gridgif.py`.
- **PixelOE (`poe`) is no longer reproducible.** It was run with `.models/pixelize/pixeloe/venv`, which is being deleted after this experiment. The other methods run on `.models/pixtools/venv` (numpy/scipy/opencv/pillow/skimage). The poe outputs on disk are kept.

## Numbers
### Stills vs the illustration (metrics.py) and vs the m96 master (`out/metrics.txt`, `out/metrics_<V>.json`)
The master is re-scored here against the same illustration with the same bbox mapping, so its absolute numbers are lower than in RESULTS.md. Compare rows within this table only.

| view | method | ssim_b | dE | sil | face_ssim | line_f | m_same (vs master) |
|---|---|---|---|---|---|---|---|
| SE | **m96 master** | **.674** | **21.5** | **.831** | **.314** | .775 | 1 |
| SE | shade_kc_hs | .391 | 35.2 | .627 | -.03 | .600 | .50 |
| SE | celo_kc_hs | .375 | 35.7 | .618 | -.03 | .604 | .54 |
| SE | matv_hs | .380 | 35.5 | .616 | -.04 | .574 | .55 |
| E | **m96 master** | **.764** | **18.3** | **.863** | .189 | .725 | 1 |
| E | shade_kc_hs | .679 | 21.9 | .824 | .248 | .709 | .68 |
| E | celo_kc_hs | .640 | 24.0 | .789 | .205 | .641 | .70 |
| S | **m96 master** | **.847** | **16.7** | **.885** | .244 | .856 | 1 |
| S | cel_kc_hs | .754 | 21.6 | .816 | .209 | .790 | .60 |
| S | celo_kc_hs | .745 | 22.0 | .813 | .219 | .798 | .59 |

- Downscaler spread within one style is ≤ .03 ssim_b, and the style spread is ≤ .05. The rig dominates.
- Without the head stamp, face_ssim is ≤ .2 and SE is negative. The rig face is a placeholder (blue blob eyes, sculpted bumps). The stamp adds 0.03–0.04 ssim_b and doubles m_same.

### Temporal (`out/temporal.txt`, `out/temporal_<clip>.json`)
- Static cells are cells whose 8×8 render block is unchanged between frames (same matid, |dlum| < .01). They are rare: walk_SE 5–57 per transition out of about 2700 figure px, idle 39–423. Under a 3D rig, almost nothing is pixel-static, because every part moves by sub-pixel amounts.
- **band_churn** = fraction of same-colour-class, non-K cells whose shade band changed between consecutive frames. It is computed from the sprites alone, so the pilot can be measured the same way.

| clip | shade_kc | cel_kc | celo_kc | celo_poe | matv | flat_kc | celo_kc_hs | animate96 pilot |
|---|---|---|---|---|---|---|---|---|
| walk_SE | .309 | .204 | **.173** | .170 | .173 | .045 (no shading) | .365 | .296 (6 fr) |
| walk_E | .379 | .254 | .227 | .235 | .240 | .082 | .340 | n/a |
| idle_SE | .138 | .097 | **.084** | .089 | .086 | .012 | .138 | .128 |

- Static-cell flicker rate (output changed on a render-static cell), walk_SE: shade_area .034, shade_kc .097, cel/matv .165, celo_kc .15.
  - Cel bands and lines depend on neighbourhood context, so a static cell can still flip.
- `tlock.py` (paste the previous output back on render-static cells) brings flicker to .005, but band churn only falls .365 → .357, because there are so few static cells.
- `_hs` raises churn: the rigid stamp jumps 1 px on head-offset rounding and doesn't turn with the body. The metric counts that as churn.

## Critiques (`crit/`)
- **Argon** (`crit/argon_SE.txt`, 8.5 KB). Best still is matv_hs / celo_poe_hs at 3.5 (master = 7); walk consistency 4.5; walk design fidelity 2.5. Problems it names:
  - T-pose arms
  - wasp waist and tutu skirt
  - long legs
  - V-neck skin triangle
  - giraffe neck at the stamp seam
  - missing or thin obi in shade/kc
  - k-centroid banding blotches on the skirt
  - hands that flicker or vanish across walk frames
  - leg overlap merging into a black mass

  Its verdict: "Hell no", 3D doesn't beat the illustration route. Use 3D only as an underdrawing.
- **Opus** (`crit/opus.txt`, non-empty; only the usual zle warnings). Best still is celo_kc_hs at 4.5 (celo_poe 4, cel_kc 4). Walk consistency is **7 for the 3D frames vs about 4 for the pilot**; walk design fidelity is 3.5 (pilot about 7). Problems it names:
  - sleeves out like wings
  - 1–2 px sash, missing in E
  - bell skirt with a bare thigh band
  - "Ƨ" thigh glitch in E
  - stride too big (reads as a run)
  - static head stamp sliding on the neck

  Best combination: **celo + kc + head stamp**. Verdict: does not beat the illustration route for stills; keep it as a motion underlay after rig fixes.

## Verdict / recommendation
1. **Don't replace the m96 masters** with 3D renders. Fidelity is −.08 to −.30 ssim_b and −.04 to −.21 sil versus the master, in every view and with every method.
2. **Best 3D chain: celo** (cel bands from the locked palette + hi-res depth/material lines) **→ E2 k-centroid** (or matv) **→ rig-material palette lock + sprite fix → head stamp.**
   - matv is the cheapest and most deterministic. It ties on churn and has few orphans (2–11).
   - shade (the existing toon pass) is the worst for churn (.31–.38).
   - pixel-art-fixer and PixelOE add nothing over kc or area on a known grid.
3. **The animation question.** Hi-res 3D gives frames that are coherent from one frame to the next:
   - walk churn: .17 vs the pilot's .30
   - idle churn: .084 vs .128
   - Opus consistency: 7 vs 4

   But the rig is off-model. It is worth pursuing only as a pixel underlay feeding the masked edit-mode redraw (team plan item 2). It needs rig fixes first:
   - arms-down rest pose
   - a wider lavender obi part
   - a longer, straight skirt with the red stocking band
   - no waist cinch
   - a smaller walk stride
   - a head that tilts and turns (heads96 layers), not a rigid stamp
4. The 3D render also gives a free static mask (render-unchanged cells) for paste-back. Under real motion it covers less than 2 % of the walk, so it does not fix boiling by itself.

## Files
- Boards:
  - `boards/rest_{SE,E,S}_hs.png`: illustration | master | 9 candidates, 4x + 1x strip
  - `boards/rest_SE_all_raw.png`: all 14 raw methods
  - `boards/strip_{walk_SE,walk_E,run_SE,idle_SE}.png`
- GIFs:
  - `gifs/grid_<clip>.gif`: shade_kc_hs | cel_kc_hs | celo_poe_hs | matv_hs | celo_kc raw, 3x
  - `gifs/walk_SE_celo_kc_hs_4x.gif`
  - `gifs/<clip>_<method>.gif`: every method, 4x
- Grids: `out/<clip>/<method>/fNN.{txt,png,json}` (pzlib format, metrics.py-ready). Hi-res passes: `big/<clip>/`.
