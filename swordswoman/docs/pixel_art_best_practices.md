# Pixel-art best practices for hand-cleaning 3D-rendered sprites

Research notes for the Crimson Ronin sprite cleanup team: an isometric chibi swordswoman, about 56 px tall in a 128 px cell, 8 directions, rendered from a rigged 3D model and then cleaned by hand.

The goal is concrete, checkable rules. Every rule cites a source. A rule marked **[derived]** is our own synthesis for this project's size and style, built on the cited principles rather than quoted from any one author.

Project constants used below come from `docs/design_bible.md` and `docs/palette.json`: a 22-colour palette, top-left screen-space key light, a pink[0] `#f49ab0` back-right rim light, 3-tone cel shading, and selective coloured outlines with outline colour `#1a1220`. This document doesn't change them. Where research suggests a refinement, it says so explicitly.

---

## 0. Prioritised rulebook (the short version)

Rules are ordered by impact on how "commercial" the result looks. P1 rules are non-negotiable.

### P1: always
1. **No orphan pixels.** Every pixel belongs to a same-colour cluster of 2 or more pixels, or does a named job: AA, eye glint, specular, or a 1 px strand that the design bible lists as [KEEP]. A lone pixel reads as noise. [Cure/Pixel Joint; Saint11 glossary]
2. **One light, everywhere.** The key light is top-left in screen space, locked to the camera, in all 8 directions and every frame. Shadows go on the bottom/right side of each form, never in a ring around it. [Slynyrd #6; design bible §5]
3. **No pillow shading.** Never shade inward from the outline. Shade from the light direction and the 3D form. [Cure; Derek Yu "Common Mistakes"; Lux/Pixel Parmesan]
4. **Clean lines.** Use 1 px lines with no doubles and no L-corners. Slopes are consistent (1:1, 2:1, 3:1), and curves change segment length in one direction only (e.g. 3-2-1-1-2-3, never 3-1-3). [Derek Yu; Cure; Saint11 "regular lines"; MortMort]
5. **Closed exterior outline, coloured but never removed.** The sprite has to read on unknown terrain, so the exterior silhouette is always closed. Lighten it by colour (sel-out with ramp colours), not by deleting pixels. No AA on the outside edge. [Derek Yu; Cure; Lux]
6. **Use the palette ramps only, per material.** No off-palette colours. Each material uses only its own ramp, plus the shared colours the palette declares. [Cure "cohesion/control"; Saint11 "consistency"; design bible quantize rule]
7. **No dithering on the character.** At 56 px, dithering reads as noise and boils in animation. Allow it only on VFX or large background areas. [Lux "Dithering"; Cure; design bible]
8. **Big readable clusters first.** If you squint, you should see a few large light and dark shapes per material. Detail never breaks up the basic form. [Derek Yu]
9. **On-model across directions.** Build a rotation strip of all 8 directions for the same frame and play it. Limb thickness and length, head size, eye size and bow size must stay constant. [Slynyrd #55]
10. **No flicker.** Step through every loop. Any pixel that toggles on and off between frames without motion is a bug. [Slynyrd #8; Dead Cells deep dive, where flicker was their known unsolved artefact]

### P2: strongly recommended
11. **Fewer tones per material.** Use base, shadow and highlight. The 4th tone (red violet) goes only on occluded undersides. Compress a sphere's six "modelling factors" into 2–3 tones. [Lux colour theory; design bible]
12. **Sharp terminators.** The light-to-shadow boundary is one hard step, not a staircase of intermediate tones. [Saint11 glossary]
13. **Kill banding.** Two neighbouring clusters must not have edges that run parallel at the same length. Stagger the cluster ends. [Cure; Lux AA article]
14. **Hard materials get high contrast and tiny speculars. Soft materials get low contrast and wide shapes.** Katana: spine steel[0], body steel[1], 1–3 px steel[2] glint on the lit edge. Cloth: no specular. Hair: one sheen band. [Saint11 glossary "specular"; Cure "independent pixels"]
15. **Value check in greyscale.** Desaturate the frame. Hair, red cloth, corset and skin must still separate. Also flip the frame horizontally to catch drawing errors. [Derek Yu]
16. **Faces are templates, not renders.** Stamp the hand-made eye, mouth and blush per direction. Never accept the 3D render's face pixels. [derived from Derek Yu (Mario eye), Slynyrd #29]
17. **Thin parts get the "chunky pixel" rule.** Nothing that must read (sword, limbs, ribbons) shrinks below its design width: blade 2 px, hook 3 px, feet 2 px. [Derek Yu "Chunky Pixels Rule"; design bible]
18. **Pose-to-pose, strong keys.** Fix the keyframes first, then the in-betweens. Remove in-betweens that weaken energy rather than polishing them. [Slynyrd #8; Dead Cells]
19. **Lock the pivot.** Feet and root sit on (64,104) in every frame. Movement is the engine's job. [design bible; Saint11 consistency, which recommends settling on integer pixel positions]
20. **Secondary motion overlaps.** Hair, bun strands, ribbons and skirt lag the body by 1–2 frames and settle after it. The hair highlight shifts a little, in a steady rhythm. [Slynyrd #55; t3ssel8r animation video]

### P3: polish
21. Sub-pixel motion (colour shifts instead of 1 px jumps) on the breathing bob, the bow and ribbon tips. [Lux AA article: "subpixel is AA applied to animation"]
22. Hold extreme poses longer than in-betweens on idles ("offset timing"). [Slynyrd #55]
23. A rim light only on the silhouette side away from the key, 1 px, and only on hair, bun, bow and cuffs. [design bible; Lux colour theory, Idle Monster Frontier example]
24. Contact shadow (AO) is 1 px of the next-darker tone where forms overlap (bow over bun, collar over neck, corset over skirt). No soft AO gradients. [derived from Saint11 "projected shadow is very sharp"]
25. Check colour-blind legibility (deuteranopia and protanopia simulation): red dress vs pink ribbons vs skin must still separate by value. [derived; see §4.7]

---

## 1. Clusters and noise

### 1.1 Definitions
- **Cluster**: "A group of 2 or more pixels of the exact same color. Clusters can connect with diagonal pixels, but it's a weaker connection. A horizontal or vertical connection is a strong one." [Saint11 glossary]
- **Orphan pixel**: "A lone pixel that doesn't touch any pixel cluster. Note that pixels that make part of anti-alias or shading curves are not considered orphan pixels. … They can be used to create small points of interest, and particle effects." [Saint11 glossary]
- "A single pixel, isolated, is a speck on a screen: it's noise. … in the wild, pixels travel in packs." [Cure, Pixel Joint "The Pixel Art Tutorial"]
- Justified independent pixels, per Cure: **bright specular highlights** and **small but essential details** such as "the eyes on a small sprite". [Cure]

### 1.2 Rules for this sprite
| Rule | Detail |
|---|---|
| C1 | **Orphans are allowed only for**: eye glint (steel[2]), katana edge glint (steel[2]), the 1 px buckles (steel[1]), and the 1 px jaw strands and flyaways listed as [KEEP]. Everything else gets merged or deleted. |
| C2 | **Minimum shading cluster [derived]**: on large forms (skirt, sleeves, collar, hair mass), a shadow or highlight cluster is at least 3 px in area and at least 2 px wide in its thinner direction. On small forms (bow loop, hand, shoe), at least 2 px. Smaller clusters are AA by definition, so they must sit on a step of a line or edge and do AA work, or be deleted. |
| C3 | **Diagonal-only links are weak** [Saint11]. A shadow cluster joined to its body only by a corner reads as speckle. Thicken it to an edge contact or remove it. |
| C4 | **Cluster shapes follow the form, not the render noise.** A cluster edge should describe one thing (a fold, the terminator, an overlap). If you can't say what an edge describes, simplify it. [Slynyrd #5: "Repetition, order, and lots of similar clusters make it appear all the pixels have purpose."] |
| C5 | **Clusters are puzzle pieces.** Changing one cluster reshapes its neighbours, so clean neighbouring clusters together. [Cure] |

### 1.3 Pillow shading (why to avoid it, and the fix)
- "Pillow shading refers to shading from the outline inward, creating a 'pillowy' effect. This type of shading almost never occurs naturally in real life and tends to make the object look blurry and indistinct." [Derek Yu, Common Mistakes]
- "Pillow-shading is bad because it pays no attention to the light source, and conforms to the shape of the area rather than the form it represents … it follows flat shapes rather than focuses on how the three-dimensional forms are lit." Frontal light is fine "so long as you pay attention to the forms". [Cure]
- Banding applied all around a contour "can lead to pillow shading, which also ruins the illusion of directional lighting and form." [Lux, Pixel Parmesan AA article]

```
PILLOW (wrong)           DIRECTIONAL, light top-left (right)
O O O O O O O            O O O O O O O
O d d d d d O            O H H B B B O
O d B B B d O            O H B B B d O
O d B B B d O            O B B B d d O
O d d d d d O            O B B d d d O
O O O O O O O            O O O O O O O
O=outline  d=shadow  B=base  H=highlight
```
Fix procedure: (1) flood the shape with the base colour; (2) place the shadow as one cluster on the side away from the light (bottom-right, plus undersides); (3) place the highlight as one smaller cluster on the top-left plane; (4) delete any shadow pixels on the lit side of the outline.

Typical 3D-render pillow trap: rim/fresnel or AO passes darken *every* edge of a form. That is pillow shading produced by the render. Remove it except where the edge is actually occluded or turned away from the light.

### 1.4 Banding
- "Banding, most simply, is when pixels line up. When neighbor pixels end at the same x or y coordinate on the underlying grid, the grid immediately becomes more evident … and the apparent resolution becomes less fine." Variants: outline-parallel banding, "fat pixels" or staircase banding, and banding across a gap ("the mind will fill in the gap"). [Cure]
- "Banding … occurs when lines of the same length are placed parallel to each other … Banding does not smooth shapes as anti-aliasing does, it only draws the eye by reinforcing the theoretical grid." [Lux AA]
- In shading, "we favor sharp transitions [at the terminator] to avoid banding." [Saint11 glossary]

```
BANDED: shadow steps exactly parallel to the outline   FIXED: shadow width varies, ends staggered
. . . . O O O O                                         . . . . O O O O
. . O O d d B B                                         . . O O d B B B
O O d d B B B B                                         O O d d d B B B
d d B B B B B B                                         d d d d B B B B
```
Fixes, in order of preference: **merge** the two bands into one tone; **stagger** the cluster ends so no two edges end on the same column or row; **vary** the band width along the form; and as a last resort replace an intermediate band with AA on the steps only.

### 1.5 Dithering at 56 px
- Derek Yu uses it "sparingly"; it "works best on large areas of a single color … or in places that we want to look rough or bumpy." [Derek Yu Basics]
- "Random dithering … isn't generally advised, as it adds a lot of single-pixel noise." Too much dither "turns into a field itself … creating unwanted texture." [Cure]
- "Some sprites are simply too small to dither relative to the amount of detail they can possibly contain. … I would not recommend dithering for most character sprites, especially those that will need to be animated." And: "Extraneous dithering often creates visual noise or the unwanted illusion of texture." [Lux, Pixel Parmesan "Dithering"]

**Rule D1:** no dithering on the character body, costume or sword (this matches the design bible). **D2:** a checkerboard dither in the 3D render (from texture noise, normal-map noise or quantisation) is a defect. Collapse it to the majority colour. **D3:** dither is allowed only in VFX (smear tail fade, petals) and in the engine's ground-shadow edge, and only as a regular 50% pattern, never random.

---

## 2. Lines

### 2.1 Clean lines and jaggies
- "The key to making nice pixel lines is reducing the number of jaggies: single pixels or small segments of pixels that break up the consistency of a line. … With curved lines, jaggies crop up when the length of the line segments don't grow or shrink in a consistent manner." [Derek Yu Basics]
- "Often times the problem is just that a segment of the line is too short or too long … Using a more uniform length of pixels to smooth the transition is the solution." [Cure]
- **Regular lines**: "Lines with a constant pixel length per step. Usually doesn't require anti-alias." [Saint11 glossary]
- Isometric 2:1 is "the foundation of isometric pixel art … an approximation of true isometry (26.5° rather than … 30)." [Lux, Isometric fundamentals; Slynyrd #41]

**Allowed straight-line step patterns:** 1:0 (horizontal), 1:1 (45°), 2:1, 3:1, 4:1 and their transposes. Non-integer slopes (e.g. 2-3-2-3) are allowed only if the rhythm is regular. 2-2-3-2-2 with a single odd step is a jaggy.

```
CLEAN 2:1                 JAGGY (one 3-step breaks the rhythm)
# # . . . . . .           # # . . . . . .
. . # # . . . .           . . # # # . . .
. . . . # # . .           . . . . . # . .
. . . . . . # #           . . . . . . # #
```

### 2.2 Curves: monotonic segment lengths
A curve's run lengths must **change monotonically** from one tangent to the other: long runs near flat tangents, shortening to 1s at the 45° point, then lengthening again on the other axis. Typical quarter arc (runs 4-2-1-1-1, then vertical runs 2-3):
```
. . . . . . # # # #
. . . . # # . . . .
. . . # . . . . . .
. . # . . . . . . .
. # . . . . . . . .
. # . . . . . . . .
# . . . . . . . . .
# . . . . . . . . .
# . . . . . . . . .
```
Wrong: 4-1-3-1-2 (lengths jump back and forth), which looks like a dent. Use this on: head, bun, bow loops, bell-sleeve cuffs, skirt hem, and the crescent hook guard.

### 2.3 Doubles and L-corners
A 1 px line must be connected **diagonally**, never with an extra pixel making an "L". The extra pixel thickens the line locally ("doubles"). MortMort's lesson "3 PixelArt Techniques/Common Mistakes (Doubles, Jaggies & Outline)" covers exactly this. Aseprite's *Pixel-perfect* stroke option removes L-corners automatically while drawing.

```
DOUBLE / L-CORNER (wrong)        PIXEL-PERFECT (right)
# . . . .                        # . . . .
# # . . .                        . # . . .
. # # . .                        . . # . .
. . # . .                        . . . # .
```
Exception: an L-corner is correct at a real **corner** of the form (collar point, skirt tail point, blade tip), where the line actually changes direction.

### 2.4 Line weight
- All outline and inner lines are **1 px** (design bible). A 2 px outline is allowed only where two separate 1 px lines meet. It is never used for emphasis.
- Perceived weight depends on value: "The brightness of a pixel or line determines how thick it appears … a line with pixels that vary in brightness … appears thinner." [Cure] Use this on purpose: a lit-side outline in a mid ramp colour reads thinner and lighter, and the shadow-side `#1a1220` reads heavier, which grounds the figure.
- AA on lines: "The longer the line segment, the longer the segment of AA we use to soften it." [Derek Yu] "Use more pixels of AA closer to the original shade and less as the AA comes to an end." [Lux AA] At 56 px, use AA **only inside the silhouette** and only on long, shallow steps (skirt hem, sleeve edge, blade). Never AA a 1:1 or 2:1 line; those are already clean. Lux: "If a sprite is too small, AA might read as noise … Always ask yourself 'is this really necessary?'"

---

## 3. Outlines

### 3.1 Options, with sources
| Style | What it is | Pros / cons for us |
|---|---|---|
| Black/near-black full outline | Uniform dark exterior and interior lines | "May be easier to animate and easier to 'read' in-game, but … a much flatter, more symbolic … effect." [Lux AA] "Creating a lot of harsh segmentation." [Derek Yu] |
| Coloured outline | Each material outlined in its own darkest ramp colour | Softer and more cohesive. Keeps material identity. |
| Sel-out (selective outline) | "Replacing a lot of the black outline with lighter colors. Toward the top, where the light is hitting … use the lightest colors or … remove it entirely." [Derek Yu] | Most naturalistic. **But** "Sel-out works if it is created for specific scenarios, such as in a game where you know the background will be consistently dark" [Cure], and removing outline pixels is effectively AA to an unknown background. |
| Exterior AA | Intermediate colours outside the silhouette | **Never** for game sprites: "If … you anti-alias on a light background then that anti-aliasing will stand out on a dark background." [Derek Yu; Lux] |

Additional points:
- Cure: "A full outline with light variation won't create jaggies as badly as a broken outline will." Sel-out "is not shading an outline according to a light source." Lux agrees: sel-out "shouldn't just be 'making the corners dark.'"
- Isometric contact: "You can lighten or remove the outlines where the object connects with the ground plane … As the connection outlines become lighter … the object appears to become more flush with the surface. Using darker outlines … may … imply that something is interactable." [Lux, Isometric]. For a player character we **want** the "interactable" read, so keep the dark closed outline at the feet.
- t3ssel8r's 3D pixel-art shader uses "light-aware edge coloration" (outlines coloured by the lighting at that edge). This is the shader version of coloured sel-out, and evidence that it reads well in a 3D-to-pixel pipeline.

### 3.2 Decision for small iso sprites on varied terrain
**Use a closed, coloured, light-aware outline**: sel-out by *colour* only, never by *gaps*. This is already the design bible rule. Research supports it:

1. The exterior silhouette is **always closed** (the terrain is unknown, so "removing it entirely" is not allowed).
2. On the shadow side (bottom/right) and at the feet, use `#1a1220`.
3. On the lit side (top/left), use the material's **darkest ramp colour** (red `#92203f`, skin `#c48089`, hair `#42282a`). Never use a mid or light tone as an exterior outline, because then the outline vanishes on light floors.
4. Where two lit-side materials meet the outside, each keeps its own outline colour. Don't run one colour across a material boundary.
5. **Inner lines**: only where two similar values meet (sleeve over skirt, arm over body, bow over bun), in the darker ramp colour, never `#1a1220` (design bible). Prefer a *broken* inner line to show soft overlaps: "I tend to utilize the breaking of inner lines to convey the softening of an edge or the meeting of two masses, rather than AA." [Lux AA]
6. Test every direction on the three standard backgrounds (light sand/stone, mid grass, dark dungeon floor). If the silhouette dissolves on any of them, darken the outline locally on that side. Never add an exterior AA halo.

```
Lit side (top-left)       Shadow side (bottom-right)
r r r                      . . . . . . . . 
r R R R                    R R R d d K
r R B B B                  R B d d K .
                           K K K K . .
r = red lit outline #92203f   K = #1a1220   R/B/d = red tones
```

---

## 4. Colour

### 4.1 Ramps and hue shifting
- Slynyrd's ramp construction: brightness increases steadily; "as the colors reach high brightness levels it's important to decrease saturation, or you'll end up with intense eye burning colors … Generally, darker colors have more saturation." Hue shift: "20 degrees of positive hue shift between each swatch … 20 is about as high as I go … positive hue shift usually results in more natural colors, warming as they become brighter." "The biggest mistake is combining high saturation and brightness." [Slynyrd Pixelblog 1]
- "When using hue shifting, bend your highlights toward a certain color (yellow …), and move the darker colors toward a second color (… blue)." Straight ramps "are usually boring." [Cure]
- **Counterpoint, which we adopt as a refinement**: hue shift is not a formula but a consequence of light colour. "If the light source is more 'warm' than the object, the object may appear to be 'cooler' in hue as it falls into shadow." And "generally midtones have greater saturation potential than either highlights or shadows." [Lux, "Color Theory for Pixel Artists: It's All Relative"]

**Project check**: the red ramp (`#4a1640` violet, `#92203f` crimson, `#d8343e` base, `#f5705a` coral) already shifts toward violet in shadow and warm coral in light, so it follows both sources. Rule: **don't invent new in-between tones** during cleanup. If two tones feel too far apart, ask for a palette revision. Don't hand-mix.

### 4.2 Saturation and value control
- "Value … is the most important for discerning form and depth." Perceived value (luminance) matters more than HSV value. [Lux colour theory]
- "We want each color to have its own identity … When colors are too similar, pixels begin to blend together and get lost." Derek Yu's fix for "naive" art: "reduce the color count and increase the contrast of those colors." [Derek Yu Common Mistakes]
- Use the full value range: "a full range of values allows you to use highlights, mid-tones, and shadows. … A common problem newer artists exhibit is not having enough contrast." [Cure]
- Accent proportion: "one main color which makes up the greatest total percent of the image, an accent color which makes up a small portion (maybe 10–20%)." [Lux colour theory]. For us, red is the main colour, pink ribbons and rim are the accent, and steel is a tiny highlight accent.

### 4.3 Limited colour count per sprite
- Reasons for small palettes are **cohesion** ("the same colors will reappear throughout the piece … the palette ties the piece together") and **control** ("The smaller the palette, the easier it is to manage"). [Cure]
- "The most common color inconsistency in games without color limitations is that some sprites don't use colors that they could be using." [Saint11, "My Thoughts on Style Consistency"]
- Cyangmou: "Bigger Palettes Increase Production Time" (tutorial listed on Lospec).

**Rule**: every frame uses only the 22 palette colours. Run a palette lint (count unique RGBA values per frame; anything not in `palette.json` fails). Any *new* colour needs an art-direction decision. A cleaner never adds one.

### 4.4 Material separation by value
Separate adjacent materials by **value first**, hue second. In greyscale, the pairs that touch must differ by at least one clear step:

| Touching pair | Guard (from palette luminances) |
|---|---|
| Hair base `#74483a` (0.087) vs red shadow `#92203f` (0.075) | Too close in value. Separate with the hair outline/shadow or the collar's lit red. Never let them touch over a long run. |
| Corset `#4a2e20` (0.035) vs red base `#d8343e` (0.174) | Fine. Keep the 1 px leather[2] top-edge line (design bible). |
| Skin shadow `#c48089` vs collar red | The v2 palette cooled skin shadow for this. Don't use red tones in the face. |
| Ribbons pink[1] vs red[3] coral | Never let ribbons touch red[3] directly. Put pink[0] or an outline between them. |

### 4.5 Greyscale, flip and squint checks
- "Remove the color from your artwork (i.e. set the saturation to zero) to see whether your shading still reads well." "Flipping your artwork horizontally … often exposes flaws in proportions and shading." [Derek Yu Basics]
- "If you squint, a few large clusters of light and dark should still emerge." [Derek Yu Basics]
- "Another method is to create the piece in shades of grey, then add color later … because relative value is a greater concern than hue." [Cure]

### 4.6 Matching sprites to the environment palette
- Colour is relative: the same grey reads as the complement of its surroundings. [Cure (iLKke example); Lux]
- UFO 50's palette was tuned by "pull[ing] in screenshots of other … games … to see what they would look like truncated down to our specific color set." [Eirik Suhrke in Game Developer, "Creating dozens of unique pixel worlds for UFO 50"] Do the same: paste the sprite onto real terrain screenshots at 1x and 3x.
- Sea of Stars' team "spent the first six months of development creating dynamic lighting capabilities that appeared visually consistent with the pixel art" [Wikipedia, Sea of Stars], which shows that engine lighting has to be designed to match hand-placed shading.
- Rule: the character's outline `#1a1220` and darkest red should be darker than any terrain tone it stands on, and the rim pink[0] should be lighter than any dark floor. Verify on the terrain test strip (`docs/palette_v1_vs_v2_terrain.png`).

### 4.7 Colour-blind check [derived]
No fetched source gave a pixel-specific procedure, so this is standard accessibility practice: run each finished direction through a deuteranopia/protanopia simulator (e.g. Aseprite plugin or any CVD filter). Red dress vs pink ribbons vs skin must still separate by **value**. If they merge, the fix is a value change in the outline or contact pixels, not a hue change.

---

## 5. Light

### 5.1 One screen-space light across 8 directions
- "A light source should be established at the very start of any illustration … the most common and natural light source is from somewhere above. … I most often have primary light from the top right or left hand side." [Slynyrd #6]
- Iso lighting: "a light source which hits the top face mainly as well as one side face partially is most effective, as each face will have a different value … A cast shadow running horizontally to the right or left … tends to work well in iso." Back or side lighting is "possible but … less visually readable." [Lux, Isometric]
- Slynyrd #22: mirroring directions is acceptable "unless you're using dramatic directional lighting, or your character has an asymmetrical design". We have both, so **no mirroring** (design bible). Each direction must be re-lit from top-left, never mirrored with its shadows.

**Rules**
- L1: light is top-left **in screen space** for every facing. When she faces N (away), her back is lit top-left. When she faces E, her front-left (screen-left) side is lit.
- L2: the 3D render's light rig must be camera-parented (design bible). Any frame where a world-space light leaked in (shadow side flips between directions) is relit by hand.
- L3: hold the *same* terminator position relative to the screen for symmetric forms (head, bun) across all 8 directions. The bun's highlight stays top-left of the bun regardless of facing.
- L4: eye glints sit on the **same side in both eyes** (light side), not mirrored. [derived from L1]

### 5.2 Form shading at small scale (cylinders and spheres)
- Compress the modelling factors: "the modeling factors often must be compressed to prevent banding and pillow shading … On the right sphere I've compressed multiple factors into single shades." [Lux colour theory]
- Saint11's shadow taxonomy: **volume shadow** (form shadow), **terminator** ("in pixel art we favor sharp transitions"), and **projected shadow** ("usually a very sharp shadow"). [Saint11 glossary]
- Simplify forms: "a treetop could be thought of as a few green spheres glued together." [Derek Yu Common Mistakes]

Templates (light top-left, B=base, d=shadow, H=highlight):
```
SPHERE (head, bun, bow knot)      CYLINDER (arm, leg, sleeve)
. . O O O O . .                    O B H B B d O
. O H H B B O .                    O B H B B d O
O H H B B B d O                    O B H B B d O
O H B B B d d O                    O B H B B d O
O B B B d d d O                    one highlight stripe 1/3 from lit side,
. O B d d d O .                    shadow stripe on the far side;
. . O O O O . .                    no stripe at the very edge (pillow)
```

### 5.3 Rim light and sel-out
- Lux's colour theory article shows a sprite whose rim light is "so intense" that it shifts the absolute colour of the fabric. Rim light is a strong colour event, so use it sparingly.
- Project rule (design bible): pink[0] 1 px on hair, bun, bow loops and cuffs, on the side away from the key. **Research refinement**: rim light *replaces* the outline pixel's inner neighbour, not the outline itself, so the silhouette stays closed (§3.2 rule 1). Never put rim and key highlight on the same edge.

### 5.4 Ambient occlusion and contact shadows
- Projected shadows are sharp [Saint11]. At 56 px, AO is **one pixel of the next-darker ramp tone** directly under an overlapping form: under the bow on the bun, under the collar on the neck, under the corset on the skirt, and inside the bell sleeve opening. Red uses its violet 4th tone only here.
- Remove all soft AO gradients from the render. They create pillow shading and banding (§1.3, §1.4).
- The ground shadow is a separate engine layer, a 2:1 ellipse, and never baked into the sprite (design bible).

### 5.5 Specular on metal (katana) vs soft materials
- "Glossy and reflective objects have small and focused highlights. Rougher objects may not have a reflection highlight." [Saint11 glossary]
- "For bright specular highlights, single pixels will often work just fine." [Cure]
- Katana rule: blade 2 px wide. The spine/back pixel is steel[0] and the edge pixel is steel[1]. Add 1–3 px of steel[2] glint on the edge **only where the blade faces the top-left light** in that frame. The glint may travel along the blade between frames (this sells the swing) but must not flicker on and off at rest. The crescent hook guard: steel[1] body, steel[0] underside, one steel[2] pixel on the top-left of the curve.
  - Note: `docs/pixel_cleanup_guide.md` R19 currently specifies a full-length `t2` lit edge plus a `t0` spine. The guide has a "Research note" there proposing the shorter glint above, pending an AD decision on light-terrain readability. Until then, R19 governs.
- Hard vs soft: hard materials (steel, buckles) get **high contrast, abrupt value jumps, tiny highlights**. Soft materials (dress, sleeves, ribbons, skin) get **lower contrast, wider clusters, no specular**. Hair is in between: one sheen *band* (hair[2]) following the head curve, not dots.

---

## 6. Shading taste: restraint and readability

- "A well-defined character has details that do not obscure the basic forms." [Derek Yu Basics]
- "Making small sprites is about making compromises. If you add an outline around something, you may lose the room to shade it." [Derek Yu Basics]
- "As one becomes more proficient in pixel art, the tendency is to do too much … the beauty of pixel art comes from the lack of information." [Slynyrd #47]
- "What looks best in one static position might become undefined noise in other frames of the animation … compromises and simplification should be favored for clarity of motion." [Slynyrd #55]
- "Is this really necessary?" before adding AA. "Many times you may find that the answer is 'no.'" [Lux AA]
- Avoid 1 px-thick protrusions: "avoid rendering anything with only a single pixel of thickness … they feel flat and flimsy." [Derek Yu "Chunky Pixels Rule"]

**What to drop at 56 px** (design bible already lists most): nose, rivets, stitching, chest cord and gem, individual fabric folds smaller than 3 px, lace texture, hair strands other than the 2 jaw strands and 1–2 flyaways, and fingers (hands are 2–4 px mitts). **What to exaggerate**: eye size, bow and bun silhouette, bell-sleeve cuff width, the hook guard, and the corset value break.

**Shading budget per material per frame [derived]**: one shadow cluster plus one highlight cluster per major form (head, bun, bow loop, each sleeve, bodice, skirt panel). A second shadow cluster is allowed only for a real overlap (AO). If a form has more than about 3 separate shadow clusters, it's noise. Merge them.

---

## 7. Faces and anime chibi at small scale

### 7.1 Principles
- "In Super Mario Bros., Mario's eye is just two pixels stacked on top of each other." The smaller the sprite, "the more responsibility each individual pixel has." Derek Yu favours chibi for small sprites: "cute and have large heads and eyes." [Derek Yu Basics]
- At small sizes "the head usually takes up a third to half of the total sprite." [Slynyrd #22]
- Anime faces: "Big eyes, little pouty lips, and an almost non existent nose … Think of seeing a face through a subtle fisheye lens." Hair is a top defining trait: "imagine flow lines of the main locks … blob in the hair with a single color. Next I refine the shape as I work in shadows, and highlights." [Slynyrd #29]
- AdamCYounis has a short titled "Eye position matters!": one pixel of eye placement changes the character's read.

### 7.2 Eye templates for this sprite
The design bible gives eyes at 4–5 px tall × 3–4 px wide for S-facing. L=`#1a1220` lash, I=iris dark `#2c3f9e`, i=iris light `#5f8ee8`, g=glint `#eef0f5`, s=skin.

```
S / front (3w x 4h)      SE/SW near eye (3x4)    far eye in 3/4 (2x3)   E/W profile (2x3)
L L L                    L L L                   L L                    L L
I I g                    I I g                   I g                    I g
I i i                    I i i                   i i                    i i
s i s                    s i s
```
- Upper lash: 1 px `#1a1220` across the top; it may extend 1 px outward and down at the outer corner for a feminine flick (same on both eyes).
- Glint: 1 px steel[2] at the **top-left** of each iris (both eyes on the same side; §5.1 L4). Never 2 glints at 56 px.
- No lower lash line. No white sclera at this size. The iris directly meets skin.
- Half-lidded calm default: drop the top iris row and keep the lash, giving a 3×3 eye.
- Combat frown: angle the lash down toward the nose by 1 px. Don't add brows (the bangs cover them per the bible).
- N (back) facing: no eyes. NE/NW: at most a 1 px lash hint at the cheek edge, or none.

### 7.3 Mouth, blush, bangs
- **Mouth**: 1–2 px, skin[0] `#c48089` for neutral; `#1a1220` only for an open shout (2×2 maximum). It sits 2–3 px below the eye line, centred between the eyes on S and offset toward the facing on SE/SW.
- **Blush**: 1–2 px pink[0] `#f49ab0` directly under the outer half of each eye, with at least 1 skin pixel between blush and iris. Drop it on E/W if it would touch the outline.
- **Nose**: none (design bible).
- **Bangs**: 3–4 large clumps with pointed tips, as one hair-base cluster plus one hair-shadow cluster beneath the tips (the shadow falls on the forehead, light from top-left). Tips follow monotonic curves (§2.2). Only the 2 jaw strands are 1 px lines. Hair sheen (hair[2]) is one curved band across the crown and one on the bun.

### 7.4 Keeping faces on-model
1. Build a **face sheet**: one approved face per direction (8) plus each expression (calm, focus, smile, hurt). Every frame's face is stamped from it, then shifted only by whole pixels with the head.
2. When the head bobs 1 px, the whole face moves 1 px. Never move an eye independently of the other.
3. Check the face across directions with Slynyrd's method: put all orientations "into a uniform position on the canvas … sequenced into a rotation animation. This revealed many errors." [Slynyrd #55]
4. Always discard the render's face pixels. 3D eyes downsampled to 3–4 px produce random iris and sclera mixes.

---

## 8. Animation cleanup

### 8.1 Flicker and boiling
- "Looping animations demand great attention to detail … a single misplaced pixel can create an eyesore … you can't hide poor cluster work with fluid animation." "Respect the clusters of every single frame. A single orphan or misplaced pixel in a looping animation is obvious." [Slynyrd #8]
- Dead Cells (3D-to-pixel at scale): "we still haven't found any solution for flickering pixels … we could clean that by hand… but the point of this workflow is to go fast." [Thomas Vasseur, Dead Cells deep dive] For a polished commercial look, **we do clean it by hand**. This is the main quality difference from Dead Cells' trade-off.
- Boiling = clusters that change shape between frames on parts that aren't moving. Rule: a part that doesn't move relative to its parent (e.g. corset during idle) keeps **identical pixels** frame to frame, shifted only by the parent's whole-pixel offset. Copy-paste it, don't redraw it.

### 8.2 Volume consistency
- "The trick is keeping the thickness and length of appendages consistent. At such a small size, one pixel can make a huge difference." For the run: "the bob of the head, the motion of the shoulder pivot, and the max swing of appendages are critical areas to observe." [Slynyrd #55]
- Rule: measure head width, bow width, blade length and leg length in each key and keep them within ±1 px of the model sheet, except smear frames and intentional squash.

### 8.3 Timing, keys and in-betweens
- "Keyframes should be the most dramatic poses … the gist of the animation should be readable from the keyframes alone." "Too many in-between frames can make your motion look sluggish." Playback speed must be rebalanced when frames are removed. [Slynyrd #8]
- Dead Cells: once timing is right "with the least amount of frames possible, I add interpolation frames before or after the key frames. Never in-between … essentially pose-to-pose." [Dead Cells deep dive]
- Head bob in a 6-frame run: "down 1px, down 1px, and up 2px … the up movement is faster than the down movement." Idle: "an offset timing that holds the frames at the extremities of the motion longer." [Slynyrd #55]

### 8.4 Sub-pixel animation
- "Subpixel … is actually just AA but applied to an animation. It conveys shifts in position that are smaller than an actual pixel." Used for small sprites "or small details of larger sprites." [Lux AA]
- Use on: the idle breathing (shift the shoulder/collar highlight edge by one colour step instead of moving the whole torso 1 px), bow loop sway, and ribbon tips. Don't use on outlines (it would create exterior AA).

### 8.5 Smear frames
- t3ssel8r's animation workflow uses "smear interpolation" and a dedicated "secondary motion and tweaks" pass for his 3D pixel-art game ("Making an Animation for my 3D Pixel Art Game").
- Project: smears use the palette smear_arc roles (steel[2] core, pink[1], pink[0]). Rules: smear frames may break volume; the smear shape is a clean crescent with monotonic curves (§2.2); no dither; the body in a smear frame still has a closed outline; the arc has at most 3 tones and fades by *width*, not by noise.

### 8.6 Secondary motion: hair, ribbons, skirt
- Slynyrd #55: "The bounce in the hair adds extra liveliness with little effort." Hair highlight: "looks odd if it stays in the same place in every orientation, but it's distractingly noisy if it jumps around too much … shift around a small amount in a consistent rhythm."
- Rules: ribbons and skirt tails lag the root by 1–2 frames (follow-through) and overshoot by at most 1–2 px. Each ribbon keeps a constant width (1–3 px per the design bible) along its length in every frame. Ribbon tips trace a smooth arc across the loop; plot tip positions and remove any zig-zag.

### 8.7 Pivot and feet locking
- Design bible: feet/root at (64,104) in every frame and direction. Lunges move the engine root.
- Saint11 (consistency): when sub-pixel positioning is used, "make the pixel layers always stabilize in integer coordinates when it stops."
- Rule: on contact frames (walk f0/f4, run f0/f4), the planted foot's pixels must not slide. Diff the foot region between consecutive contact-hold frames. It should be zero motion.

---

## 9. 3D-to-pixel cleanup specifics

### 9.1 What the references say
- **Dead Cells**: a custom tool "renders the mesh in a very small size and without antialiasing", plus a normal map and "a basic toon shader". The known residue is "flickering pixels" and "the disappointing level of details." [Game Developer deep dive]
- **Saint11, "Using 3d models as pixel art reference"**: after recording a Blender rotation, "reduced the size and the colour palette … It's horrible, I know, but again, that's not important, since we will just redraw the whole thing. … when blocking things for reference, don't waste too much time … just focus on the important part, the perspective!" He also mirrors half of the frames to get perfectly consistent rotation. (Mirroring isn't an option for our asymmetric costume.)
- **Donkey Kong Country (Rare)**: pre-rendered SGI models converted into SNES sprites. This is the historical precedent that pre-rendered sprites can ship at commercial quality when compressed and curated carefully. [Wikipedia, DKC]
- **Guilty Gear Xrd** (GDC 2015, Junya C. Motomura, "The X Factor Between 2D and 3D") is the reference talk for making 3D read as hand-drawn 2D: hand-controlled shading and limited key-framed animation. Dead Cells cites "the last Guilty Gear" as an inspiration.
- **Octopath Traveler (HD-2D)**: hand-pixelled sprites combined with 3D environments. The team tuned "depth, resolution, saturation" and whether water "should be pixel or photorealistic." [Wikipedia]. It's a reminder that pixel sprites and 3D-rendered surroundings have to be matched deliberately.
- **Children of Morta** postmortem: high-res, high-keyframe hand-drawn pixel animation was the largest cost ("every frame of every character needed to be drawn by hand"). This is why our 3D draft plus hand cleanup pipeline is a reasonable middle path. [Game Developer]
- Pixel art definition: "Any tool that places pixels automatically … is generally frowned upon … pixel art is all about control." "A high amount of colors can indicate the use of dirty tools." [Cure]. Every pixel the renderer placed must be **reviewed** by a human, even if it's kept.

### 9.2 Defect catalogue (what to fix after rendering)
| Render artefact | Symptom | Fix |
|---|---|---|
| Downsample speckle | Isolated pixels of a neighbouring material or tone | Majority-filter per material, then hand-check (§1.2 C1) |
| Edge stair noise | Silhouette steps irregular (3-1-2-1) | Redraw the outline as clean slopes or curves (§2) |
| Pillowed edges (fresnel/AO) | Dark ring inside every shape | Re-shade directionally (§1.3) |
| Normal-map noise | Shading speckle on flat cloth | Flatten to base and re-place one shadow cluster |
| Checkerboard / texture dither | 50% patterns in the dress | Collapse to the majority colour (§1.5 D2) |
| Broken thin parts | Blade becomes dotted, ribbons have gaps, strands disappear | Redraw at design width (blade 2 px, hook 3 px, ribbons 1–3 px, strands 1 px) |
| Cast shadows from the model | Self-shadow blobs that change between frames or directions | Remove. Keep only 1 px AO at real overlaps (§5.4) |
| World-space light leak | Lit side flips by direction | Relight top-left (§5.1 L2) |
| Wrong-ramp quantise | Hair pixels snapped to violet dark[1], etc. | Per-material re-quantise (design bible) or recolour by hand |
| Face soup | Eye or mouth pixels random | Replace with the face-sheet stamp (§7.4) |
| Temporal flicker | Pixels toggle frame to frame | Stabilise: copy static parts across frames (§8.1) |
| Silhouette gaps at the ground | Outline open at the feet | Close it (§3.2) |
| Sub-pixel jitter of the root | Whole sprite wobbles 1 px | Re-align to the pivot (§8.7) |

### 9.3 Repaint vs tweak: decision rule [derived]
**Repaint the part from scratch** (on a new layer, using the render only as a placement guide, as Saint11 does) when any of these is true:
1. The part is **≤ 4 px in its thin dimension** and must read: face, hands, feet, blade, hook guard, ribbons, jaw strands. Downsampling can't produce clean shapes at this width.
2. More than about **30% of the part's pixels** need changing (rough heuristic: when cleanup touches more pixels than it keeps, repainting is faster and cleaner).
3. The part **flickers or boils** across the loop. Repaint once, then copy across frames.
4. The part has **more than 3 shadow clusters**, or any pillow ring.

**Tweak in place** when the silhouette is right, the cluster count is within budget, and only edges or orphans are wrong. This is typical for the skirt, sleeves and bodice on non-smear frames.

---

## 10. Cleanup checklist and order of operations

### 10.1 One frame, in order
1. **Silhouette**: check the pose against the key, align the pivot (64,104), close the outline at the feet, fix the outline slopes and curves (§2, §3).
2. **Thin parts**: repaint the blade (2 px), hook (3 px), feet (2 px plus skin ankle), ribbons and strands at design width (§9.3).
3. **Flat colour**: flood each material with its base colour. Remove all render shading on parts being repainted.
4. **Light**: place the shadow clusters (bottom-right and undersides), then the highlight clusters (top-left), then the 1 px AO at overlaps. Use a sharp terminator (§5).
5. **Outline colouring**: lit-side material-dark, shadow-side `#1a1220`, inner lines only where values are similar (§3.2).
6. **Face**: stamp from the face sheet (§7).
7. **Accents**: katana glint, hair sheen band, rim pink[0], buckles (§5.3, §5.5).
8. **Noise pass**: orphans, diagonal-only links, doubles, L-corners, banding (§1, §2).
9. **Internal AA**: only on long shallow steps, never exterior (§2.4).
10. **Checks**: palette lint (22 colours only), greyscale, horizontal flip, squint, view on 3 terrain backgrounds at 1x and 3x (§4.5, §3.2).

### 10.2 Whole animation (one direction, then across directions)
1. **Keys first**: clean the key poses fully (10.1) before touching in-betweens. [Slynyrd #8; Dead Cells]
2. **Drop weak in-betweens**: if an in-between adds no readable change, delete it and retime per the spec instead of polishing it.
3. **Propagate static parts**: copy unchanged parts (corset, face, bow) from the cleaned key into the in-betweens, offset by whole pixels (§8.1).
4. **Clean in-betweens**: run 10.1, using the neighbouring keys as onion skin.
5. **Secondary motion pass**: ribbons, bun strands, skirt tails. Check lag, overshoot and constant width (§8.6).
6. **Loop review at game speed and at 1x**, then frame-step: no flicker, no boiling, planted feet don't slide, glint doesn't strobe.
7. **Rotation strip**: the same frame index across all 8 directions, played as a turnaround. Check volume, light side and face (§5.1, §7.4, §8.2). [Slynyrd #55]
8. **Sheet review on terrain**: all directions in-engine or in a mock-up on the 3 backgrounds.
9. **Final lint**: palette, orphans (automated count), pivot offsets, trimmed atlas export.

### 10.3 Automatable checks (suggested for `tools/pixel` lint) [derived]
- Unique colours ⊆ palette.json (exact RGBA match, alpha only 0 or 255).
- Orphan count, excluding whitelisted colours steel[2]/steel[1]: pixels with no 4-neighbour of the same colour.
- Exterior AA detection: any non-outline colour on the silhouette border that isn't lit-side material-dark.
- L-corner detection on outline pixels (3 outline pixels forming an L, where the middle one could be removed while keeping 8-connectivity).
- Frame-to-frame diff of masked static regions (flicker).
- Pivot: lowest opaque foot pixel row == 104 on contact frames.

---

## Sources

Fetched and read for this document (domains that were unreachable directly were read through the Internet Archive Wayback Machine; the original URL is given):

- Derek Yu, "Pixel Art Tutorial: Basics": https://www.derekyu.com/makegames/pixelart.html (via https://web.archive.org/web/2024/https://www.derekyu.com/makegames/pixelart.html)
- Derek Yu, "Pixel Art: Common Mistakes": https://www.derekyu.com/makegames/pixelart2.html
- Cure (ed. jalonso), "The Pixel Art Tutorial", Pixel Joint forum: http://pixeljoint.com/forum/forum_posts.asp?TID=11299 (draws on the Pixelation "Ramblethread")
- Pedro Medeiros (Saint11), Pixel art glossary: https://saint11.art/blog/glossary
- Saint11, "Using 3d models as pixel art reference": https://saint11.art/blog/3d-ref/
- Saint11, "My Thoughts on Style Consistency": https://saint11.art/blog/consistency/
- Saint11, Pixel Art Tutorials index: https://saint11.art/blog/pixel-art-tutorials/
- Raymond Schlitter (Slynyrd), Pixelblog 1 "Color Palettes": https://www.slynyrd.com/blog/2018/1/10/pixelblog-1-color-palettes
- Slynyrd, Pixelblog 5 "Back to Basics": https://www.slynyrd.com/blog/2018/5/16/pixelblog-5-back-to-basics
- Slynyrd, Pixelblog 6 "Light and Shadow": https://www.slynyrd.com/blog/2018/6/15/pixelblog-6-light-and-shadow
- Slynyrd, Pixelblog 8 "Intro to Animation": https://www.slynyrd.com/blog/2018/8/19/pixelblog-8-intro-to-animation
- Slynyrd, Pixelblog 22 "Top Down Character Sprites": https://www.slynyrd.com/blog/2019/10/21/pixelblog-22-top-down-character-sprites
- Slynyrd, Pixelblog 29 "Anime Faces and Hair": https://www.slynyrd.com/blog/2020/7/28/pixelblog-29-anime-faces-and-hair
- Slynyrd, Pixelblog 40 "3D Pixel Art Animation": https://www.slynyrd.com/blog/2022/9/25/pixelblog-40-3d-animation
- Slynyrd, Pixelblog 41 "Isometric Pixel Art": https://www.slynyrd.com/blog/2022/11/28/pixelblog-41-isometric-pixel-art
- Slynyrd, Pixelblog 47 "Tiny Pixels": https://www.slynyrd.com/blog/2023/11/26/pixelblog-47-tiny-pixels
- Slynyrd, Pixelblog 54 "Isometric Pixel Art": https://www.slynyrd.com/blog/2025/1/23/pixelblog-54-isometric-pixel-art
- Slynyrd, Pixelblog 55 "Top Down Character Animation" (8-direction): https://www.slynyrd.com/blog/2025/3/24/pixelblog-55-top-down-character-animation
- Lux (Pixel Parmesan), "Anti-Aliasing Fundamentals for Pixel Artists": https://pixelparmesan.com/blog/anti-aliasing-fundamentals-for-pixel-artists
- Lux, "Dithering for Pixel Artists": https://pixelparmesan.com/blog/dithering-for-pixel-artists
- Lux, "Fundamentals of Isometric Pixel Art": https://pixelparmesan.com/blog/fundamentals-of-isometric-pixel-art
- Lux, "Color Theory for Pixel Artists: It's All Relative": https://pixelparmesan.com/blog/color-theory-for-pixel-artists-its-all-relative
- Thomas Vasseur, "Art Design Deep Dive: Using a 3D pipeline for 2D animation in Dead Cells", Game Developer (Gamasutra): https://www.gamedeveloper.com/production/art-design-deep-dive-using-a-3d-pipeline-for-2d-animation-in-i-dead-cells-i-
- "See Guilty Gear Xrd's striking 2D/3D art deconstructed at GDC 2015", Game Developer: https://www.gamedeveloper.com/art/see-i-guilty-gear-xrd-i-s-striking-2d-3d-art-deconstructed-at-gdc-2015
- "Postmortem: Children of Morta", Game Developer: https://www.gamedeveloper.com/design/postmortem-children-of-morta
- "Creating dozens of unique pixel worlds for UFO 50", Game Developer: https://www.gamedeveloper.com/art/creating-dozens-of-unique-pixel-worlds-for-ufo-50
- t3ssel8r, "Making an Animation for my 3D Pixel Art Game": https://www.youtube.com/watch?v=1FrIBkuq0ZI (description: smear interpolation, secondary motion pass)
- t3ssel8r, "Pixel Art Shader Updates" ("light-aware edge coloration"): https://www.youtube.com/watch?v=ZsMHY4LDyRE
- t3ssel8r, "Crafting a Better Shader for Pixel Art Upscaling": https://www.youtube.com/watch?v=d6tp43wZqps
- Aseprite docs, Shading ink: https://www.aseprite.org/docs/shading/
- Wikipedia: Octopath Traveler https://en.wikipedia.org/wiki/Octopath_Traveler, Sea of Stars https://en.wikipedia.org/wiki/Sea_of_Stars, Donkey Kong Country https://en.wikipedia.org/wiki/Donkey_Kong_Country, Eastward https://en.wikipedia.org/wiki/Eastward_(video_game)
- Lospec tutorial index (author listings for MortMort, Cyangmou): https://lospec.com/pixel-art-tutorials

Referenced by title only (lists confirmed, content not transcribed in this pass):
- MortMort, "3 PixelArt Techniques/Common Mistakes (Doubles, Jaggies & Outline)": https://www.youtube.com/watch?v=gW1G_FLsuEs. "Shading Your Outline": https://www.youtube.com/watch?v=faDNIMvuZKA. "Basic Anti-Aliasing for beginners": https://www.youtube.com/watch?v=UN-m3o9V7kk
- AdamCYounis, "Eye position matters!": https://www.youtube.com/shorts/1Lvd0l_qK28. Pixel Art Class series on https://www.youtube.com/@AdamCYounis
- Cyangmou, "Pixel Art - Shapes and Outlines", "Readability - Pixel art Style possibilities", "Bigger Palettes Increase Production Time" (links via Lospec author page)
- Michael Azzi, *Pixel Logic*: https://gumroad.com/l/pixel-logic
- Junya C. Motomura, GDC 2015 "Guilty Gear Xrd's Art Style: The X Factor Between 2D and 3D" (GDC Vault)

Not reachable from this environment: gdcvault.com, itch.io, patreon.com, medium.com, DeviantArt images (Cyangmou), the Pixelation forum (most threads not archived as text), and YouTube transcripts. Hyper Light Drifter, Eastward, Blasphemous, CrossCode and Moonlighter art-pipeline specifics could not be verified from primary sources, so this document makes no claims about their methods beyond the Wikipedia lines cited.
