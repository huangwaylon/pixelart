# r19: sprites baked from Blender model B (round 2) vs S4_hd

## Files
- `compare_idle_8dir.png`: idle frame 0 for all 8 directions, at 1x, 2x and 8x. Rows are S4_hd, B at true proportions, and B with a chibi retarget.
- `faces_8x.png`: S, SE, E and SW heads.
- `walk_8dir.gif`: the S4_hd walk next to an 8-frame walk keyed on the B rig, for both B versions.
- `sheets/`: B sheets, 48x64, rows = directions, laid out like our sheets.
- `metrics.json`: the numbers quoted below.

## How it was made
1. `pipeline/blender_bake.py` (run with `blender -b`) poses the 39-bone rig and renders three Cycles passes at 12x per direction:
   - **ID pass:** colour role, body part and depth.
   - **Normal pass.**
   - **Shadow pass:** hard sun from our key-light direction.

   The relaxed idle has arms about 8° off the body and slightly bent elbows; the walk is procedural. The camera is our ortho camera at 16°. Scale puts the hair crown 33.5 px above the pivot, which matches S4_hd. The outline hulls, the modelled eyes and the face lines are hidden.
2. `pipeline/blender_sprites.py` hands the bake to the unchanged S4_hd `Scene.render_base` through a fake tracer. Everything after that is the existing pipeline:
   - majority vote over 144 samples per pixel
   - S4_hd ramps and bands
   - inner lines, despeckle, closed outline with sel-out, ring trim, bow shine and the orphan pass
   - kawaii_hd cels placed per eye at the projected Blender eye centres
3. **Chibi retarget:** head bone scaled 2.8 (neck weights above the chin moved to the head), thighs scaled 0.7, side locks swung back 25°.

## Verdict: no improvement for 48x64; keep S4_hd

**Better:**
- **Walk:** the true-proportion walk has real leg articulation: knees, a stride and arm swing come straight off the rig.
- **Fewer jaggies:** silhouettes have slightly fewer 1-px jaggies (idle: 0.8 true and 0.6 chibi, vs 1.5 for S4_hd).
- **Bow:** the bow reads as two clean loops with a knot in N, NE and NW.
- **Clean bake:** the bake is noise-free with consistent lighting, and needs no SDF tuning.

**Worse:**
- **Proportions:** at 6.5 heads the true figure is a 6-px-wide stick. Its face is 3 px wide, the eyes are 1.7 px apart (S4_hd: 5.3) and the cels don't fit, so there is no face in S.
- **Chibi retarget:** the eyes get to 4 px apart, but the long, wide hair scales with the head. It covers the scarf, coat and arms in every direction except S, SE and SW, which gives 7 brown-blob views out of 8.
- **Profile:** in E and W the side hair hides the face.
- **Hair:** the hair loses structure. The thin highlight band falls below the majority vote, so there is no crown shine, and the bangs read as a flat cap or two horns.
- **Legs:** in chibi they are 1-2 px wide.

**Gemini** (`docs/review/gemini/r19_blender_sprites.md`) agrees: do not adopt either version. It flags lost costume and silhouette, a cramped 7-px face, a flat hair mass, noisy bangs and earmuff-like bow spans. It suggests borrowing only the bow knot for the S4_hd back views.
