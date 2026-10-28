# Skinned rig + dynamic motion (swordswoman), 2026-10-28

Coordination contract: `CONTRACT.md`. This experiment has two roles: R (rigger: `rig/`, `render/`) and M (animator: `motion/`). Each writes their own section here.

## R: rigger

**Goal.** Replace the rigid-parts rig H2 with one connected, deformable mesh. H2 had separate meshes rotating about pivots, so joints gapped or intersected and nothing deformed. Also fix the design errors listed in earlier reviews:
- T-pose sleeves
- thin obi
- short bell skirt with a bare-thigh band
- waist cinch

### Method (all scripts are in this folder; nothing outside it was modified)

**`rig/build_mesh.py`** (Blender 5.2, `-b --factory-startup`) builds one watertight body in the H2 frame.
- Head, hair, face and bun come from rig H2 `parts/head.glb` and `bun.glb`. These are calibrated to the m96 masters. The bun was moved to the back-top.
- Everything else is procedural lofts fitted to the m96 masters `EC0_{S,E,SE}_96`:
  - torso with no cinch
  - wide lavender obi band, 5 rows tall as in the master
  - straight A-line skirt down to the master hem row
  - kimono bell sleeves, arms down at 26°. The inner edge stays clear of the obi so the voxel union does not fuse them.
  - mitten hands at 1.3× H2 scale
  - legs with a thin bare-thigh band, a red stocking top band and black thigh-highs
  - boots
  - front side locks hanging to the shoulders
  - new bow: knot plus two lobes at the back-top, with two ribbon tails down the back hair
- The fit loop used `qa_view.py`, `qa_rows.py`, `qa_col.py` and `qa_zoom.py`: render the matids through the game cameras, then compare the band rows and columns with the masters.
  - Result: the H2 head and obi rows matched the masters absolutely, but the legs were about 3 rows short. So the legs were lengthened and the upper body raised by 0.044 units.
  - The pixel chain aligns the soles to the master bottom row, as hires3d did: SE dx 2/dy 1, E 4/2, S 0/3.
- All parts are unioned by a **voxel remesh (0.006 units)**: one shell, about 118k vertices.
- Per-face material and per-vertex source part come from the nearest part surface (BVH). The H2 hair, skin and eye labels are cleaned with a 3-pass majority filter in `build_rig.py`.

**`rig/build_rig.py`** converts to the contract frame and builds the armature.
- Contract frame: metres (1 H2 unit = 0.775 m), +Y = front, her left = -X, soles at z = 0.
- Armature: 63 bones. All contract names are present, plus deform `shoulder.L/R`. `obi_tail` is omitted because the design has a plain obi.
- **Weights are part-aware and analytic, not heat.** Heat weighting on a fused voxel mesh bleeds across parts: hair into the shoulders, thighs into the skirt. The weights are built like this:
  - **Partition of unity per body part.** Each part is weighted with joint-plane slabs, using smooth bands at the joints:
    - hip 5 cm, knee 4 cm, ankle 3 cm
    - shoulder 5 cm, elbow 5 cm, wrist 2 cm
    - spine 3.5/6 cm, neck 2.5–3 cm
  - **Skirt.** Pelvis at the waist, then 8 azimuth panel chains (cos(2Δ)^4 windows, so the panels are near-rigid with narrow seams) in 2 vertical bands. The hem ring within about 12 cm of each thigh axis is blended to that thigh, which keeps the leg exits closed.
  - **Sleeves.** The arm chain drives the core. The bell bag (more than 4.5–7.5 cm from the forearm axis, past the elbow) goes to `sleeve.*.1`/`.2`.
  - **Hair.** Angular and height windows: bangs L/C/R, bob sides to `hair_side.*.1-2`, bob back to `hair_back.1-3`. The locks have their own 3-bone chains. The bow lobes go to `bow.*.1-2`. The ribbons ride on `bow_knot` → `hair_back.2-3`.
  - **Hair fade.** All hair-chain weight fades to 0 within 10 mesh edges of skin (a BFS distance). The H2 bangs are painted onto the head surface, so without this a bang swing tears the forehead. Bangs are capped at 0.6.
  - **Smoothing.** 6 Laplacian smoothing passes over the mesh graph heal the label seams. Torso, obi and skirt never take arm weight. Weights are trimmed to the top 4 influences.
- Armature modifier with **Preserve Volume (dual quaternion)**.
- Outputs:
  - `rig/rig.blend`
  - `rig/rest_skeleton.json`: head/tail/roll/parent plus a 3×3 `matrix` whose columns are the local axes. Local Z points front (up for foot/toe/bow, outward for skirt).
  - Colour attributes: `Color` (the hires3d matid colours, so `hx.py` works unchanged) and `PV` (palette base colours for the preview).

**`render/render_motion.py`** implements the contract CLI.
```
<blender> -b rig/rig.blend -P render/render_motion.py -- motion/<act>.json <view> <outdir> [--preview] [--stamp] [--frames=a:b] [--yaw=deg] [--no-post]
```
- It applies the motion: `root.loc` as an absolute world position of the root bone, per-bone `rotation_quaternion`, and optional pose scale.
- Game camera, the same as H2, g96 and hires3d:
  - 30° elevation, orthographic, 192 cell with pivot (96, 152)
  - in-game 128 cell = crop 32..160
  - 52.608 px per H2 unit = 67.9 px per metre at 1×
  - sun from the screen-left/above/camera side
- `--preview`: EEVEE smooth shade at 2× (env `PVS`), output as GIF plus a sheet.
- Full mode: 8× passes `guide` (matid, AA off), `lum` (16-bit) and `dep` (16-bit) feed **`render/pixel_chain.py`**, which runs on the pixtools venv and reuses `hires3d/scripts/hx.py`:
  - cel shading from the locked palette ramps, plus hi-res outline at depth threshold 0.025
  - E2 k-centroid (k = 3)
  - rig-material palette lock
  - fix: outline_sil, orphans, bare-K crumbs, largest component
  - optional m96 neutral head stamp at the rig head offset
  - outputs: `_px/` and `_px_hs/` grids, `_4x.gif` and `_hs_4x.gif` on mid-grey, sheets, and `_px.json` (align + band churn)
- Speed: about 0.5 s per frame for the 3 passes plus about 1 s for the pixel chain.

**Other scripts.**
- `render/render_all.sh`: batch renders every `motion/*.json` × SE/E/S.
- `render/compare_h2.py`: H2 vs skinned comparison GIFs.
- `render/make_test_wave.py`: arm-wave plus head-turn pipeline test (`render/test_wave.json`).
- `rig/make_stress.py`: QA poses (`rig/qa/stress.json`).

### QA
- `rig/qa/stress_SE_final.png`: stress poses from SE at 6× smooth (top) and through the pixel chain at 4× (bottom).
  - Poses: rest, deep knee bend, stride, arm raise 120°, elbow 120°, twist 30° plus head turn 40° (70° total at the head), hair chains 40°, bun/bow/sleeves 40°, skirt panels 40°, stride plus skirt.
  - Iterations (sheets `st5*`):
    1. A hair tear when the bangs swung, fixed by the skin-distance fade.
    2. Obi colour smeared into the armpit on the arm raise. Cause: the sleeve and obi fused in the voxel union. Fixed by widening the gap and blocking arm weight on the torso.
    3. Hands pixelized into detached 1–2 px blobs, fixed by making them 1.3× larger.
- `rig/qa/rest_vs_master.png`: master | rig head | rig + stamp, for S and SE.
- Comparisons with the old rig: `render/out/compare_{walk,run,idle}_SE.gif` and `compare_walk_E.gif` (old H2 celo_kc_hs | skinned + stamp | skinned rig head | preview).
- Band churn (raw celo kc, SE, final rig and motion files): walk .187, run .184, idle .120, jump .219. The `_hs` (head-stamp) versions are .33/.38/.23/.36.
  - hires3d H2 for comparison: walk celo_kc .173, `_hs` .365; idle .084.
  - The churn is similar to H2. The skinned rig doesn't add boiling. The large-amplitude motion is M's.

### Critiques (`crit/`)
**`opus_rig.txt`**, round 1, on the first weights:
- connectivity 7, deformation 5, secondaries 4, body design 7
- new vs old about 6.5 vs 4
- Problems it named:
  - bang tear (fixed)
  - armpit pinch on the arm raise (fixed)
  - skirt panels bagging (sharper panels now; still faceted at 40°)
  - knee bend collapsing into a cape
  - back-thigh volume loss in the stride
  - a flat cuff disc
  - bow lobes splaying into horns beyond about 25° (limit passed to M)

**`opus_final.txt`**:
- Scores, old H2 vs new: connectivity 3 vs 8, deformation 3 vs 6, secondary attachment 4 vs 5.
- Verdict: **"promising, a clear improvement"**. The parts are connected and joints bend believably at walk and run angles.
- Remaining items it named:
  - in SE the side lock reads like a beak in front of the face
  - hands were small (fixed after this round)
  - deep knee bend still collapses
  - the cuff disc and the chest lump at elbow 120°
  - a skirt seam crease at 40°
  - the bow and bun drift on a 70° head turn
  - too little skirt and sleeve lag in the current motion; that is M's side

