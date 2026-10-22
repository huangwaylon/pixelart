# r11 - S4 action set (draft 3: review rounds 1-2 fixes applied)

Review rounds 1-2 fixes applied. Round 2 results: animation director 11/13, art director 9/13, game director 7/13 approved. Since then: run strengthened, idle exit height fixed, throw release arm + snow streak, carry_throw crate hidden on release, crate rope tucked behind the head (props depth-split into _prop_back/_prop_front), lighter crate wood. Review round 3 is running.

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
