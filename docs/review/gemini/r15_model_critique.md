# r15 model critique (Gemini 4 Argon, round 1)

_Images:_ 00_REVIEW/r12_hd_model/S4_hd_turnaround_3d.png, 00_REVIEW/r12_hd_model/r13/r13_head_bow_closeup.png, 00_REVIEW/r13_anime_pixel/turnaround/turnaround_x3.png

## Prompt

You are a senior 3D character modeller (anime / Pokemon-DS style low-poly) advising an engineer. Our hero's 3D reference model is built from SDF primitives (ellipsoids, tapered capsules "seg", rounded boxes, tori, smooth unions) and rendered orthographically from an iso camera (elevation ~17 deg, 8 yaw directions) down to 48x64 game sprites (game proportion 3.4 heads tall).

Images:
1. S4_hd_turnaround_3d.png - our current SDF model, 8 directions (S, SE, E, NE, N, NW, W, SW), lambert shaded.
2. r13_head_bow_closeup.png - head/bow close-ups of our SDF model (top: before, bottom: current).
3. turnaround_x3.png - the APPROVED hand-drawn target turnaround (front, 3/4, side, back). This is the target look.

Design bible (key parts):
- Koyuki, 19-20, cute not childlike. Illustration height 5.4 H (H = crown to chin); game sprite 3.4 H with same head shapes, legs 1.1 H.
- Shoulders 0.9 H (sloped, narrower than hair), waist 0.75 H (belt at 2.05 H), hips 1.0 H, coat hem 1.6 H wide. Legs 2.4 H, knee at midpoint, one calf bulge, slim ankles. 1 px bust step, waist pinch, hem flare.
- Face: soft oval, full cheek, jaw tapers to a small chin. Rounded-top tare-me (droopy) eyes, 5x6 px, one eye-width apart, set low in face. Thick upper lash line.
- Hair: hime bangs - blunt cut just above brows, 2 notches = 3 panels, centre widest. Side locks 4 px wide temple to collarbone, blunt cut. Ponytail gathered at back of crown (brow height in side view) under the bow knot, swells to 0.5 H, tapers in slight S to a sharp point at the waist. Back hair long and straight, blunt slight-V cut at the hip.
- Bow (BIG): about 2x head width, wings past the head in front view; loops pinched at the knot, one crease each; swallowtail tails to the shoulder blades.
- Coat: mid-thigh A-line oat coat, fitted to the waist, 6 centre buttons, 3 px belt, rust hem and cuff trim. Chunky double-wrap teal scarf 0.3 H thick, ONE tail on her left, to the belt, fringe.
- Rounded teal mittens, dark tights, mid-calf rust-brown boots with cream cuffs.

Task: give a RANKED critique (most impactful first, ~10 items) of our 3D BASE MODEL vs the target and bible: overall proportions, anime head and face shape (cranium vs face volume, cheek/jaw, where the eyes sit), hair and bang volumes (bang shape - note ours is a sawtooth of 7 points but target is 3 blunt panels; side locks; back curtain; ponytail), the bow, the coat, scarf, limbs, boots. For each item give CONCRETE geometry changes in head units or as ratios (e.g. "cranium ellipsoid radii x:y:z = 1:0.95:1.05 H/2, face sphere offset forward 0.1H", "bang = one shell offset 0.04H from the skull cut by a plane at y=..., with 2 V-notches"), and say which primitive type to use. Also note what is already good and must be kept. Be blunt and specific.

## Response

Here is a blunt, ranked critique of the current SDF model (`S4` / `round 3`) against the target turnaround and bible, with exact SDF primitive recipes in **Head units ($1\text{ H} = \text{crown to chin}$)**.

---

### What is Already Working (KEEP THESE)
1. **3.4 H Game-Sprite Proportions & A-Line Coat Silhouette:** The overall head-to-body ratio, high waist pinch, flared skirt, and readable mittens translate well at 48×64.
2. **Scarf Asymmetry & Drape:** The single left-side hanging tail with slight S-curve and collar bulk reads clearly in all 8 directions.
3. **Ponytail S-Curve:** The side-view silhouette of the ponytail swelling out and tapering to a point is strong—just needs cleanup at the root and higher placement.

---

### Ranked Critique & SDF Geometry Fixes

