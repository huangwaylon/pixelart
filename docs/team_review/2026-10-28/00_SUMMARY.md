# Team review 2026-10-28: summary and recommendation

Panel:
- `01`: snowpeak art director and tech lead
- `02`: swordswoman art and animation director
- `03`: research lead
- `04`: repo architect (already carried out, see the end)

This page brings their findings together. The full reports are next to it.

## The short version
- **Both projects learned the same lesson.** Neither managed it from opposite ends.
  - Use 3D for placement, facing, proportions and motion.
  - Make the art in 2D at the target size, starting from an approved 2D design.
- **Snowpeak has the best *system*.**
  - It is deterministic.
  - It covers 8 directions and 13 clips.
  - It has QA metrics.
  - Its override layer requires a reason for every hand edit.
  - It has the editor.
  - Its art still reads as "rendered chibi".
- **Swordswoman has the best *look*.**
  - Its 96 px masters are the first output the user didn't reject outright.
  - It has no finished animation.

## What worked
| | Evidence |
|---|---|
| One 3D source feeds every direction (snowpeak mannequin, swordswoman rig H2) | Snowpeak idle measures 34 px tall in all 8 directions, with 0 height delta and 0 foot slide. Rig H2 is calibrated to the masters. |
| **Pixelizing a 2D illustration** (E2: k-centroid, then face pass, then palette lock) rather than 3D renders | ssim .96, face_ssim .86. The masters read as the same girl as the source art (`swordswoman/v2/m96/sheet.png`). |
| Target size chosen for the face (96 px figure for a big-eyed anime head) | Every 48 and 64 px swordswoman strand failed on fidelity. |
| Repeated hand fixes turned into generator rules (`pipeline/pixelrules.py`) | Hand pixels fell from 570 to 98 on H1. S4_hd ships with 3 override files. |
| Determinism, byte-identical checks, QC gates | They caught sock flicker, pivot drift and stale overrides. Reviewers can trust that nothing else changed. |
| Measured fidelity against the illustration, shown side by side | This was the only signal that predicted the user's verdict (see Critics). |
| LLMs as *critics* (not as modelers or pixel makers) | Gemini meshes and SDFs (r15/r17), Gemini 48 px redraws and the Blender tracks all failed when an LLM was the author. |

## What didn't
| Approach | Root cause |
|---|---|
| Cleaning up 3D renders into sprites (snowpeak r18–r20 Blender models, swordswoman v1 and hybrid) | The 3D model wasn't the design, and cleanup can't fix structure. Models were judged in close-up but fall apart at 44–48 px. |
| Gemini as pixel artist | It ignores the requested size and drifts off-model on every call, and chaining calls compounds the drift. |
| Single-view image-to-3D (Pixal3D, Hunyuan 2.1/2mini, TRELLIS) | It invents geometry (a ponytail), produces non-watertight noise, and gives dark textures. Only the 4-view Hunyuan3D-2mv run was usable. |
| Swordswoman animation (`animate96`, motion 3–5) | Four causes:<br>- The A-pose master "wins" over the guide, so the sleeves stay out like a T-pose.<br>- The head is a rigid stamp covering 40 % of the figure.<br>- Each frame is redrawn independently, so frames boil.<br>- It used old T-pose guides.<br>- No smears. |
| Trusting critic scores | Argon gave "ship" scores of 9–9.5 to masters the user rejected. The accepted m96 scored 7.2 (Argon) and 6 (Opus). Argon runs 1–3 points above Opus. The director panel came closest to the user. Several Opus critique files are empty shell errors. The "walk Opus 7" figure in `v2/motion` is actually Argon's score. |
| Process churn | Design decisions landed mid-flight and killed downstream work four times. Freeze the design before animating. |

## Best pipeline right now (recommended for both characters)
```
approved 2D design (illustration turnaround, or snowpeak r13 hand-pixel canon)
  → pixelize at a size that fits the face (E2, swordswoman/v2/pixelize)        ← deterministic, measurable
  → polished per-view masters + head stamps (swordswoman/v2/m96)               ← QC-gated
3D rig calibrated to the masters (H2 / snowpeak mannequin) → per-frame guides (+ springs)
  → key poses drawn first, then in-betweens redrawn *only where the guide moved*
  → smear frames authored for fast actions, FX layer, QC gate
  → snowpeak-style overrides (reason, stale check) + editor for the final pixel polish
  → GIF / sheet export with the engine metadata snowpeak already emits
```
Snowpeak's tooling (sheet and JSON export, override layer, editor, QA, `--release` gate) is the
backbone to keep. Swordswoman's front end (illustration, then pixelize, then masters) is the look to keep.

## Not yet tried (ranked; detail in 02 §5 and 03)
1. **Automated motion metrics** (flicker, arc smoothness, palette match against the masters). Back-test them on the pilot. Takes 1 day and costs nothing; it makes every later experiment judgeable.
2. **Animation-rest masters** (relaxed arms, sleeves down) as the base to draw from, plus **masked edit-mode in-betweens** that paste unchanged pixels back from the previous frame. These remove the T-pose and boiling problems by construction.
3. **Pixel-native generators for motion keys:** Retro Diffusion (swordswoman), PixelLab (snowpeak, 8-dir iso). About $10 per test. **Needs your approval** to allow `retrodiffusion.ai` and `pixellab.ai` through the proxy.
4. **A character LoRA trained on the approved masters** (mflux, local on the Mac). Every new pose becomes "LoRA + guide → E2" instead of a full Opus redraw. This fixes identity drift for good.
5. **Key-pose illustrations, then E2.** Gemini redraws the illustration into each key pose using the H2 render as reference, and the stage that already works converts it.
6. **Pose-driven video, then pixelize** (Wan2.2-Animate; ToonCrafter for in-betweens). This has the highest ceiling for liveliness, but the Mac ports are immature, so timebox it to one day.
7. **A user-calibrated critic.** A/B against the current best and the illustration, with past accept/reject pairs as anchors. Fail the run when a critique file is empty.
8. **Snowpeak only:**
   - a per-direction hand-drawn part library (bow, fringe, face) placed by the rig
   - re-proportioning toward the r13 canon
   - a 2-tone coat rule
   - normal-buffer interior lines

## Decisions for you
1. **Swordswoman action set.** The brief says **slash with katana**. The 96 px plan quietly switched to an unarmed **throw**, and nobody recorded approving that.
2. **Snowpeak S4_hd2.** Finish the other 10 clips and cut `S4_hd_actions_v2` with the r14 timings and r15/r16 faces, or freeze it?
3. **External pixel generators.** Allowing Retro Diffusion and PixelLab means adding them to `dangerous_allowed_domains.csv`.

## Known bugs to fix next
- `pipeline/server.py:_out()` returns `out/variants/<v>`, but builds write `out/variants/<v>__<clip>`. So the editor only opens `jump`, and override saves record `base_hash: None`.
- `pipeline/publish.py` overwrites the round README with only the clips from the latest call.
- Critique runs don't check for empty or errored output files.

## Repo reorganisation (04, carried out on branch `reorg-2026-10-28`)
See `archive/README.md` for the old path → new path table. No build-hash input was touched, and the build IDs are unchanged.
