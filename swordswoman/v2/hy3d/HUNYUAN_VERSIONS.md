# Tencent Hunyuan3D versions - what differs, what runs on our Mac

Compiled 2026-10-26. Sources: local READMEs/licences in `.scratch/hunyuan/readmes/`, site/API probes in
`../reference/3d/hunyuan_studio_research/` (global_strings.txt, tcloud_docs.txt), fork READMEs in `.scratch/hy_omni/`, plus
WebFetch of the GitHub repos for 2 / 2.1 / Omni and the HF cards for 2mv / 2mini.
**Blocked:** `https://3d-models.hunyuan.tencent.com/` (proxy refused the connection), so cloud-version facts come from
the earlier site-bundle and Tencent Cloud doc probes. Allowlists were not edited.

Two families. **Open weights** (1.0, 2.0, 2mini, 2mv, 2.1, Omni, Part) are image-to-shape DiTs with an optional
texture stage, released under the Tencent Hunyuan Community License. **Cloud-only** versions (2.5, 3.0, 3.1, V3.5,
the Rapid tier) are only available through Hunyuan3D Studio (3d.hunyuan.tencent.com / global site) and the Tencent
Cloud API.

## Main table

| Version | Release | Params | Inputs | Outputs | Licence | Local on Apple Silicon? |
|---|---|---|---|---|---|---|
| 1.0 lite / std | 2024-11 | not stated; std has "3x" the lite params (unverified absolute) | text or 1 image (via Hunyuan-DiT T2I + 6-view MV diffusion) | mesh plus baked RGB texture (baker uses Dust3R, CC BY-NC-SA) | Hunyuan Community (non-commercial bake module) | No practical path; needs 18-30 GB CUDA VRAM |
| 2.0 Shape DiT (+Fast, +Turbo) | 2025-01-21 / Fast 02-03 / Turbo 03-19 | 1.1B | 1 image | untextured mesh | Hunyuan 3D 2.0 Community (EU/UK/KR excluded) | Shape: yes (MPS, "supports macOS" per README) |
| 2.0 Paint (+Turbo), Delight | 2025-01-21 / Turbo 04-01 | 1.3B each | mesh + image | RGB albedo texture (not PBR) | same | Hard: custom CUDA rasterizer + differentiable renderer (unverified on our Mac) |
| 2mini (+Fast, +Turbo) | 2025-03-18 / Turbo 03-19 | 0.6B | 1 image | untextured mesh | same | Shape: yes (smallest, fastest) |
| 2mv (+Fast, +Turbo) | 2025-03-18 / Turbo 03-19 | 1.1B | 1-4 views keyed front/left/back(/right) | untextured mesh | same | Shape: yes |
| FlashVDM | 2025-03-19 | n/a (decoder accelerator) | flag `--enable_flashvdm` | faster VAE decode | MIT-style repo (unverified) | Usable with shape models |
| 2.1 Shape | 2025-06-13/14 | 3.3B (the 2.0 README says 3.0B) | 1 image | untextured mesh | Hunyuan 3D 2.1 Community (EU/UK/KR excluded, 1M MAU) | **Yes**: VladimirTalyzin/hunyuan3d-2.1-mac-rocm (MPS, verified on M4 Pro) |
| 2.1 Paint PBR | 2025-06-13/14 | 2B (the 2.0 README says 1.3B) | mesh + image | PBR: albedo, metallic, roughness (+normal) | same | **Partly**: same fork, pure-PyTorch rasterizer, capped at 6 views x 256 px on MPS (no flash attention) |
| Omni | 2025-09-25/26 | 3.3B | 1 image + one control: point cloud, voxel, bbox, or skeleton pose | untextured mesh (shape only) | Hunyuan 3D Omni Community (EU/UK/KR excluded) | **Yes**: cbun/hunyuan3d-omni-mlx (native MLX DiT/VAE; DINO on MPS) |
| Part (P3-SAM + X-Part light) | 2025-09 | not stated (unverified) | existing mesh | part segmentation + per-part meshes | Hunyuan Community (unverified variant) | Unverified; likely CUDA (spconv/sonata-style deps) |

VRAM (vendor figures): 2.0 shape 6 GB, shape+paint 16 GB. 2.1 shape 10 GB, paint 21 GB, both 29 GB. Omni 10 GB.
1.0 std 30 GB (24 GB with save_memory), lite 22 GB (18 GB). On a Mac these become unified-memory figures, and the
bottleneck is the missing CUDA kernels, not RAM.

## Notes per version

**1.0**
- Two stages: multi-view diffusion (~4 s) followed by a feed-forward reconstruction (~7 s). Supports text-to-3D. Superseded by 2.x; skip it.

**2.0 family** (repo Tencent-Hunyuan/Hunyuan3D-2, `hy3dgen` package)
- Two stages: shape (flow-matching DiT on ShapeVAE latents, marching cubes / octree) then Paint (multiview diffusion, baked to UV).
- *Fast* means guidance distillation, about half the DiT time. *Turbo* means step distillation (few steps), usually combined with FlashVDM.
- 2mini (0.6B) is the lightweight option. 2mv (1.1B) is fine-tuned for multiview conditioning. The HF example takes
  `{"front","left","back"}` images, so a fixed character sheet gives tighter cross-view consistency.
