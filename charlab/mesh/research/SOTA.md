# Mesh R&D: state of the art and recommendation (R1, 2026-10-30)

Scope: four charlab characters, mechanic (Rio), schoolgirl (Hana), astronaut (Nova) and shorthair (Mika). They are stylised, flat-coloured and outlined, with 2.5-3.5 heads. The concepts show a front view plus a 3/4 view in A-pose. The target is a polished, rig-ready mesh (10-40k tris), then a rig, then poses.

Builds on `swordswoman/docs/sota_image_to_3d_2026.md` (10-24), `swordswoman/v2/hy3d/{LANDSCAPE,HUNYUAN_VERSIONS,NOTES}.md` (10-26), `swordswoman/docs/pixal3d_experiment.md` and the team review `docs/team_review/2026-10-28/`. I re-checked them today against GitHub and HF. This file only repeats what matters for the new brief.

How claims are marked:
- **[V]** = verified today from a primary source (repo, README, API or local code).
- **[L]** = our own local measurement.
- **[M]** = from memory or secondary sources, not re-verified.
- **[U]** = unknown.

Access today:
- **Reachable:** GitHub, HF and docs.meshy.ai.
- **Blocked by the proxy:** top3d.ai, runpod.io and lambda.ai. I used no WebSearch tool.
- **Not tried:** Tripo's platform docs returned an empty shell, so Tripo prices come from the 10-26 notes.

---

## 0. TL;DR

1. **No image-to-3D model solves stylised chibi characters on its own.** What we learned locally still holds:
   - Single-view models invent hidden geometry (a ponytail on Akane; [L]).
   - Only multi-view conditioning (Hunyuan 2mv with 4 views) gave a usable body [L].
   - The best closed services (Tripo 3.1, Hunyuan 3.1, Meshy 7.x) are better at this, but still need retopo and rig cleanup by hand [M, practitioner quotes in LANDSCAPE.md].
2. **Omni is used below its potential. The biggest lever is the control signal, not steps or resolution.**
   - We have only used `bbox`, which is **one global box** (3 numbers) [V, `omni_encoder.py`], plus hand-authored poses.
   - The charlab lab already builds a **closed, skinned, A-posed procedural SDF mesh** from each spec (`charlab/lab/model.py`), with standard humanoid bones.
   - That mesh can be fed to Omni as `pose` (exact A-pose skeleton), `voxel` or `point` control. Its skeleton and weights can then be transferred back onto the Omni mesh. This lines up proportions, rest pose and rig in one move.
3. **Resolution and steps are cheap but small levers.**
   - The shape latent is fixed at **4096×64 tokens** [V, `vae/config.json`]. Raising `octree_resolution` from 384 to 512 only samples the same SDF more finely: smoother surfaces and less aliasing on thin parts, but **no new detail**.
   - The image encoder sees DINOv2 at **518 px** with a 15 % border [V]. A full-body chibi face therefore gets about 100-150 px. Cropping parts (the head) into their own image is the only way to get more input detail.
4. **CFG only strengthens the image, never the control** [V]. In the MLX path the unconditional branch zeroes the image tokens and keeps the control tokens. So raising `guidance_scale` pulls the result toward the picture, and the control acts the same in both branches.
5. **Omni takes one control at a time** (an `if/elif` chain) and **one image** [V]. Pose + bbox, multi-box part layouts and multi-view input are all impossible without retraining.
6. **Parts** (body, head, hair, garments as separate meshes):
   - No open model does this well for anime characters on a Mac.
   - The cheapest reliable route is **segment-then-close using the procedural mesh's own per-face materials and line groups as the segmenter**. This is the PARTS approach that worked on the swordswoman [L].
   - Hunyuan3D-Part now has an **MLX port** (P3-SAM + X-Part) [V], worth one probe.
   - StdGEN (layered body/clothes/hair, VRoid-trained) and KaiNinja / SCULPT (pending code) are the ones to watch.
7. **Rigging:** for our simple humanoids, transferring weights from the procedural rig beats every ML auto-rigger we know of:
   - UniRig: "very bad" per users.
   - SkinTokens: better, but its weights are criticised [M].
   - Fallbacks: Blender heat weights with Preserve Volume (DQS) plus Corrective Smooth, then SkinTokens (Metal/C++ port) as a comparison.
