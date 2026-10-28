# 03: Research: promising techniques we have not tried yet

Research lead, 2026-10-28. Scope: both projects (Snowpeak at the repo root, Swordswoman/Akane in `swordswoman/`).
This deliberately skips everything already covered in `swordswoman/docs/*.md` (image-to-3D survey, Hunyuan/TRELLIS/Pixal3D, pixel rules, cleanup guide), `docs/research/*.md` and `reference/3d/sota_survey`.

**Sources and confidence.** The network was only partly open this session. GitHub and the Hugging Face API were reachable. `pixellab.ai`, `retrodiffusion.ai` and other vendor sites were **blocked by the proxy**, so I could not check vendor pricing pages. How each claim is marked:
- **[V]**: verified today from a GitHub README or the HF API.
- **[M]**: from memory or secondary knowledge, not re-verified.
- **[U]**: uncertain or unknown.

## 0. What we are actually failing at (the target)

1. **Animation life.** Swordswoman `animate96` passes QC but scores only 3–5 on motion. `v2/motion` walk reached Opus 7, but the run stalled. Snowpeak animation is procedural and stiff.
2. **Identity drift when generating new poses.** Gemini 48 px redraws went off-model (4.5–5.5). Single-view 3D invents details (the ponytail).
3. **3D-to-pixel looks lifeless or noisy.** This happened with the Blender render cleanup in v1 and with the Blender models in Snowpeak r18–r20.
4. **Cost per frame.** Every frame is an Opus redraw over a rig guide plus a critic loop. That is slow and not deterministic. PixelOE itself isn't bit-deterministic either.

Below, each candidate is judged against these four.

---

## 1. Dedicated pixel-art generators (hosted)

### 1a. Retro Diffusion (RD Pro) via its MCP server
- **What:** a hosted pixel-art model family (RD Fast, Plus, Pro, Mini). It has an official MCP server at `mcp.retrodiffusion.ai/mcp`, authenticated with a bearer key [V].
- **Tools it exposes** [V]:
  - 8-direction rotations
  - walk, idle, jump, crouch and attack cycles built **from a start frame**
  - **up to 9 reference images** for consistency
  - `create_user_style` from a reference image
  - palette converter
  - free `fix_pixel_art` grid repair
- **Size and price** [V]: sprites from 16 up to 384 px depending on style. Pay per generation, no subscription. About $0.015–0.18 per image and $0.07–0.25 per animation.
- **Maturity:** a production product. The same team makes the Aseprite extension and `pixeldetector` (MIT) [V].
- **Mac:** hosted, so yes. **Blocker:** it needs `mcp.retrodiffusion.ai` on the domain allowlist, which needs user approval.
- **Plug-in point:** feed the approved `EC0_*_96` masters as references and ask for an idle or walk from the SE master. For Snowpeak, feed a locked-palette build frame.
- **Payoff:** goes straight at failures 1 and 4. The risk is failure 2: house style drifting from our masters. The 96 px figure in a 128 cell is within its limits [V]. **I do not expect frames we can ship as-is.** I do expect strong *motion keys*: timing and silhouettes that Opus then redraws on-model. That replaces our weakest asset, the rig guide's stiff motion.
- **1-day experiment:** about $10 of credits.
  1. Run 3 references (SE master, S master, one head stamp) through walk, idle and attack from the SE start frame.
  2. Score with the existing `v2/qc` gate plus Opus motion critic, against `animate96`'s 3–5.
  3. In parallel, run `fix_pixel_art` on our Gemini illustrations as a free alternative pixelizer, compared against E2.

### 1b. PixelLab
- **What:** a hosted pixel-character model. Its MCP exposes `create_character(n_directions=4|8)`, `animate_character` (walk, run, idle), tilesets and isometric tiles [V].
- **Not checked** (vendor site blocked): skeleton/pose-keypoint animation, inpainting, style reference, Aseprite plugin [M]. Pricing is a subscription of roughly $10–50 a month [M/U].
- **Fit:** strongest for **Snowpeak**. It is isometric-aware, 8-direction-native, and works at small sizes. Its best-known size range is ≤128 px [M]. Pose-skeleton animation, if confirmed, would take our raycaster's joint positions directly.
- **1-day experiment:**
  1. Generate the Snowpeak base character in 8 directions from a text description plus our palette.
  2. Animate a walk.
  3. Diff it against our deterministic build on silhouette, palette lock and outline, using `pixelrules.py` lints as the metric.

  Main question: is its 8-direction *consistency* better than ours? Ours is perfect by construction, so mostly this tests whether its *animation* is better.

