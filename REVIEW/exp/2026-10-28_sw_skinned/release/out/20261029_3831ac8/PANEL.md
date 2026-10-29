# PANEL — build 20261029_3831ac8 = ROUND 7a HYBRID "current best"
Head = round-4 pipeline: R's archived r7 rig (rig/work/rig_r7.blend) with its projected master head pass (render/r_tex_head.tex_head)
plus F's 2D face_layer on the 3D anchors (face/f_render.py + face/face_layer.py, archived). Body, motion and stance = round 5:
M's 07:55 bake (body bones identical in r7 and r8b) through P's current chain. No new critic pass, to save cost. The round-4 vs round-5 panel is in
../20261029_29614c2/PANEL.md: the r4 head was preferred (on-model 7 vs 3) and the r5 stance was preferred.

## Summary
Hybrid current best: **best head = r4** (projected master + face parts), **best body/stance = r5** (M's round-5 bake). Posture gates hold on the
r7 rig: torso 2/2, head pitch 2/2, head-forward 6/6 (E min +0.3..+1.1 px; r8b had +1.8..+2.6, because r7's neck sits a little further back).
Gates: boil 12/48, shade_swap 0/48, limbs 35/48, GIF 48/48. Bangs 28/48 is measured on the r7 hull's matid, not on the projected master pixels.
Superseded when the round-7 illustration-textured head lands.

## Ranked fixes
See ../20261029_29614c2/PANEL.md and the ROUND 6/7 lists in CONTRACT.md (the body issues are the same: limbs, shade_swap, hurt/dash arms, idle timing).
