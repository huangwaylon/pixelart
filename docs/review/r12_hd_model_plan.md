# r12 - HD reference model for S4

**Now:** S4 is 42 ellipsoids plus 2 chains (11 segments), rendered by the analytic raycaster. `jump_sc` (8x14 frames) builds in 43 s. The turnaround shows beaded hair, slab bangs, egg boots and ball hands.

## 3D artist
Ellipsoids can't make sharp hair tips, flat-cut hime locks, open bow loops, crisp hems, soles or mitten thumbs. I need tapered cones, rounded boxes, tori, subtraction (V-cuts, grooves) and soft blends at joints. Caveat: 1 px is about 1.33 units, so detail below about 1 px can't be its own pixel. It still improves silhouette and shading. Every part carries `lod`: `all` (sprites, sized 1 px or more) or `ref` (hi-res refs and STL only).

## Software engineer
- **(a) SDF + sphere tracing:** deterministic JSON, and returns the same `(t, prim, normal)` buffers. Speed fix: a bounding ellipsoid per part. The existing ray-ellipsoid code gives each 8x8 sample tile a candidate list and a [tmin, tmax] interval, so each ray evaluates only about 15 parts. Fixed 48 steps + 4 bisection, float64. Target: at most 3x the current time.
- **(b) Marching cubes + raster:** needs a remesh per frame or skin weights, plus a numpy z-buffer. **Use for export only.**
- **(c) DCC import:** no Blender here. It bypasses chargen and variants, and needs weight painting. **Rejected.**

## Decision: (a) renders; numpy marching tetrahedra exports
- **Downstream unchanged:** a hard min across materials keeps colour borders crisp. Smooth-min applies only inside a `blend` set. Face cels, line-art passes, `_smooth_field`, bands and QA are untouched.
- **Skinning:** a part is rigid on one bone, or takes `bones: [[b, w], ...]` (blended matrices, for skirt panels). The chain sim is unchanged. Chain parts sweep a tapered cone along the Catmull-Rom points instead of beads.
- **Legacy:** variants without `"model": "hd"` keep the old raycaster, byte-identical.
- **Export:** `reference/model_<pose>.stl` (binary, about 100k triangles, under 5 MB, shows in GitHub's viewer) plus `.obj/.mtl` with palette colours. Poses: rest, idle, jump apex.

## Detail list (S4, about 180 parts)
- **Hair:**
  - Crown cap with a part-line groove and an 8-point whorl.
  - 12 crown clumps sweep to the bow.
  - Back curtain: 5 chains x 2 sharp clumps.
  - Ponytail: 5 twisted sub-clumps ending in 3 points.
  - Hime bangs: 7 points, with the centre pair split.
  - 2 flat-cut side locks (2 clumps each), plus 2 temple wisps (`ref`).
- **Bow:** 2 open flattened-torus loops with creases, a grooved knot, 2 chain-driven V-cut tails.
- **Head:** chin cone and cheek fullness. Nose and ears are `ref`.
- **Coat:**
  - Bodice blended with the bust, 4 princess-seam grooves.
  - Stand collar, placket with 4 buttons.
  - Belt band, buckle frame (subtracted hole) and tongue.
  - A-line cone with 10 box pleats, 16-scallop hem band, 2 pocket flaps.
- **Sleeves:** capsules blended at the elbow, 2 crease rings, torus cuff.
- **Mittens:** palm rounded box, thumb at 35 deg with a gap, ribbed cuff.
- **Scarf:** 2 rotated knit tori, knot, flat ribbon tail ending in 6 fringe capsules.
- **Legs:** tights as thigh capsule, calf cone, knee blend.
- **Boots:** shaft, fold-over cuff with rim, toe-box blend, sole 0.6 with welt, heel 1.2, back seam. Laces and eyelets are `ref`.

## Data format
chargen emits `parts` next to `primitives`:
```json
{"name": "bang_3", "bone": "head", "shape": "rcone",
 "params": {"a": [0, 4.6, 7.4], "b": [0.3, 2.1, 8.0], "ra": 1.1, "rb": 0.05, "flat": 0.55},
 "rot": [0, 0, 4], "material": "hair", "group": "head",
 "blend": {"set": "bangs", "k": 0.5}, "op": "union", "lod": "all"}
```
- **Shapes:** `ellipsoid | rbox | capsule | rcone | torus | cone`. `op` is `union | subtract | intersect`; a subtract cuts only its own set.
- **Optional `detail`:** `pleats | ridges | scallop` with `n` and `depth`.
- **Chain parts:** `"chain": "pony", "sweep": {"clumps": 5, "twist": 40, "tip": "sharp"}`.
- **Variant JSON:** `"model": "hd"`, `part_overrides`, `add_parts` and `remove` mirror today's `prim_overrides` / `add_prims`.

## Phases
1. **M1: engine + export + HD hair/bow.**
   - Code: `pipeline/sdf.py` (primitives, smin, ops, culled march), `render_sdf()`, `pipeline/meshexport.py`.
   - Content: S4 ellipsoids converted to parts, plus the full hair and bow set.
   - Gates:
     - Legacy-only parts reach silhouette IoU of 0.98 or more against the current build.
     - `--verify` is byte-identical.
     - `jump_sc` builds in under 130 s.
     - The STL renders on GitHub.
     - Old-vs-new turnaround and sprites published to `00_REVIEW/r12_hd_model/`.
2. **Coat:** belt, buckle, buttons, pleats, hem, collar, scarf with knot and fringe.
3. **Limbs:** sleeves and cuffs, mittens, tights, boots.
4. **Motion + polish:**
   - Skirt panels weighted to the hips, swept bow tails.
   - New QA rules: `lod: all` features under 1 px are flagged, SDF/chain penetration is checked.
   - Re-render the r11 clips, the hi-res sheet and the per-pose STLs.
