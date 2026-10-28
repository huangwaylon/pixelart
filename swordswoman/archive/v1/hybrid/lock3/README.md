# lock3 (S3 r3, identity owner) — READ ONLY after MANIFEST.json; changes only via the lead as lock3.1

Built from lock2. Sources: `src/head_{S,SE,E,NE,N}.pix` (hand-typed; `o` = bow loop mask, `k` = knot mask), builders
`tools/hybrid/h4/heads.py` (heads, acting stamps, expressions) and `tools/hybrid/h4/lock3_stamps.py` (body stamps, manifest).

| item | change vs lock2 |
|---|---|
| hair (1) | stripes replaced by 3-4 clustered strand groups of varying length, lit upper-left mass, 2-3 px bang tips. lit share (hair_1+hair_2)/hair: S .32 SE .34 E .32 / NE .21 N .21 |
| bow (2) | loops ~0.3 skull width: S 85 px (front), SE/SW 62, E/W 56, NE/NW 55, N 66. N/NE/NW: loops joined through a 3x3 knot (+ band) over the bun. One shading rule for every dir: C upper-left rim, R body, r right/lower + crease at the knot, v underside |
| ribbons (3) | `stamps/ribbon_{neutral,trail_out,trail_in,float,swing_mid}_{L,R}`: 2->3->2->1 px taper, pink_1 over pink_0, 1 px K root, S-curve; drawn over=0 (behind arm/body, never across the chest) |
| sleeves (4) | bell cuff: dark arm band on top, flare exponent 1.9, 2-row red_0/red_1 lining at the mouth, K outline (`stamps/sleeve_bell_orn`) |
| arms (5) | hand = 2x2 skin (s,s / s,m) + K; upper arm limbs taper |
| purple (6) | `orn=` on the near right-arm cuff: 2 purple_0 px on the band + 2 px cord (S SE E SW) |
| katana (7) | one deterministic guard glyph per snapped angle: 4 px bar + 3 px kagi crescent (T,w,T) with a kept transparent notch; `stamps/katana_<ang>_h<hook>.png` |
| E/W corset (8) | 2 px leather_2 side strip with a steel buckle edge |
| diagonals (9) | SE/NE head +2 px toward facing, SW/NW -2 px; buckle already 3 px off-centre on SE |
| idle blade (10) | S/SE/SW 45 deg from fist y 89, N/NE/NW 135 deg: tips at y <= 103 (above the 104 baseline) |
| acting heads (11) | `head_<D>_act-{back,down,squash,lag}.png`, expressions + `closed` + `grit` (2 px red_0 mouth under the nose) |
