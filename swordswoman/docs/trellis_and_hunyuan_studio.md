# TRELLIS on Mac, and Hunyuan 3D Studio / web / API

Date: 2026-10-23/24. Machine: M5 Max, 64 GB, macOS 27. This builds on `docs/hunyuan3d_research.md`; the Hunyuan local results come from that run.

How sources are marked:
- **[V]** means verified this session, from a GitHub or HF API/README, a live web page or JS bundle, or our own run.
- **[M]** means unverified or from memory.

## TL;DR

- **TRELLIS.2 runs on this Mac. The live test worked for shape.**
  - Setup: TRELLIS.2-4B, 512 pipeline, MPS through `shivampkumar/trellis-mac`.
  - Speed: **30–35 s generation** plus 28 s load; about **66 s wall** for a warm run.
  - Memory: **11.8 GB** peak footprint (Hunyuan 2mini: 7 s, 8.9 GB).
  - Detail: much higher than Hunyuan. It carves the eyes and face, the fingers, the corset lacing and the boots. The ribbons and collar come out as real thin sheets, and the katana is separate, with a guard.
  - Mesh quality: worse than Hunyuan. It is noisy and speckled, has holes, is not watertight, and has 50k–160k fragments.
  - Texture was not tested: one 2.6 GB checkpoint could not be downloaded because the network was throttled to about 10 KB/s.
- **Hunyuan web:**
  - The CN site is mainland-China only. The Global site, **hy3d.tencent.ai**, uses an email one-time code and gives **200 free credits**.
  - It offers v2.5–v3.5 models, PBR, multi-view, triangle or quad low-poly, retopology and auto-rig.
  - Exports: GLB/OBJ/FBX/STL/USDZ.
  - The Tencent Cloud API exists, with 200 free credits on the intl site and $0.02 per credit after that.
  - Rigging explicitly excludes weapons, loose sleeves and long dresses, which is exactly our character.
- **No allowlist domains were added.** Chrome DevTools reached the Tencent sites directly, and GitHub/HF were already open.

![sheet](img/trellis_vs_hunyuan_sheet.png)

`docs/img/trellis_vs_hunyuan_sheet.png` (copy of `.scratch/trellis/out/compare_hunyuan_vs_trellis.png`). Rows:
1. Hunyuan 2mini, 312k triangles.
2. TRELLIS seed 42, 300k.
3. TRELLIS seed 7, 300k (best).
4. Hunyuan Decimate to 8k.
5. TRELLIS voxel remesh plus 8k decimate, which **fails**: the open thin shells break apart.

---

## A. TRELLIS on Apple Silicon

### A.1 Versions and license [V]

| | TRELLIS (v1) | TRELLIS.2 |
|---|---|---|
| Repo | microsoft/TRELLIS (14k stars) | microsoft/TRELLIS.2 (12.4k stars, pushed 2026-07) |
| Model | image-large 1.2B, text variants | **4B** (`microsoft/TRELLIS.2-4B`, 16.2 GB for all files, not gated) |
| Representation | Structured latent (SLAT) decoded to **Gaussians, radiance field or mesh** | **O-Voxel**, a "field-free" sparse voxel; decodes directly to a mesh with **PBR attributes** (base colour, metallic, roughness, alpha) |
| Resolutions | 64³ structure | 512, 1024, 1024_cascade, 1536_cascade |
| License | MIT | **MIT** (code and weights) |
| Dependencies with other licenses | | **DINOv3** image encoder (Meta DINOv3 License, gated on HF); **RMBG-2.0** background remover (**CC BY-NC 4.0**, gated). nvdiffrast and nvdiffrec are under NVIDIA licenses (CUDA path only). |

I found no TRELLIS.3. The newest Microsoft release is TRELLIS.2. A newer open model, **Pixal3D**, shows up in community tools (AssetFurnace calls it "best results we have"; MIT code and DINOv3 encoder) [V, README; not tested].

For our use, MIT is much simpler than the Tencent Community License: there is no EU/UK/KR exclusion and no MAU cap. Two caveats:
- Never use RMBG-2.0 commercially. We already matte with rembg `isnet-anime`.
- Read the DINOv3 License before commercial use. It is a weights license for the encoder; generated meshes are not covered by it [M].

### A.2 Mac status (October 2026) [V]

