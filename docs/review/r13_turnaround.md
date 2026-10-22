# r13 Full-body turnaround (Pixel Artist 2)

Files: `art/hand/S4/turnaround/{front,three_quarter,side,back}.pix` (96x160).
Renders: `00_REVIEW/r13_anime_pixel/turnaround/` (`*_x4.png`, `turnaround_x3.png`, `turnaround_guides_x3.png`, `silhouette_check_x2.png`).

Five passes per view: silhouette, flats, selective lines, shading, details. Lines use the material colour on lit top/left edges; `#241628` only on bottom/right edges. Light from the upper left. 27 colours or fewer per view. Remaining orphans are catchlights and noses only.

Faces are copied pixel-for-pixel (eyes, brows, nose, mouth, blush, jaw) from Pixel Artist 3's `head_small/head_{front,three_quarter,side}.pix` at offset x+28, so the faces match. Their landmark rows are used throughout.

## Landmark rows (round 3, 5.0 heads, identical in all 4 views)
| landmark | y |
|---|---|
| bow (one teardrop design, 42 px x27-68; knot 5x7 at y8-14) | 4-16 |
| crown / bang cut (2 notches) | 5 / 14 |
| brow / top lash / iris / lower lash | 15 / 18 / 19-23 / 24 |
| mouth / chin | 26-28 / 31 |
| scarf top / bottom | 32-33 / 42 |
| shoulder (her right 1 px lower) | 38 |
| bust / waist (20 px) / belt | 46-49 / 52-58 / 59-61 |
| elbow / ponytail point | 58 / 60 |
| cuff / mittens | 71-73 / 74-81 |
| hem (sides / centre) | 85 / 88 |
| knee | 100-111 |
| boot cuff (flared) | 119-122 |
| sole (free foot 1 px up) | 142 (141) |

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

## Round 3 (review 2 fixes 2-6, 8)
- **Back hair (2):** a curtain 30 px wide (x33-62) that tapers to 22 px, with 5 clump tips staggered from y60 to y76 and split wedges between them. The sleeves now show at the sides. In the front and 3/4 views, the hair beside the arms is a 2 px strand broken at y47 and ending by y62.
- **Proportion (3):** now 5.0 heads (crown y5 to sole y142). The legs lost 6 px and the boot shafts lost 6 px. The guides are updated.
- **Legs (4, 5):** one monotonic taper (9, 8, 7, 7, 6, 5) with a straight inner edge, so the seam is the single 1 px line. Each leg has one continuous `char_2` sheen line from y94 to y117. In the side view the back of the leg is now the 1 px outline.
- **Boots (6):** 7 px shafts narrowing to 6 at the ankle, a flared cuff, and a diagonal plum fold.
- **Re-sync (1, 7):** copied Artist 3's updated `head_front` (wedge bow loops at y8-13 with a crease) and `head_side` (soft forehead, upturned nose, small mouth) exactly. The side face region was re-shaped to their contour. The 3/4 file was unchanged.
- **Silhouettes (8):** rechecked on light, dark and black backgrounds. Only allowed orphans remain.

## Round 4 (review 3)
- **Bow (ruling a; fixes 1-4):** every view now uses Artist 3's bow from `head_small`, copied exactly.
  - Front: flared fans at y7-14.
  - Back: 38 px fans at y6-15 with a 5x5 knot (x45-49) and the rounded hair arc kept between the loops. My two tails continue from their roots at x41-45 and x50-54 down to y40.
  - 3/4: near-loop fan at y6-14, far nub lowered behind the crown.
  - Side: the near loop faces the viewer on the back of the skull.
- **Heads (fixes 5, 6):** the 3/4 and side views now take Artist 3's whole head, rows 5-31: face, crown, side-bang overhang, filled hole, bow, ponytail root and tail roots. My ponytails, tails and back hair continue from their positions below y31; the 3/4 view keeps the S-curve. The 3/4 skull is therefore their narrower one (back edge x57).
- **Back hair tips (fix 7):** 5 rounded points (bottom falls off as dx^2 from each tip) at y64-74, each with 1-2 `hair_1` shadow pixels on one side only. The shredded split wedges are gone.
- **Checks:** silhouettes rechecked on light, dark and black. Only allowed orphans remain. 14-28 colours per view.

## Round 5 (review 4)
- **Re-sync:** Artist 3's four `head_small` files were updated at 08:35-08:38, with the canvas widened to 44 px. The copy now reads each file's width and uses a centre-aligned offset (x+26), so no fixed x+28 is assumed. Front, 3/4, side and back heads and bows are copied exactly.
  - Back (master): puffy teardrop loops x27-68, y4-16, with a 5x7 knot and the hair arc.
  - Front: drooping lobes x27-33 and x62-68 at y5-16, with pockets.
  - 3/4: teardrop near loop at x60-68, and the skull back edge moved to x59.
  - Side: the near loop is face-on at x55-63, and the gap at x60 is filled.
- **Body continuation:** in the back view the tails continue from the new roots (x41-45 and x50-54) down to the swallowtail ends at y40. In the 3/4 view the ponytail S-curve and the back hair are shifted 2 px right to continue from the new root (x62-66 at y31), and the point is now at x71, y60.
- **Checks:** turnaround, guides and silhouette checks are re-rendered. Only allowed orphans remain, with 14-28 colours per view.

## Round 6 (review 5 head fixes)
- **Re-sync:** Artist 3's front, 3/4 and side files (08:45) and back file (08:36) are copied at offset x+26. A check script confirms 0 pixel mismatches against `head_small` in all four views. The orphan cleanup now skips the copied head rows, so their pixels (for example the side nose `v`) stay exact.
- **Side neck/collar:** the scarf top now starts at x40 on y32 and x38 on y33. The neck's front edge sits on the collar under the steeper jaw, with no notch.
- **Checks:** re-rendered, including the guides and silhouette check. The only orphans outside catchlights and noses come from Artist 3's files: back (35,16) and 3/4 (60,9).
