# State of the art: local, open-weight image-to-3D (October 2026), for the Akane chibi pipeline

Date: 2026-10-24. Machine: M5 Max, 64 GB unified memory, macOS 27, no NVIDIA GPU.
This builds on `docs/hunyuan3d_research.md` and `docs/trellis_and_hunyuan_studio.md`. Hunyuan3D-2mini (MPS) and TRELLIS.2-4B 512 (trellis-mac, MPS) already run here.

This is a desk survey only. Nothing was installed and no weights were downloaded. Raw API and README dumps are in `.scratch/sota_survey/data/`.

How sources are marked:
- **[V]** means verified this session from a primary source: a GitHub README, LICENSE or API record, a Hugging Face model API record or card, or a Hugging Face Papers abstract (the arXiv mirror).
- **[M]** means it comes from memory or secondary knowledge and was not re-verified.
- **[U]** means I could not determine it.

arxiv.org and `*.hf.space` are still blocked for curl, so abstracts came from `huggingface.co/api/papers/<id>`. GitHub was reached unauthenticated (60 requests/hour).

---

## TL;DR

- **The biggest change since our last test is Pixal3D.**
  - Who and when: TencentARC with Tsinghua, SIGGRAPH 2026. Released May 2026; multi-view code followed in September 2026 [V].
  - Licence: MIT code and weights [V].
  - What it is: a **fine-tune of TRELLIS.2** that replaces cross-attention with **pixel-aligned back-projection conditioning**. Its claimed advantage is better faithfulness to the input image.
  - Inputs: single view or **multi-view with camera poses**, so front plus back works.
  - Mac support: it runs **on Apple Silicon today** through a C++/GGML Metal engine (`raven38/pixal3d.cpp`, a fork of `pwilkin/trellis.cpp`) and through MLX ports.
  - The AssetFurnace Mac studio makes it its default backend. Its stated reasons: "best results we have", and it "keeps flat, saturated colours" where TRELLIS.2 drifts on flat or cel-shaded art [V].
- **We may not need a different model to fix TRELLIS.2's main defect.** `pwilkin/trellis.cpp` (MIT, pushed 2026-10-23) ports TRELLIS.2's *reference* post-process to Metal: weld, hole fill, narrow-band UDF remesh into **a single watertight manifold**, then CuMesh-style QEM decimation. That directly addresses the speckled, holey, 50k–160k-fragment meshes we got from the Python trellis-mac port. It also runs the 1024 cascade. Verified on an M5 with 24 GB: a res-512 textured GLB took 9 min 21 s with a 5.6 GB peak [V].
- **Rigging has a credible open, Mac-capable successor to UniRig: SkinTokens / TokenRig** (VAST, MIT, 2026-02).
  - It runs on Metal via a Rust/candle CLI (`chris-straka/skintokens`: about 32 s per rig on an M4) and via `localai-org/skin-tokens.cpp` (GGML) [V].
  - **AniGen** (VAST, SIGGRAPH 2026) generates mesh, skeleton and skin weights together from one image, but it is **CUDA-only** (at least 18 GB, spconv, nvdiffrast) and I found no Mac port [V].
- **Part-level TRELLIS.2: KaiNinja** (AlayaLab, arXiv 2609.15659). Its MIT weights went up on 2026-10-23, but **its inference code is not released yet** [V]. Worth watching: separate sword, bow and ribbons straight out of the generator would suit our rig.
- **Nothing anime-specific beats the general models.** CharacterGen (2024) and StdGEN (CVPR 2025) are older, lower-resolution, CUDA-only multiview-plus-LRM pipelines. StdGEN's layered body, clothes and hair output is the one interesting idea [V].
- **Native low-poly and artist-mesh generators are still not useful for a full character.**
  - The open ones (MeshAnything V2 at 1.6k faces, BPT, DeepMesh, FastMesh) are CUDA-oriented and cap at a few thousand faces.
  - The 2026 flow-based generators (Meshy T2, TaoFlowForge, MeshFlow, TriFlow, LATO, QuadLink, MeshWeaver) are papers only, or "release coming".
