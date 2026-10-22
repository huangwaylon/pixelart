# r11 WP A: Locomotion (idle, walk, run)

All three are 8-dir loops. QA PASS on the repo pipeline: penetrations 0, loop seam 0.0 px, orphans 0, height delta 1/3/1 px. Review copies: `00_REVIEW/r11_actions/{idle,walk,run}/`.

## idle (8 f / 1600 ms, planted)
| f | name | ms | intent |
|---|---|---|---|
| 1 | rest | 220 | exhaled |
| 2-3 | inhale, inhale_top | 220/200 | rise (squash 1.022), shoulders open, chin up |
| 4 | hold_shift | 200 | weight shift (lean 1.8), head counter-rolls |
| 5 | exhale | 200 | settle down |
| 6 | blink | 120 | half-lid `determined` cel |
| 7-8 | settle, settle_b | 220 | lean overshoots, ponytail swings back |

## walk (8 f / 800 ms, 100 ms each)
contact_L (footstep_L), down_L, pass_L, up_L, then a mirrored half (footstep_R on f5).
- Legs are FK, solved offline from foot paths: heel strike, toe-off, swing lift.
- About 1 px bob, knees-in cross-over steps.
- Arms swing about ±24°, one frame behind the legs. The head cancels the shoulder twist.

## run (8 f / 560 ms, 70 ms each)
contact, down, push, flight per side. footstep_L on f1, footstep_R on f5.
- Spine tilt 11-15.
- Head counter-tilts so the face stays visible.
- About 1.7 px bob. Both feet are off the ground on f4/f8.
- Arms pump with bent elbows, drive knee on push.

## Engine speed (feet match the ground)
- Walk: 21.5 world u/s, about 16 px/s in E/W.
- Run: 41 u/s, about 31 px/s.

## Known issues
- Chains are simulated in place, so the ponytail and scarf cannot trail. The lean and bob stand in for it. Needs a chain wind or velocity term.
- There is no closed-eye cel: face.py rejects unknown expressions, so the blink uses the half-lid.
- The coat is rigid. On drive-knee frames (S/SE) a 1 px cream thigh shows under the hem.
- The leg solver lives in `/tmp/wpA/` and is not in the repo. The JSON is the source.

## Round 1 fixes
All three rebuilt on the repo pipeline: QA PASS, 0 penetrations, loop seam 0.4 / 0.04 / 0.0 px (idle/walk/run).
- **idle:** f6 uses the engine `blink` cel at 80 ms; the other frames use `smile`. E eye is now constant: 4 ink + 1 catchlight on every frame. Body bob is 0 or exactly 1 px (drop 0/1.387, squash 1), with head pitch held constant. Arms are fixed at (20, 18, 34), so the mitten sits clear of the coat front and the dark-teal hip speck is gone.
- **run:** trail_wind 1000, so the ponytail and scarf now trail.
  - Spine tilt 15 on contact/down, head -10 (net 5). E/W eye visible on every frame (4+ ink px).
  - Squash 0.96 on down, 1.04 on flight. Ankle targets are pre-compensated for the squash pivot, so feet stay grounded.
  - Head centre sits 1.8-2.5 px ahead of the hips in E/W and 1.2-2.0 in SE/SW.
  - Flight foot spread is 8.5 px (+2.4) against 6.4 for walk. Arm pump ±60/50 with push-frame spread 28 to clear the torso.
  - engine_notes: about 53 u/s, roughly 40 px/s in E/W.
- **walk:** trail_wind 300, engine_notes added. Footsteps stay on f1/f5 in walk and run.

## Round 2 fixes
Idle and run rebuilt: QA PASS, 0 penetrations, loop seam 0.4 / 0.0 px.
- **idle exit pop:** f1 `rest` now sits at the ready height (drop 0; f1-f4 high, f5-f8 one px lower). The silhouette top of idle f1 matches the last frame of jump_sc, land, throw and carry_throw within 1 px in all 8 directions. Before this, W/NW were off by 2 px.
- **run:** spine tilt 19-21 with head -15 to -16, so the net head pitch stays at 5 or less and the E/W eye stays visible (4-9 ink px on every frame).
  - Head centre is 2.8-3.2 px ahead of the hips in E/W and 1.8-2.5 in SE/SW (round 1: 1.8-2.5 and 1.2-2.0).
  - Foot spread is 10.6 px on flight (+2.1) and 7.6 on push (+2.1). Walk's widest is 6.4.
  - Push-frame arm spread is 30/34 with raise +46/-56, so both elbows clear the torso. Arm pump on contact/flight is ±56-64.
  - Stance travel is longer: about 60 u/s, roughly 45 px/s in E/W (in engine_notes).
