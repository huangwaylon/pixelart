# r21 round 2: self-critique (built before the AD r1 notes and the user notes arrived)

Changes since r1:
- **Ponytail:** 4 layered clumps (2 on top, 2 tucked under), narrow at the knot, swelling, S taper.
- **Scarf tail:** chunky.
- **Fringe:** roots sunk deeper under the dome.
- **Temple wisps:** removed.
- **Mesh export:** welded + Taubin-smoothed (f_mesh_export).

Remaining issues, ranked (most are now covered by the AD r1 notes and the user notes):

1. **Face:** the inherited V chin looks sharp, which the user flagged.
2. **Bow:** floats about 1.9 units behind the hair (the knot sits at z -10.75, but the hair surface is at about -8.6). The loops read as torus "hoses".
3. **Hair tips** are pointy everywhere: the temple spikes (the temple pieces made the "jagged triangles" under the fringe), the V back sheets, and the needle ponytail tip.
4. **Fringe** still reads as a visor slab. **Side locks** flare like boards.
5. **Ponytail** shows faint rings. Cause: the w/t profiles were linearly interpolated, so the slope kinks at each knot. Fixed for r3 with Catmull-Rom profiles.
6. **Side/back masses** below the ears: the legacy hair_back ball plus stepped curtain plates.
7. **Mittens** not visibly bigger. **Coat** barely changed.
