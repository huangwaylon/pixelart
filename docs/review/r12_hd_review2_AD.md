# r12 S4_hd round 2 + r13: Art Director re-review

**Verdict: FIXES** (close to shippable; round-1 blockers are resolved).

Checked S/SE/E/NE/N/SW for idle, walk, run, jump_sc, throw and carry_walk, with per-pixel dumps and 5-8x crops. Coordinates are frame-local (x, y).

**Verified OK:**
- AD1, E glint: every E/W frame matches legacy. The only frames without a glint are squint frames (throw f0-5, jump_sc f1-6), and legacy has the same pattern. Profile chin at (26-28, 35).
- AD2, hem: rust row plus brown row, the same structure as legacy.
- AD3, bang arc.
- AD4, mittens: teal wins in all three cases.
- AD5, N f9 loops: symmetric.
- r13 D, sway: N walk ponytail tip moves from x22 to x25 (f2 vs f6). It reads.

**Rust at ~1.5x:** right for the hem, wrong for the head. Head rust in SE idle is 81 -> 166 px.

1. **Trim head rust.**
   - SE: stop the arc 2 px inside the outline; it now reaches the silhouette at x29-30, y26-27.
   - SE: remove the vertical seam rust at x18, y26-27.
   - N idle: arc back to 2 px; it is 4 px at y27.
   - carry_idle N: remove the crown specks.
   - Keep the hem as is.
2. **Bow volume (r13 C not met in sprites).** The loops are one flat teal. 6ACBB6 is used on 0 pixels in any clip.
   - Add a 1-2 px highlight on the upper-front of each loop.
   - Add one 1C4C54 fold pixel toward the knot.
3. **S bow ears are smaller than legacy.**
   - Each ear is now about 2 teal px.
   - There is a lone dark nub at (20, 22), left ear only, so the ears are asymmetric.
   - Want: 3-4 px wide, 2 rows, rounded and mirrored.
4. **S eye spacing jitters.** The bridge switches between 2 and 3 px:
   - carry_walk S f1 and f5;
   - throw S f1-3;
   - jump_sc S f6 and f12.

   Legacy holds a constant 3 px. Lock the S bridge to 3 px; wider-set eyes also read more anime.
5. **SE/SW mouth.** The mouth sits directly under the far eye, 1 px from the cheek edge. SE idle has it at (28, 34); mirror that for SW. Move it 1 px toward the bridge. This is most of the remaining "strange SE face": the eye spacing (2 px bridge, 1 px far cheek) is now correct perspective.
6. **SW far cheek.** x17, y30-34 has no outline (shadow skin against the background), while SE has a 0 outline. Make them consistent.
7. **SE head edge.** Remove the 1-px dark stub at (31, 28).

**Still open from round 1:**
- E/SE ponytail flat-cut tip;
- throw E bow mix;
- climb NW strays.

**Note for the user:** the r13 face shows as a 1-px jaw step plus a 2-4 px chin at sprite size. That is about the limit at 48x64. The stronger anime definition lives in the refs.
