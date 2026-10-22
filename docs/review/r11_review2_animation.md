# r11 Review 2: Animation (S4_halfup_bow)

Checked the current builds. Nothing rebuilt.

## Round-1 items
| clip | item | status |
|---|---|---|
| idle | blink 80 ms, real blink cel | FIXED |
| run | squash 0.96/1.04, tilt 15, trail_wind | FIXED |
| jump_sc | reach z_px 4 -> 2 | NOT FIXED (optional) |
| fall | even flap spacing, E/W raise | FIXED |
| land | cancel from plop | FIXED |
| climb | rise_weights, grip raise/spread, entry note | FIXED |
| pick_up | `drive` frame, press squash 1.05, hand-off to carry_idle | FIXED |
| carry_walk | elbow lag, squash 0.98 | FIXED |
| throw | timing (release at 270 ms), pack face | FIXED |
| throw | release readable in S/N/NW | NOT FIXED: arm still hidden on f5 in S, N and NW |
| throw | snow smear on `throw_release` | NOT FIXED: no entry in `fx.PUFFS` |
| carry_throw | dip 130 ms / pd 3.2 / sq 0.94, follow 100 | FIXED |
| transitions | jump_sc->fall z handoff, climb entry, walk/run phase | FIXED (engine_notes) |

## Verdicts
**APPROVE:** idle, walk, run, jump_sc, fall, land, climb, climb_top, pick_up, carry_idle, carry_walk.

**throw: CHANGES.** In S the arm points straight at the camera. The smear is now required.
- fx: add `throw_release` to PUFFS, or add a dedicated smear. 2 frames (80 ms), 3-4 white px arcing from shoulder to hand along the throw direction.
- release arm_R: raise -262 -> -250 (about 110 deg, slightly up), so the hand rises above the shoulder line in S/N.

**carry_throw: CHANGES (new).** `throw_release` moved to push, but the crate is still drawn on push (`frames: ["dip","push"]`). If the runtime spawns the projectile at frame start, two crates are visible for 70 ms. Pick one:
- (a) Move `throw_release` back to release (f3). Add `spawn_anchor_frame: "push"` so it spawns at the push carry anchor.
- (b) Keep it on push and add engine_notes: "spawn at end of event frame (+70 ms)".

## New observations (no action)
- idle: pelvis_drop is now binary (0 / 1.387), so the breath is a 1 px step rather than an ease. Acceptable at this size.
- The engine still ignores frame-level `prop` until `r11_wpC_frame_prop.patch` is applied. pick_up low frames depend on it.
