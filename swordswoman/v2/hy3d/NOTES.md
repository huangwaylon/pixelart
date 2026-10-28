# HY3D strand NOTES

## 2026-10-26 08:15 step 0: inventory
- 2mini + 2mv(turbo) already installed: .scratch/hunyuan (venv, src=Hunyuan3D-2 repo, weights/tencent/{2mini,2mv,2(vae turbo)}); runner scripts/run_shape.py (mv used front/left/back only). Prior run on old cluttered ref: out/mv_turn*, mini_front*.
- Omni MLX: .scratch/hy_omni (13 GB weights complete). old_front outputs show pose control broadly works (jump T-arms, run stride) but old cluttered ref -> ribbons/frills/hair spikes.
- 2.1: weights/Hunyuan3D-2.1 DiT ckpt was TRUNCATED (1.37 of 7.37 GB) -> never run successfully. Resuming download with curl -C -.
- Research delegated to a sub-agent -> HUNYUAN_VERSIONS.md.
- New render scripts: v2/hy3d/scripts/render.py (front/side/back/iso34(front-left,20deg)/se(front-right,30deg)), sheet.py (adds se downsampled to 56px in 64 cell, x4 nearest).
- Design turn (v2/design/turn/) not ready yet; design strand generating front now.

## 08:25 step 1: research done -> HUNYUAN_VERSIONS.md (site 3d-models.hunyuan.tencent.com blocked by proxy; used local probes + GitHub/HF)
## 08:30 step 2: design front.png arrived (clean A-pose, no katana). inputs/front.png = rembg isnet-anime, 768 RGBA.
- 2mini turbo (flashvdm, octree 384): s5: gen 3.6s (+11s load), 530k faces, watertight, RSS 12.8 GB -> CLEAN (bow, bun, bob, sleeves, flared hem, boots). s20: 7.6s, adds floaters around sleeves (turbo distill dislikes many steps). Sheet: out/sheet_mini.png
- Omni bbox:0.44,1,0.4 + 6 poses running (MLX).
- 2.1 DiT re-downloading (12 parallel ranges) -- single stream was ~0.7 MB/s.

## 09:00 step 3: Omni batch 1 + 2mv
- Lead: network approved; RESEARCH strand owns landscape (LANDSCAPE.md). I focus on local tests.
- Omni MLX bbox + 6 rig poses on new front: 149-214 s/mesh (slower than the 65 s of the earlier run; GPU likely shared with other strands), MLX peak 13.0 GB, process RSS 24.8 GB. Sheet out/sheet_omni.png.
  Pose control WORKS: run stride, jump T-arms, slash, sword_ready legs/arms follow the skeleton. Clean simple shapes (bob, bun, bow, sleeves, flared hem). Artefacts: run_stride one floater + bulbous bun; attack/sword_ready elongated hair-tail at back; overhead rig pose itself is only arms crossed at shoulder level (not a real overhead).
- 2mv turbo (design front/left/back[/right], 5-10 steps, octree 384): gen 5-9 s + 12 s load, RSS 16.1 GB. Very consistent body/side profile, bun + bow placed right, but bangs come down over the eyes (face reads as a flat mask) and bow is smaller. mv3 vs mv4 nearly identical; mv4 watertight. Sheet out/sheet_mv.png
- Batch 2 running: Omni point-cloud control from mv4_s5 mesh (=mv geometry refined by Omni/2.1 prior), custom poses authored from rest by rotating arm chains (v2/hy3d/poses: arms_up, slash_extend, tpose; scripts/make_poses.py), katana front_k with sword poses.
- 2.1: hf download (no xet) crawling ~0.4 MB/s; xet path stalled. Will use only if it finishes.

