# FACE_GUIDE2: big-eyed anime face kit for the trainer girl (FACE2 strand, 2026-10-27)

Source of truth = code: `v2/face2/tools/kit.py` (sprite stamps + `kit.build(view, expr)`), `tools/heads_e.py` (placeholder heads, hair option E), `tools/portrait.py` (40x40 portraits).
Outputs: `out/sprite/<VIEW>_<expr>.txt|_1x.png|_8x.png`, `portrait/P_<expr>.txt`, `face_kit_sheet.png` (`tools/kit_sheet.py`), `portraits_sheet.png` (`tools/portrait.py 6 portraits_sheet.png`), `anchors.json` (`tools/export.py`), `expr_map.json`.
Critiques: `crit/r1..r4_{argon,opus}.txt`. Final scores (r4): Argon sprite 8.5-9, portrait 9-9.5. Opus sprite 7-8, portrait 7.5-9. A last polish pass (r5) applied the r4 notes.

## 1. Study: how big anime eyes are built in small Japanese pixel art
Refs: `v2/style/refs/battle`, `refs/sd/` (Showdown BW-style trainer sprites, 13), `refs/fe/` (FE GBA portraits), `v2/face/refs/pmd_portrait`. Boards: `work_a.png` (trainer face crops), `work_b.png` (FE + PMD).
Sizes are measured on the char-map dumps (`v2/face/tools/dump.py`), +-1 px. For the families not fetched, the "known" values come from memory of the games and are marked (k).
| family / size | head h (crown-chin) | eye w x h | eye h / head h | construction |
|---|---|---|---|---|
| BW/B2W2 battle (Hilda, Rosa, Lillie/Serena SD) | 16-19 | 2-3 x 2-4 | 0.15-0.2 | 1 K lash row (2 px at the outer wing), iris 1-2 px colour, 1 W on the outer side as sclera+glint, no lower line; brows hidden by fringe/hat |
| HGSS/DPPt battle (Lyra, Dawn, Kris) | 16-18 | 1-3 x 2-3 | ~0.15 | as BW; Kris = 3x2 `KWK` over `SWc` |
| Gen3 battle (May) | 15-16 | 2 x 2-3 | ~0.17 | K outline round the iris, 1 W glint |
| PMD portraits 40x40 (Meloetta, Gardevoir) | ~26-30 (face fills frame) | 5-6 x 7-8 | 0.25-0.3 | heavy K lash with wing, 2x2 W glint upper-left + 1 small lower glint, dark iris top -> light bottom, dark outline round the iris; brows = the expression lever; D-shaped open mouth (dark interior + pink tongue); diagonal blush hatch; effect marks in empty corners |
| FE GBA portraits 96x80 (Lyn, Eirika, Florina, Ninian) | ~36 | 6-7 x 5-6 | ~0.17 | thick dark upper lid (2 px) with flick, iris dark top / light bottom, 1-2 W glints, thin lower lid line in dark skin; nose = 1-2 px shadow; small mouth 3-4 px |
| Rune Factory / Story of Seasons DS (k) | sprite head ~12-14 of a 32 px figure | 2 x 3 sprite; portrait 6-8 x 8-10 | sprite ~0.25 | big-head chibi; sprite eye = K lash + 1 W; portraits = tall oval iris with 2 glints, blush hatch, tiny or no nose |
| Atelier DS / Mother 3 / Tales (k) | 10-16 | 1-3 x 2-4 | 0.2-0.25 | Atelier: tall 2x3 eyes with W glint; Mother 3: dot eyes (not "anime"); Tales (SNES): 2x3 eyes with lash row, high on the face |
| Doujin chibi dot (k) | 14-18 | 3-4 x 4-5 | 0.28-0.33 | tall eyes, lash + wing, 1-2 glints, gradient bottom, 1 px blush, mouth 1-2 px, no nose. This is the reference we chose for the size. |
Takeaways used: (1) eye height ~1/3 of the head (doujin/PMD level, about 2x a battle sprite); (2) the eye is **taller than wide**; (3) the upper lash is the heaviest line, 2 px at the outer corner, with a 1 px wing; (4) glint upper-outer, a second small glint lower-inner; (5) the iris goes darker at the top and lighter at the bottom, kept *inside* the eye (a light pixel below the eye reads as a tear); (6) no nose on the sprite, and only a 1 px shadow on the portrait; (7) the mouth is 1-2 px closed, and open mouths are dark/pink without a K ring (a K ring reads as a goatee); (8) round cheeks with a 1:1 jaw that ends in a 2 px chin point; (9) 1 skin row between the fringe and the lash, so the lash never merges with the hair.

