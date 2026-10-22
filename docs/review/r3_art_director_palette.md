# r3 Art Director: Master Palette & Colourways

Board: `docs/review/r3_palette_board.png`.
Files: `data/palettes/cw_{cranberry,navy,oatmeal,forest,lavender,charcoal}.json`. Generator: `pipeline/tools/make_r3_palettes.py`.

## Palette rationale (32 colours)
- **Shared shadows make it cohesive.** `plum_0` is the shadow for cranberry, lavender, espresso hair and boots. `ink` covers navy, charcoal and blue-black hair. `teal_0` covers forest and teal. Every cream and light neutral shades into the lilac `mauve`. All shadows lean cool and purple; all lights lean warm.
- **Outline** #241628 is a plum near-black. Eyes use the same colour, the catchlight is snow_3, the mouth is crn_1, the blush is red_2, and the ground shadow is snow_1.
- **Skin** has 3 tones with a pink-red shadow. **Hair** has 3 options: espresso, auburn/copper and blue-black. Each file stores all three as `hair_*` ramps.
- **Snow/environment** is snow_0-3. Pines and rocks reuse the clothing ramps, so scene and character share one family.

## Accent strategy
There are 4 saturated accents: red_1, gold_1, orange and teal_1. A colourway uses one accent family, and only on the **hat or pom, the scarf and the mittens**. Colour lands on the head and scarf tails. The coat stays muted and takes about 60% of the pixels, and the accent takes about 25-30%.

## Value structure
The order is outline < pants/boots (ink/plum) < coat mid < accent < skin < highlights. Pants and boots are always dark, so the lower body anchors her on pale snow. Cream cuffs sit between dark masses so they never merge with snow. The oatmeal coat is capped at 2 tones with no near-white. It is still the weakest read on snow, so I'd keep it as an alternate costume.

## Hero recommendation: `cw_charcoal`
- It has the widest value spread: an ink/charcoal body against near-white snow.
- Red is its only saturated hue, so the eye goes straight to the beanie, pom and scarf tails, the shapes that carry the jump.
- It reads in greyscale, so it is colour-blind safe, and it sits furthest from the cool environment hue.

Runner-up: `cw_navy` (warmer, red accent, auburn hair).

## Addendum: fixes from the A_chibi pixel review
1. **Pom vs dome.** Only `cw_charcoal` had pom == hat. It now uses a cream pom (`mauve/oat_1/oat_2`) on the red dome, which gives a strong value break at the silhouette hook. All six files now have pom != hat.
2. **Hair is 3 tones everywhere.**
   - espresso = `plum_0/hair_1/hair_2` (copper shine)
   - auburn = `hair_1/hair_2/red_2`
   - blue-black = `ink/char_1/navy_2`

   Global Lambert bands can't give a shine band without blowing out the hat and coat highlights, so the files carry `"material_bands": {"hair": [-0.35, 0.25]}`. `pipeline/render.py` line 177 now reads this per-material override and falls back to `bands` when it is absent.
3. **Charcoal coat.** The highlight changed from `snow_0` (blue) to `lav_1`, the same purple-grey family as `char_1`. With the higher highlight threshold it appears only as a small lit edge.
4. **Skin and bands.** `skin_0` is lighter (#C06A6A -> #D07C74). Global `"3"` changed from [-0.25, 0.72] to [-0.45, 0.85], so about 70% or more of each part is base tone. Shadow sits only on the far rim and under the brim, and highlights are small.
