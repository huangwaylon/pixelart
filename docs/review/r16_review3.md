# r16 review 3: Gemini r2 items

**Verdict: APPROVED, with one flag fix:** set G1 back to dots (`S_FRINGE = True`, `make_s4_hd.py`).

## Pixels (vs HEAD~1 rebuilt in /tmp)
- **Scope:** diffs are face-only. N, NE and NW are byte-identical.
- **G2 landed.** SE far contour is x30/30/30/29/28. SW mirrors it. SW run f3 bare silhouette skin is now outlined.
- **G5 landed.** The S chin tapers on both sides (walk f0 y36 x19-26 -> x20-25).
- **G3:** shading only. Accepted. The E silhouette is still a 5-row front at x30 (r17 model).
- **G4 and throw f0:** both landed.
- **G1, dots win.** Band runs change per frame: walk goes 4-4-2 to 3-4-3, carry_walk ranges 3-5, and throw f4 is 5-4-1 with an orphan. That shimmers at 1x, and at 8x it reads as a forehead stripe, the headband look r16 removed. Dots stay 2-2-2 everywhere, with one rounded highlight per clump. Keep the band code, but leave it off.

## Gemini r3: "ship-ready"
- #1 and #2 (SW run f4 and jump_sc f7 cheeks): rejected. The pixels already step 1-2 px per row.
- #3 (E run hook): rejected. The tip already hangs at x32 y32.
- #4: moot with dots.
- #5 (near-cheek dot): noise beside the blush. Rejected.
- Stretch (crown dip): r17 model.
