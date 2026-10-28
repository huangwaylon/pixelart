### 1. Scores & Verdicts vs. N
* **N (Native): 6/10** (Baseline; clean clusters, slightly blocky silhouettes)
* **VM: 5.5/10 — Worse than N** (Introduces stray shading pixels on coat; hair silhouettes slightly rougher)
* **KC: 6/10 — Same as N** (Marginally smoother ponytail silhouette in E/W, but identical interior flaws and added brown coat noise in S)
* **PF: 3.5/10 — Worse than N** (Severe cluster fragmentation, stray highlight streaks, broken outlines, heavy walk flicker)
* **KCE: 4.5/10 — Worse than N** (Interior normal/depth lines create dark purple/brown noise at this scale, muddying hair and scarf)

---

### 2. Concrete Pixel Problems by Row & Direction

**N (Native)**
* **N SE / SW:** Detached 2x2 teal/dark pixel island mid-coat (clipping hand/scarf tail).
* **N S / SW:** Flat, unshaded vertical beige coat slab on the lit side.
* **N Walk SE f1–f8:** Mid-coat teal/dark island teleports and changes shape across frames (2px in f1, 3px in f2, 1px in f4, gone in f6).

**VM (Vote Mode-Band)**
* **VM S / KCE S / KC S:** Stray single brown pixel mid-coat on the left side (absent in N S).
* **VM E:** Ponytail tip breaks into a 1px vertical spike with a gap between ponytail and head.
* **VM SE / SW:** Retains the detached mid-coat teal island, now with an extra dark outline pixel making it look like a hole in the coat.

**KC (K-Centroid)**
* **KC S:** Stray single brown pixel in the left beige coat slab.
* **KC Walk SE f5:** Horizontal 3px brown line artifact cuts across the middle of the beige coat (flickers in for 1 frame only).
* **KC Walk SE f1–f8:** Mid-coat teal island still flickers frame-to-frame (3px cluster in f1–f3, 2px in f4, disappears in f5–f6, returns in f7–f8).

**PF (Retro Diffusion Pixel-Fixer)**
* **PF SE / E / SW:** Bright 3–4px light-brown horizontal streak cuts across the bangs/fringe; breaks hair cluster hierarchy.
* **PF E:** Ponytail splits away from head with a 2px vertical background gap; jagged dark interior pixels in hair.
* **PF N:** Bow symmetry broken; dark pixels eat into the left bow loop.
* **PF NE / NW:** Coat shading breaks into noisy checkerboard/staircase banding.
* **PF Walk SE f1–f8:** Severe temporal instability/boiling in hair highlights (light brown streak jumps height and width every frame); f4/f5 bangs turn into a noisy horizontal stripe; f8 ponytail detaches at the bottom tip.

**KCE (KC + Edge Lines)**
* **KCE S / SE / SW:** Dark purple interior edge lines around the scarf and bangs read as stray orphan pixels/dirt rather than lineart at 34px height.
* **KCE E / W:** Dark crease pixels between ponytail and head muddy the hair mass.
* **KCE N / NE / NW:** Extra dark pixels under the bow loops clutter the back of the head.
* **KCE Walk SE f4–f6:** Dark line pixels under bangs and around the neck shift 1px up/down per frame, causing line-boil.
* **KCE Walk SE f5:** Same 3px horizontal brown coat artifact as KC f5, plus extra dark pixels around the forward arm.

---

### 3. Does 8x High-Res Downscaling Fix Known Issues?
* **Flat beige coat slab:** **No** (Still a flat vertical band in S, SE, E, W, SW across all methods; PF only adds noisy dither/jaggies).
* **Teal mitten/scarf islands mid-coat in SE/SW:** **No** (Present in every single row in Idle SE/SW and Walk SE; it is a 3D geometry/clipping issue, not a sampling issue).
* **Stub legs:** **No** (Identical proportions across all rows).
* **Blob hands:** **No** (Still 2–3px undifferentiated teal blobs in all rows).
* **Small bow in S:** **No** (Still just 2–3 pixels peeking at the top corners of the head in all rows).
* **Fringe ridges:** **No** (Still a flat horizontal step in S/SE/SW; PF makes it worse by adding bright horizontal banding).

---

### 4. Ship Recommendation
**Keep N.** 

None of the 8x downscale methods solve the underlying 3D model/shader readability issues (which require geometry/material fixes, not supersampling). **N** has the cleanest cluster integrity and lowest temporal noise in the walk cycle. **KC** is a lateral move that adds a single-frame coat glitch in Walk f5, while **VM**, **PF**, and **KCE** actively degrade pixel cleanliness.
