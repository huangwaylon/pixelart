# Gemini 4 Argon critique: r19_blender_sprites

_Context:_ 48x64 RPG overworld hero sprite, 8 iso directions (S SE E NE N NW W SW), idle frame 0. Row 1 in each block is our current sprite S4_hd (SDF parts model, hand-tuned). Rows 2 and 3 are a new bake from an independent Blender anime character model (about 6.5 heads tall, long voluminous hair, ponytail, bow), rendered with the same camera (ortho, 16 deg), palette, pixel pass (majority-vote downsample, banded toon shading, sel-out outline, cleanup) and the same hand-designed face cels placed at the projected Blender eye positions. Row 2 is the model at true proportions scaled to the same height; row 3 is a chibi retarget (head bone x2.8, thighs x0.7, side locks swung back). Question: does either Blender bake improve on S4_hd (silhouette, face, bangs, bow, proportions)? Should we adopt the Blender model as the sprite source? Be specific about what is better and worse.

_Images:_ 00_REVIEW/r19_blender_sprites/compare_idle_8dir.png 00_REVIEW/r19_blender_sprites/faces_8x.png

### 1. Overall Verdict
**Do not adopt the Blender model (`Blender B`) in either form—keep `S4_hd` as your sprite source; `Blender B` destroys 1x readability, swallows the torso and costume in hair, and produces cramped, uncanny faces.**

---

### 2. Top 5 Problems Ranked by Impact

1. **Catastrophic Proportions & Torso/Costume Loss (`compare_idle_8dir.png`, Rows 2 & 3, all 8 directions, sprite y:18–36)**
   - **Problem:** Row 2 ("true proportions", 6.5 heads) is an unusable 6px-wide toothpick at 48x64 (`faces_8x.png` Row 2 S view is a 3px-wide faceless flesh pillar). Row 3 ("chibi retarget") only scaled the head bone (x2.8) while leaving the body 4–5px thin and letting the oversized hair hang down to the knees. As a result, the coat flare, arms/sleeves, and chunky scarf that give `S4_hd` its RPG hero silhouette are completely obliterated. In E, NE, N, NW, and W of Row 3, she reads as a giant floating brown hair-blob on a 4px stick leg.
   - **Concrete Fix:** Do not use bone-scaling on a 6.5-head anime mesh to fake SD/chibi pixel art. At this resolution (~38–42px tall character inside 48x64), the torso/coat must be **10–12px wide** (like `S4_hd`), with the scarf occupying a **3–4px tall** horizontal read across the chest/neck, and hair kept above or behind the shoulder line so the arms and coat hem remain visible in all 8 angles.

2. **Cramped Face & Side-Lock Claustrophobia (`faces_8x.png`, Row 3, S, SE, SW views, face region x:4–14, y:10–19)**
   - **Problem:** In `Blender B chibi` S view, the heavy front side-locks hang straight down over the cheeks, squeezing the face skin canvas down to **7px wide** (compared to `S4_hd`’s clean **11px wide** face). The 2x3px eyes are jammed against the dark brown hair border with zero skin breathing room on the outsides, and the 1px mouth sits 1px above the neck seam, making her look sunken and cross-eyed. In SE and SW, the 3/4 face is narrowed by 2–3px compared to `S4_hd`, pushing the far eye right into the contour line.
   - **Concrete Fix:** Push the side-locks back behind the jaw/ears so the front face skin is a full **11px wide × 6px tall** unobstructed canvas in S view (and **9–10px wide** in SE/SW), leaving **1px of skin** outside the outer eye corners before hitting the hair outline.

3. **Flat, Featureless Hair Mass & Missing Specular Halo (`faces_8x.png`, Row 3, all views, cranium y:4–14)**
   - **Problem:** `Blender B`'s voluminous anime hair geometry bakes down into a giant, flat mid-brown (`#6e4237`) pancake with almost no internal structure. It completely loses `S4_hd`’s signature **1–2px warm light-brown crown highlight band** (`#9b5f47`) across the bangs/top of the head, and in E/W views (`faces_8x.png` Row 3, E view) the ponytail projects so huge and low that it merges with the back of the head into a 17px-wide brown boulder (with a noisy 2×4px dark vertical slot in the middle).
   - **Concrete Fix:** Keep `S4_hd`’s compact ponytail silhouette (where a clean **2–3px negative-space notch** at the nape separates the ponytail tip from the coat back in E/W views) and maintain the **7–8px wide × 1–2px tall** light-brown crown highlight (`#9b5f47`) 3px below the top outline in all views.

