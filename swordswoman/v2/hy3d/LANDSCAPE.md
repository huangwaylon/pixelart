# 3D-gen landscape for the chibi-swordswoman reference model (2026-10-26)

Research strand. The goal is one clean, simple, consistent 3D reference built from `v2/design/turn/{front,left,back,right}.png`,
plus posed variants for animation keys. Already rejected: TRELLIS / TRELLIS.2 and Pixal3D.
See `HUNYUAN_VERSIONS.md` for per-version Hunyuan details. Raw scrape data is in `archive/scratch/landscape/`.
No accounts were created, nothing was uploaded and nothing was paid for.

---

## 1. Hunyuan3D: open weights vs Studio/cloud

### What the official sites say
**3d-models.hunyuan.tencent.com** (rendered via browser; the nav lists *Open-Source Model*: Omni, 2.1, 2.0, 1.0)
- **2.0**: "first open-source high-quality 3D-DiT ... decoupled geometry and texture". The page claims "3B, 1 min". It does text- and image-to-3D, and Paint does RGB texture plus "texture changing".
- **2.1**: "First fully open-sourced production-ready" model, with weights *and training code* (fine-tunable). It is the "first open-sourced model with PBR material generation" (albedo/metallic/roughness/normal) and replaces 2.0's RGB paint.
- **Omni**: "first open-source 3D generative model with unified multi-modal control". Inputs are skeleton, point cloud, bbox and voxel. On pose: it "supports the additional input of skeletal conditions under single-image conditions, allowing users to precisely adjust the pose of generated character assets". It uses a lightweight unified control encoder with progressive difficulty-aware training. It is built on the 2.1 shape backbone (3.3B) and outputs **shape only**.

**3d.hunyuanglobal.com** redirects to **hy3d.tencent.ai** ("Tencent HY 3D Global"). It sits behind a login wall. A notice says the Laboratory tools *Smart Topology* and *Sketch-to-3D* are being folded into **3D Studio** (Geometry Generation, Retopology, Texture Painting modules). Features found in the UI bundle strings:
- Generation versions V2.5 / V3.0 / V3.1 / V3.5. Inputs: single image, or "Add Multiple Views (Min2, Max8)". Geometry+texture or staged.
- Toggles: **T-pose**, PBR, LowPoly (tri/quad, "neat wiring"), face count.
- **Rigging**: "Show the bones", "manual bone fixation". "You need to perform bone binding first before selecting the action."
- **Animation**: "Motion Templates", "Animation Repository", "Animation Generation".
- Also: texture generation, part/component generation, geometric stylization, sketch-to-image, 3D character generation, a workflow node editor.
- Credits: "Insufficient credit. Get 200 free credits or purchase a plan", "Free usage: {remain}/{total}" (a daily free quota; Reddit users report "like 20 models every day"), subscriptions, extra credit packs.
- The ToS forbids "any automated ... method ... to extract data or Output from the Services". **Do not browser-automate Studio; use the API.**

3d.hunyuan.tencent.com (CN) never rendered (navigation timeout). It needs a CN phone/WeChat login (earlier probe screenshot `../reference/3d/hunyuan_studio_research/04_cn_login_dialog.png`).

### Tencent Cloud API (ai3d.tencentcloudapi.com, version 2025-05-13; docs updated 2026-05)
| Action | What it does | Credits |
|---|---|---|
| SubmitHunyuanTo3DProJob | Model `3.0` (default) / `3.1`. Image or text. `MultiViewImages`: left/right/back, plus (3.1 only) top/bottom/left_front/right_front. `GenerateType` Normal / **Geometry** / LowPoly (tri/quad, not on 3.1) / Sketch. FaceCount 3k-1.5M. Output obj+glb (or STL/USDZ/FBX) | Normal 20, Geometry 15, LowPoly 25, Sketch 25; +10 multiview, +10 PBR, +10 facecount, +5 format |
| SubmitHunyuanTo3DRapidJob | fast tier | 15 (+10 PBR) |
| **SubmitAutoRiggingJob** | FBX/GLB in (≤60 MB), skeleton + skin out. Optional `MotionType` **1-48 presets** (kicks, walk, idle, dance ...). Humanoid: **A- or T-pose, body only: no weapons/mounts/wings, avoid loose clothing, accessories, complex hair**. Non-humanoids allowed (no MotionType) | 10 |
| SubmitHunyuanTo3DMotionJob | HY-Motion-1.0 text-to-motion, 1-12 s FBX. `RetargetFile` must be a Hunyuan-rigged model | 10 |
| SubmitReduceFaceJob / UVJob / TextureTo3DJob / Hunyuan3DPartJob / Convert3DFormat | smart topology / UV / retexture / parts / convert | 50 / 10 / 30 / 30 / 5 |
| SubmitProfileTo3DJob | portrait to 3D figure from 20 templates. **Being retired 2027-01-19** | 30 |

