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
     to v1: the per-pixel front/back split is re-derived from the HD body's depth (round 3: `throw_sheet.json` layer
     tags differ from v1 only at frame 0 W, back -> split; prop clips move some pixels between `prop_front` and
     `prop_back`, total prop pixels unchanged).
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
- **E. Hand fixes** (data overrides, `overrides/variants/S4_hd/`, each with a reason): round 3 retired the jump_sc /
  land 1-px fixes (the final orphan pass now handles them); `carry_idle/NW/00` (4 px) hides a temple-skin sliver.

## Round 3 fixes (re-reviews: GD approved; AD + animation director)
Crops in `fixes/r3_*.png` (v1 legacy | round 2 | round 3). Legacy `_sheet.png` byte-identical to a fresh HEAD build
(idle, throw, carry_walk, walk). 13/13 QA PASS, 0 warnings, <= 16 colours per frame.

| # | Fix | Change | Evidence |
|---|---|---|---|
| 1 | Bow volume | `render.bow_shine`: 2 px teal_2 highlight on each loop's outer top + 1 teal_0 fold at the knot end (skipped only in a frame already at 16 colours) | [r3_01](fixes/r3_01_bow_highlight.png); #6ACBB6 px idle 0 -> 160 |
| 2 | S ears | loops raised + tilted (y 11.8, 26 deg, taper .35, length 3.4); hair line runs kept after despeckle | [r3_02](fixes/r3_02_s_ears.png): 4 x 2 px, mirrored |
| 3 | Jump crouch ears | `follow.max_drop` world-up clamp | [r3_03](fixes/r3_03_jump_ears.png); S f1 ears (2,2) legacy / (0,0) / (8,8) |
| 4 | Idle blips | bow springs off in idle/carry_idle; `temporal_hold` covers the scarf tail | [r3_04](fixes/r3_04_idle_blips.png); teal blips S 36/51/8, SE 22/41/7, W 29/47/18 |
| 5 | Walk sway | walk force x1.15 with a flattened (held) extreme | [r3_05](fixes/r3_05_walk_sway.png); tip +/-2.0-2.2 px, f2-3 / f6-7 held; run unchanged; walk NE f7->f0 diff 164 -> 154 px (legacy 124: the larger sway itself; the chain loop seam is 0.04 px) |
| 6 | NW skin | cranium pulled in (no temple poke) + 1 override | [r3_06](fixes/r3_06_nw_skin.png); 0 skin_0 px in carry_idle f0 / throw f4 / climb |
| 7 | Head rust | `lineart.ring_trim`: 2 px inside the outline, 1 px clear of the bow, runs < 3 dropped | [r3_07](fixes/r3_07_head_rust.png); idle head rust 603 / 886 / 549, hem unchanged |
| 8 | S bridge | `face_eyes.gap_front` 3 | [r3_08](fixes/r3_08_eye_gap.png); 3 px in every S frame |
| 9 | 3/4 face | mouth 1 px toward the bridge; `skin_edge_dark` (dark face outline both cheeks); SE stub gone | [r3_09](fixes/r3_09_face_34.png) |
| 10 | Back ponytail (Anim5) | ponytail is its own group -> plum depth line against the curtain | [r3_10](fixes/r3_10_pony.png) |

Not done in round 3: throw E bow colour mix and climb NW strays (deferred to v1.1). Release:
[`releases/S4_hd_actions_v1/`](../../releases/S4_hd_actions_v1/README.md).

## Round 4 (AD blocker)
- **Ponytail tip (E/W/SE/SW):** the sweep now ends in one tapered point instead of three sub-pixel points. The clumps converge, and the tip runs 4.5 units past the chain end, like the legacy end bead. It now reaches the legacy length and tapers in 2-3 steps to a 1-px point in every frame. Tip row vs v1, across E/W/SE/SW in 11 clips: mean -3.2 px (round 3) -> -0.7 px (round 4).
  [r4_01_ponytail_tip.png](fixes/r4_01_ponytail_tip.png)
- **SE rust arc:** 1-2 px clump-line breaks inside the arc are closed (`ring_trim.fill_gaps`), so (23,27) is no longer a gap.
  [r4_02_se_arc.png](fixes/r4_02_se_arc.png)
- **No other changes:**
  - 13/13 QA PASS, 0 warnings.
  - Heights, penetrations (0), colours (<= 16), and idle/walk flicker match round 3.
  - Legacy `_sheet.png` is byte-identical to a fresh HEAD build.
  - `releases/S4_hd_actions_v1` is rebuilt.
- **Deferred to v1.1:** throw E bow colour mix and climb NW f0 strays.
