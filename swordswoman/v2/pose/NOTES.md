# POSE strand NOTES (v2/pose/)

## Step 0 setup (2026-10-26)
- Read BRIEF, STYLE_GUIDE §7/§8/§11, hy3d/NOTES (rig_parts.py rigid parts rig, keys_parts.json, head-to-camera cheat, CHEAT stride yaw), _lead/panel argon/opus.
- There is no hy3d/rig/rig.blend: the rig is built procedurally by hy3d/scripts/rig_parts.py from a parts dir. Working copy:
  - scripts/rig_lib.py = copy of hy3d/scripts/rig_parts.py + new pose keys: `yaw` (whole-body yaw), `roll` (screen-plane tilt of the whole figure about the root = line-of-action lean, re-grounded), `cheat` (per-pose legs+blade yaw, overrides the per-view CHEAT env), `headv` (per-pose head-to-camera cheat), `blade_scr` [screen angle deg (0 = screen right, 90 = up), depth deg] = blade direction authored in SCREEN space.
  - rig/parts_ph = copy of hy3d/rp/parts_placeholder (slim placeholder proportions; PROPORTIONS_E.json not landed yet). Poses are bone rotations (same bone names/conventions as keys_parts.json) so they transfer.
  - scripts/render_jobs.py (Blender): jobs (single poses or sequences with 1-frame bow/bun/skirt lag + smear arc) -> per frame 4 passes at 4x: matid (flat vertex colours), part (object-ID: head/torso/skirt/armR/armL/legR/legL/blade/hilt/smear), core (head+torso+skirt only), blade (blade only) + screen points json. Camera = hy3d camera (ortho, 30 deg elev, AZ S/SE/E/NE/N); 48 px figure (PPU calibrated on rest SE); 96 render cell, the 64 game cell = crop (16,16); feet on row 61 (2 px above the cell bottom).
  - scripts/metrics.py: 1x metrics: area, neg (limb+blade px outside the core silhouette), blade_vis / blade_hidden / blade_over_body, blade_len (projected px), ground_gap, foot_px, w/h, clip, line of action (tilt deg, bend px, shape I/C/S from head_top-chest-hips-support foot), delta (XOR/union vs previous frame); tile/strip = 1x sil | 4x sil | 4x matid on #6e6e6e.

## Step 1 SE first pass (out_r0 -> out_r1 -> out_r2)
- r0: FK-only keys (hy3d conventions) -> sword arm and strides hard to place in screen space; slash coil sign was wrong (Z+ turns her front LEFT = away from the SE camera; coil = Z-).
- Added to rig_lib.py: `ik.R`/`ik.L` = [x, y, depth, knee] 2-bone leg IK with the foot target in the camera-facing vertical plane (x screen-right, y up, in leg lengths from the hip) -> strides/lunges are laid out across the screen by construction; `scr` {bone: [screen angle, depth]} aims any limb bone in that plane (arms). Learned: chibi arms are short (hand never gets above mid-head), so the BLADE and LEGS carry the silhouette.
- scripts/pt.py (render / sweep / export), poses_src.py (pose table source), review.py, metrics.crit_strip (1x true size + 3x matid + 3x sil). First sweeps: tmp/sweep/slwu (slash windup arm/blade), slim (impact lean/roll): picked windup arm 145 / blade 125, impact lean 4 + roll 10 + blade -15 (less hunched).
- crit r2 (SE, crit/r2/argon.md, opus.md [bni_requests]) "readable+energetic at 1x":
| | idle | walk | run | jump | dash | slash | overhead | hurt |
|---|---|---|---|---|---|---|---|---|
| Argon r2 | 6.5 | 6 | 6.5 | 7.5 | 7 | 7.5 | 7.5 | 7 |
| Opus r2 | 5 | 5 | 6 | 6 | 7 | 6 | 4 | 6 |
- Main notes: run blade reads as a lance (angle 20 deg down-left), push legs fuse; walk passing knee stacks on support leg, stride narrow; jump launch legs pinned + symmetric Y arms, apex T-pose; dash smear fan = flag (drop it, VFX layer only), burst lower; slash arc swallows head (draw smear BEHIND body), follow blade through legs; overhead never goes overhead; hurt stagger = blob.

