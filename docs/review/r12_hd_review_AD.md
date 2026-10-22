# r12 S4_hd: Art Director review

**Verdict: ADOPT-WITH-FIXES** (not shippable as-is).

Reviewed idle, run, jump_sc, throw, carry_walk (S/SE/E/NE/N) and climb (N/NE/NW) at 6-9x and at distance. At 48x64, silhouette, readability and speckle match legacy (climb speckle is up, see 8). The pleats, scallops, buttons, buckle and knit don't read at this size; boot soles read a little better. The regressions below cost more than that gain.

Coordinates are frame-local (x, y).

1. **E face, all clips (blocker).** No eye glint in any E frame of idle, walk, carry_walk, throw or jump_sc (run: only in flight_L). The flat-cut side lock covers x29-32 y27-32. Pull it back in profile, or draw the eye over the hair. W idle loses the glint in 5 of 8 frames.
2. **Rust accent lost.** #A85A3A drops 60-70% (idle: 1176 to 342 px). The legacy hem band (y49-50) is gone, so the coat bottom reads flat. Make the hem band at least 2 px tall at sprite scale.
3. **Bang highlight (S/SE/SW).** The rust arc at y22-24 is down to a 2-3 px stub; the 7-point zigzag doesn't read. Restore the arc; it's part of her identity.
4. **Rust cuffs replace the mittens.** Mitten teal must win; thin the cuff or depth-bias it behind the mitten.
   - throw S f2, x12-14 y38-41: rust and brown, no teal.
   - jump_sc N f9, x11-12 y42-43: a 2x2 rust block.
   - carry_walk S f2, x13-15 y31-32: rust specks.
5. **Bow loops.**
   - S idle/carry_walk y22-23: 1 px "antenna" spikes. Restore 2-3 px rounded loops.
   - SE idle f0, x13-18 y24-27: a flat plank with no outline.
   - N jump_sc f9: the loops are unequal and disconnected.
6. **throw E f4 bow (x15-22 y22-30).** Teal, dark teal and lavender are mixed; reduce to 2 tones.
7. **E/SE ponytail.** The bottom is cut flat into a rectangle; restore 2-3 stepped tips.
8. **climb NW f0.** These cause the speckle rise (1.27% to 1.82%):
   - unoutlined teal/rust/lavender hand at x12-16 y33-35;
   - floating belt dash at x22-25 y38;
   - 2x3 cream blob on the hem.
9. **S idle f0.** Remove the lone lavender pixels in the oatmeal; one shading wedge per side.

After fixes 1-5, re-compare. If HD still only equals legacy at 48x64, tell the user plainly: the HD model pays off in reference renders and at larger sprite scales, not in these sprites.
