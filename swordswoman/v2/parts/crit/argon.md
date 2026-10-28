**2mv single**
* Scores: On-model: 6 | Cleanliness: 5 | Rig-ability: 3 | 48px Ref: 6
* Defects: Unsegmented mesh prevents rigid posing (pose tests empty). Sleeves fuse into torso/skirt (`parts exploded`). Obi/skirt lack sharp silhouette separation (`front`).

**A split**
* Scores: On-model: 6 | Cleanliness: 5 | Rig-ability: 6 | 48px Ref: 6
* Defects: Boolean cuts leave flat caps and shoulder gaps when raised (`rigid pose test`). Skirt clips thighs during stride (`pose test side`). Obi texture bleeds across waist cut (`front`).

**B per-part**
* Scores: On-model: 4 | Cleanliness: 6 | Rig-ability: 6 | 48px Ref: 5
* Defects: Severe skin-tone projection errors on bangs/hair (`front`, `iso SE`). Missing obi entirely (`front`, `back`). Detached shoulder gaps and bow sits too small/forward (`side`, `rigid pose test`).

**C PartCrafter**
* Scores: On-model: 3 | Cleanliness: 3 | Rig-ability: 3 | 48px Ref: 4
* Defects: Torso and skirt fused into one piece, failing requirements (`parts exploded`). Floating geometry fragments near hands (`front`, `back`). Distorted hair/bow silhouette (`side`, `iso SE`).

**A+B hybrid**
* Scores: On-model: 6 | Cleanliness: 6 | Rig-ability: 7 | 48px Ref: 7
* Defects: B-arm shoulders lack volume, leaving gaps at A-torso sockets (`rigid pose test`). B-legs clip through B-skirt in stride (`pose test side`). Obi band broken at waist seam (`front`).

**Verdict: Adopt A+B hybrid.**
It preserves the accurate head/torso of A while utilizing the cleaner limb/skirt volumes of B. **Next fixes:** Extend upper-arm geometry into spherical caps to hide shoulder gaps during rotation, widen the skirt bell (or add a tilt bone) to clear striding legs, and repaint vertex IDs on the torso to restore a clean, continuous obi band.
