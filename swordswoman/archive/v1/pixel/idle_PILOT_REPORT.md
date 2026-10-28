# Idle pilot report: hand-cleaned 8-direction idle

Date: 2026-10-24. Scope: `idle`, 8 directions x 8 frames, 128 px cells, pivot (64,104). The base is a snapshot of the latest model render round (`pixel/base/idle`). The deliverable is `pixel/clean/idle` (base + `pixel/overrides/idle`).

**Final state:** `px.py apply` wrote 64 frames, and there are no stale overrides. `gif.py` produced 43 GIFs for both clean and base. The clean round-6 set had **no judge pass**. The best result was Gemini at 8.4 in round 4. The human-style judges (art director and game director) peaked at 6.4-6.5, against a ship bar of 8. Treat this set as a strong mid-tier placeholder, not a ship asset.

## Final artefacts
- Clean frames: `pixel/clean/idle/<DIR>/f00..f07.png`
- GIFs: `pixel/gifs/idle_clean/`. This holds per-direction 1x/4x GIFs on grey and on grass, `all8_4x_*.gif`, `before_after_*_4x.gif` and `before_after_all8_2x.gif`. Base GIFs are in `pixel/gifs/idle_base/`.
- Before/after (base row on top, clean row below, f00, 8 directions, 4x): `pixel/judge/idle_final/before_after_f00_4x.png`
- Clean contact sheets (rows S, SE, E, NE, N, NW, W, SW; columns f00-f07): `pixel/judge/idle_final/contact_clean_1x.png` and `contact_clean_3x.png`
- Per-round judge packs: `pixel/judge/idle_r1` .. `idle_r6` (each has contact_1x/4x, before_after_4x and the 8-direction GIF)
- Lint: `pixel/lint/idle_clean.json`

## Round history

| Round | Gemini | Art director | Game director | QA pass (dirs) | Main change / main complaint |
|---|---|---|---|---|---|
| 1 | 6.2 | 4.5 | 4.5 | 2/6 checked (NW, SW) | Only E/f00 was cleaned in E, so E f01-f07 popped ~620 px per loop. Idle was a 2-pose toggle. Hook formed a ring. Snowman back hair. Plank ribbons. |
| 2 | 7.6 | 6.0 | 5.5 | 6/8 | All frames cleaned; faces, bow and blade fixed. Back views read as soft-serve stacked hair, ribbons as planks or arms, sawtooth hems. Purple specks. Mechanical bob. |
| 3 | 7.6 | 6.0 | 6.5 | 6/8 | Hair and red tone budgets fixed. Hard gates failed: 44 outline gaps, 308 orphans. Static head boiled across frames (W 243 px). Bob phase differed per direction. |
| 4 | **8.4 (pass)** | 6.2 | 6.4 | 7/8 | Lint mostly clean, faces solid. Ribbons, hems and hilt still looked like render leftovers. Bob unsynced. In W the bow slid on the bun. Back views were a "brown ball over a red bell". |
| 5 | 7.6 | 6.3 | 6.4 | 6/7 | Pink rim read as a second outline. Feet were boxes. SW hilt read as a pole through the thigh. NE/NW sword floated. Phase still unsynced. |
| 6 | 7.6 | 6.4 | 6.5 | 8/8 | All lint hard gates 0 (off-palette, semi-alpha, outline gap, double, flicker, y/cx drift). Remaining: rigid ribbons in W/SW/NW/NE, back-view skin patches and ear spikes, W missing fist/hilt, idle acting nearly zero, phase unsynced, 8 vs 6 frames. |

Per-direction scores, round 6 (Gemini / art director / game director):
- S: 8.2 / 7.0 / 7.0
- SE: 7.8 / 6.8 / 6.5
- E: 7.5 / 6.3 / 5.5
- NE: 7.4 / 5.8 / 6.0
- N: 7.4 / 6.2 / 6.5
- NW: 7.5 / 6.0 / 6.0
- W: 7.6 / 5.7 / 6.5
- SW: 8.0 / 6.8 / 6.5

The trajectory went up fast in rounds 1 to 2 and then plateaued in rounds 3 to 6. The internal QA score went up (6/8 to 8/8 passing), but the external judges barely moved (art director 6.0 to 6.4). Fixing more pixels did not fix the remaining problems. They are about structure: acting, phase sync, ribbon and hilt shapes, the frame count and hair value. Those come from the model and animation, not from cleanup.

## Hand edits per direction (final override pixels, summed over f00-f07)

