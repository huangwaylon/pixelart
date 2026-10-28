# Pixal3D (and TRELLIS.2, same engine) on this Mac: reproducible setup

Date: 2026-10-24. Host: Apple M5 Max, 64 GB, macOS 27.0.1. Blender 5.2.0 LTS (for inspection only).
Project root: `/Users/waylonhuang/Documents/other/pixelart/swordswoman`. Everything lives under `.scratch/pixal3d/` (downloads and builds) and `.scratch/pixal3d_scripts/` (our scripts). The step-by-step log is in `.scratch/pixal3d/LOG.md`.

## 1. Route chosen and why

**Primary: `raven38/pixal3d.cpp`, prebuilt Metal binary** (C++/GGML, MIT).
- It is the only route with **both** Pixal3D single-view (`--sv-image`) **and** camera-aware multi-view (`--views` plus `transforms.json`), and published, manifest-verified q8_0 weight sets for each.
- The same binary also runs TRELLIS.2-4B single-image (the default mode), with the reference weld, hole-fill, narrow-band UDF dual-contouring remesh and CuMesh-style QEM decimation.
- There is a prebuilt macOS arm64 Metal tarball, so nothing has to be compiled.
- Repo HEAD `d1b4926452` (2026-09-23). The binary comes from release tag `showcase-assets-sv-1` (built 2026-09-24). Note: this binary predates HEAD's `--trellis2-mv`, which is not in the build.
- Open issues: none block Metal. The Metal ones are perf/accuracy follow-ups (#30, #31, #32, #47); #41 reports "MV 1024 on Metal: PASS"; #87 is a Studio drag-drop bug only. #85 (open) reports that the flow DiT drifts 1.3–4.1 % from PyTorch on all backends.

**Secondary (built, works): `pwilkin/trellis.cpp` HEAD `83e8080c40` (2026-10-23), built from source.**
- Since v0.8.0, upstream also runs Pixal3D **single-view** (`--model pixal3d --fov DEG`). It also adds `--faces N`, `--steps N`, the small-K-quant→F16 load fix (#50/#55), and optional quad retopology (Linux/Windows only).
- It has **no multi-view Pixal3D** and **no macOS release asset**.

**Not used:**
- `PHMFG/pixal-studio` (MIT, 1 star, 2026-10-22).
- `lyonsno/pixal3d-mlx` (no licence file, last commit 2026-07-02).

Both are kept as fallbacks only.

## 2. Install (prebuilt Metal binary)

```zsh
cd /Users/waylonhuang/Documents/other/pixelart/swordswoman
mkdir -p .scratch/pixal3d/rel_metal && cd .scratch/pixal3d/rel_metal
curl -sL -o trellis-metal-macos-arm64.tar.gz \
  https://github.com/raven38/pixal3d.cpp/releases/download/showcase-assets-sv-1/trellis-metal-macos-arm64.tar.gz
shasum -a 256 trellis-metal-macos-arm64.tar.gz   # 6cb8878e7c9c163d243f71e397e8c4b9ce5fea82d0c17799c2c1a608cf4c1457 (2,597,968 B)
mkdir -p bin && tar xzf trellis-metal-macos-arm64.tar.gz -C bin   # trellis-cli, trellis-server, libggml*.0.15.1.dylib (rpath @loader_path)
./bin/trellis-cli --help
```

## 3. Weights (resumable, sha256-verified, pinned revisions)

Script: `.scratch/pixal3d_scripts/fetch_hf.sh REPO REV DEST LOG files...`. It uses `curl -C -` with retries and a stall guard (`--speed-limit 100000 --speed-time 60`), runs up to 8 attempts per file, and checks size and LFS sha256 against the HF API for the same revision. Progress goes to `.scratch/pixal3d/weights/download.log`.

Measured throughput: 14–18 MB/s. HF throttled twice to under 100 KB/s; both times the download auto-resumed. Total time was about 13 min (SV) + 7 min (MV) + 9.5 min (TRELLIS.2).

```zsh
S=.scratch; W=$S/pixal3d/weights
$S/pixal3d_scripts/fetch_hf.sh raven38/pixal3d-sv-q8_0-v1 46d399ac986f45a0d7f5b1ca5058614d8729a131 $W/pixal3d-sv-q8_0-v1 $W/download.log \
  LICENSE.md MIT_LICENSE.md DINOV3_LICENSE.md README.md pixal3d-models.json pixal3d_naf.gguf dinov3.gguf ss_dec.gguf \
  pixal3d_ss_flow_sv.gguf pixal3d_shape_flow_512_sv.gguf pixal3d_shape_flow_1024_sv.gguf pixal3d_tex_flow_1024_sv.gguf shape_dec.gguf tex_dec.gguf
# MV set: the 5 shared files are byte-identical -> hard-link them, fetch only the 4 _mv flows
mkdir -p $W/pixal3d-q8_0-v1; for f in dinov3.gguf pixal3d_naf.gguf ss_dec.gguf shape_dec.gguf tex_dec.gguf; do ln -f $W/pixal3d-sv-q8_0-v1/$f $W/pixal3d-q8_0-v1/$f; done
$S/pixal3d_scripts/fetch_hf.sh raven38/pixal3d-q8_0-v1 1c4f4bdddb5fef1dc5efa512d4b88e899b10bd91 $W/pixal3d-q8_0-v1 $W/download.log \
  README.md pixal3d-models.json LICENSE.md pixal3d_ss_flow_mv.gguf pixal3d_shape_flow_512_mv.gguf pixal3d_shape_flow_1024_mv.gguf pixal3d_tex_flow_1024_mv.gguf
# TRELLIS.2-4B q8 (ilintar/trellis2-gguf q8/): dinov3/ss_dec/shape_dec/tex_dec are byte-identical to the Pixal3D ones -> hard-link
mkdir -p $W/trellis2-gguf-q8; for f in dinov3.gguf ss_dec.gguf shape_dec.gguf tex_dec.gguf; do ln -f $W/pixal3d-sv-q8_0-v1/$f $W/trellis2-gguf-q8/$f; done
$S/pixal3d_scripts/fetch_hf.sh ilintar/trellis2-gguf a57397bd3d351599d9729fc144b3f87c3f87d65b $W/trellis2-gguf-q8 $W/download.log \
  README.md q8/ss_flow.gguf q8/shape_flow_512.gguf q8/shape_flow_1024.gguf q8/tex_flow_512.gguf q8/tex_flow_1024.gguf
```

| file | bytes | sha256 (first 12) | sets |
|---|---:|---|---|
| dinov3.gguf | 323,657,920 | 0dd4ffd4b46a | SV, MV, T2 (shared) |
| pixal3d_naf.gguf | 1,334,656 | c4f6cd80e94c | SV, MV |
| ss_dec.gguf | 147,379,392 | 2790b5eecb26 | SV, MV, T2 |
| shape_dec.gguf | 881,361,568 | 0de7c7a67502 | SV, MV, T2 |
| tex_dec.gguf | 881,344,576 | 88b4fced4645 | SV, MV, T2 |
| pixal3d_ss_flow_sv.gguf | 1,426,559,744 | 75eeb538c548 | SV |
| pixal3d_shape_flow_512_sv.gguf | 1,476,761,760 | 13f5df430ca4 | SV |
| pixal3d_shape_flow_1024_sv.gguf | 1,476,761,760 | 7cb1ecb18971 | SV |
| pixal3d_tex_flow_1024_sv.gguf | 1,476,813,984 | 06ef23d3bada | SV |
| pixal3d_ss_flow_mv.gguf | 1,426,559,744 | 5211bb54a3f9 | MV |
| pixal3d_shape_flow_512_mv.gguf | 1,476,761,760 | 79a8ff77d0da | MV |
| pixal3d_shape_flow_1024_mv.gguf | 1,476,761,760 | 50cd892247d7 | MV |
| pixal3d_tex_flow_1024_mv.gguf | 1,476,813,984 | e14a590dc6c7 | MV |
| ss_flow.gguf (q8) | 1,376,059,040 | ea6d8a42b206 | T2 |
| shape_flow_512.gguf (q8) | 1,376,125,952 | 29b639f4ff22 | T2 |
| shape_flow_1024.gguf (q8) | 1,376,125,952 | 997e9fc10ab9 | T2 |
| tex_flow_512.gguf (q8) | 1,376,178,176 | 389a2cbdda59 | T2 |
| tex_flow_1024.gguf (q8) | 1,376,178,176 | cb2cb3aee74b | T2 |

- Set totals: SV 8,091,975,360 B (7.54 GiB); MV +5,856,897,248 B; T2 +6,880,667,296 B. About 19.4 GB unique on disk.
- All files match the HF LFS sha256, and the SV and MV sets also match their own `pixal3d-models.json` manifests.
- `birefnet.gguf` (882,749,024 B) was **not** downloaded. Our inputs are pre-matted RGBA, and auto mode keeps an existing alpha (otherwise it falls back to a threshold matte).

## 4. Run commands

Our wrappers run `/usr/bin/time -l`, keep the cwd in our own output directory, and append to `runs.log`:
- `run_sv.sh IN.png OUT SEED [FOV_DEG]`: Pixal3D single view (`--sv-image`, `--fov` in **radians**, `--res 1024`).
- `run_mv.sh VIEWS_DIR OUT SEED sv|mv NAME`: Pixal3D multi-view (`--views`, `--pixal3d-weights`).
- `run_t2.sh IN.png OUT SEED NAME [--res 512|1024]`: TRELLIS.2 on the raven38 binary.
- `run_pw.sh IN.png OUT SEED NAME MODELS_DIR [args]`: pwilkin source build.
- `memwatch.sh LOG [GB]`: polls `footprint` every 10 s and kills `trellis-cli` above the limit.

Raw commands:
```zsh
B=.scratch/pixal3d/rel_metal/bin/trellis-cli; W=$PWD/.scratch/pixal3d/weights
# Pixal3D single view (input must be pre-matted RGBA; it is auto-cropped to alpha bbox x1.1 square)
$B --sv-image front.png --fov 0.3490658503988659 --models $W/pixal3d-sv-q8_0-v1 --seed 7 --res 1024 --require-gpu out.glb
# Pixal3D multi-view (DIR has transforms.json + RGBA frames, no matting, no re-crop)
$B --views DIR --pixal3d-weights mv --models $W/pixal3d-q8_0-v1 --seed 7 --res 1024 --require-gpu out.glb
# TRELLIS.2 single image, same engine
$B front.png out.glb --models $W/trellis2-gguf-q8 --seed 7 --res 512 --require-gpu
```

Flags:
- `--res 1024|1536` (Pixal3D has no 512 path) and `--seed N`. Steps are fixed at 12 in this binary; the pwilkin build has `--steps`.
- `--fov RAD` (SV gauge FOV, default 20°). Use about 20° or less for our orthographic art.
- `--decim GRID` / `--decim 0` (full mesh). Defaults: Pixal3D uses a 1M-face QEM budget with a 4096 atlas; TRELLIS.2 uses 300k @1024 / 150k @512 with a 2048 atlas. This binary has no `--faces`; the pwilkin build has `--faces N`.
- Also: `--atlas PX`, `--no-texture`, `--box-uv`, `--band N`, `--tex-res 512|1024`, `--webp off` (PNG textures), `--dump-post`, `--max-tokens`.
- A `.ply` voxel dump is written next to every GLB (about 120 MB); delete it if not needed.
- Output frame: Pixal3D generates in the **input camera frame**. With `.scratch/trellis_scripts/render_compare.py`, the input-facing side renders on the "back" camera, so pass `0 180` (X rotation, Z rotation) to face the front camera. TRELLIS.2 output is already front-facing.

### Multi-view `transforms.json` format
NeRF/Blender convention:
- Top-level `camera_angle_x` (radians, horizontal FOV) and `mesh_scale`.
- `frames[]`, each with `file_path`, an optional `name`, and a 4x4 row-major camera-to-world `transform_matrix`. An optional per-frame `camera_angle_x` is allowed.
- Frame 0 is the main/front view.

Canonical rig: elevation 0, distance 3.1192049980163574, FOV 20° (0.3490658503988659 rad).
- azim 0: `[[1,0,0,0],[0,0,-1,-3.1192],[0,1,0,0],[0,0,0,1]]`
- azim 90: `[[0,0,1,3.1192],[1,0,0,0],[0,1,0,0],[0,0,0,1]]`
- azim 180: `[[-1,0,0,0],[0,0,1,3.1192],[0,1,0,0],[0,0,0,1]]`
- azim 270: `[[0,0,-1,-3.1192],[-1,0,0,0],[0,1,0,0],[0,0,0,1]]`

The upstream sample is copied to `.scratch/pixal3d/src_pixal3d_mv_example/`. Our 2-frame front+back version is `.scratch/pixal3d/mv_frontback/views/transforms.json`.

Input rules:
- Every frame needs a real alpha channel; frames that are fully opaque are refused.
- Use the same scale for every view, with the object at about 85 % of frame height and centred.
- With no `transforms.json`, exactly 4 views in natural filename order are read as front, right, back, left, and `--mesh-scale` is required.
- `mv` weights are validated at V=4 and `sv` at V=1. Other counts run with a warning.

## 5. Measured results (front.png = `.scratch/hunyuan/inputs/front.png`, 768² RGBA)

| run | wall | peak footprint | output |
|---|---:|---:|---|
| Pixal3D SV, seed 7, FOV 20°, res 1024 | 262 s (rerun 297 s) | 4.04 GB (4.26) | 1 component, 972,548 tris, 4096 atlas; 1,887 voxels @32, 8,202 HR tokens |
| Pixal3D MV front+back (mv weights, V=2), seed 7 | 354 s | 7.76 GB | 5 components, 915,948 tris; 8,553 floaters dropped |
| TRELLIS.2 q8, res 512, seed 7 | 102 s | 2.40 GB | textured, dark red-shifted (the known TRELLIS.2 colour drift) |
| TRELLIS.2 q8, res 1024 cascade, seed 7 | 364 s | 7.20 GB | 1 component, 279,676 tris, **texture near-black** |
| TRELLIS.2 1024 `--tex-res 512` | 330 s | 6.03 GB | still near-black |
| pwilkin HEAD TRELLIS.2 1024 (and `--fa-f32`) | 566 s / 591 s | 8.60 / 8.72 GB | identical near-black texture |
| control: TRELLIS.2 1024 on the upstream Pixal3D sample image, seed 42 (heavy subject: 7,607 voxels, 32,149 HR tokens; auto res-512 texture) | 1503 s | 10.52 GB | **texture colour correct** (atlas mean 103/68/46 vs input 127/94/69) |

- Peak memory stays far under the 24 GB budget.
- The two seed-7 SV runs produced the same voxel, token and face counts, so the **geometry is reproducible**. The GLB bytes differ, so the texture is not bit-identical.

Renders:
- `.scratch/pixal3d/smoke/render/smoke_sheet.png`: input, then front/side/back/iso in the raw frame. The "back" tile is the input-facing side.
- `.scratch/pixal3d/mv_frontback/render/mv2_sheet.png`
- `.scratch/pixal3d/trellis2_same_engine/render/t2_sheet.png`
- `.scratch/pixal3d/trellis2_same_engine/dbg/t512_sheet.png`

## 6. Known issues

- **Metal tensor API disabled.** ggml prints `tensor API is not supported in this environment`, so the M5 neural accelerators are not used and bf16 runs on SIMD-group matmul. The speed is fine anyway.
- **The TRELLIS.2 1024-cascade texture is near-black on Metal for our input.** This happens in both engines and with both `--tex-res` values; the geometry is fine and res 512 is fine. The control run on the upstream Pixal3D sample (`.scratch/pixal3d/trellis2_same_engine/control/`) textures correctly, so it is most likely **input-specific** (not root-caused): TRELLIS.2's 1024 cascade turns our dark red/black anime art almost black. It is not an engine or Metal bug. Until it is resolved, use TRELLIS.2 1024 for **geometry only** (`--no-texture`) and res 512 for colour.
- **Pixal3D MV with our front+back concept views** loses most of the katana and pushes the bun backwards / doubles it. This matches the README's documented "thin protruding parts get duplicated" failure, made worse because our front and back drawings are not geometrically consistent. Single view is currently the better Pixal3D mode for Akane. MV needs consistent views, e.g. renders of our Blender rig.
- **SV hallucinates** a long black ponytail on the back, and the hair comes out black rather than dark brunette.
- Building pwilkin from source with the default CLT fails: the CLT `ld` cannot parse the MacOSX27.0 SDK `.tbd` files ("unknown architecture arm64e.x1"). Build with Xcode 26.6 instead:
  ```zsh
  X=/Applications/Xcode-26.6.0.app/Contents/Developer; export DEVELOPER_DIR=$X
  cmake -S .scratch/pixal3d/src_trellis_cpp/trellis.cpp -B .scratch/pixal3d/build_trellis_cpp -DCMAKE_BUILD_TYPE=Release \
    -DCMAKE_OSX_SYSROOT=$X/Platforms/MacOSX.platform/Developer/SDKs/MacOSX26.5.sdk \
    -DCMAKE_C_COMPILER=$X/Toolchains/XcodeDefault.xctoolchain/usr/bin/clang -DCMAKE_CXX_COMPILER=$X/Toolchains/XcodeDefault.xctoolchain/usr/bin/clang++
  cmake --build .scratch/pixal3d/build_trellis_cpp --target trellis-cli -j 8
  ```
  The source checkout is at `83e8080c40727bef04dbdbeceb2aef35faaf26fb`, with the ggml submodule at `f8697b33795db2ee6a2569b40853ca6aaa69f9b9` (pwilkin/ggml, branch `trellis`). CMake FetchContent pulls libwebp v1.5.0 from GitHub.
- To run Pixal3D SV with the pwilkin build, it expects `pixal3d_*.gguf` names **without** `_sv`, `--model pixal3d`, and `--fov` in **degrees** (its default is 49.13°). Symlink the `_sv` files to those names first. This is untested here.
- MoGe-2 FOV estimation is not ported in either engine, so FOV is always a manual flag.

## 7. Licences

- Code: raven38/pixal3d.cpp is **MIT** (© 2026 Piotr Wilkin, © 2026 raven); pwilkin/trellis.cpp is **MIT**; vendored ggml is MIT. TencentARC/Pixal3D code and weights are **MIT** (© 2026 Tencent). TRELLIS.2 is MIT.
- Weights: the flow GGUFs (Pixal3D SV/MV, TRELLIS.2) and the decoders are MIT.
- **`dinov3.gguf` is under the DINOv3 License** (Meta, 2025-08-19). It is royalty-free, worldwide, and allows commercial use and derivatives. Conditions:
  - Redistribution must carry the licence.
  - Publications must acknowledge DINO.
  - No reverse engineering of the materials.
  - Trade-control and ITAR exclusions apply.

  Copies of the licence texts are in `weights/pixal3d-sv-q8_0-v1/{LICENSE.md,MIT_LICENSE.md,DINOV3_LICENSE.md}`.
- BiRefNet (not downloaded) is MIT. Avoid RMBG-2.0, which is CC BY-NC.
- These are reference meshes only; nothing is redistributed.
