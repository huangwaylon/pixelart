# Contract: skinned rig + dynamic motion (swordswoman), 2026-10-28

The owner's feedback on the rigid-parts rig H2 animations: *"body parts are not connected, the animation and poses
look stiff and unnatural. The joints look off and unnatural. Need more dynamic movement, more movement details across
the whole body, bouncing parts."*

Two people work in parallel and coordinate **only through this file and the paths below**. Each owns their own
section. Append to your own Status log, and never edit the other person's section.

- **Rigger (R)** owns `rig/` and `render/`. Builds a single connected, skinned mesh plus an armature, and a renderer
  that turns a motion file into 8x hi-res passes, pixel frames and GIFs.
- **Animator (M)** owns `motion/`. Authors the motion and simulates the secondary (spring) bones, writing
  motion files in the format below.

Root: `/Users/waylonhuang/Documents/other/pixelart/REVIEW/exp/2026-10-28_sw_skinned/`

## Skeleton (fixed names, Blender convention: .L = character's left)
**Body (FK, driven by M's keys):**
`root` (ground, carries world translation) → `pelvis` → `spine` → `chest` → `neck` → `head`.
`pelvis` → `thigh.L/R` → `shin.L/R` → `foot.L/R` → `toe.L/R`.
`chest` → `shoulder.L/R` → `upper_arm.L/R` → `forearm.L/R` → `hand.L/R`. Fingers are optional, one `hand` bone is enough at 96 px.

**Secondary chains (driven by M's spring sim; R must create and weight them):**
- `hair_front.L.1-2`, `hair_front.C.1-2`, `hair_front.R.1-2` (bangs), parented to `head`
- `hair_side.L.1-3`, `hair_side.R.1-3` (side locks), parented to `head`
- `hair_back.1-3` (back of the bob), parented to `head`
- `bun`, parented to `head`
- `bow.L.1-2`, `bow.R.1-2` (lobes), plus `bow_knot`, parented to `head`
- `sleeve.L.1-2`, `sleeve.R.1-2` (bell sleeves), parented to `forearm` / `upper_arm`
- `skirt.F|FL|L|BL|B|BR|R|FR.1-2` (8 panels around the hem), parented to `pelvis`
- `obi_tail.1-2` (only if the design has one; it may stay static)

R may add helper bones, such as twist or corrective bones, but must not rename these. If a chain is impossible, record
it in R's status log, and M will then omit it.

## Rest pose
- A relaxed rest pose: **arms down at roughly 20° from the body**, sleeves hanging, feet hip-width apart, facing +Y = the
  character's front, Z up, metres, standing on Z=0.
- R exports `rig/rest_skeleton.json`: `{bone: {head:[x,y,z], tail:[x,y,z], roll, parent}}` in world rest space.
- M reads joint positions from this file once it exists. Until then, M uses `swordswoman/v2/hy3d/rigs/H2/parts/pivots.json`
  and `skel.txt` as a stand-in.

## Motion file: `motion/<action>.json` (written by M)
```json
{"action":"walk","fps":24,"loop":true,"frames":[
  {"t":0, "root":{"loc":[x,y,z]},
   "bones":{"pelvis":{"rot":[w,x,y,z]}, "thigh.L":{"rot":[...]}, "hair_side.L.1":{"rot":[...]}, ...},
   "scale":{"head":[1,1,1]} }, ...],
 "timing_ms":[...per frame display time...], "notes":"..."}
```
- `rot` is a quaternion, local to the bone's own rest orientation (Blender pose-bone `rotation_quaternion` semantics).
- `root.loc` is world space, in metres. For loops, M keeps it in place (no forward drift); a stride is foot-plant only.
- `scale` is optional, for squash and stretch. Use it sparingly and only on pelvis, spine, chest and head.
- The secondary bones are already simulated (baked) in the file, so R's renderer just plays the file.

## Render command (provided by R; M may call it to preview their own motion)
`<blender> -b rig/rig.blend -P render/render_motion.py -- motion/<action>.json <view> <outdir> [--preview]`
- `--preview` renders fast smooth-shaded frames at 2x for checking motion.
- The full render produces 8x passes (cel + outline + matid), the pixel chain (E2 k-centroid, palette lock, fix), a GIF at 4x,
  and a contact sheet.
- Views: SE first, then E and S. The camera is the game camera: 30° elevation, orthographic, 128 px cell, PPU 26.304,
  the same as rig H2 / `v2/g96`.

## Status log (R)
- (R writes here)
- 12:00 R: **`rig/rest_skeleton.json` is up** (63 bones; all contract names). Frame exactly as contract: metres, +Y = her front, Z up, soles z=0,
  .L = her left = **-X**. Scale: 1 H2 unit = 0.775 m (figure ~1.55 m incl. bun; hip z 0.685, knee 0.368, ankle 0.068, shoulder 0.96, head bone 1.108->1.434).
  Each bone has head/tail/roll/parent plus `matrix` = 3x3 rest orientation in world (rows; **columns = local X,Y,Z axes**; Y = head->tail).
  Roll convention: local Z points to her front (+Y) for body/limbs/hair/sleeves; foot/toe/root/bow bones: local Z = up; skirt panels: local Z = outward radial.
  So for legs/spine, +rot about local X = flex. Rest pose = arms down 26 deg from vertical, slight elbow bend, feet hip-width.
  Chains: hair_front.L/C/R.1-2, hair_side.L/R.1-3 (front side locks to the shoulders), hair_back.1-3 (the bow ribbon tails ride on hair_back.2-3),
  bun, bow_knot + bow.L/R.1-2, sleeve.L/R.1-2 (parent forearm.*; sleeve.1 head at the elbow), skirt.F|FL|L|BL|B|BR|R|FR.1-2 (parent pelvis).
  Helper: shoulder.L/R are real deform bones (chest -> shoulder -> upper_arm). **obi_tail omitted** (design has a plain obi, no tail).
  Positions may still shift by a few mm while I QA weights; names/parents/rolls are final.

- 12:25 R: **`rig/rig.blend` + `render/render_motion.py` work** (contract CLI). Extra flags: `--stamp` (m96 neutral head paste),
  `--frames=a:b`, `--no-post`; env `PVS=<n>` preview scale (default 2). Motion name `rest` = identity pose. Outputs in <outdir>:
  `<act>_<view>_preview.gif` + `_preview_sheet.png` (preview) or `<act>_<view>_4x.gif`, `_sheet.png`, `_px/fNN.txt|png` (full; ~1.5 s/frame).
  Your walk.json plays fine (preview: render/out/test/walk_SE_preview.gif). Deformation QA: rig/qa/st2_sheet.png.
  Notes for M: root.loc is applied as an absolute world position of the root bone; unspecified bones = identity; `scale` applied as pose scale.

- 12:50 R: rig v2 (skeleton unchanged): hair-chain weights fade to 0 at the hair|skin boundary (no forehead tear), sharper skirt
  panels, sleeve/obi no longer fused (clean 120 deg arm raise), preview uses palette colours. All 4 of your files rendered SE/E/S
  preview + full (+head stamp) -> render/out/<act>/; H2 vs skinned comparison render/out/compare_<act>_SE.gif. Limits for M
  (geometry is surface-painted on the H2 head): **hair_front <= 15 deg**, hair_side/back <= 30, **bow.*.1 <= 25 deg** (lobes splay to
  "horns" beyond), skirt panels <= 35 (the rig couples only the hem ring around each thigh; please drive skirt.F/B a bit from thigh
  swing so stride legs don't press through the side panels). Opus rig critique: crit/opus_rig.txt (connectivity 7, deformation 5).

- 13:10 R: rig v3: hands 1.3x (they pixelized to detached 1-2 px). **Only change to rest_skeleton.json: hand.L/R tail ~1.2 cm longer**
  (head unchanged). New optional render flag `--yaw=<deg>` (whole-rig turn, view cheat; default 0). Re-rendering all your files now.

- 13:25 R: DONE for this round. Final renders of walk/idle/run/jump x SE/E/S (preview + full + stamp) in render/out/<act>/,
  comparisons render/out/compare_*.gif, NOTES.md (R section), hub entry REVIEW/entries/2026-10-28_sw_skinned_rig.json. Re-render
  any updated motion with `render/render_all.sh "<acts>" "SE E S"` (then `render/compare_h2.py <act> SE`).

- 13:45 R: **rig r4: mirror fix**. sleeve.L/R.1-2 and hair_side.L/R.* (and all other .L/.R pairs) are now exactly mirror-symmetric
  about x=0 (error 0). Root cause: the sleeve loft/bone "back" axis flipped sign per side, so the L bag sat forward. The sleeve geometry
  and weights were fixed the same way. The sleeve chain now hangs back (-Y) on both sides. Also: legs thicker (knee r 50->57 mm in H2 units,
  boots +12%), hands bigger (a 3x3 px blob at 1x), **SE default yaw -15 deg** (best 3/4 match to EC0_SE_96; `--yaw=0` restores the true camera).
  rest_skeleton.json changed for sleeve.* (up to 132 mm), hair_side/hair_front .L/.R (mirror averaged) and hand tails. I re-baked all 4 actions
  with your mbuild.py --noprev (run seam is now 3.8 mm) and ran final.sh. The ab_*_SE_old_vs_new.png boards were rebuilt with render/ab_board.py.
  Pre-r4 motion and pxeval copies are in motion/out/pre_r4/.

- 18:20 R: **ROUND 2 rig (r5) is in rig/rig.blend + rig/rest_skeleton.json.**
  - **Head = the rig's own animatable head that carries the master pixels.** rig/head_hull.py builds a visual hull from the m96 head stamps
    (S, SE, E, NE, N + mirrored SW/W/NW; reprojection IoU vs the master masks S .95, SE .88, E .88, NE .85, N .90). It is fused into the
    body mesh, and hair/bow/bun materials come from the master colours. Each view's master (rig/tex/tex_<V>.png) is camera-projected
    onto the head + side locks (UV `pj_<V>`, visibility mask `pm_<V>`). New 8x pass **`tex`** = projected master pixels (exact palette
    colours, 1 sample, alpha = head mask). It deforms with head / hair_* / bow* / bun, so turns and tilts up to +-20 deg keep the master look
    (QA rig/qa/r2_stress_SE.png). **`--stamp` is retired**: the pixel step should take head cells from `tex` (helper: `render/r_tex_head.py`,
    tex_head(T, g) = per-cell majority tex colour -> palette char). My QA-only chain render/r_qa_chain.py = r1 chain + tex head.
  - **Per-view yaw now comes from rig/align.json** (SE -10, NE -25, others 0, fitted against the masters; it also holds the fixed dx/dy
    alignment per view). info json has "yaw" and "tex" now (P request b).
  - **Limb IDs:** new 8x pass **`lid`** (flat, AA off): her-left leg red (255,0,0), right leg green (0,255,0), left arm+sleeve+hand blue
    (0,0,255), right arm yellow (255,255,0), rest black. `guide` matid colours unchanged (= hx.MATS). P: use it or keep your part pass.
  - **Legs:** fuller thighs (r +8%) and hips (skirt +3%). Thigh centres are spread so there is a >= 3 cm gap below the hem (no inner-thigh
    fusion on a narrow track). The skin band is wider (sock top 0.622 H2 units = 0.482 m) and the red sock-top band is 2 cm.
  - **Posture:** shoulders 6 mm back and down. The spine and neck bones are vertical (upright). Stress QA covers contrapposto,
    hip sway, pointed toes and close soft knees (rig/qa/r2_stress_SE.png).
  - **Skeleton changes for M:** hair_front.* (fringe now ends at the brows), hair_back.1-3, bow_knot / bow.*.1-2 (bow on the back-top of
    the head), bun, hair_side.*.1 head, arms +6 mm. **Please re-bake against the new rest_skeleton.json.** Body bones are unchanged.
    Limits stay: hair_front <= 14, hair_side <= 22, hair_back <= 28, bow <= 24, bun <= 16 deg; head turn/tilt <= +-20 deg keeps the master look.

- 18:50 R: rendered all 4 actions x SE/E/S on M's 18:35 bake (against the r5 skeleton): 8x passes incl. tex/lid, previews and my QA chain
  are in render/out/r2/<act>/. Round 1 vs round 2 side-by-sides: render/out/r2/compare_<act>_SE.gif and compare_walk_{E,S}.gif (they include P's
  chain column when render/out/p2 exists). When M posts the final round-2 motion, re-run `render/r2_all.sh` then `render/r2_compare.py <act> <view>`.

## Status log (M)
- (M writes here)
- 2026-10-28 11:50 M: started. Building `motion/scripts/` (FK + analytic 2-bone leg IK + spring sim + own capsule preview). Until `rig/rest_skeleton.json` exists I use a stand-in `motion/standin_skeleton.json` (H2 armature joints rotated to face +Y, so .L = -X, plus guessed secondary chains). Assumptions about R's file: armature object at identity, `roll` = EditBone.roll in radians, bone rest matrix = Blender vec_roll_to_mat3(tail-head, roll); `rot` = pose rotation_quaternion with L = B^-1 * r * B. I will NOT scale pelvis (Blender inherit_scale would shrink the legs); scale only on spine/chest/head, small (0.96..1.04).
- 12:05 M (clock fix: earlier entry said 12:25): switched to R's `rig/rest_skeleton.json` (my vec_roll_to_mat3 reproduces R's `matrix` for all 63 bones, err < 1e-3). First bake of `motion/walk.json` (8 fr, 105 ms), `run.json` (8 fr, 70 ms), `idle.json` (12 fr, holds), `jump.json` (14 fr one-shot) is on disk; files are in-place (root.loc = bob/sway only), secondary chains baked; extra top-level keys `travel_m_per_s`, `cycle_s`, `seam_mm`, per-frame `key` (pose name) are informational. Critique round 1 running on my capsule preview. R: when `render/render_motion.py` works I'll switch to `--preview`.
- 12:30 M: motion r3 baked (walk/run/idle/jump). Using `render_motion.py --preview` for all critique boards now (thanks). Respecting your limits:
  hair_front <= 14 deg, hair_side <= 22, hair_back <= 28, **bow.* <= 24**, skirt <= 34; skirt.* panels are now driven by thigh flexion
  (front panels follow forward thigh swing, back panels extension, 0.55 gain) + capsule collision vs thighs/pelvis.
  **Rig issue for R:** rest skeleton is asymmetric in the sleeves: sleeve.L.1 tail y=+0.050 / sleeve.L.2 tail y=+0.086 (forward) vs
  sleeve.R.1 y=-0.025 / sleeve.R.2 y=-0.043 (backward) -> 75/129 mm mirror error; also hair_side.L.1 head x=-0.174 vs R +0.189 (14 mm).
  Critics see "sleeves flare on one half of the cycle only". Please mirror them if it's not intentional (I read positions from the file, no change needed on my side).
  Also: Opus sees skin gaps/creases at the sock tops (thigh band) in idle f4-f5 / f9-f11 (free knee bent ~15-20 deg, heel lifted).
- 13:10 M: **final motion files are on disk**: `motion/{walk,run,idle,jump}.json`, baked 13:02. I won't change them further unless the owner asks.
  Outputs are in `motion/out/` (pixel GIFs with stamp, SE/E/S previews, old|new comparisons, pxeval) and documented in NOTES.md (M section).
  Hub entry: REVIEW/entries/2026-10-28_sw_skinned_motion.json.
  If you mirror the sleeve and hair_side bones, I can re-bake. `swordswoman/.venv/bin/python motion/scripts/mbuild.py <act> --noprev` takes about 10 s per action, then run `zsh motion/scripts/final.sh`.

---
- 18:55 M: **ROUND 2 motion re-baked against r5** (`motion/{walk,run,idle,jump}.json`; round 1 copies are in `motion/round1/`).
  - 1x amplitudes are checked with `motion/scripts/mpx.py`: every part moves >= 1 px or holds. Walk pelvis bob 3.1 px, run 3.9 px. Head roll/nod: walk 15/6 deg p-p, run 15/9. Spring tips >= 2 px.
  - Timing has holds: walk 90/120/90/120 ms, run 60/80/60/80 ms.
  - Posing is elegant and upright per the addendum. The idle right hand rests at the obi.
  - Your r5 limits are respected; I use align.json yaw.
  - P: the walk legs overlap in SE at passing and contact R (narrow track, 0 px screen gap), so please separate them.
  - Renders of my motion are in motion/prev/r2 (my copy of your chain call).

# ROUND 2 (2026-10-28, owner feedback on round 1)
> "Gradual improvements. Limbs like legs sometimes flicker and disappear. I need movement in the whole body including the
> head, hair should move, need animated movements, not stiff. I still see disconnected parts like legs, thighs."

Lead diagnosis (from render/out/walk/walk_SE_px_hs + walk_SE_px, at 4x):
1. **Legs vanish** (f00/f03/f07): the feet track on one line, so the legs cross in the SE view. Both are flat black sock, so an overlapping leg merges into one shape. The pixel chain can also drop limbs thinner than about 2 px.
2. **Disconnected legs/thighs:** the skirt goes straight into black socks with almost no thigh mass or skin band. Dark sock against the dark outline leaves no interior form, so the legs read as detached sticks.
3. **Head and hair frozen:** the `--stamp` paste (rigid master head) hides all head and hair motion. The rig's own head is unusable.
4. **Sub-pixel motion reads as flicker, not motion.** Every motion must be either ≥ 1 px at 1x or held.

## Round 2 owners
- **R (rigger)**: owns `rig/`.
  - **Head:** a real animatable head that looks like the master. Hair, bangs, side locks, bun and bow geometry are modelled to the m96 masters' silhouettes per view. Project each view's master head pixels as a texture onto the head mesh (camera projection per view, so SE/E/S each use their own master; handle the back and N later). Hair/bow/bun then deform with their spring bones, and the head can tilt and turn about ±20° while keeping the master's face and hair look. `--stamp` gets retired.
  - **Legs:** fuller thighs/hips (chibi), a visible skin band between hem and sock top that follows the design, and the sock top band.
  - **Materials:** split near/far legs into separable materials or IDs (`leg_near` / `leg_far` per view, or a left/right ID) so the pixel chain can separate them.
- **P (pixel engineer, new)**: owns `render/pixel_chain.py` and the post-process in `render/` (R hands over the pixel step; the Blender render stays R's).
  - **Limb protection:** a minimum 2 px width for limbs, legs never dropped.
  - **Overlap separation:** a 1 px separating line or shade step between overlapping same-material limbs, with the far limb one shade darker.
  - **Sock form:** a 2-tone sock with a lit edge.
  - **Temporal stability:** reuse the previous frame's pixels where the guide didn't move, snap parts to whole pixels, kill shade swaps.
  - **Gates:** pxeval gates (boil ≤ .02, shade swap ≤ .015, no FEET_JITTER).
- **M (animator)**: owns `motion/`.
  - **Amplitude for 1x:** pelvis bob 2–3 px in walk and 3–4 px in run, head bob plus tilt (±6–10°), and visible hair, bow, bun and skirt bounce of ≥ 2 px at the tips.
  - **Legs:** wider foot track (hip-width, never crossing), clear arm swing that shows outside the sleeves (hands visible).
  - **Head:** head turns and tilts with overlap.
  - **Timing:** snappier timing with holds on the key poses. Re-tune the springs within R's new limits.
## Status log (P)
- (P writes here)
- 17:40 P: started; I own `render/pixel_chain.py` now (round-1 chain kept as `render/pixel_chain_r1.py`, still used for `--preview`).
  New chain = material/ID vote (no k-centroid): matid x **part ID** -> 2 px limb guarantee, outline outside the fill, far-side overlap lines,
  sock/skin-band shading, temporal hysteresis. **Part IDs come from my own extra pass** `render/p_parts.py` (runs R's render_motion.py with
  KINDS=guide after setting a vertex colour = dominant deform bone; same camera/pose/yaw; writes `<outdir>/parts/*_part.png` + `bones.json`).
  So **R: no native leg_near/leg_far ID is needed** as long as the vertex-group names stay as in the contract. Please (a) keep the `guide`
  matid colours = hx.MATS or tell me the new ones here, (b) add `"yaw"` to the `<stem>.json` info so my part pass matches non-default yaws.
  End-to-end: `render/p2_run.sh "<acts>" "<views>"` -> render/out/p2/<act>/ (renders passes + parts together, so a rig/motion update can't
  desync them). render_motion.py's post stage calls the new chain unchanged (it auto-renders the part pass if missing).
- 21:00 P: **P2 pixel chain done** on r5 + M's 18:35 bake, walk/run/idle/jump x SE/E/S -> render/out/p2/<act>/ (boards, cmp GIFs, 1x strips),
  pxeval render/out/p2/pxeval/table.md, NOTES.md (P section). Uses R's `tex` head (texel-phase aligned) + rig/align.json; my own part/rest-position
  passes (render/p_parts.py) instead of `lid` (finer: per bone + skirt/sleeve/head, plus exact surface correspondence for temporal locking).
  Opus 6.5 vs r1 4.5, Argon 7.2 vs 3.4: legs never vanish, thighs connected. Gates: boil passes on walk SE/S and idle; shade_swap fails everywhere.
  74 % of the swaps are on surfaces moving > 2.5 px/frame, and the dark palette keys sit within dE 12 of each other.
  **Requests -> M:** 12-frame walk/run or holds on the passing poses, and quantised head turn/tilt (hold >= 2 frames), which removes the tex-head
  resample swaps (~.01). **-> R:** in walk SE f04/f05 the forward sole reaches row 128.6, so it is clipped at the cell bottom with dy=1.
  FEET_JITTER in SE/E is real 30-degree perspective of the stride (~7 px), not jitter.

## ROUND 2 addendum: posing direction (owner, 2026-10-28)
> "I want more elegant posing during the different actions. Not slouched, needs to be confident, feminine."

This applies to M (poses and keys), with R (rest pose) and P (readability) supporting.
- **Posture.** Upright spine, chest lifted, shoulders back and down (never hunched forward), long neck, chin level or slightly up.
  There is no forward slouch in any action. Run lean comes from the hips and ankles with a straight back, kept under about 8°.
- **Hips.** Contrapposto in idle: weight on one leg, a gentle hip tilt and shift, the free knee relaxed inward, and shoulders counter-tilted.
  Walk gets a feminine hip sway, with a hip roll of about 4–6° and pelvis yaw.
- **Legs.** A narrower, graceful track: the feet land close to the midline but **never cross**, and P separates overlaps. Knees stay soft and close,
  with toes slightly turned out or pointed when off the ground. Steps are light (heel-toe with a lift), not stompy.
- **Arms and hands.** Elbows soft and close to the body, a light, graceful swing (forearm leads, wrist trails), and relaxed hands with soft
  wrists. No stiff straight arms or flapping. In the idle, one hand may rest near the obi or the skirt.
- **Head.** Confident carriage, with small bright tilts on accents, the head leading turns slightly, and hair and bow reacting.
- **Per action:**
  - **Idle:** contrapposto + breathing + a weight shift.
  - **Walk:** poised and bouncy, like a model walk in chibi proportions.
  - **Run:** light and springy, upright, arms bent at about 90° with an elegant swing.
  - **Jump:** a graceful arc, with the body arched or extended at the apex, toes pointed, knees together on the tuck, and a soft land with a settle.
- **Silhouette check.** Each key pose must read as confident and feminine at 1x (96 px). M includes a key-pose silhouette sheet (solid fill) per action for review.

---
# ROUND 3 (2026-10-28, owner feedback on round 2)
> "The faces are all messed up. The faces need to follow the head's movements. Make sure to follow the 3D model as reference.
> The faces need to be more expressive depending on the action." · "Make sure the GIFs run and loop smoothly." · "Test different
> timings and lengths for the animation depending on the action. We want more expression, bouncy, liveliness." · "Check limbs." ·
> "Run E smooth preview: the run posture is very stiff and awkward. Maybe more leaning forward and more natural movement."

Owners and tasks:
- **F (face artist, new)** owns `face/`.
  - **Face system on 3D head anchors.** This is the proven snowpeak approach (`pipeline/face.py`: hand-designed pixel decals on 3D head anchors). Eyes, brows, mouth and blush are pixel parts drawn to the m96 face spec (`swordswoman/v2/m96/FACE_SPEC.md`, `eye_spec.json`, stamps in `v2/m96/heads/`). They are placed per frame from the 3D head's projected face anchors (R provides them) and follow head yaw, pitch and roll: spacing compresses with yaw, the far eye narrows, and the parts shift with tilt.
  - **Expression library** keyed by name: neutral, smile, joyful, determined, effort, surprised, blink, half-blink, squint (land), wink (optional), mouth open/closed variants.
  - **Works in both outputs:** the pixel frames, and the smooth preview, where the face is shown as textured decals or a composite.
  - **Coordination:** the projected-texture face is replaced. R masks the face region out of the projection, and F hands P a `face_layer` call.
- **M (animator)** owns `motion/`.
  - **Run rework (E preview called stiff/awkward):** a confident forward lean of about 12–18° from the ankles and hips with the chest still lifted and the head up looking ahead. This is not a slouch; it overrides the earlier "under 8°". Natural mechanics: knee drive, heel kick-back, a flight phase, arms pumping from the shoulder with elbows at about 90°, counter-rotation, bounce.
  - **Timing/length variants per action**, rendered side by side for the owner to pick:
    - walk: 6 / 8 / 10 / 12 frames
    - run: 6 / 8 / 10
    - idle: 8 / 12 / 16 with different holds
    - jump: short vs long anticipation and hang
    Each variant gets at least two timing feels, such as snappy holds vs even.
  - **Expression track:** a per-frame `"face": "<expression>"` key, plus `"blink"` cues, chosen per action beat (run = determined/effort, jump = joyful at the apex and squint on the land, walk = smile, idle = neutral with blinks and an occasional smile).
  - **Fixes:** remove the forward head in the idle settle and the jump fall. Act on P's requests: holds on the passing poses, and head turns held at least 2 frames.
  - **Comparison GIFs:** every frame at least 20 ms (browsers clamp shorter frames to 100 ms). Merge or resample instead of emitting 10 ms frames.
- **P (pixel engineer)** owns `render/pixel_chain.py` and the post-process.
  - **Limb audit** per frame: each limb (both arms, hands and legs) is one connected component, at least 2 px wide, and attached to the body, never floating or detached. Make it a gate and a report.
  - **Shape fixes:** the skirt is A-line rather than a tent, the hem has no stair-step corners, the skin band holds a stable size, and boot toes are rounded.
  - **Integration:** F's face layer.
  - **GIF writer:** loop=0, all frames at least 20 ms, a seamless loop seam (last→first diff in line with in-cycle diffs), and the right disposal, with no ghosting.
- **R (rigger)** owns `rig/`.
  - **Face anchors:** empties or bones on the head for `eye.L`, `eye.R`, `brow.L/R`, `mouth` and `cheek.L/R`, written per frame (projected 2D at 1x plus depth and facing) into the render info.
  - **Masking:** take the face region out of the master projection (F supplies the face).
  - **Cell clipping:** fix the sole being clipped at the cell bottom (walk SE f04/f05).
  - **Skirt:** an A-line skirt shape that's less tent-like.

All four commit nothing. The lead commits and pushes. Each owner logs in their status section below.

## Status log (F)
- (F writes here)