- **Answer to "does anything clearly beat TRELLIS.2 for anime chibi on a Mac?"** Nothing is *proven* to. Pixal3D is the only candidate with a credible claim: it is the same backbone with better input fidelity and better flat-colour handling, plus front+back multi-view, and it is Mac-runnable. No anime or chibi benchmark exists, so we have to test it ourselves.

---

## 1. Ranked local options for us

| Rank | Option | Why | Mac route | Licence |
|---|---|---|---|---|
| **1** | **Pixal3D** (TRELLIS.2 fine-tune, pixel-aligned), single-view *and* front+back multi-view | Same O-Voxel detail as TRELLIS.2 (open thin sheets for ribbons and collar), but the geometry is tied to our input pixels. Reported to keep flat colours, which matters for anime art. The multi-view mode lets us give it our consistent front and back views and skip the inconsistent side view. | `raven38/pixal3d.cpp` (Metal prebuilt; weights `raven38/pixal3d-sv-q8_0-v1`, about 8.4 GB), or AssetFurnace's `bootstrap_pixal3d.py`. MLX ports: `lyonsno/pixal3d-mlx` / `PHMFG/pixal-studio` (M5 Pro 24 GB: about 7 min at 1024, 8.8 GiB peak), `mlx-spatial` (in development). | MIT; the DINOv3 encoder is under the DINOv3 Licence |
| **2** | **TRELLIS.2-4B through `trellis.cpp`** (1024 cascade plus reference remesh) | The model we already like for detail, but with the missing hole-fill and remesh step, so the output is one watertight manifold that can be decimated. Same engine as rank 1, so the comparison is cheap. | `pwilkin/trellis.cpp` (Metal default on macOS; about 16.5 GB of GGUF weights) | MIT plus DINOv3 Licence |
| **3** | **Keep Hunyuan3D-2mini / 2.1** as the fast watertight silhouette gauge. Optionally add **SkinTokens** as an auto-rig comparison point. | Seven seconds per run, a clean closed shell that decimates to 8k triangles. Still the best shrinkwrap target. SkinTokens is the best open auto-rig on Mac today, used only to compare against our 40-bone rig. | Existing `.scratch/hunyuan` setup; SkinTokens via `chris-straka/skintokens` (Metal) or AssetFurnace | Tencent Community Licence (excludes EU, UK and KR); SkinTokens MIT |

Watch list, not runnable here yet:
- **KaiNinja** (part-level TRELLIS.2; inference code pending).
- **AniGen** (rigged generation; CUDA only).
- **Meshy T2** (native artist mesh with multi-part output and vertex budget; "preparing open-source release" since 2026-08-03).
- **Hunyuan3D 3.x** (closed).

---

## 2. Candidate table

Columns: Date | Weights and licence | Output | Apple Silicon | Quality notes (anime and thin parts).

### 2.1 General image-to-3D shape and texture