## 2. Head size (agreed with PROP, see prop/NOTES.md and prop/blockout/head_region.json)
Template range at 48 px: crown-chin 13.2-15.0 px, width 12.9-16.5. FACE2 uses **15 px crown-chin x 16 px wide**, the top of the range: crown at cell row 13, chin outline at row 27, neck at row 28, cols 24-39. Eye centre = 0.57 of the head (rule <= 0.66).
Size test (round 1, `work/c1.png`): 13 px fails (the mouth hits the chin, and the eyes shrink to 3x4 and read as dots next to the mouth); 15/16 px both work. The face zone needs 10 rows: brow row, 5 eye rows, cheek row, mouth row, jaw row, chin outline. With the hair above it (>= 4 rows plus the bun/bow, excluded) that gives 15.

## 3. Palette (v2/style/pk_palette.json; 16 colours, none added)
The sword is gone, so two slots are reused (the count stays 16): **n** (blade) = `#78b8f0`, the iris glow, i.e. the bottom of the lower-iris gradient i -> I -> n; **k** (katana guard) = `#f8a0a0`, the blush. e `#f87068` reads as a wound or tongue on skin at 1 px, so a softer pink is needed for blush. Face uses: K lash/pupil/silhouette, W glint/sclera/teeth, i/I/n iris, s/S skin + shadow (S also = nose, jaw underside, cheek shade), r mouth line/interior + lower lid (portrait), e tongue, k blush, h brows (on skin only).
Note for the lead: the hair illustrations (turnE_final) show grey-brown eyes. The kit keeps the palette's blue iris. Swapping i/I/n to browns changes no construction.

## 4. Sprite layouts (tile 19x22; crown row 4, chin row 18; cell = tile + (24, 9))
| view | eyes (stamp x0 = lash-wing col, brow row 9, eye rows 10-14) | mouth stamp (cheek 15 / mouth 16 / jaw 17) | blush row 15 | contour |
|---|---|---|---|---|
| S | near x0 3 (eye cols 4-6), far x0 12 mirrored (eye 9-11); 3x5 each, 2 px gap (7-8), 1 px skin margin outside each wing | x 6-9 (centre 7-8) | 3-4 (5) / 11-12 (10) | face cols 2-13; 1 px sidelock each side; jaw sides in h/S, chin = 2 K px at 7-8; row 17 skin only 7-8 with S at 6/9 (no K beside the mouth) |
| SE | near x0 6 (eye 7-9, 3x5), far x0 13 mirrored, `far()` = 2x5 (eye 11-12), 1 px gap, 1 skin px before the outline (col 15) | x 9-12 (centre 10-11, shifted to the far side); neutral/blinks = 1 px (MOUTH_SE) | near 7-8 (9) / far 13 (1 px) | far cheek bulges 1 px (K col 16) on rows 14-15; nose = 1 px S at (13,15); jaw steps near side; chin point under the far eye (K 9-11) |
| E | profile wedge x0 8 (lash flick/back corner col 8 over the hair edge, eye 9-11, 1 skin px in front) | MOUTH_E2 at x 10-12 | 9-10 | front outline K col per row: bangs 13, brow 14 (rows 9-10), eye 13, **nose 14 (row 14)**, philtrum 13, **lip notch 12 (row 16)**, **chin 13 (row 17)**, underside 10-12; ear = `KsS` cols 6-8 rows 12-14; jaw shadow S under the ear; neck 2 px |
| NE | - | - | 1 px k on the cheek sliver (14,13) | cheek sliver col 14 rows 11-14 + ear S col 13; **lash tip** = K at (16,11), and also (16,10) for surprised, poking past the outline on open-eye exprs (`NE_LASH`) |
| N | - | - | - | no face; bow + bun, broken sheen, nape locks, 2 px neck; one cell for every expression |
Hair placeholder = option E: side-swept bangs ending on row 8 (row 9 is skin), 1 px tips, a small bun + 7x7 red bow on her LEFT side-back (picture-right in S/SE, behind the head in E, picture-left in NE/N).

