# R2: reference images for image-to-3D (2026-10-30)

## Output layout (per character: mechanic, schoolgirl, astronaut, shorthair)
`refs/<id>/{front,left,back,right,fl34,fr34,head_front,head_side}.png` are 1024² RGBA images, alpha-matted. `512/` holds 512² copies.
`meta.json` maps each view to its camera yaw and source, and includes `hunyuan_mv` for the 2mv dict. `checks.json` holds the symmetry, consistency and matte numbers. `sheet.png` is the contact sheet:
red lines mark the feet baseline and head top, the blue line marks the detected neck row. `src.json` records which raw image, figure and flip each view comes from.
Rebuild with `.models/hy_omni/venv/bin/python refs/tools/post.py <id>`. That venv has rembg 2.0.69 and only the u2net model, so nothing new gets downloaded.

**Yaw convention:** 0 means the camera is in front. +90 means the camera is at HER LEFT, so she faces screen-left in `left.png`. ±180 is the back, and -90 is her right side.
`fl34` is +45 (camera front-left, she faces screen-left) and `fr34` is -45. This is the same convention as `swordswoman/v2/hy3d/inputsD`,
which 2mv already accepted (front/left/back/right). If a 2mv mesh comes out with the side profile mirrored, swap left and right.

**Framing:** all body views use the same scale. Body height is 0.86 of the canvas, with the feet baseline at y = 0.93. The x position is centred on the
bottom 20% of the silhouette (the feet/legs), not the bbox, so a ponytail or backpack doesn't shift the body. The 2mv/2.1 preprocessors re-centre to the bbox and scale by the longest side.
All our views are taller than wide, so height drives the scale and the views stay mutually consistent. The two head views share one scale.

## Pipeline
1. **Front first.** One call per character with the concept PNG as reference, plus the spec colours (hex), shapes simplified to the mesh tier (medium), and the shared POSE + STYLE blocks below.
   3:4 at 2K gives 1792×2400.
2. **Turnaround in one call.** The approved front is the reference. One 16:9 4K call (5504×3072) returns four figures in a row, each about 2900 px tall.
   Getting all four in one image gives the same scale, pose, colours and baseline far more reliably than separate calls.
3. **3/4 view:** one figure per call (3:4 2K), with the turnaround sheet as reference. For designs that are effectively symmetric, the other side is a mirror.
4. **Head sheet:** one 16:9 2K call giving a front and side bust.
5. **post.py.** It splits sheets into figures by connected components (hands of neighbouring figures overlap in x, so column gaps fail). It then mattes, normalises and checks.
   - Matte: flood fill of near-white pixels from the border. This keeps interior whites such as the tank top and blouse. Enclosed pure-white pockets (for example between touching legs) are removed
     when rembg also calls them background. For white-on-white designs, `"matte": "union"` uses a strict flood (min RGB ≥ 248/249) OR rembg u2net, with holes filled.
     The astronaut and schoolgirl use union. A plain flood with tol 232 ate the helmet top and part of the blouse sleeve.
   - Wrapper `tools/gen.py` = `swordswoman/tools/gemini.py` `call()` + `imageConfig {aspectRatio, imageSize}`; logs every call to `raw/calls.jsonl`.