| Model | Date | Weights / licence | Output | Apple Silicon | Notes |
|---|---|---|---|---|---|
| **TRELLIS.2-4B** (Microsoft) | 2025-12 | Open, **MIT**. The DINOv3 encoder is under a separate licence and gated; RMBG-2.0 is CC BY-NC [V] | O-Voxel mesh with PBR (base colour, metallic, roughness, alpha). Open and non-manifold surfaces allowed. 512 / 1024 / 1536 cascade. | No official support. PR #175 (MPS/Metal) **still open, not merged** (last updated 2026-08-31) [V]. Community: trellis-mac (we use it), trellis2-apple, trellis2-mlx (gtrg55, lyonsno), mlx-trellis2-swift, mlx-spatial, ComfyUI-TRELLIS.2-mac, **trellis.cpp (Metal, reference post-process)** [V] | Our baseline. Best open detail: carved face, fingers, lacing, separate katana. Thin parts come out as single sheets. On Mac the Python mesh is holey and fragmented. Colour drift on flat or vector art; 1024 cascade bleaches colour compared with 512 (AssetFurnace doc) [V]. |
| **Pixal3D** (TencentARC / Tsinghua) | Paper 2026-05-11. Code and weights May 2026. Multi-view code 2026-09 [V] | Open, **MIT** (`TencentARC/Pixal3D`, also `Pixal3D-D`). Many mirrors and quantised builds (GGUF, 4-bit, `Comfy-Org/Pixal3D`) [V] | Textured PBR GLB. Single view at 1024 (single-view mode) / 1536. **Multi-view with `transforms.json` cameras.** Output is pixel-aligned (generated in the input camera frame, not a canonical frame). | Upstream needs CUDA (natten, flash-attn or SDPA). **Metal: pixal3d.cpp / trellis.cpp `--model pixal3d`. MLX: pixal3d-mlx, pixal-studio, mlx-spatial (in development).** AssetFurnace default [V]. Base M5 32 GB: about 6 min per image (AssetFurnace) [V]. | "Near-reconstruction-level fidelity" (abstract) [V]. AssetFurnace: best results, keeps flat saturated colours, front+back mode [V]. No anime benchmark [U]. Needs a camera FOV (MoGe-2 estimate upstream; `--fov` flag in the C++ port). For our orthographic art, use a narrow FOV of about 20° [M]. |
| **Hunyuan3D 2.0 / 2mini / 2mv / 2.1** | 2025-01 to 2025-06 | Open, Tencent Hunyuan Community Licence (**not EU, UK or KR**; MAU cap) [V] | Watertight SDF mesh. 2.1 adds PBR paint. | Shape runs on MPS (we tested 2mini). MLX ports: dgrauet 2.1, Xiong / Hunyuan3D-Swift, ddalcu mlx-serve with UniRig [V] | Best clean silhouette; blobby; fuses thin parts; blank face. Already tested. |
| Hunyuan3D 2.5 / 3.0 / 3.1 / 3.5 | 2025-06 onward | **Closed** (web and API only). No GitHub repo [V] | | n/a | See the studio doc. |
| Hunyuan3D-Omni | 2025-09 | Open, Tencent licence [V] | Shape conditioned on pose skeleton, bbox, point cloud or voxels | Shape is likely MPS-able like 2.1 [M] | Useful to force an A-pose; not tested. |
| Hunyuan3D-Buffalo 1.0 | 2026-08 | **Paper only** [V] | | | |
| **UltraShape 1.0** (PKU-Yuan) | 2025-12-26 | Open, HF `infinith/UltraShape` **Apache-2.0** (GitHub licence NOASSERTION) [V] | Watertight geometry; two stages (coarse, then voxel refine). Shape only. | CUDA (cu121, cubvh) [V]; no Mac port found | "Competitive with open-source methods" (self-reported). Watertight, so thin ribbons get thickened [M]. |
| Step1X-3D (StepFun) | 2025-05 | Open, **Apache-2.0**. 1.3B geometry plus 3.5B SDXL texture [V] | Watertight TSDF mesh plus texture; label-conditioned (symmetry, sharp edges) variant | CUDA. No MPS port found (only a ComfyUI wrapper) [V] | Hunyuan-2-class vecset. No reason to prefer it over 2mini here. |
| Direct3D-S2 (DreamTech) | 2025-05 | Open, **MIT**. v1.0 and v1.1 only; the announced "v1.2 enhanced character generation" is **not on HF** [V] | Sparse SDF at 1024³, watertight, shape only | CUDA (sparse attention kernels; 24 GB at 1024) [V]; no Mac port | High-resolution shapes. Pixal3D's paper branch was built on it [V]. |
| Sparc3D | 2025-05 | **No code or weights**. The repo has only a README and citation [V] | | | Commercial Hitem3D lineage [M]. |
| Hi3DGen / Stable3DGen (Stable-X) | 2025-03 | Open, **MIT**, `Stable-X/trellis-normal-v0-1` [V] | Normal-bridged TRELLIS v1 geometry, shape only | NVIDIA libraries removed, so MPS is perhaps feasible [M]; no port found | Superseded by TRELLIS.2 / Pixal3D for detail [M]. |
| TripoSG / TripoSF (VAST) | 2025-03 | Open, **MIT** [V] | TripoSG: 1.5B rectified-flow watertight SDF. TripoSF: SparseFlex VAE at 1024³ (VAE only) | README says "CUDA ≥ 8 GB" [V]; community web apps run TripoSG locally [M] | Clean watertight shapes, Hunyuan-2-class. Closed Tripo 3.x is better [M]. |
| **SAM 3D Objects** (Meta) | 2025-11; encoder weights 2026-06-01 [V] | Open with **manual gating**, SAM Licence (royalty-free, worldwide, commercial OK; trade-control and ITAR exclusions) [V] | Geometry plus texture plus layout. Gaussian PLY with optional GLB. | **MLX port: `mlx-spatial` SAM3D marked "Stable"** [V] | Tuned for real photos with occlusion. Not aimed at stylised characters [M]. Low priority. |
| SAM 3D Body (Meta) | 2025-11 / paper 2026-02 | Gated, SAM Licence [V] | Parametric **MHR human body rig** (pose plus shape) | [U] | Recovers a realistic body pose, not a chibi costume mesh. Could give a pose prior at most. Not useful here. |
| Seed3D 1.0 / 2.0 (ByteDance) | 2025-10 / 2026-04 | **No weights**. The repo README has only a video [V] | | | Closed. |
| UltraShape / Photo3D / FLUX3D / ROAD / SymTRELLIS | 2025-12 to 2026-07 | Mostly paper-only. SymTRELLIS has a code skeleton (2026-07) [V] | | | SymTRELLIS enforces symmetry on TRELLIS.2. Our character is asymmetric (sword, scarf), so it does not apply. |

