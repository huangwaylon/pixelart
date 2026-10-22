# r10 hair stylist 1: S1 / S2 / S3 designed hair

All use `render.hair_style` + `angel_ring: false`. QA PASS, chain_penetrations 0 (jump_sc, 5 builds each).

**Ramp fix (all three):** `material_bands.hair: [-0.35, 0.985]`. The old light threshold of 0.55/0.7 scattered hair_2 blobs, the main cause of the "random strands" look. Now plum_0 = shadow side + clump lines, hair_1 = mass, hair_2 = ring only. S2 NE f7 census: 86 / 206 / 48.

**S1 waist + beret:** clump lines at 60°/30°, so 2 per side. Ring at y 0.3, just under the brim, all the way round. Fixed bare scalp showing under the tilted beret (hair_cap `clip_all` now uses a tilted plane). Locks have pointed tips. The centre lock is one segment longer, so the hem ends in a soft V.

**S2 twin tails:** tails are teardrop-tapered (3.0, up to 3.8, down to 1.0) and hang closer to vertical. Stiffness 120 curves them gently. Each tail is its own group, which fixed a 4px body-height QA FAIL. Ring at y 0.56 sits on the crown, above the earmuff band.

**S3 high pony:** clump lines at 120°/60° with az_min 70. The only seam is at 180°, and the pony hides it; the head shows just the ring. The pony is slimmer, tapers to 0.7, and is its own group (fixed a 6px height FAIL). The sidelock ellipsoids are now pointed 3-segment chin-length chains.

**Hi-res test (`S2_long_twintails_hires`, ppu 1.0, 64x80):** the ring becomes a smooth arc instead of a staircase. Clump lines read as real separations; tails taper more smoothly. Moderate gain. QA FAILs height delta (4px), likely a fixed-pixel limit meant for 48x64.

**Open:** at 0.75 ppu the S1 bangs points can't be resolved (1-2 forehead rows), and the beret hides most of the S1 ring from the front.
