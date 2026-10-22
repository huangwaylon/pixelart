# r12: S4 as drawn anime pixel art (not derived from the 3D model)

Open these first:
* `model_sheet_x4.png`: the canonical model sheet (front, 3/4, back). Every portrait and pose derives from it.
* `expressions/bust_sheet_x4.png`: 96x96 dialogue bust (3/4), all 10 expressions built from the face-slot system (swappable eyes, brows, mouth and blush). Single frames: `expressions/bust_<expression>_x4.png`.
* `expressions/bust_front_sheet_x4.png`: front-facing bust.
* `bust_16_base_x4.png`: 16-colour (GBA budget) version of the neutral bust.
* `model_sheet_bgs_x2.png`: readability on snow, navy and a dialogue box.

How it's made:
1. Illustrators author vector shapes for the body, hair and bow.
2. Faces are hand-drawn pixel grids.
3. `pipeline/illustrate.py` rasterizes everything without anti-aliasing and applies pixel-perfect lines and sel-out.

Source: `data/illustrations/S4/`. Rebuild with `.venv/bin/python -m pipeline.illustrate data/illustrations/S4/bust.json --out 00_REVIEW/r12_illustration/expressions`.

Next: the full expression set (10) and full-body poses (8), then art director review rounds.

## Update: expressions and poses (round 1)
* `expressions/bust_sheet_x4.png`: 10 dialogue expressions (neutral, smile, laugh, surprised, sad, angry, embarrassed, determined, worried, content).
* `expressions/bust_front_sheet_x4.png`: front-facing bust (neutral and smile).
* `poses/poses_lineup_x3.png`: 8 full-body cut-scene poses (idle, wave, point, hands on hips, recoil, shy, shiver, cheer). The engine sheet is `poses/poses_spritesheet.png` + `.json`.

The art director's review 1 (`docs/review/r12_review1_AD.md`) asked for changes, and the illustrators are applying them now:
* fix a sel-out "zipper" on the coat edges;
* turn the 3/4 face properly;
* make expressions distinct at 1x (smile vs neutral, sad vs worried, angry vs determined);
* fix joint redraws on the poses;
* add the head/bow turnaround and a 16-colour bust.

## Update: round 2
The old top-level `bust_*.png` (all but `bust_16_*`), `bust_x4.png` and `bust_slots_x4.png` were stale copies and have been deleted. The current bust renders are in `expressions/`. Before/after crops for the round-2 fixes are in `fixes/r2_*.png`.
