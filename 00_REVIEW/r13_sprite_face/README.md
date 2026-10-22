# r13 — SE/SW (3/4 view) face perspective fix (game sprite, S4)

Feedback: the SE-facing face looked strange. Her left eye, on the right of the screen, sat too close to the other eye.

**Fix** (`data/faces/kawaii_v2.json`, three_quarter cels, so the same change applies in every frame of every clip):
- There is now a 2 px nose-bridge gap between the eyes (it was 1 px).
- The far eye stays narrow (2 px) and keeps at least 2 px of far cheek beyond it.
- The mouth moved 1 px toward the far side.
- SW/NE/NW use the mirrored cels.

- **[se_sw_face_before_after.png](se_sw_face_before_after.png)**: before is the approved release; after is the new build. It covers idle, walk, run and throw in SE and SW.
- `<clip>/<clip>_SE.gif`, `<clip>/<clip>_8dir.gif`: the rebuilt clips. All 13 clips pass QA.

Next: the HD model work. Each eye gets its own position on a new anime head shape (defined cheek and chin), so the far eye is foreshortened by the 3D model itself rather than by the cel layout.
