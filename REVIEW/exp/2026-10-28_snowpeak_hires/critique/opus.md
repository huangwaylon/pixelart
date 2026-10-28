1. **Verdicts vs N (scores out of 10)**

| Row | Score | Verdict |
|---|---|---|
| **N** | **6** | baseline |
| VM | 5 | worse |
| KC | 6 | same: it fixes a little and breaks about as much |
| PF | 3 | worse, clearly |
| KCE | 5 | worse |

VM and KC come out almost the same pixel for pixel. The 8x render adds very little; the fix chain and the low-res model decide the result.

2. **Pixel problems**

- **N**
  - SE: a 1px light-teal highlight on the bow doesn't match the other directions.
  - SE and SW: a 2×2 teal mitten square sits in the middle of the coat.
  - S: the beige/lavender border down the coat is a stair-step zigzag.
  - Walk f3 and f5: the beige coat breaks into lightning-bolt fragments, and the light/shadow boundary jumps between frames.
- **VM / KC**
  - S, SE, SW, E, W: a 2px bright orange-brown streak across the fringe makes a hard horizontal ridge (a visor look).
  - S: a stray 2px brown speck in the middle of the coat on the left side.
  - E: the bow shrinks to a 2px-wide vertical teal spike and reads as a horn.
  - SE and SW: the mitten island becomes a 5px plus/cross shape, which is worse than the square.
  - SW: a 1px dark teal diagonal line across the coat (sleeve edge) looks like a stick.
  - Walk: the mitten island pops in and out between frames (f5 to f6).
- **PF**
  - All directions: dark-purple vertical strand lines in the hair. They read as noise and double the outline.
  - SE, E, SW: the orange shine on the hair is a broken streak.
  - E, W, SW: stray light-teal pixels on the bow and scarf (mint, not in the shading ramp).
  - W: a pink skin pixel below the eye.
  - S: the scarf darkens and gets thicker, and the coat has a 2px brown speck.
  - NE: a dark purple band under the bow.
  - Walk: the hair outline shifts by about 1px between frames, and the hair shine and purple strands jump frame to frame. This is the worst flicker of any row.
- **KCE**
  - S: the added interior lines are broken 1–2px dark dashes on the coat, not continuous lines.
  - W: the scarf turns into a heavier dark-teal slab.
  - SW: the diagonal arm line gets darker.
  - Walk: the interior line pieces turn on and off between frames (f2, f5, f7) and add more flicker than N.

3. **Does high-res rendering fix the known issues?**

| Issue | Fixed? |
|---|---|
| Flat beige coat slab | no |
| Teal mitten islands in SE/SW | no (they change from a square to a plus shape) |
| Stub legs | no |
| Blob hands | no |
| Small bow in S | no |
| Fringe ridges | no, worse in VM, KC and KCE |

Rendering at higher resolution can't fix any of these. They come from the model itself (shape, materials, pose), not from how the image is downscaled.

4. **Ship: keep N.** Don't switch to any of the four. Drop PF completely. KC is the only one worth keeping as an option, and only if the fringe streak is fixed and the mitten island is removed upstream. The effort should go into the model: shading on the coat, moving the mittens off the coat front (arm pose), longer legs, real hand shapes, and a bigger bow in S.
