# FACE_GUIDE: eye and mouth grammar for the swordswoman sprite (FACE strand, 2026-10-26)

Source of truth for the code: `v2/face/tools/faces.py` (stamps) and `v2/face/heads/*_base.txt` (head bases with anchors).
Build: `.venv/bin/python v2/face/tools/build_all.py` -> `v2/face/out/sprite/<VIEW>_<expr>.txt|_1x.png|_8x.png`; sheet: `tools/make_sheet.py <tag>`.
Animator mapping: `v2/face/expr_map.json`. Portraits: `v2/face/portrait/P_<expr>.txt` (render `tools/prender.py`).

## 1. What Pokemon does (study, refs in v2/style/refs + v2/face/refs; boards in v2/face/work/)
| family / size | eye | spacing / height | brows | mouth | blush | expression changes |
|---|---|---|---|---|---|---|
| BW/HGSS battle trainers (80x80, head 18-20 px; Lyra, Dawn, Hilda, Rosa, Lass, Battle Girl) | 2-3 w x 3-4 h. K lash row on top, 2 px thick at the OUTER end (wing). Outer column W sclera, inner columns dark iris (blue/brown); the W doubles as the glint. No lower lid line. | 3-4 px apart; lash row touches the fringe/hat brim; eye centre 0.61-0.68 down the head | hidden under bangs/hat; the fringe edge acts as the brow | 1-2 px dark red/brown closed; open (Lass BW/G4) = 2x2-3x2 red with dark top row | none | none (one static pose; B2W2 animate the body, not the face) |
| Gen5 overworld (32 px frame) | 1x2-2x2 K, sometimes 1 W | 4-5 px apart, just under the fringe | none | none/1 px | none | none |
| PMD sprites (24-32 px) | 2x3 with a 1 px K cap and 1 W glint | - | none | 1 px | none | carried by the body, Hurt frame closes the eyes |
| PMD portraits (40x40; SpriteCollab Meloetta/Gardevoir/Pikachu, 13 emotions) | 5-6 w x 7-8 h: heavy K lash with wing, dark iris top, light bottom, big 2x2 glint upper + small glint lower | eyes fill the upper-middle of the face | thin, drawn, the main expression lever with the lid angle | D-shaped open mouth: dark interior + pink tongue; closed = 2-4 px line | diagonal 2-3 px hatch (happy/joyous/inspired) | Happy = closed ^ arcs + open mouth; Determined = lid cut diagonally toward the nose; Angry = brow down-in + narrowed + anger mark; Shouting = squeezed/fierce + huge open mouth; Pain = > < + sweat; Surprised = shrunk pupils, whites, o-mouth; Worried = brows up-in, wavy mouth; Inspired = extra glints; Teary = tear line on the lower lid; Stunned = dot pupils |
Views: 3/4 compresses the far eye to 2 px and pushes it to the cheek edge, mouth offset toward the facing side; profile = one eye 1-2 px behind the front edge, nose bump, mouth = 1 px notch at the lip edge (open mouths cut the silhouette); back views show no face.

## 2. Face layout on the Level E sprite head (heads/E_*_base.txt, 19x24, crown row 7, chin rows 20-22)
| view | brow band | near eye box (x,y,w,h) | far eye box | mouth centre | blush | notes |
|---|---|---|---|---|---|---|
| S | row 13 (clear skin s since v11; was S) | 5,14,3,4 | 11,14,3,4 (mirror) | 9,19 | 5-6,18 / 12-13,18 | 3 px between eyes, 1 px skin margin outside |
| SE | row 13 | 7,14,3,4 | 13,14,2,4 (mirror, foreshortened) | 11,19 | 7-8,18 / 14,18 | mouth drops its near (left) column |
| E | row 13 | 14,14,2,4 (profile, outer wing at x13) | - | 17,19 (lip column; notch recessed to x16) | 12-13,18 | profile eyes use PROF, mouths MOUTH_P; '_' cuts the jaw outline |
| NE | - | - | - | - | cheek sliver 16,18 | only the cheek sliver shows: blush on joy/effort/shout/smile/pain |
| N | - | - | - | - | - | no face; expression shows only through head motion (squash) |
C_r4 test head (heads/C_r4_SE_base.txt): near 31,28,3,4; far 38,28,2,4; brow 27; mouth 36,33.
Rule: the lash row sits directly under the brow band (1 skin row under the fringe) so the K lash never merges with the dark fringe.

