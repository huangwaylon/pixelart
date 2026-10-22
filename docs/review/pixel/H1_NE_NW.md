# H1_B_final pixel review: NE / NW (back 3/4), jump f1-f12

Reviewer: pixel-NENW. All edits are overrides in `overrides/variants/H1_B_final/jump/{NE,NW}/NN.json` (with reasons). Verified with `--preview` (`out/variants/H1_B_final/pixelreview/fixed/NE_*.png`, `NW_*.png`). Coordinates are (x,y) in the 48x48 cell. Silhouettes were left as they are, apart from 1px outline-corner cleanups. NE and NW are not pixel mirrors: the 3D hair parting, scarf tail and fixed upper-left light all differ between them. Mirror checks therefore cover structure (boots, nape, pom, cheek, outline) and not shading.

Total: 139 px (NE 78, NW 61). 24 of 24 frames touched, 0 approved as generated.

## NE
- NE f1: 6 px fixed. Boots: (21-23,40) mauve to hair_1 and (24-25,41) mauve to plum_0. The cuff filled the ground row, so the boots read as a lilac blob; now each boot has a 1-row cuff with leather below and the darkest tone on the ground row. Hair: (19,25) hair_2 to hair_1, removing a detached drip under the highlight band.
- NE f2: 9 px fixed. Nape: (23-25,31) and (25-27,32) skin_1 to skin_0, to unify the nape value. Hair: (18,27) hair_1 to hair_2, closing a 1px pocket in the highlight band. Outline: (19,21) to red_2 and (18,31) to char_1, both doubled corners on the hat contour and shoulder stair.
- NE f3: 5 px fixed. Pom: (20,12), (19,13), (20,13) oat_2 to oat_1. The pom highlight blinked f3 on, f4 off, f5 on, f6 off; with it removed, NE matches NW, which has no pom highlight in f3-f6. Scarf: (25,30) to red_1, because the tail was 1px wide mid-strip; it now matches f4's 2px stair. Outline: (18,27) to hair_1, a doubled corner at the bob/neck pinch.
- NE f4: 1 px fixed. Outline: (18,27) to hair_1, the same neck-pinch doubled corner as f3, mirrored in NW.
- NE f5: 12 px fixed. Nape: (21-24,28) and (23-25,29) skin_1 to skin_0. Pom: (20,13), (19,14), (20,14) oat_2 to oat_1, for the anti-blink reason in f3. Hair: (16,23) to hair_2, closing a pocket in the band. Outline: (16,17) to red_1, a doubled corner on the hat dome, mirrored in NW f5.
- NE f6: 7 px fixed. Nape: (21-25,28) and (23-24,29) skin_1 to skin_0.
- NE f7: 5 px fixed. Nape: (21-23,28) to skin_0. Hair: (17,23) to hair_2, closing a band pocket. Outline: (17,26) to hair_1, a doubled corner on the bob's lower-left curve.
- NE f8: 7 px fixed. Cheek: (31,20-22) skin_1 to hair_1. The skin sliver appears only in this NE frame (flicker), and back views have no face. Shoulder: (18-19,28-29) ink to char_1. That dark 2x2 sat between lav_1-lit shoulders in f7 and f9, so it flickered and read as a hole.
- NE f9: 5 px fixed. Nape: (26-27,31-32) to skin_0. Outline: (19,29) to hair_1, a doubled corner at the neck pinch, mirrored in NW f9.
- NE f10: 9 px fixed. Nape: (20-23,27) and (23-25,28) to skin_0. Boot: (21-22,40) oat_2 to hair_1, because the left boot was cuff all the way to the ground.
- NE f11: 5 px fixed. Boot: (24-25,41) oat_2 to plum_0, a cream cuff on the ground row. Pom: (22,10), (21,11), (22,11) to oat_2. The highlight was missing only in this frame, between f10 and f12.
- NE f12: 7 px fixed. Nape: (20-22,28) to skin_0. Boot: (21-23,40) oat_2 to hair_1, where the left boot was a cream/mauve checker down to the ground. Outline: (28,29) to red_1, a doubled corner where the bob meets the scarf; NW's mirror is already a clean diagonal.

