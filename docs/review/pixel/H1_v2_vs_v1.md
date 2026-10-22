# H1 v2 vs v1.1: AD verdict

**Verdict: (b) keep v1.1 this round.** Two ramp overrides regress the whole sheet, costing more than 570 hand px to fix. v2 becomes the base once fixes 1-4 land.

## Locked rules
1. Front eye: **PASS.** Catchlights match v1.1 in all 96 frames.
2. Profile eye: **PARTIAL.** Pattern is right (E f2, W f2, E f9), but the eye is one row too low (E f2 rows 30-31 vs 29-30; E f8, W f2, W f12) and touches the jaw in E f2 and W f12.
3. Mouth: **FAIL.** Missing in S f11/f12 (v1.1 had it at 25,28).
4. Cuff: **PARTIAL.** No mauve, but oat_2 is the base (N f2: 29 vs 4 px), a white stripe. Band ends are broken (SW f11 rows 20-22, E f8 row 20).
5. Pom: **PARTIAL.** Stable, but the highlight is 5 px, adds mauve, and stays lit in NW/W/SW f3-5.
6. Boots: **FAIL.** Cuff colour on the ground row in N f2, W f9, NE f11, NW f11, SW f5/f8/f12.
7. Nape/chin: **PARTIAL.** Chin is better (W f12, SE f6), but the nape is gone (0 skin_0 px in N/NE/NW), and the E f2 chin is skin_1.
8. Coat: **PARTIAL.** No lav_1, but ink is the mid-tone (NW 55-73 px per frame vs 10-19), and char_1 is 0 in W f2 and SW f2/f9.

Also regressed: double jaw outlines (SW f11, W f12, E f9) and lost sideburns in S f2.

Improved: zero hand px, 0 orphans, the pom is stable, and the cuff has no mauve in squash frames (the v1.1 release still has it in N f3/f4).

## Generator changes, ranked
1. **Coat ramp:** [ink, char_1, char_1]. Ink for the shadow band only.
2. **Cuff ramp:** [oat_1, oat_1, oat_2]. cuff_continuity closes the band outline to outline and covers temples.
3. **grounded_soles:** run post-outline on final colours. The lowest non-outline pixel of each foot column must be hair_1 (lit) or plum_0 (shadow).
4. **backview_skin:** keep a 1-row skin_0 nape in N/NE/NW. Apply chin_shadow in E/W.
5. **Profile eye:** eye top = cuff bottom + 2, at least 1 px clear of the jaw.
6. **Mouth:** 1 row under the eyes, not 2. Omit it only on contact.
7. **pom_cel:** exact 3 px oat_2 highlight on an oat_1 body, no mauve. Off in NW/W/SW f3-5.
8. **outline_notches:** never create adjacent outline pixels.

## Round 2: v2.1 (all 8 changes in)

**Verdict: (a) adopt v2.1 as the H1 base.** The coat, cuff, nape and pom are fixed. 254 px of AD-v2 overrides are written; v1.1 needed 570.

### Locked rules, judged on the raw generator output
1. **PASS.**
2. **FAIL.** The column sits 1 px too far forward, so it merges with the front outline (E/W f1, f5, f7, f11). The squint eye climbs into the cuff (E/W f10). In the smile, the catchlight sits on top of the eye (E/W f12).
3. **PARTIAL.** Omitting the mouth on contact is now correct (S f2/f9, SE/SW f1). But SE/SW f3-6 lost the joyful mouth, and S f3/f4 moved it up until it touches the eye diagonally.
4. **PASS.** oat_1 base, closed band, temples covered.
5. **PARTIAL.** 3 px highlight, no mauve. But the "right of head centre" test also turns the highlight off in W f1/f6/f10-12, NW f6/f10/f11, SW f6/f10/f11 and SE/E/NE f9.
6. **PARTIAL.** Cuff colour is still on the ground row in N f2/f9, W f10-12, SW f1/f3/f8/f11/f12, NE f8 and S f3.
7. **PASS.** One gap: the far-cheek chin in SW f6/f7.
8. **PASS.** Ink and char_1 counts are back at v1.1 levels.

New regression: the 3/4 near-cheek outline is doubled (SE and SW, f2-12).

### Hand fixes written (author AD-v2, no build run)
- Faces: 156 px, restoring the v1.1 pixels in E/W f1-7 and f9-12, SE f2-12, SW f2-4 and f6-12, and S f3/f4/f6.
- Boot soles: 54 px.
- Pom highlight: 40 px.
- Chin row: 4 px (SW f6/f7).

QA check: no new 1 px islands that v1.1 doesn't also have. SE f3-5 pom is left unlit on purpose: only a sliver shows behind the hat.

