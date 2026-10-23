# r15 - SE/SW far eye + longer bangs (S4_hd)

Feedback:
1. The SE far eye (her left eye, on the right of the screen) still looked weird and too close.
2. The bangs should be longer, especially at the sides, so she doesn't look bald.

Write-up with the art-director discussion: [docs/review/r15_face_bangs.md](../../docs/review/r15_face_bangs.md).

## Files
- **[options_x10.png](options_x10.png)**: five pixel-edit mockups (A-E) next to the old SE face (O0).
  - Rows: idle f1 and walk f2 at 10x, then the same frames at 1x and 2x.
  - The last column is the real r15 build.
  - **B was chosen** and is now generated in every frame.
- **[before_after_faces.png](before_after_faces.png)**: S, SE, E, SW and N at 8x, for idle f1, run f3 and jump_sc f7. Before is the v1 release.
- **[bangs_hires_before_after.png](bangs_hires_before_after.png)**: smooth hi-res render of the HD model (reference parts on).
- **idle / walk 8-dir GIFs**: `*_8dir_before.gif` (v1) and `*_8dir_after.gif` (r15).
- **se_sw_all_clips_a/b.png**: head crops of every SE and SW frame in all 13 clips (r15).

## What changed
- **3/4 face** (new `data/faces/kawaii_hd.json`, used by S4_hd only):
  - The far eye is 2x3, the same height as the near eye.
  - It has a 1 px catchlight on the light side.
  - There is a 2 px nose bridge and at least 2 px of far cheek.
  - The mouth sits under the bridge.
  - The near side of the face is 1 px wider, so the eye pair fits without squeezing.
  - SW, NE and NW use the mirrored cels.
- **Bangs** (`pipeline/tools/make_s4_hd.py`):
  - Every bang is longer, and the outer ones are longest.
  - New temple bangs slope down into the side locks.
  - The tips are fuller, so the extra length shows at sprite size.
  - The centre bang stays shortest, keeping the hime notch.
  - If a bang tip dips onto the eye line during a head bob, the bang is cut short there and the lash is kept.
- **Profile (E/W)**: the eye is 1 row lower, matching the S/SE eye line. This keeps it clear of the longer bangs.

## Status
- (round 1) 13 clips + 5 r14 copies rebuilt; see Round 2 below for the current build.
- Overrides:
  - Three ponytail-tip overrides were re-approved. Their pixels are unchanged.
  - The carry_idle NW temple override was dropped because the temple bangs now produce that edge.
- Legacy S4_halfup_bow is byte-identical: the idle, walk and throw sheets were compared.
- `releases/` is untouched.
- Nothing is committed.

## Round 2 (AD fixes 1-5 + anim fix)
Rule: `render.face_eyes.hem_pin` (`pipeline/face.py` `_face_hem` / `_skin_pockets`). It works per frame, with no hand edits.
- **Anim / AD2 (flicker):** the bang hem is now drawn from the lash line, with exactly 1 skin row over the lashes in S/SE/SW, so the head bob no longer opens and closes the gap.
  - Gap per face column in run S, frames 1-8:
    - round 1: `1211..` / `1100..` / `1111..` / `0110..` (flips every frame)
    - round 2: `0011111111100` in every frame
  - walk, carry_walk and the r14 copies are steady too.
  - See **[run_flicker_strip.png](run_flicker_strip.png)** and **[run_flicker_S_SE.gif](run_flicker_S_SE.gif)**.
- **AD1:** lone hair pixels inside the face (3+ skin/eye neighbours) are cut. SE/SW count over walk, run, carry_walk, throw and jump: 34 to 0.
- **AD2/AD3 slope:** in S the outermost face column on each side hangs to the lash row. In SE/SW the 2 far-temple columns and the outermost near column hang to the row above the lash. The forehead in throw f0-f3 is down to 1 row: determined frames pin to their lowered lid, and blinks keep the open-eye line.
- **AD4:** closed-eye arches always keep 1 px of skin above them.
- **AD5:** the 1-px skin pockets above the E/W eye are filled. Run went from 8 to 0, and all clips are now 0.
- AD conditions kept: the far catchlight stays on the near eye's side and appears only on the 2x3 open eye (determined, squint and joyful have none).
- **[before_after_round2.png](before_after_round2.png)**: round 1 vs round 2 for S, SE, E, SW and W in idle, run, throw, jump and walk.
- The other boards and GIFs in this folder have been regenerated from the round 2 build.
- Rebuilt: 13 base clips and all 14 `*_r14` copies. QA: 27/27 PASS with no warnings. Legacy S4_halfup_bow is byte-identical: idle, walk and throw were compared.

## Round 3 (AD review 2: two rule-level fixes)
- **Closed and squint eyes keep skin on their open side.** This covers every view, including profile, for any cel without a catchlight (squint, joyful, determined, blink).
  - Each '.' cell inside an eye's ink box is skin. If hair covers it, the hair is replaced with skin.
  - The face pass marks these pixels as designed, so despeckle can't merge them back into the hair.
  - Fixes S jump_sc f10 (27-28, 37), where hair had filled the `<`.
- **3/4 temple edge.** On the 2 rows above the lash line, skin pixels just past the face edge are now hair, part of the hem-pin rule.
  - The 1-px far-contour notch is gone in SE walk f1/f5/f6, run f4, jump_sc f2 and throw f1, and in the SW mirrors.
  - That notch count across SE/SW in walk, run, jump_sc, throw, carry_walk and idle went from 10 to 0. Two hits remain in idle f6, but that's the blink frame, where the check reads the wrong lash row.
- **[round3_fixes.png](round3_fixes.png):** round 2 vs round 3 crops at 8x.
- The SE/SW contact sheets and the 8-dir GIFs are regenerated.
- 185 px changed in total across the 27 sheets.
- Rebuilt the 13 base clips and the 14 `*_r14` copies: QA 27/27 PASS, no warnings. Legacy idle, walk and throw are byte-identical.

## Round 4 (AD review 3: SW regression)
- **SW temple edge:** the hem rule now converts **skin only**, never an outline pixel. A pixel it places on the silhouette edge is drawn in the plum hair-outline colour, never mid-hair.
  - Every listed pixel is back to the round 2 plum: walk f1/f2/f5, run f8, throw f1/f4 and jump_sc f2/f9.
  - The same fix also turned about 40 older round-2 mid-hair silhouette pixels on the SW temple into plum.
  - 5 dark-outline pixels became plum, where the temple is now hair: throw SW f4 (16,33) and pick_up_r14 SW f10 (16,33-35).
  - The jump_sc SW f2 notch, the mirror of the SE fix, is now closed.
- **N / back views:** `last_stamped` is reset on every face call. A back view used to inherit the previous frame's stamped pixels, and the frames.py restore then rewrote those pixels (N idle f2-f6, carry_walk f3, jump_sc f12). NE/N/NW are now pixel-identical to round 2.
- **[round4_sw.png](round4_sw.png):** round 3 vs round 4 crops at 8x.
- Rebuilt all 27 clips: QA PASS, no warnings. Legacy idle, walk and throw are byte-identical.
