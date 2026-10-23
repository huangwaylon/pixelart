# r12 S4_hd round 4: Art Director re-review

**Verdict: FIXES** (narrowed blocker). Release matches `out/variants` byte-for-byte. Checked E/W/SE/SW in idle, walk, run, jump_sc, throw and carry_walk with pixel dumps against legacy.

**Verified fixed:**
- idle, walk, carry_walk E/W: 1-px point at legacy row (+/-1), 3-3-1 taper.
- SE/SW in all six clips: tapered to a point at or below legacy.
- SE rust arc is continuous (idle f0/f3/f5, walk, carry_walk).
- No regressions: at most 16 colours per frame.

**Still blocking (run, main locomotion):**
- Run E f1, f4, f5 and run W f5 still end in a flat 3-px `KKK` cap after a 4-wide row.
- In those frames the tip is 2 rows above legacy (E f1 y43 vs y45, f4 y41 vs y43, f5 y43 vs y45; W f5 y43 vs y45).
- Apply the round-4 taper to these swing frames.

**Non-blocking:**
- jump_sc E/W f2/f10 are flat and 3 rows short (legacy is flat there too).
- throw E f5 has a 4-px cap.
