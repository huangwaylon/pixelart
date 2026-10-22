# r12 - HD reference model for S4 (M1 hair + bow, M2 coat + scarf, M3 limbs)

S4 (old, ellipsoids) vs **S4_hd** (new, SDF parts). The design is unchanged: one tapered ponytail under the big back bow, with hime bangs.

## What to look at
1. **Close-ups:**
   - **[head_closeup_old_vs_new.png](head_closeup_old_vs_new.png)**:
     - Crown clumps, 7-point hime bangs and flat-cut side locks.
     - The back curtain, now 5 simulated chains x 2 sharp clumps.
     - A 5-clump twisted ponytail ending in 3 points.
     - Bow with open loops, a grooved knot and V-cut tails.
   - **[body_closeup_old_vs_new.png](body_closeup_old_vs_new.png)**:
     - Coat: bodice blended into an A-line skirt with 10 box pleats, a scalloped hem band and pocket flaps.
     - Belt band with a teal buckle, plus a placket and buttons.
     - Scarf: knit tori, a knot, and a flat tail with fringe.
     - Arms: sleeves blended at the elbow, with cuffs.
     - Mittens: palm box and an angled thumb.
     - Tights, and boots with a fold cuff, toe box, sole and heel.
2. **Turnarounds**: [S4_turnaround_3d.png](S4_turnaround_3d.png) vs [S4_hd_turnaround_3d.png](S4_hd_turnaround_3d.png).
3. **3D model**: [model_rest.stl](model_rest.stl), [model_idle.stl](model_idle.stl) and [model_apex.stl](model_apex.stl) (jump apex). GitHub shows them in 3D: drag to rotate. [model_rest.obj](model_rest.obj) with its `.mtl` carries the palette colours.
4. **Sprites, old (left) vs new (right)**: [run](boards/run.gif), [walk](boards/walk.gif), [jump_sc](boards/jump_sc.gif), [idle](boards/idle.gif), [throw](boards/throw.gif), [carry_walk](boards/carry_walk.gif).
   - Each board also has `_slow.gif` and `_keys.png` versions.
   - The boards show the body sheet only. Props (crate, snowball) are separate layers and are unchanged.
   - The jump_sc 8-dir GIFs and contact sheets are in this folder too.
   - At 48x64 the new detail mostly shows as cleaner silhouettes: the bang zigzag, pleated/scalloped hem, boot soles and heels, and the bow.
   - Sub-pixel parts appear only in the hi-res refs and the STLs: seams, buttons, grooves, knit ribs and fringe.

## Status
- All 13 action clips build on S4_hd with QA PASS: idle, walk, run, jump_sc, fall, land, climb, climb_top, pick_up, carry_idle, carry_walk, throw, carry_throw.
- Compared with legacy S4: 0 chain penetrations, equal or lower height deltas, and identical hand/carry anchors and prop-layer coverage.
- Legacy variants are byte-identical to before.
