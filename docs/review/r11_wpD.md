# r11 WP D: Throw / Air (S4_halfup_bow)

All clips pass QA with 0 chain penetrations and 0 orphans.

## throw: 8 frames, 520 ms, cancelable from f7
| # | frame | ms | intent |
|---|---|---|---|
| 1 | scoop | 70 | `prop_show`. Deep crouch, hand low. |
| 2 | pack | 60 | Pats the ball at her chest. |
| 3 | cock | 100 | Torso turned 30° away, ball out side-back. Left arm aims. |
| 4 | step | 60 | Left-foot step; the arm trails (whip). |
| 5 | release | 50 | `throw_release`. Arm forward at shoulder height. |
| 6 | follow | 60 | Arm swings across her body. |
| 7-8 | recover, ready | 60 each | Back to rest. |

Snowball: on `hand_R`, offset (0,-1.6,0.7), radius 2.5, drawn on f1-f4.

## carry_throw: 6 frames, 480 ms, cancelable from f5
dip 90, push 70, release 60 (`throw_release`, arms thrust forward, step), follow 80, recover 90, ready 90.
- **Crate:** WP C's `carry_idle.json` `props[0]`, copied verbatim. `frames` is set to dip and push.
- **Dip:** uses C's hold pose (176 / 38 / elbow 12) and dips with the knees only.
- **Head clearance:** crate box vs the hair_cap shape. Dip 1.29, push 1.35; carry_idle measures 1.26-1.31.

## fall: loop, 4 x 80 ms, loop seam 0.0
Arms flap out to the sides, the left one key ahead of the right. Knees are tucked and pigeon-toed. Head pitched about 10° forward swings the pony back, so it reads as lifted. z_px stays 0 because the engine owns height.

## land: derived from jump_sc frames [9, 13]
touchdown, hop, plop, settle, ready; 290 ms; `land` on f1.

## Known issues
- **Throw cock:** the large head hides a high overhand cock, so the cock is low, out to the side and back. Snowball visibility is 4-8 px in most views but only 0-3 px in W/SW, behind the pony.
- **Release, NW:** the arm points away from the camera, so it is hidden.
- **Fall, E/W:** the arm flaps are mostly in depth and read weakly.
- **Land cancel:** a derived clip inherits hop's cancelable flag, so cancel opens at f2 instead of f3.
- **Crate, N/NE:** the crate draws over the hair top on screen. This is depth ordering only, the same as in carry_idle.

## Round 1 fixes
- **throw.**
  - Timing: scoop 60, step 50, release 80 (turn 34, arm_R spread 50), ready 50. Pack face is now determined.
  - Release now fires 270 ms after input. The arm reads in S, N and NW.
  - Prop: `{"ref": "snowball"}`, shown on f1-f4, then `throw_release` on f5.
- **carry_throw.**
  - Dip: 130 ms, pelvis 3.2, squash 0.94, head tilt -8.
  - Arm raise: 140 on release, 115 on follow (no more foreshortening in S). Follow is 100 ms.
  - Spawn: `throw_release` moved to push (f2), so the projectile spawns at the push anchor where the crate is drawn. Total 540 ms; cancel opens at f5.
  - Prop: `{"ref": "crate"}`.
  - Clearance: crate to bow is 7.5u in the dip versus 6-7.3u in carry_idle. On screen it overlaps the hair as much as carry_idle does.
- **fall.**
  - Flap keys follow the reviewer's spacing (50/82, 50/82, 105, 5), applied to both arms with L one key ahead.
  - Added `engine_notes`: on the jump_sc -> fall handoff, the engine must add the current z_px to world height.
- **land.** Override `hop: cancelable false`, so cancel opens at plop and `inputLockEnd_ms` is 120. The sheet now has `derivedFrom`.
- All four clips QA PASS.
- **Engine gaps:**
  - `frame_info` needs `name` next to `ref`, which I added.
  - The sheet-JSON `props` exports the unresolved entry, so `bone` and `offset` are missing.
