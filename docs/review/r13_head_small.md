# r13 Head at full-body scale (Pixel Artist 3), review-3 bow ruling applied

This is candidate C's face as a ~27 px head on 40x40 canvases, pasted into the 96x160 bodies at x+28.

**Files:** `art/hand/S4/head_small/head_{front,three_quarter,side,back}.pix`, plus `expr/{front,three_quarter}_*.pix` (10 each; each one `extends:` its base view).
**Review images:** `00_REVIEW/r13_anime_pixel/head_small/` (`heads_x4`, `head_*_x8`, `expressions_x4`, `expressions_x1x2`).

## Landmark rows (the same in every view)
| row | feature |
|---|---|
| y5 | crown |
| y14 | bang cut, 2 notches |
| y15 | 1 px `hair_1` brows |
| y18 | lash |
| y19-23 | iris ramp, 1 catchlight on the upper-left |
| y24 | lower lash |
| y25-26 | blush |
| y25 | nose (side view: y23) |
| y27-28 | 1-2-1 smile |
| y31 | chin |

## Bow (review 3: one size everywhere)
Each loop sticks out 5 px past the skull, the bow spans 38 px, and the loops sit at y6-15 with the outer tip lowest. `teal_2` is on the top edge only, with one `teal_0` crease.
- **Front:** fans at x1-5 and x34-38, y7-14. Each is 2 px tall at the hair and 8 px at the tip.
- **3/4:** 5x5 knot at x30-34, y8-12. The near-loop fan is at x35-39, y6-14; the far-loop nub is lowered behind the crown (y5-7).
- **Side:** the near loop faces us at x27-35, y6-15 (4 px past the back hair), with a pleat in the centre. No clipping.
- **Back:** fans at x1-38, y6-15, with a 5x5 knot at x17-21, y9-13. The rounded skull arc shows at x12-27, y5-8. Two tails run off the bottom edge.

## Side profile
- The forehead curves from x10 to x8.
- The nose is a 1 px upturned tip at (7,23), and the face steps back at y24.
- The mouth is a single `line_skin` pixel at (9,26).
- The chin is rounded at y27-31.
- The bang overhangs 2 px with a rounded tip (row 14 starts at x8). The hole at (16,15) is filled with `u`.
- There are no side expressions.

**3/4:** far eye 4 px (3 px iris), near eye 5 px, 2 px nose-bridge gap.

Every file uses 21 colours or fewer. The only orphan pixels are catchlights, the nose and FX.
