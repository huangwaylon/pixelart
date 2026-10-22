# r13 Review 6: turnaround round 6 (AD final check)

**Verdict: APPROVED.** Checked pixel by pixel against the `.pix` grids, using nearest crops. The head rows match `head_small` at x+26 in all four views (y0-31 for front, 3/4 and side; y0-16 for back), compared by colour.

## Fixes from review 5
1. **Front lobes: PASS.** The outer end is at x27-29, y5-16. The top steps down at x28-29, 30, 31, 32, 33 and the bottom steps up at x28-29, 30, 31, 32-34. The tip tucks under the head outline at x33-35, y9-13. The pocket (x29-30, y10-12), crease (y11) and `teal_2` top arc are all present. The right lobe mirrors at x60-68. The lobes now read as bow loops, not ears.
2. **3/4 knot: PASS.** The 3x6 `teal_1` knot is at x59-61, y8-13, with `teal_2` at (60,9) and a `teal_0` bottom row. The loop-side K column is gone, and the pinch reads from the silhouette.
3. **Side profile: PASS.** Skin starts at y17. The `L` profile follows the spec exactly, with the nose at (35,23). The jaw sits at y28 x43-44, y29 x41-42 and y30 x39-40, with the neck in `u` and x37-40 at y30-31 cleared. The face is shorter and the chin is lighter.

## Stray pixels
- **Back (35,16), `d`:** a contact shadow under the left loop, next to the K outline. It is invisible at 1x. **Keep.**
- **3/4 (60,9), `teal_2`:** the knot highlight that was specified in review 5. **Keep.**
- **Side (37,24), `v`:** the nostril shadow under the nose tip. It matches the single-pixel nose used in the other views. **Keep.**

## head_small expressions (20)
All 20 read at 1x and 2x on both light and dark backgrounds. Laugh, content and sad hold their shape at 1x, and the FX marks (vein, steam, sweat) stay legible. The 3/4 angry vein floats in front of the forehead, which is an acceptable manga convention.

No further changes. Lock the turnaround and head_small.
