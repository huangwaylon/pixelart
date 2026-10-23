# r21 round 3: self-critique (AD r1 notes + user notes applied)

## Done
- **Face:** VRoid-style soft oval. Fuller jaw, small rounded chin ellipsoid, cheek pads, slightly flat face plane. The V chin is gone. The eye markers are recomputed on the new face (+0.2 z), and the sprite face cels sit as before.
- **Bow:** seated ON the hair at the ponytail root (knot sunk about 0.8 into the hair). The spring and tail chains are re-anchored on the knot with the same spring constants.
  - The loops are wide, flat satin ribbon: a lens section around a teardrop, pinched at the knot.
  - They read as horizontal wings in front and back, and as an open loop with a dark opening from the side. The knot is chunkier.
- **Soft ends:** the temple spikes are removed. Fringe corners are rounded and the notches shallow. The side-lock cut is blunt-rounded. The back sheets have a subtle V (0.5) with rounded corners. The ponytail tip is rounded.
- **Side and back:** the legacy hair_back ball is replaced by 2 static layered side sheets per side. The 5 simulated back sheets now fan out from the ponytail root (new `root_to`).
- **Ponytail:** no rings (Catmull-Rom profiles).
- **Mittens:** clearly bigger (rounded box 1.85 x 2.0 x 1.6, r 1.45), round, with a thumb.
- **Coat:** waist pinch, deeper soft folds (6), cuffs smooth-unioned into the sleeves.

## Remaining, ranked
1. **Side locks** read as thin brackets in front view, with a sliver of background between the cheek and the lock. They need to face front more and touch the cheek.
2. **Side view:** the side lock, side sheets and back sheets still read as a stack of planks with dark gaps and stepped bottoms. They should fuse into one layered mass.
3. **Temple corner:** the dome's face-opening corner shows beside the outer fringe panel.
4. **Fringe** cut edge reads straight and visor-like in the front close-up. It is acceptable for a hime cut, but could arc more.
5. **Hem band:** a few dark or missing pixels at the skirt bottom in the side and 3/4 views (fold displacement on the cone cap).
6. **Scarf fringe** looks like a comb (5 fat tines).
