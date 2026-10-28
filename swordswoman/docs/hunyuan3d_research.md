# Hunyuan3D research: how it generates meshes and whether it fits the Akane chibi pipeline

Date: 2026-10-23. Machine: Apple M5 Max with 64 GB unified memory (`hw.memsize` = 68719476736), macOS, no NVIDIA GPU.

How sources are marked:
- **[V]** means I verified it this session, either from a primary source (GitHub README or API, Hugging Face model card or API, a Hugging Face Papers abstract, the LICENSE file) or from our own run.
- **[M]** means it comes from memory or secondary knowledge and I could not re-verify it. The sandbox proxy blocked arxiv.org, fal.ai, replicate.com, tencent.com / tencentcloud.com and *.hf.space (see section 2.4).

---

## TL;DR

- **The live test worked on this Mac.** I ran the official `Tencent-Hunyuan/Hunyuan3D-2` code with PyTorch on MPS and the `Hunyuan3D-2mini-Turbo` shape model. It turned our Gemini turnaround front view into a watertight mesh.
  - Diffusion plus decode took **3–7 s**, about 23 s including model load.
  - Peak memory was about **9–13 GB**.
  - The mesh had 310k–750k triangles.
- **The silhouette and proportions are good.** It captured the chibi head ratio, the bow, the bun, the wide sleeves, the split skirt tails, the high collar, the scarf ribbons and even the thin katana blade.
- **The topology is not usable for animation as-is.**
  - The output is one fused, triangulated marching-cubes shell.
  - The sword is fused to the hand, the ribbons are fused to the body, and there is no face detail, UVs, parts or rig.
- **The license is restrictive.** It is the Tencent Hunyuan Community License: it does not apply in the EU, UK or South Korea, and it requires a separate license above 1M MAU. It is fine for a personal or small project in the Territory.
- **Recommendation:** use Hunyuan3D as a **proportion and silhouette reference and a sculpt base**, not as the final asset. Keep the procedural Blender rig and the palette-only shading as the source of truth. Details are in section 5.

---

## 1. Architecture

### 1.1 Version history

| Version | Date | Open? | Shape method | Texture method | Source |
|---|---|---|---|---|---|
| **1.0** | 2024-11 | Weights open | Two stages: multiview diffusion (about 4 s) produces six RGB views, then a feed-forward sparse-view reconstruction model produces the mesh (about 7 s). Lite and standard variants; text-to-3D through Hunyuan-DiT. | Vertex or texture colours from the views | arXiv 2411.02293 [V] |
| **2.0** | 2025-01 | Open (code + weights) | **Hunyuan3D-DiT**, a 1.1B flow-matching DiT over ShapeVAE vecset latents | **Hunyuan3D-Paint**, 1.3B multiview diffusion, plus a Delight model | arXiv 2501.12202, GH Hunyuan3D-2 [V] |
| 2.0 variants | 2025-02/04 | Open | `-Fast` (guidance distilled), `-Turbo` (step distilled, about 5 steps, FlashVDM), **2mini** (0.6B), **2mv** (1.1B, multiview input) | Paint-v2-0-Turbo | GH README model zoo [V]; FlashVDM arXiv 2503.16302 [V] |
| **2.1** | 2025-06 | Fully open, including the VAE encoder and training code | 3.3B DiT; the ddalcu MLX card describes it as an MoE flow DiT | **PBR Paint** (albedo + metallic/roughness, MaterialMVP lineage), 2B | arXiv 2506.15442, GH Hunyuan3D-2.1 [V] |
| **2.5** | 2025-06 | **Closed** (web and API only) | **LATTICE**, up to 10B parameters, "sharp detail, clean smooth surfaces" | Multiview PBR | arXiv 2506.16504 [V] |
| LATTICE paper | 2025-11 | Paper | **VoxSet**: latent vectors anchored to a coarse voxel grid. Stage 1 generates a sparse voxel anchor, stage 2 a rectified-flow transformer adds detail; decodes at any resolution. | n/a | arXiv 2512.03052 [V] |
| **3.0 / 3.x** | about 2025-09 onward | **Closed** (Hunyuan3D Studio, 3d.hunyuan.tencent.com, Tencent Cloud API) | Successor of LATTICE. The Part README recommends meshes "from Hunyuan3D V2.5 or V3.0". The E-DiT paper (arXiv 2602.13993) benchmarks on "Hunyuan3D-3.0". | PBR | [V] that it exists; [M] for marketing claims such as higher resolution |
| **Omni** | 2025-09 | Open, 3.3B, about 10 GB VRAM | Built on 2.1, with a unified control encoder for **point cloud, voxel, bbox and skeleton pose** conditioning | none (shape only) | arXiv 2509.21245, GH Hunyuan3D-Omni [V] |
| **Part** (P3-SAM + X-Part) | 2025-09/12 | Open "light" X-Part; full version in Studio | P3-SAM does native 3D part segmentation. X-Part does bbox-prompted generation of complete parts. | n/a | arXiv 2509.06784 and 2509.08643, GH Hunyuan3D-Part [V] |
| **Studio** | 2025-09 | Closed platform | End-to-end game-asset pipeline: part generation, **Polygon Generation (low-poly / "PolyGen")**, Semantic UV, PBR texture, and per the 2.0 paper, animation | | arXiv 2509.12815 [V], abstract only (full text blocked) |
| HY3D-Bench | 2026-02 | Open dataset | 252k watertight meshes, 240k part-level objects, 125k synthetic objects, plus a baseline Hunyuan3D-2.1-Small (0.8B) | | GH HY3D-Bench, arXiv 2602.03907 [V] |
| **Buffalo 1.0** | 2026-08 | Paper only, no weights | Unified VLM + DiT for text-to-3D, instruction-guided 3D editing and text-grounded part generation | | arXiv 2608.02711, GH Hunyuan3D-Buffalo1.0 [V] |

