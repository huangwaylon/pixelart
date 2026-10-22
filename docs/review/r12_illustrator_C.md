# r12 Illustrator C: S4 full-body cut-scene poses (8)

Sources are in `data/illustrations/S4/poses/<pose>.json`: idle, wave, point, hands_on_hips, recoil, shy, shiver, cheer. Each is 96x160 on `cw_oatmeal_portrait`, in 3/4 view facing left. Rebuild everything with `data/illustrations/S4/poses/_all.sh`, which runs cels, then JSON, then `pipeline.illustrate`, then the lineup and sheet. Outputs go to `00_REVIEW/r12_illustration/poses/`: per-pose renders, `poses_lineup_x3.png` and `poses_spritesheet.png/.json` (transparent, 8 frames, ground_y 153).

## Method (on-model by construction)
- **Shapes:** `_build.py` copies the model-sheet `three_quarter` layers exactly and re-poses them with a 2-bone skin warp: shoulder/elbow, hip/knee, neck tilt, and torso lean about the hip. Nothing is redrawn, so bow, bangs, eyes, colours, sel-out and line rules match the model sheet. With zero pose parameters the rebuild matches the sheet to within 2 px.
- **Secondary motion:**
  - Hair, ponytail, bow tails and scarf tail blend from the head transform into a hang/swing vector.
  - Optional hem flare and shoulder shrug.
- **Pose parameters:** all in `poses_def.py` (angles, z swaps for arms in front, extra shapes, cel choices).
- **Face cels:** 29 new full-body cels in `poses/face/` (`bQ_*`): happy ^^, wide, determined, smug, shy look-away and squeeze >< eyes; smile, joy, cheer, O, set, smirk and wobble mouths; heavy blush, cold nose, and fx (sweat, surprise lines, sparkles, shiver and wave marks). The cels are embedded in the pose JSON, and their anchors follow the head transform.
- **Shy:** one authored `scarf_up` shape (with shade and highlight) covers the mouth.

## QA
- 20-24 colours per pose. 0 overrides.
- 22-53 orphans, reported by `qa.orphan_count` (the model sheet itself has 23). I haven't broken these down by source yet; cheer (53) and recoil (47) should be checked first.
- Each pose went through 5 or more render and view passes.

## Known limits / next
- Mittens are teal like the bow and scarf. Raised hands are kept clear of the bow, but they touch the scarf in shy and shiver, where only the outline separates them.
- Cels do not rotate, so head tilt is kept at 8° or less.
- Bent elbows and knees are blended, not redrawn. The cheer knees and the shiver arm crossing would gain from a 1-2 px override pass.
- The shrug in shiver is subtle.
