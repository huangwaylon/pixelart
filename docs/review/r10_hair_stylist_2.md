# r10 Hair stylist 2: S4 / S5 / S6

All three use `render.hair_style` with `lineart.angel_ring: false`. The hair band is crisp, so only the ring gets the light tone: 3 tones (plum_0 / hair_1 / hair_2). All three pass QA on `jump_sc` with chain_penetrations 0.

**S4_halfup_bow** (user favourite, per Lead direction)
- Removed the 3 hanging locks. Added one `pony` chain that starts under the bow knot: 7 segments, widths 3.2 to 4.6, tapering to 0.8 at a point.
- `hair_back` is cut down to a nape cap. The bow sits ~1 unit further back so it covers the pony root, and the ribbon tails hang over the pony.
- The ring wraps the crown (ring_az 180). Clump lines are at ±72/±144, so the tail itself stays clean.
- Physics finding: at gravity 520 the tail floated up and folded during the fall and landing. Gravity 2400, stiffness 500 and damping 0.2 keep it as one mass in every frame.

**S5_side_braid**
- The braid is now anchored on the chest just in front of the right shoulder and lies over the chest (rest_dir forward-down, max_swing 35).
- It used to stick out forward horizontally. It is now shortened to end above the A-line skirt, which stops the skirt from pushing it.
- Widths alternate 3.4/1.9 for the segment bulges. It uses its own `hair_auburn` material (same colours, highlight band at 0.42), so each bulge's top gets a highlight and the braid reads as a zigzag.
- Ends in a 1.6 cranberry tie. The top tie is removed.
- Back of the head under the beanie: a smaller `hair_back` plus a sweep toward the braid, with only 2 clump lines (±120).

**S6_hood_down_long**
- 3 back locks overlap into one cape mass with pointed tips. The centre lock is longer, giving a V-shaped hem, and the side tips fan slightly outward.
- Added 2 tapered front locks (`front_L/R`) so the long hair reads in S/SE/SW.
- Clump lines at ±83/±166 fall on the seams between locks (2 per side). The ring wraps all the way round.

**Open issues**
- At the 16° camera the ring reads almost straight in S.
- S5's back reads short: hair under the beanie, by design.
- S6's hem points are soft in N.
