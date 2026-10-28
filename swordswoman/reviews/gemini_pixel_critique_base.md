# Gemini pixel critique: base idle f00, all 8 directions

Model: Gemini (tools/gemini.py ask), 2026-10-24. Inputs: refs/1.png, concept/chibi_iso_v5.png, reviews/gemini_pixel_critique_base_input.png (pixel/base/idle/<DIR>/f00.png, crop x41-87 y44-120 of the 128 cell, 6x nearest-neighbour, order S SE E NE / N NW W SW). Base = renders/model_round_6 snapshot.

**AD verification notes (not Gemini).** Each point was checked against palette-code dumps of the base frames. See docs/pixel_cleanup_guide.md section 6 for what was accepted and what was rejected. Rejected in short: a centred bow (the bible places it on her right side of the bun; rejected in model rounds 3 and 5 too); "the sword is on the wrong side in E/NE" (the 3D render is handedness-correct, left hand, never mirrored); white sclera / 2x2 eyes (no sclera colour in the locked palette, and the bible eye is 4 px tall); "illegal purple" (the bible allows <=3 px purple at the right upper-arm lace). Confirmed: flat h0 hair masses, missing hilt/hand, blob guard, irregular blade stair, eye glint/far-eye errors, ribbon vs skin value merge, dark r1 skirts in NW/W, clubbed feet, ragged hems, stray 1 px pixels.

---

Here is the pixel-level art direction audit for the 8-direction idle turnaround. This pass looks like an uncleaned 3D-to-pixel bake or an AI-assisted block-in. It violates core pixel-art fundamentals across every frame: rampant 1px noise, broken selective outlines, inconsistent weapon hand/placement, and unreadable micro-clusters.

---

### **1. S (South / Front)**
*   **Stray/errant pixels:** 1px dark brown dot in the middle of the red skirt (left of the leg slit); 1px pink pixels floating inside the red collar/shoulder area on both sides.
*   **Outline issues:** Double-thick #1a1220 blocks at the inner groin/top of the legs; missing exterior outline on the upper-left bow ear; jagged stair-stepping along the screen-left sleeve flare.
*   **Face:** Eyes are asymmetrical (screen-left eye has a 2px dark brow/lash line, screen-right has 1px); eye whites bleed into skin tone without clear vertical alignment; nose/mouth area is completely blank, making the lower face look flat into the high collar.
*   **Hair/bangs:** Forehead bang line is a flat horizontal bar with a single awkward 1px notch on the screen-left; hair highlight is a 4px flat horizontal dash that doesn't follow the spherical volume of the cranium.
*   **Bow:** Pushed entirely to the screen-left of the bun instead of sitting centered behind/atop the bun knot; reads as a deformed tumor rather than two distinct bunny ears.
*   **Bun:** Sitting off-center to the screen-right to compensate for the lopsided bow; highlight is noisy.
*   **Sword blade + hook guard + hilt:** **No hilt visible above the hand**; crescent hook guard is a blurry 3px grey hook that merges into the skirt hem; blade uses a 1px staircase pattern that creates severe sawtooth aliasing down the entire length.
*   **Scarf ribbons:** completely missing as distinct trailing shapes; reduced to noisy pink pixels trapped inside the collar/shoulder silhouette.
*   **Legs/feet/heels:** Legs are straight 2px-wide vertical sticks with zero taper; strappy heels read as clubbed hooves with a random 1px skin dot trapped at the very tip of the toes.
*   **Skirt hem:** Asymmetrical and noisy; the front slit doesn't show the black shorts clearly (just a 2px dark blob).
*   **Value grouping / readability:** The chest, high collar, and shoulders merge into a single flat mid-red blob; the corset lacks vertical structure and reads as a muddy brown horizontal band.
*   **Palette use:** Pink rim light is applied to the screen-right edge of the hair and bun, which works, but the same pink is used as skin/collar anti-aliasing on the chest, ruining material separation.

---

