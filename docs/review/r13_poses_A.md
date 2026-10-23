# r13 Cut-scene poses A (Pixel Artist 2): idle, wave, point, hands_on_hips

Sources: `art/hand/S4/poses/{idle,wave,point,hands_on_hips}.pix` (96x160).
Renders: `00_REVIEW/r13_anime_pixel/poses/` (`*_x4.png`, `poses_A_silhouette_x2.png`, `poses_lineup_x3.png` with Artist 3's four poses).

Each pose is built on the approved turnaround: 5.0 heads, the same palette and line rules, and sole at y142. Faces are pasted exactly from `head_small` (base view plus `expr/`) at x+26. The head is only ever translated with the line of action, never rotated. 24-28 colours per pose. The only orphans are catchlights and noses.

| pose | view / face | line of action, weight | gesture and secondaries |
|---|---|---|---|
| idle | front, smile | Soft C: head and shoulders drift 3/2/1 px toward the free side. Hips push 3 px over her right leg. | Curled mittens with thumbs. The free knee turns in and its heel is up 1 px. |
| wave | front, laugh | S-curve up her raised right arm. Weight on her right leg. | Elbow out, forearm up, open palm with the thumb spread. The scarf tail swings 2 px. Only a back-hair strand shows beside the torso. |
| point | 3/4, determined | Heel-to-fingertip diagonal. The body leans in 3/2/1 px over the bent front leg. The back leg is extended on its toe. | Arm rises 5 px to the fist, with the index pointing out and the thumb on top. The ponytail swings back. |
| hands_on_hips | front, determined | Vertical, with a 2 px chest-out bust step. Feet planted apart. | Fists on the belt with knuckle lines and thumbs. The elbow triangles are kept open by moving the hair behind the back. The scarf tail ends above the fist. |

Passes: 3-4 viewed passes per pose, plus a silhouette check on light, dark and black. All four silhouettes read distinctly.

Open: idle is the closest to the turnaround (by design). A hand-redrawn head tilt could add more life later.

## Round 2 (review 1 poses)
hands_on_hips was approved and is unchanged. Idle, wave and point now have:
- **G1 tilt:** one side of the pasted head sits 1 px lower, with the step between the eyes and the mouth. It is a 1-row offset of Artist 3's pixels, not a rotation, and the seam was checked. Wave and point tilt toward the hand; idle tilts toward the free side.
- **G2 lean:** about 1 px per 8 rows. Wave leans away from the raised arm in an S; point leans in by 3/2/1 px; idle is a 3/2/1 px C.
- **G3 hem:** lifts 1-2 px on the moving side (under the raised arm, at the back of the lean, and on the free side).
- **G4 hair:** the curtain ends trail or lift 1-3 px (moved region cells, re-outlined).
- **Wave:** the forearm tapers to the wrist with an elbow corner at (20,30). The mitten is an open palm with a lighter centre, a heel line and a splayed thumb.
- **Point:** the figure is 3 px further right, so the index tip is now at x1. The sleeve is tapered (8 to 6 rows) and the fist has a long index and a raised thumb.
- **Idle:** the free knee turns in 2 px and its heel is up 2 px (sole y140).

Orphans are only catchlights, noses and mouth corners.

## Round 3 (review 2 poses)
- Reverted the 1-row head-offset tilt: all heads are again exact `head_small` pastes. Hand-drawn tilted heads from Artist 3 will be swapped in when they land (idle tilts to the free side; wave and point tilt toward the hand).
- Idle: filled the hole at (59,57) and merged the strand-tip thorn (x66-68, y53-57) into a 2 px lock.
- Wave: deleted the loose outline pixels at x65-68, y57-60. The arm outline stays.
- Point: the figure is shifted 2 px further right (x offset +5). The smirk came from the tilt seam and is gone with the revert. The back-hair trail that opened gaps behind the lock is removed, so the ponytail swing alone carries the secondary motion.
- Re-synced the 3/4 bow fix (head_three_quarter 09:13, 3x6 knot) into the turnaround three_quarter and point.

## Round 4 (tilted heads)
- Swapped in Artist 3's hand-drawn tilts, pasted exactly at x+26 and translated with each pose's lean:
  - idle: `expr/front_tiltR_smile` (tilts to the free side);
  - wave: `expr/front_tiltL_laugh` (toward the hand);
  - point: `expr/three_quarter_tiltL_determined` (toward the hand).
- Re-synced the 09:18 `head_three_quarter.pix` (3/4 bow fix) into the turnaround three_quarter view and point.
- Checked the neck seams at x4: chin, neck shadow and the scarf top join cleanly in all four.
- Re-rendered the poses, turnaround, guides, both silhouette checks and the 8-pose lineup. Remaining orphans are catchlights, noses and mouth corners from the head files.

## Round 5 (review 3 poses)
- Idle, wave and hands_on_hips are approved.
- Point: the sleeve is now 9 rows at the shoulder and 8 at the wrist (7 rows of fill), with the cuff matched to the wrist (10 rows). A dark `#241628` top outline runs along the sleeve and cuff.
- Idle: re-pasted `expr/front_tiltR_smile` after Artist 3's lash-corner fix in `head_front_tiltR` (09:31). A check script confirms 0 pixel mismatches; (59,20) is now `u`.
- Re-rendered the poses, the silhouette check and the 8-pose lineup.
