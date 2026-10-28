# Pixel cleanup guide: Akane ("Crimson Ronin") sprites

Owner: Art Director (pixel). Status: **v1, 2026-10-24.** This is the rulebook every cleanup artist follows. The QA lead scores against the checklist in section 5.

**Authority order:**
1. `docs/design_bible.md` and `docs/palette.json`. These are locked, and this guide never overrides them.
2. This guide.
3. Gemini critiques, which are input only. Section 6 lists the points we rejected.

**Sources digested:**
- `docs/reviews/gemini_feedback_model_rounds.md` (rounds 1-5)
- `docs/reviews/gemini_pixel_critique_base.md`, a fresh per-direction critique of the base idle f00
- `archive/scratch/ai_pixel_test/gemini_opinion.txt` and `compare_sheet.png`
- the design bible and palette
- the earlier hand-cleanup project's `docs/DECISIONS.md` and `docs/review/pixel/H1_*.md` (`~/Documents/other/pixelart`)
- palette-code dumps and lint of `pixel/base/idle` (round 6)

**Validated mock-ups** are in `docs/img/pixel_guide/`. Each shows the base (left) and the template from this guide painted on a scratch copy (right):
- `test_face_S.png`
- `test_face_SE.png`
- `test_face_E.png`
- `test_bow_S.png`
- `test_sword_S.png`

They are scratch proofs and not deliverables: nothing was written to `pixel/overrides`.

---

## 0. Ground facts

| | |
|---|---|
| Cell | 128x128. Pivot (64,104) = the ground point under the root, in every frame and direction. |
| Height | About 56 px from sole to bow top. Head H is about 17 px. The face is about 13 px wide in S. |
| Palette | 22 colours, locked. The tools reject anything else. There is no white sclera, no orange, no extra pink. |
| Camera | Iso body camera. Ground contact uses 2:1 math. |
| Light | Key light from screen top-left, camera-locked. Pink rim (`pink_0`) from back-right. |
| Base | `pixel/base/idle/<DIR>/fNN.png`. **Never edit the base.** Edit only through `tools/pixel/px.py` or the editor, and give a reason for every pixel. |
| Intent | `pixel/source/idle/<DIR>/fNN.png` is the 512 px toon render, exactly 4x the cell. Use it to understand shapes. It shows the hero katana, not the sprite katana. |
| Inspect | `.venv/bin/python tools/pixel/asciidump.py DIR x0 y0 x1 y1 [fNN] [base\|clean]` prints palette codes. Use it to quote coordinates in reasons. `tools/pixel/tonestats.py` prints the R4 tone budgets. |

**Pixel-code legend** for every pattern in this guide:

| Code | Colour | Code | Colour |
|---|---|---|---|
| `#` | outline `#1a1220` (= `leather_0` = `dark_0`) | `.` | transparent |
| `s0 s1 s2` | skin shadow / base / light | `_` | leave as-is |
| `h0 h1 h2` | hair shadow / base / sheen | | |
| `r0 r1 r2 r3` | red: violet underside / crimson shadow / base / coral light | | |
| `l1 l2` | leather base / top-edge | | |
| `d1` | dark base (shorts, gloves, shoe uppers) | | |
| `t0 t1 t2` | steel spine / body / glint | | |
| `e0 e1` | iris top / iris lower | | |
| `p0 p1` | pink shadow + rim / pink scarf base | | |
| `v0` | purple lace | | |

**Base state (round 6, idle, lint `--src clean` with zero overrides):**

| | |
|---|---|
| Orphans | 1464 |
| Jaggies | 664 |
| Notches | 575 |
| Spurs | 356 |
| Banding | 99 |
| Flicker | 69 |
| Doubles | 56 |
| Off-palette | 0 |
| Outline gaps | 0 |

Tone audit of f00:
- **Hair is 61-80 % `h0`** in every direction. That is the "flat dark helmet / dark blob" Gemini has flagged since round 1.
- **Red is 55-65 % `r1` in W and NW.** Those skirts read as standing in shadow.
- **The scarf is mostly `p0`, not `p1`.** It merges with the rim light.

---

## Best-practice rules (from research)

*Added by the research pass, 2026-10-24.* The full write-up, with quotes and URLs, is in `docs/pixel_art_best_practices.md`; the section numbers below (§) refer to that file. These rules **add to** sections 1-5 and don't replace them. If one seems to conflict with an R-rule, the R-rule wins until the AD decides, and the conflict is flagged as a "Research note" beside that rule. Main sources: Derek Yu (Basics, Common Mistakes), Cure's Pixel Joint tutorial, Saint11's glossary and blog, Slynyrd Pixelblogs 1/5/6/8/22/29/41/47/55, Lux/Pixel Parmesan (AA, dithering, isometric, colour), and the Dead Cells 3D-pipeline deep dive.

**Noise and clusters**
- **BP1. No pillow shading.** Never shade inward from the outline. The shadow is one cluster on the bottom-right of each form and its undersides, and the highlight is one smaller cluster on the top-left plane. A ring of `r1`/`h0`/`s0` just inside the outline on the lit side is a defect. Render fresnel and AO passes cause this, so strip them. (§1.3)
- **BP2. Kill banding.** Neighbouring tone clusters may not have edges that run parallel and end on the same row or column for 3 or more steps. Fix in this order: merge the two tones, stagger the cluster ends, vary the band width. (§1.4)
- **BP3. No dithering on the character.** Collapse any checkerboard or random two-tone alternation from the render into the majority tone. Dither is for VFX only, and only as a regular 50% pattern. (§1.5, matching the bible)
- **BP4. Diagonal-only links are weak.** A tone pixel that touches its cluster only at a corner reads as speckle. Give it an edge contact or remove it. (§1.2 C3)

**Light and shading taste**
- **BP5. Sharp terminator.** Shadow meets base in one step. Don't stack 1 px intermediate tones along the terminator. (Saint11: "in pixel art we favor sharp transitions to avoid banding.") (§5.2)
- **BP6. Compress form.** A sphere or cylinder gets at most base + shadow + highlight. Use the sphere and cylinder templates in §5.2 for the head, bun, bow knot, arms and legs.
- **BP7. AO is 1 px.** Contact shadow is a single row of the next-darker tone only where one form overlaps another (bow on bun, collar on neck, corset on skirt, inside the cuff). Remove every soft multi-tone AO gradient and every baked cast-shadow blob from the render. (§5.4)
- **BP8. Hard vs soft materials.** Steel gets high contrast and tiny highlights (single `t2` pixels are legal). Cloth, skin and hair get wide, low-contrast clusters and **no single-pixel highlights**. Hair gets one curved sheen band, never dots. (§5.5)
- **BP9. Squint and greyscale.** Squinted, each major part shows about one light and one dark mass. Desaturated, hair, red, corset, skin and ribbons all still separate. Also flip the frame horizontally once to catch drawing errors. (Derek Yu, §4.5)

**Lines and outline**
- **BP10. No exterior AA, ever.** The ring of silhouette pixels holds only `#` or the lit-side material-dark tone (R9). Any other colour there is AA against an unknown floor. Internal AA is allowed only on long, shallow steps, and never on 1:1 or 2:1 lines. (§2.4, §3.1)
- **BP11. Gaps are not sel-out.** Sel-out here works by **colour** only. Never delete exterior pixels to "soften" the lit side (Cure: sel-out by removal only works on a known background). (§3.2)
- **BP12. Broken inner lines for soft overlaps.** Where a soft part folds over another (sleeve over skirt, bow loop over bun), you may break an interior line instead of anti-aliasing it, as long as R18's no-1-px-break rule is respected on hard edges. (Lux, §3.2 item 5)

**Colour**
- **BP13. Value before hue.** Fix any separation problem by changing a value at the contact pixel, not by adding or shifting a hue. Hue shift is baked into the locked ramps, so cleaners never hand-mix. (§4.1-4.4)
- **BP14. Terrain, dark floor and colour-blind checks.** Check each direction on light stone/sand, mid grass and a dark dungeon floor, plus a deuteranopia/protanopia simulation. Red dress, pink ribbons and skin must still separate. (§4.6-4.7)

