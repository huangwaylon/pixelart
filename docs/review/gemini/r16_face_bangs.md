# Gemini 4 Argon critique: r16_face_bangs

_Context:_ User request (verbatim): 'The face looks a bit too fat, that's why i asked for a more realistic, pointy, curved face. at least, the bangs should be more volumous and come off the forehead more, for a more layered, dynamic look'. This is a 48x64 Pokemon-GBA/DS style pixel sprite girl (bob + beanie). Images show r15 (before) vs r16 (after) at 8x, and a hi-res model render. Judge at 1x/2x sprite size whether the request is solved: is the face visibly slimmer and pointier? Are the bangs voluminous, lifted off the forehead, layered? In the S (front) view the new fringe may read as evenly spaced dark vertical bars (comb/barcode) over a skin-shadow band that could read as a headband. Give concrete pixel-level fixes for the S fringe (clump count/width, where dark goes, shadow row, highlights).

_Images:_ 00_REVIEW/r16_face_slim_bangs/before_after.png 00_REVIEW/r16_face_slim_bangs/head_hires_before_after.png

**(1) Overall Verdict**
The user’s request is **not solved** at 1x/2x: the 3D mesh adjustments were too subtle to cross the pixel-quantization threshold for the jaw, while the lifted bangs created an unintended "barcode/comb" artifact over a dark "headband" shadow in the front (S) view.

---

**(2) Top 5 Problems Ranked by Impact**

1. **S-View "Barcode" Fringe & "Headband" Shadow (Bangs Readability Failure)**
   * **Location:** `before_after.png`, Column `S` (all rows: `idle f1`, `run f4`, `jump_sc f7`, `throw f3` after r16), forehead region `x≈17..30, y≈14..16`.
   * **Problem:** Because the 3D hair tubes are narrow and uniform (`head_hires_before_after.png`), downsampling turns the gaps between bangs into 3–4 evenly spaced 1px vertical dark-brown (`#4A2A38`) teeth, sitting directly above a continuous 1px horizontal row of dark skin-shadow (`#D3846C`). At 1x, this reads as a comb or a dark headband rather than layered hair.
   * **Concrete Pixel Fix (S-View Fringe Blueprint, `x=17..30` across the 14px forehead):**
     * **Clump Count & Width:** Group the bangs into **3 asymmetric clumps** of `mid-brown` (`#7B443E`) instead of 1px teeth: Left clump = **4px wide** (`x=17..20`), Center-main clump = **5px wide** (`x=22..26`, dipping 1px lower at `x=23..25, y=16`), Right clump = **3px wide** (`x=28..30`).
     * **Where Dark Goes:** Use `dark-brown/outline` (`#4A2A38`) **only** as 1px V-notches *higher up* (`y=14`) at `x=21` and `x=27` to separate the 3 clumps. **Delete** all vertical dark bars extending down to `y=15`.
     * **Shadow Row (`y=15..16`):** Break up the continuous horizontal headband shadow. Place `skin-shadow` (`#D3846C`) **only** directly beneath the lowest hair tips (`x=18..19` and `x=23..25`, 1px tall), leaving `base-skin` (`#F3B29A`) visible in the V-notch gaps (`x=21`, `x=27`) so the forehead breathes.
     * **Highlights:** Shift the `light-brown` (`#9A5A4E`) crown highlight down 1px onto the curve of the center clump (`x=22..25, y=12..13`) and left clump (`x=18..19, y=12`) to sell forward puff/volume.

2. **Face Width & Jaw Taper Unchanged at Sprite Scale (S & SE Views)**
   * **Location:** `before_after.png`, Columns `S` and `SE` (all rows), lower cheeks and chin `x≈16..31, y≈19..24`.
   * **Problem:** In `S`, the face is still a flat-bottomed 12px-wide rectangle of skin at eye/cheek level (`y=19..22`) stepping abruptly into the scarf. In `SE`, the far cheek (`x≈31..32, y=18..22`) still bulges out identically to r15. The face does not read as slimmer or pointier.
   * **Concrete Pixel Fix:**
     * **In `S`:** Pull the inner border of both side-locks (`#4A2A38` / `#7B443E`) inward by **1px** at cheek level (`x=18` and `x=29`, `y=20..22`), narrowing the lower face by 2px total. At the chin center (`x=23..24, y=23`), push `base-skin` (`#F3B29A`) **1px down** into the top row of the teal scarf, flanked by `skin-shadow` (`#D3846C`) at `x=21..22` and `x=25..26, y=22` to create a V-taper.
     * **In `SE`:** Shave **1px** of `base-skin` off the far right cheek (`x=31, y=20..22`), pulling the dark outline (`#38202C`) left by 1px so the cheek curves inward toward the chin tip (`x=28..29, y=23`).

