# Swordswoman sprite project: retrospective (art + animation direction)

Date: 2026-10-28. Scope: everything in `pixelart/swordswoman/`. I read the notes, results, crit files and review docs, and looked at the key boards myself: the m96 sheet and stamps, the animate96 idle/walk boards, the motion r3 walk/dash boards, the pixelize board, the v1 idle before/after, the anim_redraw slash and the fx96 context.

**Bottom line.** The *look* is solved: Gemini illustration, then E2 pixelize at 96 px, then the m96 polish. The *animation* is not. The pilot shows why. Each frame is redrawn independently, anchored to an A-pose master and a rigid head stamp. That gives either boiling or frozen frames, and fixing one causes the other. Better guides alone won't fix it.

## 1. Timeline

| Strand | Approach | Best score (Argon / Opus / panel) | Verdict | Why it failed / what it contributed |
|---|---|---|---|---|
| `model/`, `renders/` | Hand-built 40-bone Blender rig from the concept art, point-sampled renders | Gemini model rounds only | Dead | The model never matched the concept. Renders had 1 px noise (no supersampling until lead note §6.4). |
| `pixel/` v1 idle | 3D render plus hand overrides, 8 directions | Gemini **8.4 "pass"**, AD 6.2–6.4 | User: "terrible" | 44,794 override px, with 48–73 % of each f00 repainted. Scores plateaued r3–r6: "fixing more pixels did not fix structure". |
| `hybrid/` S1–S7 | 6 strategies (Claude cels, Gemini grid, 3D textured, pixel-native…), 5-director panel | Best panel 6.5 (S5 r2); Gemini ≤ 6 | User: "terrible" → restart | Split: hand cels were clean but stiff; Gemini/3D had energy but mush and drift. Left behind `ANIM_DIRECTION.md` (timing, smear rules) and the gate idea. |
| `v2/design` C/D/E | Gemini turnarounds, simplified design, 3D renders as camera authority | r3I Argon 6–7 / Opus 5.5–6 | Superseded by Level E/hair | Gemini can't hold 30° elevation without a 3D render reference. Proportions were wrong ("fat and awkward"). |
| `v2/style`, `prop` | Pokémon trainer study, measured template, blockouts | A' 7 / 6.5; blockouts "MATCH" | Kept as data | The real cause of "fat": shoulders and waist at 0.95 of head width, legs 21–23 %. |
| `v2/hy3d`, `parts`, `rigcal`, `g96` | Hunyuan3D-2mv 4-view mesh → A+B parts hybrid → rigs E…H2 calibrated to the masters | Parts 8/8/9/8 vs 7/7/8/7; H2 residuals S2 SE4 E2 | **Kept (guides)** | A consistent, re-proportionable 3D guide. TRELLIS, PartCrafter, Pixal3D single-view and Hunyuan 2.1 all failed. |
| `mocap`, `pose`, `unarmed`, `throw` | CMU/Bandai/LaFAN keys + arm layers, camera-first posing | Unarmed Argon ~8/7/7; pose h2 Argon 7.5–8.5 vs Opus 4–7; throw Opus 5–6 | Kept (pose tables) | Real timing and key poses. The **slash/katana got dropped** here (rigcal: "slash dropped"; throw replaced it). |
| `v2/anim` | Toy rig guides, 88 GIFs at 48 px | Argon **8.5–9 "READY"**, Opus 5–7 | Never shipped | 3D shimmer, mush legs. |
| `v2/pixel`, `pixel_E`, `anim_redraw` | Gemini 48 px redraw over guides + head stamp + procedural smear | 4.5–6 / 4–6 | Dead | Off-model per call, legs mush, katana pops. Lessons kept: never chain frames, stamp identity, procedural smears. Its slash (`anim_redraw/sheets/slash_SE.png`) is still the best-reading smear in the project. |
| `v2/anim_cut` | 48 px cutout + `ff_redraw.py` Opus harness | r7b Opus 5.5–7; r10 5–6.5 / 4–5 | Superseded | The harness (`ff_redraw`, `lint_style`) survives. |
| `v2/masters`, `mastersF`, `final` (64 px) | Opus-drawn 64 px masters | masters Argon **9–9.5 / Opus 8–8.5 "ship"**; mastersF 8.5 / 6.5; final 6.5 / 5.5 | **User rejected** | "Doesn't represent the source art." 64 px can't hold this face, and hand edits bloated the side view by 18–35 %. |
| `face`, `face2`, `heads` | Face kit and head stamps | face2 Argon 8.5–9 / Opus 7–8 | Folded into m96 | Expression grammar and anchors. |
| `v2/hair` | Gemini turnE_final, legs (a), centred bow | User picks | **Source of truth** | The illustrations everything now derives from. |
| `v2/pixelize` | 6 conversion methods × 3 sizes, scripted metrics | E2@96: Argon 7 / Opus 7.5→6.5 | **WIN** | The face killer was palette snapping, not only size. The face pass fixes it. Gemini ignores the requested size (draws 170–330 px). |
| `v2/m96` | E2 output → geometry warp → Opus region jobs → spec eyes → QC | Argon 6.8→7.5→7.2 / Opus 6; face rounds Argon 8–8.5 / Opus 6–7 | **M96 READY**; user gave detail notes | The first base the user critiqued *in detail* (nose, brows, eye shape) instead of rejecting outright. |
| `fx96`, `qc` | 15 effects at 96 px; `qc_gate.py` | Lint-clean, READY | Kept | Infrastructure. |
| `animate96` pilot | ff_redraw over frames_H, head-lock, gates | idle motion 5/5, walk motion **3/3**; no-boiling 4 | Gate PASS, quality fail | See §2. |
| `motion` r1–r3 | Blender springs (hair, hem, ribbons), Williams/PMD keys | r2 Argon 6–7 / Opus 5–6; r3 walk Argon 7 | Mid round 3 | Scores are for **3D guide previews**, not pixels. The README's "walk Opus 7" is mislabelled: `crit/r3_walk_opus.txt` is a 70-byte zsh `zle` error, and the 7 is Argon's. |
| `heads96` | Layered heads (base/face/locks/bow/tails), Opus art jobs | n/a | In flight | `layers/*/approved/` is **empty** in all 5 views. Batch 2 of the rerun was never logged as done. |

