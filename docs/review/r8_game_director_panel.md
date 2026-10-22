# r8 Panel: Game Director (jump_v2)

All 6 pass QA. Metrics come from `/tmp/gd_r8/metrics.py` on the `ready` frame in 8 directions. C5's build hash differs from the others (5d706ea74afb), so it may have been rebuilt.

| | Area px | Body CR snow / dark | Melt % on dark | IoU S-N / E-W / all | S-N value diff | Width swing px | Jaggies | Score |
|---|---|---|---|---|---|---|---|---|
| C1 twintails | 503 | 5.2 / 1.40 | 77 | .82 / .78 / **.72** | .215 | **6.5** | 58 | **4** |
| C2 hime beret | 470 | 4.4 / 1.71 | 55 | .90 / .85 / .85 | **.229** | 3.9 | 27 | 3 |
| C3 sidepony cat | 464 | 4.8 / 1.52 | 63 | **.81** / .83 / .79 | .226 | 4.1 | 26 | **4** |
| C4 snow hood | 449 | 2.7 / **2.75** | **12** | .94 / .82 / .86 | .201 | 2.2 | 33 | **4** |
| C5 buns ribbon | 438 | 5.5 / 1.33 | 77 | .92 / .93 / .84 | .142 | 2.8 | **12** | 3 |
| C6 bob no hat | 417 | 4.7 / 1.63 | 59 | .94 / .91 / .89 | .167 | 2.8 | 77 | 2 |

CR is the WCAG contrast ratio vs #DFEAF6 and #3E4A6E. Melt % is the share of interior pixels within 1.5:1 of the dark tile. Lower IoU means better silhouette facing.

**Shared problem:** the outline only reaches about 1.7:1 against the dark tile. Before ship, add a rim light or a lighter outline on dark tiles.

- **C1:** Biggest silhouette and clearest facing. The twintail flap gives the best airborne cue. Brown hair blends into dark tiles.
- **C2:** The red beret is a locator on both grounds. Blocky silhouette, and the hair disappears on dark.
- **C3:** Side-pony asymmetry gives the best S-N silhouette split, and the pony flip reads mid-air.
- **C4:** The only one that holds up on dark ground, and the fur ring frames the face. Little hair or motion, which misses the brief.
- **C5:** Cleanest pixels, but the weakest facing (symmetric buns, flat back).
- **C6:** Smallest, disappears on dark, and has the most jaggies.

Hair motion helps readability when it changes the outline (C1, C3). C4 has almost none.

**Show the user: C1, C3, C4, C2.** C5 is the alternate.
