# Snowpeak retrospective (AD + tech lead), 2026-10-28

Scope: the repo root pipeline (`pipeline/`, `data/`, `editor/`, `art/hand/`, `releases/`, `00_REVIEW/`, `docs/`). Swordswoman, `reference/` and `.models/` are covered by another reviewer. Sources: 136 commits (2026-10-22 to 10-24, plus one cleanup commit on 10-28), the round docs, the QA reports, and the boards and contact sheets, which I looked at myself.

## 1. Timeline

| Round | Tried | Outcome (verdict / user reaction) | Kept / dropped |
|---|---|---|---|
| r0-r2 | Ellipsoid chibi on a skeleton, iso raycaster, banded toon, 64x64 jump, 8 rendered facings | Camera 26.6° → 18° (unanimous). AD r2: "REQUEST CHANGES (minor)": hat 50% of head, E/W "pasted square" face seam, braids fusing | Kept the architecture; camera later 16° |
| r3 | Palette board; "3D as mannequin, pixels drawn" grounding proposal | Locked 32-colour master + colourways; `guide.json` + 3D-vs-pixel grounding sheet | Kept |
| r4-r5 | Proportions A-E, 6 outfits x 6 colourways, resolutions R1-R4 | Panel: body B, O1 charcoal, R2 48x48 | Superseded by r9 |
| r6 | H1 hero + v2 pixel rules (`pixelrules.py`) | GD "ACCEPT WITH NOTES" (26/44 overrides stale). Hand pixels 570 → 254 → 170 → 88-98 | Rules and stale gate kept |
| r7 | jump_v2 (14 f, cuter acting) | QA PASS | Acting style carried forward |
| r8 | User: "more Japanese-esque … CUTER and more FEMININE". C1-C6 | AD shortlisted 5 | Dropped |
| r9-r10 | Semi-chibi teal S1-S6. Outline study (5 styles). HD concept portraits | User picked **S4** (half-up + back bow). Closed outline with sel-out on dark, contrast floor | S4 + outline rule kept. Concept art dropped |
| r11 | 13-clip action set, props layer, carry bone, loop-seam QA | APPROVED by AD/anim/GD after 4 rounds → `releases/S4_actions_v1` | Kept (legacy) |
| r12 HD | SDF model `S4_hd` (`sdf.py`, `make_s4_hd.py`) | AD "ADOPT-WITH-FIXES", then 6 AD rounds → APPROVED → `releases/S4_hd_actions_v1` | **Kept: current base** |
| r12 illus. | Vector shapes → `illustrate.py` rasterizer | User: *"the illustrations look terrible"* | Dropped (module slated for deletion) |
| r13 | Hand-typed `.pix` grids (`pixgrid.py`): busts, 96x160 turnaround, heads, 8 poses | All APPROVED (busts 5 rounds, turnaround 6, poses 4) | **Kept: canon** |
| r14 | Engine features (hold_of, smears, per-key ease, budgets) + retimes of every clip | `*_r14` clips QA PASS | Kept, but not in the release |
| r15 | SE/SW far-eye spacing, longer bangs. Gemini mesh critique / mesh request | AD APPROVED (review 4) | Face rules kept. Gemini mesh dropped |
| r16 | Slimmer V-taper jaw, two-layer lifted bangs | User: *"face looks a bit too fat"*. Gemini r1: "not solved … barcode/comb". APPROVED in round 3 | Kept |
| r17 | Gemini Argon writes a from-scratch model | User: *"hideous"* | Dropped |
| r18 | Two isolated Blender modelers A/B (80k tris, rig, LODs) | AD: B as base, then "FIXES. User request partly met." | Tooling kept, model dropped |
| r19 | Bake Blender B into sprites (`blender_bake.py` → `blender_sprites.py`) | "No improvement for 48x64; keep S4_hd" (6-px stick figure, 7/8 brown-blob views) | Dropped |
| r20 | From-scratch Blender base: Track C (Claude, 23 rounds) and Track G (Gemini, 2 rounds) | AD C r1: "helmet hair, V-shield jaw, bow-tie bow, tube coat, stick legs". G stopped. "Direction change to refining S4_hd" | Dropped |
| r21 | `S4_hd2`: swept sheets and smooth unions replace bead chains (7 rounds) | Self-critique only. Idle/walk/run QA PASS, S4_hd byte-identical | Open (3 of 13 clips) |

## 2. What worked, and what didn't

