# r12 Illustration plan: S4 portraits and full-body art, drawn rather than rendered

User: *"the full body and expression should not be based on the 3d model, it should be reimagined, rederived, like actual anime pixel art."* The r10 sheet is rejected. It reads as a render: no line hierarchy, flat hair, a face that is a texture.

## Research
- **FE GBA**: mugshots on a 96x80 canvas, 16 colours including transparency, eye and mouth frames swapped on a fixed bust, dark coloured lines. **HGSS trainers**: 80x80, 16 colours. **BW**: 96x96, animated. **GBA**: 16-colour palettes, 15-bit colour, 240x160 screen.
- **Craft** (Medeiros, Keddy, our `japanese_dote_style.md`):
  - 2 cel tones plus a highlight per material.
  - Hair as 3-5 clumps (毛束) with an angel ring.
  - Sel-out on the outer line. Mid-dark inner lines only at overlaps.
  - 中間色 AA inside only, 1 px.
  - Eyes are the focus: upper lash 2 px thick, iris 2-tone plus a catchlight.

## Discussion

**ART DIRECTOR:** Consistency is the whole game: 10 expressions and 8 poses, one girl. Per-pixel authoring by an LLM drifts. We are reliable with coordinates, not with pixel intuition. The design has to live in editable shapes, so one bow fix propagates everywhere.

**ILLUSTRATOR:** Shapes, yes, for the big forms: hair, clumps, coat, bow. But vector raster gives mushy jaggies, banding, and orphan pixels. Eyes and mouths at this size are pixel decisions. So I draw the face cels as small pixel grids, FE-style, and a cleanup pass fixes the lines.

**AD:** Hybrid, then: vector body, pixel face cels, overrides last. All files in git, so every run is reproducible.

**ILLUSTRATOR:** And the anatomy comes from a *model sheet*, not the rig. In the bust the head is about 45% of the height. The full body is about 4.5 heads. The 3D files are a costume and colour reference only.

## Decision: vector shapes, then pixel raster, then pixel passes, then overrides

**Files.** `data/illustrations/S4/<name>.json` holds:
- `canvas`, `design_scale` (8x), `palette`.
- `layers[]`, each with `name`, `paths[]` (SVG `d`, using M/L/C/Q/Z), `fill` (palette name), `line` (`auto`, `none`, or a name), and `z`.

Face cels go in `data/illustrations/S4/face/<slot>_<state>.json` as character grids at named anchors. Overrides go in `overrides/illustrations/<name>.png`.

**Tool:** `pipeline/illustrate.py`, reusing `pixelrules`, `palette` and `qa`. Passes:
1. Rasterize with no AA (centre-sample).
2. 1 px pixel-perfect lines per layer: remove L-doubles, keep curve runs monotonic.
3. Sel-out:
   - Shadow side takes the darkest tone or `outline`.
   - The lit top-left is one step darker than the fill.
   - Overlaps take the back part's shadow tone.
4. Shading comes from authored `*_shade`/`*_hi` layers, never computed. This avoids pillow shading.
5. Clean up orphans and stripes. Lock to the palette.
6. Composite the face cels and overrides, run QA, export at 1x, 2x and 4x.

**Layers**, back to front:

`hair_back, bow, body, coat(_shade), scarf(_shade), arm_*, hand_*, neck, face(_shade), ear, hair_side_L/R, bangs, hair_shade, hair_hi, sidelock_L/R`

Then the face slots: `brow_L/R, eye_L/R, mouth, blush, sweat, fx`.

**Canvases.**
- Bust: 96x96, shoulders up, eyes about 9x11 px.
- Full body: 96x160.
- Model sheet: 3 x 96x160.

**Palette.**
- The bust uses at most 24 colours.
- New ramp `portrait_ext` (6 colours):
  - `line_skin` (rose-brown sel-out)
  - `skin_mid` (cool rose midtone)
  - `hair_hi` (warm angel ring)
  - `iris_0`, `iris_1`, `iris_2` (teal eyes, dark to light)
- Roles:
  - Line colours: `outline`, `plum_0`, `teal_0`, `line_skin`.
  - Lashes: `ink`. Catchlight: `snow_3`.
  - Blush: `red_2` hatched, never a solid blob.

**Line rules.**
- Outer line 1 px, closed in value.
- No black inside the figure. AA inside only.
- Flat tops of 3 px or more.
- Bangs: 3-4 points. Hair: 3-5 clumps, each tapered and lined on one side.

## Deliverables
1. **Model sheet:** front, 3/4 and back, plus a head and bow turnaround. This is the canonical reference.
2. **Bust** (3/4, facing left) with 10 expressions:
   - neutral, smile, laugh, surprised, sad, angry
   - embarrassed, determined, worried, content (closed eyes)
3. **Front bust:** neutral and smile, to test the slots.
4. **Full-body poses (8):**
   - idle, wave, point, hands on hips
   - recoil, shy (scarf to mouth), shiver, cheer
5. A 16-colour neutral bust, as a stress test.

## Review checklist
- [ ] Reads as drawn anime pixel art, not a render.
- [ ] Same girl everywhere: eyes, bow and bangs within 1 px of the model sheet.
- [ ] Silhouette reads at 1x on snow, navy and the dialogue box.
- [ ] Lines are pixel-perfect: no L-doubles, monotonic runs, flat tops of 3 px or more.
- [ ] Sel-out is correct per material. No black interior lines, no outward AA.
- [ ] Light comes from the top-left. No pillow shading or banding.
- [ ] Palette locked, 24 colours or fewer, no orphans.
- [ ] Expressions read at 1x without labels.
- [ ] Every image rebuilds from git with one command.
- [ ] Overrides are under 5% of pixels. If more, fix the shapes instead.
