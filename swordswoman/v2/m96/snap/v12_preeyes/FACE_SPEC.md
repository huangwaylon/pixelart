# M96 FACE SPEC (eyes + brows + nose + mouth + blush; 96px figure, palette v2/pixelize/palette.json)
FACE ROUND 2 (2026-10-27, "faithful face"; user: less pointy face, eyes too low (not too high), feminine cat-eye lashes, side cheek bulge, blush too small, be faithful). THE ILLUSTRATION IS THE AUTHORITY: measurements in `face_measure.json` (raw illustration fractions of crown->chin + sprite-coord landmarks/contours read on the warped sources geo/src_V.png; overlays face2/measure_<V>.png; tool face2/measure.py) override the earlier Pokemon-derived eye spec. Source of truth: `eye_spec.json` + `heads/anchor.json`. Code: `tools/eyetmpl.py` (kind_tmpl, brow_tmpl, wing, blush_tmpl), `tools/stamp.py`, `tools/eyecheck.py`, `tools/face2build.py` (masters pass; `tools/faceround.sh IN OUT`), `tools/facesheet.py`.

## Round-2 measurements -> pixels (face_measure.json `targets`)
- Eye line: S illus lash top 49.7 / iris centre 52.0 / eye bottom 53.8 -> lash row 50, iris rows 51-53 (was 51 / 52-54: 1.3 px low). E 50.0 / 52.3 -> lash 50 (was 51). SE near 51.5 / far 50.8 -> lash 51 kept (both within 0.5). eye_dy (lash - crown 30): S 20, SE 21, E 20 (eye_spec eye_dy per view). Raw fractions (crown->chin): S lash .687 iris .745 mouth .895; SE near lash .712 far .681; E lash .658.
- S jaw: illus skin spans rows 56-60 = 57-70 / 57.4-70.5 / 58.8-69.1 / 60.6-67.4 / 62.6-65.4 -> skin 57-70, 58-69, 59-68, 60-67, 62-65 (was ..., 59-68, 60-67, 61-66, 63-64: pointy V); chin underside shadow row 61 g 62-65.
- SE far cheek ("sideview cheek bulge"): illus edge 74.4 at rows 54-56 vs sprite outline at 76-77 -> outline K at col 75 rows 55-56 with a 1 px hair strand H at 76 (far eye has no lower lash so the corner stays skin).
- E profile: skin edge 78 at rows 49-53, nose 78.6 at rows 54-55 (2-row bump, K at 79), 78.5 philtrum (K 78), upper lip 78.3 (row 57 K at 78), chin recedes (77, 76, 76); mouth line row 57 cols 75-76; chin bottom row 61 kept (raw proportion).
- Nose: S (63, 54-55) S (illus x 63.5); SE (71, 55-56) S (illus 71.2, 55.8-56.8). Blush (illus 56.7-60.7 x 54.7-56.7 in S): oval patches.
- Fidelity (face2/facemetrics.py; vs snap/v11_preface2): face_ssim S .556->.573, SE .593->.607, E .173->.319; lash delta S +1.3->+0.3, E +1.0->0.0, SE -0.5/+0.2 (kept); contour MAE S .74->.42, SE .82->.57, E 1.01->.92 px.

## Construction (one for every eye)
- Block 6x6 (front) = GAP row (skin) + K lash row + 3 iris rows + empty row (outer col of the empty row = '_' keep).
- FEMININE CAT-EYE: thick upper lash = K lash row from the outer corner col 0 to col 4 + K at the outer corner of the first iris row; WING = 1 K px flick up-and-out OUTSIDE the block (front_left (-1,0); front_right (6,0); far (4,0); surprised (-1,-1), blink_half (-1,1); closed/squint eyes none); LOWER LASH = 1 h px (warm dark brown; K read boxy, crit r1) at the outer corner of the iris bottom row (SE far eye: none, the corner touches the cheek outline). Stamps restore the master px under every wing position (anchor eyes[i].wing_bg) before drawing the expression's wing.
- Iris 4x3: h top row, g sides, L light bottom. Pupil 1 px K at iris col 3 row 3; CATCHLIGHT 1x2 W at iris col 2 (same screen-space position in every eye/view/expression; mirror() mirrors only lash/wing).
- Kinds: S = front_left + front_right; SE = front_left (near) + far (4 wide); E = front_left; NE = lash tip `ne_lash` + 1x2 blush; N = none.
- Iris colours h #342126, g #5e4a45, L #85706a; lash/pupil K #160c0d; catchlight W #f6eeea.
- qc note: side-hair px next to the S lower lashes are H (54-55,54), (72-73,54) so the qc eye blob does not run into the hair.

## Blush (round 2: bigger, soft oval)
- k patches per anchor [x, y, kind]: front `kkkk/.kk.` (cheerful/joy `kkkk/kkkk`, embarrassed `kkkk/kkkk/.kk.`), SE far cheek `kkk/.kk`, NE `k/k`. S (57,55) + (67,55); SE (62,56) front + (72,56) far; E one patch (72,55); NE (74,58). Only s/S/k px painted; eyecheck requires >= 3 k px per patch.

