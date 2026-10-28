# STYLE_GUIDE: chibi swordswoman in Pokemon-trainer pixel style (v1, 2026-10-26)

The 3D model (v2/parts/out/AB4, v2/hy3d/rig, keys in v2/hy3d/keys_parts/) is still the hidden reference for proportions, camera and poses.
Design authority is still v2/design/DESIGN_SPEC.md (Level D) and turnD/. This guide replaces only the **pixel rendering style** (palette, outline, shading, face, animation conventions).
User priority (via lead): **battle-trainer sprites + Mystery Dungeon**, with research deciding the details. Overworld eras are documented for context.

## 1. What "Pokemon trainer pixel art" means (measured on refs in v2/style/refs/, board: refs_board.png)

| family | frame / figure size | heads tall | camera, dirs | colours | outline | shading | face | animation |
|---|---|---|---|---|---|---|---|---|
| Gen3 GBA overworld (FRLG/Emerald) | 16x32 frame, figure ~20 px | ~2 | top-down 3/4 (~45 deg, front view squashed); 4 dirs (S, N, W; E = mirror) | 12-14 + transparent (one 16-colour OBJ palette) | pure black #000000 all round | 1 shadow tone + rare highlight; light top-left | eyes = 1x2 black px (no white) | walk: step/stand/step/stand, 8 ticks each (133 ms, pokeemerald object_event_anims.h); run: 5/3/5/3 ticks with dedicated run frames, body leans |
| Gen4 DS overworld (DPPt/HGSS) | 32x32 frame, figure ~24-28 px | ~2 | top-down 3/4; 4 dirs; HGSS following Pokemon use 4 dirs x 2 frames | ~15 | black outer; inner lines dark local colour | 2 tones + highlight, flatter than BW | 1x2 to 2x2 eyes, 1 px white sometimes | 4-beat walk (2 step frames), run has extra frames |
| Gen5 BW/B2W2 overworld | 32x32 frame, figure ~29 px (Essentials kits store it 2x as 64x64) | ~2.2 | top-down 3/4, more frontal; 4 dirs | 14-15 | black outer; inner lines dark local colour | 2-3 tones, crisper clusters, hair sheen band | 2x2-2x3 eyes with dark iris | walk 4 f; run 4 f with strong lean and big hair lag (Rosa run sheet) |
| Battle trainers G3 (64x64), G4/G5 (80x80) | figure 55 (G3), 65-69 (G4), 65-75 (G5) px | **3.2-3.6 (measured, PROPORTIONS_REF.md); slim: shoulders 0.7, waist 0.5 of head width, legs 40-45%** | single front 3/4 view, facing the player; one back sprite | 14-15 (4bpp limit) | black outer outline everywhere; inner lines dark local colour (dark red on red, brown in hair) | 3-4 tones per material, hue-shifted (red -> violet, skin -> warm tan), clear hair sheen band, light upper-left | eyes 3-4 px tall: black lash line, dark-top iris, 1 white glint | static in G3/G4; B2W2 and BW2 gyms: short looped frame-by-frame idle (coat/hair sway, throw pose) |
| PMD Explorers / SpriteCollab | frame 24x40 to 32x56 (attacks up to 72x88), figure 19-30 px | 1.5-2.5 | **8 dirs** (rows S, SE, E, NE, N, NW, W, SW), low 3/4 camera | 12-13 | pure black outer, black or very dark inner lines | 2 tones + 1 highlight, flat, chunky | big 2x3 eyes with glint | frame-by-frame, very expressive: Walk 4 f (8/12/8/12 ticks), Idle 7 f (6/12/12/20/12/12/6), Attack 10-13 f mostly 2-tick frames with 4-tick holds, Hurt 2 f (2/8); big squash/stretch, VFX drawn separately |
| Fan games / Pokemon Essentials | charset = 4x4 grid (rows down, left, right, up; 4 frames each), frames 32x32 or 64x64 (2x-upscaled art), trainer battlers 80-160 px | as source era | 4 dirs (8-dir via plugins) | 16-ish | black outer | copies BW/HGSS | as source era | 4 f walk at engine speed; run = separate charset (e.g. plrun000) |

