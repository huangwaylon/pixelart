# r11 Review 1: Game Director

Script: `/tmp/gd_r11/check_r11.py` (full output: `/tmp/gd_r11/report.txt`). It checks every clip's sheet JSON and PNG against `r11_action_set_plan.md`.

## Script results

| clip | result | failing checks |
|---|---|---|
| idle, walk, run, jump_sc, fall | PASS | - |
| climb, climb_top | PASS | - |
| land | FAIL 2 | cancel (opens at f2 / 70 ms; plan says f3 / 120 ms), `derivedFrom` missing |
| pick_up | FAIL 3 | `props[]` has 6 duplicate crate entries, no per-frame `prop.layer`, no `_prop` strip |
| carry_idle | FAIL 2 | no `prop.layer`, no `_prop` strip |
| carry_walk | FAIL 2 | no `prop.layer`, no `_prop` strip |
| throw | FAIL 2 | no `prop.layer`, no `_prop` strip |
| carry_throw | FAIL 2 | no `prop.layer`, no `_prop` strip |

These all passed:
- frame counts, total ms, durations in multiples of 10, loop flags
- every event on its planned frame
- direction sets
- 48x64 cells and pivot (24,57) everywhere
- PNG and strip grids
- release anchors in all 8 directions (`hand_R[*][4]`, `carry[*][2]`)
- climb `cycle_rise_px` 24; climb_top `root_px` decreasing steadily to (0,-30)
- feet on row 57 +/-1 in every grounded frame
- neutral-frame height within 1 px of idle (run within 2 px)

Warnings, no action needed:
- Throw and carry_throw step frames reach row 59. That is the step toward camera.
- pick_up f3 reaches row 61 because the baked crate sits in front of her.
- Chain pops are all intended pose changes:
  - fall to land: dtop 7, the touchdown squash
  - idle to throw: dtop 5, the scoop
  - carry_idle to carry_throw: dtop 4, the dip
  - walk to run: dbot 2
- The land, jump, throw, carry_throw and climb_top exits into idle all match within 1 px (IoU at least 0.93). pick_up to carry_idle matches within 2 px.

## Per clip

- **idle: APPROVE.**
- **walk: APPROVE.**
- **run: CHANGES.** At 4x on a phone it reads as a fast walk. The 8° lean isn't visible, the stride is about the same width as walk, and the arms don't pump. Widen the push and flight leg spread by 2-3 px. Add a visible forward lean (head 1-2 px ahead of the hips in E/W/SE/SW). Swing the elbows clear of the torso on push frames.
- **jump_sc, fall: APPROVE.**
- **land: CHANGES.** Either make f2 (hop) non-cancelable and set `inputLockEnd_ms` to 120, or change the plan to f2+. Emit `derivedFrom: {"clip":"jump_sc","frames":[9,13]}` so re-cuts track jump_sc.
- **climb: APPROVE.**
- **climb_top: APPROVE.** It hands off to idle with no pop.
- **pick_up: CHANGES.**
  - Collapse `props[]` to one crate declaration. Move per-frame offsets into a per-frame `prop` object.
  - The QA warning still stands: one frame uses 18 colours (limit is 16).
  - In E/W the crate reads as a tall thin column, not a box. Give it real depth so it looks like the same cube from every side.
- **carry_idle, carry_walk: CHANGES.**
  - Same E/W crate silhouette fix as pick_up.
  - In S/SW the crate's bottom edge sits on the hair line. Lift it 1-2 px so it clears the head (the "props never clip the head" gate).
  - The carry offset (0,17.8,0) doesn't match the plan's (0,3,1.5). Reconcile them in the frozen carry spec.
- **throw: CHANGES (data only).** The art reads well: the snowball shows at 4x, and the release pose is clear in all 8 directions.
- **carry_throw: CHANGES (data only).**

## Blocking issue for every prop clip

Props are baked into the body sheet. There is no `<clip>_prop.png`, and frames carry only `props:["name"]`, not `prop:{id,bone,visible,layer}`. That means:
- the engine can't hide the world crate and swap in a rock
- the engine can't order the prop front or back
- carry and snowball art can't be reused across clips

Fixes:
1. Export the prop strip on the same grid.
2. Render the body without the prop.
3. Emit a per-frame `prop` with `layer`.

Then re-run `check_r11.py`.