### Next generator changes (each removes its overrides)
1. Profile eye x = front outline - 2, giving exactly 1 nose px. Put the catchlight on the column's back side, on its top row, and keep the squint below the cuff + 1.
2. Joyful mouth: 2x2, with one clear row below the eye and no diagonal contact. Never omit it in SE/SW f3-6.
3. Find and remove whatever pass turns near-cheek skin into outline in 3/4 views.
4. grounded_soles: match by colour, so it fires even when the whole lower boot is cuff colour.
5. Pom lighting: use the rule table (off only in NW/W/SW f3-5), not the position test.

## Round 3: v2.2

**Verdict: keep v2.2 as the base.** 170 hand px remain (v1.1 570, v2.1 254). All 26 stale frames were resolved and approved by AD-v2. No build was run. The resolved override set adds no new 1 px islands.

### The 5 changes, judged on the base
1. **Profile eye: FAIL.** E f1-7/f11-12 and W f2-5/f7 have unchanged base hashes, so the new path never ran there. E/W f12 still has the catchlight on top of the eye. The eye still merges with the outline in E f7, W f1 and W f11. The squint sits at cuff + 1 in E/W f9. The squint is correct only in E/W f10, and v1.1 was kept there for consistency.
2. **Joyful mouth: PARTIAL.** S f3/f4 are fixed. Still wrong:
   - SE f3/f4: 1 px mouth.
   - SE f6: mouth omitted.
   - SW f3/f4: an extra pixel on the chin row.
   - S f6: mouth on the chin row, touching the scarf.
3. **Far eye: PASS.** The free mark 1 px inside the outline reads better than v1.1's merged bump. I dropped my cheek px in SE f3/4/7/8/12 and SW f2/3/4/6/7.
4. **Soles: FAIL.** Not a single sole override was pruned: N f2/f9, NE f8, S f3, W f10-12, SW f1/3/8/11/12.
5. **Pom: PASS.** The highlight is off only in NW/W/SW f3-5, plus the occluded S f4 and SE f3-5. No pom px remain.

### Stale frames
- **Doubled features removed** (the base pixel set back to v1.1): eye in E f9/f10 and W f9/f10; mouth in S f6 (23-24,29) and SW f3/f4/f6 (row 28).
- **Reverted:**
  - Far-eye px in SE f3/4/7/8/12 and SW f2/3/4/6/7.
  - The pom in SE f9.
- **Sole fixes:** stray oat_2 in SW f3/f8/f12.
- **Approved:** the rest.

### Remaining hand px: 170
| Group | px | Frames |
|---|---|---|
| E/W profile faces | 79 | f1-7, f9-12 |
| SE/SW/S joyful mouths | 34 | SE f3-6, SW f3/4/6/7, S f6 |
| Soles | 57 | see change 4 |

### Next generator changes
1. Route every E/W frame through the profile path, even when one eye is near-profile. The eye column is front outline - 2. Put the catchlight at column - 1 on the column's top row. Squint top = cuff bottom + 2.
2. Make grounded_soles fire per foot. If the lowest non-outline pixel is mauve or oat, make it hair_1 (lit) or plum_0 (shadow).
3. Mouth: if the row under the eyes touches the chin row or the scarf, shift one row up, never down. Never draw a 1 px joyful mouth.

## Round 4: v2.3

**Verdict: adopt v2.3. Art-side ship-ready once a `--release` build applies the 100 hand px below, and I check its contact sheet.** No build was run. All 22 stale frames were resolved and approved by AD-v2. The resolved override set adds no new 1 px islands and leaves no cuff colour on any ground row.

### The 3 changes, judged on the base
1. **Profile eye: PARTIAL.** E f7 now matches v1.1 exactly. Still wrong:
   - E/W f1, f10 and f12 put the eye directly under the cuff, with no skin row.
   - E/W f9 squint is still at cuff + 1.
   - The joyful ^ in E/W f3-6 is 2 px; v1.1 has 3.

   Where the base drew a second eye next to the kept v1.1 eye, I set the base pixels back to v1.1 (E/W f1, f10, f12).
2. **Soles: PASS.** N f2/f9 and W f10 need no hand px. Soles also dropped px in S f3, SW f3/f8/f12, and the cuff above a 1-row sole is accepted. Only 8 px remain (NE f8, S f3, SW f3/8/12).
3. **Mouth: FAIL.**
   - S f3: the 2-row mouth touches the eye.
   - S f6, SW f3/f4/f6: it touches the scarf or coat.
   - SE f6: still omitted.

   I restored v1.1 mouths and removed the doubled base pixels, including the scarf-end and temple pixels next to them (S f6, SW f3/f4/f6, W f10).

