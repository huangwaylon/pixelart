# r12 review 2: Art Director

All round-1 items are resolved: zipper gone, 3/4 face turned, brows canonical, coat on oat_0, turnaround and bust_16 added. Orphans (8-connected): sheet 2, turnaround 3, busts 5-9, poses 0-3. At most 25 colours per file. Gate met.

**Stale:** the top-level `bust_*.png` predate the expressions/ render. The README points at them.

## Verdicts
- **APPROVED:** model_sheet, bust_front, bust_16
- **FIXES:**
  - turnaround (1)
  - 3/4 bust and expressions (2-5)
  - poses (6-8)
  - folder (9)

## Fixes
1. **A, turnaround rear-3/4 cheek, x317-324 y26-44.**
   - Problem: an ink column at x321 y28-43 walls off the cheek, and skin leaks into the hair at (323,42), (323-324,43). It reads as a pasted-on disc.
   - Fix: make x321 plum_0, fill the leak with hair_1, and taper the cheek to 1 px at y42.
2. **B, bust_neutral mouth, x35-37 y54.**
   - Problem: skin_1 on skin_2 is invisible at 1x.
   - Fix: line_skin, 3 px.
3. **B, bust_determined lid, x30-49 y38-39.**
   - Problem: the flat bar reads sleepy, and this is the known neutral/determined weakness.
   - Fix: slant each lash 1 px down toward the nose, matching the brows. Add 1 px downturned mouth corners at (34,55) and (39,55).
4. **B, bust_embarrassed sweat_drop.**
   - Problem: worried has the same drop and averted eyes, the pair swapped in blind test 1.
   - Fix: remove it from embarrassed. Smile vs embarrassed then separates on light vs heavy hatch plus averted eyes.
5. **B, bust_angry fx_anger, x19-25 y12-18.**
   - Problem: it floats 4 px off the hair and reads as a sparkle at 1x.
   - Fix: move it to x25-31 y13-19, overlapping the hair edge at the temple. Give it a 2 px red_2 body with a plum_0 edge.
6. **C, blush on point, hands_on_hips and recoil.**
   - Where: point (42-54,36-38), hands_on_hips (34-47,37-40), recoil (30-43,39-42).
   - Problem: it breaks the rule of no blush for angry, determined and surprised.
   - Fix: remove it. The other poses keep theirs.
7. **C, wave knee.**
   - Problem: the "kneecap" is a lavender 1x4 column at x47 y109-112. It reads as a seam, on the wrong leg.
   - Fix: remove it. Add a 2x1 highlight at the back-leg bend (x51-52 y112). Extend the leg split at x46 from y104-106 down to y112.
8. **C, hands_on_hips eyes.**
   - Problem: the 3-row half-lid reads drowsy.
   - Fix: use B's determined eye with the fix-3 slant, scaled to bQ.
9. **A/B, review root folder.**
   - Regenerate or delete the root `bust_*`, `bust_x4` and `bust_slots_x4`.
   - Point the README at `expressions/`.
   - Re-render bust_16 after fix 2.

**Optional (A, sheet front):** the mouth at (47-48,41) sits one row above the chin line. Moving it to y40 would clean up the lower face.

Re-review covers fixes 1-9 only.
