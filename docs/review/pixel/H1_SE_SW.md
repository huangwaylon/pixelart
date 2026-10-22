# H1_B_final jump: pixel review of SE and SW (24 frames)

Reviewer: pixel-SESW. Reviewed against the regenerated base (fringe fix, base built 11:59:40), with SW mirrored next to SE for consistency. Every fix was recorded with `pipeline.override` and checked with `--preview` (out/variants/H1_B_final/pixelreview/fixed/). Palette colour names come from cw_charcoal.

Notes on what I approved:
- The `^` eyes (f3-f6), `>` eye (f10), `\` eye (f9) and the 2x2 eyes with no catchlight (f1-f2) change in step across SE and SW. I read them as deliberate expression decals.
- In 3/4 view the far eye fuses with the cheek outline. That is the accepted cost of this view.
- The red scarf tail is on the outer edge in SE and down the chest centre in SW. This comes from the single tail in the 3D asymmetry and is not a mirror error.
- Lit and shadow swaps between SE and SW (hair_2 vs hair_1, red_1 vs crn_1 mittens, oat_2 vs mauve cuffs) follow the fixed upper-left light and are correct.

## SE
SE f1: APPROVED as generated. Cuff steps down cleanly, the 2+3+2 mitten blob is readable, and the boots have cuff over a boot tone. The 1px char_1 hem tooth at (23,37) is the coat's front point; it recurs in f3/f4/f8, so removing it here would flicker.
SE f2: 2 px fixed. (22,28),(23,28) skin_1 to oat_1: forehead skin broke through the beanie cuff and touched the red hat directly. Closing the gap makes the cuff a continuous band (mirrors SW f2).
SE f3: APPROVED as generated. The small pom has its crn_1 cast shadow to the right (purposeful). The 4-row cuff block over a 2-row plum boot reads as toe-down launch.
SE f4: APPROVED as generated. The crn_1 row under the pom is its cast shadow. The OOO sleeve cuff under the hair keeps the arm continuous into f5/f6.
SE f5: APPROVED as generated. The mitten over the hair (RR/RRR) and the 3x2 sleeve cuff read well. The far mitten is a small crn_1 diamond at the cheek: dark but consistent with the light, and mirrored by the lit SW f5.
SE f6: 5 px fixed. (21,11),(19,12),(20,12) oat_1 to oat_2: the pom lost its top-left highlight only on apex, the longest frame (110 ms), while f5/f7 have it, so it flickered flat. (18,30),(18,31) oat_2 to red_1: the 2x2 mitten was outweighed by an 8px cream cuff that read as a white hand. The mitten is now 3x2, matching f5/f7 and SW f6.
SE f7: 1 px fixed. (25,21) red_1 to oat_1: a hat-red tooth poked into the 2-row cuff on this frame only.
SE f8: 2 px fixed. (30,21),(31,21) skin_1 to oat_1: cheek skin made a hole in the lower cuff row and left an orphan oat_1 at x32. The cuff now runs 2 rows to the edge as in f7.
SE f9: 2 px fixed. (21,41),(22,41) mauve to plum_0: the rear boot was cuff colour right down to the ground row and read as a lilac sock. It now has a dark sole (rule 8).
SE f10: 4 px fixed. (21,10),(23,10) to outline and (21,11) to oat_2, (23,11) to oat_1: the pom top was a 1px nipple (a lone oat_1 capped by a single outline pixel). It is now the round 3-wide cap used in f9/f11.
SE f11: APPROVED as generated. Face is 2x3 eye with catchlight, crn_1 mouth and skin_0 jaw shadow. The OOO/RRR/RRR mitten is readable and the boots have plum soles.
SE f12: 2 px fixed. (21,41),(22,41) mauve to plum_0: the rear boot cuff reached the ground row, while f11 has a plum sole.

## SW
SW f1: 2 px fixed. (25,41),(26,41) mauve to plum_0: the near boot was 3 rows of cuff colour to the ground (lilac sock). Gave it a sole.
SW f2: 2 px fixed. (24,28),(25,28) skin_1 to oat_1: the same cuff gap as SE f2. The 1px armpit notch at (31,38) is left as negative space separating the arm from the body.
SW f3: 7 px fixed. (20-23,43) and (22-24,44) oat_2 to hair_1: the front boot was a 5x5 cream block down to the ground and read as a bare white foot. It is now 3 rows of cuff over 2 rows of boot, matching SE f3 and SW f4.
SW f4: 3 px fixed. (20-22,33) lav_1 to char_1: a 1px-tall lilac strip across the belly. It shows in f4, disappears in f5 and returns in f6 (flicker), and never appears in SE.
SW f5: 3 px fixed. (22-24,41) oat_2 to hair_1: the boot cuff reached the ground row. The sole now matches f4/f6 and SE f5.
SW f6: 5 px fixed. (20,32),(21,32),(19-21,33) lav_1 to char_1: a 5px purple patch on the coat. It reads as a stain and is the same flickering highlight island as f4.
SW f7: 2 px fixed. (22,21) red_1 to oat_1: the same cuff tooth as SE f7. (25,30) red_1 to crn_1: the lit mitten and the red_1 scarf collar had fused into one red mass. A crn_1 contact shadow now separates hand from scarf (SE f7 separates them with hair).
SW f8: APPROVED as generated. Lit sleeve cuff plus a red_1 mitten mirrors SE f8's shadowed version. Cuff and boot are clean.
SW f9: 2 px fixed. (17,36),(15,36) to outline: the bottom outline under the sleeve and mitten was a sawtooth (#.#.##) with 1px transparent notches. It is now closed, as in SE f9.
SW f10: 4 px fixed. (24,10),(26,10) to outline and (24,11) to oat_2, (26,11) to oat_1: the same pom spike as SE f10.
SW f11: 9 px fixed. (19-24,30),(19,31) skin_1 to skin_0: there was no under-chin shadow, so a flat skin_1 block ran 2 rows into the scarf and gave a long chin. Added the jaw row seen in SW f10/f1 and SE f11. (25,41),(26,41) mauve to plum_0: boot sole.
SW f12: 6 px fixed. (22-25,29) skin_1 to skin_0: the missing jaw shadow again, now matching SE f12's ssss row. (25,41),(26,41) mauve to plum_0: boot sole.

Totals: SE has 5 frames approved and 7 fixed (18 px). SW has 1 frame approved and 11 fixed (45 px). Combined: 6 approved, 18 fixed, 63 px.

## Generator-level issues (better fixed procedurally)
1. **Boot cuff reaches the ground row** (SE f9/f12, SW f1/f3/f5/f11/f12). When the foot points down or is foreshortened, the boot_cuff band fills the whole visible boot. Suggestion: in the boot material pass, force the lowest 1 opaque row of each boot (2 rows when the boot is 4 or more rows tall) to the `boots` ramp, and clamp the cuff to at most 2 rows per leg.
2. **Under-chin shadow disappears when the face turns toward the light** (SW f11/f12). The skin toon band uses N·L only. Suggestion: add an ambient-occlusion or "under-surface" term so skin pixels directly above a scarf or collar pixel always get skin_0. A rule like "skin px whose y+1 neighbour is scarf becomes skin_0" would do it.
3. **Hat cuff band breaks**: skin or hat-red teeth intrude when head tilt curves the band (SE/SW f2, f7, SE f8). Suggestion: after quantisation, run a 1px morphological close on the hatcuff mask (and require at least 2 rows thick where the band is visible). A red or skin pixel with cuff above and below, or cuff left and right, becomes oat_1.
4. **Pom silhouette noise**: a 1px top spike in f10, and the highlight dropping out in SE f6. Suggestion: clean the pom mask with an opening (remove single-pixel protrusions), and always keep at least 2 px of the top ramp tone at the pom's upper-left.
5. **Coat highlight islands** (lav_1 in SW f4/f6). The 3-tone coat produces 1-row lav_1 slivers that flicker. Suggestion: apply rule 2 per frame (tone islands under 4 px, or 1 px tall, merge into the neighbouring tone) and/or drop lav_1 from the coat on parts narrower than 3 px.
6. **Sawtooth outline at part junctions** (SW f9). Where a separately outlined limb meets the body, the outline pass leaves alternating transparent pixels. Suggestion: fill a transparent pixel that has outline at left and right (or above and below) and an opaque pixel above.
7. **Mitten/scarf fusion when both are red_1** (SW f7). Suggestion: when mitten and scarf masks touch, set the scarf pixel at the contact to crn_1 (a contact shadow).
8. Minor, not fixed: the coat hem has recurring 1px char_1 "front point" teeth (SE f1/f3/f4/f8). They are consistent enough to read as a design feature. If unwanted, smooth the hem in the generator so frames don't flicker.
