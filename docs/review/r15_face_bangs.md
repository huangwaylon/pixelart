# r15 - SE far eye and longer bangs

## 1. SE far eye
**Cause:** at 45 degrees the far-eye marker lands on the cheek contour, so both eyes got shoved toward the near hair.

**Mockups** (`options_x10.png`): A wider near side + 2x3 far eye; B = A + catchlight; C 1x3; D = A + outer lash; E 2x3, no widening.

**AD:** C reads as a slit, E is still jammed, D is heavier than the near eye, and A still looks dead.
- **B wins:** the catchlight sits on the light side like the near eye's, so the gaze stays consistent. No lash wing keeps it "far".

**Implemented:**
- `kawaii_hd` 3/4 cels.
- `contour_far: 2` (far cheek of at least 2 px).
- `mouth_bias: 3` (mouth under the bridge).
- Side locks back 1.6 and a tilted hair-cap cut: near cheek +1 px, temple still covered.

## 2. Bangs
- Tips lowered (centre 9.5 to 8.6, L1-L3 to 7.9/7.6/7.2); the outer bangs are longest and the hime notch stays.
- New temple bangs reach y 7.2 and blend into the side locks.
- Fuller tips (radius 0.05 to 0.3).

**Profile:**
- The E/W eye cel moves 1 row lower, onto the S/SE eye line.
- New `lash_over_hair` rule: if a bang tip lands on the lash row while the head bobs, the lash wins.

## Round 2 (AD 1-5, anim)
New `face_eyes.hem_pin` rule: the hem is drawn from the lash line, with exactly 1 skin row in S/SE/SW.
- No bob strobe: the run S gap is a steady 1 (it flipped 1/0 in round 1).
- Slope: the outer S columns reach the lash row; in 3/4 the far-temple columns reach the row above it.
- Lone face-hair pixels cut (SE/SW: 34 to 0); closed arches keep 1 px of skin above.
- E/W skin pockets filled.
- Round 3: closed and squint eyes keep skin on their open side; the 3/4 temple edge over the lashes is always hair.
- 27/27 builds pass QA; legacy byte-identical.