### 1c. LLM pixel-painting agents (texel-studio pattern)
- `EYamanS/texel-studio` (239★, active) has an LLM paint with primitive tools: pixel, line, ellipse, read-pixel, palette inspection. Gemini makes the concept [V].
- This is close to what our Opus redraw already does, but with **tool calls instead of whole-image output**. The idea worth stealing is a *tool-based edit API* for Opus: "set these pixels", "move cluster", "query colour at" applied to the master, instead of regenerating the frame. That should cut drift (failure 2) and make edits diffable.
- **1-day experiment:** wrap our `.pix` grid format in 6 tools and have Opus do one `animate96` frame fix by tool calls. Compare pixel diff against master and the critic score.

## 2. Open-weight pixel models and character LoRAs (local, Mac)

- **Pixel-art LoRA landscape on HF (download leaders)** [V]:
  - `nerijs/pixel-art-xl` (SDXL, 33k downloads)
  - `tarn59/pixel_art_style_lora_z_image_turbo` (Z-Image, 2025-11)
  - `e-n-v-y/Krea-2-Pixel-Art` (2026-09)
  - `adirik/pixel-art-lora-flux.2-klein-4B` (2026-08)
  - `prithivMLmods/Qwen-Image-2512-Pixel-Art-LoRA`
  - PixelArt-Redmond for Z-Image, Qwen-Image and FLUX.2-Klein-9B
  - one Pokemon-trainer sprite LoRA
- **Mac route: `mflux` (MLX)** [V]. It runs FLUX.2 Klein 4B/9B, Z-Image, Qwen-Image and Kontext edit, and **supports LoRA fine-tuning on Mac for Z-Image and FLUX.2**.
- **Character LoRA on our masters.** This is the big untried idea for failure 2. Train a FLUX.2-Klein-4B or Z-Image LoRA on the following, captioned by direction and pose:
  - Swordswoman: the 5 `EC0` masters, 45 head stamps and the Gemini turnaround illustrations, upscaled ×4 nearest-neighbour
  - Snowpeak: `art/hand`
- **How it would be used:** generate poses with that LoRA, conditioned on our rig-guide render. Klein is an edit model [V], so img2img or reference-edit with the guide as input should work [U on pose-ControlNet availability for Klein on MLX]. Then run the result through the E2 pixelizer and palette lock.
- **Expected payoff:** identity locked by weights rather than by prompt. Gemini cannot give us that.
  - **Risk:** 5 masters is a tiny dataset. Augment by flipping where symmetric and by adding head-stamp composites.
  - **Risk:** diffusion re-introduces mush at 96 px. Our pixelizer already handles that.
- **Palette-indexed diffusion:** no mature open model generates palette indices directly [M]. The practical equivalent is LoRA output → k-centroid → palette lock, which we already have. Not worth research time.
- **1-day experiment:**
  1. Run `uv tool install mflux`.
  2. Train a rank-16 LoRA on Klein-4B over ~40 augmented images. On an M5 Max, expect a few hours [U].
  3. Generate SE walk contact and passing poses from H2 guide renders via edit mode.
  4. Pixelize with E2.
  5. Score identity with the Opus critic against the masters.

## 3. Animation-specific models

### 3a. ToonCrafter (keyframe interpolation)
- **What:** generative cartoon inbetweening between two keyframes, with optional sparse-sketch guidance. Apache-2.0 [V].
- **Limits:** 320×512, 16 frames. About 24 GB VRAM officially, ~10–12 GB in fp16 community versions [V]. Last dated release 2024-05 [V], so it is effectively frozen.
- **Mac:** PyTorch-MPS should fit in 64 GB, but expect slow runs and xformers removal. No Mac port is known [U].
- **Plug-in point:** our masters are excellent *keys*. Scale two approved keys (for example the walk contact and passing frames) ×4 to around 384, interpolate, then pixelize each frame with palette lock. Sketch guidance can take our rig-guide silhouettes.
- **Payoff:** smooth arcs and secondary motion (failure 1). The known weakness is flicker and colour-cluster boiling after pixelization. That is a solvable cleanup problem: temporal palette-index smoothing.
- **1-day experiment:** get it running on MPS (half a day). Interpolate idle f00 to idle f04 for SE. Pixelize, run `v2/qc`, and compare motion scores.

