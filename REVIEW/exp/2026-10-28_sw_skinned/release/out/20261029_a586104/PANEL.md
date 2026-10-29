# PANEL — build 20261029_a586104 = ROUND 8 (R r11 baked UV illustration head + fringe lift, M walk/idle/hurt re-bake, P chain + PZCLEAN)
A/B baselines: r7 = 20261029_d240736 (ab_r7/), r4 head = hybrid 20261029_3831ac8 (ab_hyb/). One Opus pass, 3 roles; raw text in panel/{ad,anim,game}_opus.txt.
Scores (B / r7 / r4head): AD 5 / 4 / 4, animation 5 / 5 / 6, game 5 / 5 / 6.

## Summary
Round 8 has the best head structurally:
- It stays locked to the head with the fewest smears (the "no smears in motion" score is 7-8 vs r7 5-6 and r4head 3-5).
- It has full bangs (8-9) and the most natural stance (7). The hurt reaction now reads as a guard plus recoil, not a T.

The r4 head (projected master + decals) still has the most readable, on-model face at 1x in the front views (8 vs 5 for B). In S/SE/SW, B's eyes come out as small sleepy slits under the fringe, with blotchy pink skin.
- Verdict: B is the base going forward. Move the r4-style face read (big master eyes, a flat 2-tone face) onto B's baked head.

Gates (B vs r7):
- bangs 48/48 vs 48/48
- preview face integrity (new) 13/30 vs 13/30 clips. The E/W profiles still show cheek/jaw streaks (walk E f3/f6, run E f2-6, hurt E f3-5).
- **limbs 33/48 vs 44/48** (regressed with PZCLEAN)
- boil 13/48 vs 13/48
- shade_swap 0/48 vs 0/48
- posture torso 2/2, head pitch 2/2, head-forward 6/6
- GIF 48/48
- PZCLEAN ran on 48/48 clips (8x colour frames present, 0 warnings).

## Ranked fixes = ROUND 9 proposals
1. [F+R] Front-view eyes: a neutral eye about 1.3x larger and open, with a clear highlight and a dark upper lash line in the illustration/UV texture. The narrowed eyes only on blink and pained frames.
2. [R] Lift the fringe another 1-2 px in the 3/4 views (SE/SW). With head yaw over ~20° it still covers the near eye (idle SE f01-02, walk SE f03-06). Add view-pick hysteresis so the NE/E face doesn't go blank (idle E/NE f06-10).
3. [P] Keep the face flat and readable: a 2-3 tone skin clamp and solid blush. The eye and mouth clusters must survive pz cleanup and despeckle.
4. [P] Limb regression 44→33/48 since PZCLEAN: the cleanup must respect the limb rules. Run the limb audit after it, or exempt limb cells.
5. [R] E/W profile cheek/jaw streaks: the face-integrity gate flags walk E f3/f6, run E f2-6, hurt E f3-5 and jump E f4/f13.
6. [P] Hair and bow highlight specks still flicker (N/NE run, E/NE idle f07-09); boil 13/48, shade_swap 0/48.
7. [M] Sleeve/skirt drag after the steps; a relaxed idle arm; heels pinned in idle E/W (feet 6/24); spread the run stride sideways in the diagonal views.
