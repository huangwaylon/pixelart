# RESULTS: Pokemon-trainer pixel style overhaul (STYLE strand), 2026-10-26

**Status: the style rules are set. No master is LOCKED.** The lead put a HOLD after the user said "ours looks fat and awkward". The proportion data for the design strand is in PROPORTIONS_REF.md. Masters will be redone on top of the re-proportioned 3D model.

## What "Pokemon trainer pixel art" is (measured; full table in STYLE_GUIDE.md section 1, board refs_board.png)
- **Gen3 overworld:** 16x32 frames, figure about 20 px tall, 1.7 heads. Black outline, 12-14 colours. Walk is step/stand/step/stand at 133 ms; run is 5/3/5/3 ticks.
- **Gen4 and Gen5 overworld:** 32x32 frames, figure about 29 px tall, 1.6 heads, with a narrow body. Black outer outline, coloured inner lines, about 15 colours, 4 directions, 4-frame walk.
- **Battle trainers (G3 64 px, G4/G5 80 px):** figure 55-75 px tall, 3.2-3.6 heads and slim. Shoulders are 0.7 and the waist 0.5 of head width, legs are 40-45% of height, and the neck is visible. Black outer outline with dark local-colour inner lines, 3-4 hue-shifted tones, a hair sheen band, low eyes. One direction only.
- **PMD:** figure 19-30 px tall, 8 directions, black outline, 12-13 colours, 2 tones plus a highlight. Animation is frame by frame with uneven holds: walk 8/12/8/12 ticks, attack mostly 2-tick frames.

## Candidates and scores (Argon / Opus, 1-10, official sprite = 9)
| candidate | r1 | r2 | r3 | r4 | final files |
|---|---|---|---|---|---|
| A PMD-40 (40 px figure, 48 cell) | 4 / 5 | 5 / 5 | - | - | tests/A_r2.txt, A_r2_6x.png |
| A' PMD-32 (32 px figure, 40 cell) | - | - | **7 / 6.5** | 5 / 6 | tests/A_r4.txt, A_r4_8x.png |
| B BW-battle-72 (72 px figure, 80 cell, chibi kept) | 2 / 3 | 5.5 / 4 | dropped | - | tests/B_r2.txt, B_r2_6x.png |
| C Hybrid-48 (BW rendering on a PMD chibi, 64 cell) | 3.5 / 5.5 | 4.5 / 6 | 5.5 / 5.5 | 4.5 / 4 | tests/C_r4.txt, C_r4_6x.png |
| A' slash, 6 frames (160/80/40/120/80/140 ms) | | | | 5.5 / 5 | tests/anim/A_slash_SE_4x.gif, _sheet.png |
Comparison boards (ours next to real sprites at the same scale): tests/board_r1.png, board_r2.png, board_r3.png and board_r4.png, each with a `_thumb`. Critiques are in crit/r{1-4}_{argon,opus}.txt.
How to read the scores: both critics scored by eye from downscaled boards, so the numbers are noisy. For example, Opus claimed in r4 that our outline was not black, but lint measures A_r4 at edge_nonK=0/99. Argon also tends to recommend coloured outer outlines, which the refs contradict.

## Findings
1. **The B variant fails.** A chibi cannot read as a battle trainer, because battle trainers are slim 3.2-3.6-head figures.
2. **PMD rendering read best.** A' scored 7/6.5 at r3. Its pure black outline, flat 2 tones plus a highlight, and compact eyes are what the critics recognise as official.
3. **C (BW shading at 48 px) stays "between styles"** at 4-6.
4. **The remaining gap is proportions, not rendering.** Both critics flag the boxy torso and missing neck in every round. The measurements confirm it: our shoulders and waist are 0.95 of head width, against 0.5-0.78 on official sprites.

## Recommendation
- **Rendering:** use the PMD rules from STYLE_GUIDE.md section 11 and the palette pk_palette.json (16 colours).
- **Proportions:** a slim trainer chibi of 3.0-3.3 heads, following PROPORTIONS_REF.md.
- **Size:** a 44-48 px figure in a 64x64 cell, with 8 PMD-order directions.
- **Animation:** draw frame by frame from the rigged 3D keys, reusing a head stamp (STYLE_GUIDE.md section 9). Timing and smear rules are in sections 8 and 11.
- **Next step:** once the design strand delivers the new proportions, redraw the SE master and lock it together with a separate head/face stamp char-map. Then fan out S, E, NE and N, plus the katana versions, as parallel Opus calls with 2 per account.

## Tools
- tools/pk.py: snap, render and lint (colours, orphans, edge_nonK).
- tools/board.py, tools/gif.py, tools/ruler.py, tools/prof.py, tools/propoverlay.py.
