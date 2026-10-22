# r12 - HD reference model for S4 (M1 hair + bow, M2 coat + scarf, M3 limbs)

S4 (old, ellipsoids) vs **S4_hd** (new, SDF parts). The design is unchanged: one tapered ponytail under the big back bow, with hime bangs.

## What to look at
1. **Close-ups:**
   - **[head_closeup_old_vs_new.png](head_closeup_old_vs_new.png)**:
     - Crown clumps, 7-point hime bangs and flat-cut side locks.
     - The back curtain, now 5 simulated chains x 2 sharp clumps.
     - A 5-clump twisted ponytail ending in 3 points.
     - Bow with open loops, a grooved knot and V-cut tails.
   - **[body_closeup_old_vs_new.png](body_closeup_old_vs_new.png)**:
     - Coat: bodice blended into an A-line skirt with 10 box pleats, a scalloped hem band and pocket flaps.
     - Belt band with a teal buckle, plus a placket and buttons.
     - Scarf: knit tori, a knot, and a flat tail with fringe.
     - Arms: sleeves blended at the elbow, with cuffs.
     - Mittens: palm box and an angled thumb.
     - Tights, and boots with a fold cuff, toe box, sole and heel.
2. **Turnarounds**: [S4_turnaround_3d.png](S4_turnaround_3d.png) vs [S4_hd_turnaround_3d.png](S4_hd_turnaround_3d.png).
3. **3D model**: [model_rest.stl](model_rest.stl), [model_idle.stl](model_idle.stl) and [model_apex.stl](model_apex.stl) (jump apex). GitHub shows them in 3D: drag to rotate. [model_rest.obj](model_rest.obj) with its `.mtl` carries the palette colours.
4. **Sprites, old (left) vs new (right)**: [run](boards/run.gif), [walk](boards/walk.gif), [jump_sc](boards/jump_sc.gif), [idle](boards/idle.gif), [throw](boards/throw.gif), [carry_walk](boards/carry_walk.gif).
   - Each board also has `_slow.gif` and `_keys.png` versions.
   - The boards show the body sheet only. Props (crate, snowball) are separate layers, but they are **not** identical
     to v1: the per-pixel front/back split is re-derived from the HD body's depth (`throw_sheet.json` layer tags differ
     at f0 E/W and f1 E; all 5 prop clips move pixels between `prop_front` and `prop_back`, total prop pixels unchanged).
     **The HD body sheet, its `_sheet.json` and its prop strips ship together as one set - never pair HD bodies with
     v1 prop strips.**
   - The jump_sc 8-dir GIFs and contact sheets are in this folder too.
   - At 48x64 the new detail mostly shows as cleaner silhouettes: the bang zigzag, pleated/scalloped hem, boot soles and heels, and the bow.
   - Sub-pixel parts appear only in the hi-res refs and the STLs: seams, buttons, grooves, knit ribs and fringe.

## Status
- All 13 action clips build on S4_hd with QA PASS: idle, walk, run, jump_sc, fall, land, climb, climb_top, pick_up, carry_idle, carry_walk, throw, carry_throw.
- Compared with legacy S4: 0 chain penetrations, equal or lower height deltas, identical hand/carry anchors and total
  prop pixels (prop front/back split re-derived, see above).
