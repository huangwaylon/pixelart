# Gemini 4 Argon critique: A vs B

## Run 1: face close-ups (A final_face.png, B v10_face.png, ref4, ref5)

Here is the blunt, part-by-part art direction critique comparing **Candidate A** and **Candidate B** against your target references (**Images 3 & 4**).

---

### Part-by-Part Comparison

#### 1. Face Shape
* **Winner: B (by a wide margin, though still flawed)**
* **Why:** **A** has a bizarre, anatomical disaster of a lower face—the cheeks bulge outward and then pinch into a thick, tubular "thumb" neck with no jawline separation in the 3/4 and profile views. In profile, A’s face is completely flat like a pug, with a sagging double-chin/neck web. **B** actually has a recognizable anime oval-to-heart contour with a distinct jaw-to-neck separation. However, B’s cranium/upper head is shaped like a tall egg/bullet, whereas the reference (Image 4) has a wider, rounder, more balanced cranial dome.

#### 2. Chin
* **Winner: B**
* **Why:** **A’s** chin melts directly into the neck cylinder; the shading under the chin looks like a goatee or a throat pouch because there is no crisp jawline normal crease. **B** has a clean, small, pointed anime chin with a sharp inked jawline that separates the head from the neck in both front and 3/4 views.

#### 3. Eyes
* **Winner: Neither (A has better size/placement; B has slightly sharper lash shapes, but both fail the reference badly)**
* **Why:** **B’s** eyes are way too huge, wide, and triangular—they look like western cartoon/bug eyes and crowd the temples, with upper lashes clipping into the bangs. **A’s** eye scale and spacing are closer to a 19–20yo anime heroine, and A actually has visible eyebrows (B’s eyebrows are completely buried under the bangs). However, both A and B have thick, clumsy black outlines around the bottom/inner sclera and muddy iris gradients. Look at Image 4: anime eyes have **no thick black outline on the inner/lower tear duct**, a heavier dark upper lash line, flat/crisp iris cel-steps, and clear space between the upper lash and the bangs.

#### 4. Hair Bangs
* **Winner: B (marginally, for sharpness)**
* **Why:** **A’s** bangs look like inflatable brown balloons or scalloped clouds—thick, rounded, blobby sausage tips with zero anime sharpness. **B** attempts sharp, V-notched flat sheets like the brief asks for, which is much closer to the sheet-like hair in Image 4. However, B’s bangs sit flatly plastered to a tall egg-head and have a bizarre horizontal "crown/braid" seam of lighter brown blobs across the upper forehead that makes no sense. Neither model lifts the bangs off the forehead to show the eyebrows properly like Image 4.

#### 5. Side Locks
* **Winner: B**
* **Why:** **A’s** side locks are stiff, uniform-width fettuccine noodles with blunt/rounded ends. **B’s** side locks have better anime tapering, thinner strand breakups, and frame the jaw more naturally.

#### 6. Back Hair
* **Winner: A (from what is visible)**
* **Why:** In **A**, the back hair flows down past the shoulders with some layered silhouette breakup. In **B’s** front view, the back hair is completely hidden behind the side locks and ponytail bulk, giving her a narrow, pin-headed silhouette from the front compared to the wide, lush back-hair framing seen in Image 4.

#### 7. Ponytail
* **Winner: A**
* **Why:** **A** shows a distinct high tie-point in profile with separate layered locks arching out and tapering to sharp points. **B’s** ponytail (visible in 3/4) is a heavy, unarticulated brown mass with no lift or bounce at the root.

#### 8. Bow
* **Winner: A (from the front), Neither (in 3/4 & profile)**
* **Why:** From the front, **A’s** bow ears sit higher and read as a classic puffy bow silhouette, whereas **B’s** bow droops downward like heavy teal handlebars or airplane wings with a thick, rolled inner lip that looks like a tire tube. However, in profile, **A’s** bow looks like a vertical green kidney bean with a paper-thin dangling string for a tail. Neither has the crisp pinched center knot, satin fold creases, or wide V-cut ribbon tails specified in the brief.

#### 9. Body Proportions / Silhouette *(Head/Neck/Shoulder area visible in renders)*
* **Winner: B**
* **Why:** Looking at the head-to-neck-to-shoulder relation visible here: **A’s** neck is way too thick at the top (blending into the jaw) and tapers *inward* toward the collar like an inverted cone. **B** has a slender, cylindrical anime neck that sits cleanly inside the scarf collar. (To match Images 3 & 4 for the full body, ensure the head width is ~1/5.2 of total height with narrow, sloping shoulders and long legs).

#### 10. Outfit *(Scarf visible in renders)*
* **Winner: A**
* **Why:** **B’s** scarf is a rigid, symmetrical, glossy teal toilet-seat/donut ring floating around the neck with a harsh cyan specular blob. **A’s** scarf actually has overlapping folds and a front knot/drape indication, though both completely lack the **cable-knit texture/normal detail** requested in the brief.