Related Tencent releases:
- **HY-Motion 1.0** (2025-12, open): text-to-skeletal-motion DiT, 1.0B / 0.46B Lite, needs at least 24–26 GB VRAM. It outputs SMPL-style skeleton animation.
- **R-DMesh** (SIGGRAPH 2026, open): video-guided animation of a static mesh.
- I found **no public repo named "PolyGen"**. Polygon generation exists only inside Studio. No `Hunyuan3D-2.5`, `-3`, `-PolyGen` or `-Studio` GitHub repos exist (the GitHub API returns 404) [V].

### 1.2 Shape stage (2.x)

I verified this against the 2mini and 2mv `config.yaml` files and the 2.0 paper abstract.

1. **Preprocessing**
   - Background removal (rembg) and recentring with `border_ratio` 0.15.
   - Image size 1022 for single view and 518 per view for multiview.
2. **Condition encoding**
   - **DINOv2-Giant** (40 layers, hidden size 1536, patch size 14). The weights ship inside the DiT checkpoint.
   - The output is patch tokens used as cross-attention context (`context_in_dim: 1536`).
   - 2mv uses `DinoImageEncoderMV`, which takes front, left, back and right views and adds view embeddings.
3. **ShapeVAE (3DShape2VecSet / Michelangelo / CraftsMan lineage)**
   - Points are sampled on the surface of a watertight mesh. The 2.0 paper describes "importance sampling" that oversamples edges and corners.
   - A cross-attention perceiver compresses them to **3072 latent tokens × 64 channels** (`num_latents: 3072`, `embed_dim: 64`).
   - The decoder is a 16-layer transformer. Query points (Fourier-embedded xyz, `num_freqs: 8`) cross-attend to the latents and predict **SDF / occupancy** values.
4. **Hunyuan3D-DiT**
   - A FLUX-style transformer with **double-stream blocks followed by single-stream blocks**: 8 + 16 for mini, 16 + 32 for 2.0 / 2mv, hidden size 1024, 16 heads.
   - It is trained with **rectified flow matching** to denoise the 3072 × 64 latent set, conditioned on the DINO tokens.
   - The Turbo variants use a consistency or PCM flow scheduler (`ConsistencyFlowMatchEulerDiscreteScheduler`), so about 5 steps are enough.
