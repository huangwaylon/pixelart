# r13 Review 3: cut-scene poses (AD + Anim Dir)

Coords: pose px; head-local in [ ]. The tilt pastes match the composed heads, and the orphan clean-up did no face damage. It did damage outlines (fixes 4, 7).

## Verdicts
- **idle: APPROVED.** Hole (59,57) filled, thorn now a 2 px lock.
- **wave: APPROVED.** Crumbs gone, tilt clean.
- **point: FIXES.** Shift and smirk verified; the arm still reads thin.
- **hands_on_hips: APPROVED.**
- **shiver: APPROVED**.
- **shy: FIXES (minor).**
- **recoil: FIXES.**
- **cheer: FIXES.**

## Fixes
1. **A, point:** the forearm (x18-30) is 5 rows against a 12-row fist, with a light `q` top edge. Add a `K` top outline at y33 and keep `q` as the inner shade. Target 7 rows at the wrist.
2. **B, recoil:** the locks (68-91, y13-28) rise above the bow and read as antlers. Redraw them as one tapered lock from the nape (~64,20), arcing back and **down**. Tip near (84,34), nothing above y16.
3. **B, cheer:** the teal fists (x20-28 / x70-77, y3-12) touch the teal bows (x26-34 / x62-69). Move the fists 2 px outward with a 1 px gap.
4. **B, cheer:** the clean-up removed the cuff outlines. Restore `K` at x19 y10-16, (70,9), (71,10), (21,16).
5. **B, cheer:** the lifted locks (x22-30, y33-52 / x63-74, y33-50) sit flush on the sleeves. Trim them 2 px with a 1 px gap. Outline the scarf tip (x68-73, y52-56).
6. **B, shy:** the mittens (x39-50, y38-47) merge with the scarf. Drop the clasp 2 px, or add a `K` row at y40-41.
7. **B, recoil:** clean-up damage. Restore the planted boot's heel outline (x52-53, y135-140) and the cuff outline (x30, y44-48).
8. **H, front_tiltR_embarrassed (shy):** the slid clusters show.
   - Delete the blush pair at (44-45,27) [20,25]; it sits on the mid-face.
   - The right iris bottom row slid to (50,25) [26,23], and the sclera is doubled at x49-50. Redraw it to match the left eye.
   - Mirror the fix in tiltL.
9. **H, front_tiltR_smile (idle):** the lash corner (59,20) [30,20] touches the face edge. Set it to `s`.
