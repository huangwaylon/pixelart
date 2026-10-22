# H1_B_final jump: AD cross-check sign-off

**Verdict: SIGNED OFF, after the AD-xcheck overrides.** releases/H1_v1 predates them and must be re-cut (I did not build).

## AD fixes (174 px, logged)
- Hat-cuff mauve to oat_1 in squash frames: S f8/11, SE f2, E f2/8/9, NE f4, W f2/8/9, SW f2 (44). Only S f2 had been fixed.
- Coat lav_1 to char_1: E f9, NE f2-5/7/9/11 (50). It blinked.
- N nape to skin_0, matching NE/NW (48).
- Pom highlight: NE f3/5 removal reverted; added to NE f4/6, S f1, E f12, SW f10 (20).
- W f11/12 rear-boot sole (4). SE/SW: far-eye catchlights (f8/12) and mouths touching the eye (f11/12) removed (8).

## Locked rules
1. Front/3/4 eye: 2x3, catchlight top-left, near eye only. Far eye: dark edge mark, no catchlight.
2. Profile eye: 1x2 column, 1 px nose in front, 1 row below cuff. Catchlight on back side, mirrored E/W. No catchlight when determined or squint.
3. Mouth: 1 row below eye, touching no eye, scarf or outline. Otherwise omitted.
4. Hat cuff: oat_1 with oat_2, unbroken, no mauve.
5. Pom: 3 px oat_2 at top-left when lit. Off only on the shadow half (NW/W/SW f3-5).
6. Boot ground row: hair_1 (lit) or plum_0 (shadow).
7. Nape and chin row: skin_0.
8. Coat: char_1 plus ink, no lav_1.

## Generator fixes, by pixels saved
1. Back-view skin (nape material, temple/cheek leak): ~119
2. Profile eye clamp and pattern (face.py): ~81
3. Drop coat lav_1 islands: ~70
4. Reserve boot ground rows: ~69
5. Hat-cuff close, no mauve (includes S temple G1): ~65
6. Screen-space pom highlight: ~49
7. Min 2 px mitten/scarf/cuff, plus separators: ~38
8. Face clearance (mouth, catchlight, jaw): ~30
9. Outline cleanup: ~25
10. hair_2 band close: ~10
