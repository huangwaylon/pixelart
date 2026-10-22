# r13 Review 2: turnaround round 2 (AD + Character Designer)

**Verdict: FIXES.** Done: R1 items 3-6, 10 and the back nape. All lead concerns confirmed.

1. **Front bow reads as buns or cat ears** (x27-38 and x57-68, y3-17; also head_front). The loops are round closed lobes. Their highest point is the inner end (x36-39, y3), which makes an ear shape. Redraw each loop:
   - a wedge that widens outward, behind the hair, at y6-13;
   - tilted down-out, at most 5 px showing;
   - one `teal_0` crease toward the hidden knot.
   Fix head_small first, then re-sync.
2. **Back hair reads as a cape** (x28-67, y42-71). It is 40 px wide with a flat bottom, it hides the arms, and the shoulder ledges at y42-44 make a bell. Make it a curtain:
   - at most 30 px wide (x33-62), tapering to 22 px;
   - 4-5 clump tips at staggered heights, y64-76;
   - sleeves visible at x28-33 and x62-67.
   **Front (reconcile):** hair beside the arms (x27-30, y36-68) is a solid 4 px column. Make it 2 px broken strands that end by y62, in the 3/4 view too.
3. **Proportion: change to 5.0 heads.** Legs from hem to sole (y86-154) are 2.4 heads, too long for cute. Remove about 12 px: thigh/shin -6 and boot shaft -6, so the sole is at y142. Update the guides.
4. **Knee kinks:** the inner edges step in at y104 and back out at y112. Use one monotonic taper (9, 7, 7, 5). The inner seam `IK..II` should be 1 ink pixel per leg.
5. **Tights read as armour:** the sheen is in separate blocks (y107-108, y113-123). Make it one continuous 1 px line from y96 to y122. In the side view, the back of the leg is a 4 px ink slab (x48-51); cut it to 1-2 px.
6. **Boots are sticks:** the 5 px shafts (`PdddP`) have a flat fold at y140. Make them 6-7 px with a slight curve and a diagonal fold.
7. **Side profile has duck lips** (x34-38, y15-31; also head_side). The forehead is a vertical wall (x36, y15-23). The nose (x34, y24) and lip (x35, y25-26) stick out almost equally, and the mouth is a slash. Fix:
   - a soft convex forehead;
   - an upturned 1 px nose at x35, y23;
   - step back at y24;
   - one `line_skin` mouth pixel at x37, y26;
   - a rounded chin at y28-30.
8. Re-check silhouettes after 1-3.
