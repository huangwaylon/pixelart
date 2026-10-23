# Gemini 4 Argon critique: r13_illustrations_r2

_Context:_ Second pass after fixes on hand-pixelled anime girl (bob + beanie, Pokemon GBA/DS style). Prior critique flagged: hair clumps, shoulders, scarf shadow, nose, vein, blush on bust; curved hem, back-hair V, ponytail tip on turnaround; recoil lock, shy/shiver hem on poses. List what improved and any remaining top 3 issues.

_Images:_ 00_REVIEW/r13_anime_pixel/bust/bust_sheet_x3.png 00_REVIEW/r13_anime_pixel/turnaround/turnaround_x3.png 00_REVIEW/r13_anime_pixel/poses/poses_lineup_x3.png

### (1) Overall Verdict
A massive leap toward production-ready DS/GBA dialogue and overworld sprite quality—most structural and shading notes were nailed, leaving only a few critical tangents, flat-hem regressions, and a severed limb bug on the pose sheet.

---

### What Improved Since Pass 1
* **Bust (`bust_sheet_x3.png`):**
  * **Shoulders & Scarf Drop Shadow:** The shoulder slope now has natural anatomical weight, and the 1–2px cast shadow directly beneath the teal scarf wrap (and along the hanging tail) grounds the scarf onto the cream coat instead of floating.
  * **Hair Clumps:** The bangs and side-locks read as cohesive volumes with clean dark-brown crevice dividers rather than noisy single-pixel strands.
  * **Nose, Blush & Angry Vein:** The 2px shadow-only nose hint sits cleanly without fighting the mouth; the diagonal blush hashes (`02`, `03`, `07`, `10`) and the high-contrast red anger mark (`06_angry`) read instantly at 1x.
* **Turnaround (`turnaround_x3.png`):**
  * **Coat Hem Curve:** `front`, `three_quarter`, `side`, and `back` now step up 1px at the outer corners, giving the flared A-line coat proper cylindrical wrap.
  * **Back-Hair V & Ponytail Tip:** The `back` view central ponytail now tapers to a clean V-point over the lower hair mass, and the `three_quarter` / `side` ponytail tips have a crisp 1px tapered flick.
* **Poses (`poses_lineup_x3.png`):**
  * **Recoil Hair Lock:** The flying hair lock in `recoil` has a much cleaner arc and secondary motion.

---

### (2) Remaining Top 3 Problems (Ranked by Impact)

1. **Severed Left Leg / Floating Gap + Missing Hem Trim (`poses_lineup_x3.png` — `recoil`, bottom-left panel, approx. x:35–42, y:108–112 in local 1x sprite coords)**
   * **Problem:** Her raised left thigh (viewer's left) has a **1px background-colour gap** between the top of the dark-grey legging outline and the bottom of the coat hem—her leg is literally detached and floating. Furthermore, the right side of the coat hem (viewer's right, x:43–52, y:107) is missing its brown trim fill and drops into a flat, un-curved line.
   * **Fix:** Move the entire raised left leg up by 1px (or extend the dark-purple thigh outline + dark-grey fill upward by 1–2px) so it tucks cleanly behind the dark-brown coat hem outline. Paint in the missing 1px warm-brown trim row across the right half of the hem and step the outer right corner up 1px.

2. **Coat Hem Regressed to Dead-Flat Ruler Line on Poses (`poses_lineup_x3.png` — `shy` and `shiver` [plus `wave`, `point`, `hands_on_hips`], coat bottom edge at y:107)**
   * **Problem:** While `turnaround_x3.png`, `idle`, and `cheer` now have the nice curved hem, `shy` and `shiver` (along with the top-row action poses) still have a 26px-wide dead-horizontal ruler line for the bottom of the skirt, killing the 3D cylinder of the coat. Additionally, `shiver` still has faint 1px light-blue/grey orphan pixels clinging to the outer skirt silhouette (x:24–26, y:92–104) that look like stray compression/rough sketch artifacts rather than intentional cold-air VFX.
   * **Fix:** Copy the 2px corner step-up from `turnaround` `front` onto the bottom corners of `shy`, `shiver`, `wave`, `point`, and `hands_on_hips` (raise the outermost 3px on both left and right edges by 1px in dark-brown outline + mid-brown trim). Erase the stray pale-grey pixels hugging the left skirt edge on `shiver`.

3. **3/4 & Side Ponytail Silhouette Fuses Into Back Hair (`turnaround_x3.png` — `three_quarter` at x:55–62, y:25–58 and `side` at x:58–66, y:25–62)**
   * **Problem:** Even though the bottom tip of the ponytail was improved, the ponytail mass in `three_quarter` and `side` runs parallel to and flush against the back of the bob cut. From neck to waist it reads as one thick, heavy wall of brown hair rather than a high ribbon-tied ponytail springing *out* from a shorter bob.
   * **Fix:** Carve a 2px-wide, 4px-tall notch of background sky colour between the lower bob edge and the inner curve of the ponytail around shoulder level (approx. y:42–48 in 1x), and shift the mid-section of the ponytail 1px further right to bow out its silhouette arc.

*(Bonus minor note — #4 for polish: In `bust_sheet_x3.png`, the bottom-most row of the teal scarf wrap at the collar [approx. y:66] is a 19px straight horizontal line. Dropping the center 7px down by 1px will make it hug the roundness of her neck/collarbone.)*

---

### (3) What Is Working and Must Be Kept
* **Expression Readability & Charm (`bust_sheet_x3.png`):** Every single expression (`02_smile` through `10_content`) reads unmistakably at 1x. The eye shapes in `05_sad`, the brow angle in `08_determined`, and the cat-mouth `07_embarrassed` have authentic GBA/DS visual-novel charm.
* **Colour Palette & Material Contrast:** The warm cream coat against the saturated teal scarf/ribbon and rich chestnut hair has superb value separation and warmth.
* **`cheer` Pose (`poses_lineup_x3.png`):** Best pose on the sheet—the flying scarf tail, split twin-tail/back-hair silhouette under the arms, curved coat hem, and staggered jump boots have great energy and zero stiffness.

---

### (4) Stretch Suggestion to Raise Appeal
* **Differentiate the Bob vs. Ponytail Silhouette in `point` and `recoil` (`poses_lineup_x3.png`):** Just like in `cheer`, whenever she moves dynamically (`point`, `recoil`), let the shorter shoulder-length bob stay near her neck while the ribbon-tied ponytail arcs higher and further back with a clear gap of negative space between them. That two-layered hair silhouette is the signature hook of her character design—pushing the negative space between bob and tail will make her silhouette 2x more dynamic at 1x scale.