#### 1. Face & Chin ("Bird-Beak" Pointed Chin vs. Soft Anime Oval)
* **Problem:** In `round 3`, adding the chin created a sharp, protruding cone at the bottom of the head (looks like a beak/funnel in S/SE/SW views) and a lumpy cheek ridge in E/W views. The old `r12` sphere was actually closer in silhouette.
* **Fix:** Anime heads are a **cranium sphere + flat/wide cheek-jaw wedge** with a high smooth-union ($k$), NOT a pointy cone chin.
  * **Cranium:** `ellipsoid` at $(0, 0.08\text{H}, 0)$, radii $(0.48\text{H}, 0.44\text{H}, 0.48\text{H})$.
  * **Lower Face / Jaw:** `seg` (tapered capsule) or `roundBox` from $(0, 0.0\text{H}, 0.08\text{H})$ to $(0, -0.40\text{H}, 0.14\text{H})$, top radius $0.42\text{H}$ (wide cheeks), bottom radius $0.16\text{H}$ (soft rounded chin—never $<0.14\text{H}$), `smin` with cranium at $k = 0.12\text{H}$.
  * Flatten the front face plane slightly by intersecting/blending with a vertical plane at $z = +0.44\text{H}$ so the face isn't bulbous in profile.

#### 2. Bow Size, Shape & Placement ("Mickey Mouse Ears" vs. Wide Horizontal Ribbon)
* **Problem:** `round 3` changed the bow loops into round, upright Mickey Mouse ears sitting on top of the head, and they barely peek out in front view. In the target (`turnaround_x3`), the bow is **2.0 H wide**, horizontal/trapezoidal, and **sticks out past the temples by ~0.35 H on each side** in front view. Also, the long teal ribbon tails down the back are completely missing.
* **Fix:** Revert to the `r12 (before)` angular wedge concept, widen it, and lower it to brow height:
  * **Knot:** `roundBox` at $(0, 0.15\text{H}, -0.48\text{H})$, size $(0.12\text{H}, 0.14\text{H}, 0.10\text{H})$.
  * **Loops (×2):** Tapered `roundBox` or flattened `seg` from the knot outward to $x = \pm 0.90\text{H}$, $y = 0.18\text{H}$, $z = -0.35\text{H}$ (angled slightly forward around the head curvature so they aren't occluded in S view). Inner height $0.12\text{H}$, outer flare height $0.32\text{H}$, thickness $0.08\text{H}$. Subtract 1 horizontal crease cylinder per loop.
  * **Bow Tails (×2):** Flat `seg` strips starting at knot, hanging down to $y = -1.1\text{H}$ (shoulder blades), $x = \pm 0.22\text{H}$, width $0.12\text{H}$, lying on top of the back hair curtain.

#### 3. Hime Bangs (7-Tooth Sawblade + Sausage Tubes vs. 3 Smooth Blunt Panels)
* **Problem:** The bangs are built from ~8 vertical capsule "sausages" ending in a 7-point zig-zag sawtooth, with a deep vertical trench down the middle of the forehead. The target has a smooth helmet shell with a **flat horizontal cut** broken only by **2 small V-notches** into **3 blunt panels** (centre widest).
* **Fix:** Delete all individual strand capsules on the cranium.
  * **Hair Dome Shell:** Offset cranium `ellipsoid` by $+0.06\text{H}$ thickness.
  * **Blunt Cut:** Slice the front shell with a horizontal plane at $y = +0.10\text{H}$ (just above brows).
  * **2 Notches = 3 Panels:** Subtract two small triangular prisms (`roundBox` rotated $45^\circ$) at $x = \pm 0.18\text{H}, y = +0.10\text{H}$, width $0.06\text{H}$, depth $0.08\text{H}$. This leaves a $0.36\text{H}$ wide blunt center panel and two $0.20\text{H}$ outer panels.

#### 4. Missing Back Hair Curtain (Crucial Silhouette Gap)
* **Problem:** Your model is a full ponytail with a bare neck/back of skull (`N`/`NE`/`NW` views show lumpy horizontal hair rolls on the nape). The target is a **half-up style**: a full, straight curtain of back hair falls all the way to the **mid-back/hips**, with the ponytail sitting *on top* of it.
* **Fix:**
  * Add a wide vertical `roundBox` / extruded curtain behind the head/torso from $(0, 0.1\text{H}, -0.35\text{H})$ down to $(0, -1.35\text{H}, -0.38\text{H})$ (waist/hip level in 3.4H scale).
  * Width: $0.96\text{H}$ (wider than the $0.90\text{H}$ shoulders), thickness $0.18\text{H}$, bottom edge cut into a slight blunt V. This completely covers the lumpy nape and frames the torso in front/back views.

#### 5. Eyes & Lash/Brow Readability ("Hollow Button Eyes" vs. Tare-Me Anime Eyes)
* **Problem:** The eyes are small dark vertical ovals floating in the middle of a blank face with no upper lash line or eyebrows, giving a creepy "button-eye doll" look.
* **Fix:**
  * **Placement & Scale:** Center at $y = -0.10\text{H}$ (below head midline), $x = \pm 0.19\text{H}$ (1 eye-width apart). Widen to $(0.16\text{H} \text{ wide} \times 0.18\text{H} \text{ tall})$.
  * **Tare-Me Shape:** Add a thick dark-brown upper lash bar (`seg` curved slightly downward at the outer corners, thickness $0.04\text{H}$) across the top of each eye, plus a small two-tone iris/highlight colour split so it doesn't render as a dead black hole.
  * **Brows:** Thin `seg` arcs just under the bang line ($y = +0.07\text{H}$).

#### 6. Side Locks (Too Short, Lumpy & Curved Inward)
* **Problem:** The side locks stop at the jawline ($y \approx -0.45\text{H}$) and curve inward like pincers. In the target, they are **straight vertical pillars** dropping past the scarf to the **collarbone/chest ($y = -0.80\text{H}$)** with a crisp flat bottom.
* **Fix:**
  * Use a single flat-faced `roundBox` per side (not multiple tubes) from $( \pm 0.44\text{H}, 0.15\text{H}, 0.05\text{H} )$ straight down to $( \pm 0.44\text{H}, -0.80\text{H}, 0.12\text{H} )$, width $0.14\text{H}$, depth $0.14\text{H}$, minimal rounding ($r = 0.02\text{H}$) so the bottom cut reads as a blunt hime lock.

#### 7. Ponytail Root & Lumpy Nape Balls
* **Problem:** In `r13_head_bow_closeup` (`NE`/`N`), there is a cluster of 4–5 bulbous spheres under the bow that looks like brain/intestine lumps, and the ponytail droops too low before swelling.
* **Fix:**
  * Delete the cluster of spheres at the nape.
  * Start the ponytail `seg` chain directly out of the bow knot at $(0, 0.15\text{H}, -0.50\text{H})$, arch it slightly *up and out* to $(0, 0.10\text{H}, -0.68\text{H})$ with radius $0.24\text{H}$ (the $0.5\text{H}$ diameter swell), then taper cleanly to a $0.03\text{H}$ point at $y = -1.25\text{H}$.

#### 8. Scarf Collar Width & Flatness
* **Problem:** The scarf neck-wrap is a narrow, drooping tube pinched into the neck, leaving the shoulders bare. In the target, the double-wrap forms a wide, horizontal, boxy cylinder that sits flush under the chin and spans nearly the full shoulder width.
* **Fix:**
  * Replace the neck torus with two stacked flattened `roundBox` or horizontal `torus` rings centered at $(0, -0.52\text{H}, 0.02\text{H})$, width $0.76\text{H}$, depth $0.62\text{H}$, total height $0.26\text{H}$.

#### 9. Coat Hem Trim, Pocket Flaps & 6 Center Buttons
* **Problem:**
  * The rust hem trim looks like a puffy inflatable inner-tube (`torus`) wrapped around the skirt bottom, and there are two dark horizontal dashes on the skirt front (pocket flaps?) that aren't in the target and clutter the 48×64 sprite.
  * Buttons only appear above the belt (2 dots); target has a continuous vertical line of **6 gold buttons** (3 above belt, 3 below belt) and a central vertical seam.
* **Fix:**
  * Delete the two front skirt dashes.
  * Make the rust hem trim the bottom $0.06\text{H}$ slice of the coat cone itself (same radius, or $+0.01\text{H}$ max), not a bulbous torus.
  * Place 6 small spheres ($r = 0.025\text{H}$) along $x = 0$ from $y = -0.70\text{H}$ to $y = -1.45\text{H}$.

#### 10. Leg Length & Boot Cuff Definition
* **Problem:** Even for the 3.4 H game proportion (where legs = $1.1\text{ H}$), the exposed legs + boots in `S4` are only $\sim 0.65\text{ H}$ tall and stumpy, with the cream fur cuff barely visible under the coat hem.
* **Fix:**
  * Shorten the coat hem slightly (end at $y = -1.55\text{H}$ instead of $-1.70\text{H}$) OR extend the lower leg/boot assembly down by $+0.25\text{H}$ so total exposed leg from hem to sole is **$0.95\text{H}–1.05\text{H}$** ($0.45\text{H}$ dark tights + $0.10\text{H}$ cream cuff torus + $0.45\text{H}$ rust boot).
  * Separate the legs slightly ($x = \pm 0.14\text{H}$) with a slight inward knee taper so a 1–2 px gap reads between the thighs/calves.
