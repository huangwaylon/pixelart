# R2 review: Game Director (JUMP, build 6042890d6309)

**Verdict: REQUEST CHANGES.** Timing, feet and metadata now pass. Clip, height, orphans and greyscale still fail.

## Criteria
1. Timing: **PASS.** 770 ms total, airborne at 110 ms, `inputLockEnd_ms` 590 (sum of f1-f9). Frames 10-12 are cancelable.
2. Foot slide: **PASS** (0.0 px).
3. Cell clip: **FAIL.** Launch f3 reaches y=63 in 7 of 8 directions (1 px margin). SE/SW f8 and SE f4 reach y=62.
4. Palette: 25 colours used, PASS. Orphans: **FAIL** (103).
5. Face at 3x, 18 deg: **PASS.** The eyes read in S/SE/SW, including crouch. Land f9 is marginal.
6. Greyscale on snow: **FAIL.** Hat lit tone #F4EAD2 has luma 234 and snow #DFEAF6 has 232. Only the outline separates them.
7. Determinism: PASS (lead verified). Metadata: PASS.

## Timing compromise: ACCEPTED
770/590 is 20 ms over my 570 lock. Airborne at 110 ms is responsive enough, and cancelable recovery covers the rest. Log it as final.

## Must-fix
1. Clip: every frame's bbox bottom <= 61 (2 px margin). Reduce launch stretch to 1.12, or toe-down to <= 20 deg.
2. Standing height 41 +/-1 px in all directions. It is currently 42-45 (NE 45). Height delta <= 2 px.
3. Hat greyscale: hat lit tone luma <= 205. Use #D8CBB8 as the top tone and drop #F4EAD2 from the hat ramp.
4. Orphans: 0. Also make QA treat height delta > 2, orphans > 0 and clip margin < 2 as errors, not a PASS.