### 2.2 Parts

| Model | Date | Weights / licence | Output | Apple Silicon | Notes |
|---|---|---|---|---|---|
| **KaiNinja** (AlayaLab) | Paper 2026-09-15; **weights 2026-10-23** [V] | HF `AlayaLab/KaiNinja`, **MIT** (two safetensors: layout flow and SLAT flow) [V] | Part-level TRELLIS.2 (dual-volume O-Voxel), with no segmenter | **Inference code not released** [V] | "Lowers whole-object Chamfer by 40%, raises strict part F-score by 16%" [V]. Best future fit for a separate sword, bow and ribbons. |
| Hunyuan3D-Part (P3-SAM, X-Part) | 2025-09 | Open "light" version [V] | Segmentation plus part completion | [M] partly | See the earlier doc. |
| PartCrafter | 2025-06 | **MIT** [V] | Up to about 16 separate part meshes (TripoSG base) [M] | CUDA [M] | Low resolution per part [M]. |
| PartPacker (NVIDIA) | 2025-06 | **NVIDIA non-commercial** [V] | Dual-volume part packing | CUDA | Not commercial. |
| OmniPart (HKU-MMLab) | 2025-07 | **MIT** (GitHub HKU-MMLab/OmniPart, HF `omnipart/OmniPart`) [V] | bbox-planned parts on TRELLIS v1 | CUDA [M] | |
| FullPart / MegaParts / CubePart / DreamPartGen | 2025-10 to 2026-08 | FullPart: Google Drive weights. MegaParts: MeshCoder repo (MIT). Others: paper only [V] | | CUDA | MegaParts is aimed at CAD-like objects. |

### 2.3 Rigging and animatable generation

| Model | Date | Weights / licence | Output | Apple Silicon | Notes |
|---|---|---|---|---|---|
| **SkinTokens / TokenRig** (VAST) | 2026-02 | **MIT**, HF `VAST-AI/SkinTokens` [V] | Skeleton plus skin weights from a mesh (Qwen3-0.6B autoregressive, GRPO-refined) | Upstream: NVIDIA ≥ 14 GB. **Metal: `chris-straka/skintokens`** (Rust/candle; M4 about 32 s per rig, 3.7 GB peak; humanoid class maps to a 22-bone `DEF-*` skeleton). **`localai-org/skin-tokens.cpp`** (GGML), AssetFurnace rig step [V] | Successor to UniRig, claiming 98–133% better skinning accuracy [V]. Less bleeding across disconnected parts [V], which helps with separate sword and ribbons. |
| UniRig | 2025-04 | MIT [V] | Skeleton plus skin | MLX in ddalcu mlx-serve [V] | Superseded by SkinTokens. |
| **AniGen** (VAST) | 2026-04 (SIGGRAPH 2026) | Code MIT; weights MIT; **bundled CUBVH is non-commercial** [V] | Image to **rigged `mesh.glb`** plus skeleton. TRELLIS-v1-style SS/SLAT flows with S³ (shape, skeleton, skin) fields | **CUDA only**, ≥ 18 GB, Linux [V]; no Mac port found | The only open "image to rigged character in one model". Lower geometric detail than TRELLIS.2 [M]. |
| Rigel3D | 2026-05 | Paper only [V] | | | |
| Puppeteer / MagicArticulate (ByteDance Seed) | 2025-08 / 2025-02 | **Apache-2.0** [V] | Skeleton, skinning, animation. MagicArticulate needs 4.6 GB VRAM [V] | CUDA [M] | |
| Make-It-Animatable / Make-It-Poseable | 2024-12 / 2025-12 (SIGGRAPH Asia 2026) | Apache-2.0 (Animatable) [V]; Poseable has no weights listed [U] | Humanoid rig / latent posing | [U] | |
| RigAnything / Anymate | 2025 | RigAnything [U]; Anymate repo not found [V] | | | |
| Stroke3D | 2026-02 | HF weights [V] | Rigged mesh from 2D strokes plus text | CUDA [M] | Not image-conditioned. |

