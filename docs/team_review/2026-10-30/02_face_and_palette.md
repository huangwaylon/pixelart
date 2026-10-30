# 02 — Eyes+brows-only face and a locked palette (2026-10-30)

Owner: *"Can we simplify things. For the face, nothing but eyes/eyebrows. No nose, no mouth, no extra blush. Keep the colours consistent."*
All files are in `docs/team_review/2026-10-30/face_palette/`. Scripts are in `face_palette/scripts/` (pixtools venv, read-only on the repo). The build audited is `20261030_66119a7` (round 10).

## TL;DR
- **Face system:** 4 colours on top of skin `s`: `K` (lash, pupil, closed line), `g` (iris lower half), `W` (one catchlight, always on the iris's screen-left column) and `h` (brow). There are 7 expressions, made only from eye shape and brow angle, in 5 px wide (front) or 4 px wide (far/profile) templates. Sheets: `expr_sheet_1x.png`, `expr_sheet_6x.png`, `expr_face_zoom10x.png`.
- **Placement: recommend (b'): exact pixel templates positioned by a surface point tracked on the 3D head.** Not the current `face.*` empties, which sit inside the head and drift 1.3–3.8 px in E/W. Option (a), a flat texture on the head, works in S/SE but loses the eye in profile and breaks blinks.
- **Palette:** every frame is on-palette, but each frame uses 10–18 keys (mean 14.9). Five near-identical darks (`K h D d H`) cause **78 % of all shade swaps** (build mean shade_swap .061 vs gate .015, 0/48 clips pass). Proposal: a **locked 14-colour palette** (drop `D d m k`) with fixed band rules. The pure remap alone cuts shade_swap by 35–41 % and colours per frame from 16 to 12.

## 1. Face system (eyes + brows only)

**Template grid.** 5 cols x 8 rows per eye, screen-left eye: rows 0–2 brow band, row 3 dome, row 4 lash, rows 5–7 iris. The screen-right eye is the mirror, with `W` moved back to the iris's left column so the light stays consistent. Far eye (SE) and profile (E) = the same template with the pupil column dropped (4 wide). `.` = skin, ` ` = keep.

```
          open    half    closed  happy^^  determined surprised hurt><
brow 0    .....   .....   .....   .hhh.    hh...      .hhh.     ...hh
brow 1    .hhh.   .hhh.   .hhh.   h...h    ..hhh      .....     .hh..
brow 2    .....   .....   .....   .....    .....      .....     .....
dome      .KKK.   .....   .....   .....    .....      .KKK.     .....
lash      KKKKK   .....   .....   .KKK.    KKKKK      KWWWK     KK...
iris      KWKK.   KKKKK   K....   K...K    KWKK.      KWKWK     ..KKK
iris      .WKg.   .WKg.   .KKKK   .....    .WKg.      .KKK.     KK...
iris      .ggg.   .ggg.   .....   .....    .ggg.      .....     .....
```
- Determined = the open eye with a flat lid (no dome) + brow sloping down toward the nose. Hurt = `>` / `<` (the mirror gives `<`) + worried brow. Surprised = a white ring with a 1 px pupil + raised brow.
- **Per facing** (master coords, `facesys.LAYOUT`): **S**: both eyes, cols 56–60 / 67–71, dome row 49 (the masters' eye line). **SE**: near eye 61–65 + far eye 72–75 (4 wide), dome row 50. **E**: one profile eye 73–76, dome row 49. **SW/W**: flipped base + mirrored layout, catchlight still screen-left. **NE**: lash tip only (2 `K` px at the cheek edge for open/determined/surprised, 1 for half, none when closed). **N**: nothing.
- Brow = `h` on skin. In the 3D frames the bangs hang lower than in the masters, and brows were 0–6 px visible (`stability.json`). So the rule is: **on hair (`H/L/g`) the brow is drawn `K`** (it shows through the fringe). Without this, determined/worried brows mostly vanish.
- **Head base:** the round-3 face-cleared masters `rig/tex/tex_<V>.png` (eyes, brows, mouth and blush cleared). The two nose pixels are cleared here too. The E profile nose is only the silhouette bump; nothing is drawn.
- Mapping from M's expression keys (`proto.EXMAP`): neutral/smile → open, joyful → happy, determined/focused/effort → determined, pained/wince → hurt, squint → half, blink 1 → closed, blink .5 → half.

At 1x the S/SE sheet reads clearly: each expression is a distinct silhouette. The weakest are surprised in E (the ring looks like a dot) and the SE far eye when closed or happy (it merges into the cheek outline).

## 2. Placement: texture on 3D (a) vs pixel templates at 3D anchors (b)

**Prototype setup** (`scripts/proto.py`, `surfanchor.py`). Frames: idle SE f00 (open) and f01 (blink), walk SE f02, run E f03 (determined), jump S f04 (determined) and f08 (surprised), all from the cached 8x passes of 66119a7. Outputs: `proto_compare_4x.png` (head 4x), `proto_compare_1x.png`/`_2x.png` (full sprite), `frames/`.
- **Clearing the old face (needed by both):** every hi-res pixel's *rest-space* position (the `rpos` pass) goes through a front planar chart (calibrated so that the illustration eyes land on the master eyes within 0.5 px in S). Pixels inside `rig/tex/face_mask_S.png` (+1 px, plus a side band for E/W) become flat `s` when the 8x8 block coverage is ≥ .5. This follows the model with no 2D special case. In production R should simply render the head with the face mask applied.
- **(a) Texture on 3D:** the same templates, painted big and flat in that chart and sampled per hi-res pixel through `rpos`. Then an 8x8 plurality vote, as P's material vote does.
- **(b) Stamp at `frames[i].face`:** template origin = master origin + round(anchor − rest anchor).
- **(b') Stamp at a surface anchor:** the rest-space surface point of each drawn eye (snapped onto the head) is found again in every frame through `rpos`. Its screen centroid places the template, and "not found" means hidden. Templates are clipped by hair, hands and outline. **If less than 60 % of an eye's ink is visible, the whole eye is dropped** (no orphan catchlight on the hair).

**Results** (ink pixels per frame, `stability.json`):

| | (a) texture | (b') surface stamp |
|---|---|---|
| idle S open (9 frames) | K 23–27, g 6–10, W 2–4: the shape boils | K 24, g 8, W 4 every frame (K 21 in one partly occluded frame) |
| blink (closed) | K 4–8: broken dots (idle SE f01 shows two specks) | K 8–10: clean line |
| run E determined | **0–2 px: the eye is gone** (planar texture at a grazing angle) | 11–12 px every frame |
| SE far eye | present, but a dark blob | dropped when hair covers it (idle SE f00/f01, walk f06) |

- **(b) with today's `face.*` empties is not good enough.** They sit 3.8 cm inside the head. Against the painted eye they drift −1.3 to −3.8 px vertically in E frames (idle E f00 −1.3, run E f03 −3.8), and the stamp lands on the cheek. The surface-anchor version tracks the painted eye within about 0.5 px in every tested frame. Same idea, and it follows the 3D model *more* strictly.
- **Trade-offs of (b'):** (1) the shape is fixed per facing, so heavy yaw or roll moves the eyes but never foreshortens them (that is the point: never mush). (2) The SE far eye toggles on and off at the 60 % threshold, so it needs hysteresis (keep the previous state for 2 frames). (3) It needs per-view templates for 3 facings + mirror (done here). (4) R must export surface points (`face_anchors.json` already has `surf`) or an `rpos` lookup.
- **Trade-offs of (a):** one asset and zero placement code, and it looks good in S/SE stills. But blinks and thin brows fall below the 8x8 vote, the shape boils frame to frame, and profile views lose the eye completely. The illustration-texture rounds already showed the same failure (5–6/10).

**Recommendation: (b')**, with face clearing done in the render (masked head texture) and the stamp as the last step of P's chain. It is the round-4 "exact pixels" approach with a 3D-derived position, so it respects "follow the 3D model, don't special-case": the position, occlusion and visibility all come from the model; only the glyph is fixed.

## 3. Palette audit (66119a7, 528 frames, `palette_audit.json`, `swap_pairs.json`)

- **Count:** 0 off-palette px. All 18 keys are used somewhere. Keys per frame are 10–18 (mean 14.9). By direction: S 16.6, SW 16.7, SE 16.2, E 15.8, W 15.4, NE 13.8, NW 12.6, N 12.1.
- **Ramps actually used** (share of each material's pixels, guide matid):
  - skin: `s` 34, `K` 20, `S` 17, **`R` 9, `k` 7.5, `h` 4.3, `E` 3.4, `m` 2.1**. Skin uses 8 keys; dress reds and hair dark sit on the skin.
  - hair: `H` 30, `h` 24, `K` 19, **`d` 10.4** (the sock key on hair), `L` 1.0 (the master sheen is almost gone).
  - red: dress `E` 67 / `R` 14 / `e` 6.5; sleeve `E` 77 / `R` 10.5 / `e` **0**.
  - obi: `O` 68 / `o` 13 / `Q` 7 (healthy).
  - socks: `D` 57 / `d` 10 / **`g` 4.6** (rim).
  - boots: `H` 43 / `h` 21 / `K` 35 (no light).
- **View drift:** SE/SW hair is `h` 25 % + `d` 25 % with only 13–15 % `H`, while S/E/W hair is 38–40 % `H`. So the hair is a full step darker in the diagonal views. SE/SW skin is only 25–28 % `s` with 12.5 % `k`, against 44 % `s` / 4 % `k` in S. The faces are pinker and darker in exactly the views the panel complained about.
- **Shade swap** (pxeval definition, all 48 clips): mean .061, worst run SE .096 / run SW .093 / jump SW .089. By pair: `Kh` 19 %, `Hh` 17 %, `ER` 13 %, `Hd` 11 %, `dh` 9 %, `Kd` 7 %, `DK` 7 %, `Ee` 3 %, `DH` 3 %, `Ss` 3 %, `Dd` 2.5 %. **The dark cluster `K h D d H` = 78 %.** CIEDE2000 between keys: D–d 3.6, d–H 4.1, K–D 9.2, K–h 9.4, h–H 10.1, E–e 5.6. `D d` are indistinguishable from `H`/`h` at sprite scale and exist only to flicker.

### Proposed LOCKED palette: 14 colours

| role | keys | rule |
|---|---|---|
| outline | `K` | Every silhouette edge and every overlap line (far side). An edge pixel is never eye white, iris or blush. Also lash/pupil. |
| hair + boots + **socks** | `h` shadow, `H` base, `g` light, `L` sheen | Hair: `H` base; `h` on normal bands facing away (lowest 25 % of N·L) and as interior strand lines; `g` on the crown top band; `L` 1 px sheen arcs on hair only. Socks = `h` with an `H` lit stripe on the near leg; boots `H`/`h` + `g` toe glint. |
| skin | `s` base, `S` shadow | The face interior is always flat `s`. `S` only for the 1 px cast under bangs/chin, the neck, inner legs and the shadow-side jaw rim. No `m`, no `k`, no hair/red on skin. |
| red (dress, sleeve, bow) | `e` light, `E` base, `R` shadow | `e` only on up-facing surfaces (bow top, shoulder, sleeve top). `R` for folds, under the obi and inside the sleeve. Optional: lift `e` by about 5 dE (E–e is only 5.6). |
| obi | `Q`, `O`, `o` | unchanged |
| eyes | `W` (+ shared `K`, `g`) | catchlight/sclera only |

Dropped: `D` → `h`, `d` → `H`, `k` → `s`, `m` → `S` (18 → 14 keys, with `W` included). **Band rule:** the band is chosen from the smoothed *surface normal* (N·L of the rest-locked surface, three fixed thresholds per material), not from the textured luminance, with P's existing hysteresis margin. Textures may only pick *which material*, never the tone.

**Before/after** (`palette_before_after.png`, `lock_result.json`; pure key remap + isolated skin crumbs → `s` + (b') face, *no re-shading*):

| clip | shade_swap before → after | keys/frame before → after |
|---|---|---|
| walk SE | .082 → .053 (−35 %) | 16.1 → 12.1 |
| run SE | .095 → .058 (−39 %) | 16.8 → 12.8 |
| idle S | .036 → .021 (−41 %) | 16.1 → 11.9 |

What remains is `Hh`/`Kh`/`ER`, which is band flicker on moving surfaces. Only the normal-band rule plus temporal locking in P's chain fixes that; a remap cannot. The gate (.015) will not pass on the remap alone.

## Asks
- **R:** render the head with the face mask applied (blank `s` face; `face/illus` expression swaps retired). Export a surface eye point per eye (or keep the `rpos` pass), and **fix the 66119a7 bug where eye whites render as transparent holes** (idle SE f00, run E f03: background shows through the eyes).
- **P:** adopt the 14-key palette + band rules; stamp the (b') templates last (clip to skin, 60 % drop rule, 2-frame hysteresis on the far eye, brows `K` over hair).
- **F:** review the 7 glyphs at 1x (surprised-E and the SE far closed eye are the weak ones).

No critique call was used.