- Legacy variants are byte-identical to a fresh build of HEAD (S4_halfup_bow idle, throw, carry_walk, walk `_sheet.png`
  cmp'd). Note: `data/faces/kawaii_v2.json` three_quarter now has a 2-px nose bridge (coordinator change), so legacy
  SE/SW/NE/NW face pixels intentionally differ from `releases/S4_actions_v1`.

## Round 2 fixes (r12 reviews AD / anim / GD)
Each `fixes/*.png` shows v1 legacy | r12 HD before | round 2 after, 5-8x nearest. Metrics: all 13 clips, before -> after
(legacy in brackets).

| # | Fix | Change | Evidence |
|---|---|---|---|
| 1 | E/W profile eye | front side lock z 2.8 -> 0.6 | [fix01](fixes/fix01_profile_eye.png); E+W glint frames 42 -> 104 (98) |
| 2 | 2-px rust hem | hem band w 0.75 -> 1.15, scallops refs-only | [fix02](fixes/fix02_hem_band.png); rust px idle 342 -> 1792 (1176) |
| 3 | bang arc | hair cap + hair_back vote with the clumps (no seam blur), ring_w 0.14 | [fix03](fixes/fix03_bang_arc.png) |
| 4 | mitten wins | slimmer cuff set back (r .35, w .68) | [fix04](fixes/fix04_mittens.png) |
| 5 | bow loops | rounded petal loops (`torus.round`), sel-out line kept on loop edges | [fix05](fixes/fix05_bow_loops.png) |
| 6 | NE waist strobe | belt clipped behind the hips | [fix06](fixes/fix06_waist_flicker.png); NE hair flicker 42 -> 13 (24) |
| 7 | idle crown flicker | idle/carry_idle 1-frame hold in the crown rows | [fix07](fixes/fix07_crown_flicker.png); S 74 -> 18 (13), N 51 -> 23 (45) |
| 8 | bow vs raised mitten | teal_0 line where ribbon touches mitten | [fix08](fixes/fix08_raised_mittens.png) |
| 9 | throw release arm | follows from fix 4 (cuff no longer reads as hair) | [fix09](fixes/fix09_throw_release.png) |
| 10 | soles <= 58 | flat sole clip + toe/heel spring in ankle space | [fix10](fixes/fix10_soles.png); y=59 rows walk 4 -> 0, carry_walk 2 -> 0 |
| 11 | run height | crown clumps 0.12 closer to the cap + heel spring | [fix11](fixes/fix11_run_height.png); run 33-35 -> 33-34 |
| 12 | README | prop-layer claim corrected (above) | - |

QA PASS on all 13 clips, 0 warnings, `--verify` deterministic. Rust is now ~1.5x legacy (hem top row is fully rust;
legacy rusts only the hem ends) - say if you want it toned back.

## User requests r13
Images in [r13/](r13/).
- **A. Face shape**: the head sphere is replaced by a cranium + narrower jaw + soft pointed chin + cheekbone pads
  (smooth-blended). [r13_head_bow_closeup.png](r13/r13_head_bow_closeup.png) (top: before, bottom: after). In sprites
  the chin shows above the scarf in S and the jaw turns away in SE/SW ([r13_face_sprites.png](r13/r13_face_sprites.png)).
- **B. Modelled eyes**: dark eye lenses on the head (refs / STL only, `lod: ref`). The sprite face pass
  (`render.face_eyes`, opt-in) places each eye cel block at its own projected eye position. Spacing rules: a >= 2 px
  bridge and >= 1 px of skin to the far cheek. Profile views keep the nose-pinned cel.
- **C. Bow**: puffy thick loops (band r 0.5, depth 1.55) with unequal soft folds (refs), a pinched knot and V-cut tails.
  Each loop rides a spring chain (`follow`), so it bounces on run, jump and land and lags on turns
  ([r13_bow_bounce_jump.png](r13/r13_bow_bounce_jump.png)). The loops count as secondary motion for the height QA, like
  the pom. S view: 2-3 px rounded ears, no 1-px antennae.
- **D. Hair sway**: curtain + ponytail get a gait-driven lateral force, in phase with the torso lean (counter to the
  hips). The verlet sim adds the lag. Ponytail tip sway: walk +/-1.8 px, run +/-2.1 px (legacy +/-0.2). 0 penetrations.
  [r13_walk_sway.png](r13/r13_walk_sway.png), [r13_run_sway.png](r13/r13_run_sway.png).
- **E. Hand fixes** (data overrides, `overrides/variants/S4_hd/`, each with a reason):
  `jump_sc/E/10` and `land/E/01` change 1 px: a skin_0 sliver between the side lock and the landing squint eye becomes
  hair. Nothing else needed hand work.
