# r12 Illustration plan: S4 portraits and full-body art, drawn rather than rendered

User: *"the full body and expression should not be based on the 3d model, it should be reimagined, rederived, like actual anime pixel art."* The r10 sheet is out. It reads as a render: no line hierarchy, flat masks for hair, a stiff torso, and a face that is a texture.

## Research (quick pass)
- **FE GBA**: mugshots on a 96x80 canvas with 16 colours including transparency. Eye and mouth frames are swapped onto one fixed bust, and lines are dark and coloured, never black. **HGSS trainers**: 80x80, 16 colours. **BW**: 96x96, animated.
- **GBA hardware**: 16-colour palettes from 15-bit colour, 240x160 screen. This is why 15-colour busts look the way they do.
- **Craft** (Medeiros on portraits and outlines; Keddy; our `japanese_dote_style.md`):
  - 2 cel tones plus a highlight per material.
  - Hair as 3-5 clumps (毛束) with an angel ring.
  - Sel-out on the outer line. Inner lines in a mid-dark tone only where parts overlap.
  - 中間色 AA inside the outline only, 1 px, on long shallow curves.
  - Eyes are the focus: upper lash 2 px thick, iris 2-tone plus a catchlight, lower lash 1 px or absent.
- spriters-resource and Bulbapedia returned 403. The sizes above are from standard references and are consistent with Wikipedia.

## Discussion

**ART DIRECTOR:** Consistency is the whole game. Across 10 expressions and 8 poses she must stay one girl: same eye shape, bow, and bangs points. Pure per-pixel authoring by an LLM drifts every time. Coordinates are where we are reliable, and pixel intuition is where we are not. I want the design to live in editable shapes, so a fix to the bow propagates everywhere.

**ILLUSTRATOR:** Agreed on shapes for the big forms: hair mass, clumps, coat, bow. But raster output from vectors gives mushy jaggies, banded tones, and 1 px orphans. Eyes and mouths at this size are pixel decisions, not curves. So shapes get us about 85% of the way, and the face and line cleanup must be pixel-native. Draw the face cels as small pixel grids, the way FE does.

**AD:** Then the rule is hybrid: vector for body and hair, pixel grids for face cels, hand overrides last. Every stage is a file in git, so a re-run reproduces it.

**ILLUSTRATOR:** One more rule. The design is a *model sheet*, not the 3D rig. Proportions for the art come from anime convention: bust head about 45% of canvas height, full body about 4.5 heads (semi-chibi, taller than the sprite). The 3D files are a colour and costume reference only.

## Decision: vector shapes, then pixel raster, then pixel passes, then overrides

**Files.** `data/illustrations/S4/<name>.json` holds:
- `canvas` (target px) and `design_scale` (8x).
- `palette` (`cw_oatmeal` plus `portrait_ext`).
- An ordered `layers[]`. Each layer has a `name`, `paths[]` (SVG path `d` strings, using M/L/C/Q/Z only), `fill` (a palette name), `line` (`auto`, `none`, or a palette name), and `z`.

Face cels go in `data/illustrations/S4/face/<part>_<state>.json` as character grids anchored at named points. Overrides go in `overrides/illustrations/<name>.png`, with alpha meaning "keep".

**Tool:** `pipeline/illustrate.py` (it can reuse `pixelrules.py`, `palette.py` and `qa.py`). It runs these passes:
1. Rasterize each layer with no AA, centre-sample at target size.
2. **Lines:** generate a 1 px outline per layer, made pixel-perfect (remove L-doubles, keep curve runs monotonic).
3. **Sel-out:**
   - Shadow side and bottom take the material's darkest tone or `outline`.
   - The lit top-left is one step darker than the fill.
   - Interior overlaps take the back part's shadow tone.
4. Shading layers (`*_shade`, `*_hi`) are authored as shapes, not computed. This avoids pillow shading.
5. Clean up orphans and 1 px stripes. Lock to the palette.
6. Composite the face cels, apply the overrides, run QA, and export at 1x, 2x and 4x.

**Layer names**, back to front:

`hair_back, bow, body, coat, coat_shade, scarf, scarf_shade, arm_*, hand_*, neck, face, face_shade, ear, hair_side_L/R, bangs, hair_shade, hair_hi, sidelock_L/R`

Then the face slots: `brow_L/R, eye_L/R, mouth, blush, sweat, fx`.

**Canvases.**
- Bust: 96x96, shoulders up. Head about 44 px tall, eyes about 9x11 px.
- Full body: 96x160, about 4.5 heads.
- Model sheet: 3 x 96x160, front, 3/4 and back.

**Palette.**
- The bust may use at most 24 of the master 32 colours.
- New ramp `portrait_ext` (6 colours):
  - `skin_shade2` (cool rose midtone)
  - `hair_hi` (warm angel ring)
  - `iris_0`, `iris_1`, `iris_2` (teal eyes, dark to light)
  - `line_skin` (deep rose-brown sel-out)
- Roles:
  - Line colours: `outline`, `plum_0`, `teal_0`, `line_skin`.
  - Eyes: `ink` lash, `iris_*`, catchlight `snow_3`.
  - Blush: `red_2` hatched, never a solid blob.
- 2 cel tones plus a highlight for each material.

**Line rules.**
- Outer line 1 px, closed in value, sel-out.
- No black inside the figure.
- 中間色 AA only inside the outline, 1 px.
- Flat tops of at least 3 px on round shapes.
- Bangs: 3-4 points. Hair: 3-5 clumps, each tapered and lined on one side.

**Expressions.** One shared bust base; only the slots change.

**Iteration.** Edit the shapes, re-run, view the 4x and the 1x side by side. Any fix to a shape propagates to every deliverable that uses that layer.

## Deliverables (r12)
1. **Model sheet:** front, 3/4 and back at 96x160, plus a turnaround of head and bow. This is the canonical reference.
2. **Bust base** (3/4 facing left) with 10 expressions:
   - neutral, smile, laugh, surprised, sad, angry, embarrassed (blush plus sweat)
   - determined, worried, sleepy/content (closed eyes)
3. **Bust, front view:** neutral and smile, to test whether the swaps hold.
4. **Full-body poses (8):**
   - idle (hands clasped), wave, point/explain, hands on hips (determined)
   - surprised recoil, shy (scarf to mouth), cold shiver, cheer/jump
5. A 16-colour stress variant of the neutral bust, to prove the GBA-grade read.

## Review checklist
- [ ] Reads as anime pixel art, not a render: line hierarchy, clumped hair, drawn eyes.
- [ ] Same girl everywhere. Overlay the eye, bow and bangs from the model sheet: within 1 px.
- [ ] Silhouette is recognisable at 1x on snow, navy and the dialogue-box colour.
- [ ] Lines are pixel-perfect: no L-doubles, monotonic curve runs, flat tops of 3 px or more.
- [ ] Sel-out is correct per material. No black interior lines, no outward AA.
- [ ] No pillow shading or banding. Light comes from the top-left.
- [ ] Palette lock passes. Bust uses 24 colours or fewer. No orphan pixels.
- [ ] Expressions read at 1x without labels. Brows and mouth carry the emotion; eyes are not swapped wholesale.
- [ ] Every image is reproducible from git (shapes, cels, overrides) by a single command.
- [ ] Hand overrides are under 5% of pixels. If more, fix the shapes instead.
