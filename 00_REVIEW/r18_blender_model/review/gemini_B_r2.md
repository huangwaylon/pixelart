### **(a) Side Profile vs. `ref6` & `ref4` (Assuming ~220 mm Head Height Scale)**
The profile does **not** yet match `ref6`’s crisp, doll-like anime silhouette. Currently, the lower face is too vertical, flat, and long (giving an adult/lantern-jawed proportion rather than the cute, recessed lower face of `ref6` and `ref4`):

*   **Forehead & Brow Slope:** The forehead is too flat and vertical. Push the upper forehead forward **+4 to +5 mm** with a fuller curve, and recess the glabella/nasion (root of the nose at eye level) inward **-3 mm** to create `ref6`'s distinct brow-to-nose dip.
*   **Nose Projection & Upturn:** The nose bridge is too straight and the tip is too blunt/low. Pull the nasal tip forward an additional **+5 to +6 mm** and raise/tilt the tip upward **+2.5 mm** to create a concave "ski-slope" bridge and a sharp, upturned button tip.
*   **Lips & Muzzle:** The philtrum/mouth area is completely flat. Push the upper lip peak forward **+2.5 mm**, add a **-1.5 mm** inward indentation at the mouth corner/stomion, and define a **+1.5 mm** lower lip roll with a **-2 mm** labiomental groove underneath.
*   **Chin & Jawline:** The distance from nose to chin is too long and the chin drops straight down. Raise the bottom of the chin **+6 mm** (shortening the lower third of the face) and push the chin/lower jaw backward **-5 to -6 mm** so it sits on a clean diagonal receding line behind the nose/upper lip plane (`ref6`). Currently, the jawline is also severely deformed During rigging (Image 6 shows the chin stretching into a sharp point when the head turns).

---

### **(b) Bald Head Shadow Patches**
This is a **combination of harsh stepped toon lighting and unedited vertex normals** (not broken geometry, though it follows the low-to-mid-poly topological contour around the temple, zygomatic arch, and ear base). 
*   In 3D anime toon shading, raw geometric normals on the cheek/temple always produce ugly polygonal terminator lines under a side/front-angled key light.
*   **Solution:** Transfer vertex normals for the face from a smooth squashed sphere/ellipsoid (or paint custom face normals) so the shadow terminator wraps cleanly, or clamp face shadows so only cast shadows (from bangs/nose) appear on the skin.

---

### **(c) Hair, Bow, Scarf, Coat & Boots Quality**
*   **Bangs:** In profile (Image 2), the bangs sit flush against the forehead like a thin helmet shell. In `ref6` and `ref4`, bangs puff outward with volume in front of the forehead and leave a visible shadow gap over the eye.
*   **Bow & Ponytail:** From the front/back (Images 3–5), the bow loops look inflated and balloon-like; from the side (Image 2), the bow looks crumpled and uneven. The ponytail tie/base sits too low and projects horizontally out the back of the head like a stiff pipe before dropping down.
*   **Back Hair:** The bottom tips of the loose back hair and ponytail (Image 5) end in flat, paper-thin, jagged saw-tooth cutouts that look low-poly and unnatural.
*   **Scarf & Coat:** In the rig test (Image 6), the hanging scarf tail warps with jagged zig-zag edges, and the coat sleeve/cuff shows brown skinning/clipping artifacts when the arm bends.
*   **Legs & Boots:** In side view (Image 4 vs `ref4`), the legs are dead-straight vertical cylinders. `ref4` has a natural anatomical S-curve (slight forward thigh, backward knee/calf curve). The boots are slightly boxy at the toe.

---

### **(d) Readability at 96px Sprite Size (Image 7)**
*   **Nose disappears:** Because the nose projection is too subtle and the face is too vertical, the nose reduces to a single faint pixel bump at 96px.
*   **Side-lock tangent:** The thin side hair strand cuts right across the middle of the eye and cheek, creating a muddy vertical line that looks like a scar or rendering glitch at sprite resolution.
*   **Eye placement:** The eye sits too far forward, leaving only a 1-pixel sliver of skin/outline between the cornea and the front of the face.
*   **Ponytail gap:** The horizontal gap between the head and ponytail reads awkwardly at small scale.

---

### **Verdict: FIXES**

1. **Resculpt Nose & Nasion:** Recess the nose bridge root **-3 mm** inward, curve the bridge concavely, and pull the nose tip **+5–6 mm** forward and **+2.5 mm** upward so it reads as a distinct 2–3 pixel upturned point at 96px.
2. **Recede & Shorten Lower Face/Chin:** Move the lower lip/chin plane back **-5–6 mm** and raise the chin bottom **+6 mm** to match `ref6`’s compact, angled anime jaw profile.
3. **Add Lip & Philtrum Contours:** Carve in a **-1.5 mm** mouth cleft and **-2 mm** under-lip crease, pushing the upper lip **+2.5 mm** forward to break up the flat vertical line below the nose.
4. **Add Forehead & Bangs Volume:** Round out the upper forehead (**+4–5 mm** forward) and puff the front bangs outward **+6–8 mm** past the forehead plane so they arch over the eyes with depth (`ref6`/`ref4`).
5. **Recess Eye in Side Profile:** Shift the eyeball/cornea **-2.5 mm** deeper into the socket so it doesn't sit flush against the front bridge line at 96px.
6. **Reposition Side Hair Locks:** Move the cheek-framing hair strands **8–10 mm** backward toward the ear so they frame the jaw/cheek without slicing through the eye and blush at sprite scale.
7. **Fix Face Normals & Jaw Rigging Weights:** Transfer smooth spherical normals to the face mesh to eliminate the jagged triangular cheek/temple shadow, and fix the head/neck bone weights so the chin doesn't stretch into a spike when posed (Image 6).
8. **Fix Ponytail Base & Bow Shape:** Raise the ponytail attachment point slightly, snug it against the skull (removing the stiff horizontal stalk), and reshape the teal bow into crisp, folded ribbon loops instead of puffy blobs.
9. **Refine Back Hair Tips:** Replace the jagged, flat saw-tooth bottom edges of the back hair and ponytail with tapered, overlapping hair clumps.
10. **Clean Up Scarf/Sleeve Skinning & Leg Curve:** Fix the zig-zag deformation on the scarf tail and brown texture bleeding on the bent left sleeve in Image 6, and add a subtle anatomical S-curve to the legs/boots in side view (`ref4`).
