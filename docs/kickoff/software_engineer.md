# Software Engineer memo: pipeline & tools

**Repo layout**
`spec/` (character, palette, anims: source of truth) · `overrides/<char>/<anim>/<dir>/<frame>.json` · `pipeline/` (Python: rig, sim, raster, pixelpass, qa, export) · `editor/` (static HTML/JS, no build step) · `server/serve.py` · `builds/<anim>_<buildid>/` (gitignored output) · `tests/golden/`.

**Data formats (all JSON, sorted keys, 2-space, schema `"version": N`)**
- `character.json`: bones (name, parent, offset), primitives (ellipsoid radii, bone, material id), face decals (anchor bone/point, per-direction pixel pattern refs), sim chains (scarf/braids/pom: mass, stiffness, damping).
- `palette.json`: ordered list of `{id, name, hex}`, ≤32; materials map to ramps (shadow/base/light/outline ids). Index 0 = transparent.
- `anim/jump.json`: `fps_sim: 60`, frames `[{id, duration_ms, pose:{bone:[rx,ry,rz]}, root:[x,y,z], ease}]`, plus per-frame `height_px` output.
- Override layer: sparse `{"base_hash": "...", "px": [[x,y,paletteId], ...]}`. `paletteId = -1` means ERASE (force transparent). Absent = keep generated. Palette ids, never RGB.
- `manifest.json` per build: build id, git rev, config hash, input file hashes, tool versions, frame list, pivots, per-frame heights, QA report.

**Determinism**
No randomness except `numpy.random.default_rng(seed)` with seeds in spec. Sim at fixed 1/60 s, frames sampled at exact ticks. float64 math, rasterization on integer grid; root offsets rounded with explicit round-half-up before raster (whole-sprite snap, no sub-pixel). Build id = first 12 hex of SHA-256 over canonicalized inputs + pipeline version. Golden-image test: rebuild must be byte-identical.

**Editor <-> pipeline**
`server/serve.py` (stdlib, 127.0.0.1:8765):
- `GET /api/spec`, `GET /api/palette`
- `POST /api/build` (`{anim, dirs?}`) -> manifest; incremental by input hash
- `GET /api/frames/<build>/<dir>/<frame>.png` (base and composited)
- `GET|PUT /api/overrides/<anim>/<dir>/<frame>`
- `GET /api/qa/<build>`
Editor writes only overrides; never touches generated pixels.

**Overrides**
Applied last, after outline/decals/shadow. Each stores the base hash it was painted against; on rebuild, if base changed, override still applies but is flagged "stale" in editor and QA. Erase = id -1. "Copy to other directions" is explicit, never automatic.

**Automated QA (fails build on error)**
Palette compliance; no semi-transparent pixels; pivot/baseline identical across 8 dirs for frame 0 and landing; bounds (>=1px margin); orphan pixels (single-pixel islands); outline closure; per-direction silhouette height delta <=2px at same frame; held-frame identity check; stale overrides; output dims 64x80.

**Risks & mitigations**
1. Rotation noise between directions: rasterize at 1x with fixed per-direction camera matrices, quantize normals to banded shading before outline, and allow per-direction decal patterns. QA height/width deltas.
2. Flicker in held frames: render each frame once; held frames reuse identical pixels (duration, not duplicated renders). Sim sampled only at frame boundaries.
3. Shading speckle at band edges: threshold hysteresis + orphan cleanup pass with fixed rules.
4. Override rot after model changes: base hash + stale flags.
5. Slow iteration: per-direction caching keyed by input hash; target <5 s full rebuild.
