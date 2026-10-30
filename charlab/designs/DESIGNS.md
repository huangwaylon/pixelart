# charlab character designs, 2026-10-30

There are 8 female characters, all built from the shared part vocabulary in [VOCAB.md](VOCAB.md). Each one has a buildable spec in `<id>.json`, a concept image in `concepts/<id>.png` (front + 3/4 view, Gemini) and an alternate render in `concepts/<id>_1.png`.
Board: `concepts/board.png`, ordered by the ranking below. Small-size check: `concepts/smallsize_4x.png` shows the front concept area-downscaled to 32, 48 and 64 px with 12 colours. This is not real pixel art; it is only a rough guide to silhouette and colour-block read.

Every character uses the same face (eyes + brows only), the same shared outline colour #2b2235, 2 tones per material, hair as 1-2 closed masses, and at most 2 secondary parts.

## Feasibility ranking (best first)
| # | id | name | preset | palette | pieces simple/med/det | secondary | why |
|---|---|---|---|---|---|---|---|
| 1 | shorthair | Mika | compact | 11 | 3 / 5 / 8 | 0 | Fewest pieces of the cast. A dark pixie cap on a yellow block reads at 32 px, and nothing on her moves except the body. She is the best baseline for validating the lab: rig, outline and shading, with no confounds. |
| 2 | runner | Kai | slim | 10 | 3 / 5 / 8 | 1 ponytail | Minimal costume, 5 material colours, and one clean spring chain gives life without mush. She is the benchmark for the slim preset. Risk: skin-on-skin limb overlap, and limbs are 1 px at 32 px, so test her only at 64 px and up. |
| 3 | schoolgirl | Hana | compact | 12 | 6 / 8 / 10 | 2 (rigid skirt, bob lag) | The navy/white/red stacking is iconic and stays readable down to 32 px. The skirt is one rigid cone, which avoids the swordswoman's panels. The bob is a single helmet mass. The palette is at its 12-colour cap. |
| 4 | mechanic | Rio | compact | 11 | 5 / 8 / 11 | 1 ponytail | Strong blocks (blue overalls, yellow gloves, red bandana). The bottom-heavy sturdy build is a different body shape from the others. Dark hair on deep skin needs hair_hi plus the bandana to separate the head. The tool belt and pouches are clutter, so keep them to the detailed tier. |
| 5 | astronaut | Nova | chibi | 11 | 6 / 9 / 12 | 0 | The most distinctive silhouette (fishbowl helmet + pack) and the best chibi test. But the white suit washes out on light backgrounds and needs disciplined shade tones for interior lines. The face sits behind the visor, so it is small. |
| 6 | ranger | Fern | compact | 11 | 5 / 7 / 9 | 1 backpack bounce | The hat + big pack make a unique mushroom shape, and the earth palette is cohesive. But the low olive/khaki contrast blurs at 32 px, and the hat brim hides the eyes from a high camera. |
| 7 | courier | Zip | compact | 10 | 6 / 8 / 9 | 1 bag pendulum | The colour pop is great (pink + green + orange), but the crossbody strap and hip bag are asymmetric, so mirrored directions aren't free. The cap brim is also a protrusion to stabilise. That is roughly 1.6x the direction work. |
| 8 | diver | Marin | slim | 12 | 4 / 6 / 9 | 1 tank lag (optional) | The worst at small size: a thin dark figure that vanishes at 32-48 px, with the tank hidden in front view. Fins break walk cycles. She is good as a skin-tight posture stress test, but weakest as a playable sprite. |

Ranking criteria, in order of weight: silhouette clarity at 32-64 px, number of moving or secondary parts, colour count and value separation, symmetry (whether mirroring halves the direction work), and how much of the read survives with the simple tier alone.

## Recommendation for the lab
1. Build **Mika (simple tier, compact)** first, end to end: model, 8 directions, idle + walk. If she isn't clean, nothing else will be.
2. Then **Kai (slim)** and **Nova (chibi)** with the same pipeline, to compare the 3 body presets at 32/48/64/96 px. Then step Mika up to the medium and detailed tiers to find where detail stops paying off.
3. Hana and Rio are the most "game-heroine" designs once the pipeline is stable. Hold back Zip, Fern and Marin unless the owner picks them.

## Resolutions to try
chibi: 32 and 48 px · compact: 48 and 64 px · slim: 64 and 96 px (the per-spec list is in `body.test_sprite_heights_px`).
