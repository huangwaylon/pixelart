# Walk SE under the DESIGN LOCK (pipeline, 2026-10-30)

This is a lean, deterministic build of one clip, walk SE, made to `../DESIGN_LOCK.md`. Everything new lives in `pipe/`. The round-10 assets in
`REVIEW/exp/2026-10-28_sw_skinned/` (rig r13, M's motion scripts, the face and line prototypes, `gifio`/`gifcheck`, `lamet`, `pxeval`) are imported or read and never edited.

```
pipe/build_walk_se.sh          # whole build, ~35 s, exit 1 if a blocking gate fails
-> pipe/out/walk_SE/f00..f07.png (+ .txt key grids), walk_SE_4x.gif, walk_SE_strip1x.png, gates.json, compare/
```
Python: `.models/pixtools/venv`. Blender 5.2: `/Applications/Blender.app/Contents/MacOS/Blender`. Two builds in a row give pixel-identical passes and frames: render dither is off, and every tie-break is sorted.

## What each step does
| step | file | what |
|---|---|---|
| 1a rig | `make_rig_lock.py` (Blender, on a COPY of rig r13 -> `rig_lock.blend`) | Bones, weights and skeleton are unchanged; only rest vertices and attributes change. **Sleeves:** sleeve vertices are pulled radially toward the arm axis by a profile of 1.0 at the shoulder, 0.82 at the elbow and 0.58 at the cuff, and the cuff past the wrist is pulled back. The bell becomes a slim tube and the hand reads outside it. **Waist:** dress/obi vertices in the obi band (z .785–.872) come in by up to 7 %, giving an inward step at the obi. **Face flat skin:** the r13 illustration head labels the drawn eyes, mouth and blush as *hair*. 2,912 head faces inside the S face-feature mask (`rig/tex/face_mask_S.png`, eye-dome row and below plus the brow windows) are reset to skin. **Bow:** a voxel majority vote, then the SE illustration colour where that projection saw the head (red = bow). This gives a solid bow and no red specks in the hair. **PARTID** attribute (leg.L/R, arm.L/R, torso, head). **Eye vertices** for step 4. |
| 1b springs | `bake_walk_lock.py` -> `walk_lock.json` | M's `mbuild.build('walk')` runs unchanged (body, head lag, timing, keys), with only the simulated chain list swapped. **10 spring bones**: bun, bow.L.1, bow.R.1, hair_back.2–3, hair_side.L.1, hair_side.R.1, skirt.F.1, skirt.B.1, sleeve.L.2. **Driven** bones are fixed fractions: bow .2 = 0.6×, side locks .2/.3 = 0.5/0.3×, skirt FL/FR/BL/BR = 0.5× F/B, skirt .2 = 0.4×. **Shared sleeve tip:** sleeve.R.2 = the X-mirror of sleeve.L.2 half a cycle later (the walk is L/R symmetric). Bangs, skirt L/R and hair_back.1 are static. |
| 1c passes | `render_lock.py` (lean copy of `render_motion.py`) | Same camera, cell, PPU, SE yaw −10 and head-yaw cheat. 8x passes: guide (matid), part, camera normal (16 bit), camera depth in metres (16 bit). Per-frame JSON with the eye surface points (deformed vertex: screen px, depth, facing), the motion keys and root motion. |
| 2 colour | `lock_chain.py` C | 14 lock keys. Each material has a fixed 2-tone ramp: hair `h/H` + one `L` sheen row, red `R/E`, bow `E/e`, obi `o/O`, skin `S/s`, socks `h/H`, boots `H/g`. The band comes from N·L (smoothed camera normal · the renderer's sun), with one threshold per material, the same in every frame. Face skin is always flat `s` and the neck `S`. Band hysteresis (±0.06) uses the previous frame moved part by part. |
| 3 lines | `lock_chain.py` B, D, F | **Outline:** the vector-line method (`proto_vecline` helpers). Trace the 8x alpha (eroded 4 px), smooth (σ 0.9 px), pin corners under 100°, Douglas-Peucker (0.8 px), redraw with uniform runs, pixel-perfect. Then `dezig` re-draws any span that still has a lamet 1-3-1 zigzag. **Temporal:** each polyline vertex snaps to the previous frame's line of the same body part, moved by that part's best integer shift, within 0.75 px. The loop is run twice so f00 sees f07. **Interior K only at the listed overlaps** (leg\|leg, arm/hand over body, hand\|sleeve, bangs\|face, bow\|hair, chin\|neck). They are drawn on the far side by camera depth, need a depth step over 2 cm except for the same-hull pairs, and are 1 px, pixel-perfect and ≥ 4 px long. Bangs\|face goes on the hair side so the face keeps its width. Lines never thin a limb below 2 px: they move to the body side instead. **Cleanup only removes K:** 2×2 clumps and redundant L-corners, never when that would add a zigzag or open a gap. Then `polish` makes local 1-px outline edits around any remaining defect, kept only if the lamet defect score drops (limbs may not get thin). |
| 4 face | `lock_chain.py` E, `calib_face.py` -> `face_calib.json` | facesys b′. The SE eye surface points come from `surfanchor.calib` (near eye; far eye = mirror), and the renderer re-finds them every frame on the deformed mesh. Templates (`facesys.eye`, 5 px near / 4 px far) are placed at point + master offset. An eye is hidden if a nearer surface covers the point (depth) or it faces away. Ink is clipped to face skin, and an eye under 60 % visible is dropped whole. Brows on hair are `K`. The SE far eye has 2-frame hysteresis. Expression = the motion keys through `proto.EXMAP` (7 expressions). Walk is `smile`, so `open` in all 8 frames. Eye whites can't be holes: the face is filled skin and `W` is stamped ink. |
| limbs | `lock_chain.py` | P's rules on the label grid: specks under 6 cells take the neighbour label; a 2-px guarantee (grow a 2×2 into torso cells); a 1–2 px crumb in a pocket of the line joins the outline. |
| 5 gates | `gates.py` -> `gates.json` | See below. |
| 6 compare | `compare.py` -> `out/walk_SE/compare/` | Round 10 vs lock (1x strip, 4x board, side-by-side GIF). Gold f00/f02: `pxeval still --ref`, plus a per-pixel diff with the candidate override pixels. |

## Gates (`out/walk_SE/gates.json`): all PASS
| gate (blocking) | result | limit |
|---|---|---|
| zigzags (lamet `zig`) per frame | 0 0 0 0 0 0 0 0 | ≤ 1 |
| redundant L-corners (lamet `dbl`) | 0 0 0 0 0 0 1 0 | ≤ 2 |
| outline gaps / 2×2 K clumps | 0 / 0 every frame | 0 / 0 |
| interior K only at listed overlaps | 0 stray K, no piece < 4 px | 0 |
| colours per frame / off-lock / cross-material | 11–12 (`EHKLORSWeghs`) / 0 / 0 px | ≤ 14 / 0 / 0 |
| limb audit (VANISHED SPLIT THIN DETACHED) | 0 failing frames | 0 |
| posture (`mgate.py`) | torso +3.0..+3.6°, head 0..+4.2°, head ahead of neck +3.0..+4.3 cm: PASS | PASS |
| GIF | loop 0, 70/120/120/110 ms ×2, gifcheck no flags | loop, ≥ 20 ms |

Notes on the gate definitions:
- Line metrics are measured with the eye/brow glyphs masked to skin. The `open` template's pupil block is a 2×2 K by design, and the lock fixes the glyphs. Unmasked lamet gives zig 0, dbl 0.125, and the same clump result outside the eyes.
- In the limb audit, "visible in 3D" is measured inside the drawn line (alpha eroded by 4 + 8 hi-res px), because the lock outline sits *on* the silhouette edge. P's chain drew its outline outside an eroded fill.

**Report only** (pxeval seq on f00–f07):
- boil .0275, shade_swap .0107 (the old gate was .015; round 10 had .061 mean, .082 on walk SE), flicker .205.
- Temporal line pops (outline px with no line within 1 px in the previous and the next frame after part-wise motion): 8 2 26 15 4 1 19 25 = 100. Without the vertex hysteresis it is 112. These pops are on the fast parts (swinging legs and arms).

**Round 10 → lock** (walk SE, lamet, 8 frames, unmasked):

| metric | round 10 | lock |
|---|---|---|
| zigzags | 6.6 | 0 |
| L-corners | 7.1 | 0.1 |
| clean-run share (mono) | .44 | .79 |
| interior K px | 42 | 11 |
| colours/frame | 16.1 | 11.6 |
| silhouette boil | .265 | .242 |

Interior boil (lamet) went up, .26 → .67. The interior K is now few, deliberate pieces (leg\|leg appears only while the legs overlap, plus the eyes), so each change is a large fraction.

## Gold comparison (`compare/gold_board_f00.png`, `gold_board_f02.png`, `gold_diff_fNN.json`)
`../gold/walk_SE_contact.png` → f00 and `walk_SE_passing.png` → f02. Both are needs-review; they arrived during this build.

| | f00 vs contact | f02 vs passing |
|---|---|---|
| pxeval vs_ref ssim / ssim_b / sil IoU / same_px | .19 / .28 / .63 / .26 | .20 / .23 / .56 / .20 |
| size delta (h / w / feet) | −3 / −10 / −3 px | −5 / −6 / −4 px |
| figure px (build / gold) | 1608 / 2376 | 1604 / 2347 |
| differing px (best ±6 alignment) | 1761 | 1850 |
| by reason (silhouette / fill / outline / interior / face) | 866 / 467 / 207 / 181 / 40 | 961 / 502 / 146 / 175 / 65 |

**These are not sparse override pixels.** About half the differences are silhouette, spread over head, body and legs. The gold is drawn to the master's proportions and turn, and the 3D render is not. The per-pixel lists in `gold_diff_fNN.json` (`candidate_overrides`: x, y, gold key, reason) amount to a redraw. The structural differences to fix in the pipeline before any override layer are:
1. **Turn.** The gold is the master's near-frontal 3/4, with both shoulders, the collar V and the obi across the front. The build is a true 45° SE with a −10° yaw cheat, so it reads half-profile and about 6–10 px narrower. This needs a stronger SE body yaw cheat (≈ −25…−30°, as NE already uses), set per view in align.json.
2. **Head.** The gold head is wider, with a bigger face and a visible neck and chin\|neck. The build's bangs come lower, and the face is narrower in SE. The far eye sits higher in 3D: the ortho camera's 30° elevation lifts it by about 4 px, where the gold uses the facesys layout row.
3. **Kimono.** The gold has a collar V, a wide front obi band, and a skirt that is a flared rectangle. The build has the r13 dress with a dark fold band from the far shoulder to the obi.
4. **Legs/boots.** The gold has shorter legs and larger boots with heel-strike and toe-off shapes. The build has the 3D leg length and small boots.
5. **Colour choices agree:** socks `H/h`, boots `g/H`, red `E/R`, hair `H/h/L`. One difference: the build draws the bow as `e/E`, the gold as `E/R`.
6. **Bow/bun.** The gold has a big upright bow with a pointed teardrop loop. The build has a smaller bow from the illustration projection.

## Files
- **Scripts:** `make_rig_lock.py`, `bake_walk_lock.py`, `render_lock.py`, `lock_chain.py`, `export.py`, `gates.py`, `compare.py`, `calib_face.py`, `build_walk_se.sh`.
- **Generated data:** `rig_lock.blend`, `walk_lock.json`, `face_calib.json`, `work/walk_SE/` (8x passes plus the frame JSON), `out/walk_SE/`.
- **Tuning knobs:** `LOCK_SIG`, `LOCK_EPS`, `LOCK_PIN`, `LOCK_SNAP`, `LOCK_SHRINK` (env). The constants at the top of `lock_chain.py` are RAMP, NSIG, HAIR_L, DSTEP and HYS. The defaults are the locked build.