### r4 follow-up (mirror fix, 13:45)
- The sleeve and hair_side bones were 75–129 and 14 mm off mirror symmetry.
  - Sleeves: `ring_pts`/`B2` used cross(t, lat), which flips per side. It now uses `bdir` = back.
  - hair_side: the H2 head mesh is asymmetric.
  - Fix: every .L/.R bone pair is averaged with its mirror, and the lock x is averaged. Mirror error is now 0. The sleeve bag hangs back on both sides.
- Legs are thicker: knee r .050→.057, calf .051→.059, ankle .036→.044, boots +12%. The thigh centres moved to ±.092 at the hem to keep the gap.
- Hands are about 1.35× thicker, a 3×3 px blob at 1×.
- SE yaw sweep against EC0_SE_96 (`rig/qa/yaw_SE_sweep.png`):

| yaw | 0 | −10 | −15 | −20 | −25 |
|---|---|---|---|---|---|
| silhouette IoU | .850 | .863 | .861 | .848 | .830 |

  −15 is now the SE default; `--yaw=0` gives the true camera.
- Re-baked M's actions (`mbuild.py --noprev`) and ran `final.sh`. `render/ab_board.py` rebuilds the A/B boards.
- pxeval walk SE, before → after:

| flicker | boil | rigid_share | sil_change | motion_px | head_jerk |
|---|---|---|---|---|---|
| .292 → .262 | .058 → .056 | .434 → .355 | .292 → .264 | 1.16 → .97 | 3.7 → 4.5 |

  The flags are unchanged.

### Round 2 (R): animatable master-look head, fuller legs, limb IDs (rig r5, 18:20)

**Head.**
- `rig/head_hull.py` (pixtools) builds a **visual hull** from the m96 head stamps.
  - Views: S, SE, E, NE and N, plus SW, W and NW mirrored from SE, E and NE.
  - It goes through the exact game camera (rig H2 frame, PPU 52.608). The per-view alignment dx/dy and yaw are in `rig/align.json`.
  - Voxels are 0.006 units. It is a strict carve, except a 2-view-tolerant zone at the top-back where the masters disagree on the bow and bun. It is smoothed and meshed with marching cubes, with padding so the surface is closed.
- **Yaw fit.** Hull consistency was best with SE −10 and NE −25. SE −10 also gave the best body silhouette IoU (.863, see the r4 sweep). These are now the per-view defaults.
- Reprojection IoU against the master head masks:

| S | SE | E | NE | N |
|---|---|---|---|---|
| .95 | .88 | .88 | .85 | .90 |

  The hull never overshoots by more than 26 px. The missing pixels are mostly the bow top in E and NE.
- Per-vertex material (hair, skin, bow, eyes) is voted from the visible master pixels. The hull replaces the H2 head, bun and bow and is fused into the body by the voxel union.
- Bones are re-anchored on the hull:
  - bow_knot / bow lobes: on the bow band at the back-top (widest bow-coloured slice at z 1.82–1.98)
  - ribbon tails: the bow-coloured hull below it, weighted to hair_back.2/3
  - bun: at the top-back
  - fringe: ends at the brows
  - hair_back: hair-coloured hull only
- **Projection.** In `build_rig.py`, each view gets UV `pj_<V>` (master cell coordinates) and a face mask `pm_<V>`. The mask covers head-group faces (hull + side locks) not occluded at rest (BVH ray toward the camera).
- **Textures.** `rig/make_tex.py` writes `rig/tex/tex_<V>.png`: the master with transparent pixels filled by their nearest opaque pixel, so a 1–2 px overshoot still gets head colours.
- **Render.** `render_motion.py` pass **`tex`** is EEVEE emission of the texture at 1 sample, with Closest filtering: exact master colours, alpha = mask. The preview shows the textured head.
- **Pixel step.** `render/r_tex_head.py` `tex_head(T, g)` gives each sprite cell more than 50 % covered by the tex pass its majority colour, snapped to the palette.
  - At rest this reproduces the master head (`rig/qa/r2_rest_vs_master.png`, 5 views).
  - Turns and tilts up to ±20°, and hair, bow and bun swings at M's limits, keep the master look (`rig/qa/r2_stress_SE.png`). Beyond about 40°, unseen texture regions smear (twist30_head40 = 70° total).
  - `--stamp` is retired (`OLDSTAMP` is not needed).

**Legs and body.**
- Thighs +8 % radius and hips (skirt) +3 %. The thigh centres are spread (±.097 at the hem) to keep a gap of 3 cm or more, so a narrow track can't fuse the inner thighs.
- The skin band is wider (sock top 0.622) and the red sock-top band is 0.026.
- Shoulders are 6 mm back and down. The spine, neck and head bones are vertical, so the rest pose stands upright.

**Limb IDs.** Pass **`lid`** (Workbench flat): her-left leg red, right leg green, left arm/sleeve/hand blue, right arm yellow. P also has its own part-ID pass.

**QA.**
- `rig/qa/r2_stress_SE.png`: 18 poses at 6× smooth, 4× pixel and 1× pixel. The 8 new poses are head turn L20 + tilt 10, head turn R20 + tilt −10, head nod, hair at the round-2 limits, contrapposto, hip sway, pointed toes and close soft knees.
- The R QA chain is `render/r_qa_chain.py`: the round-1 chain plus the tex head. The production pixel step belongs to P.
- Open issues for P: in SE the far leg can merge into the near one at 1×, and the bare-thigh band reads as separate blobs.

**Round 1 vs round 2.**
- `render/r2_all.sh` renders 8× passes, previews and the R QA chain into `render/out/r2/<act>/`.
- `render/r2_compare.py` builds `render/out/r2/compare_<act>_<view>.gif`: round 1 (stamp) | round 2 R QA | round 2 P chain | preview.

### Round 3 (R): face anchors, face-masked projection, cell clipping, A-line skirt (rig r6)
**Face anchors.**
- `build_rig.py` triangulates 7 anchors (eye.L/R, brow.L/R, mouth, cheek.L/R) by linear least squares through the affine game cameras S, SE and E. The 2D input is the m96 master anchors (`anchor.json`: eye centre = x0+3, y0+3.5; brow = y0−1.5; mouth = block centre; cheek = blush centre). Brows take their eye's depth.
- Pairs are mirror-symmetrised. Reprojection error is ≤ 1 px, except the SE far eye and cheek (master draws them 3 px lower than perspective).
- Normal = ½ hull normal + ½ head-forward.
- Each anchor is an empty `face.*` on the head bone; the data is in `rig/face_anchors.json`.
- Per frame, `render_motion.py` exports for each anchor:
  - `px`: game-cell 1× coordinates, with the output dx/dy
  - `px192`, `depth_m`, `facing`
  - `occ_m`: ray against the deformed non-head mesh
  - `visible`
  - `_head` yaw/pitch/roll in camera axes. Checked: stress head_turn_L20 → yaw +24, R20 → −27, nod up → pitch −19.
- QA: `rig/qa/r3_anchors_SE.png`.

**Face masked out of the projection.** `make_tex.py` clears the eye, brow, mouth and blush boxes to skin `s`. It keeps bangs (any hair component reaching outside the boxes), the outline and the nose. Pixels cleared: S 187, SE 160, E 89, NE 6. Masks: `rig/tex/face_mask_<V>.png`.

**Cell clipping.**
- `align.json` splits master registration (`reg_*`: hull, projection) from output placement (`dx`, `dy`), lifted by `lift_px`: S 4, SE 3, E 1, NE 2, N 2.
- Lowest rows after the fix: walk SE 124 (was 128.8), run S 127.8 (was 131.8).
- Remaining risk: the jump apex touches the cell top.

**Skirt.** A-line: rx .143 waist → .162/.176 over the hips → .184/.189 → .192 hem (was a cone .141 → .205), with depth to match.

### Round 4 (R): 8 directions, mirrored projection, skirt, nose, collar (rig r7)
**8 directions.**
- `render_motion.py` already had the 8 azimuths. `rig/align.json` now has SW/W/NW as mirrors of SE/E/NE: dx and yaw negated, dy, lift and registration as the source.
- The rig image of W is exactly the mirror of E about the cell centre (pivot on the column boundary 64), so mirrored masters register with no extra shift. Feet check: 0 px.
- `build_rig.py` writes `pj_`/`pm_` for all 8 views. `make_tex.py` writes `tex_{SW,W,NW}` (plus face masks) as horizontal flips.
- Board: `rig/qa/r4_rest_8dir.png` (flipped/lifted master | rig, 8 views).

