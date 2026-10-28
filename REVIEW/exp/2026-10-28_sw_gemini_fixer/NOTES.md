# 2026-10-28 swordswoman: Gemini pixel art + Retro Diffusion pixel-art-fixer

Owner: generative-pixel engineer. Budget: one day. Everything lives in this folder. Nothing outside it was modified.

## Question
1. Can pixel-art-fixer's grid recovery plus our palette lock rescue the Gemini "pixel art" we already have?
2. With new Gemini generations, can we get on-model 96 px sprites and **key poses**? Three routes:
   - (a) SE illustration → Gemini "true pixel art"
   - (b) illustration + m96 master + rig pose guide → Gemini pixel-art pose
   - (c) illustration + rig pose guide → Gemini **HD illustration** of the pose → E2 pixelize. This is the untried "key-pose illustration → E2" idea.

## Verdict (short)
- **The fixer is a reliable grid tool, with one blind spot.** It recovers Gemini's grid exactly when its fast path agrees (8.00, 5.12 or 10.24 px). On **15 of 26** baseline images it fell back to arbitration. There it usually mis-detects **step_x** by 2–12 % while step_y is right. Testing a square grid and keeping the lowest round-trip error fixes it: round-trip error drops from 7–10 to about 2 on true 8 px grids (`fixlib.fix_sq`). The square grid won on 14 of 26 baseline images and on 7 of 12 new ones.
- **Gemini never draws at the requested size.** We asked for "~96 art px, 8×8 blocks". The recovered figures came out at 82–347 art px on 3–14 px grids. The 1024² outputs mostly do use an exact 8 px grid, with the figure 94–112 px tall.
- **Grid recovery plus palette lock does not rescue the old outputs.** They are the old design (blue eyes, black obi, katana): ssim_b .13–.26, palL1 vs master .65–.90. The fixer can't fix identity.
- **(a) gives the best scripted fidelity of anything so far, but the critics prefer the master.** a1b, after fixer, ×0.38 downscale and lock, scores ssim_b **.93** and dE **10.7** against the illustration. The master scores .81 / 16.4 against the same illustration (.92 / 11.1 against its own warped geometry source). Both critics still pick the master (BEST=master), mainly for the face at 1x:
  - Opus: master 7/6/7, a1b 7/5/6
  - Argon: master 6/6/7, a1b 5/3/3
  - Worth porting by hand: red sock tops, the crossed collar, the visible bun.
- **Key poses: both routes hold the design but drift in proportion.** Neither is usable after only light cleanup. Opus means are **(b) 4.75, (c) 5.0**. Argon gives (b) 4–6 and (c) 4–6. The critics split: Argon says BETTER_ROW=b (cleaner clusters), Opus says BETTER_ROW=c (errors are local, and results are controllable and deterministic). Numbers:
  - **Head size at rig scale** (hair bbox / master 35 px): (b) **1.01 ± 0.22** (0.71–1.40), (c) **1.17 ± 0.10** (1.03–1.29). (c) is consistently about 15 % big-headed, so it can be corrected with one scale factor. (b) swings both ways.
  - **(b) reliability:** 2 of 8 (b) generations came back as 3-figure sheets in a different chibi style. All 8 (c) illustrations were on-model.
  - **Pixel noise:** orphans are (b) 0.6 % and (c) 1.2–1.3 %. The polished master is 0.5 %.
