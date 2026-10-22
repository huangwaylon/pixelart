# Brief r11 — action set for S4 (animators)

Plan: docs/review/r11_action_set_plan.md (game director; read it — clips, frames, timing, events, props, cancel windows).
Character: `S4_halfup_bow` (do NOT edit it). Reference clip: data/animations/jump_sc.json (copy its structure:
frame_size [48,64], pivot [24,57], directions, qa block, rest pose; channel conventions in its "conventions").
User asks: expressive, well-animated motion; CONSISTENCY across 8 directions; nothing penetrates the body.

## New engine features (available now)
* `"loop": true` — seamless looping (last key interpolates into the first); hair/scarf/pony pre-rolled 2 cycles;
  QA metric `loop_seam_px` must be <= 1.0.
* `"props": [{"name": "snowball", "bone": "hand_R", "offset": [x,y,z], "radii": [r,r,r], "rot": [..],
  "material": "prop_snow" | "prop_wood" | "prop", "frames": ["frame_name", ...] or "all",
  "parts": [{"offset": [..], "radii": [..], "material": ".."}], "release_event": "throw_release"}]` — bone may be
  `hand_L`, `hand_R` or the virtual `carry` (midpoint of both hands, chest orientation). Props render in the sprite on
  the listed frames only; at the release event the engine spawns a projectile at `anchors.hand_R/carry[dir][frame]`
  (exported automatically in the sheet JSON).
* Per-frame `"root_px": [dx, dy]` (engine root motion, e.g. climb_top), `"events": [...]`, `"cancelable": true`.
* Derived clip: `{"name": "land", "derived": {"clip": "jump_sc", "frames": [9, 13]}}` (frames sliced from another clip).
* Directions subset: `"directions": ["N", "NE", "NW"]` for climbing.
* Walk/run legs: use `"plant": false` with FK hip/knee/ankle (planted IK keeps both feet fixed, wrong for steps);
  alternate legs, bob via pelvis_drop / squash, arm swing opposite to legs, spine tilt forward for run.

## Build & inspect
```
cd /Users/waylonhuang/Documents/other/pixelart
.venv/bin/python -m pipeline.build --variant S4_halfup_bow --anim <clip> --no-reference
# out/variants/S4_halfup_bow__<clip>/preview/<clip>_contact_sheet.png (crop with Pillow), <clip>_8dir.gif,
#   slowmo/, distance_test.png, qa_report.md, <clip>_sheet.json
.venv/bin/python -m pipeline.pixelreview --build out/variants/S4_halfup_bow__<clip> --dirs S SE E N --frames 1,3,5 --zoom 8
```
QA must PASS: chain_penetrations 0, loop_seam_px <= 1 (loops), margins, orphans 0, foot slide (planted frames).
Iterate >= 4 builds per clip: arcs, timing, spacing, weight, overlap of ponytail/bow tails/scarf/skirt, silhouette
readability in all 8 directions (hands not lost behind the head), cute/feminine character (knees-in, soft wrists).
Never edit pipeline/*.py, data/variants/*, data/palettes/*, or other packages' clip files.
Write `docs/review/r11_wp<X>.md` (<= 350 words): per clip frame table + intent + known issues. Return a short summary.
