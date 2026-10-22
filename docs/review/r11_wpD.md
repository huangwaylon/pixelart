# r11 WP D: Throw / Air (S4_halfup_bow)

Every clip passes QA with 0 chain penetrations and 0 orphans. Builds: throw 9, carry_throw 2, fall 5, land 1.

## throw: 8 frames, 520 ms, one-shot, cancelable from f7
| # | frame | ms | intent |
|---|---|---|---|
| 1 | scoop | 70 | `prop_show`. Deep crouch, right hand low with the snowball. |
| 2 | pack | 60 | Both hands pat the ball at her chest. |
| 3 | cock | 100 | Torso turned 30° away, ball out to the side and back. The left arm points at the target. |
| 4 | step | 60 | Left-foot step (FK). The arm trails behind for a whip. |
| 5 | release | 50 | `throw_release`. Arm straight forward at shoulder height. |
| 6 | follow | 60 | Arm swings down across her body. |
| 7-8 | recover, ready | 60 each | Back to rest. |

The snowball is on `hand_R` at the plan's offset, radius 2.5. It is drawn on f1-f4 and hidden from f5.

## carry_throw: 6 frames, 480 ms, cancelable from f5
dip 90 (knees bend, crate sinks 0.8u, still clear of the head), push 70 (crate goes up and forward), release 60 (`throw_release`, arms thrust forward, step), follow 80, recover 90, ready 90. The crate prop is copied from `carry_idle.json` when the clip is generated. Once WP C freezes its spec, regenerate the clip so it picks that up.

## fall: loop, 4 frames x 80 ms, loop_seam 0.0
Arms flap out to the sides and the left arm leads the right by one key. Knees are tucked and pigeon-toed. A net head pitch of about 10° swings the pony back so it reads as lifted. z_px stays 0 because the engine owns height.

## land: derived from jump_sc frames [9, 13]
touchdown, hop, plop, settle, ready; 290 ms; `land` event on f1.

## Known issues
- **Overhand cock.** The head is huge next to an 11.5u arm, so a high cock gets hidden by the head or pony in many directions. The cock is therefore side/back at chest-to-shoulder height. Snowball pixels at the cock are 4-8 in most views, but only 0-3 in W and SW (the far side, behind the pony).
- **Release in NW.** The forward-right arm points straight away from the camera, so it is hidden in NW.
- **Fall arms in E/W.** The flaps are mostly in depth, so they read weakly from the side.
- **Land cancel window.** The derived clip inherits jump_sc's `cancelable` on hop, so cancel opens at f2 rather than the plan's f3. A derived clip can't patch individual frames.

Generator scripts are in /tmp/wpd/gen/*_gen.py (outside the repo).
