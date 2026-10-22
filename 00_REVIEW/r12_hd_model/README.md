# r12 M1 - HD reference model for S4 (hair + bow)

S4 (old, ellipsoids) vs **S4_hd** (new, SDF parts). The design is unchanged: one tapered ponytail under a big back bow, with hime bangs.

## What to look at
1. **[head_closeup_old_vs_new.png](head_closeup_old_vs_new.png)**: the main change. You can see:
   - 12 crown clumps sweeping back to the bow.
   - Hime bangs: 7 points, with the centre pair split.
   - Flat-cut side locks.
   - A back curtain of sharp clumps.
   - A ponytail of 5 twisted clumps ending in 3 points.
   - Open bow loops with creases, a grooved knot, and V-cut tails that now swing with the chain sim.
2. **Turnarounds**: [S4_turnaround_3d.png](S4_turnaround_3d.png) vs [S4_hd_turnaround_3d.png](S4_hd_turnaround_3d.png).
3. **3D model**: [model_rest.stl](model_rest.stl) and [model_apex.stl](model_apex.stl) (jump apex). GitHub shows them in 3D: drag to rotate. [model_rest.obj](model_rest.obj) with its `.mtl` carries the palette colours.
4. **Sprites**: [S4](S4_jump_sc_8dir.gif) vs [S4_hd](S4_hd_jump_sc_8dir.gif) (8-dir GIFs), plus the contact sheets.
   - At 48x64 most of the new detail is below 1 px, so the sprites change little: the bang zigzag, the side-lock cut and the bow shape.
   - The sub-pixel extras appear only in the hi-res refs and the STL: part-line groove, crown whorl, temple wisps, loop creases and knot grooves.

Both builds pass QA. Legacy variants are byte-identical to before.