- **Recommendation:** adopt **(c) key-pose illustration → E2** as the key-pose source, with three changes:
  1. Scale each key by head size, not by figure bbox (`s2_headnorm.py hn`), or ask Gemini for the master's head ratio.
  2. Add a post-pass that caps dark clusters and cleans stray outline pixels (Opus's fix for the eye blobs and hair noise).
  3. Run the m96 face/head stamp on top.

  Keep the fixer only as a grid tool for any pixel-native generator output (Retro Diffusion or PixelLab, if they are approved), always through `fix_sq`. Do not use Gemini as the pixel artist (route b).

## Environment and tools
- Fixer: `.models/pixel-art-fixer/venv/bin/python -I` (numpy, scipy, cv2, PIL). This venv runs the fixer, `pz.py`/`pzlib` (E2) and all of the board and identity scripts.
- Metrics: `swordswoman/v2/pixelize/tools/metrics.py`, run with `.models/pixtools/venv/bin/python` (the PixelOE venv is being retired). Step 1 was first run on the PixelOE venv, then re-run on pixtools. The code is the same and the numbers match.
- Gemini: `swordswoman/.venv/bin/python tools/gemini.py image|ask` (gemini-3-pro-image / gemini-4-argon).
- Note: `gemini.py image` writes `<out>_1.png`. In 15 of 20 jobs it was a byte-identical duplicate, and the other 5 differed by under 0.08 mean RGB. It is not a second sample, so it was deleted. Each job = 1 sample.

## Scripts (`scripts/`)
| script | what |
|---|---|
| `fixlib.py` | `fix_sq` (fixer detect, plus a square-grid check by round-trip error), `bgmask` (border-connected background, keeps enclosed figure regions), `to_h` (native → h px: nearest within 12 %, else k-centroid ×8), `lock` (E2 `pz.finish` + orphan clean), `lock2` (adds obi recovery and per-material lightness match to the master). CLI: `fixlib.py IN STEM [--view] [--h] [--step SX SY] [--nosquare]`. |
| `s1_baseline.py`, `s1_gridcheck.py`, `s1_metrics.sh`, `s1_boards.py` | step 1 on 26 existing Gemini images |
| `s2_refs.py`, `s2_guideh.py` | Gemini references (guides cropped onto grey, master ×8) and guide figure heights |
| `s2_gen.py` | all Gemini prompts (also dumped to `work/gen/prompts.json`) |
| `s2_process.py` | (a)/(b) fixer → 96 → lock / lock2; (c) `pz.py EC0 SE 96 --src` |
| `s2_headnorm.py hn|gh` | pose scale: `hn` = h solved so the head-hair bbox = master (35 px); `gh` = h = rig guide figure height |
| `s3_identity.py` | pose-independent identity/pixel metrics vs master (palette histogram L1, material L1, hair bbox, bow/eye counts, orphans) |
| `s3_metrics.sh`, `s3_summary.py`, `s3_boards.py`, `s3_crit.sh`, `s3_crit_opus.sh` | metrics, consistency summary, boards, critics |
| `dbg_seg.py`, `dbg_obi.py`, `boardlib.py` | debug and board helpers |

Bugs found and fixed along the way (relevant to anyone reusing this):
1. **Mid-grey background vs grey-lavender obi.** The first `bgmask` (distance from bg colour plus small-hole fill) dropped the whole obi as background (iou_obi .05). The fixed `bgmask` keeps enclosed regions unless they match the bg colour almost exactly, which gives iou_obi .86–.95. **Ask Gemini for a white or chroma background, not grey**, for this character.
2. **Sprite sheets.** `bgmask` keeps only the largest figure group.
3. **Anisotropic grid threshold.** Square candidates are tested whenever |sx − sy|/sy > 0.2 %. At 1 % the near-square misses were skipped (c48s_se: 15.7 → 7.6 once fixed).
4. **Pose scale.** Scaling every pose bbox to 96 px inflates heads by up to 54 % (throw), because tucked or crouched poses are shorter than 96. Boards use `hn` (head-matched) or `gh` (rig scale), never bbox-96.

## Step 1: baseline on existing Gemini pixel art (26 images)
Sources: `v2/pixel/gem` (11), `archive/v2/pixel_E/work/master_k` (4), `v2/pixelize/D` (7, method D of the bake-off, current design), `v2/pixel/anim/walk_SE` (2), `v2/anim_redraw/work/walk_SE/cand` (2).
Table: `work/base/summary.md`. Per-image: `work/base/<name>_{fix,nat,r96,r96L2,info}`. Grid check: `work/base/gridcheck.json`.

Grid and size findings:
- 11 of 26 resolved without arbitration (9 fast-path, 2 three-detector consensus); the fast-path grids were exact (8.00, 5.12, 5.69, 10.24 px).
- Arbitration (15 of 26) usually got step_x wrong. The square check won on 14 images. Examples of round-trip error before → after: g48s_a 10.5 → 3.6, pixE_mk_v2 7.3 → 2.0, anim_redraw walk 7.8 → 1.8.
- Native figure heights: 82–99 px for the old "48 px" 8–10 px-grid images. The pixelize/D images, requested at 64/80/96, came out **303–347 px tall on a 3–4.7 px grid**, except gem_S_96 (87 px on 14.1 px). So for the 96 px target the scale factor to 96 ranges from **0.28 to 1.17**.
- Fidelity after the 96 px lock, against the current illustration:
  - Old-design Gemini sprites: ssim_b .13–.26, dE 38–52, palL1 .65–.90. Off-model. The fixer can't help.
  - Method-D current-design images: ssim_b .62–.81, dE 16–33, about the same as the master's .81 / 16.4.
- Board: `boards/b1_baseline_key.png` (6 key cases) and `boards/b1_baseline_all.png` (all 26). Each row shows raw | fixer native | lock native | 96 lock 3x | 1x.

## Step 2: new Gemini generations
Prompts: see `scripts/s2_gen.py` or `work/gen/prompts.json`. Shared design string: "chibi swordswoman girl: big red ribbon bow at the back-top of the head with a small hair bun under it, dark brown bob haircut with bangs and side locks, big brown anime eyes, red short kimono dress with wide hanging sleeves and V collar, grey-lavender obi sash, black thigh-high socks, brown boots".
- **a1 / a1b** (refs: illustration). "...Convert it into a TRUE PIXEL ART game sprite: the whole figure about 96 art pixels tall..., every art pixel drawn as one uniform square block of 8x8 image pixels on one perfect grid, hard pixel edges, no anti-aliasing..., limited palette of about 16 colours, a 1-pixel dark outline..., flat cel shading... same 3/4 view facing front-right... Plain flat mid-grey (#808080) background."
- **a2 / a2b** (refs: illustration + master ×8). Same as a1, plus "Image 2 is our approved pixel-art master... matching image 2's pixel scale, palette, outline and head-to-body proportions, but with the face and design of image 1."
- **b_<pose>_<k>** (refs: illustration, master ×8, guide). "Image 1... is the authority for her identity... Image 2 is our approved pixel-art master... Image 3 is a rough 3D POSE GUIDE: use it ONLY for the body pose... Draw the character... <pose>, in exactly the pose of image 3, as a TRUE PIXEL ART game sprite... Same pixel scale, palette, outline, head size and proportions as image 2..."
- **c_<pose>_<k>** (refs: illustration, guide). "...Redraw the character of image 1 <pose>, in exactly the pose of image 2, as a clean high-resolution anime character illustration in exactly the same art style as image 1: same line weight, same cel shading, same colours, same face and eyes, same head-to-body proportions, same 3/4 front-right camera... plain pure white background, no pixel art..."
- Poses, using the SE rig H frames (`v2/hy3d/frames_H/*_SE/s96`, H2 frames are not rendered yet; H2 rest is in `work/refs/guide_rest.png`): walk f00 contact, run f02 air, jump f04 apex, throw f03 release. Guide heights at the 96 px scale: walk 101.8, run 92.3, jump 87.0, throw 80.5 px.

Fixer results on the new images (`work/proc/proc.json`):
| job | input | detected step | picked | rt-err | native fig h | → 96 |
|---|---|---|---|---|---|---|
| a1 | 752x1424 | 9.17 x 9.13 (fast) | detected | 3.3 | 142 | k-centroid ×0.68 |
| a1b | 752x1424 | 5.09 x 5.08 (arb) | square_x | 7.2 → 6.4 | 253 | ×0.38 |
| a2 | 1024² | 8.44 x 8.00 (arb) | square 8.0 | 10.7 → 1.9 | 112 | ×0.86 |
| a2b | 1024² | 8.44 x 8.00 (arb) | square 8.0 | 7.2 → 2.0 | 106 | nearest ×0.91 |
| b (8 jobs) | 6 × 1024², 2 × 1408x768 | 8.0 (5 arb → square), 5.87 for the 2 sheet outputs | | ~1.8–2.2 | 94–111 | |

## Step 3: evaluation
### (a) SE: `boards/b2_SE.png`
Columns: illustration | master 4x | 1x | then for each of a1, a1b, a2, a2b: raw | lock2 4x | 1x.
| sprite (vs iso_SE_fixed) | ssim_b | dE | sil | iou_obi | line_f | face_ssim | palL1 vs master | orph |
|---|---|---|---|---|---|---|---|---|
| master EC0_SE_96 | .806 | 16.4 | .90 | .52 | .83 | .46 | 0 | 10 |
| (master vs its own geo src) | .917 | 11.1 | .97 | .82 | .83 | .61 | | |
| a1 | .914 | 11.6 | .96 | .86 | .96 | .73 | .29 | 15 |
| **a1b** | **.928** | **10.7** | .98 | .95 | .88 | .78 | .26 | 7 |
| a2 | .735 | 18.2 | .90 | .39 | .93 | .40 | .26 | 5 |
| a2b | .851 | 14.2 | .93 | .59 | .93 | .63 | .26 | 10 |

Showing Gemini the master (a2/a2b) **hurt** fidelity: the head turns toward profile and the expression turns sullen. lock2 (per-material lightness match) is about the same as lock: ssim_b +.005, palL1 −.02.

Critiques (`crit/argon_SE.txt`, `crit/opus_SE.txt`; both reviewed `crit/b2_SE_as_critiqued.png`, which matches the final board except a1b, re-processed after the threshold fix 3):
- **Argon:** master 6/6/7 (identity/pixel/face 1x); a1 5/4/3, a1b 5/3/3, a2 6/4/4, a2b 6/5/4. Problems: muddy eye blobs with no sclera, stray dark outline pixels on the sleeve edges, aliasing from the 254 → 96 downscale. BEST=master.
- **Opus:** master 7/6/7; a1 6/5/5, **a1b 7/5/6**, a2 5/4.5/4, a2b 5.5/5/4.5. Problems: a dark seam staircase down the left torso and skirt, white orphans at the jaw and ear, bang hiding the second eye, a black band on the front shin. Worth porting onto the master: red sock tops, the crossed V collar, the visible bun, the bigger boots. BEST=master.

### Key poses: `boards/b3_poses_hn.png` (all samples) and `boards/b4_consistency_hn.png` (chosen keys)
- b3 shows, per pose: guide | b_0 raw | b_0 lock 4x | b_1 raw | b_1 4x | c_0 raw | c_0 E2 4x | c_1 raw | c_1 4x.
- b4 shows master + chosen keys, 4x and 1x:
  - (b): walk_0, run_1, jump_1, throw_1
  - (c): walk_0, run_1, jump_0, throw_1
- `*_gh` variants are the same at rig scale.

Consistency numbers (`work/summary.md`, `work/summary.json`):
| set | head ratio at rig scale (mean ± sd [min..max]) | palL1 vs master | orph % |
|---|---|---|---|
| (b) chosen | 1.07 ± 0.22 [0.86..1.40] | .27 ± .06 | 0.67 |
| (b) all 6 on-model | 1.01 ± 0.22 [0.71..1.40] | .27 ± .05 | 0.58 |
| (c) chosen | 1.14 ± 0.08 [1.06..1.26] | .35 ± .03 | 1.33 |
| (c) all 8 | 1.17 ± 0.10 [1.03..1.29] | .37 ± .04 | 1.19 |

The hair-bbox head measure is noisy by ±3 px. b_throw_0 measured 25, so its `hn` solve went to h124, which is a measurement artefact.
- (b): 2 of 8 raw outputs (walk_1, jump_0) were 3-figure sheets in a different, flat-bob chibi style. With those excluded, the palette and material usage is closest to the master (lowest palL1), because Gemini copied the master's colours.
- (c): every illustration was on-model, with good pose adherence (jump, throw). E2 keeps the master's hair cluster style. Fidelity of each pixelization to its own illustration: ssim_b .96–.98, face_ssim .73–.88 (`work/proc/metrics.txt`, rows EC0_c_*).

Critiques (`crit/argon_poses.txt`, `crit/opus_poses.txt`):
- **Argon** (BETTER_ROW=b): b walk 5, run 5, jump 4, throw 6; c walk 4, run 4, jump 5, throw 6. Its reasoning: (b) has contiguous clean blocks, while (c) has muddy face clusters and ragged hair. (Argon also wrongly claimed b_throw_1 = c_throw_1 on the board; the md5s differ.)
- **Opus** (BETTER_ROW=c): b 6/5/4/4 (mean 4.75), c 4/6/5/5 (mean 5.0). Its reasoning: (b)'s errors are structural (the hairstyle, eye style and proportions change per pose), while (c)'s are local (an eye blob on walk, stray outline pixels, the back arm). c_run_1 is the best match of all 8 poses. Its fix for (c): a post-pass that caps dark clusters and cleans stray outline pixels.

## Recommendation
1. Use **(c) illustration keys → E2** for animation keys:
   - Gemini illustrations stay on-model in pose, and E2 is deterministic and matches the master's style.
   - Correct the about +15 % head size with head-matched scaling (`s2_headnorm.py hn`), then stamp the m96 head (`v2/m96/heads`) as the existing pipeline does.
   - Add a dark-cluster/outline cleanup pass, and gate on orphans ≤ 0.7 % (master is 0.5 %).
   - Next test: render the rig **H2** frames (`v2/g96/scripts/frames_H2.py`) and run a full 6-frame walk this way, then measure boiling between adjacent keys.
2. Do **not** use Gemini as the pixel artist (b): it varies too much from sample to sample (sheets, style flips, head 0.7–1.4×).
3. Keep **pixel-art-fixer** with the `fix_sq` square check as the grid tool for any pixel-native generator output. Don't trust its arbitrated step_x on narrow figures.
4. Hand-port these (a1b) details onto the SE master if the art lead agrees: red sock tops, crossed collar, visible bun.
5. For Gemini on this character: use a white or chroma background (grey collides with the obi), one sample per call (`_1` is a duplicate), and don't pass the pixel master as a reference for a front view (it makes the face worse).