## Brows (new)
- Colour: `g` (#5e4a45, hair-ramp brown; `eye_spec.json` brow.char) only - lighter than the K lash so the lash stays the darkest line (crit r2: h brows read near-black/heavy); thin 1 px strokes, 4-5 px long (SE far eye 3-4 px), never K/m. Templates write `h` = the brow char. (h variant: face/eye_spec_hbrow.json.)
- Rows: brow template = 3 rows at lash-4, lash-3, lash-2 (eye block y0-3..y0-1, i.e. rows 46-48 in S/E, 47-49 in SE); row lash-1 (eye block row 0) is a 1-row skin GAP in every view and expression (surprised raises the lash into it, and its brow is raised too, so the gap stays 1 row).
- Placement: front_left over eye cols 0-5 (inner end = toward the nose = right); front_right = plain mirror; SE far = own 4-wide template (inner = left) at the far-eye x0; E profile = front_left (inner end toward the nose); NE/N: no brow (face hidden in the illustration).
- Brow window: the fringe is cut over the brow (front cols 0-5, far cols -1..3; from the row above the brow top down to lash-2): hair/K/m -> skin, top row plain skin s (an S row merged brow + bang edge at 1x, crit r1) so the brow never merges with the bangs. Stranded skin px are folded back (qc S4).
- Expression = brow shape only:
  - neutral: front_left `...... / ..hhh. / .h....` | far `.... / hhh. / ...h`
  - cheerful: front_left `..hhh. / .h.... / ......` | far `hhh. / ...h / ....`
  - surprised: front_left `..hh.. / .h..h. / ......` | far `.hh. / h..h / ....`
  - embarrassed: front_left `....h. / .hhh.. / ......` | far `h... / .hhh / ....`
  - pain: front_left `...... / ...hh. / .hh...` | far `.... / hh.. / ..hh`
  - determined: front_left `.hh... / ...h.. / ....h.` | far `..hh / .h.. / h...`
  - blink_half: front_left `...... / ..hhh. / .h....` | far `.... / hhh. / ...h`
  - blink_closed: front_left `...... / ..hhh. / .h....` | far `.... / hhh. / ...h`
  - joy: front_left `..hhh. / .h.... / ......` | far `hhh. / ...h / ....`
  - effort: front_left `.hh... / ...h.. / ....h.` | far `..hh / .h.. / h...`
  - shout: front_left `.hh... / ...h.. / ....h.` | far `..hh / .h.. / h...`
  (neutral/blink = gentle arc, outer end down; cheerful/joy = same arc raised 1 row; surprised = high round arch; embarrassed = slightly raised, inner end up; determined/shout/effort = steep V, angled down toward the centre; pain(hurt) = tilted up toward the centre.)

## Nose (round 2 positions, measured)
- S: 2 px vertical `S` at (63,54)-(63,55) (illus x 63.5, rows 54.7-55.5). SE: 2 px `S` at (71,55)-(71,56) beside the far eye. A single px fails qc S4.
- E profile: 2-row bump: skin (78,54),(78,55), K tip (79,54),(79,55), K underside (78,56); upper lip K (78,57).
- NE / N: none. Anchor key `nose` = [x, y, char]; eyecheck verifies it when an anchor is given.

## Eye templates (neutral; "." skin, "@" catchlight W, "_" keep; wing outside)
- front_left: `....../KKKKK./Kh@hh./.g@Kg./hgLLg./_.....` + wing (-1,0)
- front_right: `....../.KKKKK/.h@hhK/.g@Kg./.gLLgh/....._` + wing (6,0)
- far: `..../KKKK/h@hK/g@K./gLL./..._` + wing (4,0)

## Expressions (front_left eye block | wing | brow | mouth | blush)
- neutral: eye `...... / KKKKK. / Kh@hh. / .g@Kg. / hgLLg. / _.....` | wing [[-1, 0]] | brow `...... / ..hhh. / .h....` | mouth `____ / .mm. / ____` | blush `kkkk/.kk.`
- cheerful: eye `...... / KKKKK. / Kh@hh. / .g@Kg. / h.LL.. / _.....` | wing [[-1, 0]] | brow `..hhh. / .h.... / ......` | mouth `R__R / .RR. / ____` | blush `kkkk/kkkk`
- determined: eye `...... / KKKK.. / Kh@hKK / .g@Kg. / hgLLg. / _.....` | wing [[-1, 0]] | brow `.hh... / ...h.. / ....h.` | mouth `____ / mmmm / ____` | blush `kkkk/.kk.`
- shout: eye `...... / KKKK.. / Kh@hKK / .g@Kg. / h.LL.. / _.....` | wing [[-1, 0]] | brow `.hh... / ...h.. / ....h.` | mouth `_RR_ / RkkR / _RR_` | blush `kkkk/.kk.`
- effort: eye `...... / ...... / KKK... / ..KKK. / ...... / _.....` | wing [] | brow `.hh... / ...h.. / ....h.` | mouth `____ / mmmm / m__m` | blush `kkkk/.kk.`
- joy: eye `...... / ...... / .KKK.. / K...K. / ...... / _.....` | wing [] | brow `..hhh. / .h.... / ......` | mouth `R__R / RRRR / .kk.` | blush `kkkk/kkkk`
- surprised: eye `KKKKK. / ...... / .h@hh. / .g@Kg. / hgLLg. / _.....` | wing [[-1, -1]] | brow `..hh.. / .h..h. / ......` | mouth `____ / .RR. / .RR.` | blush `kkkk/.kk.`
- pain: eye `...... / KK.... / ..KKK. / KK.... / ...... / _.....` | wing [] | brow `...... / ...hh. / .hh...` | mouth `____ / mmmm / _RR_` | blush `kkkk/.kk.`
- blink_half: eye `...... / ...... / KKKKK. / Kg@Kg. / hgLLg. / _.....` | wing [[-1, 1]] | brow `...... / ..hhh. / .h....` | mouth `____ / .mm. / ____` | blush `kkkk/.kk.`
- blink_closed: eye `...... / ...... / ...... / K..... / .KKKK. / _.....` | wing [] | brow `...... / ..hhh. / .h....` | mouth `____ / .mm. / ____` | blush `kkkk/.kk.`
- embarrassed: eye `...... / KKKKK. / Kh@hh. / .g@Kg. / hgLLg. / _.....` | wing [[-1, 0]] | brow `....h. / .hhh.. / ......` | mouth `____ / m.m. / .m.m` | blush `kkkk/kkkk/.kk.`
- aliases: hurt = pain. Open-eye expressions keep the neutral iris + catchlight exactly; cheerful/determined now differ from neutral at 1x through brows (raised vs angled) + lid/lower-lash rows + mouth.

## Other face-round fixes (tools/handfix.py, masters only)
- Hands S/SE/N: slender down-pointing hands like the illustration: wrist, palm, thumb | K notch | fingers to a 1 px tip (thumb toward the body).
- Thigh skin band: S row 91 shade S -> s (only the hem row keeps shade); SE sock-top red row 94 -> skin (band 4 rows, sock top 95 = S).
- SE bow: K line where bow touches hair, lit `e` top edge; SE hair highlight calm (L/g clusters < 4 px and lone h specks -> H).

## Checker / hooks
- `python3 v2/m96/tools/eyecheck.py FRAME.txt VIEW [EXPR|auto] [--anchor v2/m96/heads/anchor.json]` -> exit 0 if every expected eye AND its brow (shape, h colour, skin gap) AND its cat-eye wing (K) match exactly (+ blush patches >= 3 k when an anchor is given) (+ nose when an anchor is given; head stamps with "; origin" are pasted into the 128 cell and checked at the anchor) and there is no stray W near the eyes; otherwise fix lines (artist retry text).
- Module: `eyecheck.check(grid, view, expr='auto', anchor=None) -> (metrics, fixes)`; `eyecheck.qc_hook(grid, view, ref_grid, pal_path)` is called by v2/qc/qc_gate.py automatically (template match + eye row vs the reference).
- One-line hook for lint_style.py / ff_redraw.validate (before `return fx`): `sys.path.insert(0, '/Users/waylonhuang/Documents/other/pixelart/swordswoman/v2/m96/tools'); import eyecheck; fx += eyecheck.check(grid, view)[1]` (grid = list of rows; view = S/SE/E/W/SW...; animated frames that move the head are searched over the whole head area when no anchor is given).
- Head stamps: `heads/<V>_<expr>.txt` ('; origin x0 y0' = paste position in the 128 cell), `heads/anchor.json` (eye/mouth/blush/ne_lash positions + stamp boxes). Rebuild: `python3 v2/m96/tools/stamp.py heads v2/m96/masters v2/m96/heads`.
- Sheets: `face_sheet.png` (illustration face crop | heads 6x neutral/cheerful/determined/surprised | 1x, measured guide lines; tools/facesheet.py), `eyes_sheet.png` (eyes 8x, views x key expressions), `stamps.png`. Critique: crit/eyes_argon.txt (consistency 9, readability 8), crit/eyes_opus.txt (7 / 5).

- Critique (crit/face_r*_*.txt): r1 Argon 8.5 / Opus 7; r2 Argon 8.5 (brows 9, nose 8, consistency 9, 1x 8.5) / Opus 6 (brows 6 heavy -> switched to g, 1x 4). 
- Cross-view consistency: brows use the same char (g), the same rows (lash-4..lash-2), the same 1-row gap and the same per-expression shape (mirrored / far-mapped) in S, SE and E; eyecheck enforces this per view, qc_gate runs it through qc_hook on masters and stamps.

- Round-2 critique (crit/face2_r*_*.txt): r1 Argon 7.5 / Opus 5 -> r2 Argon 8.5 (faithful 8.5, eye height 9, lashes 8, chin 8.5, cheek 7, blush 9) / Opus 6 (eye height 8, lashes 5, chin 6, cheek 7, blush 8). Open: Opus wants a lighter/thinner lash look and narrower E eye (kept: measured 4 px eye), flatter S chin.