## 5. Exact pixel construction (stamps; '.' = keep the base, '_' = make transparent)
Eye stamp = 5 cols: c0 lash wing (outer margin), c1-3 = the 3-wide eye (c1 outer), c4 inner margin. Rows: r0 = brow row, r1-5 = eye. S right eye = horizontal mirror. Neutral reads: K lash row with a 1 px outer wing, a 2nd K at the outer corner (2 px thick), a tall 2 px W glint (c2 r2-3), a small 2nd glint lower-inner (c3 r4), and the gradient i -> I -> n with a rounded 2 px bottom.
### Sprite eye stamps (kit.EYE, near/left eye; S right eye = mirror; SE far eye = kit.far = drop col 2)
| expr | r0 brow .. r5 |
|---|---|
| neutral | `.....` `KKKK.` `.KWi.` `.iWi.` `.IIW.` `.In..` |
| cheerful | `.....` `KKKK.` `.KWi.` `.iWi.` `.In..` `.....` |
| determined | `.....` `KK...` `.KKKK` `.iWi.` `.IIW.` `.In..` |
| shout | `hh...` `..KK.` `KKKK.` `.KWi.` `.In..` `.....` |
| effort | `hh...` `.....` `.....` `KK...` `..KK.` `.....` |
| joy | `.....` `.....` `.KKK.` `K...K` `.....` `.....` |
| surprised | `.....` `KKKK.` `.WWW.` `.WKi.` `.iKi.` `.....` |
| pain | `.....` `K....` `.KK..` `...K.` `.KK..` `K....` |
| blink_half | `.....` `.....` `KKKK.` `.iii.` `.In..` `.....` |
| blink_closed | `.....` `.....` `.....` `.....` `K....` `.KKK.` |
| embarrassed | `...h.` `.....` `KKKK.` `.KWi.` `.iIW.` `.....` |

### Profile eye stamps (kit.PROF_E, 4 cols: c0 back corner/flick, c1-3 toward the FRONT)
| expr | r0 .. r5 |
|---|---|
| neutral | `K...` `.KKK` `.KWi` `..ii` `..In` `....` |
| cheerful | `K...` `.KKK` `..Wi` `..In` `....` `....` |
| determined | `..hh` `.KKK` `..KK` `..Wi` `..In` `....` |
| shout | `hh..` `..hK` `KKKK` `..Wi` `..n.` `....` |
| effort | `hh..` `....` `....` `KK..` `..KK` `....` |
| joy | `....` `....` `..KK` `.K..` `K...` `....` |
| surprised | `....` `.KKK` `.WWW` `..WK` `..iK` `....` |
| pain | `....` `....` `..K.` `...K` `..K.` `....` |
| blink_half | `....` `....` `KKKK` `..ii` `..In` `....` |
| blink_closed | `....` `....` `....` `....` `K...` `.KKK` |
| embarrassed | `...h` `....` `KKKK` `.KWi` `..IW` `....` |

### Sprite mouths (kit.MOUTH 4x3: cheek / mouth / jaw row; SE = MOUTH_SE; profile = MOUTH_E2 3x3, '_' cuts the outline)
| expr | S | SE | E |
|---|---|---|---|
| neutral | `....` `.rr.` `....` | `....` `..r.` `....` | `...` `.r.` `...` |
| cheerful | `....` `rKKr` `.ee.` | `....` `rKKr` `.ee.` | `r..` `.r.` `...` |
| determined | `....` `rrrr` `....` | `....` `rrrr` `....` | `...` `rr.` `...` |
| shout | `rrrr` `rKKr` `.ee.` | `rrrr` `rKKr` `.ee.` | `...` `rK_` `reK` |
| effort | `....` `rrrr` `r..r` | `....` `rrrr` `r..r` | `...` `rr.` `...` |
| joy | `r..r` `rKKr` `.ee.` | `r..r` `rKKr` `.ee.` | `r..` `.K_` `..K` |
| surprised | `....` `.KK.` `.rr.` | `....` `.KK.` `.rr.` | `...` `.K_` `...` |
| pain | `....` `rKKr` `....` | `....` `rKKr` `....` | `...` `rK_` `...` |
| blink_half | `....` `.rr.` `....` | `....` `..r.` `....` | `...` `.r.` `...` |
| blink_closed | `....` `.rr.` `....` | `....` `..r.` `....` | `...` `.r.` `...` |
| embarrassed | `....` `.r.r` `..r.` | `....` `.r.r` `..r.` | `...` `r.r` `...` |