#### 11. Toon Shading & Outlines
* **Winner: B (on face), Reference is miles ahead of both**
* **Why:** **A** has hideous grey/muddy vertex-like shading around the mouth and chin, making the lower face look dirty and 3D-blobby, plus clumpy, uneven ink lines. **B** has a much flatter, cleaner front face tone, *but* B’s 3/4 view has a harsh diagonal shadow cutting across the cheek and eye socket. Look at **Images 3 & 4**: the reference uses **flattened face normals** (almost 100% lit skin tone with only a tiny nose dot and under-chin shadow), ultra-thin, delicate brown/dark-tinted outlines (not thick black magic-marker lines), and subtle, low-contrast hair cel-shading.

---

### Verdict: Base Model & Kitbash Plan

* **Use Candidate B as the Base** for the **Face, Jawline, Chin, Neck, and Side Locks**. A’s lower face/jaw topology is fundamentally broken and unsalvageable without a full resculpt.
* **Take from Candidate A:**
  1. The **ponytail root arch and layered strand separation**.
  2. The **higher bow angle/placement** (from the front view).
  3. The **overlapping scarf fold geometry** (re-centered around B's neck).
  4. The **visible eyebrows** and slightly smaller, less bug-eyed **eye proportions**.

---

### Top 8 Concrete Fixes to Reach Reference Quality (Images 3 & 4)

1. **Fix the Face Normals (Kill the 3D Cheek Shadows):**
   Transfer normals from a flattened sphere onto the face mesh (or use a custom face shadow map) so the face stays 95% flat base skin color in 3/4 lighting, just like Images 3 & 4. Eliminate B’s harsh diagonal cheek shadow and A’s muddy mouth/chin shading.
2. **Fix the Cranium & Lift the Bangs Off the Forehead:**
   Widen B’s upper skull slightly and lower the crown so it isn’t shaped like an egg. Pull the front bangs forward off the forehead plane (creating a 1–2cm shadow gap in profile like Image 3), raise the bang tips above the eyes, and make the **eyebrows clearly visible** through/under the notches. Delete that weird horizontal ring of light-brown blobs across B’s forehead.
3. **Redesign the Eyes to Match Image 4:**
   Shrink B’s eye height by ~20% so they aren't bug-eyed. Remove the thick black outline around the bottom and inner corners of the sclera. Make the upper lash line thick, dark, and winged, add subtle lower lash ticks, and flatten the iris shading into crisp, high-contrast anime cel shapes with clean white specular highlights.
4. **Fix the Profile Nose, Mouth, and Chin Projection:**
   Look at Image 3’s profile: the nose is a crisp, tiny upturned triangle, the upper lip steps back cleanly, and the chin has a tight horizontal shelf before meeting the neck. Ensure B’s profile matches Image 3’s crisp silhouette—never let the jaw web into the neck like A.
5. **Thin the Outlines by 60% and Color-Tint Them:**
   Both A and B use thick, heavy, comic-book inverted-hull outlines that scream "cheap 3D toon shader." Reduce outline thickness drastically to match the razor-thin lines in Images 3 & 4, and tint the outlines dark warm brown on skin/hair and dark teal on the bow/scarf instead of pure black.
6. **Rebuild the Bow with Real Ribbon Geometry:**
   Stop modeling the bow as inflated sausages/tires. Model a central **pinched knot**, two wide puffy satin loops with inner crease folds that sit high and proud behind the head (~1.5x head width), and two wide, flat ribbon tails with **sharp inverted V-cut notches** at the ends.
7. **Tone Down the Hair Specular & Sharpen Hair Tips:**
   Compare Image 4’s hair to A and B: Image 4 uses almost **one flat base color** with a very subtle, tight shadow step and crisp, paper-thin strand tips. Remove the giant cartoonish light-brown paint blobs on the hair, unify the base chestnut tone, and pull every bang and side-lock tip to a sharp point.
8. **Resculpt the Scarf from a Smooth Torus into a Soft Cable-Knit Wrap:**
   Replace B’s glossy teal inner-tube scarf with a matte, soft-edged wrap that hugs the neck closely, remove the shiny plastic specular highlight, and add clean toon line-art or normal-mapped **cable-knit ribbing** so it reads as winter knitwear rather than painted metal.

## Run 2: turnarounds (A final_turnaround.png, B v10_turnaround.png, ref4, ref5)

Here is a blunt, part-by-part breakdown comparing **Candidate A (Image 1)** and **Candidate B (Image 2)** against the brief and the target reference (Images 3–4). 

Right now, neither model hits the reference quality—both suffer from "western low-poly toy/Playmobil" syndrome rather than modern anime 3D (Arc System Works / Hoyoverse / *Lycoris Recoil* style)—but **Candidate B is significantly closer in facial structure and hair mechanics**, while **Candidate A has slightly better lower-hair volume and coat proportions**.

---

### 1. Part-by-Part Comparison

*   **Face Shape**
    *   **Winner: B.** 
    *   **Why:** Model A has a long, tubular "horse face" with bloated lower cheeks and zero anime plane breaks. In the 3/4 and side views, A’s face is completely flat like a cylinder. Model B actually has an anime V-taper from the cheekbones down to the jaw and a more recognizable nose/mouth placement in 3/4 and profile views. However, both completely lack the delicate forward-projecting anime nose/mouth muzzle seen in Reference 3 (profile view).
*   **Chin**
    *   **Winner: B.**
    *   **Why:** A’s chin is rounded, wide, and droopy, making her look doughy. B has a distinct, sharper pointed chin that creates the requested oval-to-heart silhouette in the front view.
*   **Eyes**
    *   **Winner: B (by a wide margin, though still flawed).**
    *   **Why:** A’s eyes are round, wide-eyed "bug eyes" with thin, uniform upper lashes and too much white sclera showing—she looks startled. B has a heavier, angled upper lash line with winged outer corners and larger irises that touch the upper/lower lids properly. However, both models have terrible eye socket depth in 3/4 and profile views (the eyes bulge out on a flat/convex surface instead of sitting recessed under the brow bone like Ref 3).
*   **Hair Bangs**
    *   **Winner: B.**
    *   **Why:** A’s bangs look like a solid, puffy croissant or sausage roll glued to her forehead; the bottom edge is scalloped with round bumps instead of sharp anime notches. B actually splits the bangs into sharp, tapered triangular tips with notched gaps showing the forehead and eyebrows underneath. Still, B’s bangs sit too flat against the skull in profile compared to Ref 3’s airy, projecting fringe.
*   **Side Locks**
    *   **Winner: B.**
    *   **Why:** B’s side locks frame the jawline tightly and have secondary thin outer strands (seen in 3/4 view) that add delicacy. A’s side locks bow outward stiffly like thick clay slabs and flare out awkwardly over the shoulders.
*   **Back Hair**
    *   **Winner: A (Front/Back silhouette) / B (Side separation).**
    *   **Why:** From the front and back views, A’s back hair has the wide, flowing bell-shaped flare and volume expected of long hair, whereas B’s back hair is far too narrow and clumped strictly between the shoulder blades (invisible from the front). However, in the side view, A’s back hair looks like a solid wall of clay, while B shows actual separation between the back hair and the torso. Both have awful "zig-zag sawblade" bottom tips from the back view.
*   **Ponytail**
    *   **Winner: B.**
    *   **Why:** B’s ponytail lifts up out of the tie before arcing down, giving it buoyancy and volume. A’s ponytail droops immediately and looks like a cluster of brown bananas.
*   **Bow**
    *   **Winner: A (Shape/Position) / Neither (Scale).**
    *   **Why:** Both failed the scale brief (~1.5x head width)—both bows are way too small (~1.05x head width). Between the two, A’s bow sits higher and perks outward with distinct loops and a clean center knot, reading better from the front. B’s bow droops downward like sad dog ears and looks lumpy in the side view. Neither has visible V-cut ribbon tails from the front silhouette.
*   **Body Proportions & Silhouette**
    *   **Winner: B (Pose & Cuffs) / A (Waist height).**
    *   **Why:** Both are ~5.2 heads tall, which fits the brief, but both look stiff and blocky compared to Ref 4. A’s 45-degree T-pose makes her look like an action figure; B’s lowered A-pose is much more natural. However, B’s legs look like straight cylinders with zero knee/calf taper, and her ankles are thick pipes. Look at Ref 3 & 4: the thighs taper into the knees, calves curve subtly outward, and ankles taper sharply into the shoes.
*   **Outfit (Coat, Scarf, Mittens, Boots)**
    *   **Winner: Tie (A has better scarf/waist; B has better cuffs/collar).**
    *   **Why:** 
        *   *Coat:* A’s belt sits higher at the natural anime empire/high waist, giving a longer skirt flare. B’s belt sits slightly too low, making her torso look boxy. However, B’s thicker brown sleeve cuffs look much better proportioned than A’s thin bands. Both coats lack the pleated/layered linework and collar structure seen in Ref 4.
        *   *Scarf:* A’s scarf has cleaner, thicker loops around the neck and neat fringe tassels. B’s scarf looks squished under the chin and has messy jagged ends. Neither has actual cable-knit texture/normal details.
        *   *Boots:* Both look like rubber rainboots. They completely lack ankle indentation, sole thickness separation, and fluffy fur silhouette.
*   **Toon Shading & Linework**
    *   **Winner: B (slightly), though both miss Reference 3/4.**
    *   **Why:** Look at Ref 3 & 4: the shading is **ultra-flat two-tone cel shading** with crisp, razor-sharp shadow terminators, zero muddy gradients on the face, subtle hair highlight bands, and clean thin internal ink lines. Both A and B have over-modeled tubular hair strands catching messy, vertical pillar-like toon shadows (especially ugly on the back of the hair) and heavy, clunky outlines.

---

### 2. Verdict: Base Model & Kitbash Plan

*   **Use Candidate B as the Base Model.** B’s head, eyes, jawline, bangs, side-locks, ponytail arc, sleeve cuffs, and arm pose are substantially closer to an anime aesthetic. Starting from A would require completely rebuilding the head and hair from scratch.
*   **Steal from Candidate A:**
    1.  **A’s Scarf Mesh:** Better volume around the neck and cleaner tassel geometry.
    2.  **A’s Bow Loop Angle:** Perk the bow loops upward like A instead of drooping downward like B.
    3.  **A’s Lower Back-Hair Width:** Widen B’s lower back hair so it flares out past the shoulders and is visible in the front silhouette.
    4.  **A’s Higher Belt/Waistline Placement:** Raise the belt slightly to elongate the lower A-line skirt flare.

---

### 3. Top 8 Concrete Fixes to Reach Reference Quality (Images 3 & 4)

1.  **Fix the Side-Profile Face & Recessed Eye Sockets (Crucial):**
    Compare B’s side view to Ref 3. B’s face is a flat vertical wall with eyeballs bulging out in front of the forehead/bridge. Pull the brow bone and nose bridge forward, recess the eyeballs inward, tilt the upper/lower eyelids in 3D space, and sculpt a small, sharp anime nose and recessed upper lip/chin curve matching Ref 3.
2.  **Flatten Hair Normals & Eliminate "Banana/Sawblade" Clumps:**
    Ref 3 & 4 have smooth, unified hair sheets where individual strands are only broken up at the very tips. Both A and B have deep vertical trenches running all the way up the crown and back hair, casting ugly vertical shadow stripes. Merge the main hair mass into a smooth dome/sheet, copy-transfer spherical vertex normals from a smooth proxy sphere so shading is clean, and cut sharp, asymmetric V-notches only at the bottom 15% of the hair tips.
3.  **Puff Out the Bangs in Profile View:**
    In Ref 3, the bangs lift off the forehead in a curved arc, creating a shadow gap over the eyes. Pull B’s bangs forward in the Z-axis so they arch off the forehead rather than sitting plastered flat against the face.
4.  **Scale the Bow up to 1.5x Head Width & Add V-Cut Tails:**
    Scale B’s teal bow up by **40–50%** horizontally and puff it out on the Z-axis. Angle the loops slightly upward, pinch the center knot tightly, and extend two wide satin ribbon tails with sharp inverted V-cut notches down past the shoulders so they clearly read in the front silhouette.
5.  **Redesign the Eyes & Brow Expressions (Ref 4 Style):**
    Make the upper eyelash mesh thicker and darker (deep charcoal/black, not thin brown), flatten the top curve of the upper lid slightly (Ref 4 has a cool, composed arch rather than a round circle), add small sharp side-lashes, add a distinct large white specular highlight + secondary lower-iris bounce glow, and make the eyebrows clearly visible *through/under* the bangs notches.
6.  **Sculpt Anime Leg & Boot Anatomy (Kill the "Pipe Legs"):**
    Look at Ref 4’s legs: there is a subtle inward curve at the knee, an outward curve at the upper calf, and a slim ankle. Taper the plum tights at the knee and ankle. Reshape the boots so they hug the ankle tightly, flare out slightly at the calf, have a distinct thicker sole/heel block, and feature a larger, softer fur cuff.
7.  **Add Tailored Coat Details & Pleat Linework:**
    Right now the coat is a smooth, featureless cone with floating gold spheres for buttons. Add a proper lapel/collar seam under the scarf, subtle A-line pleat creases or seam lines running down from the belt (like Ref 4’s skirt/coat panels), flatten the buttons into proper sewn discs, and cinch the waist inward at the belt by 15% to emphasize the hourglass-to-A-line flare.
8.  **Overhaul the Toon Shader & Outlines:**
    *   **Face:** Use custom flipped/flattened face normals so the face is 95% lit in front/3-4 views with only a clean neck cast shadow and subtle nose tick—no muddy cheek shading.
    *   **Outlines:** Reduce outline thickness by 40% on internal details (hair strands, scarf folds, fingers) while keeping a clean outer silhouette line. Color the outlines dark warm brown/burgundy instead of mud-grey.
    *   **Palette:** Shift the hair from flat terracotta orange-brown to a richer, deeper chestnut with a subtle soft horizontal highlight band across the bangs and crown.
