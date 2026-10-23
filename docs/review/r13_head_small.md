# r13 Head at full-body scale (Pixel Artist 3), review-5 final fixes applied

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
- **Front (R5):** each lobe is the visible outer half of the back loop. The outer end is at x1-3, y5-16 with rounded corners. The edges step in toward the head (top: y5 x2-3, then x4, 5, 6, 7; bottom: y16 x2-3, then x4, 5, x6-7 at y13). The tip tucks under the hair at x7-8, y9-13. Each has a `teal_0` pocket at x3-4, y10-12, a crease at y11, and `teal_2` on the top arc. Mirrored at x35-42.
- **3/4:** the skull's back edge moves to x33 (y8-28); the tail and ponytail moved +2. Knot (R5): a pinched 3x6 `teal_1` knot at x33-35, y8-13, with a `teal_2` pixel at (34,9), a `teal_0` bottom row, and no outline on the loop side. The near-loop teardrop is at x34-42, y4-16 with a 2x3 pocket. The far loop is hidden.
- **Side:** the near loop is seen face-on at x31-39, y4-15, drooping back (6 px past the back hair), with a 3x4 opening and the knot at x28-30, y8-12. The gap at x34, y27-30 is filled with `d`.

## Side profile (R5)
- The bangs hang to y16 at x11-13, so skin starts at y17.
- Profile `L`: y17 x11; y18-22 x10; y23 x9 (nose); y24-25 x10; y26-28 x11; y29 x12. The mouth is a single `L` at (12,26).
- The jaw is steeper: y28 x17-18, y29 x15-16, y30 x13-14. The neck below is `u` (x15-18, y30-31), and the old jaw block is cleared.
- There are no side expressions.

**Tilts:** `head_{front,three_quarter}_tilt{L,R}.pix` turn the whole head by hand: the crown peak moves 1 px toward the high side, the low-side bow drops 2 px and the high side rises 1 px, the low eye steps down 1 px, the mouth and chin shift 1 px low, and the side hair drops or lifts 1 px. Anchor and neck seam are unchanged. Overlays in `expr/<view>_tilt<L|R>_{smile,laugh,determined,embarrassed,surprised}.pix`; sheet `tilts_x4.png`. The 3/4 bow tail is now hair, with a 2x3 knot, two 2 px tails, and the far loop as a 2x3 block at x31-32, y12-14.

**3/4:** far eye 4 px (3 px iris), near eye 5 px, 2 px nose-bridge gap.

Every file uses 21 colours or fewer. The only orphan pixels are catchlights, the nose and FX.
