# Japanese ドット絵 style target: cute, clean, readable (inspiration only)

## 0. What's wrong with H1_v2_4 (observed in jump sheet and lines_now)
- The outline staircases are irregular (runs like 1-3-1-2), with doubled L-corners on the hat dome and hair sides. Faint grey AA/halo pixels sit outside the outline.
- The hat is about 45% of the sprite's height and hides the hair, so the girl reads as "red hat with legs".
- A brown band crosses the forehead and acts as a hard interior line. Eyes are square, and the scarf breaks into 1 px red noise.
- Hair is two rectangular side lumps with no strand rhythm. Nothing reads as feminine.

## 1. Line-art rules (線/ジャギ)
- **Pixel-perfect 1 px lines.** Each pixel touches its neighbours by edge or corner, never both. Delete the inner pixel of any L (the "double").
- **ジャギ (jaggies)** are broken run rhythms. On a curve, run lengths must change monotonically: 3-2-1-1-2-3 around a quarter-circle, never 2-1-3-1. On a straight line, keep runs equal: 1:1, 2:1, 3:1 or 1:2. Mixed slopes (2-3-2-3) are allowed only as a deliberate pattern.
- **Flat tops for round shapes.** A head or dome tip needs a flat run of at least 3 px, never a 1 px nipple.
- **Sel-out (色トレス).** The exterior line takes the darkest tone of the material it wraps: dark-red on the hat, dark-brown on hair, deep rose-brown on skin. Use near-black (#241628) only where the shape meets the background on the shadow side and at the feet. On lit top/left edges, the line may drop to the shadow tone or open up entirely.
- **Weight hierarchy.** The exterior is a closed 1 px line. Interior lines are 1 px in a mid-dark tone and appear only at real overlaps (hair over face, arm over torso, brim). Interior lines never use outline black.
- **Hair is drawn as clumps (毛束), not strands.** Use 3-5 tapered locks: a pointed tip, a 1 px dark line on one side only, and a 2-3 px highlight arc (天使の輪, the "angel ring") across the crown. Bangs are 3-4 zig-zag points over the forehead.
- **No pillow shading.** Light comes from top-left, and shadow follows form (under the bangs, under the chin, on the right side), never concentric to the outline. A tone band must not be a 1 px stripe running parallel to the outline (banding).
- **No AA against transparency.** A halo looks dirty on any background. Use 中間色 (in-between colours) only inside the sprite, at most 1 px, on long shallow curves.

## 2. Kawaii and feminine design at 32-48 px
- **Proportions.** 2-2.5 heads tall (2頭身/2.5頭身). The head, including hair, is 45-50% of height and a little wider than the shoulders.
- **Eyes.** Place them low: the eye line sits at 55-60% of head height, down from the top of the hair. Each eye is 2 px wide by 3 px tall (2x4 at 48 px), with 3-4 px of skin between the eyes.
  - Use a dark iris with a 1 px white catchlight in the upper corner, the same side on both eyes.
  - Make the upper lash thicker: a 1 px darker cap that extends 1 px outward at the outer-top corner. Omit the lower lash.
- **Face.** No brows (or hide them under the bangs). The mouth is absent, or a single 1 px darker-skin dot that opens to 1x2 for expressions. Blush is 1-2 px of pink just below and outside each eye.
- **Silhouette.** Cheeks round out with a 1 px step at the jaw. The chin is a 2-3 px flat run. Shoulders are narrow.
- **Hands and feet.** Hands are 2x2 blobs. Feet are 2-3 px wide, with toes turned slightly in (内股) for a cute stance.
- **Posture.** Head tilted 1 px. Arms close to the body. Knees together.
- **Hair silhouettes that read at 1x:**
  - twin tails (the strongest read, with 1 px of bounce on steps)
  - side ponytail
  - hime cut (straight bangs plus cheek-length side locks)
  - long straight hair with a flared tip
  - double buns
  - a bob with side-swept bangs plus an アホ毛 (ahoge, a single stray lock)
- **Accessories.** Hair should be the main silhouette, so headwear must be smaller than the hair mass.
  - A beret tilted on the head (shows bangs and hair).
  - Earmuffs: two 3x3 discs that stay on-theme for snow.
  - A ribbon of 3x5 px with two tails.
  - A fur-trim hood, down on the shoulders.
  - A cat-ear beanie.
  - A small hairclip as a colour accent.
- **Recommended for us:** brown or rose twin tails with earmuffs or a small beret, plus a scarf in an accent colour. This drops the oversized beanie.

## 3. Readability from a distance
- **Silhouette test.** Fill the sprite black: the hairstyle and pose must still be recognisable from S, E and N.
- **3-4 value masses.** Hair (dark), face/skin (light), coat (mid), accent (one saturated hue). Each mass should be at least 30 px at 1x. Squint or blur the image: you should see 3-4 blobs, not speckle.
- **Colour count.** 12-16 per frame, at most 3 tones per material, and 1-2 saturated accents covering 15-25% of pixels.
- **Thumbnail test.** View it at 1x and 2x on snow (#DFEAF6) and on dark tiles. The eyes and hair shape must survive at 1x.

## 4. References (style study only)
- **Mother 3 (GBA, Nobuhiro Imagawa).** Very low colour counts, chunky 2-tone shading, and bold readable silhouettes.
- **Pokémon HGSS overworld.** Near-frontal 2-head bodies, a hair or hat mass as the identifier, coloured outlines, and 2x2 eyes. The "Lyra" design (twin tails plus a hat) is the archetype for our target.
- **Fire Emblem GBA map sprites.** A whole personality in 16x16. Hair colour carries identity, and lit edges are cleanly sel-outed.
- **Seiken Densetsu 3 / Mana series.** Rounded, soft forms, warm hue-shifted ramps, and expressive tiny faces. The best curve discipline.
- **Final Fantasy VI / Tactics (Akihiko Yoshida, Hiroshi Minagawa).** Tactics shows clean outline sel-out and low-contrast interior lines. FF VI shows how to read at 16x24.
- **Bokujō Monogatari / Rune Factory DS.** Cute, feminine NPCs with big low eyes, blush, and accessory-driven silhouettes.
- **Octopath Traveler (HD-2D).** A modern 48 px-class sprite with a heavy dark sel-out outline, a 3-tone material discipline, and clean hair clumps.
- **Atelier (PS1/DS-era sprites).** A strongly feminine, ribbon-heavy accessory language.

## 5. Twelve implementable rules for our pipeline
1. **Smooth the silhouette before thresholding.** Gaussian-blur the alpha/SDF field (sigma about 0.7 px at target res), then threshold. This removes 1 px bumps.
2. **Run-length regulariser.** Per boundary octant, extract run lengths. Where they are non-monotonic (for example 2-1-3), re-quantise to the nearest monotone sequence, and force a run of at least 3 px at the top of domes.
3. **Remove L-corner outline pixels.** Drop any outline pixel that has 2 orthogonal outline neighbours and a diagonal outline neighbour across the corner. Iterate until stable.
4. **Closed 1 px exterior with no halo.** Delete every semi-transparent or grey pixel outside the outline, and make alpha binary.
5. **Sel-out colour.** Outline pixel = darkest ramp tone of the adjacent interior material. On the shadow side and the bottom 2 rows, use #241628. Where the normal faces the light (n·L > 0.6), use the material's shadow tone.
6. **Interior lines only at depth or material overlaps.** Keep a line only as a continuous run of at least 3 px, in the mid-dark tone, never black. Remove lines across the face, including the forehead band.
7. **Orphan cleanup.** Merge tone islands of 2 px or fewer, and remove 1 px tone stripes that run parallel to the outline (anti-pillow).
8. **Toon light from top-left, about 65-70% base tone.** Hair gets a fixed 2-3 px crown highlight arc as a decal rather than lit.
9. **Eye decal.** Eyes are 2x3 (2x4 at 48 px) in the darkest tone, with a 1 px catchlight upper-inner. The upper lash cap is 1 px and extends 1 px outward at the outer-top. No lower lash.
   - Eye line at 55-60% of head height; 3-4 px apart.
   - Blush: 2 px pink, 1 row below the eyes. No brows. Mouth optional, 1 px.
10. **Head scale.** The head plus hair ellipsoid is 45-50% of total height. Headwear volume must be at most 60% of the hair-mass area, and the bangs stay visible.
11. **Hair as clump primitives.** Model twin tails or locks as tapered capsules with pointed tips and 3-4 bang points. Each clump gets a 1-side dark edge, never a full outline.
12. **Automated QA per frame.**
    - Colour count at most 16.
    - Value masses: k-means on luminance into 4 clusters, each at least 30 px.
    - 1x thumbnail and black-silhouette PNGs, exported for review.
    - Fail the build if any L-double or halo pixel remains.
