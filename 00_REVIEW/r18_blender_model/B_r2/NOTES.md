# Modeller B: snowy heroine (Blender 5.2, all procedural Python)

## Approach
- **Head:** an implicit form built from lofted cross-section profiles, plus nose, lips, ears and neck. A quad lat-long cage is ray-projected onto that form. Rows and columns cluster at the eye line, nose, mouth and chin, giving those features dedicated loops.
- **Eyes:** separate almond eye planes with a procedurally painted iris texture. Winged lashes, crease, brows, mouth and blush are projected strips (FaceLines).
- **Body, limbs, coat, scarf, mittens, boots:** curve lofts. The coat's bodice gets a Shrinkwrap pass onto a torso proxy. The skirt has radial fold modulation.
- **Hair:** surface-following sheet patches (cap with flow grooves converging on the gather, layered bangs with 3 notches, broad V-tipped back sheets), custom lens-profile sweeps (side locks, 11 ponytail clumps around a swept axis), real Blender curves for loose strands, and a highlight band.
- **Bow:** teardrop-path puffy ribbon loops, a pinched knot, and V-cut tails.
- **Shading:** EEVEE toon (Diffuse, Shader-to-RGB, constant ColorRamp, Emission), key and fill suns, and inverted-hull outline objects (collection "Outlines", not exported).

## Stats (export: Head at subsurf 1, everything else at cage)
- 79,616 triangles.
- 85-100% quads per object.
- 0 non-manifold edges.
- 18 named objects; one material per colour role.
- Height 1.60 m, feet on Z=0, facing -Y, A-pose.

## Known issues
- From the front, the bow lobes read slightly like earmuffs.
- Brows sit under the bangs, so they are mostly hidden.
- Scarf cable-knit is subtle at full-body scale.
- Skirt folds show only at the hem silhouette.
- Sleeves are fairly tube-like, and there are no hands under the mittens.
- No rig. No Mirror modifier: symmetry is generated in code.
- GLB/OBJ carry flat base colours, not the toon ramp.

## Round 2 (AD review and user feedback)
- **Profile (user's top priority):** sculpted a midline displacement profile into the head form: sloped forehead and brow ridge, sellion dip, nose bridge, an upturned 14 mm tip with a crisp underside, philtrum, upper lip forward of the lower, mentolabial fold and chin shelf. The face front is wedged so the recessed eyes sit behind the bridge, and the midline keeps real normals so the nose catches a toon shadow. Side locks moved back off the cheek. Renders: `final_r2_profile_set`, `_profile_vs_ref6`, `_profile_96px(_x4)`.
- **Bangs** arc about 15 mm off the forehead, with deeper notches and one zig-zag crown band. **Brows** are projected over the fringe.
- **Bow:** A's perky loop shape, 0.32 m wide, tilted 17° up, 2 creases per loop, a 25 mm pinched knot and 120 mm V-cut tails.
- **Back hair:** widened to about 0.34 m (A's fan), irregular asymmetric tips.
- **Normals and outlines:** normals transferred from a hair proxy and an ellipsoid face proxy. Outlines are now Solidify modifiers about 40% thinner, tinted warm brown (dark teal on teal parts) and masked off the face front.
- **Legs and boots:** knee and ankle taper (ankle about 0.6x calf), shaped shaft, 10 mm sole, fuller fur cuff.
- **Scarf:** A's drape with twisted cable ribs; matte knit material.
- **Production:**
  - UVs: smart-project on every mesh, with one shared hair atlas.
  - Rig: 39 bones. Humanoid core plus chains for the ponytail (4), side locks (3+3), bow tails (2+2) and scarf tail (3).
  - Weights: heat weights for body and clothing; hand-cleaned skirt and neck; chain weights for hair and accessories.
  - LODs: 81.4k / 43.5k / 16.1k triangles.
  - Exports: GLB ×3 (with skin), FBX, OBJ, and `model_lods.blend`.
  - Materials: one slot per role; the unused Lip slot is gone.
- **Known issues:**
  - LOD2 has 21 non-manifold edges from decimation.
  - Seams come from smart-project, not hand-placed.
  - Body skin pokes through the raised shoulder in extreme poses.
  - The highlight band still reads slightly "stitched".
