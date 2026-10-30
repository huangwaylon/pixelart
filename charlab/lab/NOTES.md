# charlab lab: data-driven 3D characters to pixel-art walk cycles

Goal (owner): test many character designs quickly. The pipeline is: designer spec → simple primitive 3D model → shared walk → clean pixel sprites, at several tiers, body shapes and sizes.
Status 2026-10-30: all 8 designer specs are built at 3 tiers x 3 body presets x 4 sizes (288 variant-sizes). All of them pass the blocking gates, and every build is deterministic. No critic calls were made; a reviewer comes later.

## Commands
```
charlab/lab/run.sh <spec.json> [tiers] [bodies] [sizes]     # defaults: simple,medium,detailed  chibi,compact,slim  32,48,64,96
  e.g. ./run.sh ../designs/shorthair.json                   # 9 variants x 4 sizes, ~45 s (6 in parallel, CHARLAB_JOBS)
       ./run.sh ../designs/astronaut.json medium chibi 48   # one cell, ~15 s
python3 charlab/lab/hub.py charlab/designs/<id>.json [status] [note] && python3 REVIEW/build.py   # hub entry
```
- **Python:** `.models/pixtools/venv` (numpy, scipy, scikit-image, opencv, PIL).
- **Blender:** `/Applications/Blender.app` (5.2 LTS, headless).
- **Env knobs:** `CHARLAB_VIEWS` (default `SE,S,E`), `CHARLAB_HEAD_UP` (head pitch cheat, default 12°), `CHARLAB_POLISH=0` (no outline polish), `CHARLAB_SAVE_BLEND=1` (save `rig.blend`; batch does this for the recommended preset at medium tier).

## Architecture (5 files, about 1,700 lines)
| step | file | what |
|---|---|---|
| 1 model | `model.py` (venv) | Spec + tier + preset → **one closed mesh**. The body and every VOCAB piece are signed distance fields (round cones, ellipsoids, rounded boxes, cylinders, elliptic frusta, smooth unions). One marching-cubes pass means every joint is connected and garments never interpenetrate.<br>- **Per face:** material (the outermost layer at the face centre; decals are paint) and line group (head/hair/hat/body/armL/armR/legL/legR/pack).<br>- **Per vertex:** automatic skinning, a softmin over the distances to the body segments (τ 0.045H), top 4 bones. Attached pieces are rigid to their bone; the ponytail uses chain weights; the skirt uses hips + thigh near the hem.<br>- **Toon normals:** the gradient of the Gaussian-blurred field (σ 0.07H), so cel bands are big clean shapes.<br>- 2-4 s per model. |
| 2 rig + walk + passes | `blender_walk.py` (Blender) | Imports the mesh with the custom (toon) normals. Builds one armature with standard humanoid names (`root hips spine chest neck head shoulder/upper_arm/forearm/hand/thigh/shin/foot/toe .L/.R`, plus `tail.N`, `bag`, `backpack`, `tank` as needed), vertex groups and an Armature modifier.<br>**Shared procedural walk:**<br>- 8 frames, in-place treadmill, loopable by construction.<br>- Planted feet via analytic 2-bone IK: stance 60 %, heel strike -8°, toe-off +22° about the ball.<br>- Hips: bob 2.2 % of leg, lateral sway 3 %, roll 5°, yaw 7°. Chest counter-yaw 6° and 3° lean.<br>- Arm swing 17-20° with elbow follow-through and a small lag. Level head with a 2x nod.<br>- Head pitch-up cheat of 12° so the face reads under the 30° camera.<br>- The pelvis drop is solved so the stance leg never over-extends.<br>**Camera:** ortho at 30° elevation; S, SE, E = camera at -Y, (-1,-1), -X. The rest figure is 768 px tall in a 960 px frame, with the ground pivot at (480, 864).<br>**Passes per frame and view:** Workbench flat material/group ID (AA off, exact; decode errors are counted, 0 so far), and EEVEE EXR camera normal + depth, stored as compact npz.<br>48 renders in about 3 s. |
| 3 pixel chain | `pixel.py` (+ `vecline.py`) | Size S → supersample f = 768/S (24/16/12/8), cell 1.25·S.<br>1. Majority label per cell.<br>2. **Silhouette:** parts under 2.2 px are widened (≥ 2 px of fill at any size); only thick parts are eroded half a pixel.<br>3. **Vector outline:** copied from the review prototype. Trace, smooth, pin corners, Douglas-Peucker, clean 1:k runs, pixel-perfect.<br>4. **2-tone cel:** N·L from one upper-left key (KEY from the lock pipeline), smoothed per material. Face skin is flat. The palette `hi` key is used only above N·L .8 (hair_hi). A 1-px occlusion shadow falls under any nearer part (chin, fringe, hems). Band islands under 2-6 px are removed.<br>5. **Interior lines:** only at line-group changes with a depth step (arm\|body, leg\|leg ≥ 0.012H; chin\|neck and pack ≥ 0.04H; hair/hat\|face ≥ 0.015H, always on the hair side). They never thin a part to 1 px and are at least 3-4 px long. Colour is the material's shade at ≤ 48 px; above that, shade on lit cells and K on shadow.<br>6. **Polish:** greedy 1-px outline edits around lamet zigzags and L-corners, kept only if the defect score drops and no gap opens.<br>7. **Face:** eyes + brows stamped at the 3D eye points.<br>8. **Exports and gates.** |
| 4 boards | `boards.py` | `grid_SE_4x.gif`: rows tier x body, cols size, all at the same on-screen height. `boards.png`: matched-scale contact frames + S/SE/E at true relative size. `summary.json`. |
| 5 orchestration | `batch.py`, `run.sh`, `hub.py` | parallel variants, logs in `work/<id>/<tier>_<body>/build.log`; hub entry writer |