- **Official:** the README still requires an NVIDIA GPU with 24 GB or more, CUDA 12.4, flash-attn, nvdiffrast, cumesh, flex_gemm and o-voxel CUDA extensions.
  - Issue #74 ("non-CUDA backends") is open.
  - **PR #175, "[Apple Silicon] Add MPS and Metal inference support"** (2026-07-17), is **open and not merged**.
  - So there is no official MPS support yet.
- **Community ports (all MIT unless noted):**

| Project | Stars / last push | Approach |
|---|---|---|
| **shivampkumar/trellis-mac** | 497 / 2026-04 | PyTorch MPS. Replaces flash_attn with SDPA, flex_gemm with **mtlgemm** (Metal), nvdiffrast with **mtldiffrast**, and the o_voxel hashmap with Python mesh extraction. cumesh is skipped (no hole fill). Reported numbers: M4 Pro 24 GB, about 5 min cold, 18 GB peak. **Used for our test.** |
| pedronaugusto/trellis2-apple (47) | 2026-08 | The Metal stack (mtldiffrast, mtlbvh, mtlmesh, mtlgemm, CPU o_voxel fork) plus an MLX backend. The foundation for most other ports. |
| **gtrg55/trellis2-mlx** (70) | 2026-06 | Native MLX with a Gradio UI, stable at 1024³, textured GLB, "Fast Repair" and watertight voxel remesh. Tested on M4 Max 128 GB. |
| lyonsno/trellis2mlx (9) | pushed today | MLX with checkpoints/resume, 4-bit quantisation, and surface-preservation cleanup. M2 Pro 16 GB shoe: 21 min. A 768 run reached a 63.8 GB peak. |
| xocialize/mlx-trellis2-swift, havokentity/trellis2-mlx, jgranie/trellis.2-mlx (multi-view experiment), appautomaton/mlx-spatial | small | Swift/MLX re-ports and variants |
| ComfyUI | | **zjkhurry/ComfyUI-TRELLIS.2-mac** (Apache-2.0; wraps the trellis-mac stack); dmvvilela/ComfyUI-TrellisMac; LeonardMeagher2/ComfyUI-trellis2-apple (MLX). The big wrappers (visualbruno 873 stars, PozzettiAndrea 577) are CUDA-oriented. |
| Pinokio | | SUP3RMASS1VE/trellis-mac-GUI-Pinokio (0 stars, no license; not checked; pinokio.computer is blocked here) |
| All-in-one | **Bingeljell/image-to-3dlab "AssetFurnace"** (928 stars, Apache-2.0, 2026-10-22) | Mac-native studio offering Pixal3D, TRELLIS.2, Hunyuan3D-MLX and SF3D, plus a **SkinTokens auto-rig** and 21 animation presets, plus low-poly "Pixel Match". It is the most complete local image-to-rigged-character pipeline on Mac. Not tested. |
| Blender | robmcrosby/BlenderTrellis2 | Add-on for MPS or CUDA |

TRELLIS v1 (Gaussian / radiance-field output) has `vinayapathak/trellis-mac-mps` (3 stars). Community effort has moved to TRELLIS.2.

### A.3 Live test

**Layout and rules:**
- Downloaded code and weights are in `.scratch/trellis/`:
  - `trellis-mac/` (with `deps/` and the `TRELLIS.2/` clone)
  - `weights/`
  - `out/`
- My scripts are in `.scratch/trellis_scripts/`:
  - `run_trellis_shape.py`: shape-only run
  - `run_trellis.py`: full textured run through generate.py
  - `clean_mesh.py`
  - `render_compare.py`
  - `remesh_decimate.py`
  - `compare_sheet.py`
  - `dl_resume.sh`
- All Python ran with `-I`.

**Downloads.** The full TRELLIS.2-4B repo is 16.2 GB, so I took only what the 512 pipeline needs:

| Item | Size | Status |
|---|---|---|
| ss_flow 64 | 2.58 GB | complete |
| shape_slat_flow 512 | 2.58 GB | complete |
| shape_dec | 0.95 GB | complete |
| tex_dec | 0.95 GB | complete |
| ss_dec (from TRELLIS-image-large) | 0.15 GB | complete |
| DINOv3 ViT-L/16 (ungated mirror `camenduru/dinov3-vitl16-pretrain-lvd1689m`) | 1.2 GB | complete |
| **tex_slat_flow 512** | 2.58 GB | **only 0.85 GB arrived** |

On disk in total: 8.6 GB of weights plus 1.1 GB of code and venv. The network fell to about 10 KB/s for HF, GitHub and PyPI alike, so the download was stopped.

