# r13 Style Guide (AD)

Basis: FE GBA mugshots, Golden Sun, Pokemon DP/HGSS trainer art, Mother 3 (from memory; reference sites returned Cloudflare 403).
Swatch: `art/hand/S4/style/eye_brow_bang_study.pix`.

## 1. Canvases (integer scale only)
- **Bust 96x96**, the same slot as r12. Shown at x3 (288px) on a 390pt phone with room left for the text box; x2 small phones, x4 tablet. Head with hair is ~52px, brow to chin ~30px, crop at mid-chest.
- **Full body 96x160**: figure 150px tall, 5.5 heads (head about 27px). Shown at x2. Feet at y=154.

## 2. Head at bust size (3/4 view, facing screen-left)
- **Near eye 12x10** including lash and wing; iris 7x8. **Far eye 9x10** (iris 5 wide). Gap between eyes 7px. The top lash row sits at mid-head.
- **Upper lash:** ink. 2px thick at the centre, 3px at the outer corner, plus 1 wing pixel past the corner. Arc runs 5, then 9, then +2.
- **Lower lash:** 2-3px of `line_skin` on the outer third only.
- **Iris (top to bottom):** 2 rows `iris_0`, 3 rows `iris_1`, 2 rows `iris_2` glow. Rim is `iris_0`. Pupil is 3x3 ink tapering to 1px.
- **Catchlights:** a 2x2 white at the upper outer edge (light side) overlapping the pupil corner, plus 1px white at the lower inner edge. Sclera is 1px each side, `snow_2` under the lash.
- **Brow:** 1px `hair_1`, never ink. Runs 1-2-5-1 from outer to inner, 2px below the bang edge.
- **Nose:** 1-2px `skin_0` on the shadow side.
- **Mouth:** neutral is a 3px `line_skin` dash. Smile is a 1-3-1 arc. Open mouth is a `crn_1` interior up to 5x4 with a 2px `crn_2` tongue. No teeth.
- **Blush:** 3 diagonal 3px `red_2` hatches on a `skin_mid` patch about 9x3. Embarrassed: 4 hatches plus the far cheek.

## 3. Line art
- **Selective outline.** Each material's line is its darkest tone: hair `plum_0`, skin `line_skin`, coat `oat_0`, teal `teal_0`, trim `hair_1`. `#241628` is used only on the silhouette's shadow side (bottom/right).
- Lines are 1px everywhere except the upper lash. Interior lines (clump splits, folds) start at an edge and fade out; never draw a closed loop.
- **Curves use monotonic runs** (1-1-2-3-5-3-2-1-1). Banned: 2-1-2 runs, doubled corner pixels, stray stair notches.
- **AA:** at most 1 step, only on shallow dark-to-light curves (cheek, lash wing, crown). Never AA against transparency.
- In `pixgrid stats`, the only allowed orphans are catchlights, the nose and FX.

## 4. Shading
- Light comes from the upper-left front, always.
- Each material gets line + shadow + base. Only hair, teal and eyes get a highlight.
- **Hair:** shade as 4-7px clumps with tapered tips, not strands. The band highlight is one ring broken per clump: a 4-5px dash over a 2-3px dash. Bangs and side locks cast a 1px `skin_1` shadow on the skin.
- **Cloth:** coat folds are 2-4 `oat_1` wedges from the belt and elbows. The scarf gets 2-3 `teal_2` knit ridges per roll. No dithering.

## 5. Palette (26 of 32, from cw_oatmeal_portrait)
| material | line | shadow | base | hi |
|---|---|---|---|---|
| hair/brow | plum_0 #4A2448 | hair_1 #6E3C3A | hair_2 #A85A3A | hair_hi #D08658 |
| skin | line_skin #B0606A | skin_1 #EBA586, skin_0 #D07C74 | skin_2 #FCD6B4 | skin_mid #F6BCA6 (AA) |
| eye | ink #20223E | iris_0 #153E4E | iris_1 #2C9696 | iris_2 #86DCC6, snow_3 #FFFFFF, snow_2 #DFEAF6 |
| coat | oat_0 #957A80 | oat_1 #D2BFA4 | oat_2 #F2E6CE | |
| trim/boots | plum_0 | hair_1 | hair_2 | |
| teal | teal_0 #1C4C54 | teal_1 #2A8C8E | teal_2 #6ACBB6 | |
| tights | ink | char_1 #45435E | | |
| mouth/blush | crn_1 #8E2C4A | crn_2 #BA4A58 | red_2 #F06A58 | |
| buttons | gold_1 #E2A434 | | | |
| silhouette | outline #241628 | | | |

The 6 spare slots are for FX (`snow_1` tear, `red_1` anger mark) and backgrounds.

## 6. Don't (what r12 did) / Do
- DON'T use a uniform dark outline. r12 looked auto-traced.
- DON'T stripe the long hair. It read as corduroy; use 3-4 big clumps.
- DON'T draw 5-6px eyes with iris speckle. The faces were blank at x2.
- DON'T use solid red blush blobs, or a flat bang slab that hides the brows.
- DON'T leave a flat cream coat with no folds. Mittens should not be blobs, legs should not be sticks.
- DON'T make expressions by moving 2 pixels. Brow, lid and mouth change together.
- DO let eye shape and lash weight carry the emotion.
- DO keep clusters at 2px or more and give every pixel a job.
- DO check at x1 and x2 on both snow and dark backgrounds.
