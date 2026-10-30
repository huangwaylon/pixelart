# Mesh R&D brief (2026-10-30)

Owner: *"Go back and improve the 3D mesh generation phase. Research with a team: what is the current state of the art? Can we improve the
Omni option we're using? What would it take? Break it down into parts? Better reference images? More time? Higher resolution? Focus on a few
different types of characters. Focus on polishing the 3D meshes and rigging and posing first."*

## Test characters (from charlab/designs, ranked top by review r1)
| id | type | why |
|---|---|---|
| `mechanic` (Rio) | overalls, gloves, boots, bandana, ponytail | clothing layers + hair accessory |
| `schoolgirl` (Hana) | sailor uniform, pleated skirt, bob | skirt + hair volume |
| `astronaut` (Nova) | bulky suit + helmet, chibi | hard-surface, big simple forms |
| `shorthair` (Mika) | hoodie + shorts, short hair | casual baseline |

Specs: `charlab/designs/<id>.json`. Concepts: `charlab/designs/concepts/<id>.png`.

## Local stack
- Hunyuan3D-Omni + 2.1 weights, venv and sources: `/Users/waylonhuang/Documents/other/pixelart/.models/hy_omni/`
  (`venv/`, `weights/`, `src_omni*`, `src_21*`, `out/`, `poses/`).
- Previous Omni and 2mv runs and notes: `swordswoman/v2/hy3d/` (NOTES, scripts, `out/omni*`), `swordswoman/docs/hunyuan3d_research.md`,
  `swordswoman/docs/sota_image_to_3d_2026.md`, `reference/3d/`.
- Blender: `/Applications/Blender.app/Contents/MacOS/Blender`. Pixel tools venv: `.models/pixtools/venv`. Gemini images: `swordswoman/tools/gemini.py`.
- The machine is Apple Silicon (MPS, no CUDA). Cloud GPU or paid APIs need owner approval and domain allowlisting, so don't use them without asking.

## Folders (each owner works only in their own)
- `charlab/mesh/research/`: R1, state-of-the-art survey + recommendation
- `charlab/mesh/refs/`: R2, reference images
- `charlab/mesh/omni/`: R3, Omni and mesh-generation experiments
- `charlab/mesh/rig/`: R4, rigging + posing toolchain

## Quality bar for a "polished" mesh (shared by everyone)
- **Shape:** clean, watertight or cleanly separated parts, with no blobs, floaters or melted features. Hands and feet are readable, and the hair and garment
  shapes match the concept. Silhouette IoU vs the reference views ≥ 0.85.
- **Topology:** sensible density for rigging (about 10–40k tris), no self-intersections at the joints, symmetric where the design is symmetric.
- **Rig:** standard humanoid skeleton, clean weights, and no candy-wrapper or collapse at the elbows, knees, shoulders or hips through A-pose → walk keys → arms raised → squat.
- **Pose:** natural, feminine, upright A-pose rest and walk keys.

## Coordination
Append status lines to `charlab/mesh/STATUS.md` as `- HH:MM <owner>: ...`. Never edit another owner's folder. The lead commits; nobody else does.
Clean up your processes when done.
