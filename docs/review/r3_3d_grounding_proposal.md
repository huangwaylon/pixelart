# R3 — Grounding pixel art on a maintained 3D reference (3D Artist + Software Engineer)

## Where we are
The contact sheet shows what happens when ellipsoids are rendered straight to pixels. The beanie is a flat cream dome and the E/W heads split into hard wedges. Mittens and scarf turn into blobs, and the faces are tiny marks on a big skin disc. GBA/DS overworld sprites are *drawn* shapes, and style rules can't get us there.

## 3D Artist
"The model is good at *where* things are: joints, facing, overlap, the arc of the jump. It's bad at *what they look like* at 40 px. Hair, hat and face carry the character, so they must be designed per direction in pixels. The model should stay crude on purpose. It's a mannequin, so nobody polishes it."

## Software Engineer
"A caps quality where it is today. C fixes the head but leaves a rendered body next to a drawn head, which is a visible style seam. B(i) keeps all our guarantees. One rig places every part, so the 8 directions stay consistent. Parts are data, so builds stay byte-reproducible. Feedback is still 'edit a number or a part, rebuild'. Effort is bounded because each part is drawn once and reused in every frame and animation."

## Evaluation
| Option | Consistency | Reproducible | Iterability | Artist effort | Pokémon ceiling |
|---|---|---|---|---|---|
| A restyle | high | yes | high | none | low |
| C hybrid head | high | yes | high | low | medium (seam) |
| **B parts + underlay** | high | yes | high | medium, one-time | **high** |

## Joint recommendation: B, reached via C as phase 1
**The reference model** (`data/character.json`, kept low-detail) maintains:
- Proportions: 2.5-head chibi, ~40 px tall, head about 40% of height.
- Rig: the current bones (`root, pelvis, spine, chest, neck, head, shoulder/elbow/hand_L|R, hip/knee/ankle_L|R`) plus attach points `hat_top, hair_back, scarf_knot`.
- Part IDs: each primitive gets a `part` field: `head, hair, hat, torso, hips, uparm_*, forearm_*, mitten_*, thigh_*, shin_*, boot_*, scarf, braid_*, pom`.
- IK, squash and the verlet chains stay as they are.

**Guide export** (`builds/<id>/guide/<DIR>/<frame>.*`):
- `guide.json`: each joint's 2D position and depth; each part's anchor, screen angle, length, view yaw/pitch and `z_order`.
- `partid.png`, `mask.png`, `bands.png` (3-tone light band from normals).
- `underlay.png` (the current render).

**Part library** (`data/parts/<part>/*.png` + `<part>.json`):
- PNGs are palette-indexed. The JSON gives each cel's pivot, attach points and the yaw/angle range it covers.
- Head, hair and hat: 8 yaw × 3 tilt cels. Faces stay as decals, anchored per head cel.
- Limbs: 8 screen-angle buckets × near/far shade. Mittens and boots: 8 yaw cels.

**Compositor:**
1. For each part, pick a cel by yaw/angle and blit it at its projected joint, in `z_order`.
2. Add the outline with the existing `add_outline`.
3. Add inner lines where the part ID changes across a depth jump.
4. Apply overrides on top, unchanged.

**Squash/stretch and secondary motion:**
- Squash moves the joints, so parts spread apart or bunch together.
- Torso and head have pre-drawn `squash`/`stretch` cels, chosen when |1-s| > 0.08. Cels are never resampled.
- Chains (scarf, braids, pom) are drawn as small segment cels along the simulated points, so they stay deterministic.
- Long limbs are two cels that overlap at the joint.

**Editor:**
- New Parts mode: edit a library PNG with a live preview of every frame that uses it.
- Toggleable underlay, part-ID and joints overlays for painting overrides (B(ii)).
- QA flags overrides that go stale when a part changes, and any part that fell back to the render.

## Phased plan
1. **Guide export + editor overlays.** No change to the output.
2. **Head library (= C).** Draw head, hair and hat in 8 directions × 3 tilts and composite them over the rendered body.
3. **Body part library.** Switch the body to parts, with the render as fallback.
4. **Squash/stretch cels and segmented chains.** QA gate: no fallback parts.
5. **Retire direct rendering as the shipping output.** It stays as the guide exporter and underlay generator.

DECISIONS.md changes: **Model** (reference rig, not the shipped look) and **Lines** (computed on composited parts). Camera, frame, timing, palette, overrides and builds are unchanged.