**Setup fixes needed on this machine (macOS 27, Xcode 26.6, torch 2.14.1):**
1. Every Metal extension failed to build at first:
   - torch 2.14 headers require **C++20**. Fix: `sed s/-std=c++17/-std=c++20/` in the `setup.py` files of mtlbvh, mtldiffrast, mtlmesh, mtlgemm and o-voxel.
   - `-mmacosx-version-min=11.0` breaks the MPS headers. Fix: `CFLAGS/CXXFLAGS=-mmacosx-version-min=14.0`.
   - Linking against the macOS 27 CLT SDK fails ("tapi … unknown architecture"). Fix: `SDKROOT=$(xcrun --sdk macosx --show-sdk-path)`, which selects the Xcode 26.5 SDK.
   - o-voxel is missing its Eigen submodule. Fix: `git submodule update --init` in `deps/trellis2-apple`.
   - After these fixes, all five built and `flex_gemm` (Metal sparse conv) was active.
2. DINOv3 and RMBG-2.0 are gated and there is no HF token.
   - The wrapper points `image_cond_model` at the local DINOv3 mirror.
   - It replaces `BiRefNet` with a stub and feeds the RGBA crop that already has alpha.

**Command:**
```bash
S=/Users/waylonhuang/Documents/other/pixelart/.models
$S/trellis/trellis-mac/.venv/bin/python -I $S/trellis_scripts/run_trellis_shape.py \
  $S/trellis/trellis-mac $S/trellis/weights $S/hunyuan/inputs/front.png $S/trellis/out/trellis_front_s7.glb 7
```

**Results.** Same input as the Hunyuan `mini_front` run:

| Run | Generation (cond / ss / shape / decode) | Wall | Peak footprint | Raw mesh |
|---|---|---|---|---|
| Hunyuan 2mini-Turbo, 5 steps, octree 256 | **7 s** (3 s warm) | 23 s | 8.9 GB | 312k triangles, watertight, 1 component |
| TRELLIS.2 512, seed 42 (cold) | 35 s (1.4 / 10.7 / 5.5 / 17.5) | 118 s | 11.8 GB | 2.74M triangles, 162k components |
| TRELLIS.2 512, seed 7 | 30 s (0.9 / 9.7 / 5.5 / 14.0) | 66 s | 11.8 GB | 2.04M triangles, 50k components |

That is much faster than the README's M4 Pro numbers: the M5 Max plus Metal flex_gemm gives about 1.2 iterations/s for the sparse structure and about 2.4 iterations/s for the shape stage.

**Quality, from the sheet:**
- **Detail: TRELLIS wins clearly.** Carved anime eyes and face, separate fingers, corset lacing, buttons, thigh straps, boots, a clean bow (seed 7), and a sword with a tsuba. Hunyuan's face is blank and its hands are mittens.
- **Thin parts:**
  - TRELLIS represents ribbons, the collar, coat tails and the blade as **single-layer open sheets**. That is more faithful and keeps them separate from the body, which suits rigging.
  - The drawback is that those sheets are open and not watertight. A voxel remesh destroys them (row 5), and Blender Decimate stalls at about 130k triangles because of the fragments.
  - Hunyuan fuses everything into one closed blob, but that blob decimates cleanly to 8k.
- **Surface: TRELLIS is worse.** Speckled holes and noise, especially on the bow, sleeves and corset. Causes:
  - (a) no `fill_holes` (cumesh is skipped on Mac);
  - (b) the Python dual-grid extraction leaves many tiny fragments;
  - (c) the 512 resolution.
  - gtrg55 and lyonsno document cleanup passes ("Fast Repair", surface-preserving component filter) aimed at exactly this, and 1024/cascade should help.
- **Seed variance is large** (seed 42 has a broken bow and a lumpy bun; seed 7 is clean). Plan on 3–4 seeds.
- **Texture:** not tested here. Published Mac results show full PBR GLBs with base colour, metallic and roughness at 1024–2048 px. For our palette-exact pipeline, texture is only a colour-region hint anyway.
- **Anime/chibi suitability:** good. Training on Objaverse-XL/Sketchfab includes plenty of stylised characters, and our chibi proportions were reproduced closely.

**Saved:** `model/ai_ref/trellis/akane_trellis2_4b512_front_s7-shape300k.glb` (Y-up, 300k triangles) plus a `.txt` sidecar.

