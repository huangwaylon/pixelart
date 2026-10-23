# r15 animation review (Animation Director)

**Verdict: FIXES** (one item; everything else is approved)

**Scope:** 13 clips plus the r14 copies (idle, walk, run, jump_sc, throw). I compared head crops aligned on the sprite top, using Pillow diffs against the v1 release.

## Passes
- **Blinks:** idle has 1 blink, the same as v1 and r14. It is the same frame, 5 at 80 ms, in all 5 face directions. No clip gained or lost a blink.
- **Eye pops / lash-over-bang:** each eye pattern (ink + catchlight) has one shape per expression per direction in every clip. Eye ink count never changes within an expression. That is cleaner than v1, which had 1-2 px eye flicker in carry_idle, carry_walk and jump_sc. SE/SW now carry 2 catchlights every frame.
- **Loop seams:** the last-to-first diff is within plus or minus 15 px of v1 in every direction. The idle seam (about 210 px) is the same in v1, so r15 did not add it.
- **Penetration:** 0 chain penetrations, and QA passes on all 18 builds. Below the head, the diff against v1 is 7 px or less.

## FIX: S-view bang hem strobes on the head bob
The head bob moves the hem and the lash by different amounts:
- **run S:** hem rows 32/34/32/31, lash rows 34/35/34/32.
- That makes the skin gap between bang and lash flip 1/0/1/0 **every frame**, across the full 7 px hem.
- carry_walk S and run_r14 S do the same.
- walk S flips twice per cycle.
- In v1 the gap held steady at 1-2 rows, with only edge pixels changing.

The cause is the new tip radius (0.3) and y 8.6, which put the hem on a pixel boundary.

**Fix options:**
- Pin the S hem relative to the lash row, with 1 constant skin row.
- Or nudge the centre and L1-L3 tips about 0.25 px so they sit mid-pixel.

Then re-check run, carry_walk and walk S.
