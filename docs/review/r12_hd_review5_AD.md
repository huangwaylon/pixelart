# r12 S4_hd round 5: Art Director re-review

**Verdict: FIXES** (two small regressions).

**Verified fixed:** run E f1/f4/f5 and W f5 now taper to a 1-px point within 1 row of legacy. All run E/SE/SW frames point (SE f3/f4 `KKK` matches legacy). idle, walk and carry_walk are byte-identical to r4. throw E/W improved (E f5 cap gone).

**Blocking:**
- Run W f1 (x32-34, y44-45): r4 `KmK` became a solid 3x2 `KKK` black blob. Restore the `m` core.
- jump_sc E f3 `rise`: r4 point at y42 is now a flat `KKK` cap at y40 (legacy y44). Apply the run taper.

**Non-blocking:** jump_sc W f3, throw W f7 flat (as in r4).
