# Snowpeak sprite pipeline

A pipeline that turns a 3D model into pixel art. Sprite sheets come out consistent across all 8 isometric facings, reproducible byte-for-byte, and quick to iterate on from feedback.

```
data/ (character, palette, animation JSON)  ──►  pipeline.build  ──►  builds/<anim>_<hash>/  ──►  out/<anim>/ (latest)
              ▲                                        ▲
              │ edit numbers                           │ re-applied every build
        team feedback ◄── editor (pipeline.server) ──► overrides/<anim>/<DIR>/<frame>.json
```

## Quick start
```bash
python3 -m venv .venv && .venv/bin/pip install numpy pillow     # once
.venv/bin/python -m pipeline.build --anim jump --verify          # build + determinism check (~7 s)
.venv/bin/python -m pipeline.server                              # editor at http://127.0.0.1:8777/editor/
```

## Deliverables (`out/jump/`)
| File | What |
|---|---|
| `jump_sheet.png` | **Game sheet** 768x512: rows = S,SE,E,NE,N,NW,W,SW; cols = 12 frames; 64x64 cells, pivot (32,56), drawn in place |
| `jump_sheet.json` | Engine metadata: per-frame `duration_ms`, `z_px` (jump height the engine applies), `phase`, `events` (`takeoff`, `land`), `cancelable`, `inputLockEnd_ms`, `buildHash`, palette |
| `jump_shadow.png`, `jump_fx_back.png`, `jump_fx_front.png` | Direction-independent strips (same cells and pivot). Draw shadow + fxBack under the character and fxFront over it. Only the character is offset by `z_px` |
| `preview/jump_<DIR>.gif`, `preview/jump_8dir.gif` | 4x / 3x preview GIFs with jump height, shadow, snow puffs and snow ground baked in |
| `preview/slowmo/` | The same GIFs at quarter speed, for animation review |
| `preview/jump_contact_sheet.png` | Labelled 8x12 review grid |
| `preview/jump_sheet_baked.png` | Sheet with z offset, shadow and FX baked in (for engines that don't apply `z_px`) |
| `preview/greyscale_check.png` | Silhouette readability check without colour |
| `reference/character_sheet.png` | 3D turnaround + pixel turnaround + expressions + palette |
| `reference/turnaround_3d.png`, `reference/keyposes_3d.png` | Smooth 3D references the pixel art is derived from |
| `qa_report.md`, `manifest.json` | Automated QA results; input hashes, per-frame hashes, override status |

## Why the 8 views are consistent
* One 3D model (`data/character.json`: ellipsoids on a skeleton), one animation and one secondary-motion simulation feed every facing. Only the camera yaw changes.
* The key light is fixed to the screen, so every facing is shaded the same way. The palette is locked, with banded tones, rule-based outlines and despeckling.
* Faces are hand-designed pixel decals (`pipeline/face.py`) placed on 3D head anchors, so eyes stay crisp at 1 px in every view.
* Planted feet are solved with IK and checked by QA (`foot_slide_px` must be 0).

## Reproducible
* No randomness. The sim uses a fixed 5 ms timestep, and all frame durations are multiples of 10 ms.
* Build id = SHA-256 over every input (data, pipeline source, overrides). Each build writes `builds/<anim>_<id>/` with a snapshot of its inputs.
* `--verify` renders everything twice and fails unless the pixels are identical.

## Iterating on feedback
1. **Design or animation notes** become number edits in `data/`:
   * `data/animations/jump.json` uses readable channels: `arm_L.raise` (180 = overhead), `spread`, `elbow`, `leg_L.hip/knee/ankle`, `spine.tilt`, `head.tilt/roll`, `squash`, `z_px`, `ms`, `face` (`neutral|determined|joyful|squint|smile`), `plant` (IK feet).
   * `data/character.json` holds primitive sizes, materials and clip planes, chains (scarf/braids/pom: `seg_len`, `widths`, `stiffness`, `damping`, `gravity`), and `render.camera_elevation`.
   * `data/palette.json` holds colours, material ramps and shading `bands`.
   Then rebuild. Every facing updates together.
2. **Pixel-level polish** happens in the editor. Painting creates sparse override pixels (palette indices; `-1` = erase), saved per direction/frame and re-applied on every rebuild. If the base frame changes under an override, QA flags it as **stale** so someone can re-check it.
3. **Notes** added in the editor are appended to `feedback/<anim>.jsonl`, keyed to direction and frame.
4. Review history lives in `docs/review/` (each role's review plus the lead's consolidated decisions per round). Locked decisions are in `docs/DECISIONS.md`.

## Editor keys
`B` pencil · `E` erase · `G` fill · `I` / Alt-click picker · `R` revert pixel to base · `O` onion skin · `H` base only · ←/→ frame · ↑/↓ direction · Space play · Ctrl+S save · Ctrl+Z / Ctrl+Shift+Z undo/redo

## Adding a new animation
Copy `data/animations/jump.json` to `data/animations/<name>.json` and edit its frames, then run `python -m pipeline.build --anim <name>`. Open the editor at `/editor/?anim=<name>`.

## Layout
```
data/          source of truth (character, palette, animations)
pipeline/      rig.py (skeleton, IK, squash, chain sim) · render.py (iso raycaster + pixel pass)
               face.py · fx.py · frames.py · export.py · qa.py · reference.py · build.py · server.py
editor/        browser pixel editor (no build step)
overrides/     hand-painted override layers
builds/        versioned builds (immutable)   out/  latest build
docs/          kickoff memos, decisions, review rounds
```

---

# v2 additions (exploration + pixel-review workflow)

## Character generator + variants
`pipeline/chargen.py` turns a high-level design spec into the rigged 3D reference model. Variants live in
`data/variants/<name>.json` and may `"extends"` another variant:
```json
{"extends": "B_pokemon_ow", "name": "H1_B_final", "palette": "cw_charcoal",
 "proportions": {"leg": 5.4}, "outfit": {"hat": "beanie", "scarf_tails": 1, "fringe": "high"},
 "render": {"ppu": 0.75, "v2": true}, "frame": {"size": [48, 48], "pivot": [24, 41]},
 "ramp_overrides": {"coat": ["ink", "char_1"]},
 "anim_patch": {"frames": {"crouch": {"pelvis_drop": 2.2}}}}
```
```bash
.venv/bin/python -m pipeline.build --variant H1_B_final          # -> out/variants/H1_B_final/
.venv/bin/python -m pipeline.board --title "..." --out out/boards/x --variants A B C   # synced comparison GIFs
```
* `render.ppu` sets resolution (pixels per world unit): 0.55 ≈ 24 px, 0.75 ≈ 32-36 px, 1.0 ≈ 42-47 px, 1.33 ≈ 56-62 px tall.
* Colourways are in `data/palettes/cw_*.json`: one 32-colour master palette with per-material ramps and `material_bands`.
* `render.v2` turns on procedural pixel rules (`pipeline/pixelrules.py`) and the pom-pom pixel part. Each rule encodes a recurring hand fix from the pixel reviews.

## Pixel-level review loop (every pixel has a purpose)
```bash
.venv/bin/python -m pipeline.pixelreview --build out/variants/H1_B_final            # 96 zoomed sheets + census.json
.venv/bin/python -m pipeline.override --variant H1_B_final --dir S --frame 6 \
    --set 23,14,outline --reason "close outline gap on beanie" --author AD           # reason required
.venv/bin/python -m pipeline.override --variant H1_B_final --dir S --frame 6 --preview  # check without rebuilding
```
Overrides store their reasons. QA treats reviewed pixels as deliberate and flags any override that goes **stale** if the generated base changes.

## 3D grounding
Each build writes `guide/guide.json` (projected joints and depth per direction and frame) and
`reference/grounding_3d_vs_pixel.png` (smooth 3D reference beside the pixel frame with the rig overlaid).