### **2. SE (South-East)**
*   **Stray/errant pixels:** 2px purple/magenta errant pixels on the screen-left edge of the waist/corset (supposed to be the shoulder cord ornament, now floating on the ribcage); 3 dark brown stray spots scattered on the lower front skirt.
*   **Outline issues:** Broken outline on the screen-left pink ribbon tip; jagged double-pixel dark corners under the skirt hem between the legs; missing outline separating the chin from the red collar.
*   **Face:** Screen-right (far) eye is squashed against the black exterior outline, losing the 3/4 cheek turn; screen-left eye is a 2x2 blue block with no clear sclera or lash definition.
*   **Hair/bangs:** Sideburn/ear lock on screen-left is a chunky square block; pink rim light on the screen-right edge of the head is 2px thick in spots, flattening the skull silhouette.
*   **Bow:** Reads as one giant fused red blob on the top-left of the head; zero separation between the left and right bow ears.
*   **Bun:** Completely swallowed by the red bow on the left and only visible as a small brown bump on the right.
*   **Sword blade + hook guard + hilt:** Hilt is once again invisible; guard is a C-shaped grey claw attached directly to the red sleeve cuff; blade has a 2px-wide black outline on the bottom edge and a 1px outline on the top, making it look bent.
*   **Scarf ribbons:** One thick pink sausage extruding from the screen-left neck; looks like a rigid horn or arm rather than a flowing ribbon.
*   **Legs/feet/heels:** Feet are tiny dark triangles; the back (screen-right) foot is raised higher than the front foot, breaking the isometric ground plane; straps are unreadable noise.
*   **Skirt hem:** Left side terminates in a ragged, noisy dark-red fringe with single-pixel teeth.
*   **Value grouping / readability:** The front skirt is peppered with random dark brown/red 1px and 2px spots (attempting folds/tassels) that look like dirt splatters.
*   **Palette use:** Illegal use of purple pixels at the waist; over-dithering of mid-red and dark-red on the skirt.

---

