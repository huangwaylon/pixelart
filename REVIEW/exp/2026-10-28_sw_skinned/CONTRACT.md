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

- 19:40 R: **ROUND 3 rig (r6)**: rig.blend, rest_skeleton.json (bones unchanged vs r5), align.json, rig/tex/, rig/face_anchors.json.
  - **Face anchors (for F).** There are 7 anchors: eye.L/R, brow.L/R, mouth, cheek.L/R (.L = her left). Each is triangulated from the m96 master anchors
    (anchor.json) in S+SE+E (reprojection error <= 1 px, except that the SE far eye/cheek sit 3 px higher than the master draws them; the master
    draws both eyes on one row) and mirror-symmetrised. Each one is an empty `face.<name>` parented to the head bone in rig.blend, and the rest data is in rig/face_anchors.json.
    **render_motion.py writes them per frame** into `<stem>.json` -> `frames[i].face` (+ `rest_face`):
    `{name: {px: [x, y] = 1x coords in the 128 game cell INCLUDING the output placement dx/dy (= the pixel frame), px192, depth_m, facing
    (normal . toward camera), occ_m, visible}, _head: {yaw, pitch, roll (deg vs rest, camera axes: yaw + = face turns toward screen right,
    pitch + = chin down, roll + = top tilts toward screen left), centre_px}}`. `visible` = facing > 0.05 and not occluded by body/arms/hands
    (head self-occlusion is left to facing). QA overlay: rig/qa/r3_anchors_SE.png (green = visible, red = hidden).
  - **Face masked out of the projection**: rig/tex/tex_<V>.png have the eye blocks (incl. brows), the mouth block and the blush cleared to
    skin `s`. Bangs, side hair, the head outline and the nose stay. Masks: rig/tex/face_mask_<V>.png; unmasked: tex_<V>_face.png. The `tex` pass now shows a blank face.
  - **Sole clipping fixed via placement (P please note):** rig/align.json `dx/dy` are now the OUTPUT placement, lifted vs the master
    registration (`reg_dx/reg_dy`, used only for the hull/projection) by `lift_px`: S 4, SE 3, E 1, NE 2, N 2. New extents on the 18:35 bake:
    walk SE lowest row 124 (was 128.8), run S <= 127.8. The jump apex then reaches the cell top in S/SE (bow tip, <= 1 px).
    For jumps I recommend exporting root height as a per-frame offset instead of moving it inside the cell.
  - **Skirt:** an A-line (flares over the hips, then the sides run nearly straight to a 0.192 hem; was a straight 0.141 -> 0.205 cone). The skirt bones follow the new shape.

- 20:40 R: **ROUND 4 rig (r7) landed** (I: please re-render). Bones unchanged vs r6 apart from the skirt.*.1/2 positions, which follow the narrower hem.
  - **8 directions natively**: render_motion.py renders S SE E NE N NW W SW with real camera azimuths. rig/align.json has all 8. SW/W/NW mirror
    SE/E/NE: dx -> -dx, yaw -> -yaw (SW +10, NW +25). Feet check vs the flipped masters: 0 px off in x, dy = -lift exactly (rig/qa/r4_rest_8dir.png).
  - **Head projection for all 8 views**: UV `pj_<V>` + mask `pm_<V>` for the 8 views. N/NE come from EC0_N/NE_96; SW/W/NW use the horizontally flipped
    SE/E/NE masters (rig/tex/tex_{SW,W,NW}.png, plus face masks; the bow, bun and ribbons are centred, so the flip is correct). The face is still masked out for F.
  - **Skirt**: hem narrowed to .180 (was .192) with straight A-line sides, plus side-seam grooves (4.5 % at the hem) so the front and back
    panels read separately. Inner thighs are slimmer (outer volume kept) and the hem gap between the legs is about 3 px. The remaining 1x "tent" in walk f3-f6 is the
    skirt springs flaring the panels outward. **M:** cap the outward skirt swing at about 15 deg or lower the gain (side panels first).
  - **E nose bump**: an explicit nose blob on the midline at the master's E bump (now in the geometry, so it survives head motion).
  - **Red collar over the chin**: the head stamps included the kimono collar, which became hull geometry and moved with the head. It is removed from the head
    masks (dress-red pixels below the mouth row) and the hull is rebuilt; no red over the chin in walk/run SE now (rig/qa/r4_walk_run_SE.png).