### Worked (evidence)
- **3D mannequin → raycast pixel pass.** One rig, one sim and a screen-fixed key light give 8 facings that really are the same character. The release idle QA reads `standing_height_px` 34 in all 8 directions, `max_height_delta_px` 0, `foot_slide_px` 0.136, `chain_penetrations` 0. The contact sheet backs that up: there is no direction drift, and the bow, scarf side and ponytail stay consistent. No AI or hand pipeline in this repo matches it on consistency.
- **Locked palettes and banded shading.** Release frames use 15 colours, and QA reports zero off-palette pixels and zero orphans. It also makes colourway exploration (r4: 36 combos) nearly free.
- **Determinism and hashing.** A fixed 5 ms sim, 10 ms-multiple durations, `--verify` double render, and a SHA-256 build id over every input. That is why AD reviews could say "release matches `out/variants` byte-for-byte", and why r21 could prove S4_hd stayed byte-identical while S4_hd2 changed.
- **Overrides with reasons and a stale flag.** `pipeline.override --reason` is required, stale overrides fail `--release`, and the editor keeps `reasons`. Result: the S4_hd release carries only **3** override files (ponytail tips on run/jump_sc/carry_idle). The hand layer stayed small and auditable.
- **Encoding pixel rules (`pixelrules.py`, `face.py` rules).** Every recurring AD hand fix became a rule: back-view nape, profile eye clamp, boot ground rows, cuff close, 2-px nose bridge, hem pinned to the lash line, jaw taper. This is the single best idea in the project. It took hand pixels from 570 to 98 and makes fixes survive re-animation.
- **Hand-pixel r13.** Best-looking art in the repo: the turnaround and busts have real ドット絵 line hierarchy, clusters and appeal. It also became the canon every later model was judged against.
- **S4_hd (SDF).** Cleaner silhouettes (bang zigzag, scalloped hem, bow loops, boot soles) at the same 48x64 budget, it exports STL/OBJ, and it shipped all 13 clips.
- **QA metrics as review currency.** Jaggies, flicker scans, eye-pixels-hidden-by-hair, and loop seams made reviews concrete. Example: r19 was rejected on numbers (eye spacing 1.7 px vs 5.3) as well as on taste.
- **Editor plus reviewed boards.** `00_REVIEW/<round>/README` "open first" tables and synced comparison boards kept the user loop fast.

### Didn't work (root cause)
- **r12 vector illustrations.** Root cause: smooth vector fills rasterized without anti-aliasing read as flat "vector art at low res". There is no cluster design, and the eyes are generic. Honest note: the shapes (bow, coat) were clean. The method failed, not the design.
- **Gemini mesh (r15/r17).** An LLM writing SDF or mesh code blind produces noisy, broken surfaces. The v2 turnaround shows speckled coat shading, a helmet head and spiky hair. Gemini was useful as a *critic* (r16 "comb" catch) but not as a *modeler*.
- **Blender tracks r18-r20.** Root cause: the targets were wrong for the camera. A 6.5-head "production" model collapses at about 44 px. Scaling the head afterwards buries the body under hair. Even the pixel-aware Track C still shows a helmet head and a smeared, noisy coat in its sprite bake (`C_r23_sprite_px8_x6.png`). Three rounds and a large token budget went in, and the result was "keep S4_hd". The lesson: the sprite is designed at sprite size first, and a nicer close-up mesh does not survive quantization.
- **Release drift.** `releases/S4_hd_actions_v1` (`BUILD.json` git_base 23747fc) predates the r14 retimes, the r15/r16 face and bangs, and the r14 prop-depth fixes, which its own README lists as "fixed for v2". It was also built from an uncommitted working tree. The approved shippable is now 3 rounds behind the approved art.
- **Style gap.** The in-game sprite (about 3.4 heads, rendered) and the r13 canon (5.5 heads, drawn) are two different characters in proportion. The sprite is consistent, but it still reads as a "rendered chibi". My judgment from the boards:
  - The coat is a flat beige slab with lavender shadow patches.
  - Stray 1-2 px dark-teal islands (mitten or scarf bits) sit mid-coat in SE/SW.
  - Legs are 2-3 px dark stubs.
  - Hands are blobs.
  - E/W profiles lose most of the face behind side hair.

## 3. Best current pipeline (end to end)

Inputs: `data/variants/S4_hd.json` (authored by `pipeline/tools/make_s4_hd.py`), `data/animations/<clip>[_r14].json`, `data/palettes/cw_oatmeal` / `frost_r3_oatmeal`, `data/props/*.json`, `overrides/variants/S4_hd/<clip>/<DIR>/<n>.json`.

```bash
.venv/bin/python -m pipeline.tools.make_s4_hd                        # SDF model -> data/variants/S4_hd.json (S4_hd2: make_s4_hd2)
.venv/bin/python -m pipeline.build --variant S4_hd --anim run_r14 --verify          # builds/variants/<tag>_<hash>/, out/variants/S4_hd__run_r14/
.venv/bin/python -m pipeline.pixelreview --build out/variants/S4_hd__run_r14        # zoomed per-frame sheets + census.json
.venv/bin/python -m pipeline.override --variant S4_hd --anim run_r14 --dir W --frame 1 \
    --set x,y,<colour> --reason "..." --author AD [--preview]
.venv/bin/python -m pipeline.build --variant S4_hd --anim run_r14 --release         # fails on stale/unreviewed overrides
.venv/bin/python -m pipeline.publish --variant S4_hd --round rNN --clips idle walk run ...   # 00_REVIEW/rNN
pipeline/tools/gemini_critique.sh                                                    # optional second-opinion critique
```
Outputs per clip: `<clip>_sheet.png/.json` (48x64 cells, 8 rows; events, cancel windows, z_px, anchors, buildHash), shadow / fx_back / fx_front strips, prop_back / prop_front strips, 8-dir and slow-mo GIFs, a contact sheet, `qa_report.md`, `manifest.json`, `guide/guide.json`, and a 3D-vs-pixel grounding sheet. Portraits and cut-scenes come separately from `art/hand/S4/**/*.pix` through `pipeline/pixgrid.py`.

