# PANEL — build 20261029_d240736 = ROUND 7 (illustration-textured 3D head: R r10 + F illustrated expressions + P textured E2 path + M 09:10 bake)
A/B baseline A = hybrid 20261029_3831ac8 (the round-4 head pipeline: projected master + F's 2D face layer, on the same round-5 body/motion).
Boards: ab/ab_heads_<act>.png (6x), ab/ab_{idle,walk}.png (3x). Raw: panel/ad_opus.txt, panel/anim_opus.txt (with the A/B), panel/game_opus.txt (one Opus pass, 3 roles).
Scores: B (r7) AD 5, animation 6, game 5. A (r4 head) AD 5, animation 5.

## Summary
The round-7 head comes out mixed-to-better against the r4 head.
- B wins on structure: the face follows the head (A 5 -> B 8, both critics), bangs are full (5 -> 8-9; bangs gate 48/48, was 28/48), and head position improves (anim 5 -> 7).
- B loses on 1x face readability (7 -> 4): the fringe sits on the eyes so they become dark slits; blush and mouth vanish at 1x; the profile skin is a flat peach blob; white speck pixels show on the hair in N/NE/NW.
- On-model and expressive are about even.
- Other gates: limbs 44/48 (was 35), posture 2/2 + 2/2 + 6/6 (E head-forward +1.8..+2.6 px), boil 13/48, shade_swap 0/48, GIF 48/48.
- The critics still see a slight chest arch in the idle E/W look beat (f05-f08) and a hurt that reads as an arm wave.
- AD's advice: keep the B geometry and fix the feature readability.

## Ranked fixes = ROUND 8 proposals
1. [F+R] Clear the eyes: lift the fringe texture/geometry about 1-2 px above the eye line in S/SE/SW. Make sure the illustrated eye whites, pupils, catchlight, blush and mouth survive at 1x.
2. [P] Protect the features within the textured E2 path, as a general rule (not a head case): eye white/pupil/mouth/blush keep a palette slot and the 1 px features stay. Remove near-white singletons on the hair (N/NE/NW speckle), and clamp hair to its 3-tone ramp.
3. [P] Profile skin: a selective outline or shade tone at the jaw/nose so the E/W face isn't a flat blob, and the mouth off the silhouette edge.
4. [M] Idle E/W look beat f05-f08: hold the torso at about +2° and turn the head on yaw only (the chest arches back now). Hurt: snap and recoil the torso, 2-3 px knockback, pained face held f01-f04. Walk: more bob, arm swing and foot lift.
5. [P/M] Run S/SE f00-f01: the back leg hides behind the front one; feet drift 9-10 px. Remaining limb fails: 4/48.
6. [P] shade_swap 0/48 (dress bands flip) and boil on run E/W/NE/NW .10-.14.
7. [R] Dress reads as a sack: obi colour, skirt flare, a 2 px sock band. SE/SW body yaw drifts toward S/W in walk/idle.
