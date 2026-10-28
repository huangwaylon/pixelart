# PARTS strand NOTES
## 2026-10-26 11:04 step 0: read BRIEF/DESIGN_SPEC/hy3d NOTES; created v2/parts/{A,B,C,out,scripts,crit}
## step 1: approach A (split existing mesh) -- scripts/split_a.py, render_parts.py, render.sh, sheet.py
- Method: voxelise watertight best/rest_mat.glb (pitch 0.007), assign every solid voxel to a part by planes (neck y=0.105, obi bottom -0.245, hem -0.505, boot -0.82), arm capsules along skel shoulder->hand (cut plane perpendicular to upper arm, |x|>0.19), surface labels (bow=ID6 by 8-NN vote), bun sphere behind the bow; marching cubes per part + gaussian 1 vox + taubin -> every part CLOSED (caps are the cut faces). Legs get a hidden skin thigh capsule up to y=-0.40 so they can swing under the skirt. Colours = nearest original vertex.
- 11 parts, all watertight: head, bow, bun, torso, skirt, arm_L/R, leg_L/R, boot_L/R (A/parts/*.glb, A/parts/parts.json). 33 s CPU.
- Renders renders/A_{vcol,ids,explode,pose}_*.png. Pose test (rigid rotation about bbox pivots: arm raise, leg stride, head tilt) -> no tearing, legs read under the skirt. Seams are straight planar cuts; caps are hidden in rest pose. Bun piece is small (most of the bun volume is inside the head/bow). Surface keeps the 2mv lumps (bow ribbon lumps, ragged cuffs).
## step 2: C research (sub-agent; repo/HF/requirements reading, nothing installed)
- Hunyuan3D-Part (P3-SAM+X-Part): open (HF tencent/Hunyuan3D-Part 9.5 GB, Tencent community lic), input = mesh, but spconv/Sonata/torch_scatter/custom chamfer .cu + hard .cuda() -> Mac = hard (spconv has no mac wheel). Skip.
- PartCrafter: MIT, HF wgsxm/PartCrafter 3.97 GB, single image + num_parts, diffusers/TripoSG, only torch_cluster.fps (encoder only) + 'cuda' literals -> PLAUSIBLE on MPS. Rank 1.
- PartPacker (NVIDIA): non-commercial lic, HF nvidia/PartPacker 3.18 GB + DINOv2-g, single image, flash-attn optional -> plausible; parts are geometric packing not semantic. Rank 2.
- OmniPart: TRELLIS v1 stack (spconv, nvdiffrast, kaolin, flash/xformers) + 2D masks -> poor on Mac. HoloPart: needs mesh + seg mask, diso/torch_cluster -> medium; it's part completion (could cap approach A parts) but needs CUDA patching.
## step 3: approach B (Gemini part sheets -> 2mv per part -> assemble)
- scripts/gem_parts.sh: Gemini edit of locked turnD front/left/back with "redraw ONLY the <part>, same viewpoint/scale". B/gem/*.png.
  Results: LEFT views mostly OK; FRONT head returned the whole character unchanged; BACK views often wrong (head_back drew a front view; arm_back mirrored wrong; torso_back skin chest); skirt_front a tall dome seen from below; torso_left had a huge obi -> retried with front torso as 2nd ref (torso_left_1, OK but adds a bust).
  Fixes: head = deterministic crop of turnD views above the neck (narrowest row); back := mirror(front) for symmetric parts (silhouette is identical in ortho), skirt front := mirror(back).
- scripts/prep_mv.py: rembg, equal part height across views + alpha=1 sentinel pixels on a shared square box so Hunyuan's per-image recenter keeps relative extents (else wide parts get different scale per view).
- scripts/run_mv_parts.py: 2mv turbo 5 steps octree 384, 8-11 s/part, 72 s total incl. load; all watertight (268k-864k faces). B/raw/*.glb.
- scripts/dec.py (30k faces) + scripts/vcol_proj.py (colours projected from each part's own input views, palette snap, per-part allowed IDs) + scripts/assemble.py (per-axis bbox fit onto the matching A part = 2mv proportions; mirror arm/leg to L). B/parts/*.glb (7 parts: head incl. bow+bun, torso, skirt, arm_L/R, leg_L/R incl. boot).
- Look: parts individually clean & simple (smooth sleeves, clean cone skirt, clean legs), but the whole is less on-model: torso long/obi thin, arms stick out wider, head colours streaky at the sides (projection), bow smaller. Non-uniform fit scales up to 1.6x (torso depth).
## step 4: C install: PartCrafter cloned to .scratch/parts/PartCrafter, own venv .scratch/parts/venv_pc (uv, py3.11, torch 2.14.1 MPS, diffusers 0.32.2). Patches: torch_cluster fps -> optional stub; inference_utils grid device cuda->mps. Runner v2/parts/scripts/run_partcrafter.py (no rmbg/pyrender). Weights via curl -C - (3.97 GB).
- PartCrafter RUNS on MPS fp16 (after 2 patches): 8 parts, 50 steps: denoise 3 s, decode 340 s (dense grid decode per part), total 356 s. C/pc8/part_*.glb
- PartCrafter 12 parts (seed 1): 520 s. Split is MATERIAL-like (hair, face, bow, eyes, obi, dress=torso+skirt+sleeves in ONE piece, legs, boots, hands) + fragments (8-47 components/part); single-image -> thin depth, bun = flat disc. C/pc8, C/pc12; scripts/fit_c.py fits the set to the 2mv bbox + nearest colours -> C/parts.
- PartPacker not tried (non-semantic split, non-commercial licence; PartCrafter already showed image->parts gives material splits, not joint splits).
## step 5: outputs + critique round 1 (crit/prompt.txt, argon.md, opus.md [nsystem4]) on sheet_compare.png
- scripts/finalize.py -> out/<M>/<part>.glb + out/<M>_assembled.glb (named nodes) + out/<M>/pivots.json (bone, parent, pivot). A parts decimated to 12k (head 30k). Katana prop (Gemini isolated katana -> 2mini, 3.5 s; colour bands hilt/guard/blade; parked in right hand at 22 deg) in every out/<M>/katana.glb.
- Added hybrid A+B (A head/bow/bun/torso + B skirt/arms/legs).
| row | Argon (model/clean/rig/48px) | Opus |
|---|---|---|
| 2mv single | 6/5/3/6 | 6/3/1/5 |
| A split | 6/5/6/6 | 6/5/6/5 |
| B per-part | 4/6/6/5 | 5/6/8/4 |
| C PartCrafter | 3/3/3/4 | 3/2/1/3 |
| A+B hybrid | 6/6/7/7 | 7/6/8/6 |
- Both pick the hybrid. Fixes asked: clean obi band, hide shoulder gap, clean bow/bun, face in SE.
## step 6: hybrid v2 (AB2): finalize now paints obi as a straight height band, adds shoulder balls (stay at pivot when the arm rotates); scripts/bowbun.py = procedural bow (2 tapered lobes + knot, on the A bow bbox) + bun sphere; red specks on head -> hair. sheet_compare_v3.png.
- Argon v3: 2mv 7/2/1/6, A 7/5/6/6, B 4/7/8/4, C 2/1/2/2, hybrid v2 8/8/9/8 -> adopt hybrid v2. (It asks for bow ribbon tails, but Level D has none; ignored.) Remaining: sleeves less bell-flared than design, bangs hide far eye at SE.
## step 7: hybrid v3 (AB3) + final critique
- scripts/polish.py: obi = separate dark ring shell (72-bin radial hull of the torso band, +4%, y -0.25..-0.105); B sleeves flared up to 25% toward the cuff. Finalised with OBI=0. sheet_compare_final.png.
- Final: Argon hybrid v3 8/8/9/8 (2mv 7/5/1/4, A 7/4/5/5, B 4/6/7/4, C 2/2/2/2); Opus 7/7/8/7 (2mv 6/5/2/6, A 6/5/6/6, B 5/3/7/4, C 3/4/2/4). Both: adopt hybrid v3. Next: thicker bow lobes + bun peeking, shoulder clipping, skirt +2%, legs -10%, bangs up.
- RESULTS.md written. Cleanup: /tmp/parts_* thumbnails removed; no background jobs left.
## step 8: AB4 (lead request) -- scripts/fix_ab4.py (on AB3/parts) + finalize (OBI=0 ARMPIV=top) + render with PIVOTS=pivots.json (pose test now uses the real bone pivots)
- head: crown hair blended 75% toward an ellipsoid above y 0.5-0.8 (dome), temple bulge +0.035 x, chin skin tapered 22% + lifted, face plane +0.06 z, fringe hem strip (1 px = 0.04) flattened onto the forehead and painted skin, bang overhang 40%, side locks pulled back 0.06.
- bow: lobes depth ~40% of lobe width + knot 0.08, lowered 0.06 onto the crown; bun r 0.105 (0.25 H), top 0.06 above the bow, z -0.20 (embedded in the crown).
- legs scaled 0.9 about the sole, everything else dropped 0.06 (feet stay at y=-1); boots x/z +22% with a taller shaft; skirt +2.5% radial.
- arm pivot = centre of the sleeve top nudged 0.015 outward (was the inner top edge); shoulder ball 0.75x, tucked 0.6 r down into the sleeve cap.
- Crit (crit/prompt_ab4.txt, argon_ab4.md, opus_ab4.md): Argon AB3 5/6/4/5 -> AB4 6/4/6/7; Opus AB3 5/5/5/3 -> AB4 6/4/7/4. PASS: bow thickness, bun peeking (both); legs (Argon), skirt (Opus). PARTIAL: shoulders (hand/sleeve overlaps obi in side pose), fringe, skull (dome ok, SE reads as mushroom/helmet). FAIL: iso SE face still mostly hidden (both), hairline streaks.
- Post-crit tweaks (not re-critiqued): removed the cheek clamp that made streaks, fringe raise 1.5 -> 1 px, smaller tucked shoulder balls, taller boot shafts.
- SE face analysis: head-only renders at az -45 el 0 / el 30 / az -30 show the face is correct 3/4 but SMALL relative to a deep (0.82) bob, and at 30 deg the crown dominates. This is the true 3D projection; the turnD iso_SE drawing cheats (bigger, more frontal face). Pixel artist should keep hand-placing the SE face per DESIGN_SPEC; a further 3D fix would be enlarging the painted face area/shallower back hair.
- Output: out/AB4/*.glb (head, bow, bun, torso+obi shell, skirt, arm_L/R, leg_L/R incl. boots, katana prop), out/AB4/pivots.json, out/AB4_assembled.glb, out/AB4/renders/ (front/side/back/se, pose, exploded, 48px, sheet_AB4.png). READY written.