5. **Decoding to a mesh**
   - The SDF is evaluated on a dense grid of `octree_resolution`³ points (256–512).
   - **FlashVDM** decodes hierarchically: coarse 63 → 126 → 252, querying only near the surface, with adaptive KV selection. That is why decode takes under 1 s.
   - Marching cubes (`mc` or `dmc`) extracts the surface.
   - Postprocessing: FloaterRemover, DegenerateFaceRemover, and an optional `FaceReducer` (pymeshlab quadric decimation to about 40k faces).
6. **Output:** one `trimesh` with no UVs and no parts. It is a dense, isotropic triangle soup from marching cubes, usually a single connected, watertight component.

In 2.5 / 3.0, LATTICE replaces the pure vecset with **VoxSet** (latents anchored to voxels) and does coarse-to-fine sparse voxel generation followed by a refining flow transformer. That is why it can scale to much finer detail. The output is still an implicit field meshed by iso-surfacing, so the topology issue is the same.

### 1.3 Texture stage

- **2.0 Paint**
  - A **Delight** model first removes baked lighting from the input image.
  - A multiview diffusion model, based on an SD2-style UNet with reference attention and multi-task attention, is conditioned on the mesh's rendered **normal and position maps**. It generates 6 or more consistent views.
  - These views are back-projected into UV space (xatlas unwrap), then inpainted and blended.
  - The official repo needs **CUDA-only** extensions (`custom_rasterizer` is a `CUDAExtension`) [V].
- **2.1 PaintPBR:** the same idea, but it produces albedo plus metallic/roughness maps, with optional RealESRGAN upscaling. It needs about 21 GB of VRAM [V].
- **2.5 / 3.0:** multiview PBR at higher resolution (closed).

### 1.4 Topology, low-poly, parts and rigging

| Need | What Hunyuan offers | Open? |
|---|---|---|
| Clean low-poly or quad topology | Studio "Polygon Generation" (an autoregressive mesh generator in the MeshAnything / BPT family [M]). The open repos only offer quadric decimation (`FaceReducer`). | Closed |
| Separable parts (sword, bow, ribbons, skirt) | **Hunyuan3D-Part**: P3-SAM segmentation plus X-Part completion of parts | Open (light version); Space is running |
| UVs | Studio "Semantic UV" (closed). The open repos use xatlas. | Partly |
| Skeleton-aware shape | **Omni** pose control: the mesh is generated in a given skeletal pose | Open |
| Auto-rig / skinning | Studio has an animation module [M]. Community option: **UniRig** (VAST, MIT), bundled with Hunyuan 2.1 in `ddalcu/Hunyuan3D-2.1-MLX-Serve-8bit` | Community, open |
| Motion | HY-Motion 1.0 (SMPL-like skeleton, text-to-motion) | Open, but needs at least 24 GB VRAM and is CUDA oriented |

---

## 2. Can we run it here?

### 2.1 Official requirements [V]

- **2.0 family:** 6 GB VRAM for shape and 16 GB for shape plus texture. The README says it supports "macOS, Windows, Linux".
- **2.1:** 10 GB for shape, 21 GB for texture, 29 GB for both. Tested with PyTorch 2.5.1+cu124.
- **Omni:** about 10 GB.
- **On macOS:** the shape models run on MPS. Texture (Paint) does not run in the official repos because of the CUDA rasterizer and the differentiable renderer.

### 2.2 Live test (succeeded)

Setup:
- Everything is isolated in `/Users/waylonhuang/Documents/other/pixelart/.models/hunyuan/`:
  - `src/`: a shallow clone of Tencent-Hunyuan/Hunyuan3D-2, used only as an import path and never pip-installed.
  - `venv/`: a uv venv on Python 3.11.
  - `weights/`, `inputs/`, `out/`, and `scripts/` (my scripts, kept outside the downloaded code).
