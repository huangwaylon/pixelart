(eval):1: can't change option: zle
(eval):1: can't change option: zle
I'd adopt the **A+B hybrid**. Scores are on-model / parts & seams / rig-ability / 48 px usefulness, each out of 10. The iso SE column shows mostly hair in every row, while the design's iso_SE shows a clear three-quarter face. That's either a camera-yaw bug or the face is too shallow on every mesh, so check it first.

**2mv single: 6 / 3 / 1 / 5**
- Exploded view is a single lump, so there's nothing to pose and the pose columns are empty.
- The sash in the front view is a jagged, noisy dark band, and the bow edges are ragged.
- Sleeve tips and hands melt into red shards.

**A split: 6 / 5 / 6 / 5**
- In the arm-raise pose the sleeves tear at the shoulder cut, leaving red shards at the joint.
- It keeps the bad sash and bow from the baseline. The bow is a frayed flat slab and the bun is almost lost in the back view.
- In the stride pose the bare thigh shows a cut seam under the skirt.

**B per-part: 5 / 6 / 8 / 4**
- The hair has light streaks and holes through the bangs (front and iso views), which turn into noise at 48 px.
- The torso part is a tiny blue stump with no sash, so the waist doesn't match the design.
- The bow is undersized. The bun is the best of all rows.

**C PartCrafter: 3 / 2 / 1 / 3**
- The split follows materials, not joints: torso, arms and skirt are one piece, so the pose test is identical to the rest pose.
- The bow is a detached, wrong-shape flat cap, and the hair has ear-like points.
- The hands are wispy fragments.

**A+B hybrid: 7 / 6 / 8 / 6**
- It still has A's frayed bow and noisy sash, and those are the most readable shapes at 48 px.
- The shoulder seam between A's torso and B's arm shows in the arm-raise pose, with a pink/cyan gap.
- The iso SE face problem above applies here too.

**Fixes for the hybrid, in order:**
1. Fix the SE camera yaw, or push the face forward on the head.
2. Rebuild the bow and bun as clean low-poly shapes: two lobes, a knot and a sphere. Making them separate pieces lets the bow be animated.
3. Recolour the sash as a clean band, split by height rather than taken from the noisy vertex colours.
4. Hide the shoulder joint inside the sleeves and hide the hip joint under the skirt.
5. Re-render the 48 px column and compare it pixel by pixel against the design's iso_SE.

Saving session...completed.