### 2.4 Anime- and character-specific

| Model | Date | Weights / licence | Output | Apple Silicon | Notes |
|---|---|---|---|---|---|
| StdGEN | 2025-03 (CVPR 2025) | **Apache-2.0** (HF `hyz317/StdGEN`) [V] | A-pose canonicalisation, then multiview, then S-LRM, then refinement. **Separate body, clothes and hair meshes** | CUDA (cu118, xformers) [V] | Trained on VRoid (Anime3D++). Low-polygon, smooth, VRoid look; a katana or hook guard would be lost [M]. Its layering idea is good. |
| CharacterGen | 2024-02 | **Apache-2.0** [V] | 4-view A-pose, then LRM mesh | CUDA [M] | Old; low detail. |
| AniGS / LHM | 2024-12 / 2025-03 | LHM Apache-2.0 [V] | Animatable Gaussian humans (SMPL-X) | CUDA | Realistic-human oriented; Gaussians, not meshes. |
| CHARM | 2025-09 | **GPL-3.0** [V] | Parametric anime **hairstyle** strips (VRM add-on) | CUDA [M] | Interesting for hair cards. GPL. |
| See-through | 2026-02 | Paper only [V] | Anime image to layered 2.5D (Live2D-style) | | 2D, not 3D. |

### 2.5 Native low-poly and artist-mesh

| Model | Date | Weights / licence | Faces | Apple Silicon | Notes |
|---|---|---|---|---|---|
| MeshAnything V2 | 2024-08 | MIT (HF) [V] | ≤ 1,600 [V] | CUDA [M] | Too few faces for a character. |
| BPT (Tencent) | 2024-11 | MIT (HF `whaohan/bpt`) [V] | about 8k [M] | CUDA [M] | |
| DeepMesh | 2025-03 | Apache-2.0, 0.5B [V] | tens of thousands [M] | CUDA [M] | |
| FastMesh (3DV 2026) | 2025-08 | HF V1K / V4K weights; licence NOASSERTION [V] | | CUDA [M] | |
| LLaMA-Mesh | 2024-11 | Llama 3.1 licence [V] | ≤ about 500 [M] | Llama runtimes (MLX feasible) [M] | Toy quality. |
| SATO (SIGGRAPH 2026) | 2026-04 | MIT; **tokenizer only**, inference not released [V] | | | Native UV seams. |
| Meshy T2 | 2026-07 | "Preparing open-source release" (2026-08-03) [V] | vertex budget; multi-part | | The most promising if it ever ships. |
| TaoFlowForge, MeshFlow, TriFlow, LATO, QuadLink, QuadGPT, MeshWeaver, Nautilus, Meshtron | 2025 to 2026-09 | **Paper only** [V] | | | |

Practical answer: at 56 px sprite scale, Blender Decimate or Quadriflow on a clean watertight mesh is still the low-poly route. trellis.cpp's QEM `--faces N` (≥ 1000) does this inside the generator.

### 2.6 Multi-view front-ends

