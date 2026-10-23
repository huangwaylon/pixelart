# r15 - SE far eye and longer bangs (face team + AD)

## 1. SE far eye
**Cause:** at 45 degrees the far-eye marker lands on the cheek contour, so the spacing rule shoved both eyes toward the near hair. The far eye ended up a 2x2 block 1 px from the outline.

**Mockups** (pixel edits on v1 frames, `options_x10.png`):
- A: near side 1 px wider, far eye 2x3
- B: A plus a far-eye catchlight
- C: 1x3 far eye
- D: A plus an outer lash
- E: 2x3 far eye, no widening

**AD:**
- C reads as a slit.
- E is still jammed against the contour.
- D makes the far eye heavier than the near eye.
- A keeps rule 1 (no far catchlight), made for 2x2 eyes, and still looks dead.
- **B wins:** the catchlight sits on the light side like the near eye's, so the gaze stays consistent. No lash wing keeps it "far".

**Implemented:**
- `kawaii_hd` 3/4 cels.
- `contour_far: 2` (far cheek of at least 2 px).
- `mouth_bias: 3` (mouth under the bridge).
- Side locks back 1.6 and a tilted hair-cap cut: near cheek +1 px, temple still covered.

## 2. Bangs
- Tips lowered: centre 9.5 to 8.6, L1-L3 to 7.9/7.6/7.2. The outer bangs are longest, giving the gentle slope, and the hime notch stays.
- New temple bangs reach y 7.2 and blend into the side locks.
- Tip radius goes from 0.05 to 0.3, so the extra length survives at sprite size.
- In S the hair ends 1 row above the lashes everywhere (the temples showed 2-3 rows before).

**Profile:**
- The E/W eye cel moves 1 row lower, onto the S/SE eye line (it sat high because of the 16-degree camera).
- New `lash_over_hair` rule: if a bang tip lands on the lash row while the head bobs, the lash wins.

**Checks:**
- Hair now hides 0 eye pixels in idle, walk, run, jump and fall.
- QA passes on all 18 builds.
- S4_halfup_bow is byte-identical.
