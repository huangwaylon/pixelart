# charlab spec format, as the lab reads it

The lab reads the designer's specs (`charlab/designs/<id>.json`) and vocabulary (`charlab/designs/VOCAB.md` v1) **as written**.
No keys are renamed. This file records how `model.py` interprets each key, and the few places where the lab had to choose.

## Units and axes (VOCAB, unchanged)
- H = head height = 1 world unit. The floor is z = 0, the character faces -Y, and +X is her left.
- `dims` are full sizes in H. `offset` is in H from the `attach` anchor's centre, in world axes.
  For a limb anchor without a side (`foot`, `hand`, ...), the piece is built on both sides with x mirrored, so `+x` is always the outer side.

## Body (`body`)
| key | lab use |
|---|---|
| `recommended`, `allowed` | which preset the hub entry features; all 3 presets are built in sweeps anyway |
| `build.preset` | petite .93 / average 1 / athletic 1 / sturdy 1.10. These scale shoulder width (half effect), hip width (40 %) and limb radius (half effect). |
| `build.shoulder`, `hip`, `limb_radius` | multipliers on top |
| `test_sprite_heights_px` | drawn as a green corner on the grid GIF cell |

Preset table (VOCAB lengths). Radii are lab choices, in H.

| preset | heads | neck | torso | legs | head w | shoulder w | hip/shoulder | waist/hip | thigh r | shin r | ankle r | arm r | foot len |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| chibi | 2.5 | .05 | .65 | .80 | .95 | .75 | 1.06 | .80 | .17 | .12 | .085 | .09 | .34 |
| compact | 3.5 | .10 | 1.05 | 1.35 | .85 | .80 | 1.05 | .78 | .16 | .105 | .072 | .08 | .30 |
| slim | 5.0 | .15 | 1.55 | 2.30 | .80 | .85 | .98 | .72 | .145 | .095 | .062 | .07 | .36 |

**Lab choices:**
- Feet are longer than VOCAB's 0.25H at compact. Below about 0.3H, the shoe vanishes at 32-48 px.
- The rest pose is an A-pose at 25°. The walk lowers the arms to the preset's `abduct` angle (chibi 16°, compact 14°, slim 11°), plus whatever clearance the torso garment's inflate needs, capped at +10°.
- The eye line sits 0.10H below the head centre.

## Segments (VOCAB names)
- **Body segments:** `head, neck, chest, belly, waist, pelvis, upper_arm, forearm, hand, thigh, shin, foot`.
- **Sub-ranges:**
  - `_top` is t 0-0.3 along the bone and `_low` is t 0.7-1.
  - `pelvis_top` is the upper 55 % of the pelvis.
  - `thigh_top_edge` is a 0.04H ring at t 0.3 (or at `length`).
  - `torso_side` and `thigh_side` are the outer vertical stripe.
  - `head_band` is a 0.12H ring centred at eye line + 0.34H.
  - `waist` is the lower quarter of the belly segment.
- **Lab choice:** a full `forearm` inside a cover stops at t 0.86, so the hand always reads outside the sleeve.
- `length` applies to the last limb segment of a cover: from the top for thigh/upper_arm/forearm, from the bottom for shin.

## Pieces (`pieces.<name>`)
| geom / role | how it is built |
|---|---|
| `cover` | Union of the listed segment capsules, offset outward by `inflate` (H), clipped to the sub-range. Torso parts blend with k 0.10, limbs with 0.04. `side` limits it to one side. `knot` adds a 0.09H sphere behind the head. |
| `sphere` / `ellipsoid` | rigid ellipsoid at attach + offset |
| `box` | rounded box (`bevel`, default 35 % of the smallest half-size) |
| `box` + role `collar` / `bib` | Wrap: the box volume intersected with a shell 0.02H outside the outermost torso garment, so it hugs the body instead of floating. |
| `box` + role `goggles` + `lens` | front face painted in the `lens` colour inside two lens windows |
| `cylinder` | `axis` x / y / z. `cap: hemisphere` gives round ends. `valve` adds a small dark cylinder on top. `tip: "sphere D colour"` adds a ball. |
| `cone` (role `skirt`) | Elliptic frustum from the waist (fitted) down to offset z - dims.z/2. The bottom diameters are `dims` x/y. |
| `sphere` + role `helmet` | Hollow shell, 0.07H thick. If the tier lists `visor`, an angular window (sized from the visor dims, ±80° azimuth max) is cut out. The inner surface takes the visor colour (VOCAB: flat tint, face drawn on top). |
| role `cap` with `brim` (sphere) | dome (lower part clipped) + a forward brim box tilted 10° down |
| role `cap`, `cylinder` (bucket hat) | cylinder crown + a flat ring brim of radius 0.68H, tilted 15° down |
| `strap` | A band of `width` on a shell just outside the torso garment, in the plane through `from` and `to`. Front and back are both drawn. Anchors: `shoulder`, `shoulder.R`, `waist`, `back_waist`, `bib_corner`, `bag`. |
| role `decal` | **Paint** if its smallest dim is < 0.1H: it recolours garment surfaces inside the box, with the thin axis extended to 0.18H so it reaches the surface. Paint never lands on skin, hair or visor. Bigger decals (pouches, pack roll, neckerchief) are real geometry. |
| `stripe_pattern` | paint: `count` vertical bands on the skirt (lower 75 %) |
| role `visor` | not geometry (see helmet) |

