# PANEL — build 20261029_ec4cac1 = ROUND 9 (F pixel-readable eye illustrations, R r12 fringe/turn/streak fixes, P limb rules after the cleanup, M drag/idle/heels)
A/B baselines: r8 = 20261029_a586104 (ab_r8/), r4 head = hybrid 20261029_3831ac8 (ab_hyb/). F's eye check: ab_eyes/ab_eyes_r9_vs_r7_idle.png, the same build
and passes, idle S/SE rendered once more with F's round-7 illustrations (face/illus/out_r7, via release/rl_r7eyes.py; R's files untouched).
One Opus pass, 3 roles: panel/{ad,anim,game}_opus.txt.
Scores (B / r8 / r4head): AD 5 / 4 / 6, animation 6 / 5 / 6, game 6 / 5 / 6.

## Summary
Round 9 targets:
- **Limbs: met.** 47/48 (r8 33/48, target ≥ 44). The one failure left is hurt E (arm/hand).
- **Front-face readability at 1x: not met.** B scores 6 against the target of 8. r8 was 4-5, r4head 7-8.

What changed:
- B is now level with or ahead of the r4 head on everything except front-face readability and on-model. It follows the head (8 vs 5), is more expressive (6-7 vs 5-7) and has full bangs.
- **F's eyes, r9 vs r7: r9 6/10 vs r7 4/10.** r9 reads better in S. In SE/SW the r9 near eye pixelizes into a hard rectangular ring that reads as glasses, and blinks leave lid fragments.

Gates:
- bangs 48/48
- preview face integrity 14/30 (r8 13/30)
- posture torso 2/2, head pitch 2/2, head-forward 6/6
- feet 8/24
- boil 13/48, shade_swap 0/48
- GIF 48/48
- PZCLEAN ran 48/48

## Ranked fixes = ROUND 10 proposals
1. [F] 3/4 (SE/SW) eye: a solid dark iris/lash wedge with a 1 px catchlight and no closed outline box, clipped at the head silhouette. Test it pixelized at 1x before baking. Add closed-eye illustrations drawn for 1x (a 2 px curved line), and a simple 2-3 px effort mouth.
2. [F/P] S/SW face: iris ≥ 3x4 px with a white catchlight; lift the skin one shade; blush one 2 px tone kept off the eye rows. Exempt the eye, brow and mouth pixels from the cleanup's palette merging (the general thin-feature rule).
3. [R] SE/SW head turn: about 10° back toward the camera (the face reads near-profile now) and the side locks pulled behind the cheek. Limit the idle E/NE look-back (f06-09) so an eye stays visible. Lift the fringe over the eyes on the S look-away (f06-09).
4. [P] Isolated light specks on the hair and cheek edges (boil 13/48, flicker). shade_swap 0/48.
5. [M] Arms swing out straight in jump f09-11, dash f05-09 and hurt N f02: bend the elbows, make the arms asymmetric, lag the arms. Run S/N legs merge at contact: splay 2-3 px.
6. [R] Face-integrity fails remain in the profiles (E/W cheek and jaw).
