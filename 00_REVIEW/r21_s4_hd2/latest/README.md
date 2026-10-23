# r21: S4_hd2, the refined S4_hd (latest = round 7)

S4_hd2 is the same model as S4_hd (rig, proportions, animations, chains, face pass, palette, banded toon shading and
lavender-shadow smooth renders). Its geometry is rebuilt from smooth swept sheets and smooth unions, replacing the
stacked bead chains. Construction follows the 3D anime base-mesh references in work/r21/refs_web/picks
(04 / 12 / 27 / 32 / 07 / 19).
- Author: `.venv/bin/python -m pipeline.tools.make_s4_hd2`, which writes `data/variants/S4_hd2.json`.
- Build: `.venv/bin/python -m pipeline.build --variant S4_hd2 --anim idle`.
- Boards: `.venv/bin/python -m pipeline.tools.r21_review round rN`.

## Open first
1. `b_head_closeups_old_vs_new.png`: hair, bow and face (front / 3/4 / side / back). Top row S4_hd, bottom S4_hd2.
2. `a_turnaround_old_vs_new.png`: whole figure in the same shading as the r12 turnaround.
3. `d_idle_8dir_8x_old_vs_new.png` (also 1x / 2x) and `e_walk_8dir_old_vs_new.gif`: the 48x64 sprites.
4. `c_body_closeups_old_vs_new.png`: coat, scarf, mittens, boots.
5. `f_mesh_export_old_vs_new.png` and `S4_hd2_idle.obj` (with `.mtl`, smooth vertex normals): the exported mesh.
6. `critique.md`: ranked remaining issues. Earlier rounds are in `../r1` to `../r6`, each with its own critique.

## What changed (vs S4_hd)
- **Face:** base-mesh soft oval. Full cheeks curve into a small rounded chin with no point, the jaw is soft, and the profile face plane is nearly vertical (picks/32, 07).
- **Crown:** one clean, fuller dome (volume off the skull), with soft flow grooves converging on the ponytail root. No blob rows.
- **Fringe:** a thick curved shell of 7 chunky overlapping locks with soft rounded tips that curl in toward the forehead (picks/04, 12). They read as 3 panels (centre 3 locks, sides 2) with 2 shallow notches over a dark back layer. This replaces the 7-point zigzag.
- **Side locks:** broad flat ribbons cupped toward the cheek. They start under the fringe at the temple and hug the cheek and jaw, with a blunt rounded end at the collarbone. A skull-hugging under-layer means no background shows between the cheek and the lock in any view.
- **Back hair:**
  - The legacy "bun" ball is replaced by layered side sheets.
  - The 5 simulated back sheets fan out from the ponytail root and have staggered lengths. Same chains, sway and QA.
  - The outline tapers inward to a soft rounded V. All tips are soft and rounded.
- **Ponytail:** ONE ponytail of 4 layered clumps. It swells, then tapers in an S to a single rounded point. No rings.
- **Bow:**
  - **Loops:** puffy satin teardrop loops with rounded folded ends, a dark inner opening and one soft crease.
  - **Placement:** seated ON the hair at the ponytail root (chunky knot sunk into the hair). Swept back 38 deg and bent around the head; horizontal wings past the head in front view.
  - **Tails:** swallowtail with V cuts.
  - **Springs:** re-anchored on the knot with the same constants. It stays attached in walk and run.
- **Coat:** waist pinch, an A-line skirt with 6 soft rounded folds (no box pleats), a hem band following the folds, and a placket with 6 gold buttons (refs). Also the belt and buckle, a soft sleeve puff, and cuffs smooth-unioned into the sleeves. No pocket flaps (canon).
- **Scarf:** the double wrap is smooth-unioned with clean ribs. The chunky ribbon tail sits on her left, with a finer fringe.
- **Mittens:** clearly bigger (about 1.5x+ volume), round and puffy, with a thumb.
- **Boots:** clean shaft, toe, sole and heel, plus a puffy fur cuff.
- **Export:** opt-in polish (`render.mesh_export`): a finer grid with open face clip, mixed-material sets split per material (no duplicate shells), vertex welding, Taubin smoothing and OBJ vertex normals.

## Checks
- **S4_hd byte-identical:** idle and walk `_sheet.png` match the pre-r21 HEAD build (sha256 167a5477... / e5820a5a...).
- **QA:** S4_hd2 idle, walk and run all PASS. 0 orphans, 0 chain penetrations, no sub-pixel parts. Standing heights equal S4_hd. Walk and run height delta is 2.