4. **Messy, Noisy Bangs vs. Clean Pixel-Art Fringe (`faces_8x.png`, Row 3 S view, y:9–11)**
   - **Problem:** In `Blender B chibi` S view, the multi-strand 3D anime bangs downsample into two awkward, symmetrical 2px peach/highlight horns (`#d99578` / `#9b5f47`) poking into the forehead above the eyes, with a 3px flat step between them. In SE/SW/E, the bangs disappear into a vertical cliff.
   - **Concrete Fix:** Keep `S4_hd`’s stepped hime-cut / parted fringe: in S view, use a clean **1px skin notch** at the center-right part (`y:10`) flanked by two crisp **3px and 4px horizontal mid-brown fringe steps**, framed on the sides by 2px temple locks that stop at cheek level (`y:16`) rather than hanging to the waist.

5. **Bow Placement & Silhouette Detachment (`compare_idle_8dir.png` & `faces_8x.png`, Row 3, S, E, N views, top of head y:1–6)**
   - **Problem:** On `Blender B chibi`, the bow in S and N views sticks out horizontally like giant teal Mickey Mouse / goblin ears (**16px total span**, overhanging the skull silhouette by 3px on each side), while in E/W view (`faces_8x.png` Row 3, E) it collapses into a rigid **2px wide × 5px tall** vertical teal rectangle (`I`-shape) that doesn't read as a ribbon at all.
   - **Concrete Fix:** Keep the bow tucked within the head's horizontal silhouette in S view (**12px span**, angled upward into 3×3px triangular ears like `S4_hd`). However, borrow *one* thing from `Blender B`’s N/SE/NW bow: having a **1–2px dark teal knot center** separating the two ribbon loops reads slightly clearer from behind (`N` view).

---

### 3. What Is Working and Must Be Kept (in `S4_hd`, Row 1)
- **1x & 2x Instant Readability:** Look at the top-left 1x strips in `compare_idle_8dir.png`. `S4_hd` immediately reads as a charming GBA/DS RPG heroine: big bright face, unmistakable teal scarf + bow color triad, flared cream coat, and rhythmic 8-direction turnaround.
- **Face Appeal (`faces_8x.png` Row 1):** The 11px-wide face in S view and generous 3/4 cheek curve in SE/SW give the eyes, blush, and mouth room to breathe and emote.
- **Costume & Silhouette Hierarchy:** The separation of head → teal scarf collar → flared cream coat with lavender shadow → dark brown hem → boots creates 4 distinct horizontal tonal bands down the body, whereas `Blender B` collapses the top 75% of the sprite into brown hair.
- **Ponytail & Scarf Counter-Balance (E & W views):** In `S4_hd` E and W views, the ponytail jutting left/back balances the scarf tail and arms jutting right/forward, giving a lively, directional profile.

---

### 4. One Stretch Suggestion to Raise Appeal (Upgrade `S4_hd` Directly)
Instead of switching to `Blender B`, upgrade **`S4_hd`’s N, NE, and NW back-hair and bow** using the one thing `Blender B` hints at:
- Right now in `S4_hd` N view (`compare_idle_8dir.png`, Row 1, col 5), the ponytail is a very straight 4px-wide vertical column down the center of the back.
- **Actionable tweak on `S4_hd`:** Flare the lower half of the ponytail in **N, NE, and NW** by **+1px on each side** near the bottom tip (giving it a subtle pear/teardrop taper rather than a straight cylinder), and add a **1×2px darker teal knot** in the center of the bow in **N, NE, and NW** so the ribbon loops don't look like two disconnected teal blobs from behind.
