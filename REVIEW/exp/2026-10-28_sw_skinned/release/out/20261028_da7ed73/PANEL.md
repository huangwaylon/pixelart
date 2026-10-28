# PANEL — build 20261028_da7ed73 (early build: 6 actions x SE/E/S, before round-4 landings)

Raw critiques: panel/ad_opus.txt, panel/anim_opus.txt, panel/game_opus.txt, panel/argon.txt.
Scores: Opus AD 5/10, Opus animation 5/10, Opus game 4/10, Argon 5/10 (AD 5 / anim 5 / game 6).

## Summary
Early build (SE/E/S): all four critics score it 4-5/10. The consistent complaints are: hurt and dash arms flung into a T shape, so the hit reads as cheering (M); the dress and sleeves merge into a mottled red blob with arms lost, plus shade-swap flicker (P); in E, side-lock hair crosses the cheek like a beard and the near eye drops out on turns (F/R); the S bow reads as a flat red cap (R); the run legs collapse to 1-px sticks; run E is missing because of a P crash.

## Ranked fixes
1. [P] run E crash in pixel_chain.shape_fixes (empty skeleton row) — clip missing from the build.
2. [M] hurt f01-f05 / dash f07-f10: arms go out in a T. Make the recoil inward (the chest caves, the shoulders rise, the elbows tuck, the head snaps 15-20°), and sweep the dash arms back along the travel line.
3. [P] sleeve|torso separation: add an interior line or a darker inner-sleeve value, keep the hands attached, flatten the dress to 2-3 tones, and cut shade_swap (fails 16/17).
4. [F/R] E profile: the side lock is drawn over the cheek and mouth, and the near eye vanishes at large yaw (idle E f05-f10, dash E f03-f07). Clip the lock behind the face, and keep the profile eye.
5. [M/P] run S/SE: the plant leg is a 1-px stick and feet drift 9-10 px. Jump apex: the legs are glued together. Add a knee tuck and give the legs a minimum width of 3 px.
6. [R] the S/SE bow reads as a red cap: bigger lobes above the crown. The E hair volume is about 20% bigger than in S.
7. [M] walk: little knee bend, bob and arm swing; the bun, bow and locks need 1-2 frames of lag.
8. [P] hair noise: 1-px speckles and floating bun/ribbon islands. Dash smears are solid pink blobs with loose speed lines.
