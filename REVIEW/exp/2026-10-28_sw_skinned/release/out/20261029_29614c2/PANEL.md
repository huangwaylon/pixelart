# PANEL — build 20261029_29614c2 (ROUND 5 pipeline: R r8b 3D head + F 3D face textures + M round-5 bake + P chain, no head special cases), 6 actions x 8 dirs
A/B baseline: release/out/20261028_854761b (round 4, projected face). Boards: ab/ab_heads_<act>.png (6x heads), ab/ab_{idle,walk}.png (3x).
Raw critiques: panel/ad_opus.txt, panel/anim_opus.txt (both with the A/B), panel/game_opus.txt. One Opus pass in 3 roles, no Argon (cost).
Scores B (round 5): AD 4/10, animation 4/10, game 4/10. A (round-4 baseline) on the same criteria: AD 5, animation 5.

## Summary
Round 5 is mixed and slightly worse overall. Both A/B critics prefer A's face.
- Wins: stance and head placement. The posture gates now pass 6/6, against 0/6 in round 4. Torso pitch is idle +0.3..+1.3°, walk +3.0..+3.6°. The head is +1.8..+2.6 px forward of the neck base in E on every action. Critics confirm she no longer leans back. The face now follows the head (AD 6->8, anim 6->7).
- Regressions: the 3D face texture turns to mush at 96 px: muddy grey eye blobs, brown speckle on the cheeks, and a face of only 1 eye pixel in profile. On-model drops 7->3 and readable at 1x 6-7->3-4. The N head reads as a pointed hood, with the bow slid to mid-head.
- Bangs: the critics split. AD calls them full or even heavy. Anim and game see bare forehead and temple wedges. The bangs gate backs anim and game, failing in every S/SE/SW clip with 84-164 skin px above the brow (temple wedges between the fringe and the side locks; E/W/N/NE/NW clean).
- Head still looks set back in profile: the gate passes, but the back-hair and bun mass sits behind the spine line.
- Unchanged: hurt and dash T-arms, legs splitting in run SE/SW and jump S (limbs 34/48), and shade_swap 0/48.

## Ranked fixes (routed) = ROUND 6 proposals
1. [F+P] Make the face survive pixelization. Use palette-exact face textures with no speckle; bigger, higher-contrast eyes (dark lash/pupil mass, 1 bright catchlight); a thin-feature or eye-priority rule in P's chain that applies to all materials (no orphans inside the face). Profile (E/W): add an eye, brow and mouth tick. Target: face readable at 1x ≥ the round-4 baseline.
2. [R] Bangs and temples: wrap the fringe and side locks over the temples so no skin wedge shows between them in S/SE/SW. Gate: 0 skin px above the brow line (now 28/48 clips pass, all failures S/SE/SW).
3. [R] Profile head mass: back hair and bun about 15% smaller and moved forward/up, so the face is about 40% of the head width in E/W. The gate passes; the look does not.
4. [R] N/NE/NW: round the crown (no hood/onion shape), put the bun back on top, and move the bow back up. Make S/SE the bow one connected shape with a knot (not two "mouse ears").
5. [M] Hurt S/N f01-f03 and dash S/N f08-f09: replace the T/flex arms with a crumple or guard for hurt, and a forward lean with trailing sleeves for dash. Bow and side locks: about 2 frames of lag with overshoot.
6. [P] Limbs: legs split or detach in run SE/SW, jump S/SW, dash S/SW and hurt S (limbs 34/48; hurt NE VANISHED 2/9). Sleeve/body inner outline in run NE/NW.
7. [M/P] Timing: idle mixes 300 ms holds with 79 ms frames (reads as a hiccup); run S feet drift 10 px. shade_swap fails 48/48 and boil 37/48 (run E/W/NE/NW .13-.15).