- Scripts ran with `python -I`.
- Downloads:

  | Item | Size |
  |---|---|
  | `Hunyuan3D-2mini`: dit-v2-mini-turbo fp16 | 3.82 GB |
  | `Hunyuan3D-2mini`: two VAEs | about 0.4 GB each |
  | `Hunyuan3D-2mv`: dit-v2-mv-turbo | 4.93 GB |
  | `Hunyuan3D-2`: vae-v2-0-turbo | 0.41 GB |
  | rembg `isnet-anime` (into `~/.rembg`) | 176 MB |
  | **Total** | **about 9.7 GB** |

- **Gotcha:** transformers 5.x renamed the DINOv2 modules (`q_proj`), so loading the checkpoint fails with "Missing key(s) ... SingleImageEncoder". Pin **`transformers==4.48.3 diffusers==0.32.2`**. Torch 2.14.1 on MPS worked with `PYTORCH_ENABLE_MPS_FALLBACK=1`.
- **Inputs:** `concept/chibi_turnaround_v6.png` cropped into front, side and back views, with the background removed by rembg `isnet-anime`. A second test used `concept/chibi_iso_v5.png`.

| Run | Model | Steps / octree | Generation time | Faces | Result |
|---|---|---|---|---|---|
| `mini_front` | 2mini-turbo + FlashVDM, front view | 5 / 256 | **7.3 s** (first run), 23 s wall including load; peak footprint 8.9 GB, RSS 12.8 GB | 312k, watertight, 1 component | **Best.** Correct chibi ratio, bow, bun, collar, split coat tails, belt pouch, thigh strap, ribbons and a thin katana. The face is a smooth blank (no eyes, as expected). The bow reads a bit like cat ears. |
| `mini_front_hi` | same | 5 / 384 | 3.1 s | 710k | Almost identical; extra resolution adds little. |
| `mv_turn` | 2mv-turbo, front + left + back | 5 / 384 | 6.2 s | 756k, not watertight | **Worse.** Lumpy hair and noisy bun, because the views disagree: the katana is drawn in the front view and sheathed in the side view, and the side crop clips the bun. Multiview only helps when the views are strictly consistent. |
| `mini_iso` | 2mini-turbo, iso image | 5 / 384 | 3.3 s | 753k | Plausible. The face is distorted and the body is shorter; a top-down input misleads the model. Use orthographic front views. |
| `mini_front_8k` | Blender Decimate of `mini_front` to 8k triangles | n/a | under 1 s | 8k | Silhouette holds well at 8k, which is enough for 56 px sprites. Still triangulated and fused. |

Renders (Blender Workbench front, side, back, iso): `out/*_sheet.png`. Meshes: `out/*.glb`. Logs: `out/*.log`.

Reproduce:
```bash
H=/Users/waylonhuang/Documents/other/pixelart/.models/hunyuan
$H/venv/bin/python -I $H/scripts/prep_inputs.py concept/chibi_turnaround_v6.png $H/inputs concept/chibi_iso_v5.png
printf "mini_front mini 5 256 1 front.png\n" | bash $H/scripts/batch.sh   # gen + Blender render + sheet
/Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup -P $H/scripts/decimate.py -- $H/out/mini_front.glb $H/out/mini_front_8k.glb 8000
```

### 2.3 Apple Silicon and community ports [V, from Hugging Face model cards]

- **`ddalcu/mlx-serve`** (2k stars, active as of 2026-10-22)
  - A native MLX / Zig server with the bundle `ddalcu/Hunyuan3D-2.1-MLX-Serve-8bit` (about 8.1 GB).
  - It runs **2.1 shape + PBR paint + UniRig skeleton** on-device.
  - Endpoint: `POST /v1/3d/generations {"image":..., "texture":true, "rig":true}`, which returns a rigged GLB.
  - This is the only route to **texture and auto-rig on this Mac**. I did not test it.
