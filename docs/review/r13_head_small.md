# r13 Head at full-body scale (Pixel Artist 3), round-1 fixes applied

These are candidate C's face, hand-pixelled down to a ~27 px head on 40x40 canvases (the canvas size is unchanged). They are pasted into the 96x160 full bodies at x+28.

**Files:** `art/hand/S4/head_small/head_{front,three_quarter,side,back}.pix`. Expressions are in `expr/{front,three_quarter}_{10 names}.pix`; each one `extends:` its base view and adds patches.
**Review images:** `00_REVIEW/r13_anime_pixel/head_small/`: `heads_x4.png`, `head_*_x8.png`, `expressions_x4.png`, and `expressions_x1x2.png` (1x/2x on snow and on a dark background).

## Landmark rows (the same in every view; the round-1 changes are marked)
| row | feature |
|---|---|
| y4 | bow top (new) |
| y5 | crown |
| y14 | bang cut, with 2 notched V's |
| y15 | brows: 1 px `hair_1` (moved up 1 row) |
| y18 | lash |
| y19-23 | iris: i, i+catchlight, j, j, k |
| y24 | lower lash |
| y25-26 | blush |
| y25 | nose |
| y27-28 | mouth: 1-2-1 smile |
| y31 | chin |

## Bow (per review 1)
- **Front:** the loops peek 6 px each side, behind the hair, at y4-12, with a fold line. The knot is hidden and the total width is 40 px.
- **3/4:** a 5x5 knot sits on the back of the skull (x30-34, y8-12). The far loop shows over the crown and the near loop rises up and back. One tail hangs down, and the ponytail has an S-curve.
- **Side:** a lobe at y8-18 behind a 5x5 knot (x29-33, y10-14). The ponytail arcs back.
- **Back:** loops at y4-13 and a 5x5 knot (x17-21, y9-13) over the ponytail root. The dome shows above the knot. Two tails run off the bottom edge (they reach about y40 on the body).

## Face notes
- **3/4:** the far eye is 4 px wide (3 px iris) and the near eye is 5 px. There is a 2 px nose-bridge gap and 1-2 px of skin to the cheek contour. The jaw runs 1-1-1-2-2 to a soft chin.
- Every file uses 21 colours or fewer. The only orphan pixels are catchlights, the nose and FX.
