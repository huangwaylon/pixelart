# r13 Review 4: cut-scene poses (AD + Anim Dir)

Checked per pixel against the `.pix` sources and the renders. Coords are pose px.

## Regression check
I diffed the poses approved in review 3 against `d010b5d`. wave, hands_on_hips and shiver have 0 changed pixels. idle has exactly 1: the lash corner (59,20) went from `K` to `u`. That matches the face-edge column, so the re-paste is clean.

## Verdicts
- **idle: APPROVED.** No regression.
- **wave: APPROVED.** Unchanged.
- **hands_on_hips: APPROVED.** Unchanged.
- **shiver: APPROVED.** Unchanged.
- **point: APPROVED.** The `K` top outline runs the full sleeve. The fill is 6-7 rows at the wrist (x18-22) against a 10-row cuff and 12-row fist. The arm now holds its weight at 1x.
- **shy: APPROVED.** The clasp sits below the scarf band, with a `K` cap at y39. The mid-face blush is gone. Both irises are 4 rows ending in `jkkk`, and the right eye sits 1 row lower for the tilt, with no doubled sclera.
- **recoil: APPROVED.** There is now one lock from the nape. It runs flat to x80, then tapers down to a tip at (84,34), with nothing above y17 except the bow. The heel outline at x53, y135-140 is restored. The cuff's lit edge uses `d`, which follows the edge-normal rule.
- **cheer: APPROVED.** The fist-to-bow gaps are 2 px. The locks clear the sleeves with a 1 px gap from y36, and above that they tuck behind the arm, which is a valid overlap. The scarf tip is outlined.

## Fixes
None required. One optional polish item for cheer: the outer cuff columns (x17-18, y10-15; x69-71, y8-12) are bare `m`. Setting them to `d` would match recoil. It is not blocking because the cuffs read cleanly at 1x and 3x.

All 8 poses are signed off.