- **`dgrauet/Hunyuan3D-2.1-mlx`**: a Python MLX pipeline for 2.1 shape and paint (weights `dgrauet/hunyuan3d-2.1-mlx`, about 14 GB in total).
- **`ZimengXiong/Hunyuan3D-Swift`** (MIT code): an MLX `hy3d shape` CLI that uses the 2mini weights (`zimengxiong/hunyuan3d-mlx-shape-small`, 3.8 GB).
- **ComfyUI:** kijai/ComfyUI-Hunyuan3DWrapper and visualbruno/ComfyUI-Hunyuan3d-2-1. Paint nodes generally need CUDA.
- **Official Blender add-on:** `blender_addon.py` in the 2.0 repo, which talks to `api_server.py`.

### 2.4 Hosted options

- **Hugging Face Spaces:** all running on ZeroGPU A10G as of today [V]:
  - `tencent/Hunyuan3D-2`
  - `tencent/Hunyuan3D-2.1`
  - `tencent/Hunyuan3D-2mv`
  - `tencent/Hunyuan3D-2mini-Turbo`
  - `tencent/Hunyuan3D-Part`

  `tencent/Hunyuan3D-1` shows RUNTIME_ERROR. **I could not call them from this sandbox** because `*.hf.space` is blocked by the ACC proxy (403 CONNECT). To use them with `gradio_client`, add `hf.space` (or the specific `tencent-hunyuan3d-2-1.hf.space`) to `~/.claude/apple/dangerous_allowed_domains.csv`. That loosens security, so it needs your OK. ZeroGPU also has anonymous daily quotas; a HF token helps.
- **Tencent Cloud "Hunyuan 3D" API (AI3D), with 2.5 / 3.x models; 3d.hunyuan.tencent.com Studio** [M]: exists, but the domain was blocked here. It needs a Tencent Cloud account and is credit-based. This is the only way to get the closed 3.x, PolyGen low-poly and Studio part/rig features.
- **fal.ai / Replicate** [M]: in the past both hosted Hunyuan3D 2.x endpoints, and fal hosted v2.1 and later v3. Both domains were blocked here, so I could not confirm current availability or price.

### 2.5 License (Tencent Hunyuan 3D Community License; I read the 2.1 LICENSE text) [V]

- **Territory excludes the EU, UK and South Korea.** "THIS LICENSE AGREEMENT DOES NOT APPLY IN THE EUROPEAN UNION, UNITED KINGDOM AND SOUTH KOREA". Using, reproducing, distributing or displaying the weights **or their Outputs** outside the Territory is unlicensed (§5c, AUP §1). If the game will be sold or shown in the EU or UK, generated meshes become legally murky.
- **MAU threshold:** if your products had **more than 1M MAU** on the model's release date, you need a separate license from Tencent.
- **No training other models on outputs** (§5b). For example, you may not train a sprite model on Hunyuan meshes. **Outputs are not "Model Derivatives"**, and **Tencent claims no rights in Outputs** (§6d).
- Distributing the weights requires attribution (a "Powered by Tencent Hunyuan" notice) and the AUP.
- Commercial use is allowed in the Territory below the MAU threshold. MLX ports inherit the same license.

---

## 3. Fit for our use case

| Criterion | Hunyuan3D 2mini/2.1 (open) | Our procedural Blender build |
|---|---|---|
| Matches the concept silhouette | **Very good.** It reproduced collar height, sleeve bell shape, coat-tail split and bun/bow placement better than round 1 of the procedural model did. | Good, but every proportion is hand-tuned. |
| Thin parts (blade, ribbons, sleeve cuffs, bow loops) | They survive, but are fused to neighbours. The blade is a lumpy tube with no edge. Ribbons are welded to the arms. | Exact: a separate blade with an edge axis, and ribbon chains. |
| Faces / eyes | None. Anime eyes are flat paint, so geometry is blank. | Decals, exactly on palette. |
| Topology for rigging | Bad: 300k–750k triangles in one watertight shell. Body, skirt, sleeves and sword are a single surface, so automatic weights bleed between them (skirt to legs, sword to hand). It needs retopology or part separation. | Clean, purpose-built objects; 40-bone rig; custom skirt weights. |
| Deterministic / editable / palette-exact | Seeded but opaque; editing means re-sculpting. | Fully deterministic; palette AOVs; outline hull. |
| Texture | 2.0 Paint or 2.1 PBR are realistic-ish and **not palette-exact**; CUDA only, or MLX ports. We would re-quantize anyway. | Palette-exact emission ramps. |
| Cost to iterate | Seconds per variant. | Minutes to hours of scripting per change. |

