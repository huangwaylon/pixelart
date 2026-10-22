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