Reused from the repo:
- **Copied:** the vector-line method (`docs/team_review/2026-10-30/line_art/proto_vecline.py` → `vecline.py`, generalised to any f and N); the key light; the eyes + brows-only face rule (facesys); the locked-palette idea; the line spec.
- **Imported unchanged:** lamet metrics (`docs/.../line_art/lamet.py`).
- **The snowpeak lesson holds:** simple primitive bodies pixelize cleanly.

## Outputs
`out/<id>/` (tracked, about 45 MB of data for 8 characters; per-frame PNG/TXT are most of the file count):
- `grid_SE_4x.gif`, `boards.png`, `summary.json`
- `<tier>_<body>/<size>/`: `walk_4x.gif` (S | SE | E, loop, 120 ms), `walk_strip1x.png` (rows S/SE/E x 8 frames), `sheet_4x.png`, `<view>_fNN.png` + `.txt` key grids, `gates.json`
- `<tier>_<body>/variant.json`: tris, palette, spec warnings

`work/<id>/` holds the model npz/json, the passes and `rig.blend`. It is gitignored (`charlab/**/work/`, checked with `git check-ignore`) and is about 340 MB for 8 characters.

## Gates (per variant-size; all frames of S, SE, E)
- **Blocking:**
  - lamet zigzag ≤ 1
  - redundant L-corners ≤ 3
  - silhouette gaps = 0
  - colours per frame ≤ the locked palette (every pixel is a palette key by construction)
  - GIF: loops, ≥ 2 frames, every frame ≥ 20 ms (the REVIEW/build.py rule)
- **Report only:** mono (clean-run share), 2x2 K clumps, interior K, eyes placed, silhouette and interior boil (lamet flicker).

Result: **288 / 288 PASS**. Zigzags are 0 everywhere after the polish; before it, the max was 3-8 per frame. Means by group:

| | mono | sil. boil | colours/frame | 2x2 clumps |
|---|---|---|---|---|
| 32 px | .84 | .05 | 11.5 | 4.6 |
| 48 px | .85 | .08 | 11.8 | 8.1 |
| 64 px | .83 | .11 | 12.1 | 6.7 |
| 96 px | .80 | .18 | 12.4 | 5.9 |
| chibi / compact / slim | .84 / .83 / .82 | .09 / .11 / .12 | 12 | 3.4 / 5.5 / 10.1 |

Review masters, for reference: mono .44-.65. Two builds of the same variant give identical frames (md5 checked).

## What the sweeps show (for the reviewer to confirm by eye)
- **Body presets:**
  - Chibi reads at every size, and best at 32-48: big head, face and eyes are always present, and the silhouette is chunky.
  - Compact is the best all-rounder at 48-64.
  - Slim needs 64-96. At 32 its limbs fall back to the 2-px guarantee (outline-heavy, the most 2x2 K clumps); the designer predicted this.
- **Tiers:**
  - The simple tier carries the read at 32-48.
  - Medium adds bands and headwear that matter from 48 up (Kai's headband, Nova's orange rings).
  - Detailed decals (patch, pocket, bib number, pouches, antenna) only register at 64-96 and mostly become 1-3 px specks below that. That is the "detail stops paying off" point: about 64 px for decals.
- **Sizes:** the owner's eyes + brows rule works down to 32 (1-px eyes, no brows under a 12-px head). Brows and catchlights appear from 48-64.
- **Per character:**
  - Mika, Nova, Hana and Rio read clearly.
  - Nova's white suit relies on the dark outline and the suit-shade interior lines.
  - Fern's olive/khaki is low contrast at 32.
  - Marin (slim, dark wetsuit) is the weakest small sprite, as the designer ranked her.
  - Zip's cap brim and bag swing work.

## Known issues / next
- **Interior boil grows with size** (.18 silhouette boil at 96). There is no temporal line snap yet. The lock pipeline's flow-based vertex hysteresis (an `rpos` pass) is the next step if 96 px is kept.
- Slim at 32: 2x2 K clumps on the thin limbs. Consider skipping that cell (designer advice) or using a 1-px-fill limb rule.
- **Eye visibility** is decided per view per cycle. The SE far eye can still change on 1-2 frames at 32-48 px when the 1-px glyph has no free skin pixel.
- The visor is a cut-away helmet with a tinted interior; there is no glass glint yet (planned at the detailed tier through the `glint` anchor, which is already exported).
- **Spec warnings for the designer:** `mechanic` and `runner` hair reference `hair_shade`, which is missing from their palettes; the lab derived it. The antenna rod is thinner than a pixel at chibi, so only the tip reads.
- **Views:** only S, SE and E are rendered. SW/W are mirrors (except asymmetric Zip). The N directions are a camera change (add to `AZ`).
- **Hands:** mittens. Feet are 0.30-0.36H, longer than VOCAB's 0.25H (see SPEC.md).
