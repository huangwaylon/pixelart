# Locked decisions (v1) — synthesized from kickoff memos in docs/kickoff/

| Area | Decision | Owner |
|---|---|---|
| Camera | Orthographic 2:1 dimetric, elevation 26.565°, 8 facings S,SE,E,NE,N,NW,W,SW rendered (never mirrored) | GD / SE |
| Frame | 64x64, pivot (32,56) = ground point under character root. Frames drawn **in place**; vertical jump is engine-driven via per-frame `z_px` | GD |
| Size | ~41 px standing, <=46 px at max stretch, integer scaling only (3x phone / 4x tablet) | GD |
| Timing | 12 frames, 840 ms. Airborne at 130 ms. Frames 10-12 cancelable. Events: `takeoff` f3, `land` f9 | GD + 3D (compromise) |
| Palette | AD palette, 32 colours, hue-shifted ramps (data/palette.json). Zero off-palette pixels | AD |
| Light | Screen-fixed key light upper-left (camera space) so all facings shade identically | AD |
| Lines | 1px outer outline #241628; inner lines only at depth breaks between parts, in the front part's darkest tone; none inside face | AD |
| Face | 2D pixel decals anchored to 3D head points (crisp + consistent). Expressions: neutral, determined, joyful, squint, smile | AD |
| Model | Ellipsoid primitives on a skeleton (data/character.json); planted feet solved with 2-bone IK (0px slide) | 3D |
| Secondary | Deterministic verlet sim (fixed dt 5 ms) for scarf tails, braids, pom-pom, simulated once in character space -> identical across facings | 3D / SE |
| Shadow & FX | Separate strips (engine composites): ground shadow (shrinks with z), snow-puff FX on takeoff/land. Baked into previews only | GD |
| Overrides | Sparse JSON per (anim, dir, frame), palette indices, -1 = erase, records base hash -> "stale" flag if base changed | SE |
| Builds | builds/<anim>_<hash12>/ with manifest (input hashes) — same inputs => byte-identical outputs | SE |

## Round 3-5 updates (exploration phase)
| Area | Decision | Owner |
|---|---|---|
| Camera | Character camera 16° (12-18° research range); world stays 2:1 | AD+GD+3D |
| Style | Early-Pokémon (GBA/DS) overworld humans: 2-3 tones/material, 2x3 eyes w/ catchlight, no orphans (QA = 0) | AD + research |
| Palette | One 32-colour master (frost_r3) + 6 colourways (data/palettes/cw_*.json); per-material shading bands | AD |
| Architecture | 3D model = maintained reference mannequin (chargen + rig + sim); guide.json + 3D-vs-pixel grounding sheet per build; hand-drawn part library planned (heads first) | 3D+SE |
| QA height gate | Body-only silhouette (excl. pom/scarf/hair chains), limit **3 px** (was 2): crouch head-tilt perspective legitimately varies 3 px between S and N | Lead (GD to confirm) |
| Hero candidates | H1 = B body + O1 charcoal @ R2 (48x48); H2 = A body + O1 charcoal @ R2 | Panel r5 |

## Round 6 — hero spec (supersedes the v1 frame/size rows above)
| Area | Decision | Owner |
|---|---|---|
| Frame | **48x48**, pivot **(24,41)**, character ~29 px standing (B body), drawn in place | GD r5/r6 |
| Jump | apex **z = 15 px** (20 world units × ppu 0.75), 770 ms, lock 590 ms, cancel f10-f12 | GD r6 |
| Shadow | 15x5 px ellipse, shrinks to 65% at apex | GD r6 |
| QA | body height gate 3 px (GD confirmed r6); `--release` builds fail on stale/unreviewed overrides | GD r6 |
| Style rules | AD locked rules 1-8 (docs/review/pixel/H1_AD_signoff.md) are the standard; generator v2 encodes them | AD |
| Hero base | v2 procedural generator + minimal reviewed overrides (570 → 254 → 170 → 88 hand px) | AD r3/r4 |
| Engine draw order | shadow → fxBack → character (offset −z_px) → fxFront; cull on 48x63 | GD r6 |