**Conclusion:** for a 56 px, 8-direction sprite with sword-attack animations, what matters is **clean separation of parts, a controllable rig and palette-exact materials**. The procedural pipeline already does all three. Hunyuan's raw output would need retopology, separation, UVs and re-rigging, which costs more than it saves.

What Hunyuan **is** good for: quickly validating and correcting proportions and silhouettes from the concept art in 3D. At sprite scale the silhouette is about 80% of the read.

Alternatives for "AI mesh + auto-rig" [M unless noted]:
- **Tripo** (v2.5/3.x): quad and low-poly options plus auto-rig; paid API.
- **Meshy** (v5/6): remesh to quads plus auto-rig/animation for humanoids.
- **Rodin Gen-2** (Hyper3D): quad mode.
- **UniRig** (open, MIT): skeleton plus skin prediction for arbitrary meshes; the MLX port is in ddalcu's bundle [V].
- **Mixamo**: humanoid auto-rig. Chibi proportions often confuse it.
- **Hunyuan3D-Omni pose control** [V]: generates the shape in a T or A pose given a skeleton, which is useful if we want an AI base mesh already in our rest pose.

---

## 4. What we can learn from it, even if we don't ship its meshes

1. **Front-view-first, single-image works best.** Turbo-mini on a clean, orthographic, background-removed front view beat 3-view multiview, because our Gemini sheets are not geometrically consistent (sword drawn vs sheathed, cropped bun). If we use multiview, generate strictly consistent orthographic views first (same pose, same props, T/A-pose, no perspective). The same applies to briefing Gemini for any reference.
2. **Use the AI mesh as a proportion gauge.** Import `mini_front.glb`, scale it to our 2.75 H crown height, and overlay it with our procedural model in front, side and back orthographic views. Read off collar height, sleeve flare radius, skirt-tail length, bun and bow offsets, and torso depth, then feed those numbers back into `build_character.py`. This is cheap and keeps determinism.
3. **Treat it as a sculpt base or shrinkwrap target.** For organic pieces that are hard to model procedurally (hair mass, bangs clumps, bun, skirt folds), Shrinkwrap or Data-Transfer our low-poly procedural cage onto the AI surface. That gives AI-quality volume with our topology and weights.
4. **Hybrid assembly.**
   - Keep AI geometry only for body, hair and dress volume.
   - Keep procedural geometry for the **katana, bow, ribbons/scarf chains, buckles, corset straps and face decals**, which need rigid bones, exact edges or palette decals.
   - Use **Hunyuan3D-Part (P3-SAM)** to auto-segment the AI mesh into hair, bow, sleeves, skirt and so on before deciding what to keep.
5. **Decimation is enough at sprite scale.** 8k triangles kept the silhouette. For 56 px sprites, a remesh (Voxel at about 0.01 H, then Quadriflow at about 4–8k) is acceptable if we ever adopt an AI base. Outlines (inverted hull) and cel ramps hide faceting.
6. **Palette baking.** If we use Paint textures, bake to a texture, then quantize to `docs/palette.json`. This is the same idea as our matid AOV quantization: sample the albedo per material region and snap it to the nearest palette ramp, then replace it with our emission-ramp materials. In practice it is easier to just assign our materials per segmented part.
7. **The concept-to-3D loop as QA.** Running every new Gemini concept through 2mini (about 25 s) shows whether the design is "3D-coherent". Incoherent designs produce lumpy meshes, as the multiview run did. It is a cheap sanity check before modelling.

---

## 5. Recommendation (ranked)

**1. Adopt now: a reference-overlay pass (local, about 25 s per image, no licensing concerns for internal reference use in the Territory).**
- Generate a reference mesh from each approved front view.
- Import it into a hidden `REF_hunyuan` collection that is never rendered into sprites.
- Run a side-by-side orthographic comparison to tune `build_character.py` constants.

