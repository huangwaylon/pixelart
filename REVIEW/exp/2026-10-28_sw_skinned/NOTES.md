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
