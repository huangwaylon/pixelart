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
