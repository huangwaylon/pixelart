# r11 Review 1: Animation (S4_halfup_bow)

Reviewed from contact sheets, clip JSON and WP notes. Across all clips: hair/scarf chains never trail (engine needs a velocity term).

## Verdicts
- **idle: APPROVE.** Breath and seam are clean. blink: 120 -> 80 ms (the half-lid reads as a frown).
- **walk: APPROVE.** Clean opposite arm/leg swing and bob, no hitch.
- **run: CHANGES.** Too close to walk in S/N, no squash.
  - down_*: squash 1.0 -> 0.96
  - flight_*: squash 1.0 -> 1.04
  - contact_*: spine.tilt 13 -> 15
- **jump_sc: APPROVE.** Minor: reach z_px 4 -> 2, so the fall speeds up into touchdown.
- **fall: CHANGES.** Arm spacing is uneven, and E/W barely read.
  - flap_top: spread 95 -> 82, raise 40 -> 50
  - flap_low: spread 68 -> 82, raise 60 -> 50
  - flap_up: raise 80 -> 105
  - flap_down: raise 20 -> 5
- **land: CHANGES.** Cancel opens on hop while airborne (z 2-3), so the sprite drops on cancel. Make cancel start at plop (`cancel_from: 2`, or an explicit clip).
- **climb: CHANGES.** The 24 px rise is linear, so she slides up during reaches. Add `rise_weights: [1,5,5,1,1,5,5,1]`.
  - grip_*: raise 160 -> 170, spread 62 -> 52 (hands peak at ear height)
- **climb_top: APPROVE.** Good root ease-out (7, 6, 6, 5, 4, 2, 0).
- **pick_up: CHANGES.** clean -> press snaps the crate from chest to overhead in 70 ms with no drive.
  - insert `drive` after clean: 60 ms, raise 100, elbow 60, pelvis_drop 1.6, squash 0.96, face squint
  - press: squash 1.02 -> 1.05
- **carry_idle: APPROVE.**
- **carry_walk: CHANGES.** The crate moves rigidly with the body. Lag the elbow by one frame: contact 10, down 12, pass 15, up 11. down_*: squash 1.0 -> 0.98.
- **throw: CHANGES.** Release comes 290 ms after input, and the release frame (50 ms) is unreadable in S/N/NW.
  - scoop: 70 -> 60 ms
  - step: 60 -> 50 ms
  - release: 50 -> 80 ms, spine.turn 20 -> 34, arm_R.spread 32 -> 50
  - pack: face smile -> determined
  - add a 2-frame snow smear at hand_R
- **carry_throw: CHANGES.** The wind-up is too short for a heavy crate.
  - dip: 90 -> 130 ms, pelvis_drop 2.6 -> 3.2, squash 0.97 -> 0.94
  - follow: 80 -> 100 ms
  - spawn the projectile from the push-frame anchor so the crate doesn't pop

## Transitions
- **walk <-> run:** footsteps are on f1/f5 in both. Swap at the same frame index.
- **pick_up -> carry_idle:** start carry_idle at `low` to avoid a 1 px rebound.
- **carry_throw -> idle:** clean.
- **jump_sc -> fall:** jump_sc moves the sprite with z_px, but fall leaves height to the engine. At handoff the runtime must add the current z_px to world height, or the sprite pops up to 11 px.
- **climb -> climb_top:** enter only from grip_* frames, to avoid an arm pop.
- **climb_top -> idle:** clean.
