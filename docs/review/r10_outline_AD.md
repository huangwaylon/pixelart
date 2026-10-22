# r10 Outline styles: AD verdict (S4, jump_sc)

**Is a connected outline necessary?** It must be closed, but not black. Oat coat on snow melts wherever an edge is open.

## Ranking
1. **OL_selout (lock).** Reads nearly as well as dark on snow and navy, but softer. The plum hair crown and teal bow edge feel DS/GBA ドット絵. Coat waist and hem read in every direction. Weight is consistent S to N.
2. **OL_colored.** Softest and cutest. The lit oat coat dissolves on snow, the plum edge merges with navy tiles, and the 1x silhouette goes mushy. Stray teal_0 speck at N f14 (x29-30, y46).
3. **OL_dark.** Most readable, but heavy and western-indie. Outline plus hair shadow make a 2 px dark band on the hair sides. Uneven sleeve stair at S f1 (y44-47).
4. **OL_open.** Looks broken: sleeve and coat flank vanish on snow. Floating 1 px fragments (S f1, x31 y41).
5. **OL_none.** Pleasant up close. At 1x the coat vanishes on snow, hair vanishes on navy, and the bow has no edge.

**Every mode:** alpha is already binary, with no halo in the sheets. The faint greys in pixelreview are previous-frame onion-skin.

## Locked rules
- **Exterior:** closed, pixel-perfect 1 px line, no L-doubles, monotone curve runs.
- **Lit side (top/left):** darkest tone of the wrapped material (hair→plum, bow→teal_0, skin→skin_0).
- **Light materials on snow:** next darker hue (oat→mauve), not oat_1.
- **Shadow side, bottom 2 rows, feet:** near-black #241628.
- **Contrast floor:** outline-to-ground luminance gap under ~15% (test #DFEAF6 and navy) → near-black.
- **No 2 px dark bands:** lift a shadow pixel touching the outline to mid.
- **Interior lines:** only at real overlaps (bangs/face, arm/torso, bow/hair), mid-dark, runs of 3 px or more, never black (eyes excepted).
- **Alpha:** binary, no AA or halo outside. 中間色 inside only, 1 px max.
- **QA gate:** fail on halo, orphan outline pixel, or exterior gap.
