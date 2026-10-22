# r11 WP B: Vertical (climb, climb_top), Animator B

Files: `data/animations/climb.json`, `data/animations/climb_top.json`. Both are 48x64 cells with the pivot at (24,57), directions N/NE/NW. QA passes on both: 0 penetrations, 0 orphans, height delta ≤ 2, loop seam 0.0. Review output is published to `00_REVIEW/r11_actions/climb*/`.

## climb (loop, 8 x 120 ms = 960 ms, `cycle_rise_px: 24`, every frame cancelable)
| f | name | intent | events |
|---|---|---|---|
| 1 | grip_R | R hand high and out, L foot stepped high (knee out) | grip_R |
| 2 | pull_R1 | R elbow bends, L leg pushes | |
| 3 | pull_R2 | legs cross, body compressed (squash 0.97) | |
| 4 | swap_L | L hand travels up outside the head | |
| 5-8 | grip_L .. swap_R | mirror of f1-f4 | grip_L f5 |

Opposite hand and foot move together. Arms are spread 46-66° so the hands stay outside the large head; with fully vertical reaches the hands were lost behind the hair. The spine turns ±12° toward the reaching side, and the head tilts up and rolls, so the bow and ponytail sway every half-cycle. Knees are spread out (16-26°) so the steps show below the skirt.

## climb_top (one-shot, 8 x 90 ms = 720 ms, not cancelable)
root_px is the cumulative offset from the clip start.
| f | name | root_px | intent |
|---|---|---|---|
| 1 | hang | 0,0 | both hands on the ledge lip |
| 2 | elbows | 0,-7 | elbows splayed wide on the ledge |
| 3 | press | 0,-13 | push down, R knee starts up |
| 4 | knee_up | 0,-19 | R knee on the ledge, body over it |
| 5 | roll_over | 0,-24 | weight rolls forward |
| 6 | step_up | 0,-28 | L leg comes up (event step_up) |
| 7 | rise | 0,-30 | planted, small crouch |
| 8 | stand | 0,-30 | rest pose, joyful face |

## Engine blockers (the shipping pipeline does not build these clips)
1. `fx.fx_frames` raises `KeyError` on any event not in `PUFFS` (grip_R, grip_L, step_up; footstep_L/R and throw_release will hit the same). Fix: `if ev in PUFFS`.
2. `qa.run_qa` foot-slide check raises `IndexError` when no frame is planted. All of climb is unplanted. Fix: skip the check when `planted` is empty.

I verified with a patched copy in `/tmp/wpB/proj` (the repo pipeline is not edited).

## Known issues
- NE/NW: the far arm is mostly hidden by the long hair mass. The near arm and the bow read.
- The chibi arms are short: the reaching hand peaks around head and bow height, not above the head.
- climb_top f4/f5: the raised knee is mostly covered by the skirt.
- `cycle_rise_px` is not exported to the sheet JSON (build.py meta).

## Round 1 fixes (climb; climb_top approved, rebuilt unchanged)
- grip_R/grip_L arms: raise 160 -> 172, spread 62 -> 50. In N the hand now angles up past the bow tail at ear height, so it reads as a reach instead of a wave.
- grip frames: spine tilt (toward the wall) 5 -> 10.
- NE f4 -> f5 bow jump: the cause was spine.turn, not head.turn. It jumped from +12 to -12 because swap_L carried the reaching-R sign. Turn now follows the reaching arm smoothly: +12, +6, 0, -6, -12, -6, 0, +6. Head turn stays 0. The bow now shifts at most 1-2 px between f4 and f5.
- Added `"rise_weights": [1,5,5,1,1,5,5,1]` (the body rises on the pull frames).
- Added `"engine_notes"`: the climb -> climb_top entry is allowed only on grip_R (f1) or grip_L (f5); drop is allowed on any frame. Both rise_weights and engine_notes appear in the sheet JSON, along with cycle_rise_px 24.
- The engine blockers above are fixed. Both clips now build with the repo pipeline and pass QA (climb seam 0.0, penetrations 0, orphans 0).
