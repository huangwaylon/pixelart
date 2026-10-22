# r11 - S4 action set: APPROVED by all reviewers (v1)

4 review rounds. Art director, animation director and game director all approve all 13 clips. Engine-ready copy: releases/S4_actions_v1/ (body sheets + JSON, shadow/fx strips, prop_back/prop_front strips, shared prop definitions). Engine notes are in each <clip>_sheet.json (engine_notes, events, cancel windows, anchors, root_px, rise weights). Next: re-render on the high-detail 3D model.

| Clip (click for 8-dir GIF) | Frames / time | Dirs | Events | QA |
|---|---|---|---|---|
| [idle](idle/idle_8dir.gif) | 8 f / 1600 ms loop | 8 | - | PASS |
| [walk](walk/walk_8dir.gif) | 8 f / 800 ms loop | 8 | footstep_L, footstep_R | PASS |
| [run](run/run_8dir.gif) | 8 f / 560 ms loop | 8 | footstep_L, footstep_R | PASS |
| [jump_sc](jump_sc/jump_sc_8dir.gif) | 14 f / 840 ms | 8 | land, takeoff | PASS |
| [fall](fall/fall_8dir.gif) | 4 f / 320 ms loop | 8 | - | PASS |
| [land](land/land_8dir.gif) | 5 f / 290 ms | 8 | land | PASS |
| [climb](climb/climb_8dir.gif) | 8 f / 960 ms loop | 3 | grip_L, grip_R | PASS |
| [climb_top](climb_top/climb_top_8dir.gif) | 8 f / 720 ms | 3 | step_up | PASS |
| [pick_up](pick_up/pick_up_8dir.gif) | 9 f / 700 ms | 8 | grab | PASS |
| [carry_idle](carry_idle/carry_idle_8dir.gif) | 4 f / 800 ms loop | 8 | - | PASS |
| [carry_walk](carry_walk/carry_walk_8dir.gif) | 8 f / 960 ms loop | 8 | footstep_L, footstep_R | PASS |
| [throw](throw/throw_8dir.gif) | 8 f / 520 ms | 8 | prop_show, throw_release | PASS |
| [carry_throw](carry_throw/carry_throw_8dir.gif) | 6 f / 540 ms | 8 | throw_release | PASS |

Each folder has `<clip>_8dir_slow.gif` (slow motion), `<clip>_contact_sheet.png` (every frame x direction),
and the engine deliverable `<clip>_sheet.png` + `<clip>_sheet.json` (rows = directions, cols = frames).
