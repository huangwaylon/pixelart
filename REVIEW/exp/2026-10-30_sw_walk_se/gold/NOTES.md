# Gold frames v2: walk SE, contact L and passing L (2026-10-30)

These are v2. They answer the owner's "approve style, revise pose" note and DESIGN_LOCK.md Amendment 1. The style is unchanged from v1: flat 2-tone shading, the 14-colour lock, the eyes-and-brows face and the clean 1-px outline. v2 changes the view angle, proportions, poses and hair. The v1 pair is kept in `v1/`. Status: **needs-review**.

## Files
| file | what |
|---|---|
| `walk_SE_contact.png/.txt` | contact L. Body bob +1 px. |
| `walk_SE_passing.png/.txt` | passing L. Body rises to −1 px, 2 px above contact. |
| `board_gold_walk_SE.png` | master, pose guide f00, pose guide f02, gold contact, gold passing, at 1x and as a 6x crop on mid-grey |
| `gold_toggle.gif`, `gold_toggle_1x.gif` | 2-frame toggle, 400 ms per frame, infinite loop |
| `gates.json`, `iou_vs_master.json` | gate results and silhouette IoU against EC0_SE_96 |
| `critique_opus.txt` | the one Opus critique for v2. Fixes applied are listed below. |
| `build_gold.py`, `bow_block.txt`, `gates.py`, `make_board.py` | source, run with `.models/pixtools/venv/bin/python` |

## What changed from v1
- **Master view angle and proportions.** These are the shared SE standard from Amendment 1.
  - The head and hair silhouette, face, neck and collar V are placed from measurements of EC0_SE_96.
  - The hem sits at about y90, the master's leg length: thighs y91–94, a red sock band at y95, socks to y113, boots from y114.
  - The obi is a wide band slanted across the front, as on the master: higher at the far (right) end, 6 rows thick.
  - The face is turned further: the near cheek is wider, the far cheek curves in, and the chin points toward the far side.
  - The eyes use the facesys templates moved 1 px toward the far side (`EYEDX = 1`). The pipeline should copy this offset.
- **Contact.**
  - Legs: the front (screen-right) leg is planted heel-first with the toe lifted. The back leg bends at the knee and stands on its toe. Together they form a wide V stride.
  - Arms bend asymmetrically: the near arm swings forward with the hand in front of the skirt, and the far arm swings back with the elbow bent and the hand behind.
- **Passing.**
  - The body is 2 px higher than on contact.
  - The swing (near) leg's knee leads forward over the support leg, and its shin trails back with the toe pointing down.
  - The near hand crosses over the front of the skirt and the far hand tucks back. The obi counter-rotates by 1 px and the back hem corner lifts, so the torso is not a copy of the contact torso.
- **Hair.** The master's longer side locks frame the face: a near front lock over the shoulder down to about y70, a near-side back lock, and a far lock with an S-step. The bangs are full with strand tips, and the eyes are left clear.
- **Bow.** The loops are smaller (the bow now spans about x46–66). The tail is redrawn as one ribbon with a free end.

## Gates (both frames PASS)
| gate | contact | passing | limit |
|---|---|---|---|
| zigzags | 0 | 0 | ≤ 1 |
| redundant L-corners | 0 | 0 | ≤ 2 |
| outline gaps | 0 | 0 | 0 |
| 2×2 `K` clumps outside the eye templates | 0 | 0 | 0 |
| interior `K` not on a listed overlap | 0 | 0 | 0 |
| connected pieces | 1 | 1 | 1 |
| colours / off-palette | 12 / none | 12 / none | ≤ 14 |

Each frame has 7 raw clumps, all inside the exact facesys eye templates and brows. The coordinator has accepted these.

## Silhouette IoU against EC0_SE_96 (best within ±2 px of bob)
| region | v1 contact | v2 contact | v1 passing | v2 passing |
|---|---|---|---|---|
| head (y26–65) | 0.807 | 0.825 | 0.807 | 0.825 |
| torso (y63–91) | 0.781 | 0.730 | 0.785 | 0.769 |
| head+torso | 0.788 | 0.791 | 0.790 | 0.798 |
| full | 0.644 | 0.662 | 0.714 | 0.744 |

The head IoU improves. The torso IoU cannot reach the master's: the lock requires narrow sleeves where the master has bell sleeves, and the arms are posed. The full-figure IoU on contact is capped by the stride.

## Opus critique (one call)
Opus scored line art 7, match to master 5, liveliness 5, hair 6 and appeal 6, before the fixes.
- **Done.**
  - Face 3/4: the near cheek is wider, the far cheek curves in, the chin is pointed and the eyes move 1 px toward the far side.
  - Contact heel strike and toe stand.
  - Bent far arm swinging back, with the near hand raised and forward.
  - Passing knee leads and the toe points down.
  - Passing hands cross the body line, and the torso varies between frames (obi rotation, hem).
  - Wavier locks, including the far lock's S-step.
  - Smaller bow and a redrawn tail.
  - Smoother head contour and the sleeve notch.
- **Partly done.** The eyes move 1 px, not the suggested 2. They stay close to the facesys layout that the pipeline shares.
- **Not done.** The boots are not narrowed to 7 px with a heel notch.

## For the owner
1. Approve v2 as gold, or mark up pixels on `board_gold_walk_SE.png`.
2. Confirm the pipeline should copy the eye offset (+1 px toward the far side).