### Remaining hand px: 100
| Group | px | Frames |
|---|---|---|
| E/W profile eyes | 44 | f1, f3-6, f9, f10, f12 |
| E f7 collar skin_0 | 1 | |
| Joyful mouths | 47 | S f3/f6, SE f5/f6, SW f3/4/6/7 |
| Soles | 8 | NE f8, S f3, SW f3/8/12 |

My count is 100, not 88: removing doubled features added 12 px net.

Accepted as-is:
- Determined and squint mouths are omitted on contact (S f1/2/9, SE f1, SW f1), which is correct under rule 3.
- The SW f11 chin row is part skin_1: a nit, not a blocker.

### Next generator changes (not ship blockers)
1. Eye top = cuff bottom + 2. Measure the cuff bottom at the eye column after cuff_continuity, not before. The joyful ^ is 3 px.
2. A 2-row mouth may not touch the eye, scarf or coat, diagonals included. If no row fits, use a 2 px 1-row mouth. Draw it in SE f6.

## Final sign-off v2.3

**NOT SIGNED: one ship blocker.**

What is right:
- releases/H1_v2_3 is pixel-identical to the composite I approved in Round 4 (0 px difference).
- QA PASS, 0 stale overrides, 100 hand px.
- Faces, cuff, coat (no lav_1), pom and ground rows all meet the locked rules.

**Blocker: the v2.3 sole pass recolours hands and scarf.** "Any foot in the lower 40% of the sprite" plus "isolated cuff remnants join the boot" also catch the mittens and scarf ends. 45 px in 13 frames go from red/oat to hair_1, oat_2 or plum_0 (v1.1 colour, then release colour):

| Frame | Pixels |
|---|---|
| N f12 (held ready frame) | red mitten becomes an oat cuff with a brown sole (17-18, 35-37) |
| SE f7 | mitten/scarf (18-21, 30-32) becomes hair_1 |
| W f6 | scarf tail (21-24, 29-31) becomes hair_1 |
| SE f6 | (18,30-31) red to oat_2; (17,32), (18,33) to hair_1 |
| SW f6 | (15-16, 26-27) red to oat_2; (30,30), (29,31) to hair_1 |
| S f7/f8 | mitten cuff (15-16, 31) and (16,33) to hair_1 |
| SE f4 | (19-21, 28) to hair_1 |
| N f4 | (25-27, 29) to hair_1 |
| N f7 | (15,26) to plum_0 |
| NW f6 | (16,30), (17,31) to hair_1 |
| SW f5 | (29,30) to hair_1 |
| SW f7 | (28,28) to hair_1 |

The mitten reads as a boot, and it flickers between frames. I missed this in Round 4 because my checks covered only faces and the ground row.

**Fix (lead to choose; I made no change):**
- **Preferred:** limit grounded_soles and the remnant-join to the boot/boot_cuff part mask from the rig, never by colour or height alone. Then rebuild. The 100 hand px should stay valid, since none of them touch hands.
- **Stopgap:** about 45 override px restoring the v1.1 colours above, then re-cut.

**Once fixed:** re-cut and I sign without another full review. I will only diff those 13 frames against v1.1.

Last notes, not blockers:
- Single sole corner px (plum_0 or hair_1 at boot edges) are deliberate.
- The SW f11 chin row is part skin_1.

## Final sign-off v2.4 (2026-10-22)

**SIGNED (AD).** This applies to the v2.4 generator output plus the 98 hand px in 28 frames, all approved by AD-v2 with 0 left needing review. It covers the release cut only if that cut is pixel-identical to this set.

**Blocker cleared.** In all 13 frames, the red mitten/scarf px below the face are at or above v1.1 counts, and no hand or scarf is drawn in boot colours. N f12's mitten is crn_1 (shadow side), which reads correctly.

The other mitten/scarf changes are acceptable mitten-cuff or shadow tones: N f8, NW f2 and W f5-7 are oat cuffs at the wrist, and SE f7's cuff is mauve.

**Stale frames:**
- Removed the base's extra near-eye pixel that filled in the joyful ^ (SW f3/f4/f6).
- Removed the base's extra mouth px (SW f3/f4) and stray crn_1 in hair (E f4, SE f6).
- Approved all 28.

**Notes, not blockers:**
- In N f5, NW f6 and SE f4, 1-3 px of mitten tip now show at the head edge, where the old cleanup used to swallow them.
- The single sole-corner px in NE f8 and SW f3 are deliberate.
- The SW f11 chin row is part skin_1.
