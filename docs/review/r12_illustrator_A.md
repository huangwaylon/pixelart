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

## Round 1 fixes (AD review 1)
1. **Sel-out zipper fixed** (`illustrate.py` `selout()`). Each outline pixel now takes the outward normal of its edge segment, measured over a 5x5 window. A majority vote along the line then decides whole runs, so pixels no longer flip one by one. Light comes from the upper-left (`outline.light`, `lit_threshold`). After it, a new `orphan_cleanup` pass runs. Cels are stamped later and are never cleaned. Orphans: sheet 49 to 2, turnaround 3, idle and cheer poses 0-1. The bust's remaining 5-12 per expression come from B's cels: lone `W` pixels in the eyes, plum/skin_1 brow ends, the sad tear.
2. **3/4 face turned.** Far eye 6 px, near eye 8 px, features 2 px toward the facing side. The far sidelock now sits *behind* the face, so the cheek contour shows, with a 1 px nose bump at y38-41. The jaw tapers to a chin under the far eye (x≈41). Propagated to `bust.json` (layers only; B's variants and cels are kept).
   **Anchor changes:** sheet 3/4 eye_L 37→36, eye_R 46→44, mouth 42→39, nose removed. Bust: brow_L 32→30, brow_R 43→40, eye_L 32→30, eye_R 43→40, nose 39→36, mouth 38→35, blush_L 30→28, blush_R 46→43. y unchanged.
3. **Coat line**: the new `oat_0` #957A80 (warm mauve, darker than oat_1) replaces lavender `mauve` on the coat, arms and boot cuffs. The portrait palette now has 39 colours.
4. **Brows canonical**: 2-row ink arcs on the bangs at y22, above the notch tips. Cels `browF_neutral`, `browQ_near/far_neutral`.
5. **New `turnaround.json`**: 5 views (front, 3/4, profile, rear 3/4, back), 96x64 each, model-sheet scale. The front, 3/4 and back views reuse the model-sheet shapes.
6. **New `bust_16.json`**: 15 colours plus transparency, built with `extends` + `color_map`. The iris uses the teal ramp, lashes use outline.

## Round 2 fixes (AD review 2)
1. **Turnaround rear-3/4 cheek** (`turnaround.json`, panel `rear_three_quarter`).
   - The sidelock now has `line_color: plum_0`. The ink column at x321 y28-42 was the sidelock's auto line falling back to `outline`. It is now hair line, so the cheek tucks under the hair instead of being walled off.
   - The face path's lower edge now ends at a chin point (≈x320 y43), behind the sidelock. The cheek tapers 2 px at y41 to 1 px at y42.
   - A new `sidelock_under` layer (hair_1, plum auto line) fills the gap between the sidelock tips. The skin leak at (323,42) and (323-324,43) is gone.
   - Before/after: `00_REVIEW/r12_illustration/fixes/r2_A_turnaround_cheek.png`. Turnaround: 20 colours, 3 orphans.
2. **Optional, sheet front mouth: done.** Mouth anchor moved 41 to 40.
   - The nose then touched the mouth vertically, so the nose moved up one row (38 to 37). The lower face now spaces out as nose y37-38, gap, mouth y40, two skin rows, chin line.
   - Applied to both the model_sheet and turnaround front panels, which share these shapes. The 3/4 and profile views are unchanged.
   - **Updated rule:** front mouth 2 px at y40, nose at y37. Model sheet: 23 colours, 2 orphans.