### Portrait stamps (portrait.EYE 9x9 at rows 18-26, x0 10 / mirrored 29; BROW 9x3 rows 15-17, skin only; MOUTH 8x4 at x16 rows 28-31)
| expr | eye | brow | mouth |
|---|---|---|---|
| neutral | `..KKKKK..` `KKKKKKKK.` `.KWWiiiK.` `.iWWiiiW.` `.iiiKKiW.` `.iIiKKIW.` `.IIIIIW..` `..nnnn...` `.........` | `.........` `.hhhhh...` `.........` | `........` `...rr...` `........` `........` |
| cheerful | `..KKKKK..` `KKKKKKKK.` `.KWWiiiK.` `.iWWiiiW.` `.iiiKKiW.` `.iIiKKIW.` `.........` `.........` `.........` | `..hhhh...` `.h.......` `.........` | `........` `..rrrr..` `..reer..` `...rr...` |
| determined | `.........` `KKKK.....` `.KKKKKK..` `.iWWKKKK.` `.iWWiiiW.` `.iiiKKiW.` `.IIIKKIW.` `..nnnnW..` `.........` | `hh.......` `..hhh....` `.....hh..` | `........` `........` `..rrrr..` `........` |
| shout | `.........` `KKK......` `.KKKKK...` `.WWWKKKK.` `.WWiiiWW.` `.WiKKiW..` `.WIKKIW..` `..WnnW...` `.........` | `hhh......` `...hhh...` `......hh.` | `........` `..rrrr..` `.rKKKKr.` `..reer..` |
| effort | `.........` `KK.......` `.KKKK....` `.KKKKKKK.` `.iWWiiKK.` `.iiiKKiW.` `..IIIIW..` `.........` `.........` | `hh.......` `..hhh....` `.....hhh.` | `........` `.rrrrrr.` `.rWWWWr.` `..rrrr..` |
| joy | `.........` `.........` `..KKKKK..` `.KK...KK.` `KK.......` `.........` `.........` `.........` `.........` | `..hhhh...` `.h....h..` `.........` | `........` `.rrrrrr.` `..KKKK..` `...ee...` |
| surprised | `.KKKKKK..` `KKKKKKKK.` `.WWWWWWK.` `.WWiiiWW.` `.WiKKiWW.` `.WiKKiWW.` `.WWiIWW..` `..WWWW...` `.........` | `..hhhh...` `.h....h..` `.........` | `...rr...` `..rKKr..` `...rr...` `........` |
| pain | `.........` `.KK......` `...KKK...` `.....KK..` `...KKK...` `.KK......` `.........` `nn.......` `n........` | `.....hh..` `..hhh....` `hh.......` | `........` `..rrrr..` `.rKKKKr.` `........` |
| blink_half | `.........` `.........` `.........` `.........` `KKKKKKKK.` `.iiiKKiK.` `.IIIIIW..` `..nnnn...` `.........` | `.........` `.hhhhh...` `.........` | `........` `...rr...` `........` `........` |
| blink_closed | `.........` `.........` `.........` `.........` `KK.......` `.KK....K.` `..KKKKK..` `.........` `.........` | `.........` `.hhhhh...` `.........` | `........` `...rr...` `........` `........` |
| embarrassed | `.........` `.........` `KKKKKKKK.` `.KWWiiiK.` `.iWWiKKW.` `.IIIiKKW.` `..nnnn...` `.........` `W........` | `.....hh..` `..hhh....` `.........` | `........` `...r.r..` `..r.r...` `........` |

Blush (k, sprite cheek row): cheerful=2px, joy=2px, shout=1px, effort=1px, pain=1px, embarrassed=3px; embarrassed S = `kek` per cheek. Portrait blush BL[n] at rows 26-27 x10-13 / x26-29: 1: .... kkkk; 2: kkkk kkkk; 3: ekek keke