## 2. What worked, what didn't, and root causes

**What worked (with evidence)**
- **Pixelize from the illustration, not from 3D.** k-centroid gave the best fidelity at every size (ssim_b .96, dE 9.0). The face pass raised face_ssim to .86 and halved orphans. Looking at `m96/sheet.png`, the five 96 px views read as the same girl as the illustrations, which nothing before managed.
- **Measuring, not guessing.** The "fat" verdict was traced to widths (style/prop study) and to hand-edit bloat (pixelize step 7). The eye/face rounds were gated on face_ssim and never fell below v13.
- **Deterministic infrastructure.** The QC gate caught real regressions: sock flicker, double-K soles, pivot drift. Head re-paste restored 0 px in every frame, so the artists respected the head lock. The pool ran 9 parallel jobs on 3 accounts with 0 errors.
- **3D as a hidden guide only.** The calibrated H2 rig plus mocap give consistent proportions across views. The motion strand's spring secondary motion visibly improves on frames_H (`motion/prev/r3/*/crit.png`).

**What didn't, and the root causes**
1. **Starting from a model that wasn't the design** (v1, hybrid S4, v2/anim). Cleanup can't fix structure. The v1 idle plateau proves it: QA went from 6/8 to 8/8 while the AD score went only from 6.0 to 6.4.
2. **The target size was too small for the face.** The BRIEF said 48 px. The design has a big-eyed anime head, which needs about 96 px. Every 48/64 px strand (pixel, anim_redraw, masters, mastersF, final) failed against the user's real criterion, fidelity to the source art.
3. **Gemini can't make pixels.** It ignores the requested size, drifts off-model on every call, and chaining compounds the drift. It is good at illustrations and turnarounds when given a 3D render as a camera reference.
4. **Animation is lifeless. The pilot boards show the structural causes:**
   - *The master is an A-pose turnaround.* `RULES96.txt` says "where guide and master disagree … the MASTER wins" and "start from the master's body pixels". So the bell sleeves stay out like a T-pose in every walk frame (`animate96/crit/walk_SE_board.png`).
   - *The head is about 40 % of the figure, and it is a rigid stamp.* The largest mass cannot tilt, squash or lag. Layered heads (heads96) were meant to fix this, but none are approved yet.
   - *Independent per-frame redraws boil.* The cure ("rebuild f01–f05 from f00") left the idle frames almost identical (`idle_SE_board.png`), so motion and no-boiling are traded against each other. There is no shared pixel-space representation of the parts, so every frame re-invents them.
   - *The pilot ran on the old frames_H guides* (T-pose mocap arms, asymmetric stride, 2 px foot slide), not on the motion strand's or H2's guides. Neither `hy3d/frames_M` nor `hy3d/frames_H2` exists yet.
   - *Smears are missing.* fx96 only has overlays (speed lines, dust). The motion strand's "smear" frame is just a pose, and there is no 96 px smear authoring step. The user named smears as a priority twice.
