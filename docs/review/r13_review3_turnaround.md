# r13 Review 3: turnaround round 3 (AD + Character Designer)

**Verdict: FIXES (small).** Done: R2 items 2-6 and 8. The legs, boots, 5.0-head proportion and back curtain all work. Coordinates are turnaround 96x160. For head_small, x = turnaround x - 28 (rows match).

**Bow ruling (a).** One bow, tied at the back of the head. Each loop sticks out 5 px past the skull (x34-61), so the bow spans **x29-66 (38 px)**. Each loop is about 9 px tall (**y6-14**), and the outer tip tilts down. Every view shows this same size.

1. **Front: the loops read as mouse ears.** You can see it in the black silhouette. At x29-33 and x62-67, y8-13 they are round 6-row nubs. Redraw each as a flared fan, y6-14:
   - 2 px tall where it meets the hair at x33/x62, about 8 px tall at the tip;
   - lowest point at the tip (y14);
   - `teal_2` only on the top edge, plus one `teal_0` crease running toward the head.
   Do head_front first.
2. **Back: the bow is too big and the head looks flat-topped.** Shrink x27-68 to x29-66, with the loops at y5-15. Keep the hair arc between the loops (x40-55, y5-9) and round it so the skull still reads.
3. **Side: the bow reads as fins** (x61-75, y8-14). Seen from the side, the near loop faces us. Draw it 8-9 px wide, y6-15, on the back of the skull, and let it stick out at most 5 px past the back hair. In head_side it is also clipped at col 39, so make the canvas wider or move it inward.
4. **3/4:** the far-loop nub at x53-60, y3-6 reads as a sprout. Lower it to y5 or later so it sits behind the crown. Make the near loop's height match y6-14.
5. **Transparent hole (b), confirmed.** head_side (16,15) is `.`. Fill it with `u`. The turnaround side already has `s` at (44,15).
6. **Side bang is a visor.** Row 14 starts at x33, but the face starts at x38, leaving a 5 px brim with gaps under it (x33-37, y15). Cut it back to a 2 px overhang (start at x36) with a rounded tip.
7. **Back clump tips are too jagged** (y60-76). The split wedges look shredded, like a grass skirt. Round each tip into a curved point, with 1 `hair_1` shadow pixel on one side only.

**Appeal (d).** Honestly, this is no longer "terrible". The front and 3/4 faces are genuinely cute GBA/DS anime. The 5-head body and the slim tights read as feminine and youthful. Two things still drag the appeal down: the mouse-ear bow and the visor bang. Once fixes 1-6 are in, I expect APPROVED.
