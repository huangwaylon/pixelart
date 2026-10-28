**1. 2mv single** — On-model: 7 | Cleanliness: 5 | Rig-ability: 1 | 48px Ref: 4
*Defects:* Sleeves fused into skirt (`parts exploded`), impossible to rigid-bind. Bangs severely occlude the face in `iso SE 30deg` and `48px SE x4`. Obi and hem are lumpy and lack crisp silhouettes.

**2. A split** — On-model: 7 | Cleanliness: 4 | Rig-ability: 5 | 48px Ref: 5
*Defects:* Brutal boolean cuts leave jagged arm/torso seams (`parts exploded`). Rotating arms in `rigid pose test` exposes flat, un-capped shoulder stumps and floating geometry. Face still hidden at 30° SE.

**3. B per-part** — On-model: 4 | Cleanliness: 6 | Rig-ability: 7 | 48px Ref: 4
*Defects:* Severe proportion drift: wasp-waist torso and tiny head (`front`). White texture bleeding on sidelocks (`front`/`rigid pose test`). Gaping shoulder sockets visible in `side` and `pose test side`.

**4. C PartCrafter** — On-model: 2 | Cleanliness: 2 | Rig-ability: 2 | 48px Ref: 2
*Defects:* Total hallucination. Bow is a flat horn (`side`); hair silhouette is destroyed. `parts exploded` splits the face into horrifying eyeball/skin fragments while fusing sleeves to the torso. Arms cannot pose (`rigid pose test`).

**5. A+B hybrid v3** — On-model: 8 | Cleanliness: 8 | Rig-ability: 9 | 48px Ref: 8
*Defects:* Exposed skin-colored shoulder/arm caps create a bright band in `pose test side`. Procedural bow sits slightly too high/forward (`front` vs 2D target), and the bun lacks the 2D wrap-around ribbon. Bangs still obscure the up-stage eye in `48px SE x4`.

**VERDICT: Adopt A+B hybrid v3.**
It is the only mesh with clean rigid articulation, proper kimono sleeve flare, and readable 48px separation. **Fix next:** Recolor upper-arm joint spheres to match the red kimono fabric so `pose test side` doesn't flash skin, push the bow back/down onto the bun, and trim the right-side bangs back 15% so both eyes read at `48px SE x4`.
