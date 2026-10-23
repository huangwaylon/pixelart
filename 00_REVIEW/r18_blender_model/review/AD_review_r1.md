# AD review r1: A vs B

**Pick: B as the base. Port A's bow shape, back-hair width and scarf drape.**

## Per part
- **Face and chin: B.** Heart taper, pointed chin, clean jaw/neck break. A has ballooned cheeks, a melted chin and a thick neck.
- **Eyes: B, slightly.** Bolder winged lash, but the brows are buried under the bangs.
- **Profile: neither.** B is a flat wall with the eyes proud of the brow.
- **Bangs: split.** A lifts but is puffy and scalloped. B is sharper but plastered flat, with stray highlight blobs.
- **Side locks: B.** A's are stiff slabs.
- **Back hair: A.** B's is 0.23 m wide and invisible from the front. A's is 0.39 m.
- **Ponytail: B.**
- **Bow: A's shape.** A's loops perk up, B's droop like earmuffs. Both read small.
- **Body: B.** Slimmer coat. Both have pipe legs.
- **Topology: B.** GLB is 79.5k tris with 0 non-manifold edges and 0 winding flips. A has flips (Mittens 164, Scarf 96, Bow 40, Ponytail 30) and 902 open edges on its decal eyes.
- **Production: neither.** No UVs, armature or LODs. Scale, Z=0 and -Y facing are correct in both.

## Fixes (priority order)
1. **Profile.** Recess the eyeballs 4-6 mm behind the brow plane. Upturned nose tip 3 mm forward, upper lip 2 mm back, a chin shelf. Trim the side locks 15 mm at the cheek.
2. **Bangs.** Arc them 12-18 mm off the forehead. Keep the 3 V-notches with pointed tips. Replace the highlight blobs with one crown highlight band.
3. **Brows.** Raise them 4 mm, or draw them over the hair, so they show through the notches.
4. **Bow.** Rebuild on A's loop shape at 0.32 m wide (about 1.65x hair width), loops tilted 15-20 degrees up with 2 crease folds each. A 25 mm pinched knot, and 120 mm tails with V-cut ends.
5. **Back hair.** Widen to about 0.34 m. Make the bottom-20% tips uneven, not a sawtooth. Smooth proxy normals (no stripe shading).
6. **Face shading.** Transfer normals from an ellipsoid proxy (no diagonal cheek shadow). Outlines about 40% thinner, tinted warm brown.
7. **Legs and boots.** Taper the knee and ankle (ankle about 0.6x the calf). Shaped boot shaft, 10 mm sole, fuller fur cuff.
8. **Scarf.** Port A's drape onto B's neck. Matte material, cable-knit ribs.
9. **UVs.** Unwrap everything, hidden seams, 1% padding, one hair atlas.
10. **Rig.** Humanoid armature plus chains for the ponytail (4 bones), side locks (3), bow tails (2) and scarf tail. Auto weights, hand-cleaned at neck and skirt.
11. **LODs and export.** LOD0 about 80k, LOD1 about 40k, LOD2 about 15k (Decimate). Apply modifiers. Export without outlines, TorsoProxy or lights.
12. **Materials.** One slot per colour role. Base colours set in the GLB. Remove the unused Lip slot on Head.

Gemini (gemini_AvsB.md, 2 runs) also chose B as the base. It agrees on B's face and A's bow and back hair.