| Model | Date | Licence | Notes |
|---|---|---|---|
| MV-Adapter | 2024-11 | Apache-2.0 [V] | SDXL-based 6-view generator, diffusers. MPS is probably fine [M]. Could produce *consistent* orthographic views for Pixal3D multi-view or Hunyuan 2mv. |
| Era3D | 2024-05 | weights `pengHTYX/MacLab-Era3D-512-6view(-ortho)` [V]; licence [U] | Orthographic 6-view, 512 px. Old. |
| StdGEN / CharacterGen multiview stages | see 2.4 | | A-pose canonicalisation for anime characters. |
| Pixal3D multi-view | 2026-09 | MIT [V] | Takes *real* views plus cameras. Our front and back concept views can go in directly; the inconsistent side view should be skipped. |

---

## 3. Fit for Akane (chibi, red flowing dress, big bow, scarf ribbons, corset, hook-guard katana)

- **Thin parts.** O-Voxel models (TRELLIS.2, Pixal3D, KaiNinja) keep ribbons, collar and blade as single sheets. SDF / vecset models (Hunyuan, Step1X, TripoSG, Direct3D-S2, UltraShape) thicken or fuse them. For a reference mesh, the O-Voxel family is better.
- **Mesh hygiene.** Our TRELLIS problems (holes, fragments, decimation stalling) came from the Mac Python port skipping CuMesh. trellis.cpp and pixal3d.cpp re-implement the reference weld, hole-fill, remesh and QEM steps on Metal. So rank 1 and rank 2 should both decimate cleanly, though this is unverified on our asset.
- **Anime colour.** If we ever use the texture as a colour-region hint, Pixal3D's flat-colour behaviour is an advantage. TRELLIS.2 at 1024 cascade bleaches colour.
- **Rig.** No open tool handles katana, long skirt and ribbons properly. The procedural 40-bone rig stays the source of truth. SkinTokens is only for comparison.
- **Licence.** Pixal3D, TRELLIS.2, KaiNinja and SkinTokens are MIT; the DINOv3 Licence covers the encoder. All are cleaner than Hunyuan's EU/UK/KR exclusion. Avoid PartPacker (non-commercial), AniGen's CUBVH (non-commercial) and RMBG-2.0 (CC BY-NC).

---

## 4. Single best next experiment

Run **Pixal3D vs TRELLIS.2, both through the same Metal C++ engine**, on our existing input `.scratch/hunyuan/inputs/front.png`, and add one Pixal3D **front+back** multi-view run.

1. Get the prebuilt macOS (Metal) `trellis-cli` from `raven38/pixal3d.cpp` releases into its own directory. Weights: `raven38/pixal3d-sv-q8_0-v1` (about 8.4 GB), plus the TRELLIS.2 GGUF set if we want the A/B. Do this only after your OK on downloads.
2. Generate five runs:
   - **Pixal3D single-view at 1024**, seeds 7 and 42, with a narrow `--fov` of about 20° because the art is orthographic.
   - **TRELLIS.2 at 1024 cascade**, seed 7.
   - **Pixal3D multi-view** with `front.png` at azimuth 0 and the back view at azimuth 180, using the shipped `transforms.json` with only two frames.
   - Use `--faces 300000` and also `--faces 8000`.
3. Render with our existing `render_compare.py` / `compare_sheet.py` alongside the Hunyuan 2mini and trellis-mac seed-7 results.
4. Score:
   - watertight or component count;
   - whether the 8k decimation holds the silhouette;
   - fidelity of the bow, ribbons, katana guard and face planes;
   - colour-region accuracy.

If Pixal3D wins, it replaces both current references: one tool for silhouette and detail. Otherwise, keep trellis.cpp TRELLIS.2 1024 as the detail reference.

---

## 5. Sources (all fetched 2026-10-24)

