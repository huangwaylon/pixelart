# Pixal3D setup log
## Sat 24 Oct 2026 07:48:41 JST start: ML infra setup

## Sat 24 Oct 2026 07:50:03 JST route survey
- raven38/pixal3d.cpp: MIT, last push 2026-09-24, HEAD d1b4926452 (trellis2-mv native pipeline). 24 open issues, none Metal-blocking (Metal issues are perf/accuracy follow-ups #30/#31/#32/#47; #41 says MV 1024 on Metal: PASS; #87 studio drag-drop only). #85 open: flow DiT forward diverges from torch by 1.3-4.1% (numerics, all backends).
- Release showcase-assets-sv-1 has trellis-metal-macos-arm64.tar.gz (2,597,968 B, sha256 6cb8878e...4c1457 verified). Binary has --sv-image/--fov/--views/--pixal3d-weights but NOT --trellis2-mv (predates d1b4926).
- pwilkin/trellis.cpp: MIT, HEAD 83e8080c40 (2026-10-23), releases v0.8.1 have NO macOS asset -> would need source build. TRELLIS.2 only (no pixal3d).
- PHMFG/pixal-studio (MIT, 2026-10-22, 1 star) and lyonsno/pixal3d-mlx (no licence file / NOASSERTION, last 2026-07-02): fallbacks.
- Chosen: raven38/pixal3d.cpp prebuilt Metal binary (runs both Pixal3D SV/MV and TRELLIS.2 single image in one engine, reference postprocess).
- Weights: HF raven38/pixal3d-sv-q8_0-v1 rev 46d399ac (9 files, 8,091,975,360 B); MV set raven38/pixal3d-q8_0-v1 rev 1c4f4bdd shares 5 files byte-identical, +4 _mv flows (5,856,897,248 B). TRELLIS.2 ilintar/trellis2-gguf rev a57397bd q8/: dinov3/ss_dec/shape_dec/tex_dec byte-identical to Pixal3D shared files; extra needed ss_flow, shape_flow_512/1024, tex_flow_512/1024 (6,880,667,296 B) + birefnet 882,749,024 B.
- Throughput test: 100 MB ranged from HF in 7.3 s = 14.3 MB/s.

## Sat 24 Oct 2026 07:50:25 JST start SV weight download -> .scratch/pixal3d/weights/pixal3d-sv-q8_0-v1 (progress in weights/download.log)

## Sat 24 Oct 2026 08:04:35 JST SV weights downloaded + verified (9/9 size+sha256 match HF LFS and pixal3d-models.json). ~13 min incl. 2 throttle stalls auto-resumed.
## Sat 24 Oct 2026 08:04:35 JST smoke test: front.png SV seed 7 fov 20 res 1024 -> .scratch/pixal3d/smoke/

## Sat 24 Oct 2026 08:10:49 JST smoke test PASSED
- front.png (768 RGBA, pre-matted) SV seed 7 fov 20deg res 1024: 262.1 s wall, peak memory footprint 4.04 GB (/usr/bin/time -l), max RSS 4.01 GB. Metal tensor API disabled (M5 tensor ops not used by this ggml build), bf16 on.
- Output: 1 component, 972,548 tris (Pixal3D default 1M budget), atlas 4096 webp; voxels@32=1887, HR tokens 8202. Blender 5 imports EXT_texture_webp fine.
- Orientation: Pixal3D output is in the INPUT camera frame; in render_compare.py the input-facing side lands on the "back" (+Y) camera -> rotate Z 180 for our scripts.
- Quick look: strong face/eyes, bow, corset, katana, ribbons kept; hallucinated long black ponytail at back; hair too black vs dark brunette. Render: .scratch/pixal3d/smoke/render/smoke_sheet.png
## Sat 24 Oct 2026 08:10:49 JST start MV flow download (raven38/pixal3d-q8_0-v1 rev 1c4f4bdd, 4 _mv flows) + TRELLIS.2 q8 flows (ilintar/trellis2-gguf rev a57397bd). Shared files hard-linked from SV dir (sha-identical).

## Sat 24 Oct 2026 08:17:35 JST determinism: seed-7 rerun 296.8 s / 4.26 GB peak; identical voxel/token/face counts (1887 / 8202 / 972548), GLB sha differs (texture/WebP bytes) -> geometry reproducible, bytes not.

## Sat 24 Oct 2026 08:18:35 JST MV weights verified (9/9 vs manifest). MV run: front(azim0)+back(azim180), mv weights, seed 7, res 1024 -> mv_frontback/

## Sat 24 Oct 2026 08:25:02 JST MV front+back result: rc=0, 354.2 s, peak footprint 7.76 GB. V=2 with mv weights prints a "validated at V=4" warning. 8575 HR tokens; 5 components, 915,948 tris after dropping 8553 floaters.
- Quality (quick look, render .scratch/pixal3d/mv_frontback/render/mv2_sheet.png, rotated Z180): katana mostly gone, bun pushed far back / doubled, face less sharp than SV. Likely cause: the front and back concept views disagree (sword side, bun position), which is the "thin protruding parts duplicate" failure the README documents. SV is the better route for now. MV needs truly consistent views (e.g. renders of our Blender rig or a 4-view turnaround).

## Sat 24 Oct 2026 08:30:21 JST TRELLIS.2 q8 flows downloaded+verified (6 files sha OK, ~9.5 min). Run TRELLIS.2 same engine: front.png seed 7 res 1024 cascade -> trellis2_same_engine/

## Sat 24 Oct 2026 08:37:14 JST TRELLIS.2 same engine (q8, res 1024 cascade, seed 7): rc=0, 364.3 s, peak 7.20 GB. Geometry good: 1 component, 279,676 tris (300k QEM budget), dropped 665 floaters. BUT texture is ~black (base colour mean RGB 1.3/0.6/0.4 of 255). Pixal3D runs with the same tex_dec are fine -> suspect TRELLIS tex flow on Metal. Diagnosing with TRELLIS_DBG_NAN=1 --res 512.

## Sat 24 Oct 2026 08:46:33 JST TRELLIS.2 res 512: texture OK (dark/red-shifted, the known TRELLIS.2 colour drift), 101.7 s, 2.40 GB. res 1024 rerun with TRELLIS_DBG_NAN=1: again black, no NaN reported, 405.8 s, 7.21 GB. Trying --res 1024 --tex-res 512 workaround; cloning pwilkin/trellis.cpp HEAD for a source build.

## Sat 24 Oct 2026 08:47:53 JST pwilkin/trellis.cpp HEAD 83e8080c40 (v0.8.1+; ggml submodule f8697b33) now ALSO runs Pixal3D SV (--model pixal3d, --fov DEG) and has --faces/--steps + small-K-quant F16 fix. No macOS release asset -> source build in build_trellis_cpp/ (cmake Release, Metal auto, -j8).

## Sat 24 Oct 2026 08:55:19 JST --tex-res 512 workaround on raven38 binary: still very dark (atlas mean 15/7/8). 330 s, 6.03 GB. pwilkin build OK (needed Xcode-26.6 clang + MacOSX26.5.sdk: CLT ld cannot read the 27.0 SDK tbd). Running TRELLIS.2 1024 s7 on pwilkin build.

## Sat 24 Oct 2026 09:05:24 JST pwilkin HEAD TRELLIS.2 1024 s7: rc=0, 566.1 s, 8.60 GB peak; texture STILL near-black (atlas mean 12/4/4). So the dark 1024 texture is not fork-specific. Trying --fa-f32 (FlashAttention accumulation) as a numerics check.

## Sat 24 Oct 2026 09:15:28 JST --fa-f32: identical texture (no effect on Metal). Control test: TRELLIS.2 1024 on the upstream Pixal3D sample view00_azim000.png (RGBA) with the raven38 binary, to see if the dark texture is input-specific.

## Sat 24 Oct 2026 09:41:01 JST control TRELLIS.2 1024 on upstream sample: rc=0, 1503 s, 10.52 GB peak (32k HR tokens); texture colour correct -> dark 1024 texture is input-specific (TRELLIS.2 cascade + our dark flat art), not an engine/Metal bug. SETUP.md written.

## Sat 24 Oct 2026 09:42:41 JST TECH-ART: preparing Pixal3D inputs in .scratch/pixal3d/inputs/ (own white-bg flood-fill matte, no rembg)

## Sat 24 Oct 2026 09:47:49 JST MV pair v1 (gemini-3-pro-image, side-by-side sheet): mirrored-silhouette IoU 0.905 (head .945 torso .943 legs .813); sword offset ~15px; front flat sandals vs back heels.

## Sat 24 Oct 2026 09:50:39 JST v2 (edit of v1: flat sandals, 35deg sword): IoU 0.898; Argon critique 7.5/10, main issue sword offset/angle; (its bow/bun 'paradox' claim is wrong: bow in front of bun from front, bun in front of bow from back = consistent).

## Sat 24 Oct 2026 09:52:02 JST v3 (edit request to align sword) returned near-identical image (IoU 0.898). Residual: back right arm+hand+sword splayed ~16px further out (mirrored). Trying fresh v4 from prompt_v2 without v1 ref.

## Sat 24 Oct 2026 09:53:30 JST v4 (fresh, prompt_v2, refs turnaround_v6 + refs/1): IoU 0.951 (head .958 torso .953 legs .940), sword aligned within ~3px. Residual: back shows wrapped grip above hand, front hides it; back shoes look closed vs front strappy sandals. Trying v5 edit for the grip.

## Sat 24 Oct 2026 09:54:35 JST v5 (edit of v4 for grip/sandals) REJECTED: Gemini added a second katana to the front left hand (IoU 0.919). Selected v4 for MV.

## Sat 24 Oct 2026 09:55:50 JST TECH-ART inputs DONE -> .scratch/pixal3d/inputs/
- Matte: own method (.scratch/pixal3d_scripts/matte.py; numpy+scipy.ndimage): white-distance threshold (hard 18) + border flood fill, 2px opening to stop leaks through line-art gaps, soft 2px edge alpha (d/40) with un-premultiply vs white, speck removal; iso: low-chroma grey ground-shadow removal below y=800 + closing r=6 on outline-less blade edge. No rembg/isnet/BiRefNet/RMBG used (no licence question).
- Framing: frame.py, 1024x1024 RGBA, bbox max side = 85% of frame, premultiplied LANCZOS. MV pair: one shared scale + shared vertical offset (both halves of one Gemini sheet), each centred on head axis.
- Files: sv_front_v6.png, sv_iso34_v5.png, sv_front_gemA.png, mv_fb/{view00_azim000.png,view02_azim180.png,transforms.json}, mv_fb_overlay.png, inputs_sheet.png; work/ and gemini/ (fb_v1..v5 + prompts + overlays) kept for audit.
- MV iterations: v1 .905, v2 .898, v3 .898 (edit no-op), v4 .951 (chosen), v5 .919 (rejected, extra sword).

## Sat 24 Oct 2026 09:56:47 JST R1 GEN: launching sequential queue .scratch/pixal3d_scripts/r1_queue.sh (outputs .scratch/pixal3d/r1/)

## Sat 24 Oct 2026 09:56:52 JST R1 start sv_gemA_s7: /Users/waylonhuang/Documents/other/pixelart/.models/pixal3d_scripts/run_sv.sh /Users/waylonhuang/Documents/other/pixelart/.models/pixal3d/inputs/sv_front_gemA.png /Users/waylonhuang/Documents/other/pixelart/.models/pixal3d/r1/sv_gemA_s7 7 20

## Sat 24 Oct 2026 10:00:58 JST R1 end sv_gemA_s7 rc=0  245.56 real 170.16 user 8.50 sys  4229533488 peak memory footprint  245.56 real 170.16 user 8.50 sys  4229533488 peak memory footprint 

## Sat 24 Oct 2026 10:00:58 JST R1 start sv_gemA_s42: /Users/waylonhuang/Documents/other/pixelart/.models/pixal3d_scripts/run_sv.sh /Users/waylonhuang/Documents/other/pixelart/.models/pixal3d/inputs/sv_front_gemA.png /Users/waylonhuang/Documents/other/pixelart/.models/pixal3d/r1/sv_gemA_s42 42 20

## Sat 24 Oct 2026 10:06:04 JST R1 processed sv_gemA_s7 -> model/ai_ref/pixal3d/r1/akane_pixal3d_sv_frontgemA_s7-r1024-{full,8k}.glb (rz 180, mirrored X); clay + sprites done

## Sat 24 Oct 2026 10:06:09 JST R1 end sv_gemA_s42 rc=0  311.32 real 185.02 user 9.43 sys  4080012936 peak memory footprint  311.32 real 185.02 user 9.43 sys  4080012936 peak memory footprint 

## Sat 24 Oct 2026 10:06:09 JST R1 start sv_v6_s7: /Users/waylonhuang/Documents/other/pixelart/.models/pixal3d_scripts/run_sv.sh /Users/waylonhuang/Documents/other/pixelart/.models/pixal3d/inputs/sv_front_v6.png /Users/waylonhuang/Documents/other/pixelart/.models/pixal3d/r1/sv_v6_s7 7 20

## Sat 24 Oct 2026 10:07:45 JST R1 processed sv_gemA_s7 -> model/ai_ref/pixal3d/r1/akane_pixal3d_sv_frontgemA_s7-r1024-{full,8k}.glb (rz 180, mirrored X); clay + sprites done

## Sat 24 Oct 2026 10:13:08 JST R1 end sv_v6_s7 rc=0  418.45 real 193.54 user 9.74 sys  4294201184 peak memory footprint  418.45 real 193.54 user 9.74 sys  4294201184 peak memory footprint 

## Sat 24 Oct 2026 10:13:08 JST R1 start sv_v6_s42: /Users/waylonhuang/Documents/other/pixelart/.models/pixal3d_scripts/run_sv.sh /Users/waylonhuang/Documents/other/pixelart/.models/pixal3d/inputs/sv_front_v6.png /Users/waylonhuang/Documents/other/pixelart/.models/pixal3d/r1/sv_v6_s42 42 20

## Sat 24 Oct 2026 10:17:48 JST R1 end sv_v6_s42 rc=0  280.18 real 187.49 user 9.13 sys  4193685296 peak memory footprint  280.18 real 187.49 user 9.13 sys  4193685296 peak memory footprint 

## Sat 24 Oct 2026 10:17:48 JST R1 start sv_iso_s7: /Users/waylonhuang/Documents/other/pixelart/.models/pixal3d_scripts/run_sv.sh /Users/waylonhuang/Documents/other/pixelart/.models/pixal3d/inputs/sv_iso34_v5.png /Users/waylonhuang/Documents/other/pixelart/.models/pixal3d/r1/sv_iso_s7 7 20

## Sat 24 Oct 2026 10:21:51 JST R1 end sv_iso_s7 rc=0  243.33 real 155.83 user 8.26 sys  4029894376 peak memory footprint  243.33 real 155.83 user 8.26 sys  4029894376 peak memory footprint 

## Sat 24 Oct 2026 10:21:51 JST R1 start mv_fb_s7: /Users/waylonhuang/Documents/other/pixelart/.models/pixal3d_scripts/run_mv.sh /Users/waylonhuang/Documents/other/pixelart/.models/pixal3d/inputs/mv_fb /Users/waylonhuang/Documents/other/pixelart/.models/pixal3d/r1/mv_fb_s7 7 mv mv_fb_s7

## Sat 24 Oct 2026 10:22:46 JST R1 processed sv_gemA_s7 -> model/ai_ref/pixal3d/r1/akane_pixal3d_sv_frontgemA_s7-r1024-{full,8k}.glb (rz 180, mirrored X); clay + sprites done

## Sat 24 Oct 2026 10:26:11 JST R1 end mv_fb_s7 rc=0  259.20 real 167.95 user 9.44 sys  4342108072 peak memory footprint  259.20 real 167.95 user 9.44 sys  4342108072 peak memory footprint 

## Sat 24 Oct 2026 10:26:11 JST R1 start t2_gemA_s7: /Users/waylonhuang/Documents/other/pixelart/.models/pixal3d_scripts/run_t2.sh /Users/waylonhuang/Documents/other/pixelart/.models/pixal3d/inputs/sv_front_gemA.png /Users/waylonhuang/Documents/other/pixelart/.models/pixal3d/r1/t2_gemA_s7 7 t2_gemA_s7 --res 1024

## Sat 24 Oct 2026 10:27:08 JST R1 processed sv_gemA_s7 -> model/ai_ref/pixal3d/r1/akane_pixal3d_sv_frontgemA_s7-r1024-{full,8k}.glb (rz 180, mirrored X); clay + sprites done

## Sat 24 Oct 2026 10:30:24 JST R1 processed sv_gemA_s42 -> model/ai_ref/pixal3d/r1/akane_pixal3d_sv_frontgemA_s42-r1024-{full,8k}.glb (rz 180, mirrored X); clay + sprites done

## Sat 24 Oct 2026 10:31:19 JST R1 processed sv_v6_s7 -> model/ai_ref/pixal3d/r1/akane_pixal3d_sv_frontv6_s7-r1024-{full,8k}.glb (rz 180, mirrored X); clay + sprites done

## Sat 24 Oct 2026 10:31:22 JST R1 end t2_gemA_s7 rc=0  311.31 real 132.05 user 6.12 sys  4858826952 peak memory footprint  311.31 real 132.05 user 6.12 sys  4858826952 peak memory footprint 

## Sat 24 Oct 2026 10:31:22 JST R1 start t2_gemA_s7_512: /Users/waylonhuang/Documents/other/pixelart/.models/pixal3d_scripts/run_t2.sh /Users/waylonhuang/Documents/other/pixelart/.models/pixal3d/inputs/sv_front_gemA.png /Users/waylonhuang/Documents/other/pixelart/.models/pixal3d/r1/t2_gemA_s7_512 7 t2_gemA_s7_512 --res 512

## Sat 24 Oct 2026 10:32:59 JST R1 end t2_gemA_s7_512 rc=0  97.08 real 31.17 user 2.50 sys  2311096744 peak memory footprint  97.08 real 31.17 user 2.50 sys  2311096744 peak memory footprint 

## Sat 24 Oct 2026 10:32:59 JST R1 start sv_gemA_s7_r1536: /Users/waylonhuang/Documents/other/pixelart/.models/pixal3d_scripts/run_sv.sh /Users/waylonhuang/Documents/other/pixelart/.models/pixal3d/inputs/sv_front_gemA.png /Users/waylonhuang/Documents/other/pixelart/.models/pixal3d/r1/sv_gemA_s7_r1536 7 20 --res 1536

## Sat 24 Oct 2026 10:32:59 JST R1 end sv_gemA_s7_r1536 rc=1  0.01 real 0.00 user 0.00 sys  2474440 peak memory footprint  0.01 real 0.00 user 0.00 sys  2474440 peak memory footprint 

## Sat 24 Oct 2026 10:32:59 JST R1 queue done

## Sat 24 Oct 2026 10:33:07 JST R1 processed sv_v6_s42 -> model/ai_ref/pixal3d/r1/akane_pixal3d_sv_frontv6_s42-r1024-{full,8k}.glb (rz 180, mirrored X); clay + sprites done

## Sat 24 Oct 2026 10:33:59 JST R1 processed mv_fb_s7 -> model/ai_ref/pixal3d/r1/akane_pixal3d_mv2_frontback_s7-r1024-{full,8k}.glb (rz 180, mirrored X); clay + sprites done

## Sat 24 Oct 2026 10:39:31 JST R1: sv_gemA_s7 --res 1536 refused by the raven38 release ('--sv-image supports --res 1024 only in this release') -> 1024 is both default and only SV resolution; dropped. T2 1024 gemA s7 311 s 4.86 GB; T2 512 97 s 2.31 GB.

## Sat 24 Oct 2026 10:42:03 JST R1 processed sv_iso_s7 -> model/ai_ref/pixal3d/r1/akane_pixal3d_sv_iso34_s7-r1024-{full,8k}.glb (rz Z180,X-30,Z-45, mirrored X); clay + sprites done

## Sat 24 Oct 2026 10:42:16 JST R1 processed t2_gemA_s7 -> model/ai_ref/pixal3d/r1/akane_trellis2cpp_4b1024_frontgemA_s7-{full,8k}.glb (rz 0, mirrored X); clay + sprites done

## Sat 24 Oct 2026 10:42:26 JST R1 processed t2_gemA_s7_512 -> model/ai_ref/pixal3d/r1/akane_trellis2cpp_4b512_frontgemA_s7-{full,8k}.glb (rz 0, mirrored X); clay + sprites done

## Sat 24 Oct 2026 10:42:41 JST R1 baselines processed (stats + mirrored clay renders) -> .scratch/pixal3d/r1/baselines/

## Sat 24 Oct 2026 10:49:19 JST R1 processed t2_gemA_s7_512 -> model/ai_ref/pixal3d/r1/akane_trellis2cpp_4b512_frontgemA_s7-{full,8k}.glb (rz 0, mirrored X); clay + sprites done

## Sat 24 Oct 2026 10:50:42 JST R1 T2 diag: gemA T2 512 texture also near-black (atlas nonzero mean 37/38/39 grey, 6% coverage) while earlier front.png T2 512 was coloured. Running T2 512 s7 on sv_front_v6 (same art as front.png, new matte/framing) to separate art vs preprocessing.

## Sat 24 Oct 2026 10:54:50 JST R1 T2 diag RESULT: T2 512 on sv_front_v6 (1024 px) -> black; same image LANCZOS-resized to 768 px -> coloured (usual dark drift). Input pixel size 1024 triggers the near-black TRELLIS.2 texture in the raven38 T2 path (Pixal3D path unaffected). Rerunning gemA T2 512 from a 768 px copy.

## Sat 24 Oct 2026 10:56:28 JST R1 processed t2_gemA768_s7_512 -> model/ai_ref/pixal3d/r1/akane_trellis2cpp_4b512_frontgemA768_s7-{full,8k}.glb (rz 0, mirrored X); clay + sprites done

## Sat 24 Oct 2026 11:01:27 JST R1 sprites: added --colour tex mode (r1_sprites.py: per-face samples of the generated base-colour texture, snapped to palette classes, same heuristics/smoothing) for Pixal3D runs + T2 512@768px; concept-projection rows kept for parity with baselines.

## Sat 24 Oct 2026 11:07:39 JST R1 DONE (technical artist, generation round 1)
- Runs (raven38 Metal trellis-cli, sequential, memwatch 22 GB; all peaks <= 4.9 GB): SV gemA s7 246 s/4.23 GB, SV gemA s42 311 s/4.08, SV v6 s7 418 s/4.29 (contended), SV v6 s42 280 s/4.19, SV iso34 s7 243 s/4.03, MV front+back (v4 pair, mv weights, V=2) 259 s/4.34, T2 1024 gemA 311 s/4.86, T2 512 gemA 97 s/2.31, T2 512 gemA@768px 89 s/2.31. SV --res 1536 refused by this release (1024 only).
- Exports: model/ai_ref/pixal3d/r1/*-full.glb + *-8k.glb + .txt sidecars (orient_export.py: Pixal3D Z180, iso Z180,X-30,Z-45, T2 0; all mirrored X -> sword in LEFT hand; 8k = pymeshlab QEM + smart UV + Cycles colour bake).
- Watertight (strict: no boundary and no >2-face edges after welding): NONE of the r1 meshes; SETUP's earlier 'watertight' claim for the smoke mesh does not hold under this test (565-1660 open edges, 3.8k-26k non-manifold edges from DC remesh). Only Hunyuan 2mini is strictly watertight. Components: Pixal3D 1-2, T2 1-3, trellis-mac baseline 6625.
- Findings: MV front+back with the v4 Gemini pair is now the best Pixal3D geometry (full hooked-guard katana, no hallucinated ponytail; bun doubled/pushed back, sword flat in frontal plane). SV keeps inventing a long ponytail (gemA) or braid (v6). Pixal3D textures are good (red dress, corset, bow, skin) but hair is black.
- T2 near-black texture: triggered by 1024 px input images in the raven38 T2 path (512 res black on 1024 px gemA/v6; coloured after LANCZOS resize to 768 px). 1024 cascade was black even for 768 px front.png earlier.
- Sheets: .scratch/pixal3d/r1_sheet_3d.png, .scratch/pixal3d/r1_sheet_sprites.png (concept-projection rows for parity + own-texture rows via r1_sprites.py --colour tex; procedural renders/model_round_7).
- Sat 24 Oct 2026 11:08:55 JST: GEMINI LIAISON r1 verdict request sent (prompt .scratch/pixal3d_scripts/r1_gemini_prompt.txt)
- Sat 24 Oct 2026 11:09:21 JST: GEMINI r1 verdict received -> .scratch/pixal3d/r1_gemini_verdict.json (pixal3d_beats_trellis=yes; top mv_frontback_s7=7, sv_gemA_s7=7)

## Sat 24 Oct 2026 11:09:23 JST - lead 3D TA review of r1
- Blender 5 headless re-verify (.scratch/pixal3d_scripts/lead_verify_stats.py, weld 1e-6, peak RSS 1.7 GB): stats match sheet.
  pixal sv_gemA_s7 full: 956k tris, open 565, >2-face 6586, 1 comp, dims 0.52x0.58x0.94 (depth inflated by invented ponytail)
  pixal mv2 s7 full: 972k, open 1536, >2-face 14616, 1 comp, depth 0.44
  t2cpp 512@768: 146k, open 874, >2-face 3567, 1 comp, depth 0.35 ; t2cpp 1024: 278k, open 1788, >2-face 5000, 3 comps
  trellis-mac: 297k, open 73839, >2-face 23839, 6625 comps ; hunyuan mini: 311k, 0/0, 1 comp (only watertight)
  8k decimations: pixal sv 16 comps (top 3866 verts, 111), mv 32 comps; open edges rise to 866/1353 -> 8k is preview-only.
- Verdict: mixed. Pixal3D MV front+back is best reference draft for silhouette/sword; SV invents ponytails; T2 cpp cleaner surfaces but colour broken.

## Sat 24 Oct 2026 11:10:08 JST - pixel-art lead review of r1 sprite sheet
- Wrote .scratch/pixal3d_scripts/lead_pixel_counts.py (pure numpy, no scipy). Output: .scratch/pixal3d/r1/stats/lead_pixel_counts.json
- 8-dir 64px totals: iso_col = px with no same-colour 8-neighbour; pinhole = pipeline noise.json 'orphans'. Fully detached opaque px = 0 on all rows.
- iso/1k opaque px: PROC_r7 21.8 | t2_768_tex 32.4 (too dark, only 12.8 colours) | sv_iso_tex 46.8 | sv_gemA_s42_tex 52.5 | sv_v6_s42_tex 53.0 | sv_gemA_s7_tex 55.1 | BASE trellis 56.9 | BASE hunyuan 58.0 | t2_768 concept 59.0 | mv_fb_tex 60.2 | concept-projected Pixal3D 61.7-64.9 | t2 1024 67.7 | mv_fb concept 72.7
- pinholes (8 dirs): PROC 24 | t2_768 42 | t2 cpp 52-56 | hunyuan 58 | trellis-mac 70 | Pixal3D 73-97 (mv_fb 97 worst)
- Verdict: Pixal3D own-texture rows give the cleanest flat colour clusters among AI rows; concept-projected Pixal3D is no cleaner than TRELLIS. Invented ponytail and dark back-cavity holes are the main cleanup costs.

## Sat 24 Oct 2026 11:13:01 JST R2 start (technical artist, tuning round 2)
- Plan (max 4 heavy generations, sequential, memwatch 22 GB):
  1. mv4_gem_s7: Pixal3D MV with the 4 views the mv weights were validated for (v4 Gemini front/back + new Gemini side pair L/R, consistent with v4), shared scale, canonical rig transforms (azim 0/90/180/270).
  2. mv4_gem_s42: second seed of the same (robustness).
  3./4. SV front with a clearly drawn bun above the bow (Gemini edit of gemA), seeds 42 and 7; auto ponytail check depth/height > 0.45 = reject.
- Post-process for every r2 mesh AND the best T2 baseline (r1 t2cpp 512@768): weld, Blender voxel remesh (~0.0045*height), drop tiny islands, texture re-baked from the raw mesh; 8k decimated from the remesh (pymeshlab, topology preserving). Sprite post adds a 1-px pinhole (4-neighbour majority) fill, skipping eye/outline colours; applied to every AI row incl. both baselines.
- Azimuth check from the upstream example: azim 90 camera at +X sees the subject's LEFT side (face points image-left); azim 270 = RIGHT side (face points image-right).
- Sat 24 Oct 2026 11:13:42 JST Gemini side pair v1 requested (refs fb_v4, turnaround v6, refs/1) -> r2/inputs/gemini/side_v1.png
- Sat 24 Oct 2026 11:14:34 JST side_v1 rejected (non-chibi proportions, short dress, no collar, ground line). Requested 4-view turnaround turn4_v1 (front/left/back/right on one canvas)
- Sat 24 Oct 2026 11:15:19 JST turn4_v1 rejected (short dress, sleeveless, scabbards, figures cut at canvas edge). Requested side_v2 = EDIT of fb_v4 rotating both figures to side profiles
- Sat 24 Oct 2026 11:18:43 JST side_v3 (edit of side_v2: scabbard removed, flat sandals; blade still diagonal-forward in the right profile, accepted) matted+framed with frame4.py to the v4 front scale -> r2/inputs/mv4_gem/ (4 views + canonical transforms identical to upstream sample). L/R mirror IoU 0.953 (head 0.986). SV bun edit requested (bun_v1).

## Sat 24 Oct 2026 11:18:53 JST R2 start mv4_gem_s7: ./run_mv.sh /Users/waylonhuang/Documents/other/pixelart/.models/pixal3d/r2/inputs/mv4_gem /Users/waylonhuang/Documents/other/pixelart/.models/pixal3d/r2/mv4_gem_s7 7 mv mv4_gem_s7
- Sat 24 Oct 2026 11:21:58 JST r2_remesh.py tested on r1 mv_fb_s7: voxel 0.0045h alone -> watertight but sleeves shredded (8 comps, 146 islands dropped); with solidify 1.5 voxels first -> watertight, 1 component, 206k tris, sleeves + katana intact, 8k (topology-preserving QEM) also watertight/1 comp. 12.7 s, Blender peak 11.2 GB. Defaults: VOX 0.0045, SOLID 1.5, tex 2048.

## Sat 24 Oct 2026 11:22:41 JST R2 end mv4_gem_s7 rc=0  227.37 real 145.71 user 8.06 sys  4269379352 peak memory footprint  227.37 real 145.71 user 8.06 sys  4269379352 peak memory footprint 

## Sat 24 Oct 2026 11:23:09 JST R2 start sv_gemBun_s42: ./run_sv.sh /Users/waylonhuang/Documents/other/pixelart/.models/pixal3d/r2/inputs/sv_front_gemBun.png /Users/waylonhuang/Documents/other/pixelart/.models/pixal3d/r2/sv_gemBun_s42 42 20

## Sat 24 Oct 2026 11:25:03 JST R2 processed mv4_gem_s7 -> model/ai_ref/pixal3d/r2/akane_pixal3d_mv4_gem_s7-r1024-{full,remesh,8k}.glb (rot 180, mirrored X); clay + sprites (remesh, pinhole fill) done

## Sat 24 Oct 2026 11:26:56 JST R2 end sv_gemBun_s42 rc=0  226.98 real 163.64 user 6.61 sys  3930394248 peak memory footprint  226.98 real 163.64 user 6.61 sys  3930394248 peak memory footprint 
- Sat 24 Oct 2026 11:30:11 JST mv4_gem_s7 done (227 s, 4.27 GB): single bun on top-back, no ponytail, depth/height 0.40; katana became a wide plank in side/iso because the right-profile blade (diagonal-forward) contradicts the front (35 deg outward -> vertical in profile). Built mv4_gemfix: view03 blade rotated to vertical about the guard (blade_fix.py, tip at y=940 like the sole line, background strip cleared, body strip diffusion in-painted); other 3 views + transforms identical. Run 2 will be mv4_gemfix s7 (same seed -> isolates the input fix) instead of a second seed.

## Sat 24 Oct 2026 11:30:41 JST R2 start mv4_gemfix_s7: ./run_mv.sh /Users/waylonhuang/Documents/other/pixelart/.models/pixal3d/r2/inputs/mv4_gemfix /Users/waylonhuang/Documents/other/pixelart/.models/pixal3d/r2/mv4_gemfix_s7 7 mv mv4_gemfix_s7

## Sat 24 Oct 2026 11:31:15 JST R2 processed sv_gemBun_s42 -> model/ai_ref/pixal3d/r2/akane_pixal3d_sv_frontgemBun_s42-r1024-{full,remesh,8k}.glb (rot 180, mirrored X); clay + sprites (remesh, pinhole fill) done
- Sat 24 Oct 2026 11:31:48 JST sv_gemBun_s42 done (227 s, 3.93 GB). REJECTED by the ponytail detector: depth/height 0.91 (bbox 0.49 x 0.83 x 0.92). The prominent bun drawn above the bow is read as the root of a long high ponytail that reaches the hem -> the edit made the SV hallucination worse, not better. Not repeating SV with seed 7; 4th slot goes to MV.

## Sat 24 Oct 2026 11:32:35 JST R2 processed t2_gemA768_s7_512 -> model/ai_ref/pixal3d/r2/akane_trellis2cpp_4b512_frontgemA768_s7-{full,remesh,8k}.glb (rot -, mirrored X); clay + sprites (remesh, pinhole fill) done

## Sat 24 Oct 2026 11:33:44 JST R2 processed r1_mv_fb_s7 -> model/ai_ref/pixal3d/r2/akane_pixal3d_mv2_frontback_s7-r1024-{full,remesh,8k}.glb (rot -, mirrored X); clay + sprites (remesh, pinhole fill) done

## Sat 24 Oct 2026 11:34:42 JST R2 end mv4_gemfix_s7 rc=0  241.67 real 171.53 user 8.51 sys  4420341720 peak memory footprint  241.67 real 171.53 user 8.51 sys  4420341720 peak memory footprint 

## Sat 24 Oct 2026 11:36:31 JST R2 processed mv4_gemfix_s7 -> model/ai_ref/pixal3d/r2/akane_pixal3d_mv4_gemfix_s7-r1024-{full,remesh,8k}.glb (rot 180, mirrored X); clay + sprites (remesh, pinhole fill) done

## Sat 24 Oct 2026 11:37:11 JST R2 start mv4_gemfix_s42: ./run_mv.sh /Users/waylonhuang/Documents/other/pixelart/.models/pixal3d/r2/inputs/mv4_gemfix /Users/waylonhuang/Documents/other/pixelart/.models/pixal3d/r2/mv4_gemfix_s42 42 mv mv4_gemfix_s42
- Sat 24 Oct 2026 11:37:11 JST mv4_gemfix_s7 done (242 s, 4.42 GB); started mv4_gemfix_s42 (4th and last heavy run).

## Sat 24 Oct 2026 11:40:31 JST R2 end mv4_gemfix_s42 rc=0  199.42 real 147.00 user 6.43 sys  4196421376 peak memory footprint  199.42 real 147.00 user 6.43 sys  4196421376 peak memory footprint 

## Sat 24 Oct 2026 11:42:26 JST R2 processed mv4_gemfix_s42 -> model/ai_ref/pixal3d/r2/akane_pixal3d_mv4_gemfix_s42-r1024-{full,remesh,8k}.glb (rot 180, mirrored X); clay + sprites (remesh, pinhole fill) done

## Sat 24 Oct 2026 11:49:24 JST R2 DONE (technical artist, tuning round 2)
- Heavy runs (sequential, memwatch 22 GB, peaks 3.9-4.4 GB): mv4_gem_s7 227 s/4.27 GB | sv_gemBun_s42 227 s/3.93 GB | mv4_gemfix_s7 242 s/4.42 GB | mv4_gemfix_s42 199 s/4.20 GB. V=4 ran with no "validated for 4 views" warning.
- MV 4-view (Gemini v4 front/back + Gemini side pair side_v3, frame4.py shared scale; canonical azim 0/90/180/270 transforms identical to the upstream sample): single bun on top-back, no ponytail, no doubled bun; depth/height 0.40 in all 3 MV4 runs (r1 MV2 0.48, T2 0.35). Katana survives with hook guard but becomes a thick plank in side/iso (the right profile cannot match the 35-deg-outward front blade; blade_fix narrowed it slightly). s7 vs s42 consistent.
- SV with an enlarged bun (bun_v1 edit): REJECTED by the ponytail detector, depth/height 0.91 - the bun becomes the root of a floor-length ponytail. SV should not be used for this character.
- r2 post (r2_remesh.py: solidify 1.5 vox -> voxel remesh 0.0045 h -> island drop -> 2048 bake; 8k = topology-preserving QEM): every r2 mesh AND the T2 baseline (r1 t2cpp 512@768) and r1 MV2 are now strictly WATERTIGHT and 1 component at both the remesh (197-311k tris) and 8k levels; 6-18 s each.
- Sprite post (r2_post.py pinhole fill): 8-dir pinholes Pixal3D 75-97 -> 16-28, T2 42/68 -> 13/26, trellis-mac 70 -> 20, Hunyuan 58 -> 20 (procedural r7 24, no post). Remesh alone only 97 -> 83; the fill does the work.
- r2 pixel counts: .scratch/pixal3d/r2/stats/r2_pixel_counts.json. Gemini Argon verdict: .scratch/pixal3d/r2_gemini_verdict.json (best mv4_gemfix_s42; pixal3d_beats_trellis=yes; concept projection bleeds face/skin onto the back of the head).
- Sheets: .scratch/pixal3d/r2_sheet_3d.png, .scratch/pixal3d/r2_sheet_sprites.png. Models: model/ai_ref/pixal3d/r2/*-{full,remesh,8k}.glb + .txt.

## Sat 24 Oct 2026 11:51:28 JST - Gemini liaison r2 verdict
Asked gemini.py ask --json (prompt .scratch/pixal3d_scripts/r2_judge_prompt.txt) with r2_sheet_3d, r2_sheet_sprites, refs/1.png, concept v6. Verdict saved to .scratch/pixal3d/r2_gemini_verdict.json: pixal3d_beats_trellis=yes, top mv4_gemfix_s42 (7.0).

## Sat 24 Oct 2026 11:51:44 JST - lead 3D TA judge (r2)
- Blender recheck of stats, script .scratch/pixal3d_scripts/judge_stats.py. Weld at 1e-7 and face-edge connectivity give these raw piece counts: mv4_gemfix_s42 51 (main 99.7%), mv4_gem_s7 108, t2cpp 52, trellis-mac 12,750. All remesh and 8k files: 1 piece, 0 open edges, 0 non-manifold. Hunyuan mini: watertight. Depth/H: MV4 0.40-0.41, t2cpp 0.35, trellis-mac 0.42, hunyuan 0.52.
- Verdict: Pixal3D MV4 s42 is the best reference, ahead of TRELLIS.2. Katana and ribbons stay procedural.

## 2026-10-24 11:52:33 pixel-art lead review r2
- wrote .scratch/pixal3d_scripts/lead_r2_orphans.py (exact-colour iso px, small clusters, holes) and lead_r2_orphans_tol.py (RGB-tol 48 orphans); json in r2/stats/lead_pixelart_orphans.json
- tol-orphans/8 dirs: mv4_gemfix_s42_tex 393, mv4_gemfix_s7_tex 360, mv4_gem_s7_tex 408, r1_mv_fb_tex 329, sv_tex 350, t2cpp concept 423, trellismac 366, hunyuan 406, procedural r7 162
- zooms: lead_review/pxlead_zoom_a.png, pxlead_zoom_b.png
- 2026-10-24 11:53:29 JST LEAD: copied best meshes (mv4_gemfix_s42 full/remesh/8k + transforms; t2cpp 768 remesh/8k companion) to model/ai_ref/pixal3d/best/; sheets copied to docs/img/pixal3d_*.png; writing docs/pixal3d_experiment.md
- 2026-10-24 12:05:19 JST LEAD: wrote docs/pixal3d_experiment.md (setup, r1/r2 runs+sheets, verdicts, conclusion, disk usage). best/ verified.
