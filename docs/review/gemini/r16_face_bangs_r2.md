# Gemini 4 Argon critique: r16_face_bangs_r2

_Context:_ Game sprite 48x64 of a cute anime heroine. User request: 'The face looks a bit too fat ... more realistic, pointy, curved face ... bangs should be more volumous and come off the forehead more, for a more layered, dynamic look'. Image 1: S-facing frames, round 1 vs round 2 of the fix (8x and 1x/2x). Image 2: before/after across 5 directions. Is the request solved at 48x64? Top 3 remaining issues with concrete pixel fixes.

_Images:_ 00_REVIEW/r16_face_slim_bangs/round2_S_fringe.png 00_REVIEW/r16_face_slim_bangs/before_after.png

**(1) Overall Verdict**
The face-slimming and E/W profile fringe lift are a massive improvement, but the S-facing Round 2 bangs look like jagged comb-teeth at 1x, and SW/SE angles still have a protruding "balloon cheek" that breaks the pointy anime jawline.

**(2) Top Problems (Ranked by Impact)**

1. **S-Facing Fringe "Comb-Teeth" Noise (Image 1, `r16 round 2`, all S frames, Fringe y≈12–14, x≈19–29)**
   - **Problem:** Alternating 1px gaps along the fringe bottom edge (`S idle f1`, `S walk f1`, `S throw f3`) and isolated 1px orphan highlights (`S run f4` at right temple) read as pixelated saw-teeth at 1x/2x rather than lush, layered hair.
   - **Concrete Fix:** Group bangs into 2–3 asymmetric clusters instead of 4–5 even teeth. Make the center lock 3px wide, flanked by two 2px side locks stepping *up* 1px toward the temples. Replace the disconnected 1px light-brown dots at the outer edges with a continuous 4px curved highlight band (`hair_light`) 1px *above* the fringe tips, and tuck 2–3px of `skin_shadow` (the warm rose/peach shade) directly under the fringe tips to sell depth off the forehead.

2. **SW & SE "Balloon Cheek" Protrusion (Image 2, `after (r16)`, SW & SE columns, `idle f1` / `run f4` / `throw f3`, outer face edge y≈15–18)**
   - **Problem:** In `SW run f4` (left edge of face, x≈17, y≈15–17) and `SE idle f1` / `run f4` (right edge of face, x≈30, y≈15–17), the far cheek bulges outward in a vertical 3px block before snapping inward. It still reads fat/chubby instead of a curved anime 3/4 taper.
   - **Concrete Fix:** Shave 1px of `skin_base` off the outermost cheek column at the lower row (y≈17, just above the jawline corner), moving the dark-purple outline (`outline_dark`) 1px inward. Put 1px of `skin_shadow` inside that new corner to create a clean diagonal 1px-per-row taper down to the chin.

3. **E & W Profile Forehead Shelf / Flat Face Plane (Image 2, `after (r16)`, E & W columns, `idle f1` & `run f4`, front of face y≈12–17)**
   - **Problem:** Lifting the bangs off the forehead worked well, but the exposed forehead/nose profile Underneath (`E idle f1` x≈28, `W idle f1` x≈19) is a flat 3px vertical wall, making the upper face look boxy rather than delicately curved.
   - **Concrete Fix:** Set the top forehead pixel (immediately under the lifted bang tip, y≈13) 1px *inward* toward the head using `skin_shadow`, leaving the lower 2px (y≈15–16) sticking out 1px further as a cute, pointed anime nose/cheek peak.

4. **SW `run f4` Disconnected Floating Bang (Image 2, `run f4 after (r16)`, SW column, left fringe tip x≈16, y≈12–13)**
   - **Problem:** The front bang tip kicks out to the left by 2px with a flat horizontal bottom, looking like a stiff visor/cap brim rather than hair with volume.
   - **Concrete Fix:** Add 1px of `hair_base` above the protruding tip (at x≈17, y≈11) to thicken the curve from the crown, and drop the very tip 1px lower with `outline_dark` so it arcs *downward* over the brow.

5. **`jump_sc f7` Chin Squish Lost the Taper (Image 2, `jump_sc f7 after (r16)`, S / SE / SW columns, chin y≈18–19)**
   - **Problem:** Because the mouth/blush stayed wide while the jaw was slimmed, the lower face in the happy squinting frame looks squared-off at the bottom compared to `idle f1`.
   - **Concrete Fix:** Drop the center 2px of the chin (`skin_base` + underlying scarf top edge) down by 1px in S, SE, and SW `jump_sc f7` to restore the V-taper while keeping the wide happy cheeks.

**(3) What Is Working & Must Be Kept**
- **S-facing jawline slimming (`r16` vs `r15`):** Shaving the lower cheek corners in S `idle f1`, `run f4`, and `throw f3` immediately cured the "potato head" silhouette at 1x—keep this exact lower-face pixel count.
- **E & W profile lifted bang silhouette:** The 1–2px overhang of the front bang with the dark underside pocket in E/W `idle f1` and `run f4` nails the requested "comes off the forehead" dynamism.

**(4) One Stretch Suggestion to Raise Appeal**
- **Add a 2px "M-slit" forehead peek in S and SE/SW views:** Carve a single 1px vertical notch of `skin_shadow` 1px up into the off-center part of the bangs (right above the inner eyebrow in S and the front eye in SE/SW). Showing a tiny sliver of shaded forehead higher up between two thick bang locks is the classic GBA/DS anime trick to sell thick, airy hair volume at low resolution without adding noise.