- 01:10 R: **ROUND 5 rig (r8b) landed: real 3D head, no projection.** (M: please re-bake; I: re-render.)
  - **No projection or stamp:** the `tex` pass is gone (render_motion skips it: there are no pj_ UVs). rig/tex/ stays only as the archived A/B baseline.
  - **3D head (rig/build_head3d.py):** the m96 visual hull is now just the silhouette reference.
    - SKULL = fitted cranium + face/cheeks/jaw, with a natural forehead sloping into the cranium. It is fused into the body.
      Scalp = hair colour, so no skin shows between clumps or at the parting.
    - HAIR = a separate attached shell (bob, crown, back hair, bun) + a **full fringe lying on the forehead**: thick, even clumps 2.5 px wide.
      Tips are at about master row 47 in S (measured 47-48; F asked for 46.5), with notches where the brows peek through.
      The master's bang overhang ("visor") and the side-hair curtain in front of the cheeks are removed, so the profile face shows in E/W.
    - Side locks frame the face to the chin. The **bow is modelled** (knot + 2 lobes + 2 ribbon tails) on bow_knot/bow.*/hair_back.*.
  - **Face (with F):** UV `face_uv` = front planar (u = 0.5 + x/0.44 her left = image right, v = (z - 1.38)/0.44, H2 units) on the skull.
    `fmask` = all front skin from the chin up to under the fringe (F's request). F's face/tex3d/ textures are live:
    `<face>[_blink|_half][_open].png` (matid-coded, alpha 0 = base skin) + `_col.png` for the preview. They are switched **per frame inside the render** from M's
    `face`/`blink`/`mouth` keys (render_motion.face_tex(); the chosen file is written to info frames[i].face_tex). My placeholders (rig/face_tex/) are only a fallback.
  - **guide pass** is now EEVEE emission at 1 sample (exact colours): vertex matid colours + face texture mats. **P:** the matids are hx.MATS + rig/face_mats.json
    "mats" (eye_white, iris, lash, mouth, blush + F's iris_top, iris_low, brow, mouth_in, nose); treat them as ordinary materials. The `lid` pass is unchanged.
  - **Stance / head:** the spine is vertical and natural (no arch). The neck angles about 9 deg forward from the chest. The head bone and mesh sit forward of the
    neck (E-profile gate: head centre y +0.015 m >= neck base y -0.005 m). rest_skeleton.json: neck/head and all hair/bow/bun bones changed.
  - QA: rig/qa/r5_head_QA.png (8-dir rest at 4x + 1x; SE/S/E head tilt +-15, nod, turn 20, bangs/side/back/bun/bow at the spring limits, blink;
    R's QA chain = r1 chain + face mats as ordinary materials).

- 01:55 R: **rig r8c (round-5 follow-up)** (I: re-render; M: the bone changes are tiny (locks, bow lobes), a re-bake is optional; F: please re-run the UV fit, the fmask is wider).
  - **Profile faces:** the side bob now starts behind the cheek line (curtain cut at y > -0.02 for |x| >= 0.19) and the face slab reaches y < -0.02. Side locks
    moved back to y -0.03 (behind the cheek). `fmask` now also covers the cheek sides (normal_y < 0.35), so F's eye, cheek and nose land in profile.
    E rest shows the eye, cheek and nose (rig/qa/r5c_head_QA.png, S/SE/E/NE + head poses vs the masters).
  - **Bow:** the lobes have volume (0.07-0.12 deep) and angle back with level tips, so they read as a bow knot edge-on instead of red horns.
  - **Hair surface:** the hair shell is Taubin-smoothed (14 x lambda/mu, volume kept) on top of the sigma 1.2 voxel surface, which gives fewer lumps and calmer cel bands.
  - **Iris ramp:** rig/face_mats.json now has "ramps" (dark/base/light per face mat): iris_top hhh, iris hgg, iris_low gLL, eye_white WWW, lash KKK, brow ggg,
    mouth mmm, mouth_in RRR, blush kkk, nose SSS. The m96 iris is brown-grey (h/g/L) by design, so P should use these keys and not the hair/skin ramps.

- 02:40 R: **rig r8e (round-5 head rebalance + anime face plane).** **F: please re-run face/f3d/f3d_calib.sh** (face surface and fmask changed; UV formula unchanged).
  I: re-render. M: hair_back/bun/bow bones moved forward slightly, a re-bake is optional.
  - **Profile balance:** the back-of-head hair depth (incl. the bun overhang) is compressed toward the head (y' = .06 + (y - .06) * 0.62 for y > .06;
    the front views keep their silhouette and the bangs stay). Head-silhouette centre minus neck base (1x px, + = toward her front):
    E/W rest -2.7 -> -0.7, walk E -0.1..+0.7 (before about -2.0 on average), NE -2.1 -> -0.1. Sheets: rig/qa/r8d_profile_QA.png (E/W/NE rest + walk, before/after,
    yellow = silhouette centre, cyan = neck base), numbers in rig/qa/r8d_profile.json.
  - **Anime face plane (F's request):** the face front is a superellipse across x (y = yf(z) + 0.20 (|x|/0.218)^3.2): flat between the eyes,
    wrapping back at the outer eyes and cheeks, so E/W see the outer eye, cheek and mouth. There is a slight lip bump and the midline profile keeps the nose blob.
    The old hull corner in front of the face plane is removed. S/SE stay frontal (rig/qa/r8e_QA.png: master | before | after for S/SE/E/W + walk SE/E, 4x + 1x).
  - **Face dark band:** dark-skin (S) share of the head skin cells in my QA chain: E .115 -> .08, SE .027 -> .026, walk E .07-.13, but S .074 -> .14
    (cheek wrap; masters .00-.03). **P:** with this geometry the face needs the skin ramp's dark threshold lower (or the face mats + skin
    biased up a little) so the face sits in s, like the masters. Lighting stays global (no face special case).
  - **F, seen in W rest:** her left eye (eye.L, u = 0.72) doesn't show in W while eye.R shows in E. The texture seems to draw eye.L as the SE "far" eye; W needs it as a near eye.

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
- 21:55 M (ROUND 3): **expression track for F.** Every frame in `motion/<act>.json` and `motion/variants/*.json` now has
  `"face": <name>`, `"blink": 0 | 0.5 | 1` (0 = open, 0.5 = half, 1 = closed) and `"mouth": "open" | "closed"`, chosen per beat:
  - walk: smile
  - run: determined on contact/flight, effort with mouth open on down/push-off
  - idle: neutral, blink = 1 on the two blink-hold frames, smile while looking at the camera
  - jump: neutral → determined (anticipation/crouch) → effort, open (launch) → joyful, open (rise/apex) → surprised (fall) → squint, blink .5 (land/squash) → smile (recover/end)
  Head turn/tilt is held for 2 frames in idle (and in walk at 10/12 frames), per P.
  Run reworked: 15 deg lean from hips and ankles, chest lifted, head up.
  Timing/length variants: `motion/variants/` (24 files; the `variant` key has n/feel/T).
- 22:40 M (ROUND 3) DONE. Final files: motion/{walk,run,idle,jump}.json (run reworked) and motion/variants/*.json (24 timing/length variants).
  - The variant grids for the owner to pick from are in motion/out/grid_*.gif (hub entry 2026-10-28_sw_skinned_timing_variants).
  - All my GIFs use frames >= 20 ms.
  - pxeval: boil passes for walk 8/10/12 and idle; it fails for run (.05-.12) and jump (.075). shade_swap fails everywhere, so that one is P's.
  - F: the expression track is in every frame (face/blink/mouth); see my 21:55 entry.
- 23:30 M (ROUND 4) DONE.
  - **Expression runs:** face/mouth changes now last >= 2 frames in every file (the idle look-smile spans f6-f7, with the blink on f7). Blinks are 1-frame by design.
  - **New actions:** `motion/dash.json` (13 frames: anticipation lean-back hold, 2 SMEAR frames at 40/50 ms, glide, skid, brake hold, recover) and `motion/hurt.json` (9 frames: snap 45 ms, recoil hold 130 ms, buckle, stagger, recover). Both carry expression cues (face/blink/mouth).
  - **P:** smear frames have `"smear": {strength 1.0/0.6, dir_world [0,1,0], parts}`.
  - **I:** for run and dash, render **`motion/view/<act>_<VIEW>.json` in view VIEW**. These hold the 3/4-view lean cheat: SE +55 deg, SW -55, NE -20, NW +20, the others 0. All other actions use `motion/<act>.json`.
    - In-place travel speeds: dash peaks at 4.2 m/s (field `travel` per beat is in mbody.Dash.travel); hurt knockback is -1.6 m/s.
  - **F:** new faces used are focused, effort, determined, pained (blink 1 = ><), wince (blink .5).
  - Variants rebuilt with the min-run rule.
- 07:55 M (ROUND 5) DONE. Re-baked against r8b: 6 main (`motion/*.json`), 16 view (`motion/view/`), 24 variants. I: please re-render.
  - **Stance:** natural forward torso, head level to slightly down, sitting forward of the neck. Gate `motion/scripts/mgate.py` PASS on all 46 files (E profile, every frame):

    | action | torso (deg) | head pitch (deg) | head ahead of neck base (cm) |
    |---|---|---|---|
    | walk | +3.0..+3.6 | 0..+4 | +3.0..+4.3 |
    | idle | +0.3..+1.3 | 0..+2 | +2.6..+3.7 |
    | run | +12..+14 | 0..+8 | +3.8..+6.7 |
    | jump | 0..+12 | — | — |
    | dash anticipation | -8.5 | — | — |
    | hurt recoil | -18.6 (allowed) | — | — |

    Head pitch is >= 0 and the head centre >= neck base in every action.
  - **Walk** uses the Bandai walk_feminine mocap amplitudes as its baseline.
  - **Skirt:** radial cap 15 deg (front/back 26), gain 1.7. Walk SE hem +3.8 -> +2.5 px. The rest of the "tent" is the bell sleeves.
  - **Critic:** Opus 7/7 and Argon 7/8 (stance/motion).
  - **R:** Opus says the back-hair volume makes the head look jutted back in profile; it suggests cutting it by 15-20%.

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
- 23:55 P (rounds 3-5): **CLI for I (stable):** `render/p_run.sh "<motions>" "<views>"` (OUTD=p5, NORENDER=1), `render/pixel_chain.py <json>`,
  gates `render/p_audit.py <out>` (limb audit, exit 1 on any failing frame) and `render/gifcheck.py <paths>` (exit 1 on any flag),
  writer `render/gifio.py write_gif()`.
  Round 5: every head/face special case is out of the chain (tex, head hold, stamp, face_layer). Face matids come from rig/face_mats.json as ordinary
  materials, with thin-feature protection on iris/lash/brow/mouth. Round 4: dash smear frames (key contains SMEAR) get afterimages + speed lines;
  all 8 views run through the chain. Round 3: limb gate, A-line/hem/skin-band/toe shape fixes, GIF writer (1212 experiment GIFs, 0 flags).
  out/p5 (R's 23:16 rig): GIF 18/18 pass, limb audit 11/18 clips pass (S-view leg SPLIT/DETACHED, no VANISHED);
  walk SE boil .020 / shade_swap .026, idle .014-.017 / .016-.020.
  **R:** S-view tucked legs get a K line across the thigh, so the audit reads split legs; the purple iris maps to palette g (brown).
  If iris should read blue/dark, add a ramp in face_mats.json `ramps`. I'll re-run p_run.sh on your final r8 + F's textures.

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
- 21:45 F: started. Face = m96 template parts (eye_spec.json via v2/m96/tools/eyetmpl.py) placed per frame on 3D head anchors. Files in `face/`:
  `face_lib.py` (part library + named expressions + faceless textures `face/tex/tex_<V>_nf.png`), `f_render.py` (Blender: faceless head pass
  + per-frame anchors, wraps render_motion.py like p_parts.py; R's files untouched), `face_layer.py` (P's call), `f_run.sh "<acts>" "<views>"`.
  **Anchors I use until R's export exists (R: please reuse or tell me yours):** each m96 anchor pixel (anchor.json eye iris centres, brow,
  mouth, blush, nose; + `face/calib.json` offset, see below) is ray-cast from the view camera onto the REST head at identity pose, stored in the
  head bone's rest frame (`anchors_head_local_m` in `face/out/<act>/<act>_<V>_face.json`; S: eye.L/R = (+-0.074, 0.125, 0.170) m
  (x = bone X, y = along the head bone, z = front), mouth (0, 0.039, 0.184), cheeks (+-0.074, 0.05, 0.16), brows (+-0.074, 0.225, 0.213)),
  re-posed with the head bone matrix per frame and projected -> 128-cell xy + depth + facing + head yaw/pitch/roll.
  **R, finding:** at rest the rig head renders 3-4 px ABOVE the master (tex pass vs EC0 masters: S dy -4, SE -3, E -1; match .94/.95/.99).
  align.json fits the feet, the rig is taller. I compensate (face/calib.json); the 3D anchor positions above already include it.
  **R masking:** not needed any more from my side: f_render.py swaps the projection texture in memory for the faceless one
  (`face/tex/tex_<V>_nf.png`), so you can keep tex_<V>.png as is; if you mask natively, keep the hair/skin and erase only the features.
  **M:** your new per-frame `face` + numeric `blink` (0/.5/1) keys are read directly (thanks); missing keys fall back to my per-action map.
- 22:40 F: **face layer done** (walk/run/idle/jump x SE/E/S on M's 21:33 bake + R's r6). **P:** `sys.path.insert(0, '<EXP>/face'); from face_layer import face_layer;
  g = face_layer({'action': act, 'view': V, 'i': i}, g, {'rface': info['frames'][k]['face']})` after your chain (g = 128x128 char grid; list of rows
  or np array). Prerequisite per motion update: `zsh face/f_run.sh "<acts>" "<views>"` (~1 s/clip Blender + preview), which writes
  face/out/<act>/<act>_<V>_face.json + the faceless head pass. Your round-2 frames in render/out/p2 predate M's 21:33 re-bake, so I tested on the same chain
  re-run into face/out/p2cur/ (face/f_pchain.sh, your code unchanged). Not mine, seen in your frames: red collar px over the chin in walk/run SE,
  a 3 px hook on the top of the head in idle SE f09.
  **R:** I place parts with my per-view ray-cast anchors (exact at rest, 0 px). Yours are 2-3 px off the master per view (S eyes 2.3 px low, SE far eye 3.5 px
  high), so I use only your `visible`/`occ_m` (body/arm/hand occlusion). My calib = your lift_px exactly (S 4, SE 3, E 1).
  **M:** your face/blink/mouth keys are used. Idle smile is a single frame (f06) next to the f07 blink, and both critics call it a flicker: hold it for 2-3 frames.
  Critique: Opus r2 follows 7.5 / on-model 7 / clean 6 / expressive 7.5 / stable 6.5; Argon 8.5 / 9 / 8 / 9 / 8 (r1 vs the round-2 face: Opus 4/6/3/2/4, Argon 4/3/2/1/4).
  Details: NOTES.md F section; hub entry 2026-10-28_sw_skinned_face.

---
# ROUND 4 (2026-10-28, run in parallel; P finishes round 3 at the same time)
Goal: one consistent, gated set of animations the owner can review, in **all 8 directions** and for more actions.

- **R (rigger)**:
  - (a) Render all **8 directions** natively from the rig: S, SE, E, NE, N, NW, W, SW, using real camera yaws instead of mirroring. Per-view alignment for the new views goes in `rig/align.json`.
  - (b) Back and N views: the head texture/projection needs a master for N/NE, so use `EC0_N_96`/`EC0_NE_96`. NW/W/SW use the mirrored masters, with the katana-free design symmetric (check the bow/bun side).
  - (c) The skirt still reads as a tent at 1x. Narrow the hem, add slight front/back panel separation, and make sure the leg gap shows under the hem.
  - (d) The E-profile nose bump in the head shape.
  - (e) The red collar pixels sitting over the chin in walk/run SE (geometry or matid fix; coordinate with P).
- **M (animator)**:
  - (a) The idle one-frame smile next to a blink (F flagged it). Make expression changes last at least 2 frames.
  - (b) An SE view cheat so the run lean reads in SE and the other 3/4 views (e.g. bias the lean toward screen-right/down, or add a per-view yaw offset in the motion).
  - (c) A new action, **dash**: anticipation (crouch + lean back) → burst (1–2 **smear** frames) → glide → skid/brake with skirt and hair overshoot → recover. Timing per swordswoman/docs/ANIM_DIRECTION.md. Smear frames are authored in motion as stretched poses; P renders the smear look.
  - (d) A new action, **hurt**: a snap back with head whip + hold + recover (PMD-style 2/8 ticks).
  - Expression cues for both. Variants are optional.
- **F (face)**:
  - (a) Critic nits: angled brows clearing the fringe, a cleaner effort mouth, far-eye lashes off the cheek outline (walk SE f03–f05).
  - (b) Faces for NE/N (partial or none) and the mirrored W/SW/NW views.
  - (c) New expressions for dash (focused/determined) and hurt (pained ><, wince, tears optional).
- **P (pixel)**: finish round 3 (limb audit gate, skirt shapes, face_layer integration, GIF writer). Then add **smear rendering** for M's smear frames (a stretched silhouette with motion-blur pixel streaks in the palette, 1–2 frames) and the 8-direction support.
- **I (integrator, new)** owns `release/`.
  - One end-to-end script `release/make_all.sh` that re-renders every action × 8 directions on the latest rig, motion, face and pixel chain. It runs the gates and produces the review set:
    - gates: pxeval seq (boil, shade_swap), P's limb audit, GIF check (loop, ≥20 ms, seam)
    - per action: an 8-direction GIF (4x), per-direction GIFs, a 1x strip and a contact sheet
    - smooth-preview GIFs
    - a gate report table
  - Run a critic panel (Opus + Argon; the AD/animation director/game director roles from the repo's review style).
  - Update one pinned hub entry, "Swordswoman current build", that always points to the latest gated set.
  - Re-run as other owners land changes, watching their status logs.

## Status log (I)
- (I writes here)
- 22:35 I: started; **release/make_all.sh** works (one command: R render_motion.py --no-post + P p_parts.py + F f_render.py (full + --preview), cached by
  input hash in release/work/cache/ -> P pixel_chain.py (its built-in face_layer reads <clip>/face/, as p3_run.sh) -> F-style face composite on the
  preview -> release/out/<build_id>/ {<act>/<V>.gif 4x, <act>_8dir.gif, *_strip1x.png, <act>_sheet.png, previews} + GATES.md; release/out/latest).
  Env: DIRS="SE E S" (default = every view in rig/align.json), ACTS=..., JOBS=9, PANEL=1. Default motion per action = motion/<act>.json
  (release/actions.json; M: tell me here if a variant becomes the default). First build 20261028_da7ed73 (6 actions x SE/E/S, 142 s):
  boil 5/17, shade_swap 1/17, limbs 4/17, GIF 17/18.
  **P:** run E crashes in pixel_chain.shape_fixes (line ~270: `xs = np.nonzero(sk[yh])[0]; xs.min()` on an empty row -> ValueError), log in
  release/out/20261028_da7ed73/work/run/E/clip.log. **P:** limb audit fails jump S 7/16 (DETACHED/SPLIT/THIN), dash S 5/13, hurt S 3/9.
- 23:30 F (ROUND 4): done. (a) **Nits:** angled brows now keep a 1 px skin gap under the fringe (the bang px above each brow px -> skin).
  Effort mouth = a dark slit with 2 px of teeth (`mWWm/.mm.`); open = `mWWm/.RR.`, so the red-lips shout is gone. A far eye whose outer ink
  touches dark outline/side-lock px on >= 2 iris rows slides 1 px inward (walk SE f03-f05 now has a skin column before the cheek outline).
  (b) **8 directions:** `face/parts.json` has S SE E NE N W SW NW. NE/NW = blush + lash tip past the cheek outline (count per expression,
  eye_spec ne_lash). N = no face (face_layer returns the frame unchanged). W/SW/NW = E/SE/NE parts mirrored (x -> 128 - x, front_left<->front_right,
  far->far_left, mirrored mouth/blush/nose; the catchlight stays top-left per spec). Turn rules work in SW like SE.
  Mirror test `face/f_mirror_test.py` (mirrored inputs vs the mirrored SE/E/NE result): NW 0 px; SW/W 5-11 px per frame = only the unmirrored iris/catchlight.
  **R:** when native W/SW/NW land (tex_<V>.png + align.json entries), run `python face/face_lib.py build` (it erases the face from your tex_<V>.png)
  and then `NOPV=1 zsh face/f_run.sh rest "W SW NW"; python face/face_lib.py calib` (until then calib = mirrored E/SE/NE). Then f_run.sh works natively.
  (c) **New expressions:** `focused` (alias dash: open eyes, steep V brows, short set mouth, no blush), `hurt` (pain alias: > < eyes,
  brows tilted up to the centre, downturned frown), `wince` (one eye > shut, the other squinting, gritted teeth), `hurt_tear` (+ 2 px W tears;
  the palette has no blue). `strain` = the spec's squeezed-shut effort. Default maps exist for M's `dash`/`hurt` key names. M's face keys win.
  Critique r3 (face/crit/{opus,argon}_r3.txt): brows 7/8, effort mouth 6/9, far eye 8/7, focused 4/9 (since strengthened), hurt 6/9, NE 5/7.
  The mirror 4/4 came from a test-harness texel-phase artefact, now fixed: NW 0 px, SW iris only.
  face/out/p2cur deleted (~600 MB). Not mine: the NE cheek sliver flickers (dark strand line through it), from the tex/head silhouette (R/P).
- 00:20 F (ROUND 4, native 8 directions): ran `face_lib.py build` (faceless tex for all 8, incl. R's tex_{SW,W,NW}), rest renders for all 8, then `face_lib.py calib`.
  Native W/SW/NW calib = mirrored E/SE/NE exactly (dy -1/-3/-2, match .988/.935/.996). Rest anchors were re-cast on R's r7 hull for all 8 views.
  Verified on native renders: walk/idle x SW/W/NW (P chain re-run in my copy, now deleted again) + sheets `face/out/sheet_expr_{SW,W,NW}.png`.
  Fix found there: R's per-anchor `occ_m` of 0.0002 m (self-occlusion noise) hid the W profile eye in idle f07-f09. Now only occ_m > 1 cm hides a part.
  `focused` (dash): 2-row lower lid + V brow whose inner end drops into the lash (one dark wedge) + short set mouth, no blush.
  Re-critique: Argon 8, Opus 6 (was Opus 4; at 1x it is still close to determined in SE/SW). West views: Argon SW 8 / W 3 -> fixed dropout / NW 8; Opus 7 / 5 -> fixed / 6.
  **R + P (routed): NE/NW cheek-sliver flicker.** The 2-3 px skin sliver at the NE/NW cheek changes shape every frame ("Y" in idle NE f08, finger spikes in
  f03-f05, a dark strand line through it). It is the tex head silhouette/projection plus the pixel step, not the face layer (the face draws only the
  blush + lash there). R: check the NE/NW hull and mask at the cheek (the side lock in front of the cheek). P: consider holding/majority-filtering
  that skin sliver over time. Also seen in native SW walk f02 / idle f06-f07: red collar px still cut into the chin (Opus).
- 22:55 I: rebuilt on R r7 (8 dirs) + M round 4 (dash/hurt, and **motion/view/<act>_<V>.json used automatically for run/dash**) + F round 4:
  build 20261028_854761b = 6 actions x 8 dirs (48 clips, 6 min). Gates: boil 13/43, shade_swap 1/43, limbs 25/43, GIF 43/48 (the 5 missing are below).
  **P: the shape_fixes crash now hits 5 clips**: run E, run W, dash NE, dash NW, dash W (render/pixel_chain.py ~l.270 `xs.min()` on an empty skeleton
  row). Logs: release/out/20261028_854761b/work/<act>/<V>/clip.log. Re-run one clip: `release/rl.py clip <id> run E`. The N views have no face, by F's design.

---
# ROUND 5: DIRECTION CHANGE (owner, 2026-10-28)
> "Stop projecting the pixel art face onto the 3D mesh. Start with the 3D reference and then pixelate it like the rest of the
> body. Don't special case it." · "All the poses seem to be leaning back too much. They need to take on a more natural, human,
> feminine pose / stance."

## A. One pipeline for the whole figure, head included
- **No projection of master pixels**: no `tex` head pass, no stamp, no 2D face decal layer, and no head-specific holds in the pixel chain.
  The m96 masters and the turnE illustrations become **modelling reference only**.
- **R** owns the 3D head:
  - Sculpt the hair as 3D geometry: bob with bangs, side locks, bun and bow, matching the reference silhouettes per view, with clumps and tips that the existing spring chains deform.
  - Give the head a proper anime face on the mesh: UV-mapped high-res face textures (eyes, iris + catchlight, lashes, brows, mouth, blush) supplied by F, or modelled eye/brow geometry where that reads better.
  - Use flat palette materials plus shading bands, like the body. Matid entries are added for eye-white, iris, lash/brow, mouth and blush so the chain handles them as **ordinary materials**.
- **F** owns the face *textures/shapes*:
  - High-res (e.g. 1024² UV) anime face art in the m96 style (FACE_SPEC.md and eye_spec.json are the design reference, not a pixel source).
  - One texture set per expression (neutral, smile, joyful, determined, focused, effort, surprised, blink, half-blink, squint, hurt, wince), or shape keys where geometry is better.
  - Expressions are switched per frame by M's `face`/`blink`/`mouth` keys **inside the 3D render**.
  - Contrast and sizes are tuned so the eyes survive pixelization at 96 px through the *standard* chain. Iterate by rendering and pixelizing, never by pixel-painting the result.
  - The 2D `face_layer` is retired. Keep it only as an archived comparison.
- **P**:
  - Remove every head or face special case from `pixel_chain.py` (head hold, stamp, tex, face_layer).
  - Any rule must apply to all materials, e.g. thin-feature protection now also protects eyes and brows as thin features.
  - Re-tune so the face reads at 1x from the 3D render alone.
- **I**: rebuild with this pipeline. The previous projected-face build stays in the archive as the A/B baseline.

## B. Natural, human, feminine stance (replaces the round-2 "chest lifted, shoulders back, chin up" notes, which made poses lean back)
- **M**:
  - **Profile check (E view):** the torso line (pelvis→neck) is 0–4° *forward* of vertical in standing poses, and the centre of mass sits over the mid-foot / balls of the feet. No backward lean in any standing, idle or walk frame.
  - **Head:** level, with pitch about 0° (±3°). Tilts are small and come from roll, not from tipping the chin up.
  - **Shoulders:** relaxed and natural, not pinned back. The neck sits naturally forward of the spine line, as in humans.
  - **Idle:** subtle contrapposto, with the hip shifted over the weight leg, the knee of the free leg softly bent, and arms hanging relaxed with a slight bend.
  - **Walk:** natural human gait with gentle hip sway. Use mocap (CMU/LaFAN1 female walks in `/Users/waylonhuang/Documents/other/pixelart/.models/mocap`) as the **baseline** for natural posture and timing, then stylise lightly for chibi bounce.
  - **Run:** keep the forward lean.
  - **Dash:** reduce the backward anticipation lean (22° is too much; use about 8–10° plus a crouch).
  - **Measured check:** M reports measured torso pitch and head pitch per frame (E view) in NOTES and gates them: torso pitch ≥ 0° (forward) for idle/walk/standing frames.
- **R**: re-check that the rest pose spine and neck are natural, not arched back.

## ROUND 5 addendum (owner, 2026-10-28)
> "The head looks unnaturally jutted back, fix that." · "Give her longer, more consistent bangs, she looks like she's balding."
- **Head position (R + M).** The head sits *forward* over the neck as in a natural human/chibi build: the skull centre is slightly
  ahead of the neck base in profile, and the neck angles forward from the chest.
  - R fixes the rest head/neck placement in `rig/` (the head bone and mesh shouldn't sit behind the spine line).
  - M removes any backward head offset or pitch-up in every action. Head pitch is about 0° (level) to slightly down.
  - Gate (E profile, every frame): head centre x ≥ neck-base x (toward her front).
- **Bangs (R, with F for the hairline).** A full, *longer*, consistent fringe: thick bangs that cover the forehead down to about the brow line
  (eyebrows may peek through gaps), in even, chunky anime clumps across the whole front. No visible scalp or high hairline from
  any of the 8 directions, including during head tilt and spring motion. The side locks frame the face down to about the chin.
  - Hair volume overlaps the skull fully, so there's no skin showing through between the clumps or at the parting.
  - QA: 8-direction rest + head tilt ±15° + spring swing sheet, at 1x and 4x.
- 23:45 F (ROUND 5): **face = hi-res textures on R's 3D head, pixelized by the standard chain.** The 2D face_layer is retired (kept in face/ as the
  A/B baseline only). Agreement proposal for R + P (I adopt everything R already built in r8):
  - **UV:** R's `face_uv` + `fmask` (rig/build_head3d.py, planar front map) as is. I calibrate my layout on it: a UV-coded texture rendered
    through render_motion.py at rest S (face/f3d/f3d_fit.py -> face/f3d/uvfit.json, cubic fit, rms 2 / 20 texels). So R may re-sculpt and re-map
    freely; after any face_uv change I re-run the fit (2 min). **R: please keep fmask = all front skin from the chin up to under the fringe.**
  - **Textures:** `face/tex3d/<face>[_blink|_half][_open].png` (matid-coded RGBA, alpha 0 = base skin) + `<name>_col.png` (palette colours for pv),
    1024 x 1024 sRGB, exactly R's `face_tex()` lookup. Written by `face/f3d/f3d_lib.py` for 17 expressions x {open, half, blink} x {mouth default, open},
    plus alias copies of M's names (joy, cheerful, pain/pained, land, dash, blink_closed/blink_half). Switching = R's set_face() per frame. Done, live now.
  - **Materials** (ordinary chain materials; colours sRGB exact). R's rig/face_mats.json names and colours: eye_white, iris, lash (lash + pupil), mouth, blush.
    **F adds** (R: please put them in face_mats.json "mats"): iris_top (0,128,255), iris_low (128,255,0), brow (255,128,0), mouth_in (255,0,128),
    nose (0,255,255). **P: suggested flat ramps:** lash KKK, iris_top hhh, iris ggg, iris_low LLL, eye_white WWW, brow ggg (m96 brows are g, not K),
    mouth mmm, mouth_in RRR, blush kkk, nose SSS. Thin-feature class for lash/brow/mouth/iris_top/iris_low. Please read rig/face_mats.json (R's file);
    your pixel_chain.py currently defaults to rig/matids.json with other names/colours (lash_brow (20,12,16), iris (60,96,170), ...). Until you switch,
    face/f3d/f3d_chain.py registers them in memory for my tests (your code unchanged).
  - **Hairline / brows (R, important):** the design puts brows on m96 S rows 46.5-48.5, lash row 50 and iris 51-53 (master coords; the output sprite
    is lifted by lift_px). Measured on r8 at rest (first non-hair row under the fringe, master coords): **S fringe bottom ~ row 52 across cols 56-71,
    SE ~ row 50.5**. That covers the brows and the upper half of the eyes, and the pixel chain then keeps only a K line under the bangs.
    **Request:** fringe tips at row 46.5 +-0.7 in S (just above the brow line, with 1 px gaps where the brows peek), i.e. about 5 rows (~8.5 cm in head
    height) shorter at the centre. Side locks stay long. Keep the clumps thick and even so it doesn't look balding.
  - **P:** shape_fixes() crashes on a 1-frame rest render (pixel_chain.py:253, empty `sk[yh]`); my tests use SHAPE=0.
- 23:50 I: **round-4 baseline archived** = release/out/20261028_854761b (symlink release/out/r4_baseline; projected face + F face layer; 6 actions x 8 dirs).
  GATES.md now has the **round-5 gates**:
  - posture (E profile): torso pitch, head pitch, and head-forward = head centre x - neck base x per frame. Blender on the build's motion snapshot
    (release/rl_pose.py, same pose application as render_motion.py) plus R's E-view pts.
  - bangs = 1x skin cells above the brow/eye line with hair above them in the same column, from R's matid x P's part pass, in all 8 dirs.
  Baseline numbers: head-forward FAILS on every action (E min -2 to -7 px); idle torso -5..-7 deg and walk -3 deg (leaning back); bangs clean in 23/43 clips
  (S/SE/SW up to 16-30 skin px above the brow). Panel 4-5/10 (PANEL.md); all four critics independently report jutted-back head, lean-back and balding bangs.
  Next build switches release/actions.json to `"pipeline": "r5"`: no F face pass, P chain only, R's own --preview. Then an A/B vs the baseline.

# ROUND 5 proposals (I: panel on the round-4 baseline, release/out/20261028_854761b/PANEL.md)
1. [R+M] Head forward over the neck: move the head/neck pivot ~2-4 px forward in the rest pose (R) and drop the head pitch-up and backward offset (M). Gate: E head-forward >= 0 every frame (now 0/6 actions).
2. [M] Stance: idle/walk spine 2-4 deg forward, head level, pelvis under the ribcage. Less arch on the dash wind-up (-16 deg) and the jump apex (-12 deg).
3. [R(+F)] Bangs: a full fringe to the brows, overlapping clumps and a dark cap under them. No skin between the clumps in S/SE/SW or through the side locks in NE/NW (gate: bangs 23/43).
4. [P] shape_fixes crash (empty skeleton row) drops run E/W and dash NE/NW/W.
5. [M] hurt/dash: replace the symmetric T arms with asymmetric guard/recoil arms and shoulders up.
6. [P] Legs 2 px minimum in run/jump at 1x; keep the sock-top band and boot rim (limbs 25/43).
7. [P/R] Dress and sleeve blob: separate the sleeves from the torso, a 3-tone ramp with no sub-2-px patches (shade_swap 1/43); narrower waist and hem flare (R).
- 08:30 F (ROUND 5, cont.): **3D face textures live in face/tex3d/** (17 expressions x open/half/blink x default/open mouth, R's naming + M-name
  aliases, *_col.png for the preview), switched per frame by R's render_motion.face_tex(), pixelized by P's chain with no special case.
  Layout calibrated on R's current face_uv (07:46 rig) with a UV-coded render (face/f3d/f3d_calib.sh -> uvfit.json). Re-run it after any head/UV change (2 min).
  Tests (walk SE/S/E, idle SE, all expressions at rest S/SE/E): face/f3d/out/{walk,idle,fexpr}_nocut/board_expr_*.png.
  **P:** brown iris is by design. FACE_SPEC iris = h top / g / L (the illustration's grey-brown), so iris -> g is right. Your ramps = mine, no change needed.
  My f3d_chain.py wrapper is now redundant (your chain reads face_mats.json natively).
  **R (head model), from the tests + Opus (crit/opus_r5_f3d.txt):**
  (1) **E profile shows no face.** The S-design eye sits on the front corner of the head and foreshortens to ~1 px in E. The m96 E master eye
      lies on texture u ~0.04 (the head's side), but the SE camera also sees that region, so a separate side eye would be a 3rd eye in SE.
      I tried it (f3d_lib side_layer, F3D_SIDE=1) and turned it off. **This needs geometry:** a flatter, wider face front, so the front eye wraps
      toward the side (anime head plane), and the nose/lip bump in the outline. I'll re-fit the texture to whatever you sculpt.
  (2) Per-view head offset vs the masters on r8 (S-calibrated features vs master, rest): SE features land (+3.2, -4.0) px off, E (+4.9, -3.7).
      This is a rigid shift (the head-forward move), and the residuals are within +-1.5 px. Fine if intended.
  (3) The skin under the face reads as the dark band S at 1x (light from above/behind the fringe?), so the face looks redder than m96. Lighting or skin ramp (R/P).
  **M:** none. Your face/blink/mouth keys drive the textures as is.
  The 2D face_layer (face/face_layer.py) is retired and kept only as the A/B baseline.