## NW
- NW f1: 5 px fixed. Cheek: (14,21), (14-15,22), (14-15,23) skin_1 to hair_2. The cheek sliver came and went across NW frames, never appears in NE, and back views have no face. The side lock now continues the lit bob band.
- NW f2: 4 px fixed. Boot: (22-23,41) mauve to hair_1, putting leather on the ground row to match NE f2's all-plum sole. Outline: (28,21) to red_1 and (29,31) to char_1, doubled corners that mirror the NE f2 fixes.
- NW f3: 3 px fixed. Hair: (17,25) to hair_2, attaching a lone 1px band drip to the edge so the shape continues into f4. Scarf: (22,30) to red_1, widening a 1px mid-strip; mirrors NE f3. Outline: (29,27) to plum_0, the neck-pinch corner.
- NW f4: 2 px fixed. Scarf: (22,30) to red_1, the same 1px mid-strip as f3. Outline: (29,27) to plum_0, the neck-pinch corner.
- NW f5: 7 px fixed. Cheek: (16,21-23) to hair_2. Hair: (19-20,23) and (19,25) to hair_2, closing a 2px dark pocket and a notch inside the highlight band. Outline: (31,17) to red_1, the hat-dome corner that mirrors NE f5.
- NW f6: 1 px fixed. (29,27) char_1 to plum_0: a 1px coat spike poked up between two hair locks and read as a speck.
- NW f7: 3 px fixed. Hair: (19-20,23) to hair_2, the same band pocket as f5. Outline: (30,26) to plum_0, the bob-curve corner that mirrors NE f7.
- NW f8: 4 px fixed. Cheek: (16,20) to hair_1 and (16,21-22) to hair_2, which pairs with the NE f8 fix. Outline: (16,29) to red_1, a doubled corner on the arm/scarf contour.
- NW f9: 13 px fixed. Cheek: (12-13,26) and (13,27-28) to hair_2. Nape: (20-21,31) and (17-21,32) skin_1 to skin_0; this was the only skin_1 nape in NW. Hair: (19,27) to hair_2, a band notch. Outline: (28,29) to plum_0, the neck-pinch corner that mirrors NE f9.
- NW f10: 8 px fixed. Cheek: (15,21-23) to hair_2. Hair: (16,25) to hair_2, attaching a band drip to the edge. Pom: (24,12), (25,12), (24,13) to oat_2, because the highlight was missing only here, between f9 and f11. Outline: (18,28) to hair_1, the bob/neck corner.
- NW f11: 5 px fixed. Boot: (20-23,41) mauve to hair_1, because the left boot was cuff all the way down; it now matches NE f11 (cuff 2 rows, leather below). Hair: (20,26) hair_2 to hair_1, a detached drip under the band.
- NW f12: 6 px fixed. Cheek: (16,21) to hair_1 and (16,22-23) to hair_2. Pom: (24,8), (23,9), (24,9) to oat_2, because the highlight was missing between f11 and f1.

## Generator-level issues (recurring, with a proposed procedural fix)
1. **Cheek/ear skin leaks at the head edge in back 3/4 views.** NW f1, f5, f8, f9, f10 and f12, and NE f8, show 1px columns of skin_1 beside the hat cuff. Fix: in `face.py`/`render.py`, when the view yaw is more than about 110° from camera (NE, N, NW), replace any skin pixel that touches the head outline above the nape line with the nearest hair tone. Alternatively, extend the bob mesh 0.5 units forward at the temples.
2. **Nape tone flickers between skin_0 and skin_1.** The lit/unlit threshold sits right on the nape normal. Fix: tag the neck/nape as a "shadowed" material that always uses ramp[0] in back views. It sits under the bob, consistent with rule 7 ("shadow under brims/scarf").
3. **Boot cuff reaches the ground row** (NE f1, f10, f11, f12; NW f2, f11). From the high camera, the cuff band covers the whole visible boot. Fix: in post-process, force the lowest opaque row of every `boots`/`boot_cuff` region to boots ramp[0] or [1]. Optionally cap the cuff at 2 rows per boot.
4. **Pom highlight blinks** (NE f3-f6 and f11; NW f10 and f12). The oat_2 band appears or vanishes as the pom's normal crosses the band threshold. Fix: compute the pom highlight from a fixed screen-space light (top-left 3px L stamped on the pom's top-left), not from per-frame normals. Or lower the pom's `material_bands` threshold so it is always on.
5. **Doubled outline corners.** The outline pass leaves L-shaped corners on 1:1 and 2:1 diagonals (hat dome, bob curve, neck pinch). Fix: after outlining, delete any outline pixel that has no transparent 4-neighbour, has a transparent diagonal neighbour, and whose two outline neighbours are themselves diagonally adjacent. Fill it with the majority interior neighbour. Junctions between different parts (pom/hat, hem/leg, mitten/body) should be exempt, which an object-ID map can identify.
6. **Pockets and drips in the hair_2 highlight band** (1-2px of hair_1 inside or under the band). Fix: run a morphological close (3x3) on the highlight mask before quantising, then the existing <=2px island cleanup.
7. **Scarf tail collapses to 1px mid-strip in the rise frames** (f3 and f4). Fix: dilate the scarf mask by 1px horizontally wherever its width is 1, or raise `scarf_len` thickness at low ppu.
8. **Not fixed, noted:** in several frames the hat cuff thins to 1px under the central "smile" dip (NE f5, f6, f10). This is correct perspective but under the 2px minimum. Consider a +0.1 cuff height at ppu 0.75.