## Hair (`hair`)
- **Styles:** `pixie`, `short_bob`, `ponytail`, `buns`, `helmet_covered` (builds the `under` style's cap + fringe only), and `cap` (builds `under`; the hat comes from `pieces`).
- **Shell:** the head ellipsoid offset by 0.03-0.05H + (volume-1)·0.35, cut by a hairline surface.
  - The front hairline is at head centre + 0.30H across ±55° of azimuth.
  - The sides are at the ear (bob, pixie) or above it (pulled back).
  - The back is at the nape. Pixie adds a nape point.
- **`short_bob`:** an ellipsoid mass from the crown to `length` (0 = ear, .5 = chin, 1 = shoulder), with a face opening cut out.
- **Fringe:** a front-wedge slab (it never covers the cheek in profile).
  - The bottom edge is at hairline - `fringe_length`·(hairline - eye top).
  - `side_swept` slants it by ±0.06H toward `part`.
- **Ponytail:** `tail_segments` tapered capsules (`tail_taper`) from `tail_pos`. Total length is `length`·1.25H. Bones are `tail.1..n`.
- **Buns:** `bun_count` spheres of `bun_radius` at the top back.

## Face (`face`)
- **Eyes** are an `oval_tall` glyph sized from the head's pixel height at each size: eye height = round(`eye_size` × head px × 1.15), width = 0.7 × height. The 4 corners are dropped when the eye is at least 3x4. The far eye in 3/4 view is 1 px narrower.
- `highlight` gives 1 `eye_hi` pixel on the screen-left side at ≥ 48 px.
- **Brows** (`brow_colour`; `soft_arch` drops the outer end 1 px) are drawn when the head is ≥ 12 px tall, and only on skin.
- **Placement and visibility:**
  - Eyes are placed at the 3D eye surface points (Blender anchors) and nudged ≤ 2 px horizontally so the ink lands on face skin.
  - Visibility is decided once per view for the whole cycle: facing plus a depth test, by majority over the 8 frames.

## Colour
- **Materials** are (colour, shade, hi) palette keys.
  - A missing `shade` key that a spec references is derived (base x 0.75 value) and logged in `model.json` `warnings`. Mechanic and runner reference `hair_shade` without defining it.
  - `shade: null` means flat. `shade_auto: true` derives `<colour>_auto`.
- The **locked palette per character** is: the spec palette + derived shades + `eye_hi` (#fbf8f2). Every pixel is one of these keys by construction, and colours per frame are gated against that count.

## Secondary motion (`secondary_motion`)
| type | lab implementation |
|---|---|
| `spring_chain` (ponytail) | `tail.k` bones: phase-lagged oscillators (vertical bounce at 2x the cycle, lateral sway at 1x), with amplitude growing toward the tip and clamped at 25°. `stiffness` scales the amplitude (soft 1.4 ... stiff 0.6). |
| `rigid_lag` (pack, tank) | own bone; follows the parent with a 1-frame delay + 0.012H bounce |
| `pendulum` (bag) | own bone pivoting above the piece: 9° forward/back + 5° side, lagged |
| `rigid_flare` (skirt) | skirt weights: hips + up to 42 % thigh near the hem (no extra bone) |
| `rigid_lag` on hair | none (hair is rigid with the head) |

Loopability comes from the construction: every oscillator is periodic over the 8-frame cycle.

## Tiers (`tiers`)
The piece lists are used exactly. The tier also sets mesh density and body detail:

| tier | voxels over height | tris | body |
|---|---|---|---|
| simple | 150 | 29k-170k | 1-ellipsoid head, no bust, softer torso blend (k .16) |
| medium | 200 | 53k-300k | jaw ellipsoid, small bust (not chibi) |
| detailed | 250 | 82k-470k | as medium, finer mesh |
