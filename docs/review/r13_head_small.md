# r13 Head at full-body scale (Pixel Artist 3)

These are candidate C's face, hand-pixelled down to a ~27 px head on 40x40 canvases. They are meant to be pasted into the 96x160 full bodies.

**Files:** `art/hand/S4/head_small/head_{front,three_quarter,side,back}.pix`. Expressions are in `expr/{front,three_quarter}_{10 names}.pix`; each one `extends:` its base view and adds patches.
**Review images:** `00_REVIEW/r13_anime_pixel/head_small/`: `heads_x4.png`, `head_*_x8.png`, `expressions_x4.png`, and `expressions_x1x2.png` (1x/2x on snow and on a dark background).

## Landmark rows (the same in every view)
| row | feature |
|---|---|
| y5 | crown |
| y14 | bang cut |
| y15 | hair shadow |
| y16 | brows |
| y18-23 | eyes (top lash at y18) |
| y24-25 | blush |
| y25 | nose (side view: tip at y24) |
| y27 | mouth |
| y31 | chin |
| y32-33 | scarf top |

The front view's centre line falls between x19 and x20. Hair, ponytail and scarf run off the bottom edge so the body art can continue them.

## Face construction
- **Front:** eyes are 5x6 at x12-16 and x23-27, with a tare-me flick 1 px past the outer corner. One catchlight per eye, always on the upper-left.
- **3/4 (facing left):**
  - Far eye: 4x6 at x9-12, with 2 px of skin to the cheek contour.
  - Gap between the eyes: x13-14 (2 px).
  - Near eye: 5x6 at x15-19; its iris is shifted toward the gaze, so the sclera shows on the outer side.
  - The cheek bulges 1 px under the far eye. The jaw runs 1-1-1-2-2 to a soft 3 px chin.
- **Blush:** "xx" over "tt" dashes. **Mouth:** 2 px `crn_1`.

## Notes for the other artists
- The bow wings are limited by the 40 px canvas, so they come out about 1.4x the head width. The turnaround's bigger bow (2x, per the bible) should be the canonical size; widen the wings when you paste.
- Bow tails stop at about y25. The ponytail continues below the canvas.
- Every file has 21 colours or fewer. The only orphan pixels are catchlights, the nose and FX (tear, sweat, vein mark, steam).
