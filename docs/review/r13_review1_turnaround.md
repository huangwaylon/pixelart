# r13 Review 1: turnaround draft 1 + head_small (AD + Character Designer)

**Verdict: FIXES.** Palette, lines and landmark rows are consistent; the character reads wrong. All four lead concerns confirmed.

## Binding decisions (turnaround, bust, head artists)
**Bow.** The bible's "2x head" is withdrawn. Head is 28 px, so the bow spans **42 px (1.5x, range 40-44)** and sits at the **back** of the head (half-up tie).
- Front: puffy loops peek 6-8 px each side **behind** the hair at y4-17, at most 2 px above the crown (y3). No knot visible. The "bow top" landmark becomes y3.
- Side/3/4: knot on the back of the skull (side view about x63, y10-15).
- Back: 5x5 knot over the ponytail root, plus **two** swallowtail tails to y40.

**Legs.** Dark tights stay, but they must read as legs.
- Add `char_2 #6A6688` (spare slot) as a 1 px shin and kneecap sheen; `ink` on the inner edges.
- Thigh gap starts directly under the hem. Widths: thigh 9, knee 6, calf 7, ankle 4 px.
- Knees 1 px in. Weight on her right leg; the free knee bends in, heel up 1 px.
- Boots: flared cuff at about y128, 1 fold, rounded toes turned slightly out.

## Fixes
1. **Bow (all views):** redraw as above. Side view: lobes move from y0-10 to y8-20.
2. **Front hair:** back hair shows 3-4 px outside the arms (x27-30, x65-68) from y36 to y70. Side locks run over the shoulders to y44.
3. **Stance (front/3/4):** hips shift 1-2 px toward the weight leg, shoulders tilt 1 px the other way. Waist pinched to 20 px at y52-58, then the hips flare.
4. **Arms:** they are 6 px sticks with a 1-2 px slot. Add an elbow bend at about y58 so the gap opens there. Curl the mittens, with a thumb pixel.
5. **Hem (y84-87):** the flat shelf juts 4 px. Make it a gently curved hem, flaring from y72.
6. **Face (y14-31):** off-model against C.
   - Bangs are a flat slab; add C's 2 notches.
   - Brows read as a second lash: use 1 px `hair_1`, raised 1-2 px.
   - Eyes are cropped to 4 rows: use the full 5x6 iris ramp, catchlight and lower lash.
   - The `crn_1` dot reads as a surprised "o": use a 1-2-1 smile.
7. **3/4:** the face is nearly frontal. Far eye 1-2 px narrower, more skull behind the ear, ponytail S-curve instead of a straight column.
8. **Back:** add a nape and shoulder break (y34-40). 3-4 big hair clumps, not stripes.
9. **head_small:** its 40 px bow at y1-10 reads as cat ears. Apply the bow decision and fix 6, then re-sync the turnaround faces (offset x+28).
10. **Lines:** new curves use monotonic runs.
