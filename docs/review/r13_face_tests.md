# r13 face construction tests (lead pixel artist)

Sources: `art/hand/S4/face_tests/{A_gba,B_ds_moe,C_dote}.pix`. Renders: `00_REVIEW/r13_anime_pixel/face_tests/` (`*_x6.png`, `compare_x4.png`, `compare_x1.png`).
All three are 80x80, 3/4 view facing left, gentle closed smile. They share one hair, bow and body block so only the face changes. Each went through block-in, flats, lines, shading and features, then 3-4 view-and-fix passes. The only orphan pixels left are deliberate ones (catchlights, nose, mouth corners, buttons).

| | A: GBA portrait | B: DS / moe | C: dot-e (mine) |
|---|---|---|---|
| Outline | K (#241628) everywhere | coloured: hair plum, skin line_skin, teal_0, oat_0 | K outside, plum/line_skin inside |
| Near eye | 8x8, iris 5x6 | 10x10, iris 6x8 | 9x10, iris 6x7, no outer sclera |
| Far eye | 7x8, iris 5x6 | 8x10, iris 5x8 | 8x10, iris 5x7 |
| Catchlights | 1 (1px) | 2 (2x2 + 1px) | 2 (2x2 + 1px) |
| Face | longer, chin y51 | round, short, chin y51 | same as B |
| Brows | hair_1 dashes | line_skin, mostly hidden | line_skin, mostly hidden |
| Blush | 2x4 skin_mid | 2-row skin_mid/skin_0 | red_2 + skin_0 oval |
| Mouth | 1-3-1 crn_1 | 1-3-1 line_skin | small ":3" curve |

- **A**: crisp and sturdy, but small eyes and a long face make her look older and plainer. It suits a field sprite more than a cute heroine.
- **B**: the softest and most moe. Coloured outlines make the silhouette go muddy at x1.
- **C**: B's eyes and face, plus droopy outer lashes (gentle, cute) and a dark exterior outline, so she still reads at x1. Blush and mouth are the most legible at small sizes.

**Recommendation: C** for busts and cut-scenes. Take A's 1-px catchlight rule for sprites under 48 px. Next: the 10 expression patches on C's eye and mouth block.
