# r10 Face designer: kawaii_v2 face model sheet

File: `data/faces/kawaii_v2.json`. Test variant: `F_test` (S4 + kawaii_v2), jump_sc, QA PASS.
Boards: `archive/snowpeak/boards_r04_r10/r10_face_sheet.png`, `r10_face_strip.png`, `r10_face_strip_8dir.png`.
E eye, C catchlight, B blush, M mouth.

```
FRONT origin (4,1)      neutral    smile      determined joyful     squint
row -1                  EEE...EEE  EEE...EEE  .........  .E.....E.  EE.....EE
row  0 (anchor col 4)   .CE...CE.  .CE...CE.  EEE...EEE  E.E...E.E  ..E...E..
row +1                  .EE...EE.  .EE...EE.  .EE...EE.  BB.MMM.BB  EE.....EE
row +2                  .BB...BB.  .BB.M.BB.  ....M....  ....M....  .BB.M.BB.

3/4 (facing right) origin (6,1)
row -1                  EEE.EE.    EEE.EE.    .......    .E...E.    EE...E.
row  0                  .CE.EE.    .CE.EE.    EEE.EE.    E.E.E..    ..E.E..
row +1                  .EE....    .EE....    .EE....    .BB.M..    EE...E.
row +2                  .BB....    .BB.M..    ....M..    ....M..    .BB.M..

PROFILE (facing right) origin (4,1)
row -1                  .EE..      .EE..      .....      ..E..      .E...
row  0                  .CE..      .CE..      .EE..      .E...      ..E..
row +1                  ..E..      ..E..      ..E..                 .E...
```

Rules:
- Front: mirrored eyes, 3 px gap, outward lash, catchlight top-left, 2 px blush under each iris, centred mouth.
- 3/4: full near eye; far eye 2x2, no lash or catchlight, at least 1 skin px from the edge. Blush under the near eye, mouth toward the far side. Mirrored catchlight sits on the back side, as in profile.
- Profile: eye column, catchlight behind, nose in front.
- One shape family: joyful = ^, squint = > <, determined = lowered lid.
- The front face is only reliably skin on rows -1..+2 (bangs cover -2). Crouch and landing frames checked.

Pipeline limits:
1. Despeckle runs after the cels and eats the 1 px skin margins beside the front eyes. Fix: protect skin inside the cel bbox.
2. The profile nose varies between 1 and 2 px with frac(ax). W f12 loses its catchlight. Fix: snap the profile eye to the front silhouette.