## 3. Eye grammar (FINAL v11; stamp = 5x5, near/left eye, OUTER corner on the left; S right eye = mirror)
Row 0 = brow band (1 px clear skin under the fringe since v11), rows 1-4 = eye box (3x4), col 0 = outer margin (lash wing), col 4 = inner margin. '.' = keep skin.
Chars: K lash/pupil, W glint/sclera/teeth, i iris dark, I iris light, s/S skin, e blush/tongue, r mouth line.
| expr | rows 0..4 | what carries it |
|---|---|---|
| neutral | `.....` `KKKK.` `KWiK.` `.iiI.` `..II.` | confident: full eye, 2 px outer lash wing, W glint upper-outer, lash wraps 1 px at the inner corner |
| determined | `K....` `.KKK.` `..KK.` `.WiI.` `..I..` | V-brow tick in the band + lid stepping down into the inner corner (glare), iris cut to 2 rows; inner corner trimmed so the two lids never join into a unibrow |
| shout | `KK...` `..KK.` `K.KKK` `.WiI.` `.....` | angry slanted brow (outer high, inner low) + slanted lid over an open eye: fierce, not narrowed |
| effort | `.....` `KKK..` `.KKKK` `.WiI.` `.....` | strain squint: heavy lid low toward the nose, 1 iris row, no bottom row |
| joy | `.....` `.....` `.KK..` `K..K.` `.....` | closed ^ arc (cheeks pushed up) |
| smile | `.....` `KKKK.` `KWiK.` `.iiI.` `.....` | neutral eye with the bottom row hidden by raised cheeks (+ blush, U mouth) |
| surprised | `.KKK.` `KKKK.` `.WKW.` `..i..` `.....` | lash raised into the brow band, 1 px K pupil between whites, skin below (no bottom white) |
| pain | `K....` `.KK..` `...K.` `.KK..` `K....` | > chevron (mirrored <), outer ticks spill into the band |
| blink_half | `.....` `.....` `KKKK.` `.iII.` `.....` | lash lowered 1 row, light iris sliver, no outer K |
| blink_closed | `.....` `.....` `.....` `KKKK.` `.....` | flat 4 px line low in the box |
| squash | `.....` `.....` `KK...` `.KKKK` `.....` | pressed-shut wince sloping down to the nose (head 1 row shorter) |
Far eye (SE): mirror, then drop the middle column (`far()`); overrides in `FAR`. Profile eye (E): `PROF = prof(EYE)` (drop the inner column; col0 = wing behind, col3 = front skin).

