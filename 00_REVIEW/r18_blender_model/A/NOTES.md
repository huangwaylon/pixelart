# Modeller A: snowy-mountain heroine

**Approach.** All Python (bpy/bmesh) in `src/` (lib, head, body, outfit, hair, render, build). Rebuild: `blender -b -P src/build.py -- final all,cmp,export`.
- **Head:** half-ring cage with Mirror + Subsurf. Extra loops at jaw, chin, lips, nose. Normals transferred from an ellipsoid proxy give clean anime shading.
- **Face:** eye planes (sclera, iris layers, pupil, highlights), winged lash, crease, brows, mouth, lips, blush. Quad grids or ribbons, ray-projected onto the subdivided face.
- **Hair:** arched ribbons following the scalp, then Solidify + Subsurf. Shell cap, two-layer bangs with 3 notches, side locks, back sheets, lobed ponytail with clumps.
- **Cloth:** lofted shells with Solidify. A-line skirt with cosine folds and a wavy rust hem. Cable-knit scarf with tail and fringe on her left (+X).
- **Look:** toon materials (Diffuse, Shader-to-RGB, constant ramp). Inverted-hull outline, render only.
- **Iterations:** t0–t3 (head), v1–v11 (full figure), plus bow/chest detail sheets.

**Triangles at export: 84,144.** Head 10,764; Eyes 2,240; Body 1,152; Tights 3,408; Tights_Pelvis 288; Coat 12,064; Belt 264; CoatGold 2,304; Scarf 6,728; Mittens 4,200; Boots 7,344; Hair_Cap 3,520; Hair_Bangs 7,152; Hair_SideLocks 3,328; Hair_Back 7,328; Hair_Ponytail 5,660; Bow 6,400.

**Known issues**
- Slightly over the 80k target.
- No rig, UVs or textures; the face is geometry decals.
- Non-manifold edges are only open boundaries (neck, tights/boot openings, mitten cuffs, fringe roots, decals). Hidden parts intersect (body in coat, tights in boots).
- Faint hair seam at the back crown; spiky back-sheet tips; little strand detail.
- From the front, the bow can read a little like ears.
- Simple legs (little knee/ankle shape), straight sleeves, slightly angular shoulders.
- Soft, under-defined lips and chin in profile.
- About 5.5 heads per the brief, so chunkier than ref4/ref5.