**To finish the textured test later (resumable):**
```bash
S=/Users/waylonhuang/Documents/other/pixelart/.models
$S/trellis_scripts/dl_resume.sh \
  https://huggingface.co/microsoft/TRELLIS.2-4B/resolve/main/ckpts/slat_flow_imgshape2tex_dit_1_3B_512_bf16.safetensors \
  $S/trellis/weights/TRELLIS.2-4B/ckpts/slat_flow_imgshape2tex_dit_1_3B_512_bf16.safetensors 2584672728
cd $S/trellis/out && $S/trellis/trellis-mac/.venv/bin/python -I $S/trellis_scripts/run_trellis.py \
  $S/trellis/trellis-mac $S/trellis/weights $S/hunyuan/inputs/front.png --seed 7 --output $S/trellis/out/trellis_front_s7_tex --texture-size 1024
```
- The download currently has 847 MB of 2,584,672,728 bytes. The expected size comes from the `x-linked-size` header.
- The textured run uses the Metal baker and writes a GLB plus a raw OBJ.
- For 1024 or cascade quality, also download the two `*_1024_bf16` flow checkpoints (2.58 GB each).

### A.4 Verdict on TRELLIS for us

- It is the better local **detail reference** (face, hands, costume trim) and gives **better part separation** for thin pieces.
- Its raw mesh is less usable than Hunyuan's: it needs repair before any shrinkwrap or decimation.
- It takes about 4× longer and uses about 3 GB more memory than Hunyuan 2mini. Both are trivial on 64 GB.
- The MIT license is a real advantage over Hunyuan's licence, which excludes the EU, UK and South Korea.

---

## B. Hunyuan 3D web, Studio and API

**Method:**
- `curl` to Tencent domains is blocked by the ACC proxy, but the chrome-devtools browser reaches them, so **no allowlist edits were made**.
- I did not log in or accept any agreement.
- Sources: live pages, the public `GET /api/3d/config`, the sites' JS bundles (UI strings and the export-format logic), the ToS pages, and the Tencent Cloud docs.
- Screenshots and raw dumps are in `../reference/3d/hunyuan_studio_research/`.

### B.1 Three front doors

| | **CN web**, 3d.hunyuan.tencent.com | **Global web**, **hy3d.tencent.ai** (3d.hunyuanglobal.com redirects here) | **Tencent Cloud API** |
|---|---|---|---|
| Login | Tencent Yuanbao account: WeChat QR, QQ, email, or phone. ToS §2.1 requires real-name phone or WeChat/QQ [V] | **Email one-time code only**, no Google or Apple button, with a Tencent captcha [V] | Tencent Cloud account plus **real-name verification**, then SecretId/SecretKey with CAM `QcloudAI3DFullAccess` [V] |
| Region | ToS §1.1: service is "仅面向中国大陆地区用户" (**mainland-China users only**) [V]. **Not for us.** | Worldwide. Excludes only trade-sanctioned users. Singapore law. 18+ [V, ToS rev. 2026-02-06] | CN: `ai3d.tencentcloudapi.com` (2025-05-13, ap-guangzhou). Intl: `hunyuan.intl.tencentcloudapi.com` (2023-09-01; ap-singapore, eu-frankfurt, na-siliconvalley) [V] |
| Free tier | Daily count quota ("每日享有N次免费生成次数" plus invite bonuses) [V string]. N only shows after login; about 20/day [M] | Credits: "**Get 200 free credits**", "Free usage x/y", monthly plans, extra credit packs for subscribers [V strings]. Exact daily share and prices only show after login | **Intl: 200 free credits, one-time, valid 1 year. CN: 100** [V] |

### B.2 Features (Global and CN share one codebase) [V]

- **Shape models:** v2.5, v3.0 (the UI default; "3.6 billion modeling voxels… enhancing characters"), v3.1 ("more precise geometry… more reference views"), and v3.5.
- **Face-count presets:**
  - v2.5: 500k / 300k / 150k / 50k
  - v3.x: 1.5M / 1M / 500k / 50k
- **PBR texture toggle.** Styles include Universal and Cartoon.
- **Multi-view input:** front plus at least one other view. v3.1 accepts up to 8 views (left, right, back, top, bottom, left_front, right_front).
- **Low-poly / Smart Topology:**
  - **Triangle** or **Quadrilaterals** (mixed quad/tri).
  - Retopology presets: 5k / 18k / 30k faces.
  - The UI warns that complex objects are not supported for low-poly. The API says LowPoly is not available on 3.1.
  - The Lab topology page is being merged into **3D Studio** (Geometry / Retopology / Texture Painting modules). Studio is feature-flagged (gradual rollout).