## 09:50 step 4: restart recovery + SE camera check
- Lead restart killed batch 2 after 2 meshes (points_mv4_s5 305 s, pose_arms_up 217 s) and the 2.1 download (650 MB/7.37 GB). Relaunched with nohup: scripts/batch2b.sh (slash_extend, tpose; katana: attack_slash_mid, sword_ready, slash_extend) and hf download.
- points_mv4_s5: geometry follows mv mesh but the HEAD/BODY FACE BACKWARDS -> Omni point frame is rotated 180 deg about Y vs Hunyuan glb export. Fixed via PT_ROT180 (negate x,z) in scripts/run_omni.py; rerun queued (batch2c.sh: points from mv4_s5 and mini_s5).
- arms_up (custom authored pose): Omni follows it exactly (both arms raised in V), clean.
- Lead flagged SE column as back-right. Verified numerically: camera at (-3.67,-3.67,4.0) looking at (+0.61,+0.61,-0.5), i.e. front-right of a character facing -Y; az sweep /tmp/hyt.png confirms az -45 el 0 shows the face. At 30 deg elevation the generated meshes' bangs/bow overhang hide the shallow face so clay reads like a back view. Fix: add vertex-colour renders (reference turnaround projected onto the rest mesh) so face/skin/kimono read; keep camera.
- 2.1 download: proxy throughput now ~0.16 MB/s per connection (Omni's 13 GB came at ~20 MB/s yesterday); modelscope.cn blocked. 2.1 shape almost certainly won't finish today; Omni == 2.1 shape DiT + control encoder, so Omni-bbox is our proxy for 2.1 shape quality.

## 10:30 step 5: batch2b results (out/sheet_omni2.png)
- arms_up, tpose, slash_extend (authored by rotating rest arm chains): Omni follows the skeleton closely. Clean. -> Omni pose control is genuinely usable for keyposes.
- Katana (front_k image): body follows pose, but the SWORD is not controlled by the skeleton: attack_mid sword hangs down, slash_extend produced TWO swords (duplicate blade). => generate keys without katana and attach a separate katana prop.
- Times 166-222 s/mesh, MLX peak 13 GB. 1.0-1.0M faces.
- Vertex-colour projection of the design turnaround onto REST meshes (scripts/vcolor.py, render VCOL=1) makes the SE 30deg view read as front-3/4 (face visible). Camera itself was correct; clay hid the face under bangs.
- Lead: skip 2.1 download (killed); Omni-bbox stands in for 2.1 shape.

## 11:00 step 6: critiques (v2/hy3d/crit/argon.md, opus.md; prompt.txt)
| rest mesh | Argon pixel-ref | Opus pixel-ref |
|---|---|---|
| 2mini | 3 | 5 |
| 2mv4 | 8 | 7 |
| omni_bbox | 5 | 5 |
| omni_rest | 4 | 6 |
| omni_pts_mv (rot fixed) | 2 | 2 (Opus saw the old unrotated? no - rendered rot; bow/bun melted) |
Opus Omni pose control 5/10: tpose/arms_up/jump follow skeleton; overhead/attack_mid/sword_ready collapse; identity drifts (bun ball/egg/rabbit-ear, bow size, sleeve width); katana fails everywhere (duplicated blades).
Both critics: rig ONE mesh = 2mv4 (bow ~30% small, bangs low; Opus suggests enlarging bow 1.3x). Omni per-key generation = fallback/guide only.
- Material-ID tooling: scripts/clean_mesh.py (voxel remesh 0.008 + decimate 40k), scripts/matid.py (geometric bands from design front + projected labels for head) -> flat palette IDs.

## 10:40 round 3 step 1: final rest mesh -> v2/hy3d/best/ (README.md)
- (crash recovery: notes ended at step 6; rig/keys.json pose table already authored, no rig yet.)
- Re-ran 2mv4 turbo on LOCKED Level D views (inputsD/ from turnD front/left/back/right, rembg via .scratch/hunyuan/venv): out/mvD4_s5.glb, 8.7 s gen, 523k faces, watertight. Shape ~identical to C-based mv4 (same bangs-over-eyes, small bow), slightly cleaner.
- New scripts/matid2.py (visual-hull labels front(x,y) & side(z,y), height bands from turnD front, leg cores, mitten hands at wrists, bow grow) -> MUCH cleaner IDs than matid.py (old: skin patches on dress, splotchy face). Fixes: bow x1.3 (soft falloff, stays attached), bang overhang pulled back (small effect), eyes painted ~25% larger so they read under the bangs at 30 deg.
- best/rest_mat.glb, best/rest_mat_{front,side,back,se,iso34}.png, best/rest_mat_ids.npy, best/skel.txt.
- dl21.ok EXISTS (2.1 DiT downloaded, 10:15) -> step 4 will run.

## 11:15 round 3 steps 2+3: rig + keys
- scripts/rig.py (Blender 5.2 -b): imports best/rest_mat.glb, normalises height 2 / feet 0; armature from skel.txt (root,hips,spine,chest,neck,head, upper_arm/forearm/hand, thigh/shin/foot; legs re-centred on measured mesh legs) + 8 radial skirt bones (obi bottom -> hem) parented to hips.
  Weights: ARMATURE_AUTO, then overrides: head region rigid on head; arm/sleeve verts (dist<0.15 to arm chain, |x|>0.22) inverse-distance on arm bones (fixes sleeves stuck on hips); skirt shell = hips->skirt bones blend by height & angle (legs never pull the skirt -> no tearing).
  Skirt bones auto-driven per key: rotate outward by knee displacement (hips space) along the bone direction + 0.1 rad air flare when lift>0.05.
  Katana = separate hilt (dark) + straight thin blade (light steel) boxes, bone-parented to hand.R, shown only for katana=1 keys.
  Pose = keys.json Euler deg about rest world axes (B = R^-1 Q R), auto-ground + lift. Added jump_fall key; jump_launch arms -> up/out V, slash_impact arm/blade horizontal.
- Render: ortho iso 30deg elevation, SE (cam front-right) + E (profile), 96 px cell @1x x4 = 384 px, feet pivot (48,88), 26 px/unit (~48-51 px char).
  fNN_matid.png = Workbench flat vertex-colour IDs (AA off), fNN_shade.png = EEVEE 3-band toon (Shader-to-RGB constant ramp) + inverted-hull outline.
- 34 keys x 2 passes in 33 s. Outputs: keys/<action>_<SE|E>/fNN_{matid,shade}.png + keys.json; sheets keys/sheet_{idle,walk,run,jump,dash,slash}.png (rows per dir: shade | matid | 1x box-downsample x4).
- rig/rig.blend saved.
- Own look: poses read; face often hidden by the big bob at 30deg (esp. forward-lean dash/run); arms are short vs head so raised arms hide behind/inside the head.

## 11:35 round 3 step 4: 2.1 shape test (dl21.ok present)
- Fixed run: src_21_mac is empty -> used src_21 + ABSOLUTE weights path (relative path made smart_load_model fall through to HF hub -> 401). HF_HUB_OFFLINE=1.
- 2.1 DiT single-view on inputsD/front.png, 30 steps, octree 384: load 53 s, gen 165 s, 563k faces, MPS 11.9 GB. out/v21D_s30.glb, renders out/v21D_s30_*.png, clean rig/v21D_clean.glb.
- Sheet out/sheet_21.png (rows 2.1 | 2mv4_D | Omni bbox C). 2.1: cleanest front (bangs higher, face/eyes readable, crisp limbs) BUT back hair invents a tall ponytail instead of the bun, thin side profile (single view guesses depth).
## 11:45 round 3 step 5: critique of key sheets (crit/r3/prompt.txt, argon.md, opus.md [nsystem4])
| | Argon | Opus |
|---|---|---|
| idle | 4 | 2 |
| walk | 6 | 4 |
| run | 7 | 5 |
| jump | 3 | 6 |
| dash | 6 | 4 |
| slash | 4 | 5 |
| usable as guide | 6 | 5 |
| 2.1 mesh | 8 | 4 (ponytail = off-model) |
| 2mv mesh | 5 | 7 |
- Shared findings: poses TOO TIMID (idle bob invisible at 1x; walk passing ~ idle; dash burst lean too small, skid upright; slash impact~recover, no spine twist/arc); arms raised overhead (jump) bury face in sleeves; skirt hem spikes in run_reach/dash; hands clip skirt (white specks in matid); face hidden by bangs (1-2 px eyes in SE, none in E).
- Mesh choice split: Argon 2.1, Opus 2mv (bun is identity). Decision: keep 2mv (multi-view consistency + correct bun), consider trimming bangs further.

## 12:05 keys v2 (after r3 critique): exaggerated poses
- v1 renders kept in keys_v1/ (keys table rig/keys_v1.json). New rig/keys.json + rig.py: squash/stretch 'sq' (armature scale about feet), +12 deg default upper_arm abduction (hands clear skirt), all keys pushed per critics:
  idle_down knees 52 + sq .06 / idle_up sq -.03; walk passing lift .05 + swing knee 70; run thighs +-55..78, run_air lift .18 stretch; jump crouch/land sq .13/.17, launch stretch -.12 with arms forward-out V (not overhead), apex/fall arms ~horizontal-out; dash burst lean 50 + fwd .25 + stretch, skid lean back 24 with feet spread; slash: coil spine twist -45 (right shoulder back) + blade low-back, impact twist +40 lunge + horizontal blade, recover twist +58 blade down.
  (fixed: v1 slash twists were inverted.)
- keys/<action>_<SE|E>/ + keys/sheet_<action>.png regenerated (33 s). crit copies crit/r3/v2_sheet_*.png.
- Known rig limit: wide sleeves are fused to the torso side in the watertight mesh -> raised arms stretch a red web between arm and ribs (jump launch/apex/fall).

## 10:47 keys v2 critique (crit/r3/argon_v2.md, opus_v2.md [nsystem4]) -- recovered after restart
| | Argon v1->v2 | Opus v1->v2 |
|---|---|---|
| idle | 4->6 | 2->3 |
| walk | 6->6 | 4->4 |
| run | 7->6.5 | 5->5 |
| jump | 3->5 | 6->6 |
| dash | 6->6.5 | 4->4 |
| slash | 4->5 | 5->6 |
| usable as guide | 6->6.5 | 5->5 |
- Improved: crouch/land squash, launch stretch, run_reach/dash_burst lean (Argon), SE slash_impact twist + horizontal blade = best frame (Opus).
- Remaining: arms never break torso silhouette (walk/run swing too small); raised arms collapse sleeves into slabs (jump launch/fall, dash_skid); dash_skid reads as casual step/surrender, needs low pelvis + planted front heel + backward lean; slash_recover blade points at floor/merges with leg; E slash_impact katana foreshortened; sleeve/obi spikes in E slash_impact/recover; skirt hem spikes (run_air, dash_burst); hands never visible; bow edge-on in E = flame shape; bun hidden in SE.
- 11:10 step 6 running: Omni MLX on inputsD/front.png, poses rest/run_stride/slash_extend, seed 1234, 50 steps; run_omni.py gained --variant ema|none + RAW component stats + SAVE_RAW. out/omni_ema/*_{none,ema}{,_raw}.glb. Raw stats (components, frac faces outside main): none rest 38/0.11%, run 40/12.1%, slash 47/0.2%; ema rest 4/0.01%, run 29/0.12%, slash 46/0.06%. 169-236 s/mesh, MLX peak 13 GB both.
- Renders r_<pose>_<variant>_*.png (RAW meshes, floaters kept), sheets out/omni_ema/sheet_{rest,run_stride,slash_extend}.png (rows nonEMA | EMA). Own look: non-EMA run_stride has a large detached hair/bun blob + detached foot fragment; non-EMA slash bun flattened into a disc/hat, legs fold into sitting; rest similar for both (non-EMA many tiny specks). EMA cleaner on all 3.
## 11:12 step 6 result: Omni EMA vs non-EMA (crit/ema_argon.md, crit/ema_opus.md [nsystem4])
| | Argon | Opus |
|---|---|---|
| non-EMA | 4 | 4 |
| EMA | 6 | 7 |
- Both critics: EMA cleaner in every pose. non-EMA run_stride: large potato-shaped hair blob floating behind + pebble fragments by feet; non-EMA slash: stringy hand fragments, split/duplicated forward arm, head+bow smear in SE. rest: about equal (non-EMA bangs lower).
- EMA residuals: fused mitten hands, oversized back bun, run_stride extra bow on back waist / ghost third foot (Argon), disc artefact on skirt (Opus).
- CONCLUSION: GitHub issue #5 (EMA -> floaters) does NOT reproduce on our MLX fp16 path + this input; keep variant='ema' (default in run_omni.py). Omni remains fallback/guide only; rigged 2mv mesh stays THE reference.

## 11:20 ROUND 2 (lead review of keys v2): camera / face / poses
- CAMERA verified numerically: rig.py set_view SE = camera dir (-1,-1)/sqrt2 * cos30 + z sin30 -> elevation exactly 30.0 deg, azimuth 45 deg front-right; screen-right vector (0.707,-0.707,0) so her forward (0,-1,0) projects to screen right + toward viewer = lower-right. Identical to design r3iso/render_iso.py (az -45, el 30) that made vc_SE. Mesh check: eye-ID centroid x=+0.009 (no yaw error).
  Cause of the "steep / faces E" read = mesh, not camera: deep bob helmet (head 0.75 wide x 0.8 deep), face a flat recessed plate with bangs 0.04-0.07 proud of it and side locks reaching the face plane; at 45 deg a sphere's face centre lands at 0.7 r -> right edge. Sprite art cheats this, so rig now adds a per-view head offset (SE: pitch up 8, turn 14 toward camera; E: pitch up 6, turn 10) -- documented in keys.json _doc.
- FACE: new scripts/facefix.py (best/rest_mat.glb -> best/rest_v2.glb + _ids.npy): bang line raised 0.07 (front hair band -> forehead skin pushed onto a receding plane), remaining bang overhang capped at 0.015 over the forehead, side locks next to the face pulled back 0.22, eyes repainted as two big ellipses right under the new bang line. Both eyes now read in SE, one eye + cheek in E.
- RIG (scripts/rig.py; previous kept as rig_v2.py, keys as rig/keys_v2.json): Corrective Smooth (factor .7, 8 it) on skirt+arm+shoulder group; 12 skirt bones (was 8) with circular smoothing of the knee-driven panel angles (no hem spikes); skin mitten spheres (r .068) bone-parented to both hands; katana now also in dash keys.
- POSES v3 (rig/keys.json) pushed toward anim_redraw targets: run thigh -88..-92 knee-up + shin 60-105, back leg +45..62 extended, arms +-75..85 with forearms bent 80, lean 20-24; jump crouch/land knees 130-135 sq .20/.24, launch sq -.20 arms down-back, apex knees tuck 95/60, fall one leg reaching; dash low lunge (back leg +85 straight, lean 40, fwd .3) with blade trailing; slash coil twist -55 blade above rear shoulder, impact lunge 82/62 + arm -92 fully extended, recover twist +60 blade out to the side.
- keys v3 render + crit r4 (crit/r4/argon.md, opus.md; keys_v3/ kept): Argon idle7 walk6 run5 jump6 dash5 slash4 guide6 | Opus 6/5/4/5/4/5 guide5. Eyes read in SE except when head pitches down (crouches); legs hidden by skirt; dash/slash lunges too narrow; katana missing in run/jump, 1px; sleeves merge with dress.
## 11:30 keys v4 (final for round 2) -> keys/, sheets keys/sheet_<action>.png, keys/cmp_anim_redraw.png (2D anim_redraw frame | 3D shade | 3D matid per action, SE)
- rig.py: "lean" (pelvis forward tilt, thighs compensated), "blade" (blade angle about X; hand.R solved along hips+spine+chest+arm), katana thicker (2 px @1x) + tsuba, skirt flare cap SKMAX 38 deg, skirt bone length x0.8 (SKS) shorter hem, sleeves own darker-red ID (#8e222c; ids list adds "sleeve").
- keys v4: katana in run/jump/dash/slash (trail 160-170 deg), run lean 12-16 + spine 20-24, crouch/land head pitched up ~55, dash_burst lean 22 + thighs -95/+95, slash_coil overhead (upper_arm -160, blade 225), slash_impact lunge -100/+80 + downward diagonal blade, more arm abduction.
- crit r5 (crit/r5/argon.md, opus.md [nsystem4]):
| | idle | walk | run | jump | dash | slash | guide | vs 2D |
|---|---|---|---|---|---|---|---|---|
| Argon v4 | 6.5 | 6 | 6.5 | 5.5 | 6 | 6 | 6.5 | 6.5 |
| Opus v4 | 6 | 5 | 5 | 4 | 4 | 5 | 5 (overall 5.5) | - |
- Both: both eyes now read in SE across nearly all keys (face fix worked); lean better. Biggest remaining gap vs anim_redraw = LEGS: the bell skirt swallows thighs/knees in SE (2D cheats legs + sword outside the body mass); skirt webs between wide strides (dash_skid, slash_impact); blade clips skirt in E (run_reach, slash_recover, jump_land); slash_coil blade hidden behind head; katana too long/lance-like (Opus wants ~0.6 H, tip back-down 25-35 deg); jump_launch stiff; sleeve ID too close to dress.
- Coordination: PARTS strand approach A (rigid part split of the 2mv mesh) reports no tearing and legs reading under the skirt -> the natural fix for the skirt-swallows-legs/webbing problem is to swap my single skinned skirt for their rigid skirt + separate legs, keeping this rig/keys/camera. rig.py takes any glb; the keys.json pose table and view offsets are reusable.

## 12:09 ROUND 3 (lead): rigid PARTS rig
- New scripts/rig_parts.py: imports PARTS dir (pivots.json + part glbs), same armature/camera/head cheat/keys format as rig.py; bone heads moved onto pivots; each part bone-parented 1:1 (head/bow/bun->head, torso->chest, skirt->own skirt bone off hips, arm->upper_arm, leg->thigh). Legs cut at the knee (thigh piece + shin/boot piece on shin + skin knee ball) so crouches bend; arms stay one rigid piece (forearm keys ignored, cutout style); katana = my boxes on hand.R (KL blade length env); skirt bone auto-tilts with the leading thigh + flares with leg spread; sleeves recoloured to the sleeve ID. Smoke test on AB3 OK (no web, legs show under the hem). Waiting for parts/out/AB4/READY (dir exists, no READY yet at 12:08).
- 12:16 AB4 READY. AB4 head still hid the eyes in SE -> partsAB4f/ = AB4 copy with head.glb run through scripts/facefix.py (ids from vertex colours; bangs +0.07, eyes repainted). Lead/parts hints applied in rig_parts.py: E-view forward arm swing clamped to -60, skirt tilts with leading thigh (0.4*min+0.2*max thigh X, clamp 30), SE head scale x1.07 (HEADS_SE), blade solved as an ABSOLUTE direction (blade angle about X + blade_side) by rotating hand.R after posing, skirt length x0.78 (SKL), blade length 0.74 (KL).
- Pose table rig/keys_parts.json (v1 -> v2 -> v3; v1/v2 saved as keys_parts_v1.json/_v2.json, renders keys_parts_v1/, keys_parts_v2/).
- crit r6 (crit/r6/{argon,opus}.md = v3; crit/r6/v2/ = v2; crit/r6/opus_v1.md = v1):
| | idle | walk | run | jump | dash | slash | overall | usable SE/E (of 18) |
|---|---|---|---|---|---|---|---|---|
| Opus v1 | 5 | 3 | 2 | 6 | 4 | 5 | 4 | 8/7 |
| Argon v2 | 7.5 | 6.5 | 6 | 6.5 | 4.5 | 5.5 | 6.5 | 15/14 |
| Opus v2 | 5 | 3 | 3 | 6 | 3 | 4 | 4 | 7/4 |
| Argon v3 | 7 | 6.5 | 5.5 | 7.5 | 6.5 | 5 | 6.5 | 11/14 |
| Opus v3 | 6 | 4 | 4 | 5 | 5 | 5 | 4 | 7/11 |
- Consensus-usable keys (both critics yes, v3): SE idle_up, idle_down, run_push, jump_launch, jump_apex, jump_fall; E idle_up, idle_down, walk_contact, run_reach, run_push, jump_launch, dash_crouch, dash_burst, slash_impact, slash_recover. Both reject run_air and slash_coil in both views, plus SE run_reach, dash_burst and slash_recover.
- Remaining (both): the SE iso depth axis foreshortens strides and the blade (2D cheats limbs/blade perpendicular to the camera); the rigid skirt hides the front knee in SE lunges and the rear thigh pokes through its side; run_air reads upright, not airborne; slash_coil blade needs to sit high behind the head; crouch/land heads still bury the eyes; hand/cuff speckle in matid. Opus: walk/run sword grip reads as an underhand spear.
### FOR anim_cut (paths)
- Keys: v2/hy3d/keys_parts/<action>_<SE|E>/fNN_{shade,matid}.png + keys.json (key names, cell 96 px @1x x4 = 384 px, feet pivot (48,88) @1x, 26 px/unit ~48 px char, 30 deg elev, ids list). Sheets keys_parts/sheet_<action>.png, 2D comparison keys_parts/cmp_anim_redraw.png. Blend: keys_parts/rig_parts.blend.
- Rig: scripts/rig_parts.py  (Blender -b --factory-startup -P rig_parts.py -- <parts dir> best/skel.txt rig/keys_parts.json <out> [actions] [SE,E]); parts used: v2/hy3d/partsAB4f/ (= parts/out/AB4 + facefix head). Pose table rig/keys_parts.json (same bone names as the cutout rig: head/chest/hips/skirt/upper_arm/thigh/shin/hand).
- Use the consensus-usable keys above as pose guides; for the rejected ones use anim_redraw frames for pose and only take proportions from the 3D.

## 13:30-15:10 ROUND 4 (lead): per-frame guides, motion iteration, reproportion prep
- scripts/rig_parts.py extended (backward compatible): bow + bun on own bones under head (for lag), views S/SE/E/NE/N (AZ) with head cheats S [-8,0,0], NE [0,0,-10], N 0; CHEAT env = SE/NE stride+blade yaw (hips Z +g countered by spine, blade dir and fwd rotated) so strides/blades run across the screen; kd extras: skirt_add / skirt_flare / skirt_len / bow_s / sy (stretch along travel) / absz (airborne: root height = lift, no auto-ground); RIG_LIB guard; pivots.json keys starting with "_" ignored.
- scripts/anim_parts.py (exec's rig_parts.py as a library): rig/anim.json frames (key | mix | '~' mirrored | 'set' overrides with '+' additive) at STYLE_GUIDE §8 frame counts/timings (§8 lists no hurt / overhead slash -> not built); secondary = TRUE 1-frame lag (bow/bun keep the previous frame's head orientation x gain, min offset, velocity drag/stretch; skirt length/flare/tilt from previous hip motion); smear-arc guide mesh on smear frames (fan from previous blade to current); per size: s48 (48 px figure, 1x cell 96, pivot (48,84)) primary, s32 optional (cell 64, pivot (32,56)); px/unit calibrated on rest SE height. Writes frames/<act>_<dir>/<size>/fNN_{matid,shade}.png + frames.json (ms, air, smear, pivot, head_centre, head_top, hip, blade_pommel, blade_tip in 1x px) + keys.json (names, '_air' suffix for the ff_redraw harness).
- scripts/post.py: fNN_sil.png (1-bit 1x silhouette x4), preview.gif (shade, real ms), sheet.png (shade|matid|1x px|sil), onion.png. scripts/motion_sheet.py: critic sheets.
- Motion iteration (SE+E, s32 preview, crit/m1..m5, Argon + Opus nsystem4), scores = per-action averages of liveliness/bounce/weight/timing/silhouette:
| pass | Argon SE/E range | Opus SE/E range | main changes |
|---|---|---|---|
| m1 | 4-7 | 3-6 | first build |
| m2 | 6-8 | 5-7 | real lag, bigger idle, run lean, airborne run, jump apex, dash stretch, smear fans |
| m4 | 6-8 (dash SE 6) | 5.4-7.4 (jump 7.4) | walk pass rise cut (support knee bend), run push lifted, jump arc separated (apex +5 px), smear fans meet |
- Lead: proportions will change (user: "fat and awkward") -> full fan-out HELD until v2/design/PROPORTIONS_E.json exists. Lead later: s48 primary (44-48 px in 64 cell), s32 optional.
- scripts/reproportion.py SPEC IN_PARTS SKEL OUT: per-part scale/offset (head uniform about neck + bow/bun, neck extra, torso w/d/h, skirt w/d/h, arms length/thickness/shoulder_x + hands, legs length/thickness/spread + boots, eyes dy/scale), feet stay at y=-1, everything above a segment carried by its length change; re-derives pivots.json (+ _reproportion.measure) and skel.txt. Placeholder rp/placeholder.json (head .95, legs x2.05, torso w .92, arms x1.45, shoulder_x 1.18, skirt .85, neck +.05) measures heads 3.39, shoulders 0.70 x head w, waist 0.47, legs 40.2%, neck gap .051 -> rp/parts_placeholder/ renders cleanly through rig_parts.py (slim, long legs, knee bends OK).
- Motion passes m6-m12 (s48 guide size from m6; prompts crit/mN/prompt.txt, verdicts crit/mN/{argon,opus}.md). Per-action averages (SE / E):
| pass | idle | walk | run | jump | dash | slash |
|---|---|---|---|---|---|---|
| m9 Argon | 8.0/7.6 | 7.8/7.8 | 8.0/8.0 | 8.2/8.2 | 8.0/7.8 | 8.6/8.4 |
| m9 Opus | 6.2/6.2 | 6.8/6.8 | 7.2/7.2 | 8.0/7.8 | 6.4/6.6 | 7.8/8.0 |
| m11 Argon | 7.6/7.4 | 8.0/7.8 | 8.2/8.0 | 8.2/8.2 | 8.4/8.4 | 8.8/8.2 |
| m11 Opus | 7.2/6.8 | 7.0/7.0 | 7.6/7.6 | 7.6/7.4 | 6.6/6.6 | 7.4/6.8 |
| **m12 Argon** | 7.4/7.2 | 8.0/7.6 | 8.0/8.0 | 8.2/7.8 | 8.0/8.0 | 8.2/7.4 |
| **m12 Opus** | 7.1/6.9 | 7.4/7.3 | 7.6/7.5 | 7.7/7.7 | 7.2/7.2 | 7.6/7.1 |
  -> motion ACCEPTED at m12 (all >= 7 except Opus idle E 6.9). Key lessons: measure head heights from frames.json (walk bob: down +2 px / pass -1..-3 px vs contact; run air <= +5 px; idle 2-3 px), avoid big sq on contact frames, keep the blade continuous (dash blade leads from antic on, no 180 deg flips), cap E-view twists ~25 deg, speed-line VFX guides on dash smears, smear fan inner radius 70%.
- rig/anim.json = v12 (versions anim_v1..v11.json kept). Timings = STYLE_GUIDE §8 except slash recover/settle 140/80 (same total). Approved motion preview (OLD proportions, SE+E, s48): frames_preview/<act>_<dir>/s48/.
- Still HELD: full fan-out (S,SE,E,NE,N x s48 [+ s32 optional]) until v2/design/PROPORTIONS_E.json exists; design strand has locked turnE/front.png (~3.25 heads).

### FOR animators (paths)
- Guides (final, after re-proportion): v2/hy3d/frames/<action>_<dir>/s48/ (primary; s32/ optional) -- fNN_matid.png (flat IDs incl. 'smear' VFX guide), fNN_shade.png (toon), fNN_sil.png (1-bit 1x silhouette at 4x), frames.json (per frame: ms, air, smear, pivot, head_centre, head_top, hip, blade_pommel, blade_tip; 1x cell px, x right / y down), keys.json (frame names, '_air' suffix -> ff_redraw.py prep: --guides <dir> --gpivot 48 84 --gscale 4), preview.gif (real timing), sheet.png, onion.png. Cell 96x96 @1x (x4 = 384), feet pivot (48,84), 30 deg iso; SE/NE legs+blade cheated 28 deg toward screen-x; head turned to camera (SE 14, E 18, NE 10).
- Until then: v2/hy3d/frames_preview/<action>_<SE|E>/s48/ (same format, old proportions; motion approved m12).
- Rebuild: Blender -b --factory-startup -P scripts/anim_parts.py -- <parts> <skel> rig/keys_parts.json rig/anim.json frames all S,SE,E,NE,N s48 matid,shade ; then .venv/bin/python scripts/post.py frames
- 15:45 Lead: new POSE strand (v2/pose/) OWNS the pose table + camera-first posing; I stop motion/pose iteration. I keep rig_parts.py, the rig blend and re-proportioning. anim.json v12 / keys_parts.json stay as the motion-approved reference (m12) for the pose strand.
- Re-proportioning finished:
  - scripts/reproportion.py now also accepts flat keys ("head_scale", "leg_length", "shoulder", "waist", ...) and a torso WAIST taper (torso.waist; skirt waistband follows, hem keeps width).
  - scripts/reproportion_solve.py: SPEC with "targets" {heads_tall, shoulder_over_headw, waist_over_headw, legs_frac_of_height, neck_gap} -> solves head.scale / legs.length / arms.shoulder_x / torso.waist / neck.extra by fixed-point iteration (placeholder targets 3.2 / 0.7 / 0.5 / 0.42 / 0.05 -> measured 3.22 / 0.70 / 0.50 / 0.419 / 0.050 in 8 iterations), writes spec_solved.json.
  - scripts/make_rig.sh SPEC NAME -> v2/hy3d/rigs/NAME/{parts/, rig_parts.blend, rest_{SE,E,S}/}. Test: rigs/placeholder/ (from rp/placeholder_targets.json).
  - POSE TRANSFER verified: poses are per-bone Euler rotations about rest world axes with unchanged bone names, so keys_parts.json / anim.json render unchanged on the re-proportioned rig (checked rest, run_reach, slash_impact SE/E on rp/parts_ph_targets: limbs, knee split, blade grip and ground contact all correct; longer legs make the same angles read as bigger strides).
### FOR pose strand (re-proportioned rig)
- Current (placeholder until PROPORTIONS_E.json): v2/hy3d/rigs/placeholder/parts (+ skel.txt) and rigs/placeholder/rig_parts.blend. Final will be v2/hy3d/rigs/E/ (same layout) made by: scripts/make_rig.sh v2/design/PROPORTIONS_E.json E (if the JSON's keys differ from reproportion.py's, map them in a small spec file under rp/).
