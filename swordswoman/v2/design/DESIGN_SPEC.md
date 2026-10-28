# DESIGN_SPEC: chibi swordswoman, Level D (FINAL, round 3, rev r3G-I), 2026-10-26

Chosen level: **D** (the ultra-flat simplification of Level C). Both critics picked D2 over C in round r3C
(crit/r3C_argon.txt, crit/r3C_opus.txt). The reference turnaround is in `v2/design/turnD/` (see the table at the end).
Level C (`v2/design/turn/`) is kept as a fallback. It has the same shapes plus lapel lines, blush and finger hands.

## Proportions (head units, H = head height including hair, without the bow)
- **Total height:** 2.4 H from the boot sole to the top of the hair. The bow adds 0.3 H, and the bow top is the height line.
- **Head:** 1.0 H tall and 1.05 H wide. It is a round bob silhouette and the widest part of the character.
- **Torso and dress:** from the chin to the hem is 0.85 H. The obi sits at 0.35 H below the chin and is 0.15 H tall.
- **Legs:** from the hem to the sole is 0.55 H. Boots are 0.2 H tall. Legs are slightly apart, with a clear gap.
- **Arms:** the hands end at hem height. In A-pose the arms are about 20° off the body.
- **At 48 px (bow included):**
  - bow: 4 px
  - head: 20 px
  - dress: 15 px
  - legs: 6 px
  - boots: 3 px

## Shapes
- **Hair:**
  - One solid dark bob ending at jaw level. It covers the ears in every view, including the sides.
  - The bangs are one blunt horizontal shelf ending just above the eyes.
  - Two tones only: base and shadow. No strand lines and no highlights.
- **Bun:** a small round ball at the crown, slightly back. It is about 0.25 H across.
- **Bow:**
  - **Placement is locked:** the bow is tied on the FRONT/top of the bun, centred on the crown, and the loops point left and right.
  - Front view: the bun peeks above or behind the knot.
  - Back view: the bun sits in front of the knot and the loops stick out both sides.
  - Side view: the bow is on top and the bun sits just behind it.
  - Shape: two plain loops and a knot, flat, with one shadow tone. It is 1.0 H wide. This is the silhouette ID.
- **Face:**
  - Big blue eyes set low, at 0.6 H from the top. They are simple ovals with one white glint.
  - The mouth is a tiny line.
  - No blush and no nose.
- **Dress:**
  - A short red kimono-dress with a symmetric trapezoid / A-line silhouette and a flared hem at mid-thigh.
  - The neck is a tiny V of skin. No lapel or crossover lines.
  - No seams, folds, pleats, slits, shorts or tails.
- **Sleeves:** plain wide bell sleeves that end above the wrist, with a darker red inside the opening.
- **Obi:** one plain dark band. On the back it is a plain band, with no knot or bow.
- **Hands:** small rounded mittens with no fingers. At pixel size they are 2×2 skin blocks.
- **Legs:** pale and bare.
- **Boots:** simple dark rounded short boots with no laces or soles detail.
- **Katana (optional):**
  - A straight thin blade, 2 px wide at sprite size.
  - A small round guard in a contrasting colour (hilt brown `k`).
  - A short dark hilt.
  - No scabbard and no hook guard.
  - It is held down at her side, angled out about 20–25°.

## Removed (vs. original and Level A)
- Detached sleeves.
- Asymmetric skirt tails and the wrap.
- Shorts.
- Collar wrap, high collar, choker and collar points.
- Lapel crossover lines.
- Straps, buckles and pouches.
- Pink scarf ribbons.
- Arm ornaments.
- Chest flower and cords.
- Strappy sandals.
- Blush.
- Hair strand highlights.
- Bow fold lines.
- Fingers.
- Dress folds and seams.
- The hook guard on the katana.

## Palette per material (aligned to v2/pixel/palette.json chars)
| material | light | base | shadow | deepest |
|---|---|---|---|---|
| outline (all) | | | | `#` #1a1220 |
| skin | `3` #fff0e4 (rare) | `2` #f8dac2 | `1` #d89a90 | |
| hair | `j` #695453 (avoid; no highlights in D) | `H` #3c3236 | `h` #281c26 | `#` |
| red dress + bow | `e` #e8604f (sparingly, bow top/shoulders) | `E` #c03a3c | `R` #84263e (under obi, sleeve insides) | `r` #4a1640 (hem underside) |
| obi | | `d` #44374a | `D` #2c202c | `#` |
| boots | | `d` #44374a | `D` #2c202c | `#` |
| eyes | `w` #eef0f5 glint | `I` #5580a2 | `i` #2a395a | |
| mouth | | `1` #d89a90 | | |
| katana | `w` #eef0f5 glint | `n` #a8b0c0 blade | `m` #5f6678 spine | |
| katana guard and hilt | | `k` #8a5a3a guard | `D` / `#` hilt wrap | |

Blush `p` is no longer used on the character. Dust `u` and `U` are for VFX only.
In practice this is about 17 colours on the character, and 2–3 per material.

## Pixel readability notes (probe: v2/design/pal_probe.py, 40/48 px, palette-locked)
- **Holds at 48 px:**
  - bow loops
  - bob mass
  - eyes
  - red dress block
  - obi band
  - boots
  - leg gap
- **Breaks in Level C:**
  - lapel lines turn into a checker
  - blush becomes 1 px mush
  - fingers become warts
  - hair strands become noise
  - a 1 px katana reads as a stick
- 40 px is the minimum, and only with hand cleanup. 48 px is recommended.