Pricing: **100 free credits once per new account** (valid 1 year). After that, 0.10 CNY/credit prepaid (1,000 credits = 100 CNY) or 0.12 CNY postpaid. Default concurrency is 3 for Pro and 1 for everything else. Failed or moderated jobs are not charged. The platform is "migrating to TokenHub", so no new models will be added there.
Example: 3.1 multiview geometry (25) + rig (10) is about 35 credits, roughly 3.5 CNY (~US$0.50). The free 100 credits covers about 2-3 full tests.
Docs: https://cloud.tencent.com/document/product/1804/123447 (Pro), /131618 (rig), /131256 (motion), /123461 (billing).

### Omni vs 2.1 vs 2.0 vs Studio, the concrete differences
| | 2.0 (+mini, +mv) | 2.1 | Omni | Studio / API 2.5-3.x |
|---|---|---|---|---|
| Weights | open (Hunyuan 2.0 community licence, no EU/UK/KR) | open, plus training code | open (shape only) | closed |
| Shape DiT | 1.1B (mini 0.6B); mv takes front/left/back/right | 3.3B, new VAE, sharper | the 2.1 DiT plus a control encoder | 2.5 ≈ LATTICE. 3.0 has "3.6B voxels", much better on characters. 3.1 adds 8-view input |
| Texture | Paint 2.0 RGB (CUDA rasterizer) | Paint PBR 2B | none | PBR, texture editing |
| Extra conditioning | multiview (2mv) | single image only (issue #143: MV code exists but the released model does not support it) | **skeleton pose**, bbox, point cloud, voxel | multiview 2-8, T-pose toggle, sketch, low-poly, parts |
| Rig/anim | none | none | none (but it can generate *posed* meshes) | **auto-rig + 48 motion presets + text-to-motion** |
| Mac | yes (MPS; MLX/Swift port runs 2mini in 21 s / 5.6 GB) | shape yes (mac fork); PBR paint about 5-9 min | yes (MLX fork) | web/API |

Omni pitfall: GitHub issue #5, "Weird generated results ... just a bunch of fragments". The fix was "do not use `--use_ema`". Skeleton format questions are in issue #11 (no answer).
New Tencent items: **Hunyuan3D-Buffalo 1.0** (2026-08, unified generate/understand/edit; paper only, no weights), HY3D-Bench, **HY-Motion-1.0** (open text-to-motion, 1B / 0.46B Lite, "supports macOS", needs 24-26 GB VRAM).
Mac ports: `ZimengXiong/Hunyuan3D-Swift` (MLX: 2mini or 2.0-turbo shape in about 21 s, paint-PBR-2.1 in 344 s at about 39 GB). This could replace the slow 2.1 Paint fork for the hy3d strand.

---

## 2. What practitioners say (short quotes)
- Hunyuan 3.1 Studio is the popular free option: "Hunyuan3D 3.1 Is Still the Best Free 3D AI Generator" (219 votes). The author still needed AI retopo, Blender sculpting, AccuRig and manual weight fixes: "definitely not a one-prompt result". From comments: "you get like 20 models every day"; a disputed licence claim "only the case for 3.x, you can still use the HY3D 2.x versions for games"; "Hitem3D is better IMO". https://www.reddit.com/r/TopologyAI/comments/1v2o3mh/
- Same image through Hunyuan / Tripo / Meshy / Hi3D: Hunyuan "kept the clothing layout pretty close to the reference"; Tripo kept the most surface detail; Hi3D "looks more like a redesigned hero version". Commenter: "use Hunyuan for the base model and Tripo for the textures". https://www.reddit.com/r/Tripo_ai/comments/1vanfkh/
- Hunyuan rigging: "Hunyuan3D ... seems it's currently the best, both at low poly and high poly, plus it can also rig." https://www.reddit.com/r/aigamedev/comments/1r6ah62/ GitHub 2.1 #199: "I had great success rigging models generated via the webapp ... trying unirig, tripo, riganything i cannot get mixamo animations working without ... distortion." https://github.com/Tencent-Hunyuan/Hunyuan3D-2.1/issues/199
- Mac reality (M5 Max 36 GB, ComfyUI 2.1): "unbearably slow. And any setting above a resolution of 512 causes an error". Reply: it's the MPS ">2^32 bytes" single-tensor limit; "lower octree_resolution and num_chunks". https://www.reddit.com/r/comfyui/comments/1xe4p6c/
- Tripo for characters: "tripo is good. Best so far i tried. But not free and around 0.7-1$ per generation". Advice: "not just a single T-Pose image. Make a turnaround of the character." https://www.reddit.com/r/aigamedev/comments/1xbgnwu/
- Rigging AI output: "First I use an AI image editor to get the character into an A-Pose or T-Pose. Then I use Meshy ... Mixamo auto rig ... in Blender unparent the rig, and use auto weights." https://www.reddit.com/r/aigamedev/comments/1umqaa9/
- Auto-rig ML skepticism: "SkinTokens ain't gonna deliver good results, the weighting is horrible ... better off using Blender automatic weights"; "it's the successor to UniRig and does better, but ai rigging is not viable atm"; "Mesh2motion is better." https://www.reddit.com/r/TopologyAI/comments/1w3bhie/ Also "UniRig very bad." https://www.reddit.com/r/StableDiffusion/comments/1q3ijwo/
- Tripo rig on a skirted anime character (stage-gen, reference art to rigged chibi): "The most common refusal ... is a provider rig that weights a skirt hem" to the hands; "pink-sweater character still has shoulder/braid stretching". https://www.reddit.com/r/aigamedev/comments/1wfjqna/ , https://github.com/softmarshmallow/stage-gen
- **Pixel-art animation via 3D/mocap** (chibi castle-defense game, 8 methods compared): "Chibi heroes with 5 px legs can't show a kick"; "Drawn walks have more charm, rigged walks keep the feet planted. I use both"; "Blender looked great in smooth 3D, just not squeezed into 42 px pixel art". Commenters: "Mocap is no good for pixel animations." https://www.reddit.com/r/aigamedev/comments/1x93t4b/ This supports our plan: 3D only as a hidden pose and consistency guide, with exaggerated keys authored by hand.
- AssetFurnace author, who also started from a 2D pixel game: "Sprite sheets were a pain ... 3D to 2D workflow seemed easier". https://www.reddit.com/r/TopologyAI/comments/1x0ig45/
- HN on Mesh2Motion: "usable without having to create an account. It's a breath of fresh air"; "selecting the skeleton type and then adjusting it manually, joint by joint, seems ... archaic". https://news.ycombinator.com/item?id=45693325 . HN on Hunyuan 2.0, licence: "DOES NOT APPLY IN THE EUROPEAN UNION, UNITED KINGDOM AND SOUTH KOREA". https://news.ycombinator.com/item?id=42786040
- Seed3D 2.0: "impossible without a Chinese cell number". https://www.reddit.com/r/TopologyAI/comments/1sub4qp/

**Blind-vote benchmark, top3d.ai (Oct-26 season, about 236k votes)**. Geometry ELO: 1 Tripo v3.1 (1133, ~$0.30), 2 Hi3D v3.0 (1113, ~$2.1), 3 Lychee Gen 2, 4 Meshy 7 (1096), 5 YVO3D 2.5, 6 Meshy 7.1, 9 Rodin Gen-2.5 (1030), **10 Hunyuan 3.1 (1030, $0)**, 13 Seed3D 2.0, 17 TRELLIS.2 (930), 18 Pixal3D (927), which matches our rejections. Low-poly: 1 Tripo P2.0, 2 Tripo P1.0, 3 Meshy T2, ..., 8 Hunyuan retopo. https://www.top3d.ai/leaderboard?type=geometry

---

## 3. Comparison table
| Tool | Open? | Mac local? | Multi-view in | Rig / animation | Fit for simple chibi | Price / free |
|---|---|---|---|---|---|---|
| **Hunyuan 2mv / 2mini** | open (Tencent CL) | **yes** (running) | 2mv: F/L/B/R | none | very consistent body; bangs over eyes | free |
| **Hunyuan Omni** | open | **yes** (MLX) | no (1 image + control) | skeleton-**posed meshes** | pose control works (local strand) | free |
| **Hunyuan 3.1 API / Studio** | closed | API | **up to 8 views** | **auto-rig + 48 presets, text-to-motion** | strongest char. geometry of the Tencent line; rig wants no weapon, simple hair/clothes | API: 100 free credits, then ~0.1 CNY/credit (rig 10, MV geo 25). Studio: 200 free + daily quota |
| **Tripo v3.1 / P1** | closed (TripoSG/SF open) | API / web | **F/L/B/R** (multiview_to_model) | `animate_rig` v2.5 (biped/quadruped/...; mixamo or tripo spec), `animate_retarget` 27 presets | #1 geometry ELO; P1 native low-poly 48-20k faces; anime OK per docs | web free 200 cr/mo (~13 models, non-commercial, multiview Pro+). API: MV 20-30 cr, rig 25, retarget 10/anim; Pro $20/mo |
| **Meshy 7.1** | closed | API / web | multi-image (paid) | rigging (humanoid only, face +Z, ≤300k faces) + 500+ anims (20 on free) | `pose_mode=a-pose/t-pose`; smart-topology T2.5 | free 100 cr/mo, 10 downloads of 6-lite, CC BY. API paid: gen 20-35, rig 5, anim 3/action |
| **Rodin Gen-2.5** | closed | API / web | up to 5 images | **TAPose** rest-pose conditioning, bbox control, Quad mode; no rig API seen | quad 4k-50k faces; anime style preset | free preview, pay $1.5/credit to download (base 0.5 cr ≈ $0.75); API needs Business $96/mo |
| Hi3D (ex-Hitem3D) v3.0 | closed; **Hi3D v1.0 refiner open** (Linux, H20-class NVIDIA) | no | yes | no | #2 geometry, very detailed (too detailed for us) | from $19.90/mo, free tier |
| Seed3D 2.0 (ByteDance) | closed | no | ? | parts | n/a | needs CN phone |
| CSM (Cube) | closed | n/a | n/a | n/a | **csm.ai no longer resolves (DNS fail 2026-10-26)** | dead? |
| SF3D / SPAR3D | open (Stability CL) | **yes, MPS experimental** | no | no | fast, low fidelity | free |
| TripoSG / TripoSF | open MIT | CUDA | no | no | good shapes 2025-era | free |
| Step1X-3D, Direct3D-S2, Hi3DGen, UltraShape | open | CUDA only | no | no | high-detail geometry, not needed | free |
| StdGEN (CVPR25) | open | CUDA (HF Space demo) | no | outputs A-pose, decomposed body/clothes/hair (VRoid-trained) | anime but realistic proportions | free |
| **Mesh2Motion** | open MIT, CC0 anims | **browser / offline app** | n/a | template skeleton fitted by hand joint by joint, auto weights, animation library, GLB export | ideal for one simple chibi mesh; no account | free |
| SkinTokens / TokenRig (UniRig successor) | open | **skin-tokens.cpp CPU/Vulkan** | n/a | skeleton + weights to GLB; trained incl. VRoid | users: weights poor, use Blender auto-weights | free (MIT) |
| UniRig, Puppeteer, MagicArticulate, Make-It-Animatable | open | CUDA | n/a | auto-rig (Puppeteer also animates) | users rate UniRig "very bad" | free |
| Kimodo (NVIDIA), HY-Motion | open | Kimodo.cpp CPU/Vulkan; HY-Motion claims macOS | n/a | text-to-motion (SOMA/SMPL) | realistic motion; must be exaggerated for pixel art | free |
| AssetFurnace (image-to-3dlab) | open Apache | **yes, Apple Silicon** | no | SkinTokens rig + 21 Kimodo moves; "skip straight to the rig" with your own GLB | generators = Pixal3D/TRELLIS/Hunyuan-MLX; rig+animate stage reusable | free |

---

## 4. Image to rigged, animated character: the options that exist
1. **Hunyuan Cloud API**: 3.1 multiview Geometry, then SubmitAutoRiggingJob with MotionType, giving an FBX. All Tencent, about 35-45 credits per character.
2. **Tripo API**: multiview_to_model, then animate_prerigcheck (free), animate_rig, animate_retarget (preset idle/walk/run/jump/slash/...).
3. **Meshy**: multi-image-to-3d with pose_mode=a-pose, then rigging, then animation (500+ library). The web free tier includes rigging.
4. **Local Mac**: 2mv mesh, then Mesh2Motion (browser) or Blender Rigify/auto-weights or skin-tokens.cpp, then pose by hand. Alternatively, Omni pose control generates each key pose directly (no rig, but identity drifts per pose).
None of them handle the katana: every auto-rigger wants a body-only mesh. **Rig the no-katana `front.png` mesh and parent the katana to the hand bone afterwards.**

---

## 5. Ranked recommendation: what to test next
1. **Local, free, no approvals: "one mesh, one rig, all poses".** Take the best 2mv-turbo rest mesh (F/L/B/R, already consistent). Rig it once in **Mesh2Motion** (run the web app or its offline build in the browser; no GPU, no account) or in Blender (Rigify plus auto weights). Then pose the animation keys (idle, run, slash, jump) and render with `scripts/render.py`. *Expected value: highest.* Identity is identical across every key by construction, and it is cheap and editable. Keep **Omni pose** as the fallback or cross-check for poses where skinning breaks (big sleeves, hem). Add the katana as a separate parented mesh.
   - Optional: `skin-tokens.cpp` (CPU build, `skintokens-cli rig in.glb out.glb --device cpu`) for an automatic first-pass skeleton. Expect weight cleanup.
2. **Hunyuan 3.1 via Tencent Cloud API** *(needs user approval: a Tencent Cloud international account plus real-name/phone verification; 100 free credits)*. Send 4-5 views from `design/turn` with `Model=3.1`, `GenerateType=Geometry` (15+10 cr), then `SubmitAutoRiggingJob` with MotionType idle/walk/attack (10 cr). *Value:* tests whether 3.x geometry beats 2mv on face and bangs, and gives a free auto-rig plus motions to compare against our manual rig. About 2-3 runs fit in the free credits. Use the Python SDK `tencentcloud-sdk-python` (`ai3d` module).
3. **Tripo v3.1 or P1 multiview + animate_rig/retarget** *(needs approval: account; API credits must be bought, about $10 minimum. Web free 200 credits/mo, but multiview is Pro-only)*. Top blind-vote geometry. P1 native low-poly (≤20k quads) suits "simple, solid". Watch for skirt-to-hand weight bleed. About 50-90 credits per character.
4. **Meshy 7.1 web free tier** *(needs approval: account)*. Single front image with A-pose, then free rigging plus 20 animations. Quick sanity comparison. Multi-image needs Pro.
5. **Rodin Gen-2.5** *(account; free preview, $0.75+ to download)*. Only if 2-4 disappoint: 5-image input, TAPose, Quad 4-8k faces.
Skip: Hi3D/Seed3D/Step1X/Direct3D-S2/TripoSG/UltraShape (CUDA-only or over-detailed), CSM (gone), StdGEN (realistic VRoid proportions, CUDA), and AssetFurnace's generators (Pixal3D/TRELLIS, already rejected; its rig/animate stage overlaps with option 1).

**Needs user approval before anyone proceeds:** creating accounts (Tencent Cloud intl, Tripo, Meshy, Rodin), uploading our design images to third-party clouds (Tencent's ToS also forbids using Outputs to build competing models, which is fine for us), and any payment (Tripo API top-up ≥ $10, Rodin $1.5/credit, Tencent past 100 free credits). Licence note: Hunyuan open weights exclude the EU/UK/KR; Meshy free outputs are CC BY; Tripo free outputs are non-commercial.
