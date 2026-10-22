# r12 Illustrator B: S4 expressions and front bust

- `S4/bust.json`: 10 variants.
- `S4/bust_front.json`: neutral and smile.
- New cels in `S4/face/`: brows, eyes, mouths, heavy blush, `sweat_drop`, `fx_anger`.
- Renders: `00_REVIEW/r12_illustration/expressions/`. Every variant uses 18-24 colours, with 0 overrides.

## Rules kept
- Eye construction matches the model sheet: near 10x12, far 7x12, 2-row ink lash, teal iris ramp, catchlight upper-left, line_skin lower lid.
- Expressions change only lids, iris position and size, and highlights. Anchors, eye spacing and face shape are fixed.
- Blush is always hatched, never solid.

## Brows over bangs
- The bangs reach the eye line, so the brows sit on the hair: a plum_0 stroke over a 1 px skin_1 underside.
- I tested 6 halo options. The underside alone read best at 1x.
- Height is y31 on the 3/4 bust and y30 on the front, above the bang notches.

## Expressions
- **laugh:** ∩ eyes, dark D mouth with tongue
- **surprised:** small iris with white below, "o" mouth
- **sad:** inner brows up, wet highlights, frown
- **angry:** inner brows down, slanted lid, pout, anger vein
- **embarrassed:** heavy hatching, averted eyes, wavy mouth, sweat drop
- **determined:** lowered flat lid, set mouth
- **worried:** inner brows up, glancing aside
- **content:** ‿ eyes, soft smile

## Front bust
- Model-sheet front panel, scaled with the same transform as the 3/4 bust (x1.32).
- Eyes 4 px apart, mirrored, with the catchlight kept upper-left.

## 7 passes
- halo tests
- surprised ring removed
- plum mouth interiors (crn_1 read as lipstick)
- blush kept inside the face
- front eyes off the silhouette
- brows raised 1 px
- embarrassed whites reduced
