# r12 Illustrator A: S4 model sheet and bust (canonical)

Files: `data/illustrations/S4/model_sheet.json` (front/three_quarter/back panels), `bust.json`, cels in `S4/face/`, palette `cw_oatmeal_portrait` (32 + portrait_ext 6). Rebuild: `python -m pipeline.illustrate <json> --out 00_REVIEW/r12_illustration`.

Tool additions: centre-sampled raster, `paths[]`, `mirror`, `translate`, `z`, `clip`, auto-clipped `*_shade`/`*_hi`, `line: "auto"`, `panels`, anchored face cels (`:flip`), overrides, QA stats.

## Model-sheet rules (match within 1 px)
- **Proportions (front, px):** hair top y10, chin y44 (head 34 px), soles y153: ~4.2 heads. Shoulders y50, belt y70-74, hem y96-102, boot cuff y116-120.
- **Head:** face 25 px wide. Eyes 8x9, rows 28-36, 4 px apart. Mouth 2 px at y41. Hime bangs make 4 tapered clumps: tips at y≈27.6, notches at y≈23.5. Sidelocks 5 px wide, end y≈43 in two points. Angel ring: arc, zig-zag lower edge.
- **Bow:** two loops angled up and out, spanning x21-75 and y5-21. Each has a teal_0 loop hole and lower band. Knot at the crown back, two V-cut tails.
- **Ponytail:** ONE,, tapered to a point at y≈85. Loose hair ends at y≈80 in three clumps per side.
- **3/4 = front turned:** same landmark heights. Far eye is 6 wide, near eye 8. Scarf knot and tail on the left silhouette edge, buckle shifts left, toes point left.
- **Bust = 3/4 head x1.32** (head 45 px, 47% of the height). Eyes 7x12 (far) and 10x12 (near).
- **Colours:** hair hair_2/hair_1/plum_0 line, ring hair_hi. Skin skin_2/skin_1/line_skin. Coat oat_2/oat_1/mauve. Trim hair_2. Teal parts teal_1/teal_0/teal_2. Tights char_1/ink. Boots hair_1/plum_0/hair_2. Eyes ink lash, iris_0..2, snow_3. Blush red_2 hatched ///.
- **Lines:** front part owns the 1 px inner line. Silhouette sel-out: lit top-left takes the part line colour, the rest outline. No outline colour inside.
- **Bust slots** (L = viewer-left/far): brow_L/R (over bangs), eye_L/R, nose, mouth, blush_L/R, sweat, fx. Swap via `variants.<v>.cels`.