- Blender addon and ComfyUI wrappers exist. Paint is RGB only and needs the CUDA `custom_rasterizer` and
  `differentiable_renderer` builds.

**2.1** (repo Hunyuan3D-2.1)
- Weights *and training code* are released (fine-tunable). The new shape VAE encoder and DiT are bigger (3.3B) than 2.0's.
- Paint moves to PBR (MaterialMVP-style): material maps instead of baked lighting.
- Mac fork (`.scratch/hy_omni/src_21_mac`): shape verified on an M4 Pro 24 GB, 344 s at 30 steps / octree 192.
  PBR texture took 512 s at the "Safe" preset (6 views at 256 px). Larger views blow up the attention matrix on MPS.

**Omni**
- 2.1 shape backbone plus a unified control encoder. `--control_type point|voxel|bbox|pose`, with `--use_ema` and `--flashvdm` flags.
- Pose control targets *human* skeletons (PoseMaster lineage). Our exported pose files (`.scratch/hy_omni/poses/*.txt`)
  hold one bone segment per line (6 floats: start xyz, end xyz), roughly 51 lines.
- This is the only open model that takes a skeleton or bbox directly, which is relevant for posed keyframe meshes. It outputs shape only.
- MLX fork bbox smoke test (5 steps, octree 128): 59.8 s on MLX vs 73.8 s on PyTorch/MPS.

**Part**
- P3-SAM (native 3D part segmentation) plus X-Part (generates complete parts). The open release is a "light" X-Part; the full version is on Studio.
- The README recommends inputs from V2.5/V3.0 meshes, which confirms those cloud versions exist.

**Related, not 3D-asset models:** HY-Motion-1.0 (text-to-motion), HunyuanWorld-1.0 (scenes), HY3D-Bench, R-DMesh
(READMEs in `.scratch/hunyuan/readmes/`).

## Licence summary (Tencent Hunyuan 3D Community License; separate copies for 2.0, 2.1, Omni)
- **Territory excludes the EU, UK and South Korea.** Use, and *use of outputs*, outside the Territory is unlicensed (s.5c in the 2.1 text).
- If licensee products had **>1M MAU** on the version's release date, you must request a separate licence from Tencent.
- Acceptable Use Policy applies. No trademark rights beyond the "Tencent Hunyuan" attribution. Fine-tunes count as Model Derivatives under the same terms.
- 1.0's texture baker depends on Dust3R (CC BY-NC-SA, non-commercial).
- Cloud use is governed by the Hunyuan 3D ToS / AUP (captured in `tos_*.txt`), not by the community licence.

## Cloud-only versions (Studio + Tencent Cloud API)
Version strings in the global Studio bundle: `3D生成-V2.5`, `V3.0`, `V3.1`, `V3.5`. The Studio feature descriptions read:
- **V2.5**: "Higher-resolution geometry details and PBR textures". Tech report arXiv 2506.16504 (2025-06-23, LATTICE
  shape model). Commonly cited as about 10B params for shape (unverified; not in our probes). No weights.
- **V3.0**: "3.6 billion modeling voxels, high-precision modeling of complex objects, significantly enhancing the generation
  effect of characters". Backs the Tencent Cloud **Pro** API (`SubmitHunyuanTo3DProJob`, launched 2025-09-16).
  Param count unverified.
- **V3.1**: "More precise geometry, more realistic texture colors, support for more reference view controllable
  generation". On the API since 2026-01-16 with **8-view** input. `Model` accepts "3.0" (default) or "3.1"; LowPoly is
  unavailable with 3.1.
- **V3.5**: appears only as a label in the Studio UI bundle. Features, date and API availability are unverified.
- **Rapid** (极速版) API (2025-09-16): under 90 s per job, 15 credits. The underlying version is unverified.
- Pro API options: `GenerateType` = Normal (textured) / **Geometry** (white model) / LowPoly (smart topology, Polygon 1.5,
  tri or quad) / Sketch. Other options: `EnablePBR`, `FaceCount` 3k-1.5M (default 500k; 2026-01 docs mention 10k
  Normal / 3k LowPoly minimums), `MultiViewImages`, `ResultFormat` (STL/USDZ/FBX/...).
- Other cloud endpoints (2025-12): texture generation, part/component generation, UV unwrap, 3D character from portrait,
  format conversion, text-to-motion. The Studio UI also offers auto-rigging ("Show the bones", T-pose prompt) and animation presets.
- Pricing: 0.1-0.12 CNY per credit. Pro Normal is 20 credits, plus 10 each for MultiView, PBR and FaceCount. Default
  concurrency is 3. Tencent Cloud says Hunyuan services are migrating to "TokenHub" (no new purchases on the old platform).
  A free quota exists on activation. Account and region access from outside China (and from the EU/UK) is unverified.

## Fit for our use (chibi reference mesh + posed keyframes) - facts only
- Clean, simple solid shape: any shape-only model works. Geometry-only output avoids the CUDA texture stage entirely.
- Consistency across views: 2mv (open) or 3.1 multiview (cloud) conditions on our own character sheet.
- Posed meshes: Omni `pose` (open, MLX-capable) is the only skeleton-conditioned option. The alternative is rigging one
  mesh (Studio auto-rig or Blender) and posing it, which keeps identity more consistent than regenerating per pose.
- Licence territory matters if anyone in the EU/UK/KR is involved.

## Recommendation for our use
(filled in after local tests - see NOTES.md)
