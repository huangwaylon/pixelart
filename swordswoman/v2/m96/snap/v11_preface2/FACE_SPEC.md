# M96 FACE SPEC (eyes + brows + nose + mouth; 96px figure, palette v2/pixelize/palette.json)
Supersedes EYE_SPEC.md (face round 2026-10-27, user feedback "needs better nose, eyebrows are missing"). Source of truth: `eye_spec.json` (eye/brow templates, mouths, blush, rules) + `heads/anchor.json` (eye/mouth/blush/nose positions). Code: `tools/eyetmpl.py` (kind_tmpl, brow_tmpl), `tools/stamp.py` (faces/head stamps), `tools/eyecheck.py` (checker + qc hook), `tools/faceround.sh` (masters pass), `tools/handfix.py`.
## Construction (one for every eye)
- Block 6x6 (front) = GAP row (skin; brow no longer drawn here) + K lash row + 3 iris rows + empty row. Wing K one row below the lash at the outer corner.
- Iris 4x3: h top row, g sides, L light bottom (kept inside the eye; nothing under it - a lid line or grey row read as eye bags).
- Pupil: 1 px K at iris column 3, row 2. CATCHLIGHT: 1x2 px W at iris column 2, iris rows 1-2 (inset so it sits inside the iris).
- Both eyes and every view use the same screen-space catchlight/pupil position: `mirror()` mirrors only the lash/wing, never the iris. W-facing / SW frames = mirrored kinds (front_right / far_left), the catchlight still sits at iris column 2 from the left.
- Kinds: S = front_left + front_right; SE = front_left (near) + far (front_right cols 1,2,3,5: 3-wide iris); E = front_left (same main-eye box as S/SE, qc requires it); NE = no eye, lash tip `ne_lash` + 1x2 blush; N = none.
- Eye height: lash row = qc crown + 21 (row 51) in S, SE and E; eye top 21 rows below the crown in all face views.
- Iris colours = the illustration's grey-brown: h #342126, g #5e4a45, L #85706a; lash/pupil K #160c0d; catchlight W #f6eeea.

