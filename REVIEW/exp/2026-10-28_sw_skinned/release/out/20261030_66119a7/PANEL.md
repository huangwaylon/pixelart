# PANEL — build 20261030_66119a7 = ROUND 10 (R r13 SE/SW head +10° toward camera, F almond 3/4 eyes + closed-eye strokes + effort mouth + bigger S iris, P eye colours protected + specks, M arms + run legs)
A/B baselines: r9 = 20261029_ec4cac1 (ab_r9/), r4 head = hybrid 20261029_3831ac8 (ab_hyb/). One Opus pass, 3 roles (release/panel_ab.sh): panel/{ad,anim,game}_opus.txt.
The panel was told to judge faces visually: r13 turns the SE/SW head 10° more toward the camera, so similarity to the masters is not comparable.
Scores (B / r9 / r4head): AD 5 / 4 / 6, animation 6 / 5 / 6, game 6 / 5 / 7.

## Summary
**Front-face readability at 1x: B 5-6, target 8 not met** (r9 4-5, r4head 7-8).
- B is clearly better than r9. The SE/SW eyes are no longer glasses glyphs, and B is the most expressive of the three (hurt grimace, joyful closed eyes, blinks).
- B follows the head best (7-8) and has the most natural stance (7). All three critics call B the base to build on.
- What still holds it back: the r4 head still has the most readable front face. In B's SE/SW faces the far almond eye collapses into a dark "raccoon/panda" blob, the cheeks dither pink-brown, the near side lock and bangs fall over the near eye, and closed/squint eyes in profile read as a dark sunglasses bar.

Gates:
- limbs 47/48 (jump W, 1 frame SPLIT)
- bangs 48/48
- preview face integrity 15/30 (r9 14/30)
- posture torso 2/2, head pitch 2/2, head-forward 6/6
- feet 8/24
- boil 13/48, shade_swap 0/48
- GIF 48/48
- PZCLEAN ran 48/48

face_ssim (P, p10 set): .172. It is not comparable to round 9's .297 because of the r13 head turn (the r9 chain also scores .171 on r13), so it is not counted as a regression.

## Ranked fixes = ROUND 11 proposals
1. [F/P] SE/SW eyes: the far eye about 1 px narrower with a lighter iris tone. Both eyes about 20% larger, with a forced 1 px white catchlight and a 1 px sclera edge inside the protected eye mask, and a thinner top lash. Target: no dark eye blob at 1x.
2. [P] SE/SW cheeks: 2 skin tones plus a 1-2 px blush cluster per cheek and a skin brightness floor in the face. Drop isolated dark hair-shade pixels on face skin (idle S f06-08, SE f07-09).
3. [R] SE/SW side lock about 2 px back behind the cheek. Bang hem as one solid mass, 1 px above the eye line (not streaky strands). In run S, cap head pitch at ≤ 5° (the bangs cover the eyes in f1-2/f5-6).
4. [F] Closed and squint eyes in E/NE/W as a short 1 px curved lash with skin above (no temple bar). Effort/pained mouth as a 2-3 px shape drawn for 1x.
5. [M] Hurt: the guarding forearm below the chin in the front views, a 2-3 px hip shift and a squash. More follow-through on the bow tails and side locks; a 3 px landing squash in jump.
6. [P] Dash ghost trail behind the body, thinner. Near-white orphans left on the hair outline (run N/NE). boil 13/48, shade_swap 0/48. jump W limb SPLIT 1 frame.
