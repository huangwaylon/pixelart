# r12 Illustrator C: S4 full-body cut-scene poses (8)

The 8 poses are idle, wave, point, hands_on_hips, recoil, shy, shiver and cheer. Each is 96x160 on `cw_oatmeal_portrait`. Sources are in `data/illustrations/S4/poses/<pose>.json`. Rebuild everything with `poses/_all.sh`. Outputs go to `00_REVIEW/r12_illustration/poses/`: per-pose renders, `poses_lineup_x3.png` and `poses_spritesheet.png/.json`.

**Method:**
- `_build.py` copies the model-sheet `three_quarter` layers exactly. It re-poses them with a 2-bone skin warp (shoulder/elbow, hip/knee, neck, torso lean).
- Secondary motion: hair, ponytail, bow and scarf tails hang and swing; optional hem flare and shrug.
- Parameters are in `poses_def.py`. Face cels (`bQ_*`, in `poses/face/`) are embedded in the pose JSON.

**Known limits:**
- Cels do not rotate, so head tilt is kept at 8° or less.
- Elbows and knees are blended bends.

## Round 1 fixes (AD review 1)
- **Re-render on A's update:** A's sel-out fix and turned 3/4 face (with brows) are inherited through `_all.sh`. New brow cels per expression.
- **Orphans:** each pose was at 22-53 and is now at 0-3. The rest are inside face cels.
  - The hem zipper went with A's fix.
  - Single-pixel cels fixed.
  - A cleanup pass in `_build.py` recolours any leftover 1 px speck outside the face cels to its dominant 4-neighbour colour. Stored as `fix_*` cels (0-3 px per pose).
- **Shiver:** I hid the scarf tail (tucked under the hug) and re-crossed the arms, so each mitten now lies on an oat sleeve instead of the teal scarf.
- **Cheer:** tuck jump redrawn. Near shin kicked back, far leg hanging. 2 px tights gap and both cuffs visible.
- **Wave:** sharp knee bend on the back leg (`knee_soft` 6) plus a kneecap highlight.
- **Point:** elbow taper (`pinch_far`), a slight forearm lift and a 1x2 finger. Figure moved 2 px right.
- **Colours:** 20-24 per pose. 0 overrides.

## Round 2 fixes (AD review 2, items 6-8)
- **6, blush removed on point, hands_on_hips and recoil.** These poses set `blush_L`/`blush_R` to `None` in `poses_def.py`, so the inherited model-sheet blush cels are dropped. Idle, wave, shy, shiver and cheer keep theirs.
- **7, wave knee.**
  - Removed the `kneecap_hi` mauve 1x4 column (x47 y109-112).
  - New cels in `_cels.py`. `bQ_knee_split` (ink 1x6 at x46 y107-112) extends the leg split down to y112. `bQ_knee_hi` (mauve 2x1 at x51-52 y112) sits on the back-leg bend.
- **8, hands_on_hips eyes.**
  - The smug 3-row half-lid is replaced by `bQ_far_det2`/`bQ_near_det2`. These are B's bust determined eye scaled to pose size (far 6x9, near 8x9).
  - It keeps the same shape as B's: the lid is lowered 1 row from neutral, the lash is 2 rows thick, and its inner end drops 1 px toward the nose (B's fix-3 slant).
  - Brows stay flat and the smirk stays, so it still reads confident rather than angry. Point keeps its steeper `bQ_*_det`.
- **Gate:** orphans are 0-3 per pose and colours 20-23. Before/after 8x crops are in `00_REVIEW/r12_illustration/fixes/r2_C_*`.
- **Inherited changes:** idle, shy, shiver and cheer each show 1-2 px of change. These come from concurrent model-sheet edits and the cleanup pass, not from round-2 edits.
