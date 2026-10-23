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
