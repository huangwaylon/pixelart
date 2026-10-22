# r5 Panel: Game Director

Baseline: a 1170x2532 phone at 460 ppi. Tiles scale with the character (32x16, 48x24, 64x32, 80x40). Memory is RGBA8 for 8 dirs x 12 frames x 15 animations, including extrusion. Hours are my estimates.

| | R1 32x40 | **R2 48x48** | R3 64x64 | R4 80x80 |
|---|---|---|---|---|
| Height (QA) | 27 px | **36 px** | 47 px | 62 px (QA fail) |
| Phone scale | x6 / x8 | **x4 / x5** | x3 / x4 | x2 / x3 |
| On screen | 8.9 / 11.9 mm | **8.0 / 9.9 mm** | 7.8 / 10.4 mm | 6.8 / 10.3 mm |
| Tiles across, portrait | 6.1 / 4.6 | **6.1 / 4.9** | 6.1 / 4.6 | 7.3 / 4.9 |
| Tiles across, landscape | 13.2 / 9.9 | **13.2 / 10.6** | 13.2 / 9.9 | 15.8 / 10.6 |
| Face | 1 px eyes | **eyes and brows read** | dot eyes | tiny at x2 |
| Memory | 8.7 MB | **14.9 MB** | 25.4 MB | 38.8 MB |
| Cleanup per animation | ~5 h | **~8 h** | ~14 h | ~26 h |

**Resolution: R2.** 48x48 cell, pivot (24,40). Scale x4 in portrait, x5 in landscape, x6-x8 on tablet.

With tiles scaling, every option shows the same play area at a 9-10 mm hero, so R3/R4 pixels add no gameplay. R1 loses expression, and R4 fails QA at 3x the cost. R2 has:
- the finest integer zoom steps (about 2 mm each),
- the clearest face per screen pixel,
- about 60% of R3's memory and cleanup cost.

This supersedes the kickoff 64x64/x3 spec. The `z_px` apex goes from 22 to 17.

**Proportion: A (2.5 heads).** This overrides the designer's B. At 36 px, B's body gets about 16 px. In SE, NE and N it turns into a hat-ball, and facing depends on a 2 px face. A's leg split and leading arm show facing in all 8 directions. E stays as a costume. C and D are dropped.

**Outfit: O1** (charcoal parka, red beanie, cream trims). The pom gets its own ramp (oat/mauve).
- **Value does the work.** Charcoal against white snow (luma 232) and blue shadow snow is the biggest contrast on the board.
- **Colour-blind safe.** Protan and deutan players see the red as dark brown, which still stands off the snow.
- **Rejected:**
  - O4 is a red-green pair.
  - O6 has low value against snow.
  - O2's navy matches shadowed snow, so it stays an alt costume.
- **Required:**
  - `scarf_len` that scales with the torso.
  - Hat luma 205 or lower.
  - A greyscale snow check on every build.