### 3b. Video models with pose control: Wan2.2-Animate, Veo, Kling
- **Wan2.2-Animate-14B** takes a reference character image plus a driving pose video and returns the animated character. It is the open state of the art for exactly our "rig guide → on-model frame" step [M].
  - Mac ports exist but are immature: `dtellz/spielberg` (4-bit MLX port of Wan2.2-Animate, 2026-05) and `bhubbard/mlx-video-rs` (Wan2.1/2.2, LTX-2) [V, 0 stars, unvetted].
  - Wan2.2-TI2V-5B has MLX ports too [V].
- **Veo via Floodgate:** `tools/gemini.py` only calls `generateContent` on `gemini-*` models. Veo uses a long-running predict endpoint, so whether it is reachable through Floodgate is **[U]**. Worth one curl. Kling is a hosted paid API [M], and its domain would need allowlisting.
- **Plug-in point:**
  1. Render rig H2 plus mocap (LaFAN1 walk) as a skeleton/depth video at 512 px.
  2. Feed it to Wan-Animate with the SE illustration as reference.
  3. Pixelize each frame with E2, then palette lock, then temporal cleanup.
  4. Opus fixes only the face, using the existing head-stamp lock.
- **Payoff:** potentially the biggest jump in *liveliness*. The model brings cloth, hair and weight physics our springs only approximate. Risks: identity drift in the bow and katana, and pixelization flicker.
- **1-day experiment:** try `spielberg` on a 2-second walk clip. If the Mac port fails within 2 hours, fall back to one paid cloud run (rented GPU or the Kling API; needs approval) purely to measure payoff before investing.

### 3c. Sub-pixel and smear techniques (a hand rule, not a model)
These are already *documented* in `pixel_art_best_practices.md` §8.4 but not *implemented*. Two pieces:
- **Sub-pixel motion pass.** For a sub-pixel offset of the bob, bow or ribbon tips, shift the 1-px AA edge colours instead of moving whole pixels. Implement it as a post-pass on `animate96` frames using the palette ramp.
- **Smear frames.** Add these to attack clips.

**1-day experiment:** code a `subpixel_bob.py` for idle. This is a cheap motion-score lift.

## 4. 3D → pixel rendering approaches

### 4a. t3ssel8r-style stable pixel rendering (Snowpeak primarily)
- **The technique:** render 3D at native low resolution with an orthographic camera **snapped to texel grid**, toon ramp quantized to palette bands, depth+normal edge detection for outlines, and light-aware edge colouring [M; outline part cited in our docs].
- **Fit:** Snowpeak's raycaster already does most of this. The untried piece is **normal/depth-buffer outline and highlight rules**, as opposed to silhouette-only, plus *camera snapping across animation frames*, which kills shimmer.
- **1-day experiment:** export normal and depth buffers from `pipeline/render.py`. Add a Roberts/Sobel edge pass on normals for interior lines (elbow, skirt fold) with palette-coloured edges. A/B against the current outline on the idle and walk sheets.

### 4b. Guilty Gear / Dead Cells approach (for Swordswoman)
- **What these games do** [M]:
  - Dead Cells renders low-res 3D models without AA into sprites, with a toon ramp and hand-touched frames.
  - Guilty Gear Xrd uses hand-authored vertex normals, a lit/shadow threshold controlled per vertex, inverted-hull outlines, **stepped (on-twos/threes) keyframed poses with no interpolation**, and per-frame model deformation.
- **Why it's relevant:** our v1 Blender cleanup "lifeless" verdict likely came from interpolated mocap plus smooth shading. The Xrd recipe directly targets that.
- **1-day experiment:**
  1. In Blender, use the H2 rig with constant-interpolation keys at 8 fps (stepped).
  2. Apply a 2-band shader-to-RGB ramp, with an inverted-hull outline and no AA, rendered at 128 px.
  3. Palette-lock the result.
  4. Use it as a *guide* (not final). Compare Opus redraw quality over this guide vs the current H2 guide.