### **3. E (East / Profile)**
*   **Stray/errant pixels:** 1px blue pixel floating outside the face outline at the eye tip; 1px dark brown speckles scattered inside the red skirt volume; 1px skin pixel floating detached in the back neck area.
*   **Outline issues:** Severe 1px staircase jaggies down the back of the skirt; open outline gaps on the top of the bow and the tip of the trailing ribbon.
*   **Face:** Eye extends all the way to the frontmost edge of the head with a single blue pixel poking out like a horn; profile nose/mouth silhouette is a vertical flat wall.
*   **Hair/bangs:** Ear/sideburn is a vertical 2px column cutting straight down the head; crown highlight is a scattered 3-pixel dither.
*   **Bow:** Sits on the very front of the bun like a visor instead of behind/around the knot.
*   **Bun:** Pushed to the back-right of the bow, reversing the canonical anatomy shown in the concepts.
*   **Sword blade + hook guard + hilt:** Sword is held out in front of the body (even though it's in the left/far hand in an E profile, meaning the arm would have to reach across the chest); guard is a vertical grey bracket; blade is thinner and steeper than SE/NE.
*   **Scarf ribbons:** Single straight diagonal pink bar sticking out the back; lacks curve or taper.
*   **Legs/feet/heels:** Both feet are fused or aligned into a single flat horizontal line at the bottom of the skirt; zero heel silhouette visible.
*   **Skirt hem:** Complete disaster—shredded into 1px vertical icicles and random holes on the bottom-left.
*   **Value grouping / readability:** The arm, corset, and skirt are completely indistinguishable; the mid-body is a chaotic soup of red, brown, and skin-tone single pixels.
*   **Palette use:** Skin tone, light red, and pink ribbon colour all merge at the shoulder/neck junction with zero contrast.

---

### **4. NE (North-East)**
*   **Stray/errant pixels:** 1px blue pixel on the far-right edge of the head (eye bleeding into a back-three-quarter view where it shouldn't be seen, or stray hair highlight); 1px purple pixel on the far-right waist edge.
*   **Outline issues:** Heavy black #1a1220 stair-stepping along the sword blade; missing outline on the left edge of the pink ribbon where it overlaps the red cape/collar.
*   **Face:** Cheek/jaw profile on screen-right is boxy and protrudes too far forward; ear merges directly into the neck skin without hair separation.
*   **Hair/bangs:** Back of the cranium has a jagged pink rim-light line that breaks the roundness of the head.
*   **Bow:** Looks like a small red flame sticking out the top of the bun; no ear split.
*   **Bun:** Positioned below the bow, reading as a double-stacked lump.
*   **Sword blade + hook guard + hilt:** **MAJOR CONTINUITY ERROR:** The sword has jumped from the screen-right side (E) to the screen-left side (NE), which is correct for the left hand, *except* in E it was drawn on the right! Guard hook points up/left awkwardly; no hilt visible.
*   **Scarf ribbons:** Ribbon trails down the left side directly over the red sleeve and sword guard, creating a low-contrast pink-on-light-red tangency.
*   **Legs/feet/heels:** Feet are tiny stubby dark blocks peeking out from the skirt hem; zero leg shaft visible.
*   **Skirt hem:** Jagged, asymmetric sawtooth bottom edge with 2px vertical spikes.
*   **Value grouping / readability:** Back exposure/cutout of the dress reads as a rectangular skin-colored patch that blends right into the pink scarf ribbon.
*   **Palette use:** Pink ribbon and skin tone on the upper back share almost identical luminance, destroying the silhouette of the ribbon.

---

### **5. N (North / Back)**
*   **Stray/errant pixels:** 1px skin-colored pixel inside the dark hair at the lower-left nape; scattered light-red pixels inside the dark-red inner skirt shadow.
*   **Outline issues:** Jagged double-pixels on the bottom-right skirt hem; unoutlined bright red edge on the top-left of the bow.
*   **Face:** N/A (Back view), though 1px skin pixels peek out at both left and right sides of the neck/jawline asymmetrically.
*   **Hair/bangs:** Back of head is a massive flat dark-brown circle with zero volume shading or hair strand clustering; pink rim light on the right edge is broken into dashed segments.
*   **Bow:** Completely hidden behind the bun on the left, only peeking out on the top-right—in N view, both symmetric ears of the bow should be clearly visible behind/above the bun!
*   **Bun:** Giant round brown ball sitting slightly left of center, blocking the bow.
*   **Sword blade + hook guard + hilt:** Attached to the bottom-left skirt edge with no hand or hilt visible; guard hook is a 2px grey nub.
*   **Scarf ribbons:** Drawn as an inverted pink 'V' or wishbone shape plastered flat against the middle of the back, looking like suspenders or back-straps rather than flowing scarf ends.
*   **Legs/feet/heels:** Completely invisible or reduced to two 2px dark nubs that merge into the ragged skirt tips.
*   **Skirt hem:** Split into two awkward side-wings (bright red) and a dark-red central curtain with 1px jagged teeth at the bottom.
*   **Value grouping / readability:** Upper back is a confusing mess of skin, pink ribbons, and light-red collar edges all fighting in the same high-value bracket.
*   **Palette use:** The dark-red underside of the skirt forms a big flat central block that flattens the cylindrical volume of the dress.

---

### **6. NW (North-West)**
*   **Stray/errant pixels:** Isolated 1px dark pixels inside the pink ribbon on the right; 1px bright red pixel floating disconnected at the bottom-center skirt tip.
*   **Outline issues:** Heavy black double-thick corners on the bottom-right skirt hem; jagged stair-stepping along the back-right pink rim light of the hair.
*   **Face:** Jawline/cheek barely visible on screen-left, buried in a thick cluster of black outline pixels at the collar.
*   **Hair/bangs:** Back of the head is a huge flat brown expanse with zero mid-tone or highlight clusters; pink rim light on the right edge is applied as a continuous 1px inner border next to the black outline, creating a "banded" double-outline effect.
*   **Bow:** Reads as two tiny stubby red horns sticking out the top-right of the bun.
*   **Bun:** Sits below and left of the bow—again, inverted relative to how a bow tied at the base/top of a bun works in 3D space.
*   **Sword blade + hook guard + hilt:** Poking out from under the left sleeve; guard hook is a closed loop/blob; blade has severe 2px step jaggies.
*   **Scarf ribbons:** Hanging off the right shoulder; peppered with dark brown/black noise pixels inside the pink fill, making it look dirty and frayed.
*   **Legs/feet/heels:** Left foot is a flat horizontal slipper shape; right foot is swallowed by the skirt hem.
*   **Skirt hem:** Heavy, blocky, saw-toothed bottom edge in dark red; completely lacks the flowing, layered overlap of the front views.
*   **Value grouping / readability:** Almost the entire lower half of the sprite is a single flat dark-red shade (#802030 range) with zero fold definition.
*   **Palette use:** Overuse of the darkest red shade for 80% of the skirt, making NW and W look like they are standing in deep shadow compared to S/SE/SW.

---

### **7. W (West / Profile)**
*   **Stray/errant pixels:** 1px blue eye pixel isolated at the front edge of the face; random orange/light-red pixels scattered in the middle of the sleeve/corset area.
*   **Outline issues:** Thick black clumping under the chin/neck; jagged 1px steps along the back of the skirt; open outline on the left edge of the bow.
*   **Face:** Eye is a tiny horizontal slit pressed against the front outline; heavy red/pink pixels below the eye make her look like she has a bruised or bleeding cheek rather than cute chibi blush.
*   **Hair/bangs:** Giant ear/cheek gap cuts way too high into the hair volume; vast empty brown cranium with a tiny 3px highlight on the very top.
*   **Bow:** Pushed forward to the top-left of the bun (completely opposite to the E profile where it was also on the left—meaning the bow is not rotating with the head in 3D!).
*   **Bun:** Pushed to the back-right of the head.
*   **Sword blade + hook guard + hilt:** **ANATOMICAL/PERSPECTIVE ERROR:** In W profile, the left arm is the NEAR arm. We should clearly see the arm, hand, hilt, guard, and blade in the foreground. Instead, the arm is a tiny stump and the sword emerges from beneath the front skirt hem with no hilt!
*   **Scarf ribbons:** Single jagged pink strip sticking out the back-right with a stair-stepped black outline.
*   **Legs/feet/heels:** Only one foot visible at the bottom, drawn with noisy skin/black alternating pixels that look like bare toes rather than a strapped heel.
*   **Skirt hem:** Hangs lower in the back than the front, with a chunky blocky cutout around the front foot.
*   **Value grouping / readability:** The near arm (left arm) completely disappears into the red torso; impossible to tell where the sleeve ends and the body begins.
*   **Palette use:** Same issue as NW—back half of the skirt is a massive flat dark-red slab while the front is noisy orange/mid-red dither.

---

### **8. SW (South-West)**
*   **Stray/errant pixels:** 1px bright orange-red dot on the far-left sleeve tip; 1px dark pixels floating on the shins/ankles.
*   **Outline issues:** Missing outline on the far-left edge of the sleeve flare (warm red pixels touch the grey background directly); clumped black pixels between the thighs.
*   **Face:** Screen-left (far) eye is squashed against the outline; screen-right (near) eye is a large 3x2 blue patch with a heavy dark-red/brown bag underneath it.
*   **Hair/bangs:** Parting/notch in the bangs is off-center; pink rim light runs up the entire right contour of the hair and bun cleanly, but the main brown hair mass is completely flat.
*   **Bow:** Sits on the top-left of the bun—again, failing to rotate properly around the vertical axis of the head.
*   **Bun:** Sits lower and to the right of the bow.
*   **Sword blade + hook guard + hilt:** Sword is held on the screen-right (her left hand, which is correct for SW), emerging from behind the knee/skirt; guard hook is a big grey 'U' shape; zero hilt visible.
*   **Scarf ribbons:** Hanging on the screen-right behind the shoulder; merges slightly with the pink rim-light on the collar.
*   **Legs/feet/heels:** Both legs are visible, which is good, but the ankle straps are messy asymmetric diagonal lines and the knees have weird vertical dark lines running between them.
*   **Skirt hem:** Much cleaner silhouette than E/NE/NW, showing the front slit and side flares, though the screen-left sleeve tip blends into the skirt flare.
*   **Value grouping / readability:** The screen-left arm (her right arm) is a shapeless red/orange mitten blob with no hand or cuff definition.
*   **Palette use:** Good lighting contrast from top-left to bottom-right, but ruined by the unoutlined orange highlight on the left sleeve edge.

---

### **GLOBAL CLEANUP RULES FOR ARTISTS**

1.  **Strict Selective Outline Policy:**
    *   Exterior silhouette MUST have a continuous, 1px-thick outline. Do not leave raw highlight pixels (like the SW left sleeve or bow tops) open against the background unless it is the top-leftmost sun-struck apex, and even then, use the darkest shade of that local ramp (dark red/dark brown), never bright orange/red.
    *   Eliminate all 2x2 black `#1a1220` interior clumps (especially between the legs, under the chin, and at the skirt hem corners). Use dark local colors (dark red, dark brown) for interior linework.

2.  **Eliminate 1px Noise & Enforce Cluster Minimums:**
    *   **Zero single-pixel islands** of shading or detail on clothes. Every shadow, highlight, or fold cluster on the hair and dress must be at least **3–4 connected pixels**.
    *   Remove all brown/dark speckles from the skirt and all stray purple pixels from the waist. At 56px height, micro-ornaments like the tiny waist pouches or shoulder cords must either be simplified into clean 3px+ readable shapes or omitted entirely.

3.  **Standardized Eye & Face Template:**
    *   In **S**, eyes must be symmetrical: 2px wide by 2px tall (1px dark lash top, 1px blue iris + 1px white sclera bottom), separated by 3px of skin.
    *   In **SE/SW**, the near eye is 2x2, and the far eye is 1x2, separated from the exterior black outline by at least 1px of skin or hair so it doesn't bleed into the background.
    *   In **E/W**, the eye is 2px wide, recessed 1px back from the front nasal bridge line. Do NOT let blue iris pixels touch or breach the exterior profile outline.
    *   Remove all dark-red pixels directly beneath the eyes; use only the soft peach/pink blush shade on the outer cheek.

4.  **3D-Consistent Bun & Bunny-Ear Bow Geometry:**
    *   Establish a true 3D anchor: The **bun** is a 7x6 sphere centered on the upper-back crown. The **bow** ties at the *front/top base* of the bun with **two distinct ears** flaring upward and outward in a 'V' silhouette.
    *   In **S/N**, both bow ears must be visible on either side of the top of the bun.
    *   In **SE/SW/NW/NE**, one ear is foreshortened and the other flares out—do NOT draw the bow permanently glued to the screen-left of the bun in every single frame!

5.  **Bangs & Hair Volume:**
    *   Break the flat helmet look in S/SE/SW by carving a clean 2px vertical/diagonal skin notch (parting) slightly off-center over the left eye, matching Image 2.
    *   Add a curved 2px-tall crescent specular highlight across the upper crown in all 8 views (including N/NW/NE, which are currently dead flat brown circles).

6.  **Canonical Weapon Hand, Hilt, Guard & Blade Matrix:**
    *   **Handedness Lock:** She holds the katana in her **LEFT hand** in all 8 frames.
        *   In **E**, her left hand is on the *far* side of her body—the blade should angle down and back/left behind her, NOT out in front of her chest.
        *   In **W**, her left hand is the *near* foreground arm—we must clearly see her sleeve, hand, and the **3px red/black wrapped hilt** protruding above the hand.
    *   **Blade Line Discipline:** Use a strict **2:1 pixel step (2 vertical : 1 horizontal, or uniform 1:1 45-degree)** for the blade edge and highlight. Never mix 1px, 2px, and 3px steps along the same straight blade.
    *   **Guard (Tsuba):** Draw a crisp 3px straight cross-bar in light silver with a 2px crescent hook (*kagi*) curving toward the blade tip on the forward edge.

7.  **Scarf Ribbon vs. Skin Value Separation:**
    *   The pink scarf ribbons MUST be clearly separated from skin tone in **NE, N, and NW** where her upper back is exposed. Either border the ribbon with dark red/brown interior lines, or shift the back skin into the shaded skin tone so the bright pink ribbon pops in high contrast.
    *   Every ribbon must have a clean, tapered 2px-to-1px flowing curve—no blocky sausages or jagged dirty internal pixels.

8.  **Skirt Hem & Isometric Feet Grounding:**
    *   Clean up the shredded bottom skirt hems in **E, NE, N, NW, W**. Replace the 1px vertical teeth and flat dark-red slabs with 2–3 smooth, overlapping curved hem folds using mid-red on the outer pleats and dark-red only inside the inner recesses/underside.
    *   **Feet Alignment:** Both feet must sit on a proper 2:1 isometric ground diamond. Define each foot as a clean 3x4 wedge: dark heel/sole at the bottom, 2px skin instep, and a crisp 1px dark ankle strap. Eliminate all clubbed hooves and stray toe pixels.