| Dir | Override px | Per frame | f00 override px / f00 opaque px |
|---|---|---|---|
| S | 4,741 | 550-629 | 550 / 1142 (48 %) |
| SE | 7,030 | 866-903 | 866 / 1180 (73 %) |
| E | 5,502 | 640-726 | 640 / 1027 (62 %) |
| NE | 5,256 | 616-706 | 620 / 1102 (56 %) |
| N | 5,638 | 674-732 | 674 / 1177 (57 %) |
| NW | 6,031 | 708-802 | 718 / 1093 (66 %) |
| W | 5,008 | 566-667 | 566 / 999 (57 %) |
| SW | 5,588 | 625-746 | 625 / 1104 (57 %) |
| **Total** | **44,794** | ~700 | |

The override counts include `clear` edits, so the ratio is an approximation. `HISTORY.jsonl` has 60,199 logged operations: 59,159 set, 1,004 revert and 35 erase.

**Key fact:** about half to three quarters of every frame was repainted by hand. At this ratio the "sparse override" model is really a full repaint stored as a diff. That is too expensive to repeat for the roughly 6 remaining animations x 8 directions x 6-10 frames, about 400 frames.

## Final lint (clean)
- Zero in all 8 directions: off-palette, semi-alpha, outline_gap, double, flicker, y_drift, cx_drift.
- Totals across directions:
  - orphan: 274 (S 57, SE 64, SW 64, E 32, NW 25, W 24, NE 8, N 0)
  - notch: 167 (SW 47)
  - spur: 174
  - jaggy: 50 (S 29, W 15)
  - banding: 170
  - inner_break: 8 (SE)
- Colours per frame: 18-21, all inside the locked palette.
- base_y per direction: NE/NW 105, S/E/N/W 106, SE/SW 107. This is still a 2 px hop when the character turns.
- Frame-to-frame changed pixels (f→f+1, wrapping):
  - S: 22, 234, 71, 0, 26, 229, 80, 0
  - SE: 0, 256, 277, 5, 0, 283, 270, 12
  - E: 15, 8, 4, 305, 14, 8, 322, 4
  - NE: 0, 192, 182, 5, 9, 194, 196, 5
  - N: 9, 155, 199, 9, 0, 167, 189, 11
  - NW: 0, 310, 49, 15, 0, 311, 15, 49
  - W: 56, 266, 85, 14, 71, 255, 79, 14
  - SW: 0, 191, 116, 18, 0, 196, 115, 18

  The motion is still mostly a 1 px body translate, with the main transition at a different frame index in each direction. E pops at f03→f04 and f06→f07, while most other directions pop at f01→f02 and f05→f06.

## Lessons learned: rules to encode before walk, run, jump, sword combo, dash and hurt

### A. Fix upstream, not in pixels (biggest lesson)
1. **Lock the frame count to `docs/anim_spec.json` before cleanup.** Idle shipped 8 frames against a spec of 6 at 150 ms, and every game-director round flagged it. Make the snapshot refuse when the frame count differs from the spec, or get the spec changed first.
2. **Sync the phase across all 8 directions in the rig or animation, not by hand.** Every round failed on "bob dips at f03 in S, f04 in E, f02 in W". Rule: the key poses (contact, down, up, impact) must fall on the same frame index in all directions. Check this with a per-direction "body-top row per frame" table before cleanup starts.
3. **Lock the ground baseline per animation across directions.** The lowest foot row varies from 105 to 107. Fix it in the camera or pivot, or apply one global vertical offset per direction, not per-pixel edits.
4. **Acting is a model or animation problem.** Hip weight, ribbon and skirt follow-through, and sword-hand settle (R51) cannot be painted into 64 frames economically. For walk, run and combo, secondary motion must exist in the render (cloth or ribbon bones with 1-2 frame lag). Otherwise every frame repeats the "frozen sprite that twitches" verdict.
5. **Hair value: decide in the bible before painting.** Five rounds swung between "dark helmet" and "milk-chocolate". Encode one tone budget for the hair: h0 ≥ 35 %, h1 ≤ 55 %, h2 used only as a single crescent sheen. Then lint it.
6. **Secondary shapes need model fixes.** Planks or sticks for ribbons, a pole for the SW hilt, and a hidden fist in W were all repainted every round, and the shapes reappear in every frame. Fix the ribbon taper and S-curve and the hilt length in the model.

