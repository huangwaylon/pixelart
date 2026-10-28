# r20: a from-scratch Blender base model (pixel-art reference)

The user asked (verbatim): "use the gemini model argon and also claude opus 5.5, start from scratch to create a base
anime model that will be used for pixel art reference. Look at the existing good references from claude to understand
the character design. do not give any 3d models to the LLMs. use words + the good photo / art references." and
"use blender to create the models, iterate and improve".

There are two independent tracks, each building its own model from this brief:
- **Track G:** Gemini 4 Argon writes the Blender script.
- **Track C:** a Claude Opus 5.5 modeller.

Neither track sees any existing 3D model, mesh, .blend, render of an old model, or old modelling code. Each sees only
this text, the images in `work/r20/refs/`, and renders of **its own** model.

---

## 1. Why this round exists (lessons, in words)

- **6.5 heads is too tall.** A previous Blender model was about 6.5 heads tall and pretty in close-up, but at game size
  (about 44 px tall) it became a 6-px-wide stick with no room for a face.
- **Scaling the head bone after the fact failed.** It made the long hair bury the coat in 7 of 8 directions.
- **So this model must be built for the pixel camera from the start:**
  - big readable shapes;
  - hair that frames the body and never buries it;
  - a face with room for big eyes;
  - a BIG bow;
  - a clear coat A-line;
  - slim but not stick-thin legs.
- **It is a reference model.** Pixel artists will trace poses, volumes and turn angles from it. Clean, designed, readable
  forms beat surface detail. Every shape should look intentional from all 8 directions.

## 2. Reference images (`work/r20/refs/`)

**Character design (the canon).** These are the APPROVED hand-drawn art of this exact character. Match her design to
them.

| File | What it is | Take from it |
|---|---|---|
| `c1_turnaround_approved.png` | Front, 3/4, side and back full body | **The** design: proportions, coat cut, scarf, bow, hair silhouette in every view |
| `c2_front.png` … `c5_back.png` | The same turnaround, one view each, bigger | Close reading of each view |
| `c6_bust_3q.png` | 3/4 dialogue bust | Face: eye shape and size, bangs, side locks, collar, scarf knit |
| `c7_head_front.png`, `c8_head_side.png`, `c9_head_back.png` | Head close-ups | Bangs panels, ponytail root, bow shape from front, side and back |
| `c10_model_sheet_alt.png` | An earlier, also good, model sheet | The bow wings read from the front; button and belt layout |

**Model language (style only, not the character).** These are third-party images. Use them for how a stylised anime 3D
model is built. Do not copy their outfits, colours or likeness.

| File | What it is | Take from it |
|---|---|---|
| `ref2.png`, `ref3.png` | Stylised 3D women, front and 3/4 | Face construction: slim oval-to-heart face, narrow jaw to a small defined chin, slim neck; slim limbs, defined waist |
| `ref4.png`, `ref5.png` | Anime cel-shaded toon model, side and front | **The target modelling language:** clean toon forms, hair as a few large smooth layered sheets, blunt bangs, flat-shaded clothes with crisp folds, slim straight legs, small feet |
| `ref6.png`, `ref7.png` | Hand-painted stylised anime 3D character | Hair as big glossy sheets plus a voluminous ponytail made of layered clumps; small pointed chin |
| `ref8.png`, `ref9.png` | Portrait and bust sculpt | Face planes and surface quality only (ref8 is a real person: general style only, never likeness) |

## 3. The character (words)

**Who she is**
- Koyuki ("Yuki"), heroine of a cosy isometric mobile game set in snowy mountains.
- Cheerful, plucky, a little clumsy. Looks 19-20: cute and feminine, not childlike.
- Must read as "adorable anime heroine" in one glance.

**Style**
- Japanese anime toon model: smooth, clean, designed surfaces with no realism, no muscles and no lumpy blobs.
- Think of the toon model in ref4/ref5 crossed with a modern cute JRPG field model.

**Proportions: BASE build** (matches the approved turnaround; H = crown-to-chin head height, not counting hair volume)
- **Height:** 5.4 H.
- **Head:** big for the body, about 18.5% of height. Hair volume adds roughly 0.15 H on top and the sides.
- **Neck:** short and slender.
- **Shoulders:** 0.9 H wide, sloped, narrower than the hair mass.
- **Waist:** 0.75 H, the narrowest point. The belt sits about 2.05 H below the crown.
- **Hips:** 1.0 H. The coat hem flares to 1.6 H wide at mid-thigh.
- **Legs:** 2.4 H from hip to sole, knee at the midpoint. Slim but with real volume: one soft calf curve, slim ankles,
  slightly full thighs.
- **Curves:** a modest bust, a pinched waist and soft hips under the coat.
- **Arms:** slim. With the arms down, the hands reach the coat hem. Small round mittens.

