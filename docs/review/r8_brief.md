# Brief r8 — cute / feminine / Japanese candidates (shared by all designers)

**User asks:** more Japanese-esque design (ドット絵 / JRPG handheld tradition), clean line-art and pixel edges,
CUTER and more FEMININE character, explore hair styles and hats (incl. no hat), must READ WELL FROM A DISTANCE,
expressive animation. Female, winter clothes, snowy mountains. Original character (inspiration only).

**Read first:** docs/research/japanese_dote_style.md (rules), docs/review/pixel/H1_AD_signoff.md (locked rules),
docs/review/r7_animation_jump_v2.md, pipeline/chargen.py (all outfit options + docstring), data/palettes/cw_*.json.

**Every candidate file** `data/variants/C<n>_<name>.json` must contain:
```json
{"extends": "H1v2_B_final", "name": "C1_...", "label": "C1 - short description",
 "palette": "cw_charcoal",
 "outfit": {"hair": "...", "hat": "...", "bangs": "...", "accessory": "...", "ahoge": false, "scarf": "long", "scarf_tails": 1},
 "face": {"eyes": "kawaii", "eye_pitch": -12},
 "render": {"ppu": 0.75, "lineart": {"smooth": 0.7, "line_min_run": 3, "pixel_perfect": true, "selout": true,
            "no_face_lines": true, "angel_ring": true, "regularize": true}},
 "anim_patch": {}}
```
* `"anim_patch": {}` resets H1's jump.json patch (the new animation `jump_v2` has its own frame names).
* Options: hair `bob|bob_long|long|twintails|side_pony|pony|buns|braids`; hat `none|beret|earmuffs|cat_beanie|hood|beanie|beanie_tall|beanie_slouch`;
  bangs `straight|side|points`; accessory `ribbon_side|ribbon_back|clip|null`; `ahoge`; `tail_len`; `hair_color` (`espresso|auburn|blueblack`);
  coat `parka|puffer|duffle` (+`coat_len`), legs `pants|skirt_tights`, boots `snow|tall`, `sleeve_cuffs`, `hem_trim`, `pom_size`, `hair_volume`.
* Proportions (cuter: bigger head, narrower shoulders, smaller hands/feet): `proportions.head_r, torso, leg, arm, shoulder_w, body_w, body_d, limb, hand_r, foot`.
* **Sculpt freely without code**: `"prim_overrides": {"<prim>": {"center": [..], "radii": [..], "rot": [..], "material": ".."}}`,
  `"chain_overrides": {"<chain>": {"seg_len": .., "widths": [..], "rest_dir": [..], ...}}`, `"remove": ["<name>"]`,
  `"add_prims": [{"name": "..", "bone": "head", "center": [..], "radii": [..], "material": "ribbon", "group": "hat"}]`.
  Prim/chain names: see `out/variants/<name>__jump_v2/inputs/character_generated.json` after a build.
* Colour tweaks: `"ramp_overrides": {"<material>": ["colour", ...]}` using master palette colour names (e.g. a pink ribbon accent).
  Materials: skin hair hat hatcuff pom coat coat_trim scarf mitten pants skirt boots boot_cuff ribbon.
* You may try `"render": {"ppu": 1.0}` + `"frame": {"size": [64, 64], "pivot": [32, 55]}` if the design genuinely needs more pixels — say so.

**Build & inspect (animation jump_v2):**
```
cd /Users/waylonhuang/Documents/other/pixelart
.venv/bin/python -m pipeline.build --variant C1_xxx --anim jump_v2 --no-reference
# out/variants/C1_xxx__jump_v2/preview/jump_v2_contact_sheet.png  (crop with Pillow; wide)
# out/variants/C1_xxx__jump_v2/preview/distance_test.png          (1x/2x on snow & dark, silhouette, squint)
.venv/bin/python -m pipeline.pixelreview --build out/variants/C1_xxx__jump_v2 --dirs S SE E N --frames 1,7,13 --zoom 10
```
**Quality bar (scrutinise pixel by pixel):** clean curves (no 1-3-1 jaggies), readable face with big low eyes,
hair is the main silhouette and reads in the black-silhouette row at 1x, 3-4 clear value masses in the squint row,
hat smaller than the hair mass, nothing noisy, cute + feminine, consistent across 8 directions, QA passes.
Iterate >= 4 builds per candidate. Never edit pipeline/*.py, data/palettes/*, or other designers' C files.
EOF
echo ok