8. **Cloud is worth it only for multi-view generation plus an auto-rig comparison.** The best option is Hunyuan 3.1 or Tripo multiview at about $0.3-0.6 per model. A rented H100 for open CUDA-only models (TRELLIS.2 reference, Hi3D refiner, AniGen, SAM3D-Part) costs about $2-3/h [M]. Both need owner approval and allowlisting.

---

## 1. Image / multi-view → 3D (October 2026)

| Model | Open? Licence | Multi-view | Max res | Mac / MPS | Anime-chibi fit | Runtime here |
|---|---|---|---|---|---|---|
| **Hunyuan3D-Omni** (installed) | open, Tencent Omni CL (no EU/UK/KR) [V] | no, 1 image + 1 control | 4096-token vecset; octree 384 default, 512 in demos [V] | **yes**: cbun MLX fork (DiT/VAE MLX, DINO MPS) [L] | clean closed shells; fuses thin parts; face blank; identity drifts with pose [L] | 150-236 s at 50 steps / octree 384, MLX peak 13 GB, RSS ~25 GB [L] |
| Hunyuan3D 2.1 shape (installed) | open, same CL | no (MV code exists, the released weights don't use it) [M] | same VAE | yes (MPS) [L] | crisp front, thin side profile, invented ponytail [L] | 165 s at 30 steps / octree 384, 11.9 GB [L] |
| Hunyuan3D 2mv / 2mini | open, 2.0 CL | **2mv: F/L/B/R** | 2.0 VAE | yes (MPS; **weights deleted 10-28**) | **only usable Akane mesh** (bangs low, bow small) [L] | 9 s turbo [L] |
| Hunyuan3D-2.1 Paint | open, same CL | n/a (texturing) | 6 views at 256 px on MPS [L] | MLX: Hunyuan3D-Swift (~344 s, ~39 GB), ComfyUI-Hunyuan3D-Paint (MPS/MLX) [V] | PBR, so it shades our flat art; we use material IDs instead | 5-9 min |
| Hunyuan 2.5 / 3.0 / 3.1 / 3.5 | **closed** (Studio + Tencent Cloud API) | 3.1: up to **8 views** [V 10-26] | "3.6B voxels" [V 10-26] | API | strongest Tencent line for characters; auto-rig + motions [V 10-26] | about 1-2 min in the cloud |
| TRELLIS.2-4B | MIT (+DINOv3 licence) [V] | no | O-Voxel 512/1024/1536 | trellis.cpp (Metal) [V]; **deleted here** | best open detail, open sheets, dark texture on our art [L] | 89-364 s [L] |
| Pixal3D | MIT [V] | yes (4 views with cameras) | 1024/1536 | pixal3d.cpp (Metal) [L]; **deleted** | 4-view beat TRELLIS.2 on proportions; single-view invents hair [L] | 4-7 min [L] |
| Hi3D v1.0 refiner (new, 10-23) | open weights (Sparc3D lineage) [V] | coarse mesh + image | **1536³** sparse [V] | **no**: CUDA ≥ 8.0, validated on a 96 GB H20 [V] | could refine a coarse Omni mesh; probably over-detailed for 48-96 px [M] | cloud only |
| SPAR3D / SF3D | Stability Community licence [M] | no | low | MPS experimental [M] | fast, low fidelity | seconds |
| TripoSG / TripoSF | MIT [V] | no | SparseFlex 1024³ (VAE) | CUDA [V] | clean, 2.0-class | - |
| Tripo 3.1 / P1 | closed API | **F/L/B/R** | - | API | #1 geometry Elo on 10-26 (top3d, now blocked) [V 10-26]; P1 low-poly 48-20k faces | ~$0.3/gen [V 10-26] |
| Rodin Gen-2.5 (CLAY lineage) | closed | 5 images, **TAPose**, bbox | quad 4-50k | API ($96/mo Business) | anime preset [V 10-26] | - |
| Meshy 7.1 / T2.5 | closed | multi-image (7.1/6 only) [V] | remesh endpoint | API | A/T-pose mode, rig (humanoid, needs a textured mesh, ≤320k faces, face +Z) [V] | 20 cr mesh, 5 rig, 3/anim [V] |
| Step1X-3D | Apache-2.0 [V] | no | TSDF | CUDA | 2.x-class | - |
| Direct3D-S2 | MIT [V] | no | 1024³ sparse SDF | CUDA 24 GB [V] | high-res shapes | - |
| Sparc3D | no code [V 10-24] | - | - | - | commercial (Hi3D) | - |
| StdGEN | Apache-2.0 [V] | A-pose canonicaliser + MV | LRM, low | CUDA | **anime, layered body/clothes/hair**, VRoid look [M] | - |
| AniGen (VAST) | MIT code/weights, CUBVH non-commercial [V] | no | TRELLIS v1 class | CUDA ≥ 18 GB | image → **rigged** mesh [V] | - |

New since 10-26 [V]:
- the Hi3D v1.0 open refiner;
- SAM3D-Part (SIGGRAPH Asia 2026: click a part, get it as its own mesh refined by TRELLIS.2; needs an 80 GB GPU);
- the Hunyuan3D-Part MLX port;
- AssetFurnace 0.5 (Mac: rig plus 21 moves via SkinTokens, a "retopologise" step).

Still pending: KaiNinja (weights only, README-only repo, pushed 10-22) and SCULPT ("release coming" since 08-14). Tencent pushed no new 3D repos this month, and Omni and 2.1 have been untouched since 2025-10 [V].

Observation on our concepts: the mechanic's ponytail is **hidden in the front view** and only visible in the 3/4 view. A front-only Omni run will drop it or invent something. The schoolgirl's bob volume and the astronaut's backpack have the same problem. Single-image conditioning should use the 3/4 view, or carry the hidden volume in the control (the procedural mesh has it).

---

## 2. Part-aware / decomposed generation

| Method | What it does | Status for us |
|---|---|---|
| PartCrafter (MIT) | image → up to ~16 part meshes (TripoSG base) | CUDA, low resolution per part [M] |
| PartPacker (NVIDIA) | dual-volume parts | non-commercial, CUDA |
| OmniPart (MIT) | bbox-planned parts on TRELLIS v1 | CUDA |
| HoloPart (MIT) | completes the occluded parts of a segmented mesh | CUDA; the idea is reusable |
| SAMPart3D (MIT) | zero-shot 3D part segmentation | CUDA; segmentation only |
| Hunyuan3D-Part (P3-SAM + X-Part light) | segment + generate parts | **MLX port exists** (9.5 GB weights; X-Part default res 128; public auto-seg mIoU ~40-60 %, not the paper's 81 %) [V] |
| SAM3D-Part (new) | interactive part extraction + TRELLIS.2 refinement | 80 GB CUDA [V] |
| KaiNinja / SCULPT | part-level native generators | code not released [V] |
| StdGEN | body / clothes / hair layers for anime | CUDA; VRoid proportions [M] |

**Answer: yes, but not with a generator.**
1. Generate one mesh: Omni, with procedural control.
2. Label every face by its nearest procedural piece (`model.py` already stores a material and a line group per face: head/hair/hat/body/armL/armR/legL/legR/pack).
3. Cut along the label boundaries. Close the cuts with a cap or a short inward extrusion, so hair and garments stay shells over the body.

The swordswoman PARTS rig (rigid parts, legs cut at the knee) scored best on tearing and leg readability [L]. The schoolgirl's skirt is already a rigid cone in the spec.

Generating each part separately with Omni (a crop of only the hair, only the skirt) is possible, but the parts won't share a frame and need hand placement. Keep it for heads only (section 4).

---

## 3. Auto-rigging, skinning, retopology

| Tool | Licence / where | Verdict |
|---|---|---|
| **Weight transfer from the procedural rig** (Blender Data Transfer, nearest face interpolated, then smooth) | local | **Best fit.** Same skeleton names, same A-pose, aligned geometry when the mesh came from procedural control. |
| Blender heat / auto weights + Armature "Preserve Volume" (DQS) + Corrective Smooth | local | the fallback. DQS fixes candy-wrapping at the wrists and forearms; Corrective Smooth fixes collapse at the elbows and knees. |
| SkinTokens / TokenRig (VAST, MIT) | Metal: chris-straka/skintokens, skin-tokens.cpp, AssetFurnace [V] | the best open ML rig on a Mac; users say its weights are weak [M]. Comparison only. |
| UniRig (MIT) | MLX in mlx-serve | superseded; users rate it "very bad" [M] |
| RigNet (GPL-3.0) | CUDA, 2020 | outdated |
| MagicArticulate / Puppeteer (Apache) | CUDA | general articulation, not humanoid-specific |
| Make-It-Animatable (MIT) | CUDA (pushed 2026-09) [V] | humanoid rig in seconds, Mixamo skeleton; cloud test candidate |
| HumanRig | repo not found [U] | - |
| Mesh2Motion (open app, CC0 animations) | browser / offline [V] | manual joint fit + auto weights + animation library; good for quick checks |
| Mixamo / AccuRIG | free accounts; AccuRIG is a Windows desktop app [M] | single-mesh, T/A-pose humanoid; skirts bleed to the hands [M] |
| Anything World, Meshy, Tripo, Hunyuan auto-rig | paid API | comparison only |

Retopology and remesh, all local:
- Blender **voxel remesh** at 0.006-0.01 H: closes the mesh, kills fragments, and the swordswoman clean step used it.
- Then **QuadriFlow** (built into Blender) to 10-20k quads, which is 20-40k tris. Or pymeshlab isotropic remesh + QEM.
- Instant Meshes (BSD-style, an old binary) is optional.
- Then **Symmetrize X** for symmetric designs, and Laplacian/HC smoothing on the body only, never the face or hair edges.
- Edge loops at the joints matter more than total count. QuadriFlow with sharp-edge preservation off gives even loops.

---

## 4. Improving our Omni setup: levers from the code

Where these come from:
- Install: `.models/hy_omni/src_omni_mlx`, weights `weights/Hunyuan3D-Omni` (with an EMA checkpoint).
- Runner: `scripts/run_omni.py` (`variant='ema'`, `num_chunks=8000`, `mc_mode='mc'`).

Pipeline defaults (`config.json`): 50 steps, octree 384, num_chunks 50000, mc_level 0, box_v 1.01. The demos use 50 steps, octree 512 and guidance 4.5.

| Lever | What the code does | Expected gain | Cost on the M5 Max 64 GB |
|---|---|---|---|
| **Control = pose from the procedural skeleton** | `pose` is (51,6) bone segments, Fourier-embedded, plus a type token [V]. Frame: Y-up, +Z forward, bbox [-1,1] (`export_omni_pose.py` exists). | exact A-pose 25°, correct limb lengths, arms clear of the torso, so it rigs cleanly. Pose adherence was good on authored poses [L]. | same time |
| **Control = voxel / point from the procedural mesh** | surface sampled, voxelised (`generate_voxel`), embedded [V] | locks proportions and hidden volumes (ponytail, backpack, bob) and the A-pose; the image adds shape detail. **Risk:** point control from the 2mv mesh "melted" the bow and bun (scored 2/10) [L]; issues #6/#14 report misalignment. Needs Y-up and the 180° fix we found [L]. | same |
| Reference image | DINOv2-L at 518 px, recentred with a 0.15 border on white [V] | the **biggest quality lever after control**. Needed: a single figure (split the concept's two views), clean alpha, an A-pose that matches the skeleton, outlines thin or removed (thick dark outlines can turn into grooves [M]), flat but slightly shaded fills to give a depth cue. The 3/4 view gives hidden volumes. | - |
| guidance_scale | scales only the image branch [V] | 4.5 → 6-7.5 means more image fidelity and more floaters risk; 3 means smoother and blobbier | none |
| Steps | Euler flow, linear timesteps [V] | 30 is about 50 in quality (2.1: 30 steps clean [L]); 80 gives little | ~3 s/step; 30 steps saves ~60 s |
| octree 384 → 512 | VAE query grid only; the latent is fixed [V] | smoother shells, crisper thin edges (bandana knot, collar); no new features | decode ~1.8-2.4× (~+30-60 s, estimated); fine on MLX. On PyTorch MPS keep num_chunks ≤ 20k (the 2^32-byte tensor limit [M]). |
| mc_level | iso-level of the SDF [V] | -0.002…+0.002 thickens or thins thin parts slightly | none |
| EMA vs none | `variant` | EMA cleaner in every pose (4-7 vs 4) [L] | keep EMA |
| Seeds | - | variance is large; pick the best of 3-4 by silhouette IoU | 3-4× time |
| Per-part head crop | a separate run on a head+hair crop with a head-shaped bbox | ~3× more pixels on the face and hair, so better fringe and bun shapes; place it on the body by the neck joint | +1 run |
| Paint (2.1 PBR) | MLX ports exist [V] | gives a texture, but we render flat material IDs. Better: transfer materials from the procedural mesh by nearest surface. | skip |
| Post | FloaterRemover, DegenerateFaceRemover already run [V] | then voxel remesh, QuadriFlow, symmetrize, smooth (section 3), which gives the 10-40k tri target | ~1 min in Blender |

Memory: Omni MLX peaks at 13 GB, so it fits easily. Run only one generator at a time; GPU sharing doubled our times [L]. Never run 2.1 and Omni together (~25 GB RSS each).

---

## 5. Recommendation

### 5.1 Best pipeline we can run locally now (no approvals needed)
```
charlab spec → model.py procedural mesh (A-pose 25°, per-face material + line group, skeleton)
   ├─ export Omni pose txt (51 bones)   ┐
   ├─ export voxel/point cloud (Y-up)   ┘→ Omni MLX, EMA, 50 steps, octree 512, cfg 4.5-6, 3 seeds
ref image (R2): single A-pose view, 3/4 if hidden volumes, clean alpha, thin outlines
   → pick best seed by silhouette IoU (front + 3/4) ≥ 0.85
   → Blender: voxel remesh → QuadriFlow 15k quads → symmetrize (if design symmetric) → smooth body
   → label faces from the procedural mesh → cut hair / garment / body parts (optional rigid parts)
   → transfer weights + skeleton from procedural rig → DQS + Corrective Smooth
   → stress test: A-pose → walk keys → arms up → squat
```
The safety net is the procedural mesh itself, which is already closed, skinned and on-spec. It is the floor any AI mesh has to beat.

### 5.2 Upgraded pipeline (needs owner approval + allowlist)
- **Hunyuan 3.1 multi-view via the Tencent Cloud API.**
  - Request: front + 3/4 + back (R2 views), `GenerateType=Geometry`, then `SubmitAutoRiggingJob` for comparison.
  - Cost: about 30-40 credits ≈ 3-5 CNY ≈ **$0.5-0.7 per character**. There are 100 free credits.
  - Account: an international account with phone verification.
  - Domains: `ai3d.tencentcloudapi.com`, `*.tencentcloud.com`.
- **Tripo multiview + rig** (~$0.3-1 per character; minimum $10 top-up; `api.tripo3d.ai`).
- **Meshy** multi-image + rig (25 credits per character [V]; dollars per credit [U]; Pro is about $20/month [M]; `api.meshy.ai`).
- **Rented GPU** (RunPod/Vast, H100 ~$2-3/h, A100-80 ~$1.2-2/h [M]; their pricing pages are blocked today).
  - 1 day ≈ **$15-25** to try TRELLIS.2 reference post-processing, Hi3D refinement of Omni meshes, Make-It-Animatable, AniGen and PartCrafter.
  - Domains: the provider plus `pypi`/`download.pytorch.org` from the pod.
- Expected gain: multi-view cloud geometry is the only route with a credible jump in hidden-side fidelity. Everything else is incremental.

### 5.3 Ranked 1-day experiments
**R3 (omni/)**
1. **Control A/B, the highest value.** 4 characters × {bbox (baseline), pose, voxel, point} from the procedural mesh. Same reference, seed 1234, 50 steps, octree 384. Score:
   - silhouette IoU against the front and 3/4 views;
   - component count and watertightness;
   - left/right symmetry error;
   - Chamfer distance to the procedural mesh.

   About 16 runs × 3.5 min ≈ 1 h.
2. **Reference A/B with R2:** front vs 3/4 vs cleaned A-pose; outline on vs off; flat vs lightly shaded. Use the best control from 1.
3. **Parameter sweep on the winner:** cfg {3, 4.5, 6, 7.5} × steps {30, 50} × octree {384, 512}, plus 3 seeds. Report time and memory.
4. **Head-crop part run** on schoolgirl (bob) and mechanic (bandana + ponytail), swapped onto the body.
5. **Post chain** (remesh, QuadriFlow, symmetrize) to 20-40k tris. Check that no self-intersections appear at the armpits or crotch.
6. *(Optional)* Hunyuan3D-Part MLX segmentation of the best mesh vs procedural-label cutting.

**R4 (rig/)**
1. **Weight transfer** from the procedural rig onto the best Omni meshes vs Blender heat weights. Both with DQS + Corrective Smooth, through the 4-pose stress set.
2. **Rigid parts vs skinned** for schoolgirl's skirt and astronaut's helmet and backpack.
3. **SkinTokens** (skin-tokens.cpp / chris-straka Metal) as an ML comparison. Mesh2Motion as a sanity check.
4. Feed R3 an **A-pose skeleton** taken from the rig, so the generated mesh matches the rig's rest pose.

**Needs owner approval:** any cloud/API account or payment, uploading the designs to third parties, re-downloading the 2mv weights (deleted at the owner's request on 10-28; it was the only usable multi-view open model), and the allowlist entries above.

Licence reminder: Hunyuan open weights are unlicensed in the EU, UK and South Korea, and that covers their outputs too.