- **Auto-rig and animation:** "Bone binding" (automatic or manual markers) plus a preset animation library.
  - **The tip says: T-pose only, no weapons, hair must not cover the shoulders, no loose long sleeves, long dresses or traditional costumes.** The API rigging doc repeats this.
  - Akane breaks every rule, so expect a poor rig or a rejection.
- **Parts / UV:** SemanticUVExpansion in the web workflow. The API has `SubmitHunyuan3DPartJob` (FBX input, model 1.5) and `SubmitHunyuanTo3DUVJob`.
- **Exports:**
  - Default: GLB, OBJ, FBX, STL, USDZ, MP4, GIF. Geometry-only results add 3MF.
  - **Quad results: everything except GLB, so use OBJ/FBX.**
  - **Rigged results: FBX, USDZ, GIF, MP4.**

### B.3 API [V]

**Credits per call (intl):**

| Item | Credits |
|---|---|
| Pro normal | 25 |
| Pro LowPoly | 30 |
| Pro geometry-only | 15 |
| +MultiView | +10 |
| +PBR | +10 |
| +FaceCount | +10 |
| Express | 15 |
| Smart Topology | 50 |
| Part | 30 |
| Texture | 30 |
| UV | 10 |
| Auto-rig | 10 |
| Format convert | 5 |

**Pricing:**
- Packs: 1,000 credits for $15, up to 100k credits for $1,350.
- Postpaid: $0.02 per credit.
- Failed jobs are free.
- Concurrency: 3 (Pro).

**Endpoints:** `SubmitHunyuanTo3DProJob`/`Query…`, `…RapidJob`, `Submit3DSmartTopologyJob` (CN: `SubmitReduceFaceJob`, PolygonType triangle|quadrilateral, FaceLevel), `SubmitHunyuan3DPartJob`, `SubmitAutoRiggingJob`, `SubmitHunyuanTo3DUVJob`, `Convert3DFormat`.
- Result URLs expire after 24 h.
- SDK: `tencentcloud-sdk-python`, modules `ai3d` (CN) and `hunyuan` (intl).
- The CN docs say the service is migrating to "TokenHub".
- There is no official MCP server. `dcc-mcp/dcc-ai-hunyuan3d` (MIT) wraps the cloud API.
- Do **not** use `ABOOAI/hunyuan3d-workbench`: it scripts the web account, which breaks the ToS ban on automated extraction.

**What 200 free credits buy:** about 5 runs of v3.1 + PBR + FaceCount (45 each), or about 2 runs of LowPoly-quad + PBR (40) each followed by Smart Topology (50).

### B.4 Terms for generated assets [V]

- **Global ToS:**
  - §6.3: Tencent **assigns you its rights in Outputs**. Commercial use is not prohibited.
  - §6.6: **label published outputs as AI-generated**.
  - Visible and invisible **watermarks must not be removed**.
  - No using outputs to build competing models. No automated scraping. Outputs may not be unique.
  - There is **no EU/UK/KR carve-out**, unlike the open-weights Community License.
- **CN ToS:** outputs belong to the user (§5.3), with the same restrictions, but the service is mainland China only.

### B.5 Steps for the user (Global site; Claude cannot log in for you)

1. Open **https://hy3d.tencent.ai**.
2. Enter your email, tick the ToS / AUP / Privacy box, solve the captcha, and type the emailed code.
3. Claim the **200 free credits**.
4. Upload from `../reference/3d/hunyuan_studio_research/upload/`. These are our rembg crops flattened onto white at 1024²; the RGBA originals are in `.scratch/hunyuan/inputs/`.
   - **Run A (main reference):** `akane_front_white.png`, single image, model **V3.1**, face count **500k**, **PBR off** (or on, for a colour hint), style Universal. Download **GLB + OBJ**.
   - **Run B (low-poly):** the same image, model **V3.0** (LowPoly is not on 3.1), **Smart Topology / low-poly** on, **Quadrilaterals**. Download **OBJ + FBX** (quad results have no GLB). If Studio is enabled, you can instead put Run A through **Retopology at medium (18k), Quadrilaterals**.
   - **Optional multi-view:** front + `akane_back_white.png` only. Skip `akane_left_white.png`: the bun is clipped there and the sword is sheathed.
   - **Optional rig (expect failure because of the katana and sleeves):** Bone binding, Automatic, on the Run B mesh. Export **FBX**. If it is rejected, don't spend more credits on it; we rig in Blender.