Weaknesses:
- **Bow in the S view is small** (1-2 px past the head in S4_hd2, r21 critique #1). Seating it at the ponytail root conflicts with front readability.
- **Fringe roots show as ridges** where the hard-unioned locks leave the dome (S4_hd2 #2). S4_hd's bead-chain crown also shows blob rows up close.
- **Thin-sheet noise.** Marching and tracing noise on hair and bow sheet edges, plus surface wobble in the exported mesh (#3).
- **Editor variant path bug.** `pipeline/server.py:66-67` `_out()` returns `out/variants/<variant>`, but `build.py:466` writes `out/variants/<variant>__<anim>` for every anim except `jump`. So the editor can only open variant **jump**, and override saves read `frameHashes` from the wrong (or missing) manifest, which records `base_hash: None`. The server also falls back to the classic `data/palette.json`.
- **Hash churn.** The build id hashes all pipeline and variant files, so any unrelated edit changes every hash. Compare pixels, not ids.
- **`publish.py` overwrites the round README** with only the clips in the latest call (r14_retime lists 4 of 13).
- **Two parallel clip sets** (`clip` and `clip_r14`) and a stale release. README.md and START_HERE.md still describe the H1/jump era.
- **CPU raycaster cost.** It is fine at 48x64, but hi-res reference renders are the slow path.

## 4. Lessons that transfer to other characters
1. **Design at target resolution first.** Every 3D upgrade that was judged in close-up (r18-r20) failed at 44 px. The swordswoman approach (illustration → pixelize → hand-polished masters) starts from a 2D target. Snowpeak should have adopted its r13 canon as a sprite-scale master earlier.
2. **Keep 3D for what it is good at:** placement, facing, overlap, arcs, secondary motion, depth for prop splits, and foot IK. Swordswoman's "rig-guided per-frame redraw" is the same insight applied the other way round: 3D or a rig as the guide, pixels as the art. Snowpeak's `guide.json` plus grounding sheet already provides that guide.
3. **Turn repeated hand fixes into rules** with a pixel-saved count. This carries over to any generator, including a pixelize step.
4. **Make the hand layer sparse, reasoned and stale-aware.** Swordswoman's hand polish would benefit from Snowpeak's override and `--release` gate.
5. **Determinism plus byte-identical checks** let reviewers trust "nothing else changed". Hash pixels, not the whole input set.
6. **LLM models make good critics and bad modelers.** Use Gemini or Claude to critique boards, not to author geometry blind.
7. **Cut releases from commits,** and re-cut them when approved art moves on.
8. **Put user taste quotes in each brief** (r13/r16/r17 did). Restarts happened when that taste diverged from what the team was optimising.

## 5. Open questions / untried ideas
- **Hybrid sprite master.** Hand-pixel one S4_hd frame per direction (idle f1) to the r13 cluster standard. Then use the generator only as the per-frame guide and diff. The override layer is effectively this, but scaled to about 30-80 px per frame. What override budget is acceptable per clip?
- **Per-direction part library** (proposed in r3 as "B parts + underlay", never built). Hand-drawn hair, bow and face per facing, placed by the rig, would fix the bow in S, the fringe ridges and the profile hair without any more SDF work.
- **Re-proportion the sprite toward the r13 canon** (about 4 heads at 48x80?) and re-test whether legs and coat stop reading as stubs. Nobody has tested this since r4/r5.
- **Coat shading:** drop the lavender band to a 2-tone with a single fold line, and add a rule against teal islands inside the coat silhouette.
- **S4_hd2:** finish the remaining 10 clips, or freeze it? The judgment between S4_hd2 and S4_hd at 1x has not been put to the user.
- **Re-cut `S4_hd_actions_v2`** from a commit with the r14 timings and r15/r16 faces, and retire the non-`_r14` clips.
- **Fix `server._out()`** to use the build's `vdir` logic (or read `builds/latest_*.json`), and add an editor test.
- **Palette-aware downsampling** (majority vote plus rules) applied to the r13 hi-res canon rather than to 3D renders. This is the swordswoman route; it is untried here.
- **Night-tile outline swap** (decided in r10) is not yet exercised in any shipped sheet.