**Animation**
- **BP15. Keys first, then propagate (matches R44).** Delete in-betweens that add no readable change instead of polishing them. Fewer, stronger frames beat many soft ones. (Slynyrd #8; Dead Cells, §8.3)
- **BP16. Static parts are copied, never redrawn.** Anything that doesn't move relative to its parent is pasted from the cleaned key and offset by whole pixels. This is the cure for the boiling and flicker that Dead Cells left unsolved. (§8.1)
- **BP17. Secondary motion.** Ribbons, skirt tails and bun strands lag 1-3 frames (R51) and overshoot by at most 1-2 px. Plot the ribbon-tip positions across the loop: the path must be a smooth arc, with no zig-zag. (§8.6)
- **BP18. Planted feet don't slide.** On contact frames (walk/run f0/f4, attack plants), the planted foot's pixels are identical between frames while it is planted. (§8.7)
- **BP19. Smear frames** (attacks): a clean crescent with monotone curves, at most 3 smear tones from the palette roles, no dither, fading by width rather than noise. The body outline stays closed. (§8.5)

**3D-render triage**
- **BP20. Repaint vs tweak.** Repaint a part from scratch on its own layer, using the render as a placement guide only, when any of these is true: it is 4 px or less in its thin dimension and must read (face, hands, feet, blade, hook, ribbons, strands); about 30% or more of its pixels need changing; it flickers or boils across the loop; or it has more than 3 shadow clusters or a pillow ring. Otherwise tweak it in place. (Saint11 3D-ref: "we will just redraw the whole thing"; §9.3)

---

## 1. Global style rules

### 1.1 Palette, ramps, tone budget
- **R1. Zero off-palette and zero semi-alpha pixels.** Never add a colour. If a ramp seems to lack a tone, the shape is wrong, not the palette.
- **R2. Each pixel snaps to its own material's ramp.**
  - Hair never borrows `dark_1`.
  - Skin never borrows `pink`, except the blush (R27).
  - The scarf never uses `red_3`. Its lit edge is `skin_2`.
- **R3. Three tones per material, at most.**
  - Red has a 4th tone, `r0` (violet), but only on occluded undersides: inside the skirt, under the sleeves, and under the bow loops.
  - Steel is 3 tones. Eye is 2 tones plus the `t2` glint.
  - Leather is `l1` mass, an `l2` 1 px top edge, and `#` recesses.
  - Dark is `d1` plus `#`.
- **R4. Tone budget per frame**, measured over the material's pixels. Tolerance is ±5 points. Count with `tools/pixel/tonestats.py`.

  | Material | Shadow | Base | Light | Notes |
  |---|---|---|---|---|
  | Hair (incl. bun) | `h0` ≤ 35 % | `h1` ≥ 50 % | `h2` 5-12 % | `h0` goes only on the bottom/right shadow side, under the bun, under the bow, and in lock partings |
  | Red cloth | `r1` ≤ 40 % | `r2` ≥ 45 % | `r3` 5-12 % | `r0` ≤ 5 %. **The same in all 8 directions**, because the light is camera-locked. NW/W may not be darker than SE/SW. |
  | Scarf | `p0` ≤ 35 % | `p1` ≥ 60 % | `s2` ≤ 10 % | |
  | Skin | `s0` 15-30 % | `s1` majority | `s2` ≤ 10 % | `s2` on lit thigh, shoulder and cheek only |
- **R5. Colours per frame:** at most 22, the palette. A typical frame uses 19-22. `v0` purple is at most 3 px per frame and sits only at her **right upper-arm lace**.

### 1.2 Light
- **R6. Key light comes from screen top-left in every direction, fixed to the camera, not the world.**
  - Highlights (`r3`, `h2`, `s2`, `t2`, the eye glint) sit on top-left-facing surfaces.
  - Shadows (`r1`, `h0`, `s0`) sit on bottom-right-facing surfaces.
  - Highlight positions are screen-fixed, so in W the glint is still top-left.
- **R7. Rim light:** a 1 px `pink_0` line on the back-right silhouette, just inside the outline. It goes on hair, bun, bow loops and sleeve-cuff edges only.
  - It is never 2 px thick, and it never goes on skin, the face, or the scarf.
  - It covers at most 60 % of any contour's length. Break it at the lower third of the head and where the contour turns away, so it doesn't read as a second outline (Gemini, NW).
  - It never touches scarf pink: put 1 px of the material's own tone between them.
- **R8. No cast shadows across the face** (Gemini r1). The face is flat `s1`. `s0` goes only on the chin row, the far-side cheek column in 3/4, and under the bangs where they overhang by 1 px.

### 1.3 Outline (selective, coloured: "sel-out")
- **R9. The exterior silhouette is a closed, 1 px, 8-connected line.**
  - The bottom and right (shadow side) and every ground contact use `#`.
  - The top and left (lit side) use the material's darkest ramp tone:
    - red: `r1`
    - skin: `s0`
    - hair: `h0`
    - scarf: `p0`
    - leather: `#`
    - steel: no lit-side outline (R20)
  - Where the lit-side tone sits next to the material's own base tone and reads as a gap at 1x, use `#`.
- **R10. No doubles.**
  - No 2x2 or L-shaped outline clumps. Gemini found these between the thighs, under the chin and at hem corners in every direction.
  - If removing an outline pixel keeps the line 8-connected, remove it. lint's `double` flag finds these.
- **R11. Interior lines only at depth breaks** between parts of similar value: sleeve against skirt, arm against body, bun against head, legs against each other.
  - Use the front part's darkest ramp tone, not `#`. The only exceptions are the corset recesses and leg/heel contacts.
  - **No lines inside the face**: no lines around the blush or under the eyes (Gemini r1).
- **R12. No notches and no spurs.** That means no 1 px dent into the silhouette and no 1 px tooth out of it. The deliberate exceptions are the skirt-tail points, the collar points, the heel point and the hook tip.

### 1.4 Clusters, orphans, noise
- **R13. No orphans.** Every pixel has a same-colour 8-neighbour. Legal exceptions, which must be justified in the reason:
  - the eye glint `t2`
  - the mouth `s0`
  - blush `p0` (1-2 px)
  - a buckle `t1`
  - the heel point
  - the blade tip
  - the purple lace
  - the kashira cap
- **R14. Cluster minimums.**
  - Shading and highlight clusters on hair and cloth: ≥ 3 connected px, and ≥ 4 on the skirt.
  - Feature widths: ≥ 2 px for scarf ribbons, sleeve cuffs, legs, hands and skirt tails.
  - Small slivers flicker, so merge any tone island under the minimum into its neighbour tone (G5 lesson from the previous project).
- **R15. Kill the speckle.**
  - Remove single `l1`/`#` dots inside the skirt. Gemini called them "dirt splatters" in S, SE, E and N.
  - Remove skin pixels trapped inside hair, except the ear (R29) and the cheek sliver in NE/NW.
  - Remove `e0`/`t2` pixels on hair or the silhouette edge.
  - Remove pink pixels inside the collar.
  - Corset buckles are at most 2 `t1` px. Drop rivets, stitching and extra pouches.

### 1.5 Lines and curves (anti-jaggy)
- **R16. Straight edges use one clean ratio for their whole length:** 1:0, 1:1, 2:1, 3:1 or their transposes. Never mix 2-2-1-2 on one straight edge.
- **R17. Curves use monotone run lengths.** Runs only grow or only shrink along an arc, for example 3-2-1-1-2-3. Patterns like 3-1-3 or 1-4-1 are jaggies, and lint's `jaggy` flag finds them.
- **R18. Inner lines follow the same rules.** No 1 px breaks in an interior line (lint `inner_break`).

### 1.6 Value separation
The bible rule is that touching colours must differ by ≥ 1.8x in luminance or by a strong hue jump. These pairs are the traps found in the base:

| Pair | Ratio | Rule |
|---|---|---|
| `p1` scarf vs `s1` skin | **1.07** | **Fail.** They may never touch. The skin pixel against the ribbon becomes `s0`, because the ribbon casts a shadow (`p1`/`s0` = 1.97). |
| `p0` vs `s1` | 1.18 | **Fail.** Never put `p0` against skin. The ribbon edge facing skin is `p1`, and the skin side is `s0`. |
| `p0` vs `s0` | 1.57 | Weak. Add a 1 px `#` or `r1` separator where it occurs. |
| `p1` vs `r3` | 1.80 | Borderline. Where the scarf crosses coral highlight, the red side becomes `r2`. |
| `p0` vs `r3` | 1.44 | **Fail.** Same fix as above. |
| `p0` / `p1` vs `r2` | 2.6 / 3.3 | OK. This is where ribbons should read. |
| `s0` vs `r2` | 1.67 | Weak. At the collar-jaw join use `r1` against `s0`, or `r2` against `s1`. |
| `h0` vs `#` | 3.5 | OK. Hair can carry the outline. |
| `h1` vs `l1` | 2.5 | OK. The bible still demands an `l2` or red pixel between corset and hair. |
| `t2` vs `s1` | 1.6 | Weak. Where the blade crosses skin (legs), keep its `#` shadow line. |

### 1.7 Katana: blade, guard, hook, hilt, hand
The sword is held in her **LEFT hand** in every direction. The 3D render is handedness-correct, so never mirror it or move it to "the other side". Proof: `test_sword_S.png`.

- **R19. Blade.**
  - 2 px wide: `t2` glint edge on the lit (upper-left) side and `t0` spine on the shadow side, drawn as two parallel 1 px stairs. This is the "1 px blade line, doubled". The bible minimum is 2 px.
  - One step ratio for the whole length (R16). The S base mixes 2-2-1-2 at x76 y100, which is wrong.
  - The tip tapers to a single `t2` pixel, capped by `#` below and right.
  - *Research note: a `t2` edge running the full length of the blade puts the palette's brightest tone along a long line. Sources favour "small and focused" highlights on glossy objects (Saint11 glossary; Cure on single-pixel speculars). Consider `t1` for most of the lit edge, with a 2-4 px `t2` glint where the blade faces the top-left light. The glint can then travel along the blade in swings, which sells the motion. Keep the full-length `t2` only if a `t1` edge fails the light-terrain readability test (`t1` vs light floors). This is an AD decision; R19 stands until then. See best-practices §5.5.*
  - In idle the blade angles 25-35° out of the silhouette and sticks out past it in every direction, N/NE/NW included.
- **R20. Blade outline: 1 px `#` on the shadow side only.**
  - No lit-side outline. The base draws `# t2 t0 #`, which makes the blade 4 px fat and saw-toothed.
  - Where the blade crosses the body, the body pixel on the blade's lit side becomes the body's own shadow tone, which keeps the blade separated.
- **R21. Guard bar (tsuba).**
  - A straight 1 px line of `t1`, 4-6 px long, perpendicular to the blade, centred on the blade root.
  - `t2` on its lit end, `#` under its shadow side.
  - Never a blob. The base S/W guards are 5x4 `t0`/`t1` lumps.
- **R22. Hook (kagi).**
  - A **3 px crescent**: a 1 px-thick arc from one end of the bar, ending in a `t2` tip.
  - It needs a ≥ 1 px transparent gap inside the curve so the crescent's negative space reads.
  - Outline only on its outer (shadow) side.
  - It is ≥ 3 px in every frame and direction and is checked by hand (bible). The direction of curl follows `refs/1.png` and the source render: the points curl back toward the hilt. Never flip it between frames.
- **R23. Hand and hilt.**
  - Glove: `d1` 2x2 blob with 1 `s1` finger pixel.
  - Hilt: at least **2 px beyond the fist** in S, SE, SW and W (near-hand or front views), as `#` with 1 `r2` diamond. It ends in a 1 px `t1` kashira cap.
  - In E/NE/N/NW the hand may be hidden by the body (3D). Don't invent it there, but the guard and hook must still show.
  - Every Gemini pass says "no hilt visible". This rule fixes that.

Hilt, guard and hook, S idle. This is the painted proof, dumped from the mock-up (cell x71-80, y89-100). The blade runs down-right at 2:1.
```
      71 72 73 74 75 76 77 78 79 80
  89  r2 r2 r2  #  .  .  .  .  .  .     sleeve cuff
  90  r2 r2 r2  #  .  .  #  .  .  .
  91  r2 r2 r2 r2  .  #  t2  #  .  .    hook tip t2
  92  r1 r2  #  r2 r2 .  .  t1  #  .    hook arc 1 px; open (transparent) side faces the hand
  93  r1  #  d1 d1  #  .  .  t1  #  .   fist d1 under the cuff
  94  r1 s1 d1  #  #  t1 t1  #  .  .    s1 finger | bar rises 2:1 to the right, into the hook
  95  r0 r1  .  t1 t1  #  #  #  .  .
  96   #  t2 t1  #  #  .  .  .  .  .    bar lit end t2 | # under the bar's shadow side
  97   .  #  #  t2 t0  #  .  .  .  .    blade root: t2 glint + t0 spine, # on the shadow side only
  98   .  .  .  .  t2 t0  #  .  .  .
  99   .  .  .  .  t2 t0  #  .  .  .    2:1 all the way to the tip
 100   .  .  .  .  .  t2 t0  #  .  .
```
Hilt beyond the fist, when visible (S/SE/SW/W), at any angle along the hilt axis: `t1` cap, then `#`, `r2`, `#`. For example, at a 1:1 diagonal going up-left from the fist:
```
 t1  .  .
  .  #  .
  .  . r2      <- 1 red diamond window; the rest of the wrap is outline-dark
  .  .  [fist d1]
```

### 1.8 Face templates
The face is a decal and must be **identical in every frame** of a direction, apart from translation by the bob (R50).

**Common rules:**
- **R24. Eye block.** Each near eye is 3 wide x 4 tall:
  - 1 row of `#` lash, extended 1 px outward into a wing
  - 3 rows of iris: `e0`, `e0`, `e1`
  - 1 `t2` glint at the iris top-left
  - No sclera (no colour exists for it). No second glint, and no `e0`/`t2` outside the eye.
- **R25. Placement.**
  - Eye rows are the same for both eyes. The base S right eye sits 1 row lower than the left, which is wrong.
  - The lash row touches the bang tips: the bangs cover the brows (Gemini r2-r5, bible).
  - The eye line sits slightly below the head midpoint.
- **R26. Mouth.**
  - Neutral: one `s0` pixel, 2 rows below the iris bottom, on the face centre column (in 3/4, shifted 1 px toward the facing side).
  - Combat/determined: 2x1 `s0`. Never 2 rows.
  - It may not touch an eye, the collar or the outline, diagonals included. If it can't fit, omit it rather than misplace it (previous-project rule 3).
  - No nose.
- **R27. Blush.**
  - One `p0` pixel under the outer corner of each visible eye, 1 row below the iris.
  - In profile, 1 `p0` behind and below the eye.
  - **Never `r1`/`r2`/`s0` under the eyes.** Gemini, W/SW: "reads as a bruise".
- **R28. Collar.** The red collar frames the jaw as a 2-3 px band. Chin row: `s0` where skin meets the collar, `r1`/`r2` per R9 and 1.6.

**S (front).** 13 px block, proof `test_face_S.png`. The block starts 3 rows above the lash and is centred on the face's skin centre column.
```
     0  1  2  3  4  5  6  7  8  9 10 11 12
B0  h0 h1 h1 h0 h1 h1 h1 h1 h0 h1 h1 h1 h0    bang locks, h0 partings lean screen-left going down
B1  h0 h1 h0 h1 h1 h1 h1 h0 h1 h1 h1 h0 h0    (swept to HER right)
B2  h0 h0 s1 h1 h1 h1 h0 s1 h1 h1 h0 s1 h0    lock tips point down; skin shows between tips
L   h0  #  #  #  # s1 s1 s1  #  #  #  # h0    lash rows, outer wing on each side
I1  h0 s1 t2 e0 e0 s1 s1 s1 t2 e0 e0 s1 h0    glint top-left of each iris
I2  h0 s1 e0 e0 e0 s1 s1 s1 e0 e0 e0 s1 h0
I3  h0 s1 e1 e1 e1 s1 s1 s1 e1 e1 e1 s1 h0
C1   _ p0 s1 s1 s1 s1 s1 s1 s1 s1 s1 p0  _    blush under the outer corners
C2   _ s1 s1 s1 s1 s1 s0 s1 s1 s1 s1 s0  _    mouth on the centre column; far-right jaw s0
```
- Columns 0 and 12 are the 1 px `h0` jaw strands (bible: they reach the jaw). They run down to the collar.
- The iris gap is 3 px, which is 1 eye-width (bible).

**SE (3/4 facing screen-right).** Proof `test_face_SE.png`. The far eye is compressed to 2 px and keeps ≥ 1 px of skin before the face outline. The far eye has no glint.
```
     0  1  2  3  4  5  6  7  8  9 10 11
L   h0  #  #  #  # s1  #  # s1 s1  #  .     near lash 4 wide (wing left) | far lash 2 | cheek | outline
I1  h0 s1 t2 e0 e0 s1 e0 e0 s1 s0  #
I2  h0 s1 e0 e0 e0 s1 e0 e0 s1 s0  #
I3  h0 s1 e1 e1 e1 s1 e1 e1 s1 s0  #
C1   _ p0 s1 s1 s1 s1 s1 p0 s1 s0  #
C2   _ s1 s1 s1 s1 s0 s1 s1 s0  #  .        mouth 1 px toward the facing side of centre
```
- **SW is the exact mirror of this block:** near eye on screen-right, far eye toward screen-left, and the glint *still at the top-left* of the near iris (R6).
- Base errors:
  - SE: a second glint at (66,73), and the far eye `e0` sitting on the outline at (70,72).
  - SW: the far eye is on the outline at (57,71-72), and the glint is not at the iris corner (62,73-74).

**E / W (profile).** Proof `test_face_E.png`. One eye, 2 px iris, recessed: **≥ 1 skin column between the iris and the front outline.** The lash wing points to the back of the head. In the template below, F is the front face outline.
```
     -7 -6 -5 -4 -3 -2 -1  F
B2   h0 h0 s1 h1 h0 s1 h1 s1      bang tips reach the brow line
L    h0 s1 s1  #  #  # s1 s1  #   lash 3 wide, wing on the back (-5)
I1   h0 s1 s1 s1 t2 e0 s1 s1  #
I2   s1 s1 s1 s1 e0 e0 s1  #      the front contour steps back 1 px under the eye (cheek to chin)
I3   s1 s1 s1 p0 e1 e1 s1  #      blush behind and below the eye
C1   s1 s1 s1 s1 s1 s1 s0  #      mouth: 1 s0 at the front column, 2 rows below the iris (when there's room)
```
- W is the mirror. In W the glint stays top-left, so it sits on the eye's front side.
- Base errors:
  - E: `e0` on the hair outline at (72,69), and `t2` on the face front at (70,72).
  - W: the eye is pressed against the front outline.

**NE / NW (back 3/4).** No eye, no glint, no mouth.
- The facing tell is a **2-4 px wide `s1` cheek/ear sliver** on the facing side under the hair, as one cluster:
  - `s0` on its bottom row
  - an `h0` jaw strand separating it from the collar
- Base error: NE has a `t2` on the edge at (72,71). Remove it.

**N (back).** No skin on the head at all, and the collar hides the nape (bible). See R33.

### 1.9 Bangs
- **R29. Bangs are chunky anime locks, never a flat bar.** Base S: the bottom of the hair is one straight `h0` row at y70.
  - 3-4 locks across the forehead, each 3-4 px wide, in `h1`.
  - Partings are 1 px `h0` diagonals leaning screen-left as they go down (swept to her right).
  - Each lock ends in a down-pointing tip, so there are 1 px skin V's between the tips.
  - The tips touch the lash row: there is no bare forehead (Gemini r2-r5 must-fix).
- **R30. Side locks and strands.** Two 1 px `h0` face-framing strands, one per side, running to the jaw (S/SE/SW). In 3/4 the near-side lock is 2 px.
  - The ear shows only in E/W: a 2x2-2x3 `s1` with `s0` bottom, ringed by `h0`, mid-head.
  - All other skin-in-hair is a leak (S (55,70), (72-73,70); N (54,71), (72,71)). Repaint it `h0`/`h1`.
- **R31. Hair mass.** Obey the R4 budget. `h1` is the mass.
  - The `h2` sheen is a **curved 2 px crescent band** following the skull, upper-left, 5-9 px long. It is never a flat horizontal dash (Gemini) or a tonsure ring (Gemini r3).
  - Back views (N/NE/NW) need the band too. They are currently "dead flat brown circles".

### 1.10 Bun
- **R32. The bun is a separate ball.**
  - About 7x6 px, round, high at the crown and set back (bible: 0.45 H diameter, 0.25 H back).
  - It gets its own `h1` mass, a 2-3 px `h2` highlight top-left, and an `h0` underside.
  - **Separation from the skull:** a 1 px line where they overlap, in `h0` on the lit side and `#` on the shadow side, curved (R17). Never a perfectly straight full-width `#` row: the S base has one at y57.
  - In N/NE/NW the bun must not merge with the head mass. Below the separator line, the head's first row is `h1`, not `h0`, so there is a value step on both sides of the line.
  - Placement per facing tells: the bun is behind the crown in E/W, and toward the camera-far side in NE/NW so that NE doesn't read as E.
- **R33. Back views: no nape skin.** The bible says the collar wraps fully and hides the nape. A skin band between hair and collar (N y75) is a gap: repaint it in collar red or hair.
  - The **bare back strip** below the collar is legal and required in N/NE/NW. It is one clean `s1` cluster with `s0` edges, separated from the scarf by R36.

### 1.11 Bow
- **R34. Bow.** It is **always two loops plus a knot plus two short tails.** Never one blob: the S/SE base is a fused `r2` mass.
  - Placement follows the bible: at the base of the bun, **on her right side of the bun**. That is screen-left in S/SE/SW and screen-right in N/NE/NW. **Do not centre it** (section 6).
  - Width is at most 0.85 H, about 14 px.
  - Each loop is an upright bunny ear, 3-5 px wide and 4-6 px tall, in `r2`, with a **2-3 px `r3` highlight at its top-left**.
  - Lit edge `r1`, shadow edge `#`, and 1 px `p0` rim on the back-right (R7).
  - Between the loops, a V notch (transparent) at the top, and a 1 px `r1` crease from the notch to the knot.
  - Knot: a 2x2 `r1` with `r0` underneath, where it ties onto the bun (`r0` is the only legal violet there).
  - Tails: 2 px wide `r2`/`r1`, 2-3 px long, ending in `#`, splaying away from each other.
  - From the front, at least one loop peeks above or beside the head. In N both loops must read.

Generic two-loop bow, about 10x10 (adapt the loop size to the facing; proof `test_bow_S.png`):
```
     0  1  2  3  4  5  6  7  8  9
0    .  . r1 r1 r1  .  .  .  .  .
1    . r1 r3 r3 r2  #  . r1 r1  .      two ears, r3 top-left of each
2   r1 r3 r2 r2 r2  #  r1 r3 r2  #
3   r1 r2 r2 r2 r2 r1 r3 r2 r2  #      r1 crease from the V notch down to the knot
4    . r1 r2 r2 r1 r2 r2 r2 r1  #
5    .  .  # r2 r1 r1 r1 r1  #  .
6    .  .  . r1 r1 r0 r1  #  .  .      knot 2x2 r1 over r0 (occluded underside)
7    .  . r1 r2  # r0  # r1  .  .
8    .  . r1 r2  #  .  # r2 r1  .      tails, 2 px wide, splayed
9    .  .  .  #  .  .  .  #  #  .
```

### 1.12 Scarf ribbons
- **R35. Ribbon shape.** Two ribbons from the back of the collar, each a flowing **S-curve, 2-3 px wide, tapering to 1-2 px at a cut or swallowtail tip**.
  - No straight planks, horns or sausages. The SE/E/W base ribbon is a single straight bar.
  - Edges follow R17.
  - In idle they hang mostly down, at most 1 H (about 17 px), and drift.
- **R36. Ribbon colour and value.**
  - `p1` base at ≥ 60 %, `p0` on the shadow edge and underside, `s2` for a 1 px lit edge only.
  - **Ribbon against skin: the skin pixel is `s0` and the ribbon pixel is `p1`, always.** This applies to the bare back in N/NE/NW and the shoulders in SE/SW. Never `p0` against skin, and never `p1` against `s1` (1.6 table).
  - Over red: fine as is, except over `r3` (section 1.6 table).
  - Outline: `p0` on the lit side, `#` on the shadow side.
  - No dark specks inside the pink (Gemini, NW).

### 1.13 Collar, shoulders, torso
- **R37. Collar.** A 2-3 px red band around the jaw: a tall funnel with points, and its V opening toward the facing side. In S/SE/SW the V shows skin at the throat.
- **R38. Shoulders, corset and pouch.**
  - Shoulders: 1-2 px bare skin (`s1`, `s2` on the lit side) between the collar and the sleeve top.
  - Corset: a solid `l1` band with a 1 px `l2` top-edge line, `#` recesses, and at most 2 `t1` buckle px. It is the value break of the body.
  - Hip pouch: a 2-3 px bump.
  - Thigh strap: 1 px `l1` where the left leg faces the camera.
  - The chest cord and gem are dropped. Purple per R5.
- **R39. Sleeves.** Wide bell cuffs at least 2 px thick at the hem.
  - An `r1`/`r0` inside where the opening shows, and `p0` rim on the back-right edge.
  - The cuff must end with a clean outlined edge. The SW base has a raw `r3` open to the background at the far-left sleeve tip.

### 1.14 Legs, feet, heels
- **R40. Legs.** 2-3 px wide, tapering from thigh to ankle (bible). The lit side is `s1`/`s2`, the shadow side `s0`, and the outline per R9.
  - No outline notches biting into the shin. S base: (59,101), (66,102).
  - The two legs have a ≥ 1 px gap or an `s0`/`#` separator, so they never fuse into one pillar (Gemini r2).
- **R41. Feet are 3 rows, read from the ground up:**
  - **ground row:** `#` sole, with a **1 px heel point** under the back of the foot
  - **above it:** `d1` upper, 2-3 px
  - **top:** a **1 px `s1` ankle** with a 1 px `#` strap pixel across it
  - Toe direction follows the facing. Both feet sit on the 2:1 ground plane, so the far foot is 1 px higher in SE/SW, never more.
  - The S base feet are 2x2 `d1` boxes with no heel, sole or ankle ("clubbed hooves").
  - No skin pixel at the toe tip.

Foot, SE-facing, toe to the right. This is a schematic: adapt the length to the facing.
```
  .  s1  .  .  .     1 px skin ankle
  #  #  d1 d1  .     strap pixel (#) across the instep, d1 upper
  #  d1 d1 d1  #
  #  .  #  #  #      heel point (left) | transparent arch gap | sole
```

### 1.15 Skirt hem
- **R42. Skirt hem.** The hem is **2-4 broad petal tails with clean points**. No 1 px icicles, teeth or holes. The E/N/NW/W base hems are "shredded".
  - Each tail is ≥ 3 px wide until its last 2 rows, and its edges follow R17.
  - Hem points are the only legal spurs on the skirt.
  - High-low in E/W (short front, long back). In S, the front slit is on screen-right (her left) and shows the shorts as a ≥ 2x2 `d1` cluster.
- **R43. Skirt shading.**
  - `r2` mass with `r3` on the upper-left of each panel and `r1` in fold recesses.
  - `r0` only inside or under the hem, where the inside of the skirt shows.
  - Folds are 2-3 broad diagonal `r1` wedges, not speckle.
  - Budget per R4, identical across directions.

---

## 2. Per-direction notes (round-6 base, idle f00; coordinates are in the 128 cell)

Each note lists the facing tells (bible §2), what is wrong in the base, and what to do.

**S (front)**
- **Tells:** face with eyes and blush, collar V toward the camera, both bell cuffs symmetric, slit on screen-right.
- **Face:**
  - Eyes are 1 row out of line: left lash y71, right lash y72.
  - The right iris touches the collar at (70,73-75).
  - No blush.
  - Replace the face with the S template (R24-R27).
- **Bangs and hair:**
  - The bangs are a flat `h0` bar (y67-70). Replace with R29 locks.
  - The hair is 63 % `h0`. Rebalance it (R4, R31).
  - Temple skin leaks at (55,70) and (72-73,70).
- **Bun and bow:**
  - The bun separator is a straight full `#` row at y57. Curve it (R32).
  - The bow's left mass is a flat `r2` blob. Carve loops, crease, knot and tails (R34).
- **Torso:**
  - The two `v0` at (56,82-83) are legal only if attached to the right upper-arm lace.
  - Remove the pink specks in the collar (Gemini).
- **Sword:**
  - The guard is a 5x4 blob at (73-80,91-96) with no hand.
  - The blade stair breaks at (76,100).
  - Redraw per R19-R23. The proof is `test_sword_S.png`.
- **Legs and feet:**
  - Feet: 2x2 `d1` boxes at (58-59,104-105) and (65-66,104-105). Redraw per R41.
  - Leg notches at (59,101) and (66,102).
  - Remove the double outline clump at the crotch.

**SE**
- **Tells:**
  - Face 3/4 toward screen-right, with a bigger near cuff.
  - The katana is in her left hand on the far (upper-right) side, so check that the blade sticks out past the skirt.
- **Face:**
  - A second glint at (66,73), and the far-eye `e0` sits on the outline at (70,72).
  - Use the SE template.
- **Hair:** 67 % `h0`. The near sideburn is a chunky square: make it a 2 px lock.
- **Bow:** one fused blob at (52-61,48-58) that swallows the bun. Split the loops and show ≥ 4 px of bun. The `r0` pixels at (55-56,56) are acceptable only as the knot underside.
- **Scarf:** the ribbon at (52-58,75-79) is a straight horn. Curve it per R35, and make sure it doesn't cross the face or arm with `p0` against skin.
- **Torso:** purple at the waist edge must sit on the arm, at most 3 px.
- **Sword:** guard and hook form a C-claw glued to the sleeve. Separate them with 1 px of background, and add the bar.
- **Feet:** tiny triangles. The far foot must be exactly 1 px higher than the near one.
- **Skirt:** remove the brown speckles and the 1 px teeth on the left hem.

**E (profile, facing screen-right)**
- **Tells:** profile with one eye, high-low skirt, bun clearly behind the crown, ribbons trailing behind.
- **Stray pixels:** `e0` on the hair outline at (72,69), and `t2` on the face front at (70,72).
- **Head:**
  - The eye touches the front outline. Use the E template, with 1 skin column of recess.
  - Hair is 77 % `h0`.
  - The 2 px skin column at (58-59,71-73) is the ear: make it a clean 2x3 ear (R30).
- **Bun and bow:** the bow sits like a visor on the front of the bun. Seat the knot at the bun base and keep both loops visible above. Don't move the bun.
- **Body:**
  - Arm, corset and skirt are a soup. Add an `r1` interior line where the near sleeve overlaps the skirt (R11), and make the corset band solid.
  - The shoulder/neck join merges skin, light red and pink. Apply 1.6.
- **Hem and feet:**
  - Rebuild the hem as petal tails (R42), especially the bottom-left icicles.
  - Feet need a visible heel point (R41).
- **Sword:** the far-hand katana appears in front of the skirt. That is 3D-correct (it angles forward and out), so keep the position. Clean only the guard shape and the stair.

**NE (back 3/4)**
- **Tells:** bun and bow fill the head, a 1-2 px cheek/bang edge on the facing side, skirt tails toward the camera, bun toward the camera-far side.
- **Stray pixels:** `t2` on the head edge at (72,71), and a purple pixel on the far waist edge (remove it if it is not on the right arm).
- **Head:**
  - Hair is 80 % `h0`, the worst of all directions. Needs the sheen crescent and `h1` mass.
  - The cheek patch at (65-71,70-75) is too boxy and protrudes. Reduce it to a 2-4 px sliver with an `h0` strand (1.8 NE/NW).
- **Bow:** a single flame. Show two loops.
- **Scarf:** the ribbon over the sleeve and guard is pink on light red with no separation. Use `r2` under it and a `p0` lit edge.
- **Back:** the bare back strip sits against the ribbon. Apply R36 (`s0` skin edge).
- **Hem and sword:**
  - The hem has 2 px sawtooth spikes. Fix per R42.
  - The hook points awkwardly. Follow the source and keep it at least 3 px.

**N (back)**
- **Tells:** bun and bow centred over the head, bare back strip, full long skirt tails, both ribbons visible and trailing.
- **Hair:**
  - 75 % `h0`, a flat circle. Add the `h2` crescent upper-left and the `h1` mass.
  - The rim on the right is dashed. Make it a continuous 1 px run over the upper 2/3, then stop (R7).
- **Nape:** skin strip at y75 (x60-61, 65-67) and skin specks at (54,71) and (72,71). Remove them (R33).
- **Bow:** only the right loop peeks out. Both ears must read above or beside the bun. Keep the bow on her right, which is screen-right here.
- **Scarf:** a `p1` wishbone at (63-64,79-81) lies flat on bare `s1` skin (ratio 1.07, invisible at 1x). Apply R36, and give the two ribbons separate S-curves that hang past the back.
- **Skirt:** the central `r1` curtain flattens the cylinder. Shade per R43, and turn the bright-red side wings into proper petal tails.
- **Feet and sword:**
  - The feet are 2 px nubs. Show the heel points.
  - The sword attaches to the skirt edge with a 2 px hook nub. The hook must be at least 3 px.
- **Lint:** `cx_drift` is 6.9 here. Check whether the sword ID pass is being counted in the feet centre before trusting the pivot report (R50).

**NW (back 3/4)**
- **Tells:** same as NE, mirrored by the camera. The cheek sliver is on screen-left.
- **Skirt:** about 65 % `r1`, a dark slab. Rebalance to the R4 budget. This is the biggest value fix in the set.
- **Scarf:** remove the dark specks inside the pink ribbon on the right.
- **Hair:** flat. The rim is a continuous inner border that bands like a double outline. Break it (R7).
- **Hem:** double-thick `#` corners at the bottom right (R10). A floating `r2` pixel at the bottom-centre tip.
- **Bow:** "two stubby horns". Make the loops 3-5 px tall per R34.
- **Feet:** the left foot is a flat slipper and the right is swallowed by the hem. Show both heels, or one heel plus a 1 px toe.

**W (profile, facing screen-left)**
- **Tells:** the mirror of E, but the katana hand is the near hand.
- **Sword:** the near arm is a stump and the sword comes out from under the hem with no hilt. Draw the fist, at least 2 px of hilt with an `r2` diamond, the bar and the hook (R23). The near sleeve must separate from the torso with an `r1` interior line.
- **Face:**
  - The eye is a slit against the front outline. Use the mirrored E template.
  - Remove the red/pink pixels under the eye. Blush is 1 `p0` (R27).
- **Body:**
  - Thick `#` clumping under the chin. Remove it per R10.
  - The skirt is 55 % `r1` at the back. Fix per R4.
- **Ribbon:** a jagged straight strip. Make an S-curve (R35).
- **Foot:** skin/black alternating "toes". Use the R41 foot.

**SW**
- **Tells:**
  - Face 3/4 toward screen-left. The katana is on the near (lower-right) side.
  - This is the cleanest base silhouette: protect it.
- **Face:**
  - The far eye sits on the outline at (57,71-72).
  - There are two glints, at (62,74) and (63,73).
  - A dark red/brown "bag" sits under the near eye.
  - Use the mirrored SE template.
- **Sleeve:** the far-left sleeve tip is raw `r3` against the background with no outline. Add an `r1` lit-side outline (R9/R39). The screen-left arm is a shapeless blob: add an `r1` cuff line and the `d1` glove.
- **Legs:** remove the vertical dark lines between the knees (R40). The ankle straps must be single `#` pixels, not diagonals (R41).
- **Hair:** the bangs notch is off-centre. Follow R29, with the lock partings leaning toward her right (screen-right here). Hair is 61 % `h0`.

---

## 3. Animation consistency rules

- **R44. Fix one frame, then propagate.** Clean one key frame per direction (f00), get AD sign-off, then carry it with `px.py copy` and adjust per frame. Every frame's reason cites the key frame.
- **R45. No flicker.** A pixel may not toggle A→B→A over consecutive frames while its 5x5 neighbourhood is static (loops wrap f07→f00). lint `flicker` must be 0.
  - Tone islands that appear in one frame only get merged (R14).
  - Highlights (`h2` crescent, bow `r3`, `t2` glint) keep their size and position relative to the part in every frame.
  - *Research note: this is right for idle. For run, dash and attacks, Slynyrd (Pixelblog 55) found that a hair highlight frozen in place "looks odd", while one that jumps is "distractingly noisy". Best is a small shift (≤ 1 px) in a consistent rhythm with the head bob. Highlights should never toggle on and off. The blade glint may travel along the blade during swings (see the R19 note).*
- **R46. Volume preservation.** Per part, the opaque pixel count varies by at most ±3 % across a loop, and by at most ±2 px for the head, bun and bow.
  - The idle breath is a 1 px bob of the upper body. It is not a resize: the head, face and bow are translated, never redrawn smaller or larger.
  - *Research note (optional polish, P3): sub-pixel animation is "just AA applied to an animation" (Lux, Pixel Parmesan). An in-between breath frame can shift only the shoulder or collar highlight edge by one tone step instead of moving the whole upper body. This softens the 1 px pop without touching the face lock. Never apply it to the exterior outline, because that would create exterior AA.*
- **R47. Face lock.** The face decal is pixel-identical across all frames of a direction after removing the bob offset.
  - The eye is never redrawn and the mouth never moves relative to the eyes.
  - If the base face changes between frames, overwrite it with the template copy.
- **R48. Sword lock.**
  - In idle the sword is rigid with the hand. The guard, hook and hilt pattern is pixel-identical apart from translation.
  - The blade keeps one step ratio across the loop, and the hook stays at least 3 px in every frame.
- **R49. Tone budgets are stable.** R4 percentages vary by at most ±3 points frame to frame, and the light, rim and highlight side never swap.
- **R50. Pivot lock.**
  - The feet baseline (lowest body row, sword excluded) is constant in every frame of a direction: lint `y_drift` 0. NE and NW currently show 1.
  - The feet centre `cx_drift` is ≤ 0.5 px in idle.
  - The root lands on (64,104) in every direction. SE/SW sit 1 px lower (baseline 107 vs 106): confirm against the 2:1 foot-depth rule, and do not "fix" it by shifting a single frame.
  - Never move the whole sprite to fix a pixel problem.
- **R51. Secondary motion.** Scarf, sleeves, skirt tails and bow loops lag 1-3 frames behind the body and trail against velocity. Idle ribbons drift without changing width, colour proportions or tip shape. A ribbon may not shrink to 1 px in one frame.
- **R52. Cross-direction consistency.** These must match between directions:
  - eye size and lash style (S/SE/SW/E/W)
  - bow loop count and highlight side
  - bun size, ±1 px
  - sword pattern
  - foot construction
  - hair and red budgets

  Check the all-8 GIF (`tools/pixel/gif.py --anim idle --src clean`) at 1x and 4x on grey and grass.
- **R53. Staleness.** When the modelling workflow lands a new round, re-snapshot, then run `px.py stale`. Re-check conflicts and re-approve them before any further edit. Never paint over a stale frame.

---

## 4. Workflow per frame

1. Open `pixel/review/idle/<DIR>/fNN.png` (CLEAN | BASE | DIFF | SOURCE | FLAGS) and the source underlay (**U** in the editor).
2. Fix in this order:
   1. silhouette and outline (R9-R12, R42)
   2. tone masses (R4, R31, R43)
   3. features (face, bangs, bow, bun, sword, feet, ribbons)
   4. orphans and jaggies last (R13-R18)
3. Run `px.py apply`, then `lint.py --anim idle --src clean --dir <DIR>`, then `review.py` and `gif.py`. Look at it at 1x before you look at the zoom.
4. Each override reason names the rule, e.g. `"R41 heel point + ankle"`. Use `PX_AUTHOR=<you>`.

---

## 5. QA checklist (score each item pass/fail per direction; the frame-level items cover every frame)

Run `.venv/bin/python tools/pixel/lint.py --anim idle --src clean` and `px.py stale` first.

Count tone budgets with `.venv/bin/python tools/pixel/tonestats.py --src clean [--frame f03]`. In S, SE, SW, NE, N and NW, its pink column also counts the `p0` rim, so judge the scarf `p1` share on the ribbon pixels themselves (ID pass `pixel/base/idle/_id`, or by eye on the review sheet).

**Hard gates.** Any fail is a reject.
1. 0 off-palette and 0 semi-alpha pixels (R1).
2. 0 stale or conflicting overrides (R53). Every override has a reason that cites a rule.
3. Silhouette outline closed: lint `outline_gap` 0. No raw highlight on the background (R9).
4. 0 doubles (R10).
5. Orphans: 0, apart from the R13 whitelist. Each remaining orphan is listed with its whitelist reason.
6. Flicker 0 (R45).
7. Pivot: `y_drift` 0 and `cx_drift` ≤ 0.5 per direction. The baseline matches the agreed value per direction (R50).
8. Blade at least 2 px (`t2` + `t0`), one step ratio, `#` on the shadow side only, sticking out past the silhouette in all 8 directions (R19-R20).
9. Hook at least 3 px, crescent with an open inside, same curl in every frame. Guard bar 4-6 px, straight, not a blob (R21-R22).
10. No `p0`/`p1` pixel 4-adjacent to `s1`/`s2`. Scarf against skin always meets `s0` (R36).

**Scored items.** 1 point each. Pass needs ≥ 90 % of the applicable items per direction.

11. Hair budget: `h1` ≥ 50 %, `h0` ≤ 35 %, `h2` 5-12 % (R4).
12. Red budget: `r2` ≥ 45 %, `r1` ≤ 40 %, `r0` ≤ 5 %, `r3` 5-12 %, within ±5 points of the S value (R4/R43).
13. Scarf budget: `p1` ≥ 60 % (R4/R36).
14. `v0` at most 3 px and only on the right upper arm (R5).
15. Highlights top-left and shadows bottom-right. Rim 1 px, `p0`, back-right, ≤ 60 % of the contour, not on skin or scarf (R6-R7).
16. No cast shadow or inner lines on the face (R8/R11).
17. Cluster minimums: shading ≥ 3 px (skirt ≥ 4). Ribbons, cuffs, legs, hands and tails ≥ 2 px wide (R14).
18. No speckle: no dots in the skirt, no skin in the hair (except ear and cheek sliver), no eye or steel pixels on the hair or edge (R15).
19. Straight edges are single-ratio and curves are monotone. Lint `jaggy` on the body (not the sword) is ≤ 10 per frame, and each remaining jaggy has been looked at (R16-R17).
20. Face matches the direction's template (S / SE / SW / E / W):
    - lash row with wing
    - 3x3 iris (2 px in far eye and profile)
    - one glint at top-left, near eye only
    - eyes level
21. Far eye and profile eye have at least 1 skin px before the outline (R24-R25, 1.8).
22. Mouth 1 px (2x1 in combat), 2 rows under the iris, touching nothing. Blush is 1 `p0` per eye, with no red under the eyes (R26-R27).
23. NE/NW: cheek sliver only, with no eye or glint. N: no head skin and no nape strip (1.8, R33).
24. Bangs: 3-4 locks with down-pointing tips touching the lash row, swept to her right, no flat bar. Jaw strands present (R29-R30).
25. Hair `h2` is a curved crescent, present in back views too, with no tonsure ring (R31).
26. Bun separated by a curved 1 px line. At least 4 px of bun visible in every direction. Bun placement per facing tells (R32).
27. Bow: 2 loops with `r3` top-left, a V notch, crease, knot and 2 tails. On her right side of the bun, at most 14 px wide (R34).
28. Ribbons: 2-3 px S-curves tapering to the tip, at most 1 H in idle, no specks (R35).
29. Collar band 2-3 px around the jaw. Bare shoulders 1-2 px. Corset solid `l1` with an `l2` top edge, at most 2 buckle px (R37-R38).
30. Sleeve cuffs at least 2 px with an outlined end and `p0` rim (R39).
31. Legs separated and tapered, with no notches (R40).
32. Each visible foot has a `#` sole with heel point, a `d1` upper, and a 1 px `s1` ankle with a strap pixel. No skin at the toe. The far foot is ≤ 1 px higher (R41).
33. Hem: 2-4 petal tails, at least 3 px wide until the tip, no icicles or holes, high-low in E/W, slit and shorts in S (R42).
34. Hand and hilt visible in S/SE/SW/W: glove, at least 2 px hilt with `r2`, and kashira (R23).
35. Facing tells from bible §2 readable at 1x. NE ≠ E, NW ≠ W, N shows both bow loops.
36. Face, sword and bow pixel-identical across frames after the bob offset (R47-R48). Volume ±3 % (R46).
37. All-8 GIF at 1x on grey and grass: hair, corset, shorts and shoes separable. The pink rim is visible on hair and bow. Nothing reads as a blob.

*Items 38-49 were added by the research pass (see "Best-practice rules (from research)"). They are scored items, 1 point each, and count toward the 90 % pass. Items marked "(anim)" apply only to animations that have that feature.*

38. No pillow shading: no ring of shadow tone just inside the outline on the lit (top-left) side of any part (BP1).
39. Banding: lint `banding` reviewed for the frame. No two neighbouring tone clusters with parallel edges ending on the same row or column for ≥ 3 steps (BP2).
40. No dithering on the character: no checkerboard or random two-tone alternation. VFX are exempt (BP3).
41. No exterior AA: every silhouette-ring pixel is `#` or the lit-side material-dark tone, and no outline pixels were deleted to "soften" the lit side (BP10-BP11).
42. Sharp terminators (no 1 px intermediate-tone staircases), and AO is only 1 px at real overlaps. No baked render cast-shadow blobs (BP5, BP7).
43. Single-pixel highlights only on steel and the eye glint. No 1 px highlight dots on cloth, skin or hair (BP8).
44. Greyscale and squint test passed: desaturated, hair, red, corset, skin and ribbons separate, and each major part reads as about one light and one dark mass. Horizontal-flip review done on the key frame (BP9).
45. Extra backgrounds: the item 37 GIF also checked on light stone/sand and a dark dungeon floor, plus a deuteranopia/protanopia simulation. Red, pink ribbons and skin still separate (BP14).
46. Static parts pixel-identical to the key after the parent's whole-pixel offset. No boiling on corset, collar, shoes or bun (BP16).
47. Secondary motion: ribbons and skirt tails lag 1-3 frames with constant width, and the ribbon-tip path across the loop is a smooth arc with no zig-zag (R51, BP17).
48. (anim) Planted foot identical between frames while planted on contact frames (BP18).
49. (anim) Smear frames: clean crescent, monotone curves, ≤ 3 palette smear tones, no dither, body outline closed (BP19).

---

## 6. Feedback triage (what we accept from Gemini and what we reject)

**Accepted and encoded above:**
- **Round feedback:**
  - flat helmet bangs, bangs too high, and the bare forehead (R29)
  - hair too dark and low contrast in back views (R4/R31)
  - no face shadows or inner face lines (R8/R11)
  - straps readable rather than 1 px noise (R41)
  - ribbons as S-curves, not planks, with clean tips (R35)
  - the 1 px blade breaking up (R19)
  - bun readability (R32)
  - buckles and rivets becoming noise (R15/R38)
  - legs merging into one pillar (R40)
  - back views as a dark blob (R31)
  - the tonsure-ring highlight (R31)
  - jagged outline segments around the bun, neck, skirt tips and ankles (R9-R12)
  - the guard reading like a broadsword bar (R21)
  - no hilt visible (R23)
- **From the base critique:** everything in section 2 except the items below.
- **From the AI-pixel test (`gemini_opinion.txt`):**
  - Paint over the procedural base, never over the AI rows.
  - Use TRELLIS only as a reference for bow split, corset presence and sleeve/skirt flare.
  - No projection-bleed white edges.

**Rejected (with reason):**
- **Centring the bow on the bun or making it symmetric.** The bible places it on her right side of the bun, and this was already rejected in model rounds 3 and 5. We do require two readable loops.
- **"The sword is on the wrong side in E/NE" and "the bow doesn't rotate".** The renders come from one rigged 3D model and are never mirrored. Positions are geometrically correct. Pixel artists fix shapes, not 3D placement. Send placement concerns to the model workflow.
- **2x2 eyes with white sclera.** There is no sclera colour in the locked palette, and the bible eye is about 4 px tall with 2 iris tones and a glint.
- **"Illegal purple at the waist".** The bible allows up to 3 `v0` px for the right upper-arm lace. Only pixels away from that arm are removed.
- **A pink tassel on the katana hilt.** The AD rejected it in the model rounds. Don't add one.
- **The "7x6 bun as a perfect sphere" and "3x4 foot wedge" sizes.** These are taken as guidance. The bible proportions and R32/R41 govern.


## 7. Lessons from the earlier pixelart project (added by lead, 2026-10-24)

Source: docs/pixelart_project_study.md §6.2 (an earlier project at ~/Documents/other/pixelart that took a hero from 570 to 98 hand-fixed pixels). These rules are binding unless they conflict with §1. Where they conflict, flag it to QA rather than silently choosing. QA must also score items 6, 7, 8, 9, 10 and 12 below.

Each rule is given with its reason. Where our bible already says it, it is marked (bible).

1. **Closed 1-px exterior with sel-out** (bible §5): lit side gets the material's darkest tone, shadow side and the bottom 2 rows get the outline colour. **Plus:**
   - even outline runs (no single off-colour outline pixel; that shimmers);
   - L-corner doubles removed using the exterior mask;
   - a contrast floor to the outline colour wherever a lit-edge tone is within ~15% luminance of the test floors.
2. **The outline colour is exterior-only.** Pupils and lash use the same hex in our palette (`#1a1220` = outline = dark[0] = leather[0]). That blocks the engine's "swap outline to light rim on dark floors" trick (their 0% melt result). **Consider a separate `ink` index**, even if it has the same RGB, so the engine can tell exterior line from interior pixels. See conflicts, §6.4.
3. **Inner lines only at real part overlaps** (bible), in the front part's darkest tone, never the pure outline, never across skin. Drop interior line fragments shorter than 3 px.
4. **Highlights are designed, not lit.**
   - Hair sheen (angel ring) and bow shine come from a head-space mask or AOV and are then trimmed: 2 px inside the silhouette, minimum run 3, 1 px clear of the bow, 1-2 px gaps filled.
   - Raise the hair highlight threshold so lighting alone can never produce hair[2] specks.
   - A 1-px highlight run collapses to base unless it touches a 2x2 block.
5. **About 70% base tone per part.** Shadow tone only on the far rim and occluded undersides (our red[0] violet rule matches).
6. **No orphans** (QA = 0), except deliberate stamped pixels (eye glint, 1-px nose/mouth). The editor and lint must know which pixels are deliberate.
7. **Despeckle is per material** (islands ≤2-3 merge only into their own ramp). Run it again after the face stamp, with face pixels protected.
8. **Curves use monotone runs; banned patterns are 2-1-2 and 2-1-3-1; a dome top is a flat run of ≥3 px.** Applies to the bun, the bow loops, the bell-cuff hems and the skirt petals.
9. **Minimum feature width 2 px**, except deliberate 1-px tips. Our bible's 2-px blade, 3-px hook and 2-px foot fit this. For 1-px tips (skirt-tail points, ribbon ends, the jaw strands) **protect them from the silhouette regularizer**. The pixelart team lost 6 AD rounds to a 1-px ponytail tip the cleanup kept trimming.
10. **Select by part ID, never by colour or height.** Every cleanup rule and every override macro should be scoped by our object-ID pass. The v2.3 "mittens as boots" blocker is the cautionary tale. For us the risk is red cloth vs bow vs collar vs sleeve, all on the red ramp.
11. **`separate_materials`.** Where two same-ramp parts touch (sleeve cuff vs skirt; bow vs collar), the nearer one takes its line colour. Our bible already asks for "interior lines where two similar values meet"; this is the mechanical rule for it.
12. **Faces:**
    - Eyes are stamped cels, never rendered.
    - Both eyes share one row unless the head roll is ≥12°.
    - Lock the S bridge (e.g. 3 px).
    - 3/4: bridge ≥2 px, far eye ≥2 px of skin to the cheek contour, near eye ≥1; the far eye is narrower, not shorter.
    - Catchlight on the light side, the same side for both eyes.
    - Profile: the eye column sits behind a 1-px skin nose pinned to the actual face edge.
      - *Research note: this conflicts on its face with R26 "No nose" and bible "[DROP] nose". Anime convention supports both, split by view. Slynyrd (Pixelblog 29) gives an "almost non existent nose" from the front, but notes "the nose is much more prominent from the side view". Suggested resolution for the AD: no nose pixels in S/SE/SW; in E/W a 1 px bump on the face contour is allowed (it's silhouette, not an interior feature).*
    - Mouth: 1 row under the eyes, touching only skin, else omitted.
    - One expression shape family.
    - Blink = the lash row moved down one.
13. **Pin the bang hem to the lash row.** Exactly 1 skin row between the bangs and the lash in S/SE/SW, in every frame, including blinks. If a bang tip hits the lash row, the lash wins. Fixes bang/eye strobing on the idle breathing bob.
14. **Temple and hair-vs-skin rules convert skin only, never the outline.** Check every face rule on the mirrored direction (SE↔SW, E↔W) separately. Our costume is asymmetric, so mirrored *checks* are structural only.
15. **Back views (N/NE/NW):** head skin becomes hair (no cheek slivers), except the intended 1-2 px cheek/bang edge our facing-tell table asks for in NE/NW. Nape/chin row = skin shadow.
16. **Accessory cels must be identical every frame.** Small round or iconic items (bun knot, hip pouch, flower cluster) are stamped, not lit per frame. Lit vs unlit comes from a rule table, not per-normal lighting, which blinked.
17. **Temporal stability:** no A→B→A pixel toggle in idle unless the neighbourhood moves. A static loop must look static.
18. **Every override has a reason; any fix that recurs in ≥3 frames becomes a `sprite_post.py` rule.** Track the override pixel count per animation as the health metric.