### B. Cleanup craft rules that proved out (keep and encode)
7. **Build one key frame per direction (f00), then propagate it.** Static cels (head, face, bow, bun) must be byte-identical across frames at whole-pixel offsets (§7.16). Round 3 failed because the head boiled (W 243 px). Use `px.py copy` plus an offset, and do not redraw per frame.
8. **Clean every frame of a direction before judging.** Round 1 E was rejected because f01-f07 were raw. A partial direction is worse than no cleanup, because the loop then pops.
9. **Pink rim light ≤ 60 % of the contour, with breaks (R7).** A continuous pink_0 rim reads as a second outline.
10. **Katana in every direction:** a 2 px blade, a hook of at least 3 px with a transparent gap inside the crescent (no closed ring), a visible d1 fist, 2 px of hilt past the fist with an r2 wrap diamond, and a t1 kashira (R21-R23). It must angle 25-35° clear of the silhouette. The blade tip must not go below pivot +2 (W/SW went 7 px below).
11. **Back views:** the bun overlaps the skull on a curve (no stepped tiers, R32) and is pushed to the camera-far side so the facing reads. Include a crescent sheen (R31). Do not use square skin patches or ear spikes past the hair outline.
12. **Feet are strappy heels:** heel point, 1 px skin ankle, # sole. No d1 boxes (R41).
13. **Hems are petals, not sawteeth:** no 1 px teeth or icicles; step sizes vary smoothly (R16, R42).
14. **No purple_0 or violet speckle outside its whitelisted use.** Merge coral r3 blotches into fold wedges (R14, R15, R43).
15. **Facing tells:** NE/NW need a 1-2 px cheek or bang edge. SW needs a real 3/4 head turn so it does not read as S. E/W need more than one eye pixel.
16. **Terrain check:** review every round at 1x on grass, sand, slate, dark (#24202c) and crimson. Red-on-red sel-out disappears on crimson ground, so keep a continuous dark outline on the outer dress edge.

### C. Process lessons
17. **Gemini overrates.** It passed round 4 at 8.4 while the art director gave it 6.2. Use Gemini only for triage, and gate shipping on the director-style checklist and lint (guide §6).
18. **Internal QA drifted toward lint-passing.** QA reached 8/8 while the external judges stayed around 6.4. Add the acting, phase and spec checks (A1-A3) to the QA checklist so QA cannot pass a set the directors will reject.
19. **Budget:** about 5.6k override pixels per direction for an idle. Moving animations will cost more. Without fixes A1-A6 the remaining set is roughly 300k+ hand pixels.

## Cleanup rules: safe to automate vs must stay manual

### Safe to automate (deterministic, low risk, verify with lint)
- Snap colours to the nearest locked palette entry, and make alpha binary (no semi-alpha).
- Fix the frame count and timing against `anim_spec.json` (reject or resample before cleanup).
- Apply a per-direction vertical offset to lock base_y to a single value; lock cx drift.
- Propagate static cels: copy the key-frame head, bow, bun and face to the other frames at the detected whole-pixel body offset (`px.py copy` + shift). Diff-check after.
- Sync phase by re-indexing frames so each direction's dip frame lands on the same index, when the renders contain the same poses.
- Remove single-pixel orphans that are not on the R13 whitelist (eye glints, mouth). Erase 1 px exterior spurs, and fill 1 px exterior notches with the neighbour majority colour.
- Close outline gaps (kagi or diagonal gaps in the exterior outline) with `outline`.
- Remove one-frame blips: if a pixel differs from both neighbour frames while those two agree, set it to the neighbour value (the flicker detector already finds these).
- Purge purple_0 outside its whitelisted region (using the object-ID pass).
- Lint the tone budget (hair h0/h1/h2, red r0-r3, pink p0/p1) as warnings, not auto-fix.
- Break the rim-light run: if a contiguous pink_0 contour run is over 60 % of the edge, insert breaks at fixed intervals. Do a quick visual check after.

### Must stay manual (shape and readability judgement)
- Face decals (eye block, glint, blush, mouth), bang locks, and profile eye placement.
- Bow two-loop shape, bun overlap curve, back-view hair silhouette and sheen crescent.
- Katana hook crescent with interior gap, fist, hilt wrap diamond and kashira; blade angle clearance against the silhouette.
- Ribbon S-curve and taper (unless fixed in the model), hem petal shapes, fold wedges.
- Feet and heel construction, and SW 3/4 head turn and facing tells.
- Selective-outline decisions (where to use the dark outline versus a coloured sel-out) and the 1x terrain readability check.
- Any secondary motion or acting added in pixels: ribbon lag and sub-pixel in-betweens (R46/R51). Prefer fixing these in the rig.
- Final sign-off against the director checklist.
