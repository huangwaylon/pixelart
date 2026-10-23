# r13 Review 2: cut-scene poses round 2 (AD + Anim Dir)

Coords: source px.

## Status
- **A:** reviewed at 77a7b55.
- **B is pending.** shy and cheer are uncommitted (09:12 edits), with no Round 2 notes and stale renders.

## Head tilt (G1)
**This reads as a broken face, not a tilt.** Only the features move. The outline, crown, bows, bangs and chin stay level.
- idle is the worst. The right eye drops a row (y19 against y18), and its lash corner (59,20) touches the outline at x60. A droop.
- wave is hidden by the closed eyes, point by the 3/4 view.

## Verdicts
- idle: FIXES. The knee and heel fix is verified.
- wave: APPROVED, except the head. Taper, elbow (20,30), palm and lean verified.
- point: FIXES (minor). Shift, sleeve, fist and lean verified.
- hands_on_hips: APPROVED.

## Fixes
1. **Artist 3:** hand-redraw four tilted heads: front-L, front-R, 3/4-L and 3/4-R. Rotate the whole head as a unit:
   - The crown peak moves 1 px toward the high side.
   - The low bow drops 2 px and the high bow rises 1 px.
   - The eye line steps 1 px. Redraw the eyes; do not shear.
   - The mouth and chin move 1 px toward the low side, and the low-side jaw loses 1 row.
   - The bangs follow the slant; the curtains drop 1 px low-side and lift 1 px high-side.
   - Keep the x+26 anchor and the neck seam. Add the five expression overlays.
2. **A:** swap them in. idle tilts to the free side, wave and point toward the hand, recoil back, shy down.
3. **A, idle:**
   - Fill the hole at (59,57).
   - The curtain tip (x67-68, y53-58) reads as an elbow thorn. Merge it into a 2 px lock.
4. **A, wave:** delete the crumbs at (65-67, y57-60).
5. **A, point:**
   - The index tip is at x1. Shift 2 px right for a 3 px margin.
   - The diagonal mouth (x41-44, y26-28) reads as a smirk. Flatten it.
6. **B:** finish, commit, re-render, add notes.