Common invariants across all families (these are what make it "read Pokemon"):
1. **Pure black outer outline** (#000000), 1 px, continuous. Never a coloured selout on the outside.
2. **Inner lines in a dark version of the local colour**, not black, on larger sprites (battle, BW).
3. **About 15 colours per sprite** (16-colour hardware palette).
4. **Light from the upper-left**, shadow on the right and underside, **hue-shifted** shadows.
5. **Hair is a solid mass with a light sheen band**, not strands. Clean cel clusters, no dithering, no AA ramps on the outline.
6. **Eyes are the face**: black upper lash line, dark iris top, one white glint; mouth 1-2 px; no nose at chibi sizes.
7. Animation is **frame-by-frame**, with holds of different lengths (PMD) rather than even timing.

## 2. Candidate sub-styles (tested in tests/; scores in RESULTS.md)
| id | name | size | use | strengths | risks |
|---|---|---|---|---|---|
| A | **PMD-40** | figure 40 px in 48x48 (actions up to 64x64) | 8-dir action sprite | closest to PMD feel and to our action set; cheapest to animate (fewer pixels per frame) | katana 1-2 px; face only 2x3 eyes; less "rendered" |
| B | **BW-battle-72** | figure 72 px in 80x80 | front 3/4 portrait/battler, idle loop, attack pose | richest rendering, most "trainer" look | single direction; 3x the pixels per frame; chibi proportions are off-model for real battle trainers (they are 3.2-3.6 heads and slim) |
| C | **Hybrid-48 (battle rendering on PMD chassis)** | figure 48 px in 64x64 (actions 96x64) | 8-dir action sprite | keeps the existing 48 px pipeline and proportion lock; enough pixels for 3-tone shading, 3x4 eyes, 2 px blade | still needs hand cleanup; must avoid pillow shading in 3 tones |

## 3. Shared palette (v2/style/pk_palette.json, 16 opaque colours)
| char | hex | role |
|---|---|---|
| K | #000000 | outer outline, pupils, lash line |
| W | #f8f8f8 | eye white, glint, blade highlight |
| s / S | #f8d0b8 / #d89878 | skin base / shadow + mouth |
| L / H / h | #847078 / #403038 / #241c24 | hair sheen / base / shadow (h also obi/boot shadow and inner lines in dark areas) |
| e / E / R / r | #f87068 / #d03848 / #982840 / #581838 | red light / base / shadow / deepest (inner lines on red, sleeve inside) |
| d | #4c4460 | obi and boots base |
| I / i | #3868b8 / #1c2c58 | iris lower half / iris dark (most of the iris) |
| n / k | #a8b0c8 / #b07838 | blade / katana guard |
Per-material tone budget: A uses 2 tones + highlight (skips e on dress, L only as 1 band); B uses all; C uses all but e only on bow + shoulders.

## 4. Proportions (from DESIGN_SPEC Level D; pixel rows from the top of the figure)
| part | A 40 px | C 48 px | B 72 px |
|---|---|---|---|
| bow | 3 | 4 | 6 |
| head (hair top to chin) | 17 | 20 | 30 |
| dress (chin to hem) | 12 | 15 | 22 |
| legs | 5 | 6 | 9 |
| boots | 3 | 3 | 5 |
| head width | 18-19 | 23 | 32 |
Feet pivot = bottom centre of the cell, 2 px above the bottom edge.

## 5. Outline and shading rules (testable)
- O1: every silhouette edge pixel is K. No K-less edge, no double-thick outline except at the boot soles and the underside of the hair mass (2 px allowed).
- O2: inner lines: hair over skin = h (the bang edge is h, not K, in B/C; K in A); dress/obi = r over d; sleeve vs body = r; legs/hem = K; bow knot = r.
- O3: no outline jaggies: a line stepping 1 px per row must use equal step lengths (1-1-1 or 2-2-2), no 1-3-1.
- S1: light upper-left. Shadow tone on the right-hand third of every volume and under every overhang (under bow, under bangs on the forehead 1 px S band, under sleeves, under obi, under hem on the legs).
- S2: no pillow shading: never ring a shape with its shadow colour on all sides.
- S3: hair = H base, h on the right and underside, one curved L sheen band (2-3 px thick in C/B, 1 px in A) on the upper-left of the skull, following the head curve.
- S4: clusters >= 2 px except the eye glint and the blade tip. Lint: 0 orphans outside the face/blade.
- S5: <= 16 colours per frame; the same char always means the same hex in every frame.

## 6. Face construction (SE view)
- C 48: eye = 3 wide x 4 tall. Row 1 KKK lash (outer end extends 1 px down-out), rows 2-3 `iW i` / `II I`: dark iris top i, glint W upper-inner, iris I below, row 4 I base, no lower lid line. Far eye 2 wide. Eyes start 1 px below the fringe. Mouth = 1-2 px S, 3 px below the eyes, off-centre toward the facing side.
- A 40: eye = 2 wide x 3 tall (K lash row, iW, II). Mouth 1 px.
- B 72: eye = 4-5 wide x 6 tall: K lash 2 px thick at the outer corner, i top 2 rows, I middle, 1 px lighter iris bottom (I with W glint 2x2 upper-inner), thin S lower lid hint. Mouth 2-3 px r or S.

## 7. Directions
A and C: 8 directions in PMD row order S, SE, E, NE, N, NW, W, SW; draw S, SE, E, NE, N and mirror W, SW, NW (katana hand swaps, accepted). B: front 3/4 only (+ optional back view), like battle sprites.

## 8. Frame counts and timing (ms; PMD ticks are 1/60 s)
| action | frames | timing | notes, Pokemon basis |
|---|---|---|---|
| idle | 6 | 200,150,150,300,150,150 | PMD idle (uneven, 1 long hold); 1 px body bob, bow lags 1 f |
| walk | 6 (or 4 PMD-pure) | 100 each (PMD 133/200 alternation for 4 f) | contact frames drop the head 1 px; Gen3 step/stand/step/stand structure |
| run | 6 | 70 each, contact 80 | Gen3 5/3/5/3 tick rhythm = long contact, short passing; lean 2 px forward, hair/bow lag 1 f |
| jump | 7 | antic 120, crouch 80, launch-stretch 50, rise 80, apex hold 160, fall 80, land-squash 100 (+recover 120) | squash/stretch 2-3 px |
| dash | 5 | antic 100, smear 40, smear 40, skid 120, recover 120 | smear = stretched silhouette + 2-3 speed lines in W/n, 1-2 frames only |
| slash | 7 | antic 160, wind-up 80, smear arc 40, impact hold (hit-stop) 120, follow-through 80, recover 120, settle 100 | PMD Attack: mostly 2-tick frames with a 4-tick hold; arc drawn as a solid W/n crescent with K outline, like Pokemon move VFX |
Lively/bouncy/smears within the Pokemon look: (1) uneven timing with holds (PMD), (2) squash/stretch of 1-3 px, never sub-pixel, (3) secondary motion on the bow and bob (1 f lag), (4) smears are solid palette shapes with the K outline, one frame, plus separate VFX layer (white arc, dust puffs) as Pokemon does for move effects.

## 9. Animation method (lead request)
Frame-by-frame redraws guided by the rigged 3D keys (v2/hy3d/keys_parts/*/fNN_matid.png) is recommended for A/C. The cutout rig read as a "paper doll" (rigid head+torso block, arms barely move) and PMD/BW animations are hand-drawn per frame.
Pipeline: (1) 3D key render per frame at target size gives the pose, foreshortening and contact timing; (2) the pixel artist redraws the whole figure per frame as a char-map, reusing only the **head stamp** (8 dirs x 2-3 expressions, may be squashed by 1 px) and re-drawing torso, sleeves, skirt, legs and hair silhouette each frame; (3) lint (pk.py) for palette, orphans and outline; (4) smear frames are drawn, never generated from the rig.
Cutout with swap poses is acceptable only for idle/hold frames.

## 10. Round-1 critique corrections (binding for r2+)
- R1: **no black inside the silhouette** except lash lines and pupils. Sleeve/body, obi edges, hem/legs crease and arm/torso seams use r (on red), h (on hair/obi/boots), S (on skin).
- R2: 3-tone volume shading with a clear upper-left light: 1 px S cast shadow from the fringe across the forehead, R shadow from the skirt hem onto the thighs (S on skin), right third of skull/dress/sleeves in the shadow tone, deepest tone (r / h) only in crevices (sleeve inside, under the bow knot, under the obi).
- R3: hair: the bob is one mass but its silhouette is not a helmet; fringe ends in 3-4 shallow tapered points; the bob ends taper into 2-3 short points at the jaw; sheen = 2-3 short broken L dashes following the skull curve (not one stripe).
- R4: eyes: heavy upper lash line (K, 1 px, 2 px at the outer corner, flicks 1 px outward), iris mostly i with I only on the bottom row(s), one W glint; no pale-blue fill.
- R5: head: rounder skull, cheeks taper 1-2 px toward a soft chin; jaw is not a vertical wall.
- R6: pose: true SE 3/4 turn (far side narrower, face centre shifted toward picture-right), weight shift, feet staggered (far foot 1-2 px higher), katana held deliberately (relaxed low guard), slight head tilt.
- Rejected critic advice: hue-shifted outer outlines (measured: PMD, BW and HGSS refs all use pure #000000 outside).

## 11. Recommendation after 4 rounds (see RESULTS.md) and slash learnings
- **Rendering = PMD rules** (from A', the best-scoring test): pure black 1 px outer outline (lint `edge_nonK=0`), no black inside except eyes, 2 tones + 1 highlight per material (3 on red), compact L sheen cluster, 2x3 eyes with a 1 px K cap and 1 W glint, 1 px mouth, chunky readable clusters, <=16 colours.
- **Proportions = slim trainer chibi** per PROPORTIONS_REF.md (3.0-3.3 heads, shoulders 0.70-0.75 / waist 0.5 of head width, legs 35-40%, 1-2 row neck, eye centre 0.65 down the head). This replaces the 2.4-head trapezoid, which measures 0.95 body/head width and is what reads "fat".
- **Size = 44-48 px figure in a 64x64 cell** (40 px in 48x48 minimum). 32 px only fits the 1.7-head overworld recipe.
- **Slash (from the A' test, critics 5-5.5/10):** pin the back foot to one ground row in every frame; anticipation = 1 px crouch, not a stretch; turn the torso and move the head 1-2 px into the swing on smear/impact; the smear crescent is attached to the hilt, follows the real swing path (overhead -> low-front), 3-4 px thick, with the K outline only on the leading edge and the trailing edge tapering out without an outline; impact frame gets a 1-2 frame white hit spark; follow-through must overshoot (otherwise merge it with recover and hold 200 ms); blade length and head size are constant (rotate, don't rescale).
