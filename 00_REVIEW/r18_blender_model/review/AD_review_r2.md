# AD review r2: Model B

**Verdict: FIXES.** User request partly met.

## Profile vs refs 6, 2, 3 and 9
The nose tip is 7.6 mm past the brow. Upper lip -81, lower lip -79 and chin -72 mm, against a tip of -93 mm. So nose to chin is one straight diagonal. Ref6 alternates in and out: sellion dip, upturned tip, forward lip, chin groove, rounded chin, jaw line. At 96 px the nose is 1 px and the eye touches the front silhouette.

## Triangle shadow
It stays with shadows and outlines off, so it is mostly the dead band between key and back fill. With a single key, real seams remain and **would show in game**: a vertical seam at the 25 mm face-mask ramp, temple and jaw kinks, and an ear nub.

## The 12 fixes
- **Done:** 3, 4, 7, 8, 12.
- **Partial:**
  - 1: profile.
  - 2: the band looks stitched.
  - 5: sawtooth tips.
  - 6: the seams above.
  - 9: Solidify shells overlap 100% inner/outer. Bangs use 1% of the atlas.
  - 10: see Rig.
- **11 verified:** 81,410 / 43,504 / 16,075 tris. 0 flips. 0 non-manifold, except 21 edges on the LOD2 scarf.
- **Rig:** 39 bones. Weights clean (all verts weighted, at most 4 influences, normalized). Hair_Back uses only head and chest, so it swings as a slab. Skin pokes through at the shoulder.

## Fixes
1. **Nose.** Sellion -3 mm. Tip +4 mm forward, +2 mm up, crisp underplane. Target 2 px at 96 px.
2. **Mouth and chin.** Upper lip +3 mm with a roll. Lip groove -2 mm. Chin +5 mm forward, 4 mm higher. A defined jaw line.
3. **Eyes.** Recess 2.5 mm, so skin shows in front of the cornea.
4. **Normals.** One smooth head proxy with a 50 mm falloff. Native normals only on the nose and lips. Remove the ear nub and temple kink.
5. **Preview light.** The fill must not leave a dead band.
6. **Side lock.** Move it 8 mm back, off the eye.
7. **Back hair.** Add 3 chains of 3 bones. Use tapered clumps.
8. **Crown highlight.** One smooth band.
9. **UVs.** Separate the inner shells. Hair atlas at least 60% used.
10. **Skinning.** Fix the shoulder and the LOD2 scarf edges.

Gemini (gemini_B_r2.md) also says FIXES on the same points.
