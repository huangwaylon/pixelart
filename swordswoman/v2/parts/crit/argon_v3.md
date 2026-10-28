**2mv single** — On-model: 7 | Cleanliness: 2 | Rig: 1 | 48px: 6
*Defects:* Unsegmented mesh fails rigid-rigging requirement (`parts exploded`); sleeves/skirt fused into a blobby mass (`front`/`back`); bow is a melted blob lacking ribbon tails (`back`).

**A split** — On-model: 7 | Cleanliness: 5 | Rig: 6 | 48px: 6
*Defects:* Arm rotation exposes jagged cut seams and skin-colored artifacts (`rigid pose test`); planar boolean cuts leave flat, unnatural part caps (`parts exploded`); bow lacks distinct lobes (`back`).

**B per-part** — On-model: 4 | Cleanliness: 7 | Rig: 8 | 48px: 4
*Defects:* Severe facial/hair texture bleeding (`front` head); unrequested shoulder cutouts expose skin (`side`/`pose test side`); black vertex-color artifacts streak down the legs (`pose test side`).

**C PartCrafter** — On-model: 2 | Cleanliness: 1 | Rig: 2 | 48px: 2
*Defects:* Splits by material/eyes rather than anatomical joints (`parts exploded`); floating mesh debris around waist (`front`/`rigid pose test`); proportions and flat-bill bow completely off-model (`side`).

**A+B hybrid v2** — On-model: 8 | Cleanliness: 8 | Rig: 9 | 48px: 8
*Defects:* Procedural bow sits too high on the bun and lacks the downward ribbon tails from the turnaround (`front`/`back`); sleeves are tubular rather than flared kimono bell-sleeves (`front`); overhanging bangs still obscure the far eye (`iso SE 30deg`/`48px SE x4`).

**VERDICT: Adopt A+B hybrid v2.**
It is the only rig that survives the `rigid pose test` without breaking silhouette or exposing holes. **Fix next:** 1) Push the procedural bow down into the hair crease and add the two downward ribbon tails (`back`). 2) Flare the lower arm meshes into wide bell-sleeves (`front`). 3) Trim or push back the front-right bangs on the head mesh so both eyes read clearly in `48px SE x4`.
