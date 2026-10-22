# R2 Art Director review: jump

**Verdict: REQUEST CHANGES (minor).** This is a big step up. At 18 deg the face, pigtails and scarf read in S/SE/SW, the pom is a separate ball, the bangs are clean and the boots have weight. What's left is polish.

## Cross-angle consistency
Yes, it's the same character in all 8 views. Proportions, palette, hat, scarf and boots match and the height looks stable. Three weak spots: E/W show a hard vertical hair/face seam, so the face reads as a pasted square. In N/NE/NW the braids merge into the hair into a flat brown "brim". In E/W the scarf tail and mitten merge into one yellow star blob.

## Fixes (max 6)
1. **Hat is still about 50% of the head, and it merges with the face in greyscale.** Change `beanie` radii `[10.4, 7.6, 10.2] -> [10.4, 6.6, 10.2]`, pom anchor y `18.6 -> 17.6`, and ramp `knit` `[cream_0, cream_1, cream_1] -> [cream_0, cream_0, cream_1]` so the cuff becomes a darker value band between hat and skin.
2. **E/W face seam.** Change `hair_cap` clip_any `[0, 0, -1, -0.3] -> [0, 0.5, -1, -0.3]` so the hairline slants: forward at the temple, back at the jaw.
3. **Braids fuse with the hair in back views.** Give `braid_L/R` their own group (`"group": "braid"`) so the inner outline is drawn against `hair_cap`. Also change rest_dir y `-1 -> -1.3` so they hang down instead of extending the hair sideways.
4. **Mittens are oversized and merge with the scarf.** Change `mitten_L/R` radii `[2.4, 2.5, 2.4] -> [2.0, 2.1, 2.0]` and `thumb_L/R` radii `1.1 -> 0.9`.
5. **Scarf blob in E/W.** Change `scarf_front` rest_dir `[0.35, -1, 0.35] -> [0.2, -1, 0.6]` so the tail hangs in front of the chest, not over the arm.
6. **Pixel override.** In NE and NW, all 12 frames, repaint the pale 1px rim on the hat's upper-left and upper-right silhouette edge with `outline` (#241628). Also check SE/SW f9 for any orphan pixels left on the cheek.