## Hand-fix rules for pixel artists (from final critiques r3E-r3I)
- **Bow:** give it a dark outline (`#` or `r`) and a light top (`e`). Otherwise it merges with the red dress at 40 px. In iso_N/iso_NE draw it as ONE bow (centre knot + two solid loops), not two red "ears".
- **Katana (pixel rule, implemented in `pal_probe.py --kat`, see `probe/D_turn_k_pal.png`):**
  - Blade = **2 px steel** (`w` upper px, `n` lower px) + **1 px dark `#` edge on the underside**, one clean stack per step along the blade; tip = 1 px `n` + `#`.
  - Hilt 2-3 px dark (`#`/`d`) + a 1-2 px `k` tsuba so the grip separates from hand and sleeve.
  - Same blade length in every view (foreshorten only in iso_S_k/iso_SE_k where it points toward camera). Keep it off the legs, angled outward.
  - Mirrored views (W/SW/NW/right_k) swap the katana hand. Accepted. left_k: hilt hand is the far hand -> partly hidden.
- **Side views (left/right/iso_E):** hand-place a 2 px eye, a 1 px nose bump and a 2x2 mitten. Draw the near sleeve as a darker-red block (`R`) hanging below the elbow, not a thin column; no vertical red stripe cutting the obi.
- **Back views:** separate obi from hair (obi `d`/`D`, hair `H`/`h`); sleeves one step darker than the skirt.
- **iso_S:** eyes 1 px clear of the bangs; bun shows only as a sliver behind the bow.
- **Head scale:** one shared head-height guide for all iso views (use iso_SE head size); iso_NE/iso_N heads run ~10% big.

## Camera and foreshortening authority
- **Design authority** (shapes, colours, proportions): the turnD drawings.
- **Camera authority** (exact 30 deg elevation, foreshortening, facing): 3D renders of the hy3d material-ID mesh `v2/hy3d/best/rest_mat.glb`: `v2/design/r3iso/c/mat_{S,SE,E,NE,N}.png` (flat palette colours; `matw_*` = same on white). Rendered with `VCOL=1 Blender -b -P r3iso/render_iso.py -- rest_mat.glb r3iso/c/mat 768`: ortho, el 30, az S 0 / SE -45 / E -90 / NE -135 / N 180. Older `r3iso/vc_*.png` (2mv4 mesh) are superseded.
  - r3G-I iso drawings were redrawn with these renders: iso_SE/E/NE/N now show the crown and downward-curving obi/hem. Residual: iso_S is slightly over-elevated (~45 deg; lower body stretched 1.8x by `r3iso/c/stretch.py` to restore leg length), iso_N is still mild (~15-20 deg).
  - When an iso drawing and its render disagree on foreshortening, follow the render: head top visible, obi and hem curve like ellipses, legs shortened.
- Directions: S faces the viewer; SE faces down-right; E faces right in profile; NE is a back 3/4 facing up-right; N is the back. Get W, SW and NW by mirroring.

## FINAL files (other strands read these)
| file | what |
|---|---|
| `turnD/front.png`, `left.png`, `back.png`, `right.png` | orthographic model views (right = mirror of left) |
| `turnD/iso_S.png`, `iso_SE.png`, `iso_E.png`, `iso_NE.png`, `iso_N.png` | in-game-camera design views |
| `turnD/front_k.png`, `left_k.png`, `back_k.png`, `right_k.png`, `iso_S_k.png`, `iso_SE_k.png`, `iso_E_k.png`, `iso_NE_k.png`, `iso_N_k.png` | katana variants |
| `turnD/sheet.png`, `turnD/sheet_k.png` | contact sheets |
| `r3iso/c/mat_*.png` | 30 deg camera/foreshortening guides (3D renders, hidden reference only) |
| `probe/D_turn_pal.png`, `probe/D_turn_k_pal.png` | 40/48 px palette-locked probes (katana probe uses the 2px+edge blade rule) |
Everything in `turnD/old/`, `turnD/r3/`, `r3iso/` (except `c/mat_*`), `r3k/`, `turn/` (Level C) is non-final.

## 48px PIXEL MASTERS (round 4, FINAL)
Hand-cleaned 64x64 masters (char-maps = source of truth, palette `v2/pixel/palette.json`, '.' transparent), Opus pixel artist + lint (`m48/tools/cm.py`).
- No katana: `m48/{S,E,NE,N}.txt` + `.png` (1x). Katana: `m48/{S,E,NE,N}_k.txt` + `.png`. SE = `v2/anim_redraw/m48/SE.png` (anchor; its boxy skull is being replaced by the v2/heads/ round head set).
- Contact sheet: `m48/sheet_4x.png` (1x + 4x row, guide lines: bow top row 10, skull top 16, chin 35, ground 60).
- Proportion lock (all views): bow top row 10-11, round head = shared superellipse template `m48/work/head_tpl.txt` (rows 16-35, centre col 30, max width 23; measured head_w 23-24, drift <=1px), obi rows 41-43, hem row ~50, boots to row 59 (ground), body centre col 30.
- Head: domed crown, hair bulging past the temples, cheeks taper to a small soft chin, bun always present; flat 2-tone hair (H/h/# only); bow flat with 1px # outline; anchor eye construction; mitten hands.
- Katana: her right hand (S: picture-left, E: near hand, NE/N: picture-right), held down/outward; 2px steel (w over n) + continuous # underside edge, k tsuba touching the fist, 2px dark pommel.
- Known residuals for the anim strands: S_k/NE_k blades not foreshortened; N_k blade angle = NE_k; NE_k grip mostly hidden by the fist; E bun/bow read as one mass at 1x.
