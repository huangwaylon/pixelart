# Brief r9 — semi-chibi, feminine, curvy, long hair, interesting silhouette (teal)

**User direction (latest):** semi-chibi proportions; more feminine and curvy; longer hair; an interesting silhouette;
likes the **teal-blue colour scheme** of O6 (palette `cw_oatmeal`: oatmeal coat, teal hat/scarf/mittens, brown trim).
Also: **design consistency across the 8 angles** (e.g. scarf direction/angle/side must match) and **nothing may
penetrate the body** (scarf, hair) during the jump. Japanese ドット絵 line-art quality (docs/research/japanese_dote_style.md)
and readability from a distance still apply. Original character.

**Start from** `data/variants/S0_semichibi_base.json` (read it): every candidate file `data/variants/S<n>_<name>.json` has
`"extends": "S0_semichibi_base"` + only what changes. S0 already has: semi-chibi proportions (~3.4 heads), curvy A-line coat
(`coat: aline` + `proportions.waist/hip/flare/bust`), long hair (`hair_len` 1.0 = shoulder blades, 2.0 = waist),
scarf_v2 (knot, swing limit, consistent side), `sim.body_collide` (chains collide with the real body + floor; QA counts
`chain_penetrations` and fails on any), kawaii eyes, line-art passes, 48x64 cell.

**Options** (pipeline/chargen.py): hair `long|twintails|side_pony|pony|buns|braids|bob|bob_long` (+`hair_len`, `tail_len`, `hair_volume`,
`hair_color` espresso|auburn|blueblack); hat `none|beret|earmuffs|cat_beanie|hood|beanie*`; bangs `straight|side|points`;
accessory `ribbon_side|ribbon_back|clip|null`; `ahoge`; coat `aline|parka|puffer|duffle` (+`coat_len`, `hem_trim`, `sleeve_cuffs`);
legs `skirt_tights|pants`; boots `tall|snow`; scarf `long|chunky|none`, `scarf_len`, `scarf_v2`.
Sculpt via `prim_overrides`, `chain_overrides`, `remove`, `add_prims`; colours via `ramp_overrides` (master palette names)
and `material_bands` (per-material shading thresholds). Prim/chain names: `out/variants/<name>__jump_v2/inputs/character_generated.json`.
Teal family only: you may shift accents within the master palette (teal_0/1/2, oat, mauve, hair tones, a small red/gold accent ok).

**Build & inspect:**
```
cd /Users/waylonhuang/Documents/other/pixelart
.venv/bin/python -m pipeline.build --variant S1_xxx --anim jump_v2 --no-reference
# out/variants/S1_xxx__jump_v2/preview/{jump_v2_contact_sheet.png, distance_test.png}, qa_report.md
.venv/bin/python -m pipeline.pixelreview --build out/variants/S1_xxx__jump_v2 --dirs S SE E N --frames 1,7,14 --zoom 8
```
(The animator is making a semi-chibi-tuned animation `jump_sc`; when `data/animations/jump_sc.json` exists, also check your design with `--anim jump_sc`.)

**Quality bar:** feminine, curvy hourglass read; long hair as a distinctive silhouette element in all 8 directions
(black-silhouette row of distance_test); clean curves; 3-4 value masses; accessories on a consistent side; scarf never
through the body; QA PASS with `chain_penetrations` 0. Iterate >= 4 builds each. Never edit pipeline/*.py,
data/palettes/*, S0, or other designers' files.
