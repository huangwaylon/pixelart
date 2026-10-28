# M96 EYE SPEC (96px figure, palette v2/pixelize/palette.json)

Source of truth: `eye_spec.json` (templates, mouths, blush, rules) + `heads/anchor.json` (positions). Code: `tools/eyetmpl.py` (pure-python templates), `tools/stamp.py` (faces/head stamps), `tools/eyecheck.py` (checker + qc hook).

## Construction (one for every eye)
- Block 6x6 (front) = brow row + K lash row + 3 iris rows + empty row. Wing K one row below the lash at the outer corner.
- Iris 4x3: h top row, g sides, L light bottom (kept inside the eye; nothing under it - a lid line or grey row read as eye bags).
- Pupil: 1 px K at iris column 3, row 2. CATCHLIGHT: 1x2 px W at iris column 2, iris rows 1-2 (inset so it sits inside the iris).
- Both eyes and every view use the same screen-space catchlight/pupil position: `mirror()` mirrors only the lash/wing, never the iris. W-facing / SW frames = mirrored kinds (front_right / far_left), the catchlight still sits at iris column 2 from the left.
- Kinds: S = front_left + front_right; SE = front_left (near) + far (front_right cols 1,2,3,5: 3-wide iris); E = front_left (same main-eye box as S/SE, qc requires it); NE = no eye, lash tip `ne_lash` + 1x2 blush; N = none.
- Eye height: lash row = qc crown + 21 (row 51) in S, SE and E; eye top 21 rows below the crown in all face views.
- Iris colours = the illustration's grey-brown: h #342126, g #5e4a45, L #85706a; lash/pupil K #160c0d; catchlight W #f6eeea.

## Templates (neutral; '.' skin, '@' catchlight W, '_' keep)
- front_left: `...... / .KKKK. / Kh@hh. / .g@Kg. / .gLLg. / ......`
- front_right: `...... / .KKKK. / .h@hhK / .g@Kg. / .gLLg. / ......`
- far: `.... / KKK. / h@hK / g@K. / gLL. / ....`

## Expressions (front_left; brow row first)
- neutral: eye `...... / .KKKK. / Kh@hh. / .g@Kg. / .gLLg. / ......` | mouth `____ / .mm. / ____` | blush 2 px
- cheerful: eye `...... / .KKKK. / Kh@hh. / .g@Kg. / ..LL.. / ......` | mouth `____ / RRRR / .kk.` | blush 3 px
- determined: eye `...... / KKKK.. / Kh@hKK / .g@Kg. / .gLLg. / ......` | mouth `____ / mmmm / ____` | blush 2 px
- shout: eye `.mmm.. / KKKK.. / Kh@hKK / .g@Kg. / ..LL.. / ......` | mouth `_RR_ / RkkR / _RR_` | blush 2 px
- effort: eye `mm.___ / ...... / KKK... / ..KKK. / ...... / ......` | mouth `____ / mmmm / m__m` | blush 2 px
- joy: eye `...... / ...... / .KKK.. / K...K. / ...... / ......` | mouth `R__R / RRRR / .kk.` | blush 3 px
- surprised: eye `.KKKK. / ...... / .h@hh. / .g@Kg. / .gLLg. / ......` | mouth `____ / .RR. / .RR.` | blush 2 px
- pain: eye `...... / KK.... / ..KKK. / KK.... / ...... / ......` | mouth `____ / mmmm / _RR_` | blush 2 px
- blink_half: eye `...... / ...... / .KKKK. / Kg@Kg. / .gLLg. / ......` | mouth `____ / .mm. / ____` | blush 2 px
- blink_closed: eye `...... / ...... / ...... / K..... / .KKKK. / ......` | mouth `____ / .mm. / ____` | blush 2 px
- embarrassed: eye `..mm.. / .KKKK. / Kh@hh. / .g@Kg. / .gLLg. / ......` | mouth `____ / m.m. / .m.m` | blush 4 px
- aliases: hurt = pain. Open-eye expressions keep the neutral iris + catchlight pixels exactly; expressions change only lash/brow/lid rows, mouth and blush (qc stamps rule). Closed/squint (joy, blink_closed, effort, pain) drop the iris.

## Checker / hooks
- `python3 v2/m96/tools/eyecheck.py FRAME.txt VIEW [EXPR|auto] [--anchor v2/m96/heads/anchor.json]` -> exit 0 if every expected eye matches its template exactly and there is no stray W near the eyes; otherwise fix lines (artist retry text).
- Module: `eyecheck.check(grid, view, expr='auto', anchor=None) -> (metrics, fixes)`; `eyecheck.qc_hook(grid, view, ref_grid, pal_path)` is called by v2/qc/qc_gate.py automatically (template match + eye row vs the reference).
- One-line hook for lint_style.py / ff_redraw.validate (before `return fx`): `sys.path.insert(0, '/Users/waylonhuang/Documents/other/pixelart/swordswoman/v2/m96/tools'); import eyecheck; fx += eyecheck.check(grid, view)[1]` (grid = list of rows; view = S/SE/E/W/SW...; animated frames that move the head are searched over the whole head area when no anchor is given).
- Head stamps: `heads/<V>_<expr>.txt` ('; origin x0 y0' = paste position in the 128 cell), `heads/anchor.json` (eye/mouth/blush/ne_lash positions + stamp boxes). Rebuild: `python3 v2/m96/tools/stamp.py heads v2/m96/masters v2/m96/heads`.
- Sheets: `eyes_sheet.png` (eyes 8x, views x key expressions), `stamps.png`. Critique: crit/eyes_argon.txt (consistency 9, readability 8), crit/eyes_opus.txt (7 / 5).
