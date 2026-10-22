# R1 Art Director review: jump

**Verdict:** at 1x she reads as a **cream cupcake on a red sack**. The hat takes up the head, the face barely shows, the braids and scarf are missing as silhouette hooks, and the shading is muddy (1010 orphan pixels).

## Camera: switch to 18 deg (change DECISIONS.md, `render.camera_elevation 26.565 -> 18`)
At 18 deg the face and scarf read in S/SE/SW and the hat stops being the main shape. The mismatch against the 2:1 world isn't noticeable at this size. 26.6 buries the face.

## Top 8 fixes, in priority order
1. **Shrink the hat.** Change `beanie` radii `[10.7, 9.6, 10.6] -> [10.4, 7.6, 10.2]` and its clip d `0.26 -> 0.20`. Change `beanie_cuff` center y `12.7 -> 12.4`, radii `[11.1, 1.7, 10.7] -> [10.8, 1.4, 10.4]`. The dome top drops from y 20 to 18 and the brim stays at y 11, so no extra forehead gets covered. Target: hat no more than 45% of head height.
2. **Make the pom a separate ball.** Change the pom tip `radius 2.7 -> 2.2`, anchor y `19.8 -> 18.6` (to follow the lower hat), `seg_len 2.4 -> 3.0`. It currently fuses into an onion tip.
3. **Fix the bangs.** Delete `bangs_C`. Change `bangs_L/R` radii y `2.0/2.2 -> 1.4` and center z `8.0 -> 8.6`. They read as dirt.
4. **Reduce face shadow.** Change bands `"4"` `[-0.05, 0.45, 0.88] -> [-0.35, 0.40, 0.85]`. Right now `skin_0` covers half the face in E/W/SE.
5. **Lift the hair mass.** Back views are a brown helmet. Change bands `"3"` `[-0.05, 0.55] -> [-0.30, 0.45]` so `hair_1` dominates. Change `hair_cap` clip_all d `-0.78 -> -0.55` so the hair stops at the nape and the hood or scarf shows.
6. **Make the braids stick out.** Change `braid_L/R` anchor x `±8.0 -> ±9.2`, y `4.6 -> 5.6`, rest_dir x `±0.45 -> ±0.85`, widths `[2.1, 1.8] -> [2.4, 2.2]`, seg_len `3.3 -> 3.6`.
7. **Make the scarf read.** Change `scarf_front`/`scarf_back` widths `-> [3.0, 2.8, 2.6]`, segments `3 -> 4`, stiffness `30 -> 18`. Ban `mustard_0` on the scarf (ramp floor = `mustard_1`), because brown on red reads as a stain.
8. **Clean up the parka; chunkier feet.**
   - Parka: set `hem` radii y `1.4 -> 2.2`, move `hood` center z `-4.4 -> -5.2`, and drop inner lines between same-material torso parts. This kills the `parka_0` blotches.
   - Feet: `bootcuff` radii `-> [3.4, 1.4, 3.4]`, `boot` radii `-> [2.9, 2.3, 3.8]`.

## Also
- `expressions.png` crops too high (hat only). Center it on the face anchor.
- Lilac `cream_0` rim dots are noise. Use `cream_0` only under the cuff.
- Fix the SW f3 edge-touch, and normalize height to 41-42 (currently 41-45).
