# r8 Designer B: C3 and C4

Both pass QA with `regularize` on: C3 has 26 jaggies, C4 has 33. Each uses 15 colours.

## C3_sidepony_cat
**Intent:** a lively, asymmetric girl whose dark side-pony is the silhouette, with a small cat beanie pushed back.
- **Hair:** `side_pony` with `side` bangs, and the hair_espresso ramp set to `plum_0, plum_0, hair_1` for a dark mass.
- **Pony chain:** anchored lower and swept back, thicker so it shows in E/W.
- **Beanie:** a shallow cap tilted back 12°. I removed the `pom` and `beanie_cuff` and raised the ears.
- **Colours:** mauve hat, navy_2 coat as the mid value, red scarf and pony bow as the accent.
- **Bow:** three `ribbon` prims.

**Strengths:** the hair carries the silhouette in S, SE and N.
**Weaknesses:** the pony is weak in the pure E silhouette, dark hair merges on dark tiles, and the profile face is about 3 px wide.

## C4_snow_hood
**Intent:** a cosy "snow bunny": a rose hood with a cream fur ring, bob fringe, blush, and teal mittens and tie-poms.
- **Outfit:** `bob` with high fringe, `puffer`, no scarf.
- **Colours:** coat `crn_1, crn_2, red_2`; fur `oat_1, oat_2`, with no mauve.
- **Fur ring:** rebuilt as 16 balls, set back at the sides so the profile eye shows.
- **Removed:** the `bob_side` and `bob` chains, which showed as dark holes on the back.

**Strengths:** the best front read. The ring and face survive at 1x, and the egg silhouette is unique.
**Weaknesses:** the hood, not the hair, is the silhouette, and the back views are a flat red ball. Lop ears blurred into the hood, so I dropped them.

## Generator limitations
1. The `hood` fur ring has only 10 balls over 270°, which leaves a gap on the left.
2. The ring at z=0.62hr hides the face in profile.
3. A hair ramp containing `outline` gets checkerboarded by pixel_perfect.
4. The `cat_beanie` keeps its pom, and its ears are buried in the dome.
5. The `clip` is hidden by the fringe, and the shared `ribbon` material can't be recoloured.
6. Height QA counts the hat ears, so a 0.4-unit move flips PASS/FAIL.
