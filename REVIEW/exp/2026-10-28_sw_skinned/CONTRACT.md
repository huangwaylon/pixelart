# Contract: skinned rig + dynamic motion (swordswoman), 2026-10-28

The owner's feedback on the rigid-parts rig H2 animations: *"body parts are not connected, the animation and poses
look stiff and unnatural. The joints look off and unnatural. Need more dynamic movement, more movement details across
the whole body, bouncing parts."*

Two people work in parallel and coordinate **only through this file and the paths below**. Each owns their own
section. Append to your own Status log, and never edit the other person's section.

- **Rigger (R)** owns `rig/` and `render/`. Builds a single connected, skinned mesh plus an armature, and a renderer
  that turns a motion file into 8x hi-res passes, pixel frames and GIFs.
- **Animator (M)** owns `motion/`. Authors the motion and simulates the secondary (spring) bones, writing
  motion files in the format below.

Root: `/Users/waylonhuang/Documents/other/pixelart/REVIEW/exp/2026-10-28_sw_skinned/`

## Skeleton (fixed names, Blender convention: .L = character's left)
**Body (FK, driven by M's keys):**
`root` (ground, carries world translation) → `pelvis` → `spine` → `chest` → `neck` → `head`.
`pelvis` → `thigh.L/R` → `shin.L/R` → `foot.L/R` → `toe.L/R`.
`chest` → `shoulder.L/R` → `upper_arm.L/R` → `forearm.L/R` → `hand.L/R`. Fingers are optional, one `hand` bone is enough at 96 px.

**Secondary chains (driven by M's spring sim; R must create and weight them):**
- `hair_front.L.1-2`, `hair_front.C.1-2`, `hair_front.R.1-2` (bangs), parented to `head`
- `hair_side.L.1-3`, `hair_side.R.1-3` (side locks), parented to `head`
- `hair_back.1-3` (back of the bob), parented to `head`
- `bun`, parented to `head`
- `bow.L.1-2`, `bow.R.1-2` (lobes), plus `bow_knot`, parented to `head`
- `sleeve.L.1-2`, `sleeve.R.1-2` (bell sleeves), parented to `forearm` / `upper_arm`
- `skirt.F|FL|L|BL|B|BR|R|FR.1-2` (8 panels around the hem), parented to `pelvis`
- `obi_tail.1-2` (only if the design has one; it may stay static)

R may add helper bones, such as twist or corrective bones, but must not rename these. If a chain is impossible, record
it in R's status log, and M will then omit it.

## Rest pose
- A relaxed rest pose: **arms down at roughly 20° from the body**, sleeves hanging, feet hip-width apart, facing +Y = the
  character's front, Z up, metres, standing on Z=0.
- R exports `rig/rest_skeleton.json`: `{bone: {head:[x,y,z], tail:[x,y,z], roll, parent}}` in world rest space.
- M reads joint positions from this file once it exists. Until then, M uses `swordswoman/v2/hy3d/rigs/H2/parts/pivots.json`
  and `skel.txt` as a stand-in.

## Motion file: `motion/<action>.json` (written by M)
```json
{"action":"walk","fps":24,"loop":true,"frames":[
  {"t":0, "root":{"loc":[x,y,z]},
   "bones":{"pelvis":{"rot":[w,x,y,z]}, "thigh.L":{"rot":[...]}, "hair_side.L.1":{"rot":[...]}, ...},
   "scale":{"head":[1,1,1]} }, ...],
 "timing_ms":[...per frame display time...], "notes":"..."}
```
- `rot` is a quaternion, local to the bone's own rest orientation (Blender pose-bone `rotation_quaternion` semantics).
- `root.loc` is world space, in metres. For loops, M keeps it in place (no forward drift); a stride is foot-plant only.
- `scale` is optional, for squash and stretch. Use it sparingly and only on pelvis, spine, chest and head.
- The secondary bones are already simulated (baked) in the file, so R's renderer just plays the file.

## Render command (provided by R; M may call it to preview their own motion)
`<blender> -b rig/rig.blend -P render/render_motion.py -- motion/<action>.json <view> <outdir> [--preview]`
- `--preview` renders fast smooth-shaded frames at 2x for checking motion.
- The full render produces 8x passes (cel + outline + matid), the pixel chain (E2 k-centroid, palette lock, fix), a GIF at 4x,
  and a contact sheet.
- Views: SE first, then E and S. The camera is the game camera: 30° elevation, orthographic, 128 px cell, PPU 26.304,
  the same as rig H2 / `v2/g96`.

## Status log (R)
- (R writes here)

## Status log (M)
- (M writes here)
