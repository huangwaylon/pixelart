# r12 S4_hd round 3: Art Director re-review

**Verdict: FIXES** (one blocker). The release candidate matches `out/variants` byte-for-byte. Checked S/SE/E/NE/N/SW for idle, walk, run, jump_sc, throw and carry_walk at 5-8x with pixel dumps.

**Round-2 items verified:**
1. Head rust: SE arc sits 3 px inside the outline, the x18 seam is gone, carry_idle N specks are gone, hem unchanged. The N idle arc was removed rather than cut to 2 px; acceptable.
2. Bow volume: highlight plus fold on every loop in S/N/NE/SE/E.
3. S ears are 4x2 and mirrored with no nub. They are larger than legacy in every clip. Throw S f2 shows no left ear, but legacy shows none either.
4. S bridge is 3 px in every frame of 10 clips.
5. Mouth: SE (27,34) and SW (20,34) mirror, 2 px from the cheek edge.
6. The SW far cheek is outlined at x17.
7. SE edge: (31,28) is now part of a continuous outline, not a stub.

No regressions: at most 16 colours per frame, and the N walk sway reads.

**Blocker:**
- **E/W and SE/SW ponytail.** HD ends in a flat 2-3 px "00" cap, 2 rows above legacy in E (y41 vs y43). In SE it ends at y39 vs y43, so it reads as a bob.
- This is the main silhouette trait, it fails in the most-used locomotion directions, and it has been open since round 1.
- Fix: restore the legacy length and a 2-3 step taper to a 1 px point.

**Non-blocking (v1.1):**
- Throw E bow colour mix: transient frames.
- Climb NW f0 strays (unoutlined hand, cream hem blob): low-visibility clip.
- SE rust arc has a 1 px break at (23,27).
