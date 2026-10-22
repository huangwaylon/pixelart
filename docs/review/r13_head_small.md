# r13 Head at full-body scale (Pixel Artist 3), review-2 fixes 1 and 7 applied

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

## Bow
- **Front:** a wedge on each side, coming out from behind the hair at y8-13 (x1-6 and x33-38). It shows 5 px or less, widens outward and has one `teal_0` crease. The outer corner is the highest point.
- **3/4:** a 5x5 knot on the back of the skull (x30-34, y8-12). The far loop shows over the crown and the near loop goes up and back.
- **Side:** lobe y8-18, knot x29-33 y10-14.
- **Back:** a 5x5 knot (x17-21, y9-13) over the ponytail root; two tails run off the bottom edge.

## Side profile
- The forehead curves from x10 to x8.
- The nose is a 1 px upturned tip at (7,23), and the face steps back at y24.
- The mouth is a single `line_skin` pixel at (9,26).
- The chin is rounded at y27-31.
- There are no side expressions.

**3/4:** far eye 4 px (3 px iris), near eye 5 px, 2 px nose-bridge gap.

Every file uses 21 colours or fewer. The only orphan pixels are catchlights, the nose and FX.