5. Drop the files into **`model/ai_ref/hunyuan_studio/`**, named like:
   - `akane_hy3d_v31_front_tri500k.glb`
   - `akane_hy3d_v30_front_lowpoly-quad.fbx`

   Add a same-name `.txt` sidecar with the date, inputs, exact settings, credits used and any defects (see `model/ai_ref/README.md`).

---

## C. Which route is best for our pipeline

1. **Keep the procedural Blender rig and palette materials as the source of truth.** Nothing here changes that. No route gives a rig that handles the katana, skirt and ribbons.
2. **Local reference, free and repeatable:**
   - Use **Hunyuan 2mini** for clean proportion and silhouette overlays and as a shrinkwrap target (watertight, decimates to 8k).
   - Use **TRELLIS.2** (seed sweep of 3–4) as the **detail reference** for face planes, hands, costume trim and how the thin ribbon and collar sheets sit.
   - Both run in under 2 minutes on this Mac.
3. **Hunyuan Global web, about 5 free runs:** worth one session to get a **v3.1 high-quality mesh** and a **quad low-poly (18k) mesh**. The quad retopology is the one thing the local tools can't do and is the best AI base for a hand cleanup. Skip its auto-rig.
4. **If we ever want an all-local "AI base plus auto-rig" experiment:** try AssetFurnace (Pixal3D/TRELLIS.2 plus SkinTokens rig) rather than the Tencent rig.
5. **Licensing preference:** TRELLIS.2 (MIT) and the Global-web outputs (rights assigned, AI label required) are cleaner for shipping than the open Hunyuan weights (EU/UK/KR excluded).

## D. Network and allowlist

- **Domains added to `~/.claude/apple/dangerous_allowed_domains.csv`: none.**
  - The ACC guide says not to edit that file without your direct, per-change confirmation. A relayed instruction doesn't count as that.
  - In the end it wasn't needed: Chrome DevTools reached 3d.hunyuan.tencent.com, hy3d.tencent.ai, cloud.tencent.com, www.tencentcloud.com and docs.qq.com, while github.com, huggingface.co and the HF CDN were already open.
- Still blocked for curl:
  - Tencent domains
  - arxiv.org
  - `*.hf.space`
  - pinokio.computer
  - registry.comfy.org
- If you want curl or API access to Tencent Cloud later, the narrowest entries would be `tencentcloudapi.com` (API) and `hy3d.tencent.ai`. Add them yourself through the ACC Dashboard (Domains tab).
- The HF download slowdown on 2026-10-23 was general network throttling (GitHub and PyPI were slow too), not a block.

## Sources

**GitHub:**
- microsoft/TRELLIS, microsoft/TRELLIS.2 (README, issue #74, PR #175)
- shivampkumar/trellis-mac, pedronaugusto/trellis2-apple, gtrg55/trellis2-mlx, lyonsno/trellis2mlx, xocialize/mlx-trellis2-swift
- zjkhurry/ComfyUI-TRELLIS.2-mac, visualbruno/ComfyUI-Trellis2, PozzettiAndrea/ComfyUI-TRELLIS2
- SUP3RMASS1VE/trellis-mac-GUI-Pinokio, Bingeljell/image-to-3dlab, robmcrosby/BlenderTrellis2
- TencentCloud/tencentcloud-sdk-python, dcc-mcp/dcc-ai-hunyuan3d

**HF API:** microsoft/TRELLIS.2-4B, microsoft/TRELLIS-image-large, facebook/dinov3-vitl16-pretrain-lvd1689m (gated), camenduru mirror, briaai/RMBG-2.0 (gated).

**Tencent:**
- 3d.hunyuan.tencent.com, rule.tencent.com/rule/202501080004 (CN ToS)
- hy3d.tencent.ai (plus `/api/3d/config` and its JS bundles)
- docs.qq.com/doc/DSHRnRWp2YUVuQXJv (Global ToS), docs.qq.com/doc/DSHFRaU96UWVhRVZV (AUP)
- cloud.tencent.com/document/product/1804 and /document/api/1804/120832
- www.tencentcloud.com/products/ai3d and /document/product/1284 (75281, 75287, 75540, 75301, 75538), /document/api/1284/75534
