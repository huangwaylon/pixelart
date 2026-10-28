# STYLE strand NOTES (Pokemon-trainer pixel style overhaul), 2026-10-26

## Step 1: research access
- Spriters Resource / Bulbapedia / Bulbagarden Archives: Cloudflare challenge (403) even though allowlisted -> unusable from curl.
- Added to allowlist (user approved): play.pokemonshowdown.com, essentialsdocs.fandom.com (also CF 403), www.pokecommunity.com, eeveeexpo.com (empty pages to curl).
- Usable primary sources: pret decomps on GitHub (pokeemerald/pokefirered graphics + anim tables; pokeplatinum tree), Showdown trainer sprites (official battle pics G3/G4/G5, 80x80), PMDCollab SpriteCollab (PMD sheets + AnimData.xml timings), FloofyPanthar Essentials Gen5 kit (BW-style overworlds, Essentials charset layout).
- Hard data pulled:
  - Gen3 OW: frame 16x32 (2x4 tiles), character ~20 px tall, 12-14 colours, black #000000 outline. Walk anim (pokeemerald object_event_anims.h): step/stand/step/stand at 8 ticks each (60 Hz) = 133 ms; fast walk 4 ticks; run anim 5/3/5/3 ticks with dedicated run frames.
  - Battle trainers (Showdown 80x80; Emerald 64x64): 14-15 colours (4bpp limit), 55 px (G3) / 65-69 px (G4) / 65-75 px (G5) tall, 3.2-3.6 heads (measured later; first estimate "5-6" was wrong), pure black outline + dark coloured inner lines.
  - G5 OW (Essentials kit, stored 2x): native ~29 px tall in 32x32 cell, ~2.2 heads, 14-15 colours, black outline.
  - PMD (SpriteCollab): Walk frame 24x40 / 24x48, characters 19-29 px tall, 12-13 colours, black outline; 8 direction rows (S,SE,E,NE,N,NW,W,SW); Walk 4 f durations 8/12/8/12 ticks; Attack 10-13 f mostly 2-tick frames; Idle 7 f (6/12/12/20/12/12/6); Hurt 2 f (2/8).
## Step 2: refs
- refs/{gen3,gen5,battle,pmd}/ (gen4 overworld not obtainable as files; the Essentials kit NPC_10 is DPPt/HGSS-style and is filed under gen5/).
- Board: refs_board.png (1600x1656), refs_board_thumb.png.
- Lead update: user wants Battle-trainer sprites + Mystery Dungeon style; priority over overworld.
## Step 3: STYLE_GUIDE.md v1 written (research table, 3 candidates, palette pk_palette.json, rules, timing, animation method)
## Step 4 r1: style tests
- Gemini concepts work/g{A_pmd40,B_bw72,C_hyb48}_1.png -> auto snap (tools/pk.py snap) work/{A1,B1,C1}.txt: mushy (lost iris, muddy skin), useful only as guides.
- Opus pixel artist (nsystem4) hand char-maps: tests/{A,B,C}_r1.txt/.png/_6x.png; board tests/board_r1.png (+thumb).
## Step 5 r1 critique (crit/r1_argon.txt, crit/r1_opus.txt)
- Argon: A 4, B 2, C 3.5 (best base A). Opus: A 5, B 3, C 5.5 (best base C).
- Both: B fails because BW battle trainers are much taller and slimmer (critics said 5-6 heads; measured 3.2-3.6); a 2.4-head chibi cannot read as one. Shared faults: black inner lines, 2 flat tones without clear light, helmet hair with one stripe, pale generic eyes, boxy jaw, stiff frontal pose (reads S not SE).
- Argon's "hue-shifted outer outline" advice rejected (refs measured pure #000000).
- Guide section 10 (R1-R6) + palette v2 (darker iris) added.
## r2 (tests/*_r2*, board tests/board_r2.png; crit/r2_*.txt)
- Argon: A 5, C 4.5, B 5.5 (best for action: A shrunk to ~32 px). Opus: A 5, C 6, B 4 (best for action: C; A too small for the sword in slash frames, B wrong proportions + 3x cost).
- Decision: iterate C (Opus + lead hypothesis). Palette v3: hair sheen L brightened to #847078 (both critics: hair highlight too close to base).
## r3 (tests/C_r3*, tests/A_r3* = A' PMD-true 32 px in 40x40; board tests/board_r3.png; crit/r3_*.txt)
- Argon: C 5.5, A' 7.0. Opus: C 5.5, A' 6.5. Both now pick A' (PMD-32) as the master for the 8-dir action set (pixel density matches PMD, cheaper, less frame-to-frame boiling); C kept for portrait/battle use.
- Next: A' r4 + 6-frame slash GIF (one Opus session), C r4 in parallel for a fair final comparison.
## r4 (tests/A_r4*, tests/C_r4*; anim test tests/anim/A_slash_SE_4x.gif + _sheet.png, 6 f 160/80/40/120/80/140 ms)
- Run on be_system + bni_requests in parallel (2 concurrent calls worked).
- USER FEEDBACK via lead: ours "fat and awkward"; Pokemon ones graceful/skinnier. HOLD: no LOCKED master, no direction fan-out until the design strand re-proportions.
## Proportion study -> PROPORTIONS_REF.md + prop/proportions_overlay.png
- Battle trainers measured 3.2-3.6 heads (my earlier "5-6" was wrong, corrected), shoulders 0.65-0.78 / waist 0.45-0.6 of head width, legs 40-45%, neck visible, eye centre 0.61-0.68 down head.
- Ours: 2.2-2.3 heads, shoulders AND waist 0.94-0.96 of head width (main "fat" cause), legs 21-23%, no neck, eyes high (0.58).
- Size advice: slim 3.0-3.3-head figure needs 44-48 px (64 cell) for the face; 40 px minimum; 32 px only works for the 1.7-head overworld recipe.
## r4 critique (crit/r4_*.txt): Argon A' 5, C 4.5, slash 5.5; Opus A' 6, C 4, slash 5. Opus "outline not black" claim false (lint edge_nonK=0/99, added to pk.py lint).
## Step 6: RESULTS.md written; STYLE_GUIDE.md section 11 (recommendation + slash fixes). No LOCKED (HOLD from lead).