## 4. Mouth grammar (FINAL v11; front stamp 5 wide x 3 rows: row 0 cheek row 18, row 1 mouth row 19, row 2 chin row 20; centre col 2)
Closed mouths = 1 px r line whose SHAPE is the emotion; open mouths = dark K core + e tongue / W teeth, framed by r. Open mouths stop at row 20 (row 21 = jaw outline).
| expr | front (S) | SE (4 wide) | profile E (MOUTH_P, 4 wide) | read |
|---|---|---|---|---|
| neutral / blinks | `....r` `.rrr.` `.....` | `...r` `rrr.` `....` | `..r.` `.r..` `....` | cocky smirk: 3 px line, right corner kicked up 1 row |
| determined | `.....` `.rrr.` `.....` | `....` `rrr.` `....` | `....` `rr..` `....` | flat set 3 px line |
| shout | `.....` `rKKKr` `.KeK.` | `....` `KKKr` `KeK.` | `....` `KK__` `eeK_` | open yell: dark K core with r corners, K-e-K tongue row |
| effort | `.rrr.` `rWWWr` `.rrr.` | `rrr.` `WWWr` `rrr.` | `....` `rKW.` `....` | gritted teeth fully enclosed in r |
| joy | `.....` `rKKKr` `.rer.` | `....` `KKKr` `rer.` | `r...` `.K_.` `.e..` | open D grin, tongue |
| smile | `.....` `r...r` `.rrr.` | `....` `r..r` `.rr.` | `r...` `.rr.` `....` | closed U |
| surprised | `.rr..` `rKKr.` `.rr..` | `rr..` `KKr.` `rr..` | `....` `.K_.` `....` | round O, dark core |
| pain | `.....` `.r.r.` `r.r.r` | `....` `r.r.` `.r.r` | `....` `r...` `.r..` | closed zigzag wince (not open = not laughing) |
| squash | `.....` `.rrr.` `r...r` | `....` `.rr.` `r..r` | `....` `rrr.` `....` | down-turned "oof" frown |
SE: `MOUTH_SE` override or the front stamp minus its left column. E: lip notch in heads/E_E_base.txt (anchor `; mouth 17 19`; col 2 = notched outline, col 3 = lip column, `_` cuts the silhouette).
Mouth colour r (#581838); K only as open-mouth core, W teeth, e tongue. Blush e, 2 px per cheek on row 18, only on joy/smile/effort/shout.

## 5. 1-4 pixel edits (how one expression becomes the next)
- neutral -> determined: brow tick appears at the outer band px, the lash steps down 1 row toward the nose, the glint row loses its top; the smirk px drops into line.
- determined -> shout: a 2nd brow px joins the slant, the lid opens under it; the mouth opens (r corners + K core + K-e-K).
- shout -> effort: lid drops to a squint, the open core becomes W teeth enclosed in r.
- neutral -> smile: delete the bottom iris row (2 px per eye), smirk -> U, +2 px blush per cheek. smile -> joy: eye closes to ^, U fills to an open D.
- neutral -> surprised: lash jumps 1 row up into the band, the iris becomes W-K-W with a 1 px pupil, mouth -> O.
- neutral -> blink_half -> blink_closed: the lash moves down 1 row, then 1 more; iris px drop out.
- neutral -> squash: eye -> wince line, mouth turns down, head loses one skull row.

## 6. Palette (v2/style/pk_palette.json)
K #000000 lash/pupil/shout core, W #f8f8f8 sclera/glint/teeth, i #1c2c58 iris dark, I #3868b8 iris light, s #f8d0b8 skin, S #d89878 skin shadow/brow band, r #581838 mouth line/interior, e #f87068 tongue/blush, h #241c24 fringe edge over skin. No new colours on the sprite.

## 7. PMD portrait grammar (40x40, portrait/P_*.txt)
Same logic scaled: near eye ~5x7, heavy 2 px lash with wing, i top / I bottom iris, 2x2 W glint upper-left + 1 px lower glint; brows 1 px under the fringe (the main lever); open mouths = dark interior + e tongue (+W teeth for shout); effect marks only in empty corners (anger mark, sweat drop b, sparkles, tears). Extra emotions: worried, inspired, teary.

FINAL r5 (2026-10-26): zoom-in framing (face ~24 rows, bob cropped by the frame), near eye 6-7x8, burgundy interior lines (K only for silhouette/lash/pupil), brows 1px h on skin, head and bust shift 1-2px per emotion; P_blink = PMD Stunned slot, calm blink = P_blink_calm.txt. Generator portrait/tools/expr.py + blocks.py.

## 8. Re-fitting onto a new master head
1. Copy the head from the master, clear each eye box to '.', make the brow band and mouth row plain skin.
2. Add `; eye_near X Y W H`, `; eye_far ...`, `; brow_row Y`, `; mouth X Y`, `; blush X Y W`, `; blush_far ...` lines (NE: `; cheek X Y`).
3. Run `faces.build_view(base, VIEW, expr)`; nothing else changes. The eye box must stay 3x4 (near) / 2x4 (far, profile) with one skin row between the fringe and the lash.

## 9. Re-fit for the Level E FINAL head (turnE slim build, new head shape) - STATUS: PENDING
As of 2026-10-26 v2/design/NOTES.md has no FINAL Level E turnE files and no Level E pixel head master (last entry E11: front still being edited).
Targets the new head will have (v2/design/PROPORTIONS_E.json design_2d + v2/style/PROPORTIONS_REF.md, 48 px figure):
3.45 heads -> crown-chin ~14 px (now 16: rows 7-22), hair mass ~15 px wide (now 19), face 0.55 headW ~8 px (now 11), eye centre 0.66 down
the head (= crown+9; now crown+8.5), eyes 2-3 w x 3 h with 3 px between, mouth 2-3 rows under the eyes, soft-V chin in 1:1 steps over the last 3 rows, neck visible.
Exactly what to adjust when the master lands (code is ready: `faces.EYE3`, `faces.MOUTH3`, compact path in `build()`):
1. Head bases: cut each view from the master as in section 8; keep 1 clear skin row between the fringe and the lash row (brow band).
2. Eye zone: anchors `; eye_near X Y 3 3` (h=3 switches the whole build to the compact set). S view: if the face at eye level is <10 px use `w=2` for both eyes (2+3+2 = 7 px + 1 px margins); SE near 3x3 / far 2x3; E profile 2x3, 1 px behind the front outline.
   EYE3 = EYE minus the bottom row (joy keeps its arc rows 2-4; pain/surprised have explicit 3-row stamps). Glint stays upper-outer; lash wing col 0.
3. Mouth / chin: anchor `; mouth X Y` = left px of a 3-wide stamp on the row 2 above the chin tip; MOUTH3 is 3 w x 2 h and must keep >=1 skin row above the chin outline (open mouths shout/joy/surprised/effort use both rows; closed mouths 1 row). SE: same stamp shifted 1 px toward the facing side; E: re-cut the lip notch on the new profile and re-anchor MOUTH_P (col 2 = notched outline).
4. Blush: `; blush X Y 1` (1 px per cheek on the row under the outer eye corner; the 2 px version will not fit an 8 px face).
5. Squash: `; squash_row` = a skull row above the brow band on the new head; NE/N `; cheek` on the new cheek sliver.
6. Then rebuild (`build_all.py`, `make_sheet.py`, `final_sheet.py`) and re-check at 1x: determined vs blink_half and smile vs neutral are the pairs most at risk at 3-row eyes (keep the V-brow tick and the blush).
