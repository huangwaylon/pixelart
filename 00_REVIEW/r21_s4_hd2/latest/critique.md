# r21 round 7 (polish): AD r6 notes

## Done
- **Crescent closed.**
  - **Root cause:** the side lock was smooth-unioned into the hair dome's blend set. Near the face opening a lock hit was attributed to the dome, then culled by the dome's face-opening clip plane, so no surface was drawn.
  - **Fix:** the side locks are now hard-unioned. A new under-layer sheet hugs the skull just outside the face silhouette from temple to jaw.
  - The same bug had been eating the fringe-lock tips (the "drippy" tips). The fringe locks now melt only into each other (own set) and are hard-unioned with the dome, so they are full chunky locks with clean rounded tips.
  - Checked in S / SE / SW hi-res and in the sprites: no gap.
- **Bow:** loop long axis tilted down (up -6 deg, which reads about 0-5 deg up through the 16 deg camera) and scaled 1.2, so the round puffy wings sit horizontally past the head in the front view (c2). The S sprite shows 1-2 px wing tips on both sides. Backward sweep and seating are unchanged.

## Remaining, ranked
1. **Bow in the S sprite:** still small (1-2 px past the head). SE / SW / N read well. A bigger front read would need longer wings or a higher seat, which conflicts with "seated at the ponytail root".
2. **Fringe roots:** show as distinct ridges where they leave the dome (hard union). It is fine in the sprites, but up close the hairline reads slightly "planted".
3. **Hi-res lock sheets:** small marching / tracing noise on thin sheet edges (side view near the ear). The exported mesh shows some surface wobble on thin parts (hair sheets, bow) after smoothing.