## Step 2 SE r3 + roll fix + E first look
- rig_lib.py: `roll` is now applied FIRST (whole figure rotated in the screen plane about the feet), then leg IK / scr / blade_scr are solved in the final frame -> lean reads in the torso while both feet stay planted; blade angles are final screen angles.
- Smear arc: thin crescent near the blade tip (0.72-0.80 .. 1.03 L), rendered as its own pass and composited BEHIND the body (head/face pop in front, per critics). Dash frames: no arc (smear = separate VFX layer), `arc: 0`.
- SE r3 renders: out_r3/<act>_SE/ (crit.png, preview.gif, sheet.png, metrics.json). E first look (E inherits the screen-authored SE pose, no overrides): out_e1/ -> strides/blade transfer well; big torso twists (slash/overhead Z+30) show her back in E -> need E caps.
- Working rig switched to rig/parts_ph2 = copy of hy3d/rigs/placeholder/parts (hy3d's newer target-solved placeholder). Poses render unchanged (checked run/slash SE).

## Step 3 thumbnail variants (method step 4) + SE r4
- Sweeps for 8 hero keys (vars/h_*.py, 8 variants each, ranked by metrics.score; strips tmp/sweep/<tag>/{ranked,top3,small}.png; top-3 strips copied to crit/v1/*.png + ranked.json).
- crit v1 (variant pick, crit/v1/argon.md, opus.md): winners idle A/B, walk A, run_air A/B, jump_apex C, dash_burst A/B, slash_impact A, ovh_raise A/C, hurt_hit A. Energy (Argon/Opus): idle 6/4, walk 5/4, run_air 8/7, apex 7/6, dash 8/7, slash 7/6, ovh_raise 5/3, hurt 7/6.
- Applied winners + pushes: idle wider stance, blade lifted, head to camera; walk blade 20 deg down-left + more lean; run air horizontal leg split + lift .38 + head ahead; apex one leg dropped; dash burst = v01 + blade tip up; slash impact = v07 (deep lunge, roll 18, chest opened to camera); overhead raise: NEW `bs` bone-scale key (rig_lib) stretches both arms x1.45 so the hands get above the head (allowed squash/stretch cheat), wider stance; hurt hit = v06 + head snapped back, arched, airborne.
- E view: VIEW_XFORM["E"] caps torso twist (spine Z <= 12, chest <= 6, front can't turn away from the camera) and adds head turn -6 toward the camera. out_e2/.

## Step 4 SE+E rounds r4-r6
- crit r4 (crit/r4SE, crit/r4E): SE Argon 6.5/6.5/7.5/7.5/7.5/7.5/7.5/7.5, Opus 5.5/6/7/7/7/7/6/6.5; E (first) Argon 6.5/7/7.5/7.5/8/7/7.5/7.5, Opus 4/5/6/6/6.5/6.5/5.5/6 (idle..hurt). Global note: flat blade at hip = spear -> rest angle ~35 deg down-left (SE); E gets its OWN carry (tip forward-down to screen right, clear in front of the knees).
- r5: per-view overrides (F(..., E={...}) via *_E tables), E carry, bigger bobs, coil fixes, overhead = own vertical chop. crit r5: SE Argon 7/6.5/7.5/7.5/8/7.5/7.5/7.5, Opus 7/6.5/7/7.5/7.5/7.5/6.5/7.5; E Argon 6.5/7/8/7.5/8/7/6.5/7, Opus 5.5/6/6.5/6.5/7/6.5/6/6.5.
- Bug found by critics: smear arc took the short slerp path (overhead arc went UNDER her feet). render_jobs.smear_obj now sweeps in the screen plane, clockwise by default (`cw` frame flag).
- r6: walk pass knee up, steeper blades, run push blade off the rear-leg diagonal, land != crouch, overhead smear over the top + more vertical impact, hurt blade flung up-left; E raise/windup blades clear of the head, E idle carry further forward. Sweep tmp/sweep/oi2 (overhead impact arm stretch/blade).

## Step 5 r6 crit, baseline A/B, S/NE/N first pass
- crit r6: SE Argon 7.5/7/7.5/7.5/8/7.5/7.5/8, Opus 7/7/7/7.5/8/7.5/7/7 (ALL >= 7, idle..hurt); E Argon 7.5/7/8/7.5/8.5/7.5/7.5/7.5, Opus 6.5/6/7/7/7/7/6.5/7. E fixes after r6: idle settle = real halfway pose + bigger blade tip swing + wider feet; walk down frames 2 px lower, E blade swing (tip up on pass) + free arm swing; E overhead raise arms x1.75 + arched back, impact deeper.
- Lead asked to start from hy3d anim.json v12 (m12) motion: blind A/B (crit/ab/<act>_<view>.png, A = hy3d frames_preview m12, B = pose strand r7, same 48 px camera): B wins ALL 6 actions in SE and E for both critics (Argon A 3-5 / B 8-9; Opus A 3-5 / B 7-8). Borrowed from A per critics: run blade higher (off the trailing leg), dash smear kept as low as burst, heavier dash antic squash, slash windup blade cocked behind (twisted away), rounder/lower jump crouch.
- S / N: VIEW_XFORM converts the screen-authored stride x into depth (S toward the camera, N away) + a diagonal screen component (0.45 x) so strides still open negative space; feet spread sideways; knees toward travel (new 5th IK element = depth knee hint); roll x0.3; twists capped +-20. N also mirrors all screen angles (sword hand on screen right) and the smear sweep direction. NE uses the SE screen-authored pose as is (sword arm near side, front to screen right).

## Step 6 rounds f1-f4 + two rig fixes
- crit f1 (5 views, first full set; SE re-scored by a fresh be_system Opus = noisy, 6-7), f2 (SE Argon 7.5/7/8/7.5/8.5/8/7.5/8, Opus 6.5/6/7/7.5/7.5/7.5/6.5/7; E Argon 8/7.5/8.5/8/8/8/8.5/7.5, Opus 6.5/6/6.5/7/6.5/7/6.5/6), f3 (SE Argon 7/7/7.5/8/8/8/7.5/7.5, Opus 6.5/6/7/7.5/7.5/7.5/7/7; E Argon 7.5/6.5/7.5/7.5/7.5/7.5/7.5/7, Opus 6/6/6.5/7/7/7/6/6). NE (f1): Argon 7.5/7/8/6.5/8/8.5/8.5/6.5, Opus 5.5/5/6.5/6.5/6.5/7/6.5/6. S (f1): Argon 6/5/5/7/6/7/7/6, Opus 6/5/6/7/6/6/6/6. Critic noise is ~+-1 between rounds/accounts.
- E slash: new horizontal smear band (`plane_E: "h"`: sweep about world Z through the camera side) so the E slash reads as a side swing, distinct from the overhead chop.
- New `ikg.*` (absolute ground foot targets) + `drop` (body lowered in leg lengths) = planted feet; idle uses it (critics: feet slid between idle frames). Final grounding now keeps the drop.
- RIG FIX 1 (rig_lib): arm stretch `bs: {upper_arm.*}` no longer scales the bone (that made the katana longer); the arm MESH is scaled along its rest axis about the shoulder (parent-inverse) and the hand bone is moved to the stretched arm end -> blade length constant.
- RIG FIX 2 (rig_lib, affects hy3d rig too): the katana fist sat ~1/3 of the arm short of the mesh hand on the re-proportioned placeholder (skeleton wrist row not scaled with arms.length) -> hand bones now placed on the mesh mitten centre (far 12% of arm vertices). Tell hy3d: their rigs/placeholder grip floats mid-forearm.
- Learned: raised arms disappear inside the big bob hair in E/SE, so the overhead raise needs the x1.9 arm stretch to get the hands + blade above the head (sweeps tmp/sweep/er, er2, er3).

### FOR hy3d (rig fixes made in pose/scripts/rig_lib.py, a copy of hy3d/scripts/rig_parts.py; port them to the owner rig)
1. Katana grip: on hy3d/rigs/placeholder/parts the hand bone (from skel.txt) sits ~1/3 of the arm short of the mesh mitten (arms.length 1.45 scales the mesh, not the wrist row) -> the katana floats mid-forearm. Fix: in edit mode, after the pivot move, set hand.S head = centroid of the farthest 12% arm vertices from the shoulder - (hand vector)/2, forearm.S tail = that head.
2. Bone scale on upper_arm (squash/stretch cheats) propagates to hand.R -> longer katana. Fix: stretch the arm MESH via matrix_parent_inverse (scale along the rest arm axis about the shoulder) and move the hand pose matrix to shoulder + (hand - shoulder) * f.
3. Final grounding should be `ao.location.z - zmin` (not `-zmin`) if anything lowers the root before grounding (my `drop`).
Also new pose keys (all optional, backward compatible): yaw, roll (applied first), cheat, headv, blade_scr, scr, ik.S, ikg.S, drop, bs.

## Step 7 (fresh instance) resume
- Found: crit f5 SE (Argon 7.5/6.5/7.5/7.5/8/8/7/7.5, Opus 6.5/6/7/7.5/7.5/7.5/7/7) and out_f6 (f5 pushes applied, SE+E) rendered but not logged/critiqued. PROPORTIONS_E.json not READY -> stay on placeholder (rig/parts_ph2). No poses.json / gifs/ yet.
- Next: crit f6 SE + E, fix, then S/NE/N rounds, export poses.json (+expression from face/expr_map.json), gifs/, sheets.
- crit f6: SE Argon 6.5/7.5/8/8/8.5/7.5/7.5/8, Opus 6/6.5/6.5/7/7/7/6/6.5; E Argon 7.5/7.5/8.5/8/8.5/8/8/8, Opus 6/6/7/7/7/7/7/6 (crit/f6SE, f6E). Opus recurring: blade flat along legs (run push, walk, land, hurt), free arm tucked, crouch/impact/stagger blobs with head down.
- f7 (backup of f6 table: tmp/poses_src_f6.py): steeper walk blades + free arm out, wider down feet; run push blade up-left (-200) off the rear leg; crouch/land knees wider + free arm up; dash antic reach forward, skid front foot further; slash windup arm x1.7 + more coil; overhead impact wider/taller step, head up; hurt stagger taller legs, head up, blade up-left. NOTE head X sign: + = pitch DOWN (forward), - = look up/back. E overhead raise = arms 130 / blade 150 (sweep: ov0, blade out behind the bob).
- Added scripts/mont.py (ones4 matid strips montage <=800px for self-review).
- crit f7: SE Argon 6.5/7.5/8/8/8/7.5/7.5/7.5, Opus(be_system) 6.5/6.5/7/7/7/7/6/6.5; E Argon 7.5/7.5/8.5/8/8.5/8/8/8, Opus 6/6/7/7/7/7/6/6.
- f8 (backup tmp/poses_src_f7.py): slash impact taller + blade diagonal down-right at hip, windup arm x2.0; overhead antic = low guard (blade up-forward), E raise blade straight up; hurt recoil sword arm flung up-back + head up; dash antic free arm x1.35 reach. crit f8: SE Argon 7.5/7.5/8/7.5/8.5/8/7/7.5, Opus 6/6/7/7/7/7/6/6; E Argon 7.5/7.5/8.5/8/8.5/8/7.5/8, Opus 6/6/7/7/7/7/7/6.
- Opus scores look anchored (6/6/7/7/7/7/6/6 across 3 rounds regardless of edits). scripts/autoblade.py (blade angle offsets vs visible blade px): metric biased to flat blades (more px), used only for occlusion cases: SE overhead raise blade was 15 px visible (behind the bob) -> sweep -> arms 118/112, blade 95 (straight up, 26 px); hurt hit blade -> trailing lower-left.
- f9 = f8 + idle knees, walk down feet wider, overhead raise/follow, hurt hit/stagger blades (backup tmp/poses_src_f8.py).
- crit f9: SE Argon 7.5/7.5/8/7.5/8/8/7.5/7.5, Opus 6.5/6.5/7/7.5/7/7/7/7; E Argon 7.5/7.5/8.5/8/8.5/8/8/8, Opus 6/6/7/7/7/7/7/6.
- f10: idle legs crossed (knee hints pushed the far knee across) -> rig_lib ikg.* now takes a 5th element (depth knee hint), idle knees toward travel/camera; idle bob kept ~6 px (STYLE_GUIDE says 1 px; Opus kept asking for more, but measured h 45->38 already in f9 while Opus claimed "1 px" -> critics cannot resolve 1x distances). Walk pass knee further forward, blade bob opposite hips; E hurt recoil legs/blade; E run contacts lean more.
- prompt_base.txt calibration line added (per-action energy: idle = calm breathing loop, walk = relaxed stride; don't guess px). Old base: tmp/prompt_base_v1.txt.
- crit f10: SE Argon 7.5/7.5/8/8/8/7.5/7.5/8, Opus 7/6.5/7/7.5/7/7.5/6.5/7; E Argon 8/7.5/8.5/7.5/8.5/8/8.5/8, Opus 6.5/6.5/7/7/7.5/7/7/6.5.
- f11 (backup tmp/poses_src_f10.py; SE/E pushes from crit f10). crit f11: SE Argon 7.5/7.5/8/8/8/7.5/7.5/7.5, Opus 7/6.5/7/7/7/7/6.5/6.5; E Argon 7.5/7.5/8/8/8.5/8/8/8, Opus 6.5/6.5/7.5/7.5/7.5/7/6.5/6.5.
- S/NE/N first look on the current table (out_f11, crit/f11{S,NE,N}): S Argon 7.5/5.5/6.5/7/5.5/7.5/7.5/6.5, Opus 6/5/6/7/5/6/6/6; NE Argon 7.5/7.5/8/8/8/6.5/7.5/6.5, Opus 5/5/6/6.5/6.5/7/6.5/5; N Argon 7.5/6/6.5/7.5/6/7.5/7.5/7, Opus 5/5/6/7/6/7/6/6.
- S/NE/N: new per-view override mechanism: scripts/ov_S.py, ov_NE.py, ov_N.py (PRE merged before VIEW_XFORM, POST applied after it; pt.resolve applies fr["<V>_post"]); helpers in scripts/poses_src_helpers.py. VIEW_XFORM S/N: side spread 0.10 -> 0.15, screen diagonal 0.45 -> 0.60 x.
- crit f12 S/NE/N (first overrides): S Argon 7/6/6/7/7/7.5/7/6.5, Opus 6/5/6/6.5/6/7/6.5/5.5; NE Argon 7.5/7/7.5/8/7.5/8/8.5/6.5, Opus 5/5.5/6/6/6.5/6.5/5.5/5.5; N Argon 7/6/6.5/7.5/6.5/8/8/7.5, Opus 5/5/6/6.5/5.5/6.5/6/5.5.
- SE/E f12: overhead antic back to low blade behind (critics: up-forward guard = poke), raise hands further back; SE walk contact vs contact2 now differ in depth (front foot far vs near); hurt recoil head up + free arm up-right; E idle back foot under hips, shorter down strides, raise blade tilted back, recoil arm stretch.
- Spawning 3 forked sub-strands (S, NE, N), each owns only scripts/ov_<V>.py, logs to notes_<V>.md; SE/E stay with me.
- crit f12: SE Argon 8/7.5/8/7.5/8/7.5/7.5/7.5, Opus 7/6.5/7/7.5/7.5/7/6.5/7; E Argon 8/8/8/8/8.5/8.5/8.5/8, Opus 6/6.5/7.5/7/7.5/7/7/6.5.
- f13 (backup tmp/poses_src_f12.py): overhead raise SE arms 115/109 blade 130 (sweep), E blade 140 + more arch; walk pass blade -155, contact2 far foot further right; SE hurt stagger hunched, blade tip to the floor; E recoil less extreme (spine -12, roll -10); E idle feet under hips. pt.py now also writes game.gif (deliverable: 1x matid, 64 cell, NN x6 on #6e6e6e) and export() adds "expression" per key (poses_src.EXPR, names from face/expr_map.json).
- crit f13: SE Argon 8/7.5/8/8/8.5/8/7.5/8, Opus 7/6.5/7/7.5/7.5/7.5/6.5/7; E Argon 7.5/8/8.5/8/8.5/8/8.5/8, Opus 6/6.5/7/7/7.5/7/6.5/6.5.
- f14 (backup tmp/poses_src_f13.py): overhead raise arms pushed BEHIND the head plane (scr depth +25 SE / +45 E; sweep), E idle drop 0.01+0.025t + blade down-right, E stagger blade to the floor, E recoil head further back.
- crit f14: SE Argon 7.5/7.5/8/7.5/8/8/7.5/7.5, Opus 6.5/7/7/7.5/7.5/7.5/7/7; E Argon 7.5/7.5/8/8/8.5/8/8.5/8, Opus 6.5/6.5/7/7.5/7.5/7/7/7. Remaining < 7: idle (SE, E), walk E (Opus).

## Step 8 rig E + sub-strand results
- Sub-strands (forks) done, 4 rounds each, only ov_<V>.py edited, logs notes_S.md / notes_NE.md / notes_N.md:
  S_r4 Argon 8/8/8/8/8/9/8/8, Opus 7/6/7/7/7/8/7/6 (legs for walk/run/jump/hurt written as POST final ik; blade depth toward camera to unhide);
  NE_r4 Argon 7.5/8/8/8/8.5/8/8/8.5, Opus 6.5/6/7/6.5/7/7/6.5/7; N_r4 Argon 7.5/7.5/8/8/8.5/8/8.5/8, Opus 6/6/7/7/7/7/6/6 (N slash re-staged; idle feet mirrored).
- crit f15 SE Argon 7.5/7.5/8/8/8.5/8/7.5/7.5, Opus 6.5/6.5/7/7.5/7/7.5/6/7; E Argon 7.5/7.5/8.5/8/8.5/8.5/8.5/8, Opus (be_system) 5/6/7/7/7/6/6/6 -> same poses as f14 for slash/overhead/hurt scored 1 lower: Opus noise ~+-1 per run.
- E walk pass re-staged (planted foot under the hip, swing knee forward, blade above the knee).
- Lead: PROPORTIONS_E.json READY -> built hy3d/rigs/E (make_rig.sh, 3.6 heads, legs 0.43), copied to pose/rig/parts_E; pt.py default PARTS = rig/parts_E. Poses transfer as is (out_g1 SE/E check: grip OK, grounding OK). pt.py: per-view smear direction flag `cw_<V>`.
- crit g1 (rig E, all 5 views, out_g1, crit/g1<V>): S Argon 7.5/7.5/7/8/7.5/8/8/7.5, Opus 7/6.5/7/7.5/7/7.5/7/7; SE Argon 7.5/7/7.5/7.5/7.5/7.5/7/7, Opus 6/6/7/7/7/7/6/6; E Argon 7.5/7.5/8.5/8/8.5/8/8/8, Opus 6.5/6.5/7.5/7/7/7/7/6.5; NE Argon 7.5/8/8.5/8/8/7.5/7.5/8.5, Opus 6/6/7/7/7/7/6/6; N Argon 7.5/7.5/7/7.5/7/7.5/6.5/7.5, Opus 5.5/5/6/7/6/6.5/6/6.5. Rig E (smaller head, longer legs) lowered SE a little.
- Sub-strands re-launched on rig E (S_e*, NE_e*, N_e*). My SE-only tweaks now go to scripts/ov_SE.py (POST; not inherited by S/NE/N) so the forks' baselines stay stable; E tweaks in the *_E tables.
- g2 (backup tmp/poses_src_g1.py): SE idle narrower/straighter, walk pass foot under hip + constant blade -145, run push leg back + contact blade -160, skid foot + blade up-left, overhead raise arms depth 40 blade 150, stagger taller; E idle head/blade dip, walk pass knee forward + blade 20, recoil thrown back, stagger knee.
- crit g2: SE Argon 7.5/7.5/8/8/7.5/8/7/7.5, Opus 6/6/7/7/7/7/6.5/6.5; E Argon 7.5/7.5/8/8/8.5/8/8.5/7.5, Opus 7/7/7.5/7/7.5/7/7/6.5.
- g3 (ov_SE backup tmp/ov_SE_g2.py): SE overhead raise re-staged as an open Y (sweep: sword arm 135 up-left beside the head, blade vertical 95, free arm 60 up-right; face open), idle down/down_hold split, free hand off the hip, walk pass foot under hip + free arm on its own side; E recoil more upright, free arm up.
- crit g3: SE Argon 7.5/7.5/8/8/8/8/8/7.5, Opus 6.5/6/7/7.5/7.5/7/7.5/6.5; E Argon 7.5/7.5/8/7.5/8/8/8/8, Opus 6/6/7/7/7.5/7/7/7.
- S rig-E rounds: kept S_e1 (Argon 8.5/8/8/8.5/8.5/8.5/8.5/8, Opus 6.5/6/6.5/7.5/7/6.5/7/6.5); e2/e3 worse for Opus, contradictory notes. NE rig-E: NE_e3 Argon 8/8/8.5/8.5/8.5/7.5/8.5/8, Opus 6/6/7/7/7/7/7/6. (S fork emptied tmp/sweep/.)
- N rig-E: N_e3 Argon 8/7.5/7.5/8/7.5/8.5/8.5/8, Opus 6/6/5/7/6/7/7/6. cw_N=True moved into poses_src (overhead smear sweeps over the top in N).
- pt.py: onion.png per clip (each frame's 1x silhouette outline in its own colour) - shown to critics with idle/walk because they cannot see 1x bobs on a static sheet.

## Step 9 (fresh instance) finish on rig E
- Predecessor's final crit (crit/fina_*) had died (empty). out_final = current table (rig E). Re-ran crit h1 (SE/E/N on out_final): SE Argon 7.5/7.5/.., Opus 6/6/7/7/7/7/7/6; E Argon 8/8/8.5/8.5/8.5/8/8.5/8, Opus 6/6/7/7/7/7/7/6; N Argon 8/8/8/8.5/8/8.5/8.5/8, Opus 6/6/6.5/7.5/6/7/7/6.5.
- h2 (backups tmp/poses_src_h1.py, ov_SE_h1.py, ov_N_h1.py): idle SE/E/N blade tip + free hand LAG the bob one frame (idle_E(t, tl), _LAG tables), SE/E idle wider stance, N idle down 0.75 (differs from down_hold); walk blade swings vs legs (SE -132/-138/-160, E 4/12/36), SE pass swing foot forward, E pass2 E_post (far swing leg was hidden); N walk feet split sideways 0.30 + free arm swing; N run contact lean 22 + back foot down-screen + free arm out; SE stagger blade toward floor + spine fold 8; E recoil free arm 150.
- h2 rendered (out_h2); first h2 crit run died (empty). Re-running crit h2 SE/E/N.
- (fresh instance 2) crit h2 Argon had actually completed (crit/h2<V>/argon.md): SE 7.5/7.5/8/8/8.5/8/8.5/8, E 8/7.5/8.5/8/8.5/8/8.5/8, N 8/7.5/8/8.5/8/8.5/8.5/8. Opus died (zle error, empty). Re-running Opus short: one call per view on crit/h2<V>/sheet_<V>.png (mont.py), scores only.
- crit h2 Opus (short, single 800px sheet, crit/h2<V>/opus2.md): SE 5/5/6/6/6/7/6/4, E 5/5/6/6/6/6/6/4, N 5/4/5/6/5/7/6/4. Not comparable to h1 Opus (h1 saw full crit sheets + onion); its fixes ask for things already present (bob, crouch, smear) = downscale artefact. Argon h2 vs h1: E/N walk -0.5, E jump -0.5, rest equal -> not clearly worse. DECISION: KEEP h2 (current poses_src/ov_*). POSE ITERATION STOPPED.
- (b) EXPORTED poses.json (pt.py export, h2 table): 8 actions x 5 views, per key ms/smear/expression (EXPR table = expr_map.json names) + bone rotations/scales.
- (c) FAN-OUT tooling: render_jobs.py GUIDES=1 adds passes guide (matid incl smear crescent) + shade (EEVEE toon+outline); pt.py frames ACT VIEW FROOT GIFROOT -> hy3d/frames/<a>_<v>/s48/ (fNN_matid/shade.png 4x of 96 cell, pivot (48,76), frames.json ms/air/smear/pivot/head_centre/head_top/hip/blade_*/expression, keys.json '_air' suffix) + final_gifs/<a>_<v>.gif; then hy3d/scripts/post.py adds fNN_sil/preview/sheet/onion. ff_redraw prep needs --gpivot 48 76. Backups tmp/render_jobs_pre_fanout.py, tmp/pt_pre_fanout.py.
- frames idle_SE done (6 frames, checked sheet).
- frames idle_S done
- frames idle_E done
- frames idle_NE done
- frames idle_N done
- frames walk_S done
- frames walk_SE done
- frames walk_E done
- frames walk_NE done
- frames walk_N done
- frames run_S done
- frames run_SE done
- frames run_E done
- frames run_NE done
- frames run_N done
- frames jump_S done
- frames jump_SE done
- frames jump_E done
- frames jump_NE done
- frames jump_N done
- frames dash_S done
- frames dash_SE done
- frames dash_E done
- frames dash_NE done
- frames dash_N done
- frames slash_S done
- frames slash_SE done
- frames slash_E done
- frames slash_NE done
- frames slash_N done
- frames overhead_S done
- frames overhead_SE done
- frames overhead_E done
- frames overhead_NE done
- frames overhead_N done
- frames hurt_S done
- frames hurt_SE done
- frames hurt_E done
- frames hurt_NE done
- frames hurt_N done
- (c) FAN-OUT COMPLETE: 40 clips (8 actions x S,SE,E,NE,N) in v2/hy3d/frames/<a>_<v>/s48/ + 40 GIFs in v2/pose/final_gifs/. Verified ff_redraw.guide_from_matid on slash_SE smear frame (smear -> W). Use: ff_redraw.py prep ACT DIR --guides ../hy3d/frames/<a>_<v>/s48 --gpivot 48 76 --gscale 4 (ms in keys.json/frames.json). W/SW/NW = mirror E/SE/NE. POSE STRAND DONE.