### 4c. VRoid Studio → VRM → Mixamo/mocap
- **What:** VRoid Studio (free, native on Mac) builds anime humanoids with editable hair strands, and has proportion sliders that reach chibi-ish ratios [M]. VRM brings a standard humanoid rig and spring bones. Blender's VRM add-on imports it.
- **Fit:** solves the "invented ponytail" class of problems by construction, because we *author* the bob, bangs and bun. It gives a clean, watertight, rigged mesh that retargets to Mixamo, CMU or LaFAN1 immediately. VRM spring bones replace our hand springs.
  - For Snowpeak it is an alternative to the failed r18–r20 Blender modelling: a parametric anime base instead of hand modelling.
- **Risk:** chibi head:body ratios fight VRoid's defaults. The bow and katana are separate props.
- **1-day experiment:** build Akane in VRoid (bob, bangs, bun, red short kimono texture from the turnaround). Export the VRM, retarget a LaFAN1 walk in Blender, and render the SE guide. Compare it as a guide against H2.

### 4d. 2D cutout or Spine rigs drawn in pixel
- Spine and DragonBones mesh-deform rasterize badly at 96 px (rotated pixels) [M]. The pixel-safe variant uses **swap-only parts**: a library of pre-drawn pixel parts (arm at 8 angles, skirt at 4 states) placed at integer offsets. This is what `v2/anim_cut` approximated at 48 px.
- **Verdict:** low priority for Swordswoman, already superseded. Plausible for Snowpeak's editor (override layer plus part swaps).

## 5. Automated pixel critics and metrics

At the moment Opus and Argon judge, which is slow and noisy. Deterministic metrics to add to `v2/qc` and Snowpeak QA:

| Area | Metrics |
|---|---|
| Pixel-art quality | orphan-pixel count, L-corner/doubles count, banding detector, cluster-size histogram, colour count per region |
| Model consistency | palette-index IoU per region against the master; silhouette IoU against the rig-guide mask |
| Animation | (a) **temporal stability**: % of pixels changing between frames outside the motion mask, a flicker measure; (b) arc smoothness of tracked keypoints (head-stamp centroid, bow, sword tip) via second-difference energy; (c) a timing histogram against `ANIM_DIRECTION.md` |

Prior art: `pixeldetector` (MIT) for grid detection; `alexkorol/pixel-respecter` and `UnlimitedEditing/ComfyUI-SpriteSheetPack` for grid-aligning diffusion output [V]. None is a quality critic. We would build ours (about 300 lines of numpy).

**1-day experiment:** implement the flicker and arc metrics. Back-test on `animate96` (scored 3–5) vs the `v2/motion` walk (Opus 7). If the ranking agrees with Opus, use them as a cheap pre-filter before LLM critics. Every generative experiment above needs this anyway.

---

## 6. Ranked top-5 recommendation

1. **Deterministic motion metrics (§5).** One day, no cost, no new dependencies. It is a prerequisite for judging 2–5 fairly, and it cuts critic cost.
2. **Retro Diffusion animation from our masters (§1a).** About $10 of credits plus domain-allowlist approval. Fastest test of "can a pixel-native model give us *motion* we lack". Use its output as motion keys for Opus redraw, not as final frames. Try PixelLab (§1b) the same week for Snowpeak.
3. **Character LoRA on the masters via mflux on Mac (§2).** The only local, permanent fix for identity drift (failure 2). It turns every future pose into "LoRA + guide → E2 pixelize" instead of a full Opus redraw.
4. **Wan2.2-Animate pose-driven video → pixelize (§3b).** Highest liveliness ceiling. The Mac port is immature, so timebox it to one day and accept a one-off cloud run to measure the ceiling. ToonCrafter (§3a) is the cheaper fallback for interpolating between existing keys.
5. **Stepped Guilty-Gear-style guides, plus normal-buffer interior lines (§4a/4b).** Cheap Blender and raycaster changes:
   - for Swordswoman, they make the rig guides livelier, so the redraw inherits better poses
   - for Snowpeak, they add interior form lines without hand pixels

   VRoid (§4c) is the alternative if the H2 rig keeps limiting poses.

**Not recommended:** palette-indexed diffusion research, a Spine mesh-deform rig at 96 px, more single-view image-to-3D.

**Approvals needed:** `mcp.retrodiffusion.ai`, `pixellab.ai`, and any cloud GPU or Kling endpoint must be added to `~/.claude/apple/dangerous_allowed_domains.csv` with user confirmation. `huggingface.co` and `github.com` already work for the mflux and Wan downloads.
