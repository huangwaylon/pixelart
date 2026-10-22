# r12 S4_hd: Animation Director review

**Verdict: ADOPT-WITH-FIXES**

All 13 clips vs S4_halfup_bow, frame by frame at 4-8x nearest. I also measured frame diffs, loop seams and one-frame flicker pixels (changes at f, reverts at f+1).

## What holds
- Timing, key poses, arcs and root motion match legacy (diffs within about 10% per frame).
- No visible penetration. The hair follows through on jump_sc frames 9/11 and land frame 0, as in legacy.
- Silhouette flicker and loop seams are about equal to legacy.
- Hands read in side and front views.

## Fixes
1. **idle NE, frames 0/5/7:** a 4 px #6E3C3A run at the waist (y43-44, x22-25) switches on and off, so it strobes at 220 ms. Clamp the curtain chain tips above the belt band, or bias their depth behind the coat. Check NW too.
2. **idle S/N/NE, frames 2-3 and 6-7:** the crown clumps and bow-knot pixels flicker. Hair-colour flicker is 34 vs 16 (S), 42 vs 17 (N) and 31 vs 11 (NE). Cut idle chain noise below 0.5 px or add hysteresis, and hold the crown highlight fixed.
3. **N/NE/NW, arms raised:** the wider bow loops touch the raised mittens. Both use #2A8C8E, so they fuse into one teal bar and the hands disappear. Affects carry_idle, carry_walk, carry_throw f0 and pick_up f6-8. Keep a 1 px #241628 gap between bow and mitten, or shade back-view mittens #1C4C54.
4. **throw N, frame 4 (release):** the throwing arm is mostly hidden behind the curtain and bow. Legacy shows it clearly. Sort the arm above the hair for this frame, or push the curtain chains away from the throwing side as follow-through. Check NE frame 4.
5. **Back views N/NE/NW (idle, walk, carry):** the ponytail merges into the curtain as one wedge, so the "single tapered ponytail" no longer reads. Add a 1 px #4A2448 edge where the ponytail overlaps the curtain, or drop the curtain one value.
6. **walk S/SE/NE/NW/SW, down frames 1 and 5 (low priority):** the curtain edge pixels toggle. Silhouette flicker is +30-55% vs legacy (S 81 vs 52, SE 124 vs 87). Smooth the chain output, or snap the curtain to 2-frame holds.
7. **Inherited from legacy, not blocking:** the idle 3→4 shift and the 7→0 seam are each about 150-210 px in both models.

Re-review fixes 1-4 before release. Fixes 5-6 can land in the next pass.
