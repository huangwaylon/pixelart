# r13 dialogue busts (lead pixel artist)

Sources are in `art/hand/S4/bust/`: `bust_base.pix` plus `01_neutral` to `10_content.pix`. Each expression is `extends: bust_base.pix` with `patch:` blocks only.
Hand-typed runs and blocks live in `pipeline/tools/r13_bust/`. Nothing is traced.
Output goes to `00_REVIEW/r13_anime_pixel/bust/`:
- sheets: `bust_sheet_x3.png`, `bust_sheet_x1.png`
- one render per bust: `*_x6.png`
- engine files: `bust_spritesheet.png` (960x96, transparent) and `.json`

## Base (96x96, from C)
- C's face is kept. The bang is lifted so the 1px `hair_1` brows show, and it keeps 2 notches.
- Eyes follow the style guide (pupil, catchlights, sclera, tare-me droop). Near eye 10 px, far 8 px.
- Added hair: clumped bangs, side locks to the collarbone, back hair, and a ponytail behind the head.
- Added clothes: a double-wrap scarf with the tail on her left, and a coat with a Peter Pan collar, buttons, folds and a bust curve.
- **Bow (review 1):** tied at the back of the skull, with puffy loops.
  - The far loop is pinched to 6 rows at the knot and is 22 rows tall at its tip.
  - The near loop peeks over the crown.
  - Two swallowtail tails hang down.
- 27 colours. The only orphans are catchlights, the nose and FX.

## Expressions
Brows, lids and mouth change together, following the bible. FX:
- surprised: ticks
- sad: tear
- angry: vein and a puffed cheek
- embarrassed: nose blush and steam
- worried: sweat drop
- determined: star catchlight and a sparkle

## Blind tests
Six rounds, fresh agent and shuffle each time, unlabeled 1x+2x images. **Every round scored 10/10.** The final round had 6 high-confidence and 4 medium-confidence answers.

Fixes made between rounds:
- worried: added a sideways glance and a bigger sweat drop
- smile: squinting lids
- determined: heavier brow, firm mouth, sparkle

Closest pairs: smile vs content, determined vs neutral.