5. **Process churn.** Design decisions kept arriving mid-flight (proportions, legs, centred bow, faces), and each one killed downstream work: animate killed at 16/38 frames, m96 restarted, final stopped, g96 recalibrated. Nothing downstream was safe until the design was frozen.
6. **Scope drift.** The brief's actions are idle, walk, run, jump, dash and **slash**. The 96 px pipeline plans idle, walk, run, jump, dash, hurt and **throw**, unarmed. Nobody recorded the user approving the swap.

## 3. Critic reliability

| Case | Argon | Opus | Panel | User |
|---|---|---|---|---|
| v1 idle | 8.4 pass | n/a | 6.2–6.5 | terrible |
| hybrid r1/r2 | ≤ 6 | n/a | ≤ 6.6, no pass | terrible |
| v2/anim r4 | 8.5–9 READY | 5–7 | n/a | not accepted |
| masters 64 px | 9–9.5 ship | 8–8.5 ship | n/a | rejected ("fat", "not the source art") |
| mastersF | 8.5 ship | 6.5 | n/a | rejected |
| m96 | 7.2 | 6 | n/a | **accepted** (detail notes only) |

- **High scores did not predict acceptance.** The one base the user accepted scored lower than three the user rejected. The critics judged each sprite on its own. The user judges it against the illustration.
- **Measured fidelity was the best predictor.** Metrics against the illustration (ssim_b, face_ssim, dE, silhouette) plus side-by-side illustration | sprite sheets lined up with the user.
- **Argon inflates.** It typically scores 1–3 points above Opus, gives "READY/ship" freely, and sometimes misreads (Opus's "outline not black" claim, `style/`, was false too).
- **Opus is more conservative and catches structure** ("legs never swap", walk motion 3), but it also passed the 64 px masters at 8–8.5.
- **The director panel was closest to the user.** It never passed anything, and it was right not to.
- **The scores are noisy.** The same face scored 7.8 or 6.5 depending on prompt framing.
- **Tooling corrupts the data.** Opus calls via `zsh -ic` sometimes return only `zle` errors (pose h2, motion r3), and nothing checks that a critique file is non-empty. Opus scoring downscaled thumbnails invents defects (pose h2).
- **Motion scores in `motion/` rate the 3D preview, not the pixels.** They must not be read as sprite quality.

## 4. Best current pipeline and its gaps

Python is `/Users/waylonhuang/Documents/other/pixelart/swordswoman/.venv/bin/python`, run from `swordswoman/`.

1. **Illustrations.** `v2/hair/turnE_final/{front,…,iso_N}.png` (FINAL SET v2, centred bow).
2. **Pixelize.** `v2/pixelize/make_top.sh top1` → `v2/pixelize/top1/EC0_<V>_96.{txt,png,json}`, palette `v2/pixelize/palette.json` (18 colours).
3. **Masters.** In `v2/m96/tools`: `geom.py V geo` → Opus region polish (`runjob.sh`, `accept.py`) → `faceround.sh snap/v11_preface2/masters` → `stamp.py heads masters heads` → `finish.sh`.
   - Outputs: `v2/m96/masters/EC0_<V>_96.*` and `v2/m96/heads/<V>_<expr>.txt` (45 stamps).
   - Gates: `v2/qc/qc_gate.py masters` and `qc_gate.py stamps v2/m96/heads`.
4. **Rig.** `v2/hy3d/rigs/H2` (RIG H2 READY, PPU 52.608 in the 192 cell).
5. **Guides.**
   - `motion/scripts/frames_M.py final ACT VIEW` → `v2/hy3d/frames_M/<act>_<dir>/s96` (H2 is picked automatically, with springs and a per-frame `head` block).
   - Fallback: `g96/scripts/frames_H2.py` → `hy3d/frames_H2`.
   - **Neither has been run.**
6. **Heads.** `v2/heads96/tools/compose_head.py`, fed by `layers/<V>/approved/`. **Empty, so this is a gap.**
7. **Draw.** `zsh v2/animate96/tools/fanout.sh prep1|draw1|post1|prep2|draw2|post2 <guides>`. It wraps:
   - `ff_redraw.py prep … --head-lock --qc gate,eye --lint-rel --rules v2/animate96/RULES96.txt`
   - `run96.py` (pool of 9)
   - `post96.py clean|out|qc`
   - Then `critboard.py` and `fix96.py`.
8. **FX.** `v2/fx96/tools/build.py 3`; post96 places dust_step automatically.

**Gaps:**
- No slash guide, katana sprite or smear stage at 96 px.
- No animation-pose master.
- No temporal-consistency mechanism other than "rebuild from f00".
- heads96 is unfinished.
- The DX/PX pivot table must be re-derived from the H2 guides.
- Critique files aren't validated.

**Shortest path to 6 action GIFs** (SE first, then E; about 80 frames; pilot rate about 50 s wall per frame at 9 jobs, so roughly 2–3 h including one fix round):
1. **Ask the user one question:** slash with katana, or throw unarmed? Confirm SE+E first and the 8 directions later.
2. **Draw one animation-rest body per view, once.** Relaxed arms, sleeves down, contrapposto. Gate it with `qc_gate.py`, then set it as `--master` for drawing. Keep EC0 as the turnaround reference.
3. **Render guides:** `frames_M.py final idle,walk,run,jump,dash SE,E`. For slash, add key tables to `motion/work/act_M.json` from `poses_mocap.json` slash (or the pose strand's), with the katana prop on.
4. **Finish heads96 batch 2.** Promote with `accept.py`. If it slips, ship v1 with stamps and use heads96 only for tilt/squash keys.
5. **Draw keys first** (contact/pass, antic/burst/skid, coil/smear/impact). Draw in-betweens in **edit mode**:
   - The artist gets the previous frame's char map.
   - A mask of the regions the guide moved (matid diff) limits what may change.
   - post96 pastes unmasked pixels back from the previous frame, which removes boiling by construction.
6. **Smears.** One authored smear frame each for dash burst, jump launch and slash: port `v2/anim/smear.py` (crescent, w/n/m bands, taper) to the 96 palette and add fx96 speed lines and afterimage.
7. **Review.** `post96 out` → `qc_gate clip` → one `fix96` round → put the GIFs on `v2/REVIEW/index.html` next to the illustration and get the user's verdict. Critics are triage only.

## 5. Untried ideas within this project

1. **Animation-pose masters** (above). This targets the T-pose root cause directly.
2. **Masked edit-mode redraws with automatic paste-back** of static regions. The rule exists in RULES96 but is not enforced.
3. **A pixel-space cutout puppet at 96 px.** Cut the m96 masters into parts (heads96 labels already exist for heads), place them per guide with RotSprite-style rotation, and have Opus fix only the joints and silhouette. The 48 px cutout failed on off-model masters, not on the method.
4. **Key-pose illustrations, then E2.** Gemini redraws the turnE illustration into each key pose using the H2 render as a reference (the r3iso trick). Then the *winning, deterministic* E2 converts it, with a head-stamp lock. This reuses the stage that worked instead of asking for pixels.
5. **Hold-heavy PMD timing with fewer drawings.** Walk = 4 drawings with legs swapped near/far and torso pixels copied. Reach for this before adding frames.
6. **80 px figure** (the bake-off runner-up). 1.4× fewer pixels per frame, if the cost blocks the fan-out.
7. **A user-calibrated critic.** Give critics the user's past accept/reject pairs as few-shot anchors. Make A/B comparison against the current best and the illustration the default, not absolute scores. Fail the run when a critique file is empty or has no score.
8. **Image-to-video from the illustration** (no strand tried it), pixelized by E2 per frame with the head lock. Useful as a motion reference for idle and hair even if the frames aren't used directly.