**Head.**
- `head_hull.py` drops dress-red pixels below the mouth row (or in the stamp's bottom 5 rows) from the stamp masks. That collar used to become head geometry and draw red over the chin.
- It adds a nose ellipsoid (r .014/.016/.016) on the midline, at the master S nose / E profile bump and 6 mm proud of the face.

**Skirt and legs.**
- Hem .180/.142, near-straight sides.
- Side-seam grooves: −4.5 % × t^1.3 within ±11° of the sides.
- Inner thigh radius at the hem .064 (outer .074), centres ±.092: a leg gap of about 3 px under the hem.
- Board: `rig/qa/r4_walk_run_SE.png`.

### Known issues / next
- **Placeholder head.** The H2 head has a ragged hair/skin boundary and blob eyes. Use `--stamp` for now. The proper fix is heads96 layers that turn with the head.
- **SE body yaw.** The master SE is drawn more frontal than a true 45° camera. `--yaw=-15` approximates this (not the default).
- **Deep crouches.** The solid skirt flattens and there is no thigh volume helper. Corrective bones would help: hip-front and knee-cap helpers, a thigh twist.
- **Cuffs and fringe.** The bell cuffs are solid, so the opening reads as a disc when the arm is raised. The bangs are surface-painted, so `hair_front` should stay ≤ 15°.
- **Skirt drive.** The skirt is coupled to the legs only at the hem ring. Driving the front and back panels from thigh swing (M's sim) would stop the legs pressing into the side panels.

## M: animator

**Goal.** Fix the owner's verdict on the H2 animations: *"stiff and unnatural, the joints look off, need more dynamic movement, more movement details across the whole body, bouncing parts"*. Author idle / walk / run / jump as contract motion files with whole-body mechanics and baked spring secondary motion on every chain.

**Verdict.** The new motion is better than the old one in every A/B test, but it is not at game quality yet.
- **A/B against the old rejected frames** (r7, raw pixel renders from both pipelines; scores are A → B):

  | action | Opus | Argon |
  |---|---|---|
  | walk | 4 → 5 | 4 → 5 |
  | run | 4 → 5 | 3.5 → 5.5 |
  | idle | 4 → 5 | 3.5 → 5.5 |

  Both critics say "partly fixed" for the owner's complaint.
- **Absolute scores on the smooth preview** stayed at 5–6 / 10 over 7 rounds. The jump peaked at Opus 6 (key poses 7). The target of 7 was **not reached**.
- **What the remaining complaints are.** They are increasingly about things that are hard to read in the SE view, not about the motion data:
  - arms and sleeves flare on one half of the cycle (SE projection plus the rig's asymmetric sleeve bones, below)
  - legs overlapping on one contact
  - bell sleeves hiding the arms
  - the critics contradicting each other between rounds (stride "too long" vs "too short", contact foot "ahead" vs "under the hips")

  The motion is exactly mirror-symmetric between the two halves (checked: 0.0 mm ankle mirror error).
- The owner should judge `motion/out/cmp_*_old_vs_new.gif`.

### Files (all under `motion/`)
- Motion files (contract format): `walk.json`, `run.json`, `idle.json`, `jump.json`.
  - Extra informational keys: per-frame `key` (pose name), `travel_m_per_s`, `cycle_s`, `seam_mm`, `notes`.
  - `t` = source frame at 24 fps (it can be fractional, because frames are sampled from a continuous bake).
- Scripts in `scripts/` (team venv `swordswoman/.venv/bin/python`). The pipeline for one action is `mbuild.py <act>`:
  - `mrig.py`
    - Loads `rig/rest_skeleton.json`, or a stand-in made from the H2 joints if that file is missing.
    - Implements Blender's `vec_roll_to_mat3`. It matches Blender to 1e-7, and R's `matrix` for all 63 bones.
    - Runs FK with pose scale.
    - Bone-local quaternions use L = B⁻¹·r·B.
  - `mpose.py`: the pose solver.
    - Torso is set by world yaw/pitch/roll on the pelvis, chest and head. Spine and neck are slerped between them.
    - Arms are shoulder flexion about the yawed lateral axis, plus abduction, elbow, wrist and clavicle.
    - Legs use an **analytic 2-bone IK** to world ankle targets.
    - Foot roll pivots on the heel, ball or toe, and the toe stays flat while the heel lifts.
    - Knee pole is the pelvis-forward direction, with outward knee yaw.
  - `mbody.py`: key curves (`mcurve.py`, periodic and one-shot Hermite with flat holds) per action.
  - `msim.py`: the secondary motion.
    - Head lag spring.
    - Damped-spring particle chains with a cone limit.
    - Capsule and sphere collision.
    - The skirt panel ring is coupled, and skirt panels are driven by the thighs.
  - `mbuild.py`: bakes the action and writes the JSON.
- Preview and critique tools:
  - `mprev.py`: my own capsule preview, used in r1 before R's renderer existed.
  - `mboard.py --rig`: R's `render_motion.py --preview` → numbered frame grids for SE and E, plus an E onion skin.
  - `crit.sh` and `ab.sh`: Opus and Argon critiques. Each output file is checked for a SCORE line.
  - `mcompare.py`: OLD|NEW side-by-side GIF and A/B board.
  - `final.sh`: full pixel renders (SE, head stamp), preview GIFs for SE, E and S, comparisons, and `pxeval seq`.
- Outputs in `out/`:
  - `<act>_SE_px4x.gif`: pixel chain output with head stamp.
  - `<act>_<SE|E|S>_preview.gif`
  - `<act>_SE_px_sheet.png`
  - `cmp_<act>_SE_old_vs_new.gif`
  - `ab_<act>_SE_old_vs_new.png`
  - `pxeval_<act>_SE.json`
- Critiques and boards are in `crit/`: `r1..r7_<act>_{opus,argon}.txt`, `r6/r7_ab_*`, `board_<act>_<view>_<round>.png`.

### How the motion is built
- **Feet first (treadmill).** Each foot has a stance phase in which the ball/heel ground point moves backward linearly (the planted foot is fixed in the world when the game moves the sprite at `travel_m_per_s`), then a swing phase.
  - The swing is a Hermite curve whose end velocities match the stance velocity, plus lift and fore/aft offset keys.
  - Foot pitch follows the roll: heel strike with the toe up → flat → heel rise pivoting on the ball → toe-off → toe trailing down → reach.
  - The legs are pure IK, so there is no foot slide in the data.
- **Walk pelvis height is "compass gait".** For each phase, the highest pelvis at which every *stance* leg still reaches (0.995 L) is computed, Gaussian-smoothed, and then a keyed dip is subtracted.
  - This gives DOWN as the lowest point (knee about 40°), PASSING as mid, and UP (push-off on the ball) as the highest, with no hyperextension.
- **Run and idle use a keyed bob.** For the run, the base height is lowered just enough that no *planted* leg over-reaches. A swinging leg just straightens.
- **Overlap.** Shoulder, upper arm, forearm and hand each lag in phase (0 / 0.06–0.09 / 0.14–0.17 of the cycle).
  - The head has an angular spring driven by the neck-base acceleration, so it nods late on the down and tilts late on the sway.
  - In the idle the upper body lags the weight curve by 1 frame and the arms by 2.
- **Squash and stretch.** Scale is applied to the chest and head only (never the pelvis, because Blender inherits scale into the legs). The amounts are:

  | action | chest | head |
  |---|---|---|
  | walk | ±3% | ±0.8% |
  | run | ±7% | ±3.5% |
  | idle breath | +3.5% | – |
  | jump | −8% … +6% | −4.5% … +3% |

### Keys and timing chart (frames as displayed; the springs were simulated continuously at 400 Hz)

**walk**: 8 × 105 ms, cycle 0.84 s.
- Keys: f0 contact L, f1 down, f2 passing, f3 up, f4 contact R, f5 down, f6 passing, f7 up.
- Stride: ball travels ±0.22 m (step about 0.36 m, foot speed 0.87 m/s = 6.2 px/frame at 1x).
- Pelvis: bob 4.6 cm peak to peak, sway ±2.6 cm, yaw ±13°, roll ±7.5°.
- Chest: counter-yaw ±10°, lean 10°.
- Arms: ±24–28° at the shoulder, inward on both swings. Elbow 16–46°, peaking 1 frame late.
- Feet: heel strike toe-up 30°, toe-off −42°, swing lift 10 cm.

**run**: 8 × 70 ms, cycle 0.56 s (sampled +0.15/8 phase so that f2 = push-off and f3/f7 = mid-flight).
- Stance 30%, so each step has a flight phase.
- Pelvis: bob 8–9 cm, down knee about 60°, contact knee about 4°.
- Lean: chest 24°, pelvis 12°, head pitched about 8°.
- Arms: −52/+62° from world vertical (corrected for the lean), elbow 80–108°.
- Legs: heel kick up to 0.32 m, knee drive forward 0.16 m.

**idle**: 12 frames, 2.4 s. Display times:
- 300 / 300 (holds) / 80 / 120 / 160 (transfer, eased) / 240 (settle) on her left, then the same on her right.
- Holds: hip shift ±7.5 cm with a 7% overshoot at each settle; pelvis roll ±11° (contrapposto); chest counter-tilt −7°.
- Transfers: knees dip 1.6 cm, then a 0.7 cm overshoot up with chest squash.
- Free leg: heel lifts 24°.
- Head: tilts toward the free hip by 8°, lagging 0.18 s. At the R hold it turns 27–32° toward the camera, leading by 1 frame.
- Breathing: 2 breaths per loop. Chest +3.5%, shoulders +5°, head following 1 frame behind.
- Arms swing 7°, 2 frames behind.

**jump**: 16 frames, one-shot, 1.36 s.

| frame | ms | key |
|---|---|---|
| f0 | 100 | stand |
| f1 | 80 | anticipation |
| f2 | 70 | crouch (hold) |
| f3 | 50 | launch |
| f4 | 60 | take-off stretch (toes −40°, arms 172° overhead) |
| f5, f6 | 80 + 80 | rise (ballistic: 50 / 30 / 15% spacing) |
| f7 | 120 | apex (tuck, arms up-and-out V) |
| f8, f9 | 60 + 40 | fall (legs reach) |
| f10 | 35 | land on the toes |
| f11 | 75 | absorb |
| f12 | 100 | squash (pelvis −19 cm, lean 32°) |
| f13 | 80 | overshoot onto the toes |
| f14 | 110 | settle dip |
| f15 | 250 | end |

- Apex: pelvis +0.33 m.

### Spring parameters (`msim.GROUPS`, with per-action overrides in `mbuild.SPRING`)

| chain | f (Hz) | ζ | gravity-hang | air drag (1/s) | gain | max ° | collision |
|---|---|---|---|---|---|---|---|
| hair_front | 4.2 | .30 | .15 | 0.6 | 1.6 | 14 | head sphere |
| hair_side | 2.3 | .32 (walk .44, run .5) | .45 | 1.2 | 2.4–2.7 | 22 | head sphere, neck |
| hair_back | 2.1 | .32 (walk/run .5) | .40 | 1.4 | 2.5–2.7 | 28 | head sphere, neck |
| bun | 2.6 | .20 | 0 | 0.2 | 3.4 | 16 | – |
| bow lobes | 2.3 | .22 | .08 | 0.8 | 3.0 | 24 (R limit 25) | – |
| sleeves | 2.3 | .34 | .45 | 1.6 | 1.0 | 25 | chest, spine |
| skirt ×8 | 3.0 | .30 | .12 | 1.4 | 2.6 | 34 | thighs, pelvis + thigh drive 0.55 + neighbour ring |

How the springs work:
- **Driving force and drag.** Each chain is driven by its parent bone's world motion: inertia, drag against the travel wind, and a gravity hang that blends toward the world-rest direction.
- **Gain.** The gain exaggerates the simulated deviation on output, clamped to the max. Inside the sim there is a cone limit of 1.3 × max / gain, which keeps the chains stable.
- **Idle.** Softer and slower (bow 1.7 Hz, hair 1.5–1.6 Hz, skirt 1.9 Hz).
- **Jump.** Softer, with 4–5/s air drag so the hair and skirt float up on the fall.
- **Loops.** These are simulated for 6 pre-roll cycles, and the last cycle is kept. Seam error (chain points, cycle n vs n−1) is ≤ 0.4 mm on all final loops.
- **Lessons on spring tuning:**
  1. **Damping below about 0.3 under strong running bobs goes chaotic.** Hair flipped and the seam error was 0.1–0.5 m, so the cycle never repeats. Raise ζ.
  2. **Keep the natural frequency below about 0.4 × the sprite frame rate.** Otherwise the oscillation aliases into frame-to-frame "buzzing". Opus flagged the bow jittering in the idle at 3.6 Hz with 80–300 ms frames.
  3. **Use spheres, not capsules, for head collision.** The capsule's end caps flipped the push direction.

### pxeval `seq` (SE pixel GIFs, OLD = hires3d grid cel_kc_hs column → NEW)

| clip | flicker | boil | motion_px | articulation | rigid_share | sil_change | pose_range | head_range px | head_jerk |
|---|---|---|---|---|---|---|---|---|---|
| walk | .36 → .29 | .13 → .06 | 1.14 → 1.16 | .34 → .29 | .33 → .43 | .35 → .29 | .54 → .48 | 3.6/1.0 → 5/7 | 2.1 → 3.7 |
| run | .41 → .43 | .12 → .16 | 1.05 → 1.19 | .34 → .30 | .21 → .40 | .43 → .38 | .58 → .53 | 6.2/5.7 → 3/8 | 4.5 → 5.8 |
| idle | .12 → .15 | .016 → .036 | .53 → .68 | .15 → .17 | .53 → .53 | .09 → .15 | .27 → .46 | 1.2/0.5 → 7/5 | 0.4 → 2.8 |
| jump | – | .08 | .94 | .29 | .26 | .39 | .79 | 14/37 | 9.8 |

- **The head now moves a lot more** (it was a rigid stamp before): head_range 5–7 px, against 1–4 px.
- **The idle has much more motion**: pose_range .27 → .46, sil_change .09 → .15.
- **The walk boils less**: .13 → .06.
- rigid_share went up (.33 → .43): a larger share of the motion is one block slide. Part of this is the bigger whole-body bob, but it also matches the critics' "torso is a block" complaint. No clip trips STIFF or FROZEN. Flags (BOILING / SHADE_SWAP) come from R's pixel chain, not from the motion.
- Caveat: the old numbers come from a cropped 3× GIF column.

### Round log (Opus / Argon absolute scores; boards in `crit/`)

| round | change | walk | run | idle | jump |
|---|---|---|---|---|---|
| r1 | first bake; capsule preview, stand-in skeleton → R's skeleton | 5/6 | 5/6 | 4/4 | 4/5 |
| r2 | bob peaks on UP, heel strike 24°, lean, run flight (stance .30), idle amplitude ×2, jump retimed; **switched boards to R's skinned preview**; arm swing axis fixed (it crossed the body at large angles) | 4/5 | 5/5 | 4/5 | 5/5 |
| r3 | per-action springs, sleeve hang, skirt gain | 5/5 | 5/5 | 4/5 | 5/6 |
| r4 | skirt panels driven by thighs (R request), springs below the aliasing frequency, run arms in world vertical, idle contrapposto ×1.5 | 5/6 | 5/5 | 5/5 | 5/5 |
| r5 | knee-yaw sign bug fixed (the R knee went inward, so legs crossed and knees knocked); only stance legs set the pelvis height; longer strides | 5/5 | 5/5 | 5/4 | 5/5 |
| r6 | idle U-arc dip + overshoot, jump fall/land/overshoot rework; first A/B against the old frames | 5/5 | 5/5 | 5/5 | **6**/5 |
| r7 | arms swing inward both ways (less SE "wings"), narrower track (the SE legs overlapped on one contact), smaller idle dip; A/B | 5/5 | 5/6 | 5/6 | (r6) |

Recurring critic notes that are still open:
1. Sleeves look like "wings" on one half in SE. This is projection plus the rig's asymmetric sleeve bones (reported to R).
2. The torso reads as a block. The yaw/roll are there but small on screen. Could try a camera-aware cheat: more chest twist in SE.
3. The bun, bow and skirt still move "too little" at sprite size. They are capped by R's deformation limits (bow ≤ 25°, hair_front ≤ 15°).
4. Walk contacts read flat because the boots are big.
5. Run contacts read as marching in SE.

The critics also contradict each other on stride length and foot placement, so the next step is the owner's eye on `out/cmp_*.gif`, not another critic round.

### Notes for R / next
- **Rest skeleton asymmetry:**
  - sleeve.L tails are at y = +0.050 / +0.086 and sleeve.R tails at −0.025 / −0.043, a 75–129 mm mirror error.
  - hair_side.L.1 head is at x −0.174 and hair_side.R.1 at +0.189.
  - Mirroring these needs no change on my side.
- **Sock-top creases** show in the idle when the free knee bends.
- **Run travel speed** is 2.5 m/s = 11.9 px per 70 ms frame at 1x. If that is too fast for the game, scale `T` up, or play at about 80 ms per frame.

## M: round 2 (owner: "gradual improvements… legs flicker… whole body incl. head, hair should move… not stiff"; posing: "elegant, not slouched, confident, feminine")

**Result.** All 4 actions were re-baked against R's r5 rig: animatable master-textured head, new hair/bow/bun bones, SE yaw −10.
- Rendered through P's round-2 pixel chain with no head stamp, so head and hair motion now shows.
- A/B round 1 → round 2 at 1x and 4x on the same rig and chain (`crit/r10_ab2_*`):

  | action | Opus | Argon |
  |---|---|---|
  | walk | 4 → 5 | 4 → 6 |
  | run | 4 → 5 | 4 → 6 |
  | idle | 4 → 5 | 4 → 6 |
  | jump | 5 → 5 | 4 → 6 |

- Posing sub-scores for B: Argon gives elegance 6 and no-slouch 6–8; Opus stays at 4 / 3–6 (it still sees the head pitching forward in parts of the idle and jump).
- Every motion is now ≥ 1 px at 1x or held (table below). Target 7 not reached.

**What changed**
- **Pixel-aware amplitudes**, checked per part per frame with the new `scripts/mpx.py`. It projects through R's camera at 1x (67.88 px/m, per-view yaw from `rig/align.json`) and measures:
  - pelvis and head-top bob
  - head roll, nod and yaw
  - spring tip displacement against a rigidly attached secondary
  - tip direction flips
  - hand distance from the sleeve hem
  - L/R leg screen separation
  - planted-foot slip at the game travel speed
- **Snappier timing with holds**, sampled phase-correctly (no time warp, so no foot slip):
  - walk 90/120/90/120 ms (contact / **down held** / passing / **up held**)
  - run 60/80/60/80 ms (down and flight held)
  - The motion keys were moved onto those sample phases.
- **Posture (owner addendum)**
  - Walk: chest lifted (chest pitch −4°, nod limited to 2°), chin up 7°, shoulders back and down 5° / 3°, poised hip sway (roll 5.5°), pelvis yaw cut to ±6° (the ±10° read as the whole body turning in SE). Feet closer to the midline but never crossing (track 0.62 of hip width), toes pointed in swing (−45°), lighter heel strike (18°).
  - Arms: soft and close (abduction −16°), forearm leads and wrist trails (lag 0 / 0.13), swing −20/+26°, wrists bent 10–32°.
  - Run: upright, lean 8° (from the hips), chin level, elbows about 90° held in close, hip yaw ±6°, bob cut to 3.9 px.
  - Idle: contrapposto kept and stronger (hip shift ±8.5 cm, roll ±11°, free knee relaxed inward, free heel up 30°). Chest lifted 6°. **Right hand rests at the front of the obi** (elbow 98°). The left arm hangs soft along the skirt. The head turn toward the camera is cut to 20° (R's limit), and the breath is bigger (chest +5%, shoulders +7°).
  - Jump: shallower crouch with the hips hinged and the chest open (lean 10°). **Arched apex**: chest −13°, chin up, lower legs swept back, toes pointed −55°, knees together. Arms make an asymmetric up-and-out V with soft elbows. Soft landing (−12 cm, lean 6°) with an overshoot onto the toes.
- **Springs, and two bugs found with the px measurements**
  1. **The output clamp saturated.** Most chains sat at their max angle 80–100% of the time, so they flapped between the limits frame to frame. It is now a soft `tanh` limit, and the gains were re-tuned to target tip p-p.
  2. **The chain-curl feedback (`follow`) made long hair flail.** Run hair_back went 20 px → 6 px with follow off. follow is now 0–0.15.
  - Frequencies now avoid the step bob (walk 2.4 Hz, run 3.6 Hz): bow 3.4 Hz with ζ .5, bun 3.6 Hz, long hair 1.9–2.0 Hz with ζ .7.
  - R's r5 limits are respected: hair_front 14, hair_side 22, hair_back 28, bow 24, bun 16°.
  - Loop seams ≤ 0.3 mm.

**1x amplitudes in SE (px p-p, `out/mpx_<act>_SE*.json`; round 1 → round 2, same rig)**

| | pelvis bob | head-top bob | head roll / nod (°) | bangs | side locks | back hair | bun | bow | skirt | min leg sep | foot slip |
|---|---|---|---|---|---|---|---|---|---|---|---|
| walk | 4.5 → **3.1** | 7.7 → 6.5 | 11 / 2 → **15 / 6** | 1.6 → **2.3** | 13.5 → 5.8 | 16.6 → 7.0 | 3.0 → 2.7 | 5.6 → 4.3 | 6.3 → 4.7 | 1.7 → 0.0 (at passing) | 0.6 → 0.7 |
| run | 5.3 → **3.9** | 9.7 → 8.3 | 8 / 7 → **15 / 9** | 3.4 → 4.2 | 10.7 → 8.4 | 12.6 → 12.3 | 2.9 → 2.8 | 5.8 → 5.5 | 11.2 → 7.0 | 1.3 → 0.8 | 0 |
| idle | 3.6 → 4.0 | 5.0 → 5.1 | 17 / 4 → 19 / 3 | 5.0 → 2.4 | 12.6 → 7.2 | 11.0 → 5.3 | 4.0 → 3.4 | 5.2 → 4.3 | 10.1 → 6.0 | 8.0 → 6.4 | 0 |
| jump | 31 → 27 | 42 → 36 | 19 / 27 → 12 / 20 | 4.8 → 2.0 | 13.5 → 10.8 | 9.8 → 8.2 | 2.2 → 1.9 | 5.9 → 5.4 | 9.1 → 7.5 | 8.8 → 6.5 | 0 |

- **Round 1's tips already moved in the data**, but they flailed at the clamp, and the owner never saw them because `--stamp` covered the head.
- **Round 2 tips are calmer and coherent.** The flip share is 0.25–0.5, meaning 1–2 reversals per bounce, not frame-to-frame jitter.
- **Walk leg separation reaches 0 px at passing and contact R in SE.** Legs pass each other in SE with a feminine narrow track. This is left to P's overlap separation, plus R's thigh gap.

**pxeval seq** (P chain, SE, `out/pxeval2_*`; round 1 → round 2):

| action | boil | shade_swap | pose_range | sil_change |
|---|---|---|---|---|
| walk | .022 → **.016** (BOILING flag gone) | .043 → .039 | .47 → .46 | .24 → .21 |
| run | .087 → .057 | .049 → .043 | .52 → .44 | .36 → .29 |
| idle | .008 → .007 | .027 → .027 | .45 → .50 | .15 → .15 |
| jump | .083 → .070 | .046 → .045 | .77 → .74 | .38 → .31 |

The rest of the flags (SHADE_SWAP, FEET_JITTER) come from the chain, which is P's.

**Files (new)**
- `scripts/mpx.py`: 1x amplitude check.
- `scripts/r2_render.sh`: R render + P part pass + P chain → `prev/r2/` (round 1 motion → `prev/r1cmp/` via `MDIR=motion/round1 OTAG=r1cmp`).
- `scripts/msil.py`: silhouette sheets, 1x/4x strips, A/B board.
- `scripts/ab2.sh`: critic prompt. It scores elegance/confidence/femininity and no-slouch explicitly.
- Outputs in `out/`: `cmp2_<act>_SE_r1_vs_r2.gif`, `r2_<act>_SE_px4x.gif`, `sil_<act>_SE.png`, `strip_<act>_SE_r2.png`, `mpx_*`, `pxeval2_*`.
- Round 1 motion is kept in `motion/round1/`.

**Still open**
- Opus keeps seeing a forward head and slouch in the idle settle and the jump fall.
- The bell sleeves still flare wide on one half of the SE walk.
- Bun motion is at the 16° limit, about 2–3 px.
- The run hair_back swings about 12 px. That is lively, maybe too much.

## P: pixel engineer (round 2)

**Goal.** The owner said: *"limbs like legs sometimes flicker and disappear ... I still see disconnected parts like legs, thighs"*. Make the 3D→pixel step produce
clean, stable, readable 96 px frames on the locked palette (`v2/pixelize/palette.json`), with the m96 masters as the reference look.

**Verdict.** Both critics say P2 fixes the two failures the owner named: legs no longer vanish, and the thighs stay attached to the skirt.
- Opus: 6.5/10 for P2 vs 4.5 for round 1 as shipped. Argon: 7.2 vs 3.4 (round 2 critique, `crit/p2/*_r2.txt`). Round 1 critique: 6 vs 4 and 6.0 vs 4.8.
- **The pxeval gates are not met**, except boil on walk SE/S and idle:
  - boil fell in 9 of 12 clips;
  - shade_swap still fails everywhere (best: idle S .017);
  - FEET_JITTER is mostly geometric (explained below).

### Files (all under `render/`)
- **`pixel_chain.py`** (I own this now). It is called unchanged by R's `render_motion.py` post stage. Round 1 is kept as `pixel_chain_r1.py`, which `--preview` still uses.
- **`p_parts.py`**: my extra Blender passes. It runs R's `render_motion.py` with `KINDS=guide` after swapping in my own vertex-colour attribute, so camera, pose, yaw and alignment are identical. R's guide pass reads the attribute named `Color`, so the names are swapped in memory only; the rig file is never saved.
  - `*_part.png`: per-face dominant deform bone, plus `bones.json` (bone → part group). The groups are torso, head, skirt, leg.L/R, arm.L/R and sleeve.L/R.
  - `*_rpos.png`: rest-pose surface position, plus `rpos.json`. This gives exact surface correspondence between frames.
- **`p2_run.sh "<acts>" "<views>"`**: end to end into `out/p2/<act>/`. It renders R's passes (`--no-post`) and my parts together, so a rig or motion update can't desync them. It then runs the P2 chain, and the round-1 chain on the same passes into `out/p2/r1/<act>/` as a fair baseline.
- `p2_board.py`: comparison boards (master | r1 shipped | r1 chain | P2) at 4x/6x plus 1x strips.
- `p2_gifs.py`: `cmp_<act>_<view>_4x.gif` (r1 chain | P2) and a 1x strip.
- `p2_eval.py`: pxeval seq on every clip → `out/p2/pxeval/*.json` + `table.md`.

### Method (P2 chain, all knobs are env vars)
1. **Vote by material and part, not by colour clustering.** Each hi-res pixel's segment is its matid material × its part from the bone pass. Each 8×8 block gets the segment with the best coverage, weighted 1.25 for limbs and 1.3 for the nearest depth. k-centroid and palette snapping are gone; colours come straight from the ramp of the chosen material.
   - Skirt cloth weighted to the thigh bones (the hem ring) is reassigned to the skirt. The leg part is only skin band, sock band, socks and boots, so there are no leg lines inside the skirt.
2. **Outline outside the fill.** The fill is the silhouette eroded by `ERODE` = 6 hi-res px (legs `ERODE_LEG` = 9, which makes them slimmer). The 1 px K outline is the 4-dilation of the fill, made pixel-perfect (L corners removed). Thin parts are no longer eaten by their own outline.
3. **Limb protection (legs and hands).** Cells on the hi-res skeleton are forced to the limb, with the nearest limb winning. Every limb pixel must then sit in a 2×2 block of that limb, grown toward the block with the most hi-res coverage. So legs keep ≥ 2 px of fill and can't vanish.
4. **Silhouette cleaning.** 1 px spikes and notches are fixed, a 3×3 majority pass runs on the skirt, torso and sleeves, and enclosed holes of ≤ 4 px are filled (they had made dotted K rings in the arm/body slits). Limbs and the head are exempt.
5. **Overlap separation.** leg.L | leg.R overlaps, and arm or sleeve over the body (depth step > `DTHR` .03), get a 1 px K line on the **far** side. Two exceptions:
   - If that would thin the far limb below 2 px, the near limb carries the line.
   - If neither side has room, the line is replaced by a lit edge.

   Interior lines shorter than 3 px are dropped (r10 rule). Leg|leg lines are always kept.
6. **Form on dark materials.**
   - Socks are D, with a lit `d` stripe on the near leg and a **`g` rim along the leg|leg line**. Opus asked for a lighter value; `d` was invisible at 1x.
   - A red sock-top row (E) is guaranteed between skin and sock.
   - The skin band is `s`, with `S` on the hem row.
   - The skirt uses two values only (E/R, no flickering `e` clusters).
   - The far leg is one step darker (S / R / boots down one band). It is fixed per view (her left leg in SE/E), so it doesn't swap when the legs pass.
   - I did not use sel-out on the socks: with this palette the sock's dark tone *is* D, which would erase the leg edge. The masters use K everywhere.
7. **Head = R's `tex` pass.** It is the projected master: I find the texel phase, roll it onto the sprite grid, and take the per-cell mode of the exact palette colours. There is no double outline where the master's own K is already the edge. Orphan cleaning skips the head.
8. **Temporal stability.**
   - Every cell finds the previous cell showing the same rest-pose surface point (same bone, k-d tree on `rpos`).
   - Hysteresis is applied on fill coverage (.3/.7), on the label (the previous label is kept unless beaten by 25%) and on shade bands (margin `HYS` .08). Shades are surface-locked (`LOCK` .12).
   - The head is held when < 30% of it changes.
   - Unchanged hi-res blocks reuse the previous output.
   - Isolated one-frame shade flips (a = c ≠ b within one material class) are removed.
   - Loops run twice, so f0 sees the end of the cycle.

### pxeval seq (same passes, current rig r5 + M's 18:35 motion; r1 = round-1 chain with the rig head, P2 = new chain with the tex head)
| clip | boil r1 → P2 | shade_swap r1 → P2 | feet_range | articulation/s | flags P2 |
|---|---|---|---|---|---|
| walk SE | .021 → **.016** | .029 → .038 | 5 → 5 | 3.35 → 2.78 | SHADE_SWAP FEET_JITTER |
| walk E | .054 → .046 | .034 → .038 | 4 → 4 | 3.43 → 2.76 | BOILING SHADE_SWAP FEET_JITTER |
| walk S | .023 → **.015** | .036 → .027 | 9 → **2** | 3.00 → 2.51 | SHADE_SWAP |
| run SE / E / S | .072/.142/.030 → .060/.133/.035 | .034/.032/.055 → .040/.043/.038 | 8/15/6 → 8/7/6 | ~5.1 → ~4.4 | all |
| idle SE / E / S | .011 → **.007/.008/.006** | .025/.027/.027 → .027/.026/**.017** | 2/2/2 → 2/1/2 | ~1.2 → ~1.0 | SHADE_SWAP |
| jump SE / E / S | .077/.083/.117 → .082/.070/.094 | .035/.032/.038 → .044/.046/.028 | ~31 (root motion) | ~3.4 → ~2.9 | n/a for feet |

- **Round 1 as shipped** (old rig and motion, head stamp, walk SE): boil .056, shade_swap .047, feet 8.
- **P2 with the rig head instead of tex**, for a like-for-like chain comparison: walk SE .018/.024, idle SE/E/S .009/.016, .009/.018, .007/.020.
  So the chain itself lowers both numbers. The projected master head adds about .01 of shade_swap: its fine h/H/K hair texels are resampled whenever the head turns or tilts.
- No clip is FROZEN or STIFF. articulation/s stays at 2.5–4.5 for walk/run and about 1 for idle. The drop of about 15% against r1 is noise that is no longer counted as articulation.

### Why the gates still fail (measured, for the lead)
- **shade_swap is mostly fast motion on near-colour dark materials.** 74% of walk SE shade swaps sit on surfaces moving > 2.5 px/frame (via the `rpos` correspondence; pxeval's matcher only explains ±2 px shifts).
  - K/D/h/H/d are all within ΔE 12 of each other, so any edge on a fast-swinging leg counts as a "shade swap".
  - On slow surfaces P2 is .0116 vs r1 .016.
  - The gate (snowpeak, lighter palette, more frames per cycle) can't be reached at 8 frames per walk/run cycle without in-betweens or holds. **M:** 12-frame walk/run, or holds on the passing poses. **R/M:** quantise the head turn/tilt (hold the head pose for ≥ 2 frames) to remove the tex-head swaps.
- **run/jump boil is limb motion over 2 px/frame on uniform dark patches**, which pxeval reads as "rigid". The flags agree with the r1 chain; in-betweens would fix this as well.
- **FEET_JITTER in SE/E is real perspective, not jitter.** At 30° elevation the forward foot of a 0.22 m stride projects about 7 px lower. In walk SE f04/f05 the sole reaches hi-res row 128.6, so it is **clipped by 1 row at the cell bottom** with the align.json dy=1. **R:** consider dy=0 for SE walk/run, or a taller cell. walk S (no depth stride) is 2 px, which passes.

### Critiques (`crit/p2/`)
- Round 1 (`opus_r1`, `argon_r1`):
  - Opus 6 vs 4: "fixes the two failures the owner rejected".
  - Remaining issues it named: the legs merge into a "trunk" at the passing pose, blotchy skin under the hem, hem flicker, an inconsistent sock-top band, and toe spurs.
  - Fixes: slimmer legs, the near-leg rim, a guaranteed sock-top row, a 2-value skirt, hem smoothing, and pelvis-weighted thigh skin set to S.
- Round 2 (`opus_r2`, `argon_r2`):
  - Opus 6.5 vs 4.5 (thigh connection 8 vs 3). Argon 7.2 vs 3.4.
  - Still open: the passing-pose legs (the `g` rim was added after this round), the skirt reads as a wide tent with stair-stepped hem corners, the skin wedge under the hem changes size each frame (R's fuller thighs show under the flared skirt), squared boot toes, and blush blocks or hair pixels over the face in idle f06–f09 (from the tex head).

### Next
- Toe-tip template (2 px taper) and hem curvature smoothing.
- Lock the height of the skin wedge to 2–3 rows.
- Head hold keyed to the motion (needs M's holds).
- Re-run `render/p2_run.sh` when M posts the final round-2 motion.

## M: round 3 (owner: run "very stiff and awkward, more leaning forward"; "test different timings and lengths"; "more expression"; "GIFs loop smoothly")

**Result (A/B round 2 → round 3, `crit/r11_ab3_*`):**

| action | Opus | Argon |
|---|---|---|
| run | 4 → 5 | 4 → 6 |
| walk | 4 → 5 | 5.5 → 6.5 |
| idle | 5 → 5 | 5 → 6 |
| jump | 5 → 5 | 5.5 → 6 |

- The face region is blank in these renders: R masked it, and F adds the faces.
- **The lean reads in E but not in SE.** The run lean (15°) is clear in the E preview, which is the one the owner criticised (`out/run_E_preview.gif`, `out/grid_run_pv_E.gif`). In the SE game view a forward lean points mostly toward the camera, so Opus reads it as "no lean" or a head drop. If SE has to show it, the next step is a view cheat: a screen-space lean in SE.

**Changes**
- **Run rework (`mbody.RUN`).**
  - Confident lean: chest 15° and pelvis 14° (straight back, from the hips). The foot track sits 5 cm behind the hips, so the lean also comes from the ankles. Head held up looking ahead (−7°). Arm pump measured from world vertical.
  - Heel kick-back first (u .18: foot 22 cm up, 8 cm back), then knee drive (30 cm up, 17 cm forward), then the foot reaches under the hips. Toes pointed −75° in the kick.
  - 30% stance, so there is a real flight phase. Elbows 90 ± 7°, swing −44/+52°, close (−12°). Counter-rotation: hips ±9°, chest ±12°.
  - Bob 4 px with chest squash 6%.
- **Timing and length variants.** 24 files in `motion/variants/`, made by `scripts/mvariants.py` via `mbuild.build(act, var=…)`. Frames are sampled phase-correctly, so a hold is a real pose hold and the feet still never slip.

  | action | frame counts | feels | cycle |
  |---|---|---|---|
  | walk | 6 / 8 / 10 / 12 | **s**nappy (samples on the key poses, passing held per P) / **e**ven | 0.84 s |
  | run | 6 / 8 / 10 | snappy / even | 0.56 s |
  | idle | 8 / 12 / 16 | **h**olds / even | 2.4 s |
  | jump | anticipation (crouch hold) ×0.5 / ×2.5 crossed with apex hang ×0.6 / ×1.8 | — | one-shot |

  - Jump time warp: the springs run in real time over a warped key timeline.
  - The cycle stays the same within an action, so the comparison grids loop seamlessly.
  - **Grid GIFs** (labelled A, B, …, with frame number, ms and key per cell): `out/grid_<act>_px.gif` (P pixel chain 3x), `out/grid_<act>_pv_SE.gif`, plus `grid_{walk,run}_pv_E.gif`. They use 20 ms ticks, so every GIF frame is ≥ 20 ms, and the loop equals the cycle. Jump cells are padded with an end hold.
- **Expression track** for F, on every frame of every file: `face`, `blink` (0 / .5 / 1) and `mouth`.
  - walk: smile
  - run: determined, then effort with mouth open on down/push-off
  - idle: neutral, blinks on the 2 hold frames, smile when looking at the camera
  - jump: neutral → determined → effort → joyful at the apex → surprised on the fall → squint on the landing → smile
- **Posing fixes.**
  - The idle settles and the jump landing no longer nod forward. The head stays pitched up 3–10° in every frame (measured from FK).
  - **Head turn/tilt is held for 2 frames** (`head_hold`): idle always, walk at 10/12 frames. This is P's request, to stop the tex-head resample swaps.
  - Walk snappy timing holds the passing pose (71 / 118 / **126** / 105 ms).
- **GIF timing.** All comparison GIFs are re-written on 20 ms ticks: `out/cmp_*` (H2 vs round 1), `cmp2_*` (round 1 vs round 2), `cmp3_*` (round 2 vs round 3). Minimum frame times: grids 20 ms, cmp 20–100 ms, R previews 30–70 ms, P pixel GIFs 40–80 ms. (Round 2's motion JSONs were overwritten by this bake. Their pixel renders are kept in `prev/r2/`, and `motion/round2/` has labels only.)

**pxeval gates** (P chain, SE; `out/pxeval3_table.txt`)

| gate | walk 8 / 10 / 12 | walk 6 | run | idle | jump |
|---|---|---|---|---|---|
| boil ≤ .02 | **pass** (.005–.018) | fail (.033) | fail (.05–.12; fewer frames boil more: 6 frames .12, 10 frames .05) | **pass** (.009–.016) | fail (.073–.076) |

- **shade_swap ≤ .015 fails everywhere** (.018–.041). That is P's chain on fast surfaces.
- **FEET_JITTER** comes from the SE stride perspective, as P found.
- Takeaway: more frames per cycle means less boil. The 10/12-frame walk and the 16-frame idle are the cleanest.

## F: face artist (round 3)

**Goal.** The owner said: *"the faces are all messed up. the faces need to follow the head's movements ... follow the 3d model as reference ... more expressive depending on the action."*
In round 2 the face was baked into R's projected head texture, so it smeared whenever the head turned or tilted, and hair and blush texels fell onto the eyes (idle f06–f09).
The round-3 face is hand-designed pixel parts placed per frame on the 3D head's projected anchors. This is the snowpeak `pipeline/face.py` idea, with the approved m96 face as the parts.

**Verdict.**

| critic | round 1 | round 2 |
|---|---|---|
| Opus (a / b / b2 / c / d) | follows 6, on-model 7, clean 7, expressive 6, stable 7 (previous round: 4 / 6 / 3 / 2 / 4) | 7.5 / 7 / 6 / 7.5 / 6.5 |
| Argon | 7.5 / 8.5 / 7.5 / 9 / 6.5 (previous round: 4 / 3 / 2 / 1 / 4) | 8.5 / 9 / 8 / 9 / 8 |

Critiques are in `face/crit/{opus,argon}_r{1,2}.txt`.

### Files (all under `face/`)
- **`face_lib.py`**: the part library. It reads `v2/m96/eye_spec.json` through `v2/m96/tools/eyetmpl.py`, so eyes, brows, mouths, blush and nose are pixel-identical to the m96 masters and stamps.
  - Named expressions (`EXPR`): neutral, smile (closed `m..m/.mm.`), smile_open, joyful, determined, effort, strain, shout, surprised (small "o"), squint (land, `> <`), wink, blink and half_blink.
  - Effort keeps narrowed, open eyes. The critics read squeezed-shut eyes during a run as "eyes shut all jump". The spec's squeezed eyes are kept as `strain`.
  - Overlays: blink cues (M's numeric 0/.5/1) and M's `mouth: open|closed`.
  - A 3 px foreshortened far eye (`far3`).
  - `build` writes faceless textures `tex/tex_<V>_nf.png`: the master with the features erased. `calib` writes `calib.json`.
- **`f_render.py`** (Blender). It wraps R's `render_motion.py`, as P's `p_parts.py` does, and leaves R's files untouched.
  - It swaps the projection texture in memory for the faceless one and renders the `tex` pass (8x) or the `--preview` frames.
  - It ray-casts each m96 anchor pixel onto the rest head and stores it in the head bone's rest frame. Per frame it re-poses the anchors with the head-bone matrix and projects them.
  - Output: `out/<act>/<act>_<V>_face.json`, with per-anchor xy, depth and facing, plus head yaw/pitch/roll.
- **`face_layer.py`**: **P's call** `face_layer(frame_info, pixel_frame, passes) -> pixel_frame`, plus a CLI `apply <frame_dir> <act> <view> <out_dir>`.
- `f_run.sh "<acts>" "<views>"`: end to end. Use `NORENDER=1` to re-place without Blender and `NOPV=1` to skip previews.
- `f_preview.py`: face composite on the smooth preview.
- `f_board.py`: boards, GIFs and expression sheets.
- `f_critstrip.py`: critique strips.
- `f_pchain.sh`: P's unchanged chain re-run on the current motion into `out/p2cur/`. My test frames live there because M re-baked at 21:33 and the frames in `render/out/p2` no longer match the poses. You can delete it (≈600 MB).

### Method
1. **Anchors (3D).** For each view, the anchor.json eye iris centres, brows, mouth, blush and nose are ray-cast at rest from the view camera onto the head. Each is kept as a point in head-bone space (`anchors_head_local_m`; S: eyes ±0.074 m, mouth 0.039 m up the bone).
   - Per frame: p = H_head(frame) · H_head(rest)⁻¹ · p₀, then the camera projection gives 128-cell xy, depth and facing.
   - At rest these points reproduce the master exactly, error 0 px. R's `rig/face_anchors.json` points are mirror-symmetrised triangulations that sit 2–3 px off the master per view (S eyes 2.3 px low, SE far eye 3.5 px high). So I place parts with mine and use R's `visible`/`occ_m` only for body, arm and hand occlusion.
   - **Calibration.** The rig head renders above the master by S 4, SE 3 and E 1 px. That is exactly R's new `lift_px`. `calib.json` measures it from the rest render: match .94/.94/.99.
2. **Face zone.** Head cells inside the face bbox are re-taken from the faceless head pass, so no baked or smeared eyes remain. One-pixel hair crumbs on face skin become skin.
3. **Placement without jitter.**
   - The whole face moves by one integer offset with hysteresis (±0.68 px).
   - eye.0 gets a residual. Every other part is placed relative to eye.0 with a wider dead band (0.85–0.97 px). Mouth and nose stay within 1 px of the eye pair.
   - Eyes share one row unless the roll is at least 5°. The row difference is up to 2 px for a roll of 10° or more, and 1 px for closed eyes.
   - Measured: relative part changes per transition are 1–2 of 8 to 15 on walk SE/E and jump SE/E, and 5–7 of 8 to 12 on S/idle/run SE, which are real roll and yaw changes. See `out/jitter.txt`.
4. **Foreshortening and turns.**
   - SE far eye: `far` → `far3` (dyaw < −11°) → hidden (< −24°). When the head turns toward the camera (> 13°, as in the idle look), the far eye opens to the full `front_right` eye.
   - S view: on a turn of 12° or more, the far eye becomes the 3/4 `far` eye.
   - Any eye whose ink would land on the silhouette slides up to 2 px toward the face centre.
   - In profile (E), the mouth is 3 px wide and set 1 px back from the muzzle edge.
5. **Occlusion.** Brows, mouth, blush and nose are drawn only on skin, so bangs may cover the brows. Eyes always win over hair, and nothing is drawn on the outline edge. The brow window cuts hair to skin only at bang tips.
6. **Expressions.** These come from M's per-frame `face`/`blink`/`mouth` keys. If those are missing, `DEFAULT_MAP` maps the motion `key` names.
   - walk: smile.
   - run: determined/effort.
   - idle: neutral with blinks and a smile on the look.
   - jump: determined → effort → joyful → surprised → squint → smile.
7. **Preview.** It is rendered with the faceless head. The same face cells are composited as 2×2 blocks at the projected anchors, with the face offset at half-pixel precision, so the face glides with the head. GIFs are 2x the preview size.

### Outputs
- `out/<act>/cmp_face_<act>_<V>_4x.gif`: round-2 chain (now faceless) | F.
- `<act>_<V>_face_4x.gif` and `board_face_<act>_<V>.png`: P2 | F | F + anchors | body.
- `cmp_preview_face_<act>_<V>.gif` and `sheet_preview_face_*`.
- `out/sheet_expr_{SE,S,E}.png`: 12 expressions plus turn variants against the master.
- `crit/strip_<act>_<V>.png`: master | round 2 baked | F | 2x body.
- All GIFs use loop=0 and frames of at least 20 ms (48 files checked).

### Open / for others
- **M:** the idle smile lasts a single frame (f06) and sits next to the f07 blink. Both critics read it as a flicker, so hold it for 2–3 frames or move the blink. Jump squint lasts 3 frames, which is OK.
- **P:** call `face_layer` after your chain (it needs `face/f_run.sh` for the same motion). These are not mine: red collar pixels over the chin in walk/run SE, a 3 px hook on the top of the head in idle SE f09, and a missing E nose bump in run E f02+ (head silhouette).
- **R:** native masking is now redundant for my pass (I swap the texture in memory). Please keep `tex_<V>_face.png`, which `face_lib build` uses through the masters.
- Next: an E-view far eye when the head turns toward the camera (use the S head-local anchor), a thinner effort mouth slit, and a 1 px margin for far-eye lashes at the cheek outline.

### F round 4 (nits, 8 directions, dash/hurt expressions)
- **Brows:** the bang pixel directly above every brow pixel becomes skin, so angled V brows keep a 1 px gap under the fringe.
- **Mouths:**
  - effort: `____/mWWm/.mm.`, a gritted slit with a dark rim. The open variant is `mWWm/.RR.`.
  - hurt: a frown, `.mm./m..m`.
  - focused: `mmm.`.
- **Far eye:** if the far eye's outer ink column has dark outline or side-lock pixels outward on 2 or more iris rows, it slides 1 px inward. This fixes walk SE f03–f05.
- **8 directions.** `face_lib.parts_for(V)` covers every view:
  - NE: blush plus 0–2 lash-tip pixels outside the cheek outline (eye_spec `ne_lash`).
  - N: none.
  - W/SW/NW: the E/SE/NE parts mirrored (`mirror_anchors`), with the iris kept unmirrored.
  - `face_lib build` writes `tex_<W|SW|NW>_nf.png` once R's mirrored textures exist.
  - `calib` falls back to the mirrored source until a native rest render exists.
- **Mirror test** (`f_mirror_test.py`, `out/mirror/*_vs_*.png`): NW is identical (0 px). SW/W differ by 5–11 px per frame, all at the iris/catchlight, as expected; closed-eye frames differ by 0.
  - The first run showed a whole-face 1 px shift on one frame. That came from the harness flipping the hi-res texture: a texel phase of exactly 4 then rounds the other way. Native renders are not affected.
- **New expressions:** `focused` (dash), `hurt`, `wince`, `hurt_tear` and `strain`. There are default maps for dash (anticipation/burst/smear/glide/skid/recover) and hurt (hit/snap/whip/hold/recover).
- **Sheets:** `out/sheet_expr_{SE,S,E,NE}.png`. The NE and N clips are in `out/{walk,idle}/` (boards, GIFs, previews).
- **Critique r3:** `crit/{opus,argon}_r3.txt`. The weak "focused" (Opus 4) was strengthened afterwards (open eyes and a short set mouth).
- `out/p2cur` is deleted, so the boards can only be rebuilt after re-running `f_pchain.sh`.

## M: round 4 (expression runs, 3/4-view lean cheat, new dash and hurt)

- **(a) Expressions last at least 2 frames.**
  - `mbuild.min_runs()` merges any 1-frame `face`/`mouth` run into its longer neighbour. It runs cyclically on loops. Blinks stay free: they are 1-frame events by design.
  - In the idle, the look-at-camera smile now spans both R-hold frames (f6 smile, f7 smile with a blink), so there is no lone smile next to the blink.
  - All main, variant and view files are rebuilt. Every face/mouth run is now at least 2 frames.
- **(b) Per-view lean cheat (`scripts/mview.py`) → `motion/view/<act>_<VIEW>.json`** for run and dash, 8 views each.
  - In the 3/4 views the forward lean points at the camera. So the lean axis is turned toward the side the character travels on screen (`lean_yaw`, cap 55°), and the lean is ×1.3.
  - Values: SE +55°, SW −55°, NE −20°, NW +20° (they use R's per-view yaws). E/W/S/N are 0°, so those files equal the main file.
  - Result: in SE the torso visibly tips toward screen-right, with the head several px ahead of the hips (`out/run_SE_lean_cheat.png`, `out/run_SE_preview_leancheat.gif`).
  - **I: render `motion/view/<act>_<V>.json` for run/dash in view V.** Other actions use `motion/<act>.json`.
- **(c) dash** (`mbody.Dash`, `motion/dash.json`, one-shot, 13 frames, in place: the game moves the sprite at `travel` up to 4.2 m/s). Timing follows ANIM_DIRECTION (smear 40 ms, holds 90–140 ms):

  | frame | ms | beat |
  |---|---|---|
  | f0 | 50 | stand |
  | f1 | 40 | anticipation |
  | f2 | 110 | anticipation hold: crouch with chest leaning back 22°, weight on the back foot, arms cocked |
  | f3 | 40 | **SMEAR 1**: stretched along travel, lean 30°, legs split 36 cm, arms swept back −72°, chest stretch +12% |
  | f4 | 50 | **SMEAR 2** |
  | f5–f6 | 80 + 80 | glide: skimming, stretched |
  | f7 | 80 | skid contact: front heel plants with toes up 22°, torso pitches back |
  | f8 | 90 | brake hold: deepest point, −7.5 cm, squash −7%, arms out for balance |
  | f9 | 120 | overshoot |
  | f10 | 120 | recover |
  | f11 | 140 | settle |
  | f12 | 250 | end |

  - The spring sim gets the in-place frame's acceleration (new `frame_acc` in `msim.step`). Hair, bow, skirt and sleeves stream back on the burst and **whip forward past rest on the brake**, then settle.
  - Smear frames carry `"smear": {"strength", "dir_world", "parts"}` for P's smear look.
  - Faces: focused → effort (smears) → focused (glide) → determined, mouth open (skid/brake) → smile (recover/end).
- **(d) hurt** (`mbody.Hurt`, `motion/hurt.json`, one-shot, 9 frames, PMD-style snap and hold):

  | frame | ms | beat |
  |---|---|---|
  | f0 | 45 | stand |
  | f1 | 45 | **HIT snap**: the head whips back first, −26° and rolled 9°, shoulders back, hips forward, arms fly up and out |
  | f2 | 130 | recoil hold (8 ticks) |
  | f3 | 80 | recoil: steps back |
  | f4 | 120 | buckle: knees give, the head drops **late** |
  | f5 | 140 | stagger: caught on the back foot, arms out |
  | f6 | 160 | recover: the head comes back last |
  | f7 | 180 | settle |
  | f8 | 250 | end |

  - Knockback is fed to the springs at reduced drag, so the hair flies up and sideways and not across the face.
  - The head stays within R's ±20° look limit (roll range 30°, i.e. ±15°).
  - Faces: pained with blink 1 (squeezed >< eyes), mouth open (hit/recoil) → wince with blink .5 (buckle/stagger) → neutral.
- 1x amplitudes (`mpx`, SE):

  | action | pelvis bob | head-top bob | tips |
  |---|---|---|---|
  | dash | 4.1 px | 7.2 px | 3–15 px |
  | hurt | 2.5 px | 4.7 px | 3–15 px |

- **Files:** `out/strip_{dash,hurt}_E_SE.png` (numbered frames with key and face), `out/{dash,hurt}_{SE,E,S}_preview.gif`, `out/dash_SE_preview_leancheat.gif`.
- **Native 8 directions (R r7):** after `face_lib build`, the rest renders and `calib`, the native W/SW/NW offsets equal the mirrored E/SE/NE ones exactly. Verified on native SW/W/NW walk/idle.
  - Bug found: R's `occ_m` of 0.0002 m hid the W eye during the idle turn, so occlusion now requires occ_m > 1 cm.
- **`focused`, final:** a 2-row lower lid, the V brow moved 1 row down so its inner end joins the lash, a short set mouth and no blush. Scores: Argon 8, Opus 6 (it is still close to determined at 1x in SE/SW, where the near brow meets the hair).
- NE/NW cheek-sliver flicker is routed to R and P (head silhouette and pixel step).
