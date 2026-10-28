# Outline techniques for pixel art

## 1. Approaches
- **Black closed outline**: reads best, but looks flat and "stickery" and vanishes on dark backgrounds.
- **Dark coloured outline**: a hue-shifted dark of each fill, or one shared plum/navy accent. Softer than black and the most common modern choice (GBA/DS Pokémon).
- **Sel-out**: dark on the shadow side, near-fill or broken on the lit side. Adds volume and light direction, but is weak where the lit fill matches the background value.
- **Open outline**: lit edges dropped. Airy, but the silhouette leaks.
- **Lineless**: shape from value/hue contrast only. Needs a controlled palette or bigger sprites.
- **Outer vs inner**: outline where the sprite meets the background. Separate interior parts with the shadow shade of the part *behind*, not full dark. Full-dark inner lines clutter 40px sprites and shrink faces.
- **1px vs 2px**: use 1px for 16–64px sprites. 2px is for UI and sticker borders.
- **AA**: anti-alias inward only (line to fill). Against transparency the neighbour colour is unknown, so outward AA becomes a halo.

## 2. When outlines are needed
- **Needed**: small sprites (≤32px), busy or varied-value backgrounds, a far camera, phone screens, overlapping actors and VFX.
- **Lineless works**: high-res art, a controlled world palette, strong figure/ground value contrast (Hyper Light Drifter), or separation by **rim light**, **contact shadow**, back-glow or a muted background.

## 3. References (style inspiration only)

| Game | Year | Outline | Camera | Height | Lesson |
|---|---|---|---|---|---|
| Final Fantasy Tactics | 1997 | Dark coloured + sel-out | **Isometric** | ~40px | Closest to our camera and size |
| Pokémon R/S/E | 2002 | Dark coloured, closed | Top-down 3/4 | ~24px | Hue-shifted dark reads on every tile |
| Pokémon D/P | 2006 | Dark coloured; softer inner lines | Top-down 3/4 | ~28px | Inner lines lighter than outer |
| PMD Red/Blue | 2005 | Dark coloured, closed | Top-down | ~24–32px | Chunky silhouettes on noisy floors |
| Mother 3 | 2006 | Black, closed | Top-down 3/4 | ~20px | Max readability, toy charm |
| Stardew Valley | 2016 | Dark brown, closed | Top-down | ~28px | One warm dark unifies the palette |
| Hyper Light Drifter | 2016 | Mostly lineless | Top-down | ~24px | Value contrast replaces lines |
| Celeste | 2018 | Dark, closed | Side | ~11px | Tiny sprites: outline = silhouette |
| CrossCode | 2018 | Dark coloured | Iso-ish | ~32px | Readable in fast iso action |
| Octopath Traveler | 2018 | Dark coloured, closed | 3/4 HD-2D | ~36px | Lines survive bloom and blur |
| Dead Cells | 2018 | Lineless; 3D→pixel, rim light | Side | ~50px | Our pipeline's ancestor: rim light separates |
| Blasphemous | 2019 | Selective dark | Side | ~55px | Lit edges carry shape in a dark world |
| Eastward | 2021 | Lined actors, lineless world | Top-down 3/4 | ~32px | Figure/ground split by line use |
| Sea of Stars | 2023 | Sel-out / near-lineless + lighting | Iso-ish 3/4 | ~36px | Current trend; mobile port 2026 |

**Japanese モダンドット絵**: the mainstream (Pixiv, mobile/gacha) is bright chunky chibi with a dark coloured outline (often one deep plum/brown) plus sel-out highlights. A second current, lineless chunky 横スクロール, belongs to the high-res end. At ~40px the first is the safer model.

## 4. Recommendation for Snowpeak
These notes come from viewing our renders at 1x on snow and navy (`archive/snowpeak/boards_r04_r10/8_outline_styles_keys.png`, `out/variants/OL_*__jump_sc/preview/distance_test.png`):
- **dark**: strongest on snow. On navy, the hair and boot outline merges with the background and the silhouette shrinks ~1px.
- **none / colored**: nearly identical at 1x. The oat coat and lavender shadow go soft against the pale snow.
- **selout**: the best on both. Shadow-side darks anchor the figure on snow, and the lit fills hold the edge on navy.
- **open**: leaks where lit oat meets white snow.

**Adopt a 1px sel-out built on a dark coloured outline, on the outer silhouette only:**
1. **Outer line**: dark hue-shifted per material (hair → dark brown, teal → deep teal, cloth → plum). Never black, and never the night-tile navy. Closed on the shadow side and the feet.
2. **Lit top/upper-left edges**: one shade darker than the fill, never transparent. The silhouette stays continuous in value.
3. **No full-dark interior lines.** Overlaps use the back part's shadow shade. The face stays clean.
4. **Night and dark rock**: a palette-swapped 1px light rim on the lit edges plus the contact-shadow ellipse. Don't rely on the outline there.
5. **No outward AA.**
6. **Gate**: the 1x silhouette test must pass on snow, rock and navy.

**"Do we need a connected outer outline?"** Yes, closed *in value*, but it doesn't need to be one dark colour all the way round.

**Reading**: Sam Keddy, "Pixel Art Outlines" 1–2; Pedro Medeiros (saint11), "Outlines"; Cyangmou, "Shapes and Outlines" (see lospec.com/pixel-art-tutorials/tags/outlines).
