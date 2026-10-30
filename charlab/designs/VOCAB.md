# charlab part vocabulary (v1, 2026-10-30)

Shared vocabulary used by the 8 specs in this folder (`<id>.json`). No lab SPEC/NOTES existed when this was written,
so the lab engineer should rename freely here and in the JSONs. The JSON keys below are the contract.

## Units and axes
- All dims and offsets are in **H = head height** of the chosen preset. Offsets are relative to the `attach` anchor's centre.
- Blender convention: Z up, character faces **-Y**, +X = character's left. Rest pose is an A-pose with arms at 25 deg.
- `dims` = [x width, y depth, z height]. For sphere, ellipsoid, cylinder and cone these are full diameters/heights.

## Body presets (`body.recommended`, `body.allowed`)
| preset | heads | head | neck | torso (chest+belly+pelvis) | legs | head width | shoulder width | test sprite px |
|---|---|---|---|---|---|---|---|---|
| chibi | 2.5 | 1.0 | 0.05 | 0.65 | 0.80 | 0.95 | 0.75 | 32-48 |
| compact | 3.5 | 1.0 | 0.10 | 1.05 | 1.35 | 0.85 | 0.80 | 48-64 |
| slim | 5.0 | 1.0 | 0.15 | 1.55 | 2.30 | 0.80 | 0.85 | 64-96 |

`body.build` scales widths: `preset` is one of petite / average / athletic / sturdy, and `shoulder`, `hip` and `limb_radius` are multipliers (1.0 = preset default).
Feminine defaults: hip width >= waist + 15%, slightly narrower shoulders than hips at chibi/compact, neck thin, and feet small (0.25H long at compact).
`body.test_sprite_heights_px` lists which sizes are worth rendering per preset. Slim at 32 px gives 1-px limbs, so skip it.

## Body anchors / segments (bones)
`head, neck, chest, belly, waist, pelvis, upper_arm, forearm, hand, thigh, shin, foot` (limbs are .L/.R, and a spec without a side means both).
Sub-ranges used by `cover`: `pelvis_top, upper_arm_top, forearm_top, forearm_low, thigh_top, thigh_top_edge, shin_top, shin_low, torso_side, thigh_side, head_band`
(the top/low ranges are the top or bottom 30% of the segment, `_edge` is a thin 0.04H ring, `torso_side`/`thigh_side` are a vertical stripe on the outer side, and `head_band` is a ring around the head at brow+0.1H).
The base body is built as capsules, one per segment, plus an ellipsoid head. Hands are mittens: no fingers.

## Piece geometry (`pieces.<name>.geom`)
| geom | meaning | keys |
|---|---|---|
| `cover` | shell over body segments = the segment capsules scaled by (1+inflate) | `segments[]`, `inflate` (H), optional `length` (0-1 of last segment), `sleeve` none/short/long, `hem` waist/hip |
| `sphere`, `ellipsoid`, `box`, `cylinder`, `cone` | rigid primitive parented to `attach` | `attach`, `dims`, `offset`, optional `bevel`, `axis`, `mirror` (also place at -X) |
| `strap` | thin flat band between two anchors | `from`, `to`, `width`, `mirror` |
| `stripe_pattern` | painted stripes on another piece (no geometry) | `attach`, `count` |

Every piece also has a `piece` field naming its **vocabulary role**: `one_piece_suit, top, bottom, skirt, shoes, boots, socks, gloves, helmet, visor, cap, headband, goggles, collar, bib, belt, band, strap, backpack, tank, bag, fins, antenna, decal`.
`decal` means paint it flat or use a near-flat box (no silhouette change) and drop it first when simplifying. Free-text `note`, `brim`, `cap`, `valve`, `knot` and `tip` keys are builder hints.

## Colour roles
`colour` = base, `shade` = flat shadow tone (null means use the outline tone only, and `shade_auto: true` means derive it as base x 0.75 value), both naming keys in `palette`.
Every palette has `outline` (#2b2235, shared by the whole cast), `skin`, and `skin_shade`, then hair (2-3), material pairs, and 1 accent: 8-12 colours in total.
Shading model is 2 tones per material (base + shade) + outline. Highlights are only `hair_hi` and the optional eye highlight.

## Hair (`hair`)
| style | build |
|---|---|
| `pixie` | skull shell (head ellipsoid x `volume`), nape tapers to a point, fringe slab |
| `short_bob` | shell + one closed mass down to `length` (0 = ear, 0.5 = chin, 1 = shoulder), ends curve inward |
| `ponytail` | pulled-back shell + `tail_segments` tapered ellipsoids (taper `tail_taper`) at `tail_pos` high_back/high_crown |
| `buns` | slick shell + `bun_count` spheres of `bun_radius` at `bun_pos` |
| `helmet_covered` | hair hidden by a helmet; only the `under` style's fringe is built, inside the visor |
| `cap` | headwear (`hat`: baseball default / bucket) over the `under` style |
Shared params: `length` (0-1), `volume` (shell scale 1.0-1.2), `fringe` none/straight/side_swept, `fringe_length` (0-1 of forehead), `part` left/right.
Rule from the swordswoman: hair is **one or two closed masses**, with no loose locks and no strands. The fringe is one solid slab.

## Face (`face`)
Eyes and brows only. `eyes: oval_tall` (dark outline colour, `eye_size` in H, `eye_spacing` centre-to-centre in H), `brows: short_flat | soft_arch` in `brow_colour`, and `highlight` adds 1 white px per eye at >= 48 px.
No nose, no mouth geometry (a mouth may be added later as a 1-2 px decal per expression).

## Secondary motion (`secondary_motion[]`, max 3, usually 0-1)
`type`: `none` | `rigid_lag` (follows the parent with N-frame delay, clamped angle) | `pendulum` (1 bone) | `spring_chain` (n bones, `stiffness`, clamp deg) | `rigid_flare` (skirt: follows the pelvis + small hem lift).

## Tiers (`tiers.simple|medium|detailed`)
Exact lists of piece names to build. The simple tier has to read on its own at the smallest test size, medium adds bands, straps and the headwear, and detailed adds decals plus at most 1 extra protrusion.
