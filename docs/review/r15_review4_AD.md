# r15 AD review, round 4: S4_hd

**Verdict: APPROVED**

Per-pixel diff of all 27 clips vs HEAD~1 and round-2 (c27a551) rebuilds:
- **SW regression fixed.** walk f1/f2/f5, run f8, throw f1/f4, jump_sc f2/f9 are plum again. No outline pixel (K or P) became fill in any clip or direction. The jump_sc f2 notch is closed.
- **~40 h>P pixels on the SW temple edge:** these close old mid-hair gaps in the contour. Keep them.
- **5 K>P pixels (throw f4 (16,33), pick_up_r14 f10 (16,33-35)):** accepted. The plum ends one pixel below the hair and steps diagonally into the K cheek line. Approved walk SW f1 (16,32) does the same.
- **N/NE/NW:** pixel-identical to round 2.
