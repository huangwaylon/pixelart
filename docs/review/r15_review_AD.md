# r15 AD review: S4_hd far eye + bangs

**Verdict: FIXES**

**Request 1, SE far eye: solved.** The far eye is 2x3 with a 2 px cheek and a 2 px bridge. Reads naturally in every open-eye frame.
**Request 2, bangs: mostly solved.** Forehead skin is down in every S/SE/SW frame vs v1; no eye pixel lost. Gaps remain (fixes 2-3).

**Rulings**
- E/W eye 1 row lower: **APPROVED**.
- Far-eye catchlight: **APPROVED**, if it stays on the near eye's side ("Vn" in SE, mirrored in SW) and is dropped when the far eye is under 2x3.

**Fixes**
1. **Lone bang tips between the eyes.** A single hair pixel sits in the bridge on or above the lash row (`nnnhsnn`), about 20 frames vs 5 in v1:
   - SE walk f1/f2/f5, run f5/f7, carry_walk f0/f1/f5/f7, throw f2/f4/f6/f7, jump_sc f2/f4/f5/f12
   - the SW mirrors

   Cut face hair pixels with 3+ skin/eye neighbours.
2. **Bob frames lift the bangs.** This leaves a 1-row strip up to the far contour in SE walk f2/f5, run f3/f5/f7, carry_walk f5 and the SW mirrors. Keep the 2 far-temple columns as hair above the lash.
3. **S has no slope; throw is still bald.**
   - S idle has a flat bang edge over a 12 px skin row. Drop the outermost bang column on each side to the lash row.
   - Throw S/SE/SW f0-f3 show 2 forehead rows. Lower the bangs 1 row.
4. **Joyful far arch touches the bangs** in jump_sc SE f4-f6 and SW f5-f6. Keep 1 px of skin above closed-eye arches.
5. **Skin pocket in E/W run.** E/W run f0/f2/f4/f6 have a 1 px skin pocket (`shhK`) above the eye. Fill it with hair.

**Gemini** (auth OK):
- #1 agreed (fix 4).
- #2 rejected: both SE catchlights are already screen-left.
- #3 partly agreed (fix 5).
