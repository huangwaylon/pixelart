# Gemini 4 Argon critique: r15_face_bangs

_Context:_ Pixel-art game sprite (Pokemon GBA/DS style, girl with bob + beanie/bow). User requests verbatim: (1) 'the SE facing face the left eye (the eye on the right from our perspective), is still a bit weird looking. still too close I think?' (2) 'the bangs on the character should be longer, especially near the sides of the head, gentle slope, to cover more forehead. the forehead, esp on the sides are too exposed and the character looks bald'. r15 fix: SE/SW far eye now 2x3 with a catchlight, near cheek 1px wider, far cheek >=2px; bangs lowered with outer bangs longest and new temple bangs; E/W profile eye lowered 1 row. Image 1 is before/after faces at 8x (S, SE, E, SW, N); image 2 is head crops of every SE/SW frame across clips. Judge whether each of the two user requests is solved, and list the top 3 remaining issues, per pixel where possible.

_Images:_ 00_REVIEW/r15_face_bangs/before_after_faces.png 00_REVIEW/r15_face_bangs/se_sw_all_clips_a.png

### (1) Overall Verdict
r15 successfully fixes the bald temple/forehead problem and makes the SE/SW far eye readable, though the 2px-wide far eye still leaves only a 2px bridge between the eyes (feeling slightly crowded) and the lowered bangs now crash directly into the happy/squint eyes during `jump_sc` and `land`.

---

### Evaluation of the Two User Requests

1. **Request 1 (SE/SW far eye weirdness & spacing):** **Mostly Solved (80%).**
   * **What improved:** Expanding the far eye from a cramped 1x3 sliver to a 2x3 block with a 1px white catchlight (`before_after_faces.png`, SE/SW `after (r15)`) stops it from looking like a stray vertical scar, and the 2px far cheek gives the face proper 3/4 turn volume.
   * **What remains:** Because the far eye was widened *inward* to 2px while the near eye stayed in place, the skin bridge between the two eyes is still only **2px wide** (same as S view, or tighter visually because both catchlights sit on the inner columns facing each other). In 3/4 view, foreshortening should compress the *far eye width* (1px iris + 1px catchlight/lash, or shift the near eye 1px toward the ear) rather than pinching the nose bridge.
2. **Request 2 (Longer bangs, gentle slope at sides, cover forehead/temples):** **Solved (95%).**
   * **What improved:** The stepped side bangs in S, SE, SW, and E (`before_after_faces.png`, `after (r15)`) completely eliminate the "bald/receding hairline" boxiness of v1. The 1–2px dark/mid-brown steps framing the upper cheeks read immediately as a soft bob/hime-cut taper.

---

### (2) Top 3 Remaining Issues (Ranked by Impact, Plus Actionable Fixes)

#### 1. Lowered bangs collide with happy `^ ^` / `> <` eyes, turning them into angry/stitch marks
* **Location:** `before_after_faces.png` (`jump_sc f7 after (r15)` in S, SE, SW) and `se_sw_all_clips_a.png` (`jump_sc` SE/SW frames 3–7 & 10, `land` SE/SW frames 1–2; at the top row of the dark eye arch, ~y=11–12 of head).
* **Problem:** In v1, the `^ ^` happy arches had 1px of skin clearance above them. In r15, the lowered bangs sit directly on top of the peak pixel of each `^` eye. With zero skin pixels above the arch, the dark eye pixels merge into the dark hair shadow row, reading like furrowed angry brows or jagged vertical scars instead of cheerful closed eyes.
* **Pixel Fix:** On all closed-arch / squint frames (`jump_sc` f3–f7, f10; `land` f1–f2):
  1. Flatten the eye arch by **1px vertically** (use a 3px-wide, 2px-tall soft curve where the top center is 1px lower, OR shift the closed eye arch **down 1px** so its peak sits on the middle eye row rather than the top eye row).
  2. Restore at least **1px of mid-skin/shadow-skin** between the top of the dark eye pixels and the bottom of the brown bangs.

