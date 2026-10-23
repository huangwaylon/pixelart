# r21: S4_hd2, the refined S4_hd (latest = round 4)

S4_hd2 is the same model as S4_hd (rig, proportions, animations, chains, face pass, palette, banded toon shading and
lavender-shadow smooth renders). Its geometry is rebuilt from smooth swept sheets and smooth unions, replacing the
stacked bead chains.
- Author: `.venv/bin/python -m pipeline.tools.make_s4_hd2`, which writes `data/variants/S4_hd2.json`.
- Build: `.venv/bin/python -m pipeline.build --variant S4_hd2 --anim idle`.
- Boards: `.venv/bin/python -m pipeline.tools.r21_review round rN`.

## Open first
1. `b_head_closeups_old_vs_new.png`: hair, bow and face (front / 3/4 / side / back). Top row S4_hd, bottom S4_hd2.
2. `a_turnaround_old_vs_new.png`: whole figure in the same shading as the r12 turnaround.
3. `d_idle_8dir_8x_old_vs_new.png` (also 1x / 2x) and `e_walk_8dir_old_vs_new.gif`: the 48x64 sprites.
4. `c_body_closeups_old_vs_new.png`: coat, scarf, mittens, boots.
5. `f_mesh_export_old_vs_new.png` and `S4_hd2_idle.obj` (with `.mtl`, smooth vertex normals): the exported mesh.
6. `critique.md`: ranked remaining issues. Earlier rounds are in `../r1` to `../r3`, each with its own critique.

## What changed (vs S4_hd)
- **Face:** VRoid-style soft oval. Full cheeks curve into a small rounded chin (the V chin is gone), with a soft jaw and a slightly flat face plane.
- **Crown:** one clean dome, with soft flow grooves converging on the ponytail root (no blob rows).
- **Fringe:**
  - 3 panels: blunt hime cut, 2 shallow notches, centre panel widest.
  - The panels are a curved shell on the forehead (lens section, thinner tip, rounded cut, lifted about 0.4) over a dark back layer that shows in the notches.
  - It replaces the 7-point zigzag.
- **Side locks:** straight, flat and cupped toward the cheek. They start under the fringe and end in a blunt rounded cut at the collarbone.
- **Back hair:**
  - The legacy "bun" ball is replaced by 2 layered static side sheets per side.
  - The 5 simulated back sheets now fan out from the ponytail root. Same chains, sway and QA.
  - Lens sections, soft V tips, all smooth-unioned into the dome.
- **Ponytail:** ONE ponytail of 4 layered clumps (2 on top with a soft groove, 2 tucked under). It swells, then tapers in an S to a single rounded point, with slight clump separation at the tip. No rings.
- **Bow:**
  - Wide flat satin ribbon loops: a teardrop about 2.2:1, pinched at the knot, with a puffy lens section, a dark inner opening and one soft crease.
  - Horizontal wings: 5 deg up, swept back 22 deg.
  - Seated ON the hair at the ponytail root, with a chunkier knot.
  - Swallowtail tails with V cuts.
  - Same springs, re-anchored on the knot. It stays attached in walk and run.
- **Coat:** waist pinch, an A-line skirt with 6 soft rounded folds (no box pleats), a hem band following the folds, and a placket with 6 gold buttons (refs). Also the belt and buckle, a soft sleeve puff, and cuffs smooth-unioned into the sleeves. No pocket flaps (canon).
- **Scarf:** the double wrap is smooth-unioned with clean ribs. The chunky ribbon tail sits on her left, with a finer 9-strand fringe.
- **Mittens:** clearly bigger (about 1.5x+ volume), round and puffy, with a thumb.
- **Boots:** the same clean shaft, toe, sole and heel, plus a puffy fur cuff (soft ribbing on the refs).
- **Export:** opt-in polish (`render.mesh_export`): a finer grid with open face clip, mixed-material blend sets split per material (no duplicate shells), vertex welding, Taubin smoothing and OBJ vertex normals.

## Checks
- **S4_hd byte-identical:** idle and walk `_sheet.png` match the pre-r21 HEAD build (sha256 167a5477... / e5820a5a...).
- **QA:** S4_hd2 idle, walk and run all PASS. 0 orphans, 0 chain penetrations, no sub-pixel parts. Standing heights equal S4_hd (idle 34 px in every direction). Run height delta is 2.
