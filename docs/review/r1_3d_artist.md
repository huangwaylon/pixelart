# R1 review: 3D Artist / Animator (jump)

## Verdict
Anticipation (dip into crouch: a forward C-curve, arms swept back) and landing (0.76 squash, 24 degrees of tilt) read well. Launch is a stiff "I". Rise, rise_high and apex keep the arms at 160-172, so the mittens hide behind the head from this camera, and the three frames share one silhouette. The apex tuck vanishes under the parka, and the 3-degree lean is invisible. Fall reads as a T-pose in S/N. The z arc is fine. Half head squash (about 0.87 on land) is acceptable. The frames sum to **850 ms**, but 840 is locked.

Secondary motion barely reads. The chains are near critical damping (scarf zeta ~1.1, braids ~0.7, pom ~0.65), so there is no flick. The pom never clears the beanie, and the scarf tails stay inside the parka silhouette.

## Edits: data/animations/jump.json
- launch: spine.tilt -6 -> -10, head.tilt 8 -> 12, leg_L/R.ankle 35 -> 45 (reverse-C line of action)
- rise: arm_L.raise 162 -> 150, arm_R.raise 158 -> 145, spread 22 -> 30
- rise_high: arm_L.raise 168 -> 140, arm_R.raise 165 -> 136, spread 34 -> 48
- apex: arm_L.raise 172 -> 132, arm_R.raise 170 -> 128, spread 46/44 -> 62/58, elbow 14/16 -> 22/26 (open V clear of the head); spine.lean 3 -> 7; head.roll -4 -> -9; leg_R.hip 28 -> 8, leg_R.knee 55 -> 18 (asymmetric)
- fall: arm_L raise 105 -> 115, spread 68 -> 54, elbow 15 -> 32; arm_R raise 100 -> 95, spread 66 -> 58, elbow 15 -> 26; z_px 18 -> 17
- drop: z_px 9 -> 8; leg_L/R.ankle 15 -> 22
- crouch: head.tilt -20 -> -24; ms 80 -> 90
- land: head.tilt -10 -> -16 (face stays visible in S under 24 degrees of spine tilt)
- dip: ms 50 -> 40
- ready: ms 100 -> 90 (total = 840)

## Edits: data/character.json chains
- pom: seg_len 2.4 -> 3.2, stiffness 260 -> 140, damping 0.10 -> 0.035, gravity 300 -> 260
- braid_L/R: seg_len 3.3 -> 3.8, widths [2.1,1.8] -> [2.4,2.1], stiffness 140 -> 110, damping 0.08 -> 0.03, anchor x +/-8.0 -> +/-8.6
- scarf_front: seg_len 3.0 -> 3.6, widths [2.3,2.2,2.0] -> [2.8,2.6,2.3], thickness 1.0 -> 1.3, anchor [3.2,-0.6,4.4] -> [4.2,-0.6,4.6], rest_dir x 0.15 -> 0.35, damping 0.06 -> 0.02, stiffness 30 -> 22
- scarf_back: same seg_len/width/thickness/damping/stiffness changes; anchor x -3.6 -> -4.4, rest_dir x -0.25 -> -0.4
- Target lags: P 1, B 1.5, S 2-3 frames. Tails float up on fall (fall acceleration ~1100 > gravity 650) and slam down on land. Check collider pokes, and that each tip is within 1px of rest by ready.
