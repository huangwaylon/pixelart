# r19: sprite bake from Blender model B r2

**Approach.** `pipeline/blender_bake.py` (headless Blender) poses the 39-bone rig into an idle and an 8-frame procedural walk. It yaws the character through the 8 directions under our 16° orthographic camera. At 12x it renders role/part/depth, normal and hard-shadow passes using the pipeline key light. `pipeline/blender_sprites.py` feeds these into the unchanged S4_hd `render_base` through a fake tracer. That pass does the majority vote, bands, inner lines, despeckle, sel-out outline, cleanup and kawaii_hd cels at the projected Blender eyes. There are two versions: true proportions, and a chibi retarget (head x2.8, thighs x0.7). Boards are in `00_REVIEW/r19_blender_sprites/`.

**Results.**
- **Better:** the bake is noise-free and has fewer jaggies (0.6-0.8 per frame vs 1.5). The rig walk has real knee and stride articulation, and the bow knot reads in back views.
- **Worse:** the 6.5-head design doesn't fit 48x64.
  - True proportions: a 3-px face with eyes 1.7 px apart (S4_hd: 5.3), so the cels don't fit.
  - Chibi: the eyes reach 4 px apart, but the hair scales with the head and buries the scarf, coat and arms in 7 of 8 views.
  - Both: the side hair hides the profile face, there is no crown shine, and the bangs are flat.

**Gemini.** Adopt neither version. It flags lost costume hierarchy, a cramped face, a flat hair mass, noisy bangs and an earmuff bow. It suggests borrowing only the dark bow knot for the S4_hd back views.

**Recommendation.** Don't adopt model B as the sprite source; keep S4_hd. Keep the bake tooling for a model built for sprites: about 2.5-3 heads, an 11-px face, side hair kept off the cheeks, a 10-12 px coat and a 2-px shine band.

**Porting the 13 clips to such a model.** Clips store semantic joint angles (spine, head, arm raise/spread/elbow, leg hip/knee/ankle) plus pelvis_drop, squash and z_px. The work:
- A field-to-`rot_bone` adapter: about 150 lines.
- Driving the ponytail, side-lock, bow-tail and scarf chain bones from ChainSim.
- Props as separate layers.
- About 1,000 bakes at 1.5 s each.

That's about 2-3 days including QA.