## Prompt blocks that worked (full text in `tools/prompts.sh`)
- STYLE: *"clean stylized 3D character render like a modern 3D game model or vinyl toy (smooth matte materials, simple solid colour regions), soft flat even
  studio lighting from all sides, very gentle ambient-occlusion shading only, NO cast shadows, NO floor shadow, NO outlines or ink lines, NO text … Pure solid white background (#FFFFFF).
  Orthographic camera at the character's mid-height, no perspective distortion."* This turns the thick-outline 2D concepts into shaded 3D-toy renders,
  which are closer to what Hunyuan was trained on (rendered assets) and carry shape cues from soft shading. No ink outlines are drawn that could be read as geometry.
- POSE: *"neutral symmetric A-pose … arms straight and held out 35 degrees away from the body so there is clear empty space between arms and torso, hands open and relaxed with
  fingers together (not fists), palms facing the thighs, legs straight and slightly apart (feet hip-width, a clear gap between the legs), feet flat … head level"*. This worked first time for all 4.
- TURN: *"four full-body views side by side in one row … all the same size, same height, feet on the same baseline, identical A-pose … (1) FRONT identical to the attached
  image; (2) LEFT SIDE profile … (3) BACK … (4) RIGHT SIDE profile … In the side profiles the arms stay angled out to the side … not swinging forward or back."*
- Per-character "details to keep consistent" lines, such as the ponytail visible in side and back views, a solid back for the helmet, the backpack box, and the collar flap on the back. These are what got the back views right.
- For hair, say *"one smooth closed rounded mass / solid sculpted shell, no loose strands or side locks"*. All four hairstyles came back as clean closed shells.
- White subjects: *"off-white suit with soft grey shading so every edge stays readable against the white background"* helps, but rembg/union is still needed.

## What fails (Gemini 3 Pro Image)
- **Left/right is unreliable.** Asking for "(2) faces LEFT … (4) faces RIGHT" gave the opposite order for mechanic and schoolgirl, and **two left-facing profiles** for
  astronaut and shorthair. Always label views by inspection, never by prompt order. Fixes: mirror the good profile (astronaut, which only has a tiny chest patch that's asymmetric),
  or make a separate single-figure call ("her nose and toes point toward the RIGHT edge … this is the opposite side from the profiles in the sheet"). That worked first try for shorthair.
- **Two-figure 3/4 sheets fail.** Both figures came out turned the same way and only about 20°. Use single-figure calls.
- **3/4 yaw is under-rotated.** Asking for "exactly 45°" gives about 30–35° (mechanic, shorthair) up to about 40–45° (schoolgirl, astronaut). Extra anatomical cues (far eye foreshortened, far cheek
  hidden, near ear fully visible) moved shorthair from about 20° to about 30°. `meta.json` keeps the nominal ±45 and adds `yaw_note`. Don't feed the 3/4 views to a
  method that needs exact camera poses, or treat them as roughly ±35°.
- **Head close-ups drift in style.** The schoolgirl head came back with realistic brown irises instead of the body's dot eyes. The geometry (bob shape, bangs, ears) matches, so it's fine as a
  hair/face shape cue but not for texture. The mechanic head-side bust has a cut-off shoulder plane at the bottom, which is expected for a bust.
- **Proportions drift from the concepts.** The 3D renders are about 4.5–5.5 heads tall (shorthair most realistic) against about 3.5 in the concepts. The astronaut stayed chibi. If chibi proportions matter
  for the mesh, add "head is one third of total height" and re-run the front only. The turnaround follows the front.
- **Side profiles show the arm edge-on over the torso.** That is correct for an A-pose seen from the side, but it hides the torso depth outline at hip level. The front/back carry the arm gap.

## Checks (`checks.json`; mirror IoU = silhouette vs its own mirror, centred on x centroid)
| id | front sym | back sym | front vs mirrored back IoU | left vs mirrored right IoU | band-width rel diff F~B / L~R | neck row spread (px @1024) |
|---|---|---|---|---|---|---|
| mechanic | 0.972 | 0.982 | 0.965 | 0.996 | 1.1% / 0.2% | 10 |
| schoolgirl | 0.988 | 0.993 | 0.984 | 0.995 | 0.6% / 0.1% | 6 |
| astronaut | 0.996 | 0.989 | 0.991 | 0.992 (mirror) | 0.4% / 0.2% | 5 |
| shorthair | 0.933 (side-swept fringe) | 0.968 | 0.983 | 0.977 | 0.8% / 1.8% | 19 (3/4 views) |
Matte IoU flood vs rembg is 0.96–0.99 everywhere except astronaut back/head_front (0.88/0.90, white on white), which is why the astronaut uses union.
I spot-checked all 32 outputs on a dark background (no halos, holes or eaten edges after the fixes).

## Gemini budget
21 image calls in total: 4 fronts, 4 turnarounds, 4 head sheets, and 9 for 3/4 views and profiles, including retries. Everything is in `raw/` (raw outputs are kept, including rejects:
`mechanic_34_a` two-figure 3/4 failure, `shorthair_34*_a` about 20° 3/4, `*_front_a` alternate single fronts).

## Suggestions for R3
- 2mv: `meta.hunyuan_mv` (front/left/back/right). For Omni/2.1 single view: `front.png`. All views are already RGBA, so skip rembg.
- For hair or head fidelity, try a second pass on `head_front`/`head_side` alone (2mv with front plus side) and graft it, or use it as a visual check.
- If an extra view helps (methods that take N posed views, e.g. MV-Adapter or InstantMesh-style), use fl34/fr34 at about ±35°.