## Brows (new)
- Colour: `g` (#5e4a45, hair-ramp brown; `eye_spec.json` brow.char) only - lighter than the K lash so the lash stays the darkest line (crit r2: h brows read near-black/heavy); thin 1 px strokes, 4-5 px long (SE far eye 3-4 px), never K/m. Templates write `h` = the brow char. (h variant: face/eye_spec_hbrow.json.)
- Rows: brow template = 3 rows at lash-4, lash-3, lash-2 (eye block y0-3..y0-1, i.e. rows 47-49 in S/SE/E); row lash-1 (eye block row 0) is a 1-row skin GAP in every view and expression (surprised raises the lash into it, and its brow is raised too, so the gap stays 1 row).
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

## Nose (new)
- Light from screen-left (matches the hair sheen / skin shading): the nose cue sits on the shadow (screen-right) side.
- S: 2 px vertical `S` (skin shadow) at (64,54)-(64,55), 1 col right of the face centre, between the iris bottom row and the mouth. SE: same 2 px `S` at (70,54)-(70,55), next to the far eye (3/4 nose). A single px or m/S pair fails qc S4 (orphans) and reads as a smudge; the S pair reads as a soft anime nose shadow.
- E profile: upturned bump in the outline: K tip at (79,54) out of the x78 face line, skin at (78,54), K underside at (78,55) (nose row = iris bottom row, as in the illustration).
- NE / N: none. Anchor key `nose` = [x, y, char] list per view; eyecheck verifies it when an anchor is given.

## Eye templates (neutral; "." skin, "@" catchlight W, "_" keep)
- front_left: `...... / .KKKK. / Kh@hh. / .g@Kg. / .gLLg. / ......`
- front_right: `...... / .KKKK. / .h@hhK / .g@Kg. / .gLLg. / ......`
- far: `.... / KKK. / h@hK / g@K. / gLL. / ....`

## Expressions (front_left eye block | brow | mouth | blush)
- neutral: eye `...... / .KKKK. / Kh@hh. / .g@Kg. / .gLLg. / ......` | brow `...... / ..hhh. / .h....` | mouth `____ / .mm. / ____` | blush 2 px
- cheerful: eye `...... / .KKKK. / Kh@hh. / .g@Kg. / ..LL.. / ......` | brow `..hhh. / .h.... / ......` | mouth `R__R / .RR. / ____` | blush 3 px
- determined: eye `...... / KKKK.. / Kh@hKK / .g@Kg. / .gLLg. / ......` | brow `.hh... / ...h.. / ....h.` | mouth `____ / mmmm / ____` | blush 2 px
- shout: eye `...... / KKKK.. / Kh@hKK / .g@Kg. / ..LL.. / ......` | brow `.hh... / ...h.. / ....h.` | mouth `_RR_ / RkkR / _RR_` | blush 2 px
- effort: eye `...... / ...... / KKK... / ..KKK. / ...... / ......` | brow `.hh... / ...h.. / ....h.` | mouth `____ / mmmm / m__m` | blush 2 px
- joy: eye `...... / ...... / .KKK.. / K...K. / ...... / ......` | brow `..hhh. / .h.... / ......` | mouth `R__R / RRRR / .kk.` | blush 3 px
- surprised: eye `.KKKK. / ...... / .h@hh. / .g@Kg. / .gLLg. / ......` | brow `..hh.. / .h..h. / ......` | mouth `____ / .RR. / .RR.` | blush 2 px
- pain: eye `...... / KK.... / ..KKK. / KK.... / ...... / ......` | brow `...... / ...hh. / .hh...` | mouth `____ / mmmm / _RR_` | blush 2 px
- blink_half: eye `...... / ...... / .KKKK. / Kg@Kg. / .gLLg. / ......` | brow `...... / ..hhh. / .h....` | mouth `____ / .mm. / ____` | blush 2 px
- blink_closed: eye `...... / ...... / ...... / K..... / .KKKK. / ......` | brow `...... / ..hhh. / .h....` | mouth `____ / .mm. / ____` | blush 2 px
- embarrassed: eye `...... / .KKKK. / Kh@hh. / .g@Kg. / .gLLg. / ......` | brow `....h. / .hhh.. / ......` | mouth `____ / m.m. / .m.m` | blush 4 px
- aliases: hurt = pain. Open-eye expressions keep the neutral iris + catchlight exactly; cheerful/determined now differ from neutral at 1x through brows (raised vs angled) + lid/lower-lash rows + mouth.

## Other face-round fixes (tools/handfix.py, masters only)
- Hands S/SE/N: slender down-pointing hands like the illustration: wrist, palm, thumb | K notch | fingers to a 1 px tip (thumb toward the body).
- Thigh skin band: S row 91 shade S -> s (only the hem row keeps shade); SE sock-top red row 94 -> skin (band 4 rows, sock top 95 = S).
- SE bow: K line where bow touches hair, lit `e` top edge; SE hair highlight calm (L/g clusters < 4 px and lone h specks -> H).

## Checker / hooks
- `python3 v2/m96/tools/eyecheck.py FRAME.txt VIEW [EXPR|auto] [--anchor v2/m96/heads/anchor.json]` -> exit 0 if every expected eye AND its brow (shape, h colour, skin gap) match the templates exactly (+ nose when an anchor is given; head stamps with "; origin" are pasted into the 128 cell and checked at the anchor) and there is no stray W near the eyes; otherwise fix lines (artist retry text).
- Module: `eyecheck.check(grid, view, expr='auto', anchor=None) -> (metrics, fixes)`; `eyecheck.qc_hook(grid, view, ref_grid, pal_path)` is called by v2/qc/qc_gate.py automatically (template match + eye row vs the reference).
- One-line hook for lint_style.py / ff_redraw.validate (before `return fx`): `sys.path.insert(0, '/Users/waylonhuang/Documents/other/pixelart/swordswoman/v2/m96/tools'); import eyecheck; fx += eyecheck.check(grid, view)[1]` (grid = list of rows; view = S/SE/E/W/SW...; animated frames that move the head are searched over the whole head area when no anchor is given).
- Head stamps: `heads/<V>_<expr>.txt` ('; origin x0 y0' = paste position in the 128 cell), `heads/anchor.json` (eye/mouth/blush/ne_lash positions + stamp boxes). Rebuild: `python3 v2/m96/tools/stamp.py heads v2/m96/masters v2/m96/heads`.
- Sheets: `face_sheet.png` (illustration face crop | heads 6x neutral/cheerful/determined/pain | 1x; tools/facesheet.py), `eyes_sheet.png` (eyes 8x, views x key expressions), `stamps.png`. Critique: crit/eyes_argon.txt (consistency 9, readability 8), crit/eyes_opus.txt (7 / 5).

- Critique (crit/face_r*_*.txt): r1 Argon 8.5 / Opus 7; r2 Argon 8.5 (brows 9, nose 8, consistency 9, 1x 8.5) / Opus 6 (brows 6 heavy -> switched to g, 1x 4). 
- Cross-view consistency: brows use the same char (g), the same rows (lash-4..lash-2), the same 1-row gap and the same per-expression shape (mirrored / far-mapped) in S, SE and E; eyecheck enforces this per view, qc_gate runs it through qc_hook on masters and stamps.
