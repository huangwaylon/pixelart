# r8 Panel: Art Director (jump_v2, pixel review)

Small fixes applied and rebuilt; all 6 pass QA. Originals: `/tmp/ad_r8/bak/`.

| | Cute | Dot-e | Line | Distance | X-dir | Total |
|-|-|-|-|-|-|-|
| C1 twintails | 5 | 5 | 3 | 5 | 3 | **21** |
| C3 sidepony cat | 4 | 4 | 4 | 4 | 4 | **20** |
| C4 snow hood | 5 | 4 | 4 | 4 | 3 | **20** |
| C2 hime beret | 4 | 4 | 4 | 3 | 3 | **18** |
| C5 buns ribbon | 4 | 3 | 5 | 3 | 3 | **18** |
| C6 bob no hat | 3 | 3 | 2 | 2 | 4 | **14** |

## Fixes per candidate (✓ = applied)
- **C1:**
  - ✓ Moved `muff_L/R.center` to `[±11, 9.0, -2.4]`.
  - ✓ Scaled the bow radii by 1.25.
  - Shrink the oat earmuff band.
  - Tail `widths` `[3.4, 3.0, 2.3, 1.4]` to cut the jaggies (59).
- **C2:**
  - ✓ `hair_blueblack` set to `[ink, char_1, char_1, lav_1]`.
  - ✓ `beret.radii` set to `[8.2, 1.9, 7.4]`, rot 20.
  - Still a red dome in E/W: move `beret.center` z to -1.6. Enlarge the ribbon loops to 2.2.
- **C3:**
  - ✓ `beanie.radii` y reduced from 4.8 to 4.2. Bigger ears broke the height QA, so I reverted them.
  - The plum_0 hair merges with the outline: use `[plum_0, hair_1, hair_1, hair_2]`.
  - Raise the ears and lower the beanie by the same amount.
- **C4:**
  - ✓ `hair_espresso` set to `[plum_0, hair_1, hair_1]`.
  - Move `hood_fur_7..9` back by 1.0 in z, because the E face is only 2 px.
  - Change the teal mittens to oat.
- **C5:**
  - ✓ Widened `bun_L/R.radii` to `[4.5, 4.0, 4.2]`. Taller broke QA.
  - The flat hair mass needs a clump line.
  - Move the buns to x ±7.6 so they separate in E/W.
- **C6:**
  - ✓ Ahoge `widths` set to `[1.6, 1.0]` and `rest_dir` to `[1, .55, .2]`.
  - The crown ends in a 1 px nipple: use `hair_volume` 1.05.
  - The bob reads as a helmet: add cheek flip prims.
  - Use a crn `scarf` ramp, because the cream scarf merges with the face.

**Dark tiles (GD note):** I agree. Every hair mass except C4's melts at about 1.5:1. Pipeline fix: a 1 px light rim (lav_1/snow_2) on the lit outline, applied only on dark backgrounds. A global lighter outline would break sel-out on snow.

## Ranking
1. **C1:** the archetypal Lyra-style read, with the best silhouette and wing-flare on landing.
2. **C3:** asymmetric and playful, with the best S/N split.
3. **C4:** the cutest front view and the only one that holds up on dark tiles, but the back views are a red ball.
4. **C2:** elegant dark/cream/red, but an egg silhouette.
5. **C5:** the cleanest pixels (12 jaggies), but plain.
6. **C6:** 73 jaggies, a helmet silhouette, and it disappears at 1x.

**Show the user: C1, C3, C4, C2, C5.** Drop C6, or rework it as the hatless reference.
