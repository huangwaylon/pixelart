# PANEL — build 20261028_854761b = ROUND 4 BASELINE (projected face + 2D face layer), 6 actions x 8 directions

Raw critiques: panel/ad_opus.txt (art director), panel/anim_opus.txt (animation director), panel/game_opus.txt (game director), panel/argon.txt.
Scores: Opus AD 4/10, Opus animation 5/10, Opus game 4/10, Argon 5/10 (AD 5 / anim 5 / game 5).

## Summary
Round-4 baseline (projected face), 8 directions: the panel scores it 4-5/10. All four critics name the same faults the owner did. In E/W/NE/NW the head sits jutted back, behind the neck. Idle and walk lean back. The measured posture gates agree: head forward is -2 to -7 px in E on every action, and idle torso pitch is -5 to -7° in the E projection. In S/SE/SW she reads as balding: a thin fringe with skin between the clumps and a high hairline (bangs gate: 23/43 clips clean, up to 24-30 skin px above the brow). The other faults are hurt/dash T-pose arms, 1-px stick legs in run, the dress/sleeve blob with shade-swap flicker, and run E/W and dash NE/NW/W missing because of the P crash.

## Ranked fixes (routed)
1. [R+M] Head forward over the neck: the head/neck pivot is about 2-4 px forward in the rest pose (R). Remove the head pitch-up and backward head offset in every action (M). Gate: head-forward ≥ 0 in every E frame. Currently 0/6 actions pass.
2. [M] Stance: in idle/walk, put the spine 2-4° forward, keep the head level, and keep the pelvis under the ribcage. The dash wind-up (-16°) and the jump apex (-12°) are less arched.
3. [R(+F)] Bangs: one full fringe down to the brows, with overlapping clumps and a dark hair cap under them. No skin between the clumps in S/SE/SW or through the side locks in NE/NW. Take the skin-tone highlight out of the crown.
4. [P] The pixel_chain.shape_fixes crash (empty skeleton row) drops run E, run W, dash NE, dash NW and dash W.
5. [M] Hurt and dash: the arms go out in a symmetric T. Make them asymmetric, with a guard and the shoulders up, and curl the torso away.
6. [P] Legs at 1x: run and jump legs become 1-px sticks or vanish behind the skirt (limb audit 25/43). Keep a 2-px minimum and the sock-top band and boot rim.
7. [P/R] Dress and sleeves read as a poncho blob, with blotchy dark-red patches and shade_swap at 1/43. Separate the sleeves from the torso with a line or value step, use a 3-tone ramp with no patches under 2 px, and narrow the waist and flare the hem (R).
8. [F→r5] The profile mouth and nose stick out past the head silhouette (idle E f06-f10, dash E f03-f05); toothy open mouths. Moot once the r5 3D face lands; recheck then.