**Head and face** (the most important part, see c6/c7/c8)
- **Head shape:** NOT a sphere.
  - A rounded cranium, and a soft oval face with full cheeks.
  - Below the eye line the jaw tapers to a small, softly pointed chin.
  - Front: a gentle heart/oval. Profile: a slight forward cheek curve, a tiny nose tip and a small chin, with the jaw
    line visible from ear to chin.
- **Eyes:** BIG anime eyes, about 0.22 H tall each.
  - Placement: set low (the eye centre is a little below the head's mid-height), about one eye-width apart.
  - Shape: rounded top lid, gently drooping outer corner (tare-me).
  - Lash and iris: a thick dark upper lash line with a small flick past the outer corner. Teal iris with a darker top,
    and a white catchlight.
  - Construction: model the eyes as shapes that sit in or on the face surface (shallow inset or conforming decals as
    geometry) so they turn correctly in 3/4 and side views. In profile the eye is a narrow wedge set back from the
    cheek.
- **Brows:** thin hair-coloured strokes just under the bang line.
- **Nose, mouth and blush:** a tiny nose (a small soft ridge or tip, almost no bridge). A small mouth. Faint blush
  ovals under the eyes (separate material).
- **Ears:** mostly hidden by the side locks.

**Hair: warm chestnut brown, built as designed sheets and clumps, never a smooth helmet and never random strands**
- **Bangs:** hime-style, blunt-cut just above the brows, in 3 panels with 2 small notches (centre panel widest). They
  have VOLUME: the bangs lift off the forehead and curve over it like a shell, with visible thickness at the cut edge.
  A slight forward overhang reads in profile (c8).
- **Side locks:** one flat lock per side in front of the ears, about 0.18 H wide. Each runs from the temple to the
  collarbone with a blunt cut, framing the cheeks without covering the face.
- **Back hair:** long and straight behind the shoulders, as a few broad layered sheets, with a blunt slight-V cut at
  hip level (base build). It stays BEHIND the arms and shoulders, so the coat, sleeves and scarf stay visible in the
  front and 3/4 views.
- **Half-up ponytail:**
  - Where: the upper hair gathers at the back of the crown, at about brow height in side view, under the bow knot.
  - Shape: ONE ponytail that swells to about 0.5 H thick, then tapers in a gentle S-curve to a sharp single point at
    waist level.
  - Construction: a few layered clumps (see ref6/7), not a single tube.
  - Silhouette: in side view the ponytail makes a clear arc behind the back.
- **Hairline and crown:** a smooth crown with slight volume, and a part/whorl implied by how the sheets flow from the
  crown.

**Bow: BIG teal satin ribbon at the back of the head, at the ponytail root. Signature.**
- **Loops:** two puffy teardrop loops. Tip to tip they are about 2x the head width, so in front view the wings stick
  out past both sides of the head (c1 front, c10) as two rounded teal shapes.
  - Each loop is pinched into the knot, has a thick rim, a hollow inner opening and one soft crease.
  - The loops angle slightly up and back.
  - From the front the wings must read as a bow, not as cat or bear ears: they sit behind the head, slightly lower and
    angled outward.
- **Knot and tails:** a small pinched centre knot. Two swallowtail tails (V-cut ends) hang down over the ponytail to
  about the shoulder blades.

**Outfit: cosy winter**
- **Scarf:** a chunky teal knit, double-wrapped high around the neck, about 0.3 H thick. Ribbed knit grooves run
  across the wrap.
  - ONE tail hangs down the front on **HER LEFT** (+X, the viewer's right in front view). It reaches the belt, has
    vertical rib grooves and a short fringe of light-teal tassels.
  - The scarf is identical in every view, and it hides the coat collar.
- **Coat:** cream/oatmeal, fitted through the bodice and waist.
  - Belt: a thin dark-brown belt with a small gold buckle.
  - Skirt: below the belt it flares to an A-line skirt with a few soft vertical folds, ending at mid-thigh in a slightly
    curved hem with a rust-brown trim band.
  - Buttons: 6 small gold buttons down the centre, 3 above the belt and 3 below.
  - Sleeves: long and slightly puffy, with rust-brown cuffs.
  - Back: the coat back is plain, with a centre seam on the skirt.
- **Mittens:** teal, rounded, with a small thumb.
- **Tights:** dark plum-charcoal, on slim legs.
- **Boots:** brown winter boots to mid-calf, with a cream fur/knit cuff, a rounded toe and a small low heel.

**Pose**
- A relaxed standing rest for a reference sheet. Arms down but held about 12-15 degrees away from the body, so the arm
  silhouette separates from the coat and the waist reads.
- Elbows very slightly bent; mittens relaxed.
- Feet slightly apart (about a fist), toes forward.

**Colours** (use these as material base colours; viewport `diffuse_color` MUST equal them)

| material | hex | material | hex |
|---|---|---|---|
| skin | #FCD6B4 | skin_shadow (optional) | #EBA586 |
| blush | #F4A0A0 | mouth | #8E2C4A |
| eye_white | #FFFFFF | iris | #2C9696 |
| iris_dark | #1C4C54 | lash (lashes, brows-line, pupils) | #20223E |
| brow | #6E3C3A | catchlight | #FFFFFF |
| hair | #A85A3A | hair_shadow (inner layers) | #6E3C3A |
| hair_hi (optional sheen band) | #D08658 | teal (bow, scarf, mittens) | #2A8C8E |
| teal_dark (inside loops, knot) | #1C4C54 | teal_light (fringe) | #6ACBB6 |
| coat | #F2E6CE | coat_shadow (inner/hem underside) | #D2BFA4 |
| rust (trim, cuffs) | #A85A3A | belt | #6E3C3A |
| gold (buttons, buckle) | #E2A434 | tights | #45435E |
| boots | #6E3C3A | fur (boot cuff) | #F2E6CE |

## 4. Second build: SPRITE build (same script, a parameter)

The same script must also produce a **semi-chibi game-sprite build** at **3.4 H** total. It must be BUILT, not
retargeted.

| Part | Sprite build |
|---|---|
| Head, face, bangs, side locks, bow, ponytail | Same shapes, same size relative to the head |
| Torso | Squashed |
| Legs | 1.1 H from hip to sole |
| Coat | Hem at mid-thigh still; the A-line flares a little wider (1.7 H) |
| Shoulders, waist | Slightly wider relative to height, so the torso stays at least 0.85 H wide |
| Back hair | Shorter: its cut ends at the coat waist/belt |
| Ponytail tip | Ends at about the belt |

The back hair must never cover the sleeves in the front, 3/4 or side views. The point of this build is that at about
44 px tall the face still has room for big eyes and the coat, scarf, mittens and boots all read.

Both builds are normalised so the top of the hair crown (not the bow) is at z = 1.0.

## 5. Technical contract

- **Script:** one Python script for Blender 5.2 (bpy, bmesh, mathutils, math only; no add-ons, no network, no files
  outside the output dir). Run as
  `Blender -b --factory-startup -P gen.py -- <outdir> --build base|sprite`.
  It starts from an empty scene (`bpy.ops.wm.read_factory_settings(use_empty=True)`) and saves `<outdir>/model.blend`.
- **Axes:** Z up, feet at z = 0, the character faces **-Y**, HER left is **+X**. Metres.
- **Construction:** anything inside Blender, for example:
  - bmesh-built and lofted geometry;
  - Subdivision Surface modifiers on low-poly cages (recommended for clean anime forms);
  - Mirror modifiers;
  - curves with bevel/taper for hair clumps and scarf tails, converted or left as curves;
  - shrinkwrap/solidify;
  - lattice or proportional deformations.

  Modifiers may stay live, since the render harness evaluates them. Aim for roughly 40k-200k triangles evaluated.
- **Objects:** one object per logical part, named clearly (e.g. `head`, `eye_L`, `bangs`, `sidelock_R`, `ponytail`,
  `bow`, `scarf`, `coat`, `sleeve_L`, `mitten_L`, `leg_L`, `boot_L`, ...). Materials are named as in the colour table.
  Each material's `diffuse_color` is its base colour (the harness renders with these). A simple toon node setup for
  EEVEE is welcome but optional.
- **Face framing:** create an Empty named `head_center` at the centre of the head (crown-to-chin midpoint, on the face
  centreline) with a custom property `head_h` = H in metres.
- **Rendering:** do NOT render in gen.py. The operator renders with the fixed harness:
  - `pipeline/tools/rounds/r20_render.py`: Workbench, flat material colours plus a soft studio shadow;
  - a front / 3/4 / side / back turnaround;
  - face close-ups;
  - 8 iso directions at 16° elevation;
  - an aliased ~44 px preview.
- **No rig** is required this round, but keep the limbs as separate objects with sensible origins (shoulder, hip) so
  that rigging later is easy.

## 6. Evaluation (each round)

1. Run both builds, render with the harness and compose boards (`pipeline/tools/rounds/r20_boards.py`).
2. Self-critique: compare against the c-references view by view.
   - Silhouette per view.
   - Head shape and face in front, 3/4 and side.
   - Bangs volume and panels.
   - Side locks.
   - Bow size and shape in front and back.
   - Ponytail arc in side view.
   - Scarf tail on HER left.
   - Coat A-line, buttons and belt.
   - Hands and boots.
   - The ~44 px preview: is there room for the face, and does the coat read?
3. Fix the top problems, re-render, repeat.
4. Art director review compares the two tracks against the canon (not against each other's internals).
