# r12 Illustrator B: S4 expressions and front bust

- Sources:
  - `S4/bust.json`: 10 variants.
  - `S4/bust_front.json`: neutral and smile.
  - `S4/face/`: the cels.
- Renders: `00_REVIEW/r12_illustration/expressions/`.

## Rules
- Eyes follow the model sheet: near 10x12, far 7x12, ink lash, teal iris ramp, catchlight upper-left, line_skin lower lid.
- Expressions change only lids, iris, brows, mouth, blush and FX. A owns the anchors. `gen` writes only the brow, fx and sweat anchors.
- Brows are 2 px: an ink core with plum_0 tapers at y28-29.
- Blush is always hatched. There is none on neutral, determined, angry, surprised, worried or sad.

## Expressions

- smile: upturned mouth
- laugh: ∩ eyes
- surprised: small iris and an "o" mouth
- sad: tear and frown
- angry: glare and anger mark
- embarrassed: heavy hatch and averted eyes
- determined: lowered, slanted lid
- worried: sideways glance and sweat drop
- content: ‿ eyes

## Round 1
- Brows redrawn.
- Face re-anchored to A's turn.
- Weak pairs separated.
- Blind tests: 8/10, then 10/10, then 10/10.

## Round 2 (AD review 2)
- **2, neutral mouth:**
  - Already a 3 px line_skin line at x35-37 y53. Nothing in the current data puts skin_1 at y54, so the review probably read the stale root renders.
  - Kept as specified.
- **3, determined:**
  - Each lash steps 1 px down toward the nose.
  - Mouth: a 4 px plum line with line_skin ends turned 1 px down.
- **4, embarrassed:** sweat drop removed.
- **5, angry:** the new 7x7 mark has red_2 corner arms 2 px long and a plum_0 edge. It sits at x25-31 y13-19, on the temple hair edge.
- **9, folder:**
  - Deleted the stale root files: 39 `bust_*` files (all except `bust_16_*`) plus `bust_slots_x4`.
  - The README now points to `expressions/`.
  - bust_16 re-rendered.
- **Extra fixes, found by blind tests:**
  - Test 4 scored 7/10: determined read as angry, and angry's open lid read as surprised. Fix: angry eyes narrowed 1 row.
  - Test 5 scored 8/10: smile and embarrassed swapped. Fix: heavy hatch is now 2 on, 1 off.
  - Test 6 scored 10/10 (3 high, 5 med, 2 low). Weakest pairs: smile vs neutral, determined vs sad.
- **Gate:**
  - Variants: 18-23 colours and 5-9 orphans.
  - bust_16: 15 colours and 8 orphans.
- Crops: `00_REVIEW/r12_illustration/fixes/r2_B_*`.
