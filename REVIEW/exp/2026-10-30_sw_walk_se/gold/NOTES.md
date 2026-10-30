# Gold frames: walk SE, contact L and passing L (2026-10-30)

These are the two frames that define "done" for milestone 1 (DESIGN_LOCK.md §6). They are hand-authored to the lock. They are **needs-review**: they become gold only once the owner approves them.

## Files
| file | what |
|---|---|
| `walk_SE_contact.png/.txt` | contact L (motion/walk.json key 0): left leg (screen-right) forward on the heel, right leg back on the toe. Near arm forward with the hand in front of the skirt; far arm back. Body bob +1 px. |
| `walk_SE_passing.png/.txt` | passing L (key 2): left leg planted straight; right (near) leg passes in front with the knee bent and the foot tucked up behind. Arms near neutral, with the hands at different heights. |
| `board_gold_walk_SE.png` | master, pose guide f00, pose guide f02, gold contact, gold passing, at 1x and as a 6x crop on mid-grey |
| `gold_toggle.gif`, `gold_toggle_1x.gif` | 2-frame toggle, 400 ms per frame, infinite loop (4x and 1x) |
| `gates.json` | per-frame gate results (`gates.py`) |
| `critique_opus.txt` | the single Opus critique (round 1). Fixes applied are listed below. |
| `build_gold.py`, `bow_block.txt`, `make_board.py`, `gates.py` | source. `.models/pixtools/venv/bin/python build_gold.py && ... gates.py && ... make_board.py` |

Char maps use the lock's letters, `.` = transparent. The cell is 128×128 and the feet sit at y=124, the same as `EC0_SE_96`. Figure height is 97 px, the same as the master.

## How they were authored
- **Large masses** (hair, face, neck, torso, obi, skirt, sleeves): polygons with hand-picked vertices in 1x pixel units (`head()`, `body()`), rasterised into a part map. Legs and boots are hand-placed pixel spans with uniform 1:2 slopes.
- **Line**: a closed 1-px `K` silhouette. Interior `K` appears only on the lock's listed overlaps (`lines_for()`): leg/leg, arm over body (and body over the far arm), hand/sleeve cuff, bangs/face, bow/hair, and chin/neck. This is followed by a pixel-perfect clean-up (redundant elbows, 2×2 clumps).
- **Shading**: flat 2-tone per material with the light from the upper left. Red is `E`/`R`, hair `H`/`h` plus one `L` sheen arc, skin `s`/`S` (the face is flat `s`), obi `O`/`o`, socks `H`/`h`, boots `g`/`H`. The far sleeve is entirely in shadow (`R`). The socks and boots are lighter than the outline, so the legs separate from each other and from the line.
- **Face**: `facesys.py` `open` templates at the SE layout: a 5-px front eye at (61,47) and a 4-px far eye at (72,47), with +1 y on contact. Brows are `h` on skin and `K` where they fall on hair.
- **Drawn by hand as char blocks**: the bow and bun (`bow_block.txt`), plus the hands, cuffs and skirt corners (`REGION`/`PATCH` in `build_gold.py`, each with a reason).

## Gates (both frames PASS)
| gate | contact | passing | limit |
|---|---|---|---|
| zigzags (lamet `zig`) | 0 | 0 | ≤ 1 |
| redundant L-corners (lamet `dbl`) | 0 | 0 | ≤ 2 |
| outline gaps | 0 | 0 | 0 |
| 2×2 `K` clumps in line art | 0 | 0 | 0 |
| interior `K` not on a listed overlap | 0 | 0 | 0 |
| connected pieces (no stray pixels) | 1 | 1 | 1 |
| colours / off-palette | 12 / none | 12 / none | ≤ 14 / none |

Colours used: `K h H g L s S E R O o W`. `e` and `Q` are unused: the lock allows 2-tone only, with a highlight only on hair.
**Note on clumps:** lamet counts 5 raw 2×2 `K` blocks per frame. All 5 are inside the exact `facesys` eye templates: the `open` lash/pupil block has 3 in the front eye and 2 in the far (mirrored, 4-px) eye. The lock requires the exact templates (§1), so the gate counts clumps outside the eye boxes and reports these separately as `clump_face`. If the owner wants a strict 0, the `open` template's lash row needs a change, which is a lock change.

## Critique (Opus, one call) and what was done
Opus scored 7 for line art, 6 for consistency, 6 for appeal and 6 for anatomy, before the fixes.
- **Done.**
  - Wider V stride on contact: front boot heel-strike with the toe up, back boot on its toe.
  - Passing free leg: knee bent, foot tucked under the body with the toe down.
  - Arms are more asymmetric: on contact the near arm is bent at the elbow with the forearm forward and the far hand higher, and on passing the hands sit at different heights.
  - Stronger SE turn: the far cheek and far hair strip come in by 1 px, the near-side hair goes out by 1 px, the far lock is removed, the chin moves right, the body sits 1 px left of the head (head forward), and the collar V is offset right.
  - Hem raised 2 px with longer socks, closer to the master's leg length. The back hem corner is rounded.
  - The bow is redrawn: the upper loop is now a pointed teardrop, so the bun and bow no longer read as "mouse ears". The tail is redrawn as one ribbon with a uniform 1:2 slope.
  - The hair sheen is a short angled arc instead of three dashes.
  - The hands are redrawn as clean mittens.
- **Not done, and why.**
  - Removing the `K` line across the top of the hands: hand/sleeve is a listed overlap, so the lock asks for that line.
  - Moving the eyes: they stay on the facesys SE layout, which the pipeline also uses.
  - "Far eye to 4 px": it already is 4 px.
  - An inward obi step: both obi ends sit under the sleeves' arm-over-body lines, so the waist break comes from the band itself and the skirt flare.
  - Longer wavy chest locks like the master's: the hair stays a bob to the jaw and shoulders, as on the illustration. The owner should decide this.

## Open questions for the owner
1. Approve the two frames as gold, or mark up pixels on `board_gold_walk_SE.png`.
2. Accept the 5 eye-template clumps, or change the `open` template?
3. Side-lock length: should the hair be the illustration's jaw/shoulder bob (current) or the master's longer wavy locks?
