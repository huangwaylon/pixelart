# r13 Head at full-body scale (Pixel Artist 3), review-4 bow applied

This is candidate C's face as a ~27 px head. **The canvas is now 44x40, so paste at x+26** (turnaround x = head_small x + 26). Rows are unchanged; all x values below are 44-canvas.

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

## Bow (review 4: puffy teardrops, 42 px)
- **Back (master):** loops x1-18 and x24-42, 13 rows at the outer end (y4-16), pinching to 5 rows (y9-13) at a 5x7 knot (x19-23, y8-14). Corners are rounded and the bottom droops. Each loop has a 3x3 `teal_0` pocket (x4-6 / x37-39, y9-11) and a crease to the knot. `teal_2` is on the top arc only, with no stripes.
- **Front:** behind-hair lobes at x1-10 and x33-42. They meet the head at y8-13 and swell to y6-17 at the tip. The top slopes down outward so they droop. The pocket is 2x3 at x3-4 / x39-40, y12-14. I lowered the lobes 1 row from the spec so the silhouette doesn't read as ears.
- **3/4:** the skull's back edge moves to x33 (y8-28); the tail and ponytail moved +2. Knot at x32-36, y8-12. The near-loop teardrop is at x34-42, y4-16 with a 2x3 pocket. The far loop is hidden.
- **Side:** the near loop is seen face-on at x31-39, y4-15, drooping back (6 px past the back hair), with a 3x4 opening and the knot at x28-30, y8-12. The gap at x34, y27-30 is filled with `d`.

## Side profile
- The forehead curves from x12 to x10.
- The nose is a 1 px upturned tip at (9,23), and the face steps back at y24.
- The mouth is a single `line_skin` pixel at (11,26).
- The chin is rounded at y27-31.
- The bang overhangs 2 px with a rounded tip (row 14 starts at x10). The hole at (18,15) is filled with `u`.
- There are no side expressions.

**3/4:** far eye 4 px (3 px iris), near eye 5 px, 2 px nose-bridge gap.

Every file uses 21 colours or fewer. The only orphan pixels are catchlights, the nose and FX.
