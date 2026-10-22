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

## Round 1 fixes (AD review 1)

### Brows
- Now 2 px: an ink core with plum_0 tapers, and no skin underside (the arcs with a skin_1 underside read as glasses).
- They sit at y28-29, clear of the bang notches, which start at y30-31.
- Brow x positions follow A's eye anchors, so the turned face carries them.
- Angry far brow is a steep 3-row diagonal.

### Expressions
- **smile:** upturned plum 5 px mouth, lower lids up 1 row.
- **sad:** lids droop at the outer corner, tear drop below the near eye, plum frown with corners down.
- **worried:** iris hard to the right, zigzag mouth, sweat drop.
- **angry:** clenched tooth row. fx_anger is now 7x7 and floats in open space at (22,15).
- **determined:** lid lowered 2 rows, brows set 1 px lower and slanted, plum set mouth.
- **embarrassed:** 5-row red_2 hatch.
- **No blush:** neutral, determined, angry, surprised, worried and sad.

### Front bust
- Neutral mouth is a 3 px flat line. Smile mouth is a 4 px plum curve, with lids up and blush.
- New eyeBF_L/R cels: sclera on the outer side only, mirrored per eye, catchlight upper-left on both. This fixes the gaze drift.

### A's turned face
- Re-checked after A's anchor move: eyes now at x30 and x40.
- `gen` now writes only the brow, fx and sweat anchors. A owns all the others.

### Gate
Blind 1x tests, run by a fresh agent each time:
- Test 1: 8/10. Worried and embarrassed swapped.
- Test 2: 10/10, three low-confidence.
- Test 3: 10/10, 7 high and 3 med.

Every variant is at most 24 colours with fewer than 10 orphans.
