# r13 Review 5: turnaround round 5 (AD + Character Designer)

**Verdict: FIXES (final).** Fixes 1, 5 and 6 from review 4 pass. The back bow is now the hero shape: keep it as it is. Coordinates are given as turnaround (T) and head_small (H). H = T x-26, same y. Apply each fix to both files.

1. **Front lobes still read as mouse ears.** They are round discs joined to the head along a long seam, with gaps at y15-17. Redraw each lobe as the visible outer half of the back loop: tall at the outer end, narrowing into the head.
   - Left lobe, outer end: T x27-29 / H x1-3, y5-16, with rounded corners.
   - Top edge steps down toward the head: y5 x28-29, y6 x30, y7 x31, y8 x32, y9 x33 (H: x2-3, 4, 5, 6, 7).
   - Bottom edge steps up: y16 x28-29, y15 x30, y14 x31, y13 x32-33 (H: x2-3, 4, 5, 6-7).
   - The tip tucks under the head outline at T x33 / H x7, y9-13. Nothing should rise above the crown next to the hair, and there should be no transparent gaps.
   - Add a `teal_0` pocket at T x29-30 / H x3-4, y10-12, and a crease to the tip at y11. Use `teal_2` on the top arc only.
   - Mirror on the right: T x62-68 / H x36-42.
2. **3/4 knot.** It is currently a 5x5 outlined dark box at T x58-62 / H x32-36, y8-12. Replace it with a 3x6 pinched knot at T x59-61 / H x33-35, y8-13.
   - Fill with `teal_1`. Add one `teal_2` pixel at T x60 / H x34, y9, and `teal_0` on the bottom row only.
   - Remove the K column on the loop side, T x62 / H x36, so the knot flows into the loop.
3. **Side profile: face too long, jaw too heavy.**
   - Bring the bangs down so skin starts at y17: hair at T x37-39 / H x11-13, y15-16.
   - Profile line `L`: y17 at x37; y18-22 at x36; y23 at x35 (nose); y24-25 at x36; y26-28 at x37; y29 at x38. In H that is x11, 10, 9, 10, 11, 12.
   - Steeper jaw: y30 at T x39-40 / H x13-14, y29 at T x41-42 / H x15-16, y28 at T x43-44 / H x17-18.
   - Below the jaw: neck in `u` at T x41-44 / H x15-18, y30-31. Clear T x37-40 / H x11-14 at y30-31.

Then: APPROVED.
