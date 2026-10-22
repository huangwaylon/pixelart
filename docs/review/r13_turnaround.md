# r13 Full-body turnaround (Pixel Artist 2)

Files: `art/hand/S4/turnaround/{front,three_quarter,side,back}.pix` (96x160).
Renders: `00_REVIEW/r13_anime_pixel/turnaround/` (`*_x4.png`, `turnaround_x3.png`, `turnaround_guides_x3.png`, `silhouette_check_x2.png`).

Five passes per view: silhouette, flats, selective lines, shading, details. Lines use the material colour on lit top/left edges; `#241628` only on bottom/right edges. Light from the upper left. 27 colours or fewer per view. Remaining orphans are catchlights and noses only.

Faces are copied pixel-for-pixel (eyes, brows, nose, mouth, blush, jaw) from Pixel Artist 3's `head_small/head_{front,three_quarter,side}.pix` at offset x+28, so the faces match. Their landmark rows are used throughout.

## Landmark rows (identical in all 4 views)
| landmark | y |
|---|---|
| bow top | 0 |
| crown | 5 |
| bang cut | 14 |
| brow / top lash | 16 / 18 |
| chin | 31 |
| scarf top / bottom | 32-33 / 42 |
| shoulder | 38 |
| bust step | 46-49 |
| belt (3 px) | 59-61 |
| ponytail point | 60 |
| hip / back-hair V | 70-73 |
| cuff trim / mittens | 71-73 / 74-81 |
| hem trim | 84-87 |
| knee | ~108 |
| boot cuff | 124-127 |
| sole | 154 |

Head is about 27 px and the figure is 5.4 heads tall. In the front view the centre line falls between x47 and x48.

## View notes
- **Front:** the bow wings span x15-80 and the knot shows above the crown. The scarf tail hangs on her left (the viewer's right). There are 6 buttons, a gold buckle, and transparent gaps between the arms and the waist.
- **3/4 (facing left):** the near wing and knot sit at the back, the far wing peeks over the crown, and the ponytail S-curves to a point. The scarf tail sits right of the button line.
- **Side:** the bow is drawn as two lobes opening backward, and the ponytail arcs out to x72. The scarf tail is on the near side, and the toes point left.
- **Back:** the full bow, swallowtail tails splayed to y46, and the scarf across the nape are all visible. The ponytail lies over the long hair. The scarf tail is hidden by the body.

## Open points
- My bow is bigger than the one in head_small, following the bible's "2x head width". Pixel Artist 3 and I need to agree on one size.
- The side profile face is small at this scale.