### What changes per expression (1x read)
- **neutral**: full 3x5 eye, the glints, 1 px-row 2 px mouth.
- **cheerful**: bottom eye row dropped (cheeks pushed up) + open D mouth `rKKr/.ee.` + 2 px blush.
- **determined**: lash slants down toward the nose (`KK...` over `.KKKK`), the top iris row is hidden, and the mouth is a flat 4 px line. No brow px: they formed a T-bar with the bang tip.
- **shout**: 2 px brow slanting down-in, with the lid under it. Open mouth 3 rows `rrrr/rKKr/.ee.` (r rim, no K ring) + 1 px blush.
- **effort**: eyes squeezed to `\_` lines + 2 px brow with a skin gap, grimace `rrrr/r..r`.
- **joy**: closed arcs over 5 px (`.KKK.` / `K...K`) + a wide grin with the corners up `r..r/rKKr/.ee.` + blush.
- **surprised**: W ring with a K 1x2 pupil and blue iris beside it, a glint on the pupil's top-left, the lash kept on r1 (raising it merges with the fringe), and an `o` mouth `.KK./.rr.`.
- **pain**: `>` `<` chevrons spanning the wing col + open grimace `rKKr` + 1 px blush. Portrait adds a sweat drop.
- **blink_half**: lash on r2 + 2 iris rows. **blink_closed**: low curve `K....`/`.KKK.` (the lash weight is kept).
- **embarrassed**: lid lowered 1 row, iris shifted down, inner brow px, `kek` blush (3 px), zigzag mouth `.r.r/..r.`.

### Edits that turn one expression into the next (1-4 px)
neutral -> cheerful: delete the eye's bottom row (2 px per eye), fill the mouth to `rKKr/.ee.`, +2 px blush per cheek. cheerful -> joy: the eye becomes an arc and the mouth corners go up. neutral -> determined: the lash steps down 1 row toward the nose and the mouth goes flat. determined -> shout: brow px join and the mouth opens 3 rows. neutral -> blink_half -> blink_closed: the lash moves down 1 row, then to the bottom curve.

## 6. Portraits (PMD 40x40, `portrait/P_<expr>.txt`)
The base is built in `portrait.base()`: face skin rows 12-33, sides at col 9 down to row 24, then the jaw tapers 1,1,1,3,2,1,1 to a 2 px chin at row 33 with a K line under it. Bangs are 5 pointed locks (`LOCKS`, edge rises 1 px per px from each tip), with tips <= row 17 and an h line at each valley. Sidelocks taper and frame the jaw. A broken L angel ring sits on rows 3-7. The bun + 10x10 bow sit on her left side-back, fully in frame (top right). Back hair falls behind the red kimono V collar (R fold px).
Eyes: 7 wide x 8 tall (`.KKKKKK..` top + `KKKKKKKK.` = 2 px upper lash with the outer wing), a 2x2 W glint upper-outer, a 1 px W sclera column inner, a 2x2 K pupil, the gradient i -> I -> n inside the eye, a rounded bottom `..InnI...`, and no lower-lid pixel (it read as eye bags). Gap between the eyes = 4 px (cols 18-21). Nose = 1 px S (20,27). Brows (h) are drawn only on skin, so the bangs hide them in neutral.
Effects: pain/embarrassed sweat drop (top-left, W/n/K), shout cross-vein anger mark (5x5 E), surprised `!` marks.
PMD slot mapping: see `expr_map.json` -> `portrait_slots`.

## 7. Fitting onto the masters (MASTERS-F) and the final hair
1. Draw the hair; keep the face zone as plain skin. That is cols 26-37 (S), the brow row 18 is skin, eyes on rows 19-23, the cheek row 24, mouth 25, jaw 26, chin outline 27 (2 px K point). Hair must end on cell row 17 over the eyes.
2. Stamp with `kit.build`, or copy from `out/sprite/<VIEW>_<expr>.txt` (tile -> cell offset +24,+9). Anchors are in `anchors.json`.
3. If the master head is 1 px narrower: drop the 1 px skin margin outside the S wings (keep the 2 px gap); never go below 3x5 for the near eye or 2x5 for the far eye.
4. W/SW/NW: mirror the E/SE/NE face stamps; the bow/bun does NOT mirror (her left side).