```bash
H=/Users/waylonhuang/Documents/other/pixelart/.models/hunyuan
$H/venv/bin/python -I $H/scripts/prep_inputs.py concept/chibi_turnaround_v6.png $H/inputs
printf "ref_v6 mini 5 256 1 front.png\n" | bash $H/scripts/batch.sh
# in Blender: import $H/out/ref_v6.glb, normalize height to the crown (2.75 H), place in REF collection, ortho-compare
```

**2. Next: Gemini "3D-consistent" turnaround, then 2mv.** Ask Gemini for an orthographic A-pose turnaround with identical props in every view (katana drawn in the left hand in every view, full bun visible), then rerun `mv` mode. Use it only if it beats single-view.

**3. Optional, if the procedural hair or skirt keeps looking stiff: hybrid shrinkwrap.**
- Run P3-SAM via the Hunyuan3D-Part Space or locally to split the hair and skirt.
- Voxel-remesh plus Quadriflow those parts to a few thousand faces.
- Shrinkwrap our procedural hair and skirt cages onto them.
- Keep our bones, weights and palette materials.
- Never use the AI sword, ribbons or face.

**4. Optional experiment: full AI route on this Mac (shape + texture + UniRig).**
```bash
hf download ddalcu/Hunyuan3D-2.1-MLX-Serve-8bit --local-dir ~/.mlx-serve/models/ddalcu/Hunyuan3D-2.1-MLX-Serve-8bit   # ~8.1 GB
mlx-serve --serve --model-dir ~/.mlx-serve/models
curl localhost:8080/v1/3d/generations -H 'Content-Type: application/json' \
  -d "{\"model\":\"ddalcu/Hunyuan3D-2.1-MLX-Serve-8bit\",\"image\":\"$(base64 -i inputs/front.png)\",\"texture\":true,\"rig\":true}"
```
Expect a single-shell mesh with a generic skeleton. Treat it as a comparison point, not a replacement for the 40-bone rig.

**5. Not recommended for this project:**
- Shipping raw Hunyuan meshes as the sprite source.
- Paying for closed 3.x or Studio PolyGen just for this character.
- HY-Motion, which is CUDA-heavy and SMPL-oriented; our attack and anime timing is better hand-keyed.
- Any use if the game is distributed in the EU, UK or South Korea, or exceeds 1M MAU, without first checking the license.

**Network note:** HF Spaces (`*.hf.space`), arxiv.org, fal.ai, replicate.com and the Tencent domains are blocked by the ACC proxy here. To call the Spaces with `gradio_client`, add `hf.space` to `~/.claude/apple/dangerous_allowed_domains.csv` (this needs your approval). The local route already works without it.

## Sources
- GitHub:
  - Tencent-Hunyuan/Hunyuan3D-1
  - Hunyuan3D-2 (README, `hy3dgen` code, configs)
  - Hunyuan3D-2.1 (README, LICENSE)
  - Hunyuan3D-Omni
  - Hunyuan3D-Part
  - HY3D-Bench
  - Hunyuan3D-Buffalo1.0
  - HY-Motion-1.0
  - R-DMesh
- Hugging Face:
  - Models: tencent/Hunyuan3D-2, -2mini, -2mv, -2.1, -Omni, -Part
  - Spaces: tencent/Hunyuan3D-* (runtime API)
  - MLX ports: dgrauet/hunyuan3d-2.1-mlx, zimengxiong/hunyuan3d-mlx-shape-small, ddalcu/Hunyuan3D-2.1-MLX-Serve-8bit
- Papers (abstracts via Hugging Face Papers API): arXiv 2411.02293, 2501.12202, 2503.16302 (FlashVDM), 2506.15442, 2506.16504, 2512.03052 (LATTICE), 2509.12815 (Studio), 2509.21245 (Omni), 2509.06784 (P3-SAM), 2509.08643 (X-Part), 2602.03907 (HY3D-Bench), 2602.13993 (E-DiT, mentions Hunyuan3D-3.0), 2608.02711 (Buffalo)
