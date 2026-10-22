# r13 Full-body turnaround (Pixel Artist 2)

Files: `art/hand/S4/turnaround/{front,three_quarter,side,back}.pix` (96x160).
Renders: `00_REVIEW/r13_anime_pixel/turnaround/` (`*_x4.png`, `turnaround_x3.png`, `turnaround_guides_x3.png`, `silhouette_check_x2.png`).

Five passes per view: silhouette, flats, selective lines, shading, details. Lines use the material colour on lit top/left edges; `#241628` only on bottom/right edges. Light from the upper left. 27 colours or fewer per view. Remaining orphans are catchlights and noses only.

Faces are copied pixel-for-pixel (eyes, brows, nose, mouth, blush, jaw) from Pixel Artist 3's `head_small/head_{front,three_quarter,side}.pix` at offset x+28, so the faces match. Their landmark rows are used throughout.

## Landmark rows (round 2, identical in all 4 views)
| landmark | y |
|---|---|
| bow top (front loops y3-17; back y4-17; side lobes y8-20) | 3 |
| crown / bang cut (2 notches) | 5 / 14 |
| brow / top lash / iris / lower lash | 15 / 18 / 19-23 / 24 |
| mouth (1-2-1) / chin | 27-28 / 31 |
| scarf top / bottom | 32-33 / 42 |
| shoulder (her right 1 px lower) | 38 |
| bust / waist (20 px) | 46-49 / 52-58 |
| belt | 59-61 |
| elbow bend | 58 |
| ponytail point | 60 |
| cuff / mittens | 71-73 / 74-81 |
| hem (curved: sides / centre) | 85 / 88 |
| knee | 108-111 |
| boot cuff (flared) | 124-128 |
| sole (free foot 1 px up) | 154 (153) |

## View notes
- **Front:** the bow wings span x15-80 and the knot shows above the crown. The scarf tail hangs on her left (the viewer's right). There are 6 buttons, a gold buckle, and transparent gaps between the arms and the waist.
- **3/4 (facing left):** the near wing and knot sit at the back, the far wing peeks over the crown, and the ponytail S-curves to a point. The scarf tail sits right of the button line.
- **Side:** the bow is drawn as two lobes opening backward, and the ponytail arcs out to x72. The scarf tail is on the near side, and the toes point left.
- **Back:** the full bow, swallowtail tails splayed to y46, and the scarf across the nape are all visible. The ponytail lies over the long hair. The scarf tail is hidden by the body.

## Open points
- My bow is bigger than the one in head_small, following the bible's "2x head width". Pixel Artist 3 and I need to agree on one size.
- The side profile face is small at this scale.

## Round 2 (review 1 fixes)
- **Bow (1):** 42 px (x27-68). Front: loops behind the head, no knot. 3/4 and side: knot on the back of the skull. Back: pinched loops, 5x5 knot, two swallowtail tails to y40.
- **Hair (2, 8):** back hair now shows 3-4 px outside the arms (front and 3/4) from y36 to y70. Locks run to y44. Back view: the nape narrows under the scarf (y31-42) and shoulders break at y38-47. The long hair has 4 clump tips with dark split wedges.
- **Stance (3, 4, 5):** weight is on her right leg, hips shift 1-2 px, and the shoulder on that side drops 1 px. Waist is 20 px. Elbows bend at y58 and open the arm gap. Mittens curl and have thumbs. The hem curves (sides y85, centre y88).
- **Legs:** added `char_2 #6A6688` sheen on the kneecap and shin, with ink on the inner edges. Widths are 9/6/7 px, with a thigh gap below the hem. The free knee turns in and its heel is up 1 px. Boots have a flared cuff, one fold, and toes turned out.
- **Faces (6, 7, 9):** front, 3/4 and side faces are copied exactly from Artist 3's round-1 `head_small` files (offset x+28), including the crown clumps. The 3/4 has a narrow far eye, more skull behind the ear, and an S-curve ponytail.
- **Stats:** 14-28 colours per view. Allowed orphans only, plus four notch-flank pixels that come from Artist 3's front file.