#### 2. SE/SW inner eye bridge feels pinched because both catchlights face inward across a 2px gap
* **Location:** `before_after_faces.png` (`idle f1 after` and `run f3 after`, SE and SW columns) and across open-eye frames in `se_sw_all_clips_a.png` (center of face between near and far eye).
* **Problem:** In SE `idle f1 after`, reading left-to-right across the top eye row: `[near eye: 2px dark, 1px white] -> [2px skin bridge] -> [far eye: 1px white, 1px dark]`. Having both white catchlights on the inner columns facing each other across a 2px skin gap draws the viewer's focus into the center of the bridge, making her look slightly cross-eyed / eyes too close together—the exact issue the user flagged.
* **Pixel Fix:**
  1. **Standardize catchlight direction** (light source from top-left or viewer-left, matching the hair highlight): in **SE**, place the catchlight on the **left** column of the near eye (`[1px white, 2px dark]`) and the **left** column of the far eye (`[1px white, 1px dark]`). This immediately adds 1px of dark pupil between the near catchlight and the nose bridge, visually widening the separation without moving the eye sockets.
  2. **(Optional stronger fix for SE/SW):** Shift the **near eye 1px toward the back of the head** (left in SE, right in SW)—you just widened the near cheek by 1px in r15, so moving the near eye 1px outward into that cheek space opens the inter-eye bridge from **2px to 3px**, which completely cures the "too close" read.

#### 3. E Profile (`run f3 after` and `jump_sc f7 after`) loses the temple side-lock and clips the eye into the hairline
* **Location:** `before_after_faces.png`, column `E`, rows `run f3 after (r15)` and `jump_sc f7 after (r15)` (forehead/temple region just left of the eye).
* **Problem:** In `idle f1 after` (E), lowering the eye 1px worked great and there is a nice stepped brown sideburn/temple lock to the left of the eye. However, in `run f3 after` (E), the loweredbangs overwrite the top of the eye socket so the white catchlight touches the brown bangs directly with a flat horizontal cut, and in `jump_sc f7 after` (E) the happy eye arch touches the outer face outline and bangs with only 1px of stray highlight skin trapped above it (an orphan pixel).
* **Pixel Fix:**
  1. In **E `run f3 after`**, raise the single brown bang pixel directly above the white eye catchlight by **1px** (restore 1px of skin above the eye so the E run expression matches E idle's clean read), and bring the temple sideburn lock down **1px** on the column left of the eye to keep the sloped bang silhouette consistent with `idle f1`.
  2. In **E `jump_sc f7 after`**, replace the trapped 1px light-skin orphan above the happy eye with **mid-brown hair**, and move the dark happy-eye pixels **1px down and 1px left** away from the outer face outline.

---

### (3) What Is Working and Must Be Kept
* **S-view `idle f1` and `run f3` (r15):** Spot-on GBA/DS protagonist proportions. The 1px stepped outer bangs frame the face with a cute, rounded curve that completely fixes the v1 "boxy forehead" look.
* **E-view `idle f1` (r15):** Lowering the profile eye 1px and bringing the bangs down makes her look much younger, softer, and on-model with the S view.
* **2px far-cheek width in SE/SW (`se_sw_all_clips_a.png`):** Gives the far side of the face enough flesh and blush room so the far eye never merges into the dark outer face outline during `walk` and `run` bobbing.

---

### (4) One Stretch Suggestion to Raise Appeal
* **Add 1px of warm-skin/peach brow-shadow (anti-aliasing) at the inner bang steps in S/SE/SW:** Right where the brown bangs step up 1px over the bridge of the nose, placing a single pixel of the **darker skin-shadow/blush tone** directly under the step softens the hard brown-to-light-skin contrast and gives the bangs a sense of hovering slightly off the forehead, just like *Pokémon HeartGold/SoulSilver* overworld heroines.