3. **Profile (E & W) Bangs Still Flat Against Forehead Silhouette**
   * **Location:** `before_after.png`, Columns `E` and `W` (all rows), front hair outline `E: x≈30..32, y≈11..16` / `W: x≈15..17, y≈11..16`.
   * **Problem:** While the hi-res E profile shows the bangs slightly lifted, at 1x the outer front silhouette of the hair in `E` and `W` didn't move a single pixel outward. The forehead still looks flat and vertical.
   * **Concrete Pixel Fix:** In `E` (and mirrored in `W`), extend the frontmost fringe tip **1px outward** (right in `E` at `x=32, y=12..14`) using `mid-brown` (`#7B443E`) on the inside (`x=31`) and `dark-outline` (`#38202C`) at `x=32`, leaving a 1px notch at `y=15` before the eye/brow begins. This gives an immediate curved overhang over the face.

4. **SE / SW 3/4 View Fringe Reads as a Heavy Dark Brow Block**
   * **Location:** `before_after.png`, Columns `SE` and `SW` (`idle f1`, `run f4` after r16), `SE: x≈23..30, y≈14..16` / `SW: x≈17..24, y≈14..16`.
   * **Problem:** Raising the bangs exposed a 2px-thick cluster of `dark-brown` (`#4A2A38`) cast shadow right above the eyes (`y=15..16`), making her look angry or heavy-browed rather than airy and layered.
   * **Concrete Pixel Fix:** Replace the `dark-brown` (`#4A2A38`) pixels at `SE: x=24..29, y=15` with `mid-brown` (`#7B443E`) in two diagonal steps (`x=24..26, y=15` and `x=28..29, y=15`), and use only 2 pixels of `skin-shadow` (`#D3846C`) at `x=25, y=16` and `x=28, y=16`. Leave `x=27, y=15..16` as `base-skin` (`#F3B29A`) for a clean parted-bangs slit.

5. **3D-to-2D Pipeline Root Cause (Why r16 Missed)**
   * **Location:** `head_hires_before_after.png`, all 3 views.
   * **Problem:** At 48x64 resolution, 1 sprite pixel equals roughly 6–8% of head width. The r16 3D edits moved the jawline inward by less than half a pixel's worth of screen space, and modeled the bangs as 8+ thin individual cylinders. Thin cylinders smaller than 2 sprite pixels wide always alias into noisy vertical stripes ("comb teeth") when downsampled.
   * **Concrete Pixel Fix (if fixing via 3D mesh before pixel pass):** Merge the 8 thin front hair cylinders into **3 wide, overlapping flat ribbons** (3–5px wide each at sprite scale), push them forward off the forehead by a full **1.5–2 sprite pixels**, and pull the lower cheek vertices (`y=20..22`) inward by at least **1.5 sprite pixels** per side with a sharper chin point pushing 1px down over the scarf collar.

---

**(3) What Is Working and Must Be Kept**
* **Overall GBA/DS Proportions & Palette:** The head-to-body ratio, cozy teal scarf/bow contrast against the warm brown hair, and soft purple-brown outlines (`#38202C`) are spot-on for the style.
* **Expression Readability (`jump_sc f7`):** The happy `^ ^` eyes and blush placement in `jump_sc f7` read clearly at 1x and have great charm—keep the eye/blush coordinates intact while tucking the lower cheek contour in by 1px beside them.
* **Side-Lock Framing in 3/4 (`SE`/`SW`):** The near-side hair lock framing the cheek in `SE` (`x=19..21, y=16..24`) separates the head from the ponytail cleanly.

---

**(4) Stretch Suggestion to Raise Appeal**
* **Add a 1px "Airy Overlap" Silhouette Break on the Outer Bangs (`S` & `SE`):** At the temple where the bangs meet the side-locks (`S: x=15, y=13..14` and `x=32, y=13..14`), flare the outer silhouette out by **1px** (`#38202C` outline + `#7B443E` fill) and tuck it back in by 1px at `y=16`. Combined with the narrower jaw at `y=20..22`, this creates a classic anime heart/diamond head taper (wider, fluffy top bangs → tapered, delicate chin) that instantly makes the face look slimmer without losing chibi appeal.
