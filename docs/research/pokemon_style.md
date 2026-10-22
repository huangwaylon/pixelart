# Style target: Gen 3/4 Pokémon overworld humans (inspiration only)

## 1. Sprite specs
- **Cells:** Gen 3 humans **16x32** (bikes/large NPCs 32x32). Gen 4 **32x32**.
- **Height:** Gen 3 about 20-24 px, Gen 4 about 24-28 px (12-16 px wide).
- **Proportions:** about 2 heads tall. Head plus hair/hat is 45-50%, torso 25-30%, legs 20-25%.
- **Directions:** 4 (right = mirrored left), no diagonals.
- **Walk:** 3 unique frames (stand, step-A, step-B) played stand-A-stand-B. One 16 px tile takes 16 frames at 60 fps (about 267 ms), with the pose changing every 8 frames and a 1 px bob on steps. **Run** is a separate 3-frame sheet: forward lean, longer stride, 8 frames per tile.

## 2. Rendering traits
- **Colours:** 4bpp, so 16-colour palettes with index 0 transparent, leaving 15. A single sprite really uses about 9-13.
- **Outline:** closed 1 px exterior, very dark and slightly coloured (not pure black). Gen 4 lightens lit edges (mild sel-out). Inner lines only at overlaps (brim, hair over face, arm over torso), in the shadow tone. None inside the face.
- **Shading:** flat cel, **2 tones per material**, sometimes 3 on hair or hats. Light from top/upper-left. **No dithering, gradients or AA.** Highlights are rare: a 1-2 px band on hair or a cap.
- **Face:** eyes 1x2 or 2x2 dark px, set wide apart, mid-head. Gen 4 sometimes adds a 1 px catchlight. No brows, mouth usually omitted, skin 2 tones.
- **Hair/hats:** one big, high-contrast mass, often wider than the face. The main identifier, readable from behind.
- **Hands/feet:** hands are 2x2 skin blobs. Shoes are 2-3 px, darker than the legs.
- **Bright terrain:** dark outline plus mid/dark clothing contrast with pale ground. On snow routes, warm accents carry the read.

## 3. Perspective
Maps are top-down oblique, but humans are drawn **near-frontal** (effective elevation about 10-20°): face fully visible, a sliver of hat top, no foreshortening. Keep 26.565° for terrain, but render the **character at 12-18°** (our sheet's 18° is fine). This mixed projection is exactly the Pokémon approach.

## 4. Palette philosophy
- Short ramps (2-3 tones), **1-2 saturated accents** per character, everything else muted.
- Values: outline < clothing < skin < highlight. The silhouette must read in greyscale.
- Hue-shift: cool/purple shadows, warm/yellow lights, pink-red skin shadows.
- Lospec cross-checks: **Apollo** (AdamCYounis; icy ramp #172038→#a4dddb, snow #ebede9, warm #a53030/#de9e41) and **Endesga 32** (steel #262b44→#c0cbdc, accents #e43b44/#feae34). snowpeak_v1 already follows this logic.

## 5. Ten rules for our pipeline
1. **At most 3 tones per material**, 2 for skin and boots. Collapse parka/mustard 4-band ramps to 3, and skip the light band on small parts.
2. **No orphans:** delete tone islands of 2 px or fewer. Bands become chunky shapes.
3. **Minimum feature width 2 px** (limbs, scarf, braids, pom-pom).
4. **Exterior outline #241628.** Optional sel-out to the part's shadow tone on top/left lit edges. Inner lines only at brim, hair/face and arm/torso.
5. **Eyes 2x3 px** at 41 px scale (1x2 at 24 px) in the darkest tone, with a 1 px light catchlight top-left and about 4 px spacing. **Remove brows** (or 1 px). No mouth in neutral.
6. **Big hair/hat silhouette:** hat dome in 2 tones plus one 2-3 px highlight band, hair mass wider than the face.
7. **Raise the toon threshold** so about 70% of each part is base tone. Shadow only under brims and scarf and on the lower/back half. Fixed upper-left light.
8. **Mittens 2x2-3x3 blobs; boots 3-4 px**, darkest on the ground row.
9. **Character camera 12-18°**, independent of the map. Consider a 4-direction-plus-mirror mode for authenticity.
10. **Value test:** readable in greyscale at 1x on #DFEAF6 snow, warm accent (parka red / mustard) at about 25-35% of pixels, and at most 16 colours per frame.