- **GitHub READMEs and API:**
  - TencentARC/Pixal3D
  - raven38/pixal3d.cpp, pwilkin/trellis.cpp
  - Bingeljell/image-to-3dlab (README, `scripts/bootstrap_pixal3d.py`, `docs/trellis2-flat-illustration-colour-drift.md`)
  - PHMFG/pixal-studio, lyonsno/pixal3d-mlx, appautomaton/mlx-spatial
  - microsoft/TRELLIS.2 (PR #175)
  - VAST-AI-Research/AniGen (README, LICENSE), VAST-AI-Research/SkinTokens, VAST-AI-Research/UniRig, VAST-AI-Research/TripoSG, VAST-AI-Research/TripoSF, VAST-AI-Research/HoloPart
  - chris-straka/skintokens, localai-org/skin-tokens.cpp
  - AlayaLab/KaiNinja, PKU-YuanGroup/UltraShape-1.0
  - stepfun-ai/Step1X-3D, DreamTechAI/Direct3D-S2, lizhihao6/Sparc3D, Stable-X/Hi3DGen
  - facebookresearch/sam-3d-objects (LICENSE), facebookresearch/sam-3d-body
  - wgsxm/PartCrafter, NVlabs/PartPacker, HKU-MMLab/OmniPart, hkdsc/fullpart, InternRobotics/MeshCoder
  - Seed3D/Puppeteer, Seed3D/MagicArticulate, Seed3D/Seed3D
  - jasongzy/Make-It-Animatable, jasongzy/Make-It-Poseable
  - zjp-shadow/CharacterGen, hyz317/StdGEN, hyz317/CHARM, aigc3d/AniGS, aigc3d/LHM
  - buaacyw/MeshAnythingV2, zhaorw02/DeepMesh, nv-tlabs/LLaMA-Mesh, jhkim0759/FastMesh, Xrvitd/SATO, meshy-dev/meshy-t2
  - huanngzh/MV-Adapter, pengHTYX/Era3D
  - symtrellis/SymTRELLIS, Whalesong-zrs/Stroke3D
  - Tencent-Hunyuan/Hunyuan3D-2.1, Tencent-Hunyuan/Hunyuan3D-Omni, Tencent-Hunyuan/Hunyuan3D-Part
  - Org listings: Tencent-Hunyuan, VAST-AI-Research, stepfun-ai, TencentARC, DreamTechAI, Seed3D
- **Hugging Face model API:**
  - TencentARC/Pixal3D, vegax87/Pixal3D, raven38/pixal3d-sv-q8_0-v1, plus the Pixal3D search listing
  - VAST-AI/AniGen, VAST-AI/SkinTokens, AlayaLab/KaiNinja, infinith/UltraShape
  - wushuang98/Direct3D-S2, stepfun-ai/Step1X-3D, VAST-AI/TripoSG, VAST-AI/TripoSF, VAST-AI/UniRig
  - facebook/sam-3d-objects, facebook/sam-3d-body-*
  - wgsxm/PartCrafter, nvidia/PartPacker, omnipart/OmniPart
  - tencent/Hunyuan3D-2.1, tencent/Hunyuan3D-Omni, tencent/Hunyuan3D-Part, tencent/Hunyuan3D-2mini
  - Seed3D/*, hyz317/StdGEN, 3DAIGC/LHM, Yiwen-ntu/MeshAnythingV2, whaohan/bpt, Zhengyi/LLaMA-Mesh, huanngzh/mv-adapter
  - jasongzy/Make-It-Animatable, Stable-X/trellis-normal-v0-1, microsoft/TRELLIS.2-4B
- **Hugging Face Papers (arXiv mirror):**
  - Image-to-3D: 2605.10922 (Pixal3D), 2512.14692 (TRELLIS.2), 2512.21185 (UltraShape), 2505.14521 (Sparc3D), 2606.04108 (SymTRELLIS), 2606.24874 (FLUX3D), 2607.28581 (ROAD)
  - Rigging and animatable: 2604.08746 (AniGen), 2605.13129 (Rigel3D), 2602.04805 (SkinTokens), 2512.16767 (Make-It-Poseable), 2602.09713 (Stroke3D)
  - Parts: 2609.15659 (KaiNinja), 2608.14783 (MegaParts), 2605.28763 (CubePart), 2510.26140 (FullPart), 2506.09980 (PartPacker)
  - Artist and low-poly mesh: 2607.28675 (Meshy T2), 2609.37139 (TaoFlowForge), 2606.20131 (TriFlow), 2606.04621 (MeshFlow), 2603.06357 (LATO), 2605.16813 (QuadLink), 2604.09132 (SATO), 2509.21420 (QuadGPT), 2606.04688 (MeshWeaver), 2508.19188 (FastMesh)
  - Meta and ByteDance: 2511.16624 (SAM 3D), 2602.15989 (SAM 3D Body), 2510.19944 / 2605.13862 (Seed3D 1.0 / 2.0)
  - Anime: 2602.03749 (See-through), 2509.21114 (CHARM)
