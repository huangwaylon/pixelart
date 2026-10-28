# r4 Costume & Colour: outfit study on A_chibi

Board: `archive/snowpeak/boards_r04_r10/outfits_keys.png`. Variants: `data/variants/O1..O6_*.json` (all `extends: A_chibi`). 4 iterations each, rebuilt after the lead's fix.

**Hat choice:** all six use `beanie_tall`. After the fix, the plain `beanie` still shows skin on top of the dome: the head top (hc+0.95hr) is above the dome top (hc+0.91hr). `beanie_slouch` shows a forehead strip between the dome and the cuff from S/SE.

| Variant | Intent | Strengths | Weaknesses |
|---|---|---|---|
| O1 Parka + trims, charcoal/red, pom 1.5 | Classic hero | Best value contrast. Cream cuff, hem and sleeve breaks | Pom is the same red as the hat. Salmon `red_2` band is large |
| O2 Puffer + skirt/tall boots, navy/red, chunky scarf | Cosy | Red pom on navy and the red scarf frame the face | Hat merges with coat. No scarf tail. Tall boots don't show |
| O3 Long duffle, cranberry/mustard, pom 1.4 | Storybook | Mustard pom, scarf and mittens make a triangle | Monochrome red. The long length doesn't read |
| O4 Parka + tall boots, forest/orange | Outdoorsy | Strongest hue contrast on snow | `gold_2` highlight covers about 40% of the dome (candy corn) |
| O5 Cropped duffle + skirt, lavender/yellow, bob_long | Playful | Long bob frames the face. Cream pom | Cream skirt, hem and boot cuffs make stripe noise |
| O6 Puffer, oatmeal/teal | Muted alt | Good back view | Teal cuff merges into the teal dome. Weakest on snow |

## Top picks
1. **O2**: the warm pixels sit only at the head, scarf and hands, and the pom reads as its own shape.
2. **O1**: strongest silhouette and greyscale read. It becomes the hero once the pom gets its own colour.

## Proposed palette edits (art director)
- Pom = hat: only `cw_charcoal` merges. Change to `"pom": ["mauve","oat_1","oat_2"]`.
- `cw_forest`: `"hat": ["gold_0","orange"]`.
- `cw_oatmeal`: `"hatcuff": ["mauve","oat_1"]`.
- `cw_lavender`: add `"skirt": ["ink","char_1"]`.

## Feature requests
- Plain `beanie`: dome height 0.80hr or more, or clip the head under the hat.
- `beanie_slouch`: close the forehead gap above the cuff.
- Duffle: hem trim so `coat_len` reads. Tall boots: a contrasting cuff visible on chibi legs.
- Per-variant `palette_overrides` / `hair_ramp`.
- A chunky scarf with one short tail.
- The orphan, margin and height QA errors are inherited from A_chibi.
