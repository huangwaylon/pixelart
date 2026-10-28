# PARTS strand RESULTS (2026-10-26)

**Question:** can we generate parts and assemble them into a clean, consistent, rigid-part 3D reference that mirrors the cutout rig?
**Answer:** yes, as a hybrid. Cut the existing 2mv mesh (approach A) for the identity parts (head and torso), and use per-part generation (approach B) for the limbs and the skirt. Replace the bow and bun with simple procedural shapes, and make the obi a separate shell. Full image-to-parts generators (approach C) split by material, not by joint, so they don't solve rigging.

## Deliverables
- **Final parts (adopt):** `out/AB3/*.glb`, the combined `out/AB3_assembled.glb` (one named node per part) and `out/AB3/pivots.json` (bone, parent and pivot per part, in the 2mv glb frame: Y up, faces +Z, her left = +X, feet at y = -1).
  - Parts: head, bow, bun, torso (with the obi shell), skirt, arm_L/R (each with a shoulder ball), leg_L/R (with boot) and an optional katana.
  - All of them except the katana bind 1:1 to bones: head/bow/bun -> head, torso -> chest, skirt -> its own skirt bone off hips, arm -> upper_arm, leg -> thigh.
- **Other methods:** `out/{A,B,C,AB,AB2}/` plus their `_assembled.glb`.
- **Renders:** `out/renders/<M>_{front,side,back,se,pose_front}.png`. SE is the iso view at 30° elevation with the camera front-right, so the face is visible. 48 px downsample: `out/renders/<M>_se_48px.png` and `_x4.png`.
- **Comparison sheets:**
  - `sheet_compare_final.png`: 2mv single | A | B | C | hybrid v3.
  - Earlier rounds: `sheet_compare.png`, `sheet_compare_v2.png`, `sheet_compare_v3.png`.
  - Columns: front, side, back, iso SE, exploded, rigid pose test (arm raise, leg stride, head tilt), pose side, 48 px x4.
- **Critiques:** `crit/` (prompt*, argon*.md, opus*.md; Opus ran on the nsystem4 account).

## Scores (on-model / seams / rig / 48 px)
| row | Argon r1 | Opus r1 | Argon final | Opus final |
|---|---|---|---|---|
| 2mv single (baseline) | 6/5/3/6 | 6/3/1/5 | 7/5/1/4 | 6/5/2/6 |
| A split existing mesh | 6/5/6/6 | 6/5/6/5 | 7/4/5/5 | 6/5/6/6 |
| B Gemini part sheets -> 2mv per part | 4/6/6/5 | 5/6/8/4 | 4/6/7/4 | 5/3/7/4 |
| C PartCrafter (12 parts) | 3/3/3/4 | 3/2/1/3 | 2/2/2/2 | 3/4/2/4 |
| **A+B hybrid** (r1 -> v3) | 6/6/7/7 | 7/6/8/6 | **8/8/9/8** | **7/7/8/7** |
In every round, both critics picked the hybrid.

## What each approach showed
- **A, split the mesh** (`scripts/split_a.py`, 33 s on CPU).
  - Method: voxelise the watertight mesh, assign regions by planes, arm capsules and labels, then run marching cubes per part. This gives 11 closed, watertight parts with planar seams that are hidden at rest. The legs get a hidden thigh capsule up to the hip.
  - It is cheap, exactly on-model and pixel-consistent with the existing rig and keys.
  - Weakness: it inherits the 2mv surface noise: ragged sleeve cuffs, a lumpy bow, a jagged obi colour edge, and a bun that's mostly buried in the head.
- **B, generate per part** (`gem_parts.sh`, `prep_mv.py`, `run_mv_parts.py`, `vcol_proj.py`, `assemble.py`). 2mv takes 8-11 s per part.
  - Gemini part isolation is unreliable:
    - front head: it returned the whole character;
    - back views: wrong;
    - skirt front: a dome;
    - torso side: a huge obi.
  - What worked:
    - head = a deterministic crop of the turnD views at the neck;
    - back = mirror of front (the orthographic silhouette is the same);
    - equal-scale views with alpha=1 sentinel pixels, so Hunyuan's per-view recenter keeps the relative extents.
  - Limbs, sleeves and the skirt come out clean and simple. The head and torso are off-model: projected colours leave streaks and holes, and the torso is thin.
  - The parts are fitted per axis to the A bboxes, so the proportions equal the 2mv mesh.
- **C, part-aware generators.** Research is in NOTES step 2.
  - PartCrafter (MIT) runs on MPS after 2 small patches. Its venv is `.scratch/parts/venv_pc`. 8 parts took 356 s and 12 parts 520 s.
  - Its parts are material-like (hair, face, eyes, bow, obi, dress+sleeves+skirt as one piece, legs). There are many fragments and the depth is thin because it works from a single image. Its rig value is about zero.
  - Hunyuan3D-Part (spconv/Sonata), OmniPart (TRELLIS v1 CUDA stack) and HoloPart (needs a segmentation mask, CUDA) are not practical on Mac. PartPacker was skipped: its parts are not semantic and its licence is non-commercial.

## Recommendation
Adopt **hybrid v3** (`out/AB3`) as the rigid 3D guide, and bind each part 1:1 to the matching cutout-rig bone. Next fixes, which both critics agree on:
1. Give the bow lobes about 40% depth (they look paper-thin from the side), and lift the bun so it peeks above the bow in front.
2. Push the shoulder pivot outward and limit arm roll so the sleeve doesn't clip into the chest. Push the skirt shell out about 2% so legs don't poke through at the hem; let the skirt bone tilt with the leading thigh in a stride.
3. Shorten the B legs about 10% and make the boots chunkier.
4. Trim the 2mv bangs 1-2 px higher so both eyes read in SE at 48 px. This is a mesh property: the SE camera was verified as correct.

The hy3d rig (`v2/hy3d/scripts/rig.py`) can load these parts with rigid parenting and no weights. That removes the sleeve-web and skirt-tear artefacts the HY3D strand reported.

## AB4 (adopted reference, 2026-10-26, after the lead's fix list)
- `out/AB4/` (parts + `pivots.json` with bone/parent/pivot in the glb frame, feet y=-1), `out/AB4_assembled.glb`, renders in `out/AB4/renders/` (incl. `sheet_AB4.png` AB3 vs AB4, 48px SE). Built by `scripts/fix_ab4.py` + `OBI=0 ARMPIV=top scripts/finalize.py AB4 AB4/parts out B/raw/katana.glb`.
- Crit: Argon 6/4/6/7, Opus 6/4/7/4 (AB3 in the same round: 5/6/4/5 and 5/5/5/3). Bow thickness and bun pass; legs/boots, shoulders, skull partial; iso SE face still small (true 3D projection of the deep bob at 30 deg; turnD iso_SE cheats) -> keep hand-placing the SE face in pixels.
- Rig notes for HY3D: bind each part rigidly; rotate arms about pivots.json shoulder points and limit forward arm swing (~60 deg) so the hand stays off the obi; tilt the skirt bone with the leading thigh in stride.
