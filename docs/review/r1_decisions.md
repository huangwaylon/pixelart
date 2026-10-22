# Round 1 — consolidated decisions (lead)
Inputs: r1_art_director.md, r1_3d_artist.md, r1_game_director.md

| # | Decision | Source |
|---|---|---|
| 1 | Character camera elevation 26.565 -> **18 deg** (world tiles/shadow stay 2:1) | AD+GD+3D unanimous |
| 2 | Timing **770 ms**: dip 40, crouch 70 (GD wanted 50, 3D 90), rebound 50, settle 60, ready 70. Airborne 110 ms. Frames 10-12 cancelable -> inputLockEnd 590 ms | GD vs 3D compromise |
| 3 | Air poses per 3D: reverse-C launch, open-V apex arms clear of head, asymmetric legs, softer uneven fall arms | 3D |
| 4 | Launch stretch capped 1.16 (cell clip) | GD |
| 5 | Model: smaller beanie (+cuff merged into hat group), separate pom ball, bangs L/R only, bigger braids sticking out, wider 4-seg scarf, chunkier boots, thicker hem, hood back | AD |
| 6 | Chains dynamics: low damping (0.02-0.035) so pom/braids/scarf overshoot and flick | 3D |
| 7 | Shading bands widened (less face shadow, lighter hair); scarf uses mustard_1..3 only | AD |
| 8 | Zero foot slide (legs keep x/z under squash when planted); orphan despeckle pass; `buildHash`, `inputLockEnd_ms` in JSON; greyscale silhouette check; expression crop centred on face | GD/AD/SE |
