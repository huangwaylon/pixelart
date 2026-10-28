# tools/pixel: hand-cleanup toolchain for the sprite cells

Workflow: **snapshot** a model render round, then **paint sparse overrides** (CLI or editor). Next, **apply** them to get the clean frames, and **review / lint / gif** the result.

Ideas and code were adapted from `~/Documents/other/pixelart` (`pipeline/override.py`, `pixelreview.py`, `server.py`, `editor/`). That repo is read-only for us.

Run everything from the project root with `.venv/bin/python`. Frames are **0-based** (`fNN.png` = `renders/..._f<N>_64.png`). Coordinates are `(x = column, y = row)` in the 128x128 cell, and the pivot is (64, 104).

Never touch `model/`, `renders/`, `docs/palette.json` or `docs/design_bible.md`. Pixel work lives in `pixel/`.

## Layout
```
pixel/base/<anim>/<DIR>/fNN.png        snapshot (byte-identical copy of the round's sprite cell). Never edit.
pixel/base/<anim>/_id/<DIR>/fNN.png    object-ID pass of the frame (region tags for lint)
pixel/base/<anim>/SNAPSHOT.json        round, provenance, per-frame pixel hashes
pixel/source/<anim>/<DIR>/fNN.png      512 px toon render, same camera/framing (exactly x4 the cell)
pixel/overrides/<anim>/<DIR>/fNN.json  hand edits: JSON list of {x,y,color,reason,author,time,base_hash,base_color}
pixel/overrides/<anim>/HISTORY.jsonl   append-only log of every change (CLI + editor)
pixel/clean/<anim>/<DIR>/fNN.png       base + overrides (px.py apply). This is the deliverable.
pixel/review/<anim>/<DIR>/fNN.png      zoom review sheets, plus strip.png
pixel/lint/<anim>_<src>.json           detector report
pixel/gifs/<anim>_<src>/               preview GIFs
pixel/feedback/<anim>.jsonl            notes added in the editor
```

## Commands
```sh
# 1. base frames (+ 512 px source renders via Blender, about 45 s for 64 frames)
.venv/bin/python tools/pixel/snapshot.py --round latest --anim idle      # or --round 6; --no-hires; --force
#    'latest' = the highest renders/model_round_N with a COMPLETE anim_<anim> set: all 8 dirs, same
#    frame count, and checks.json + sheet.png not older than the cells. A round that is being
#    re-rendered right now is skipped.
/Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup -P tools/pixel/render_hires.py -- \
    --anim idle [--dirs S,SE] [--frames 0,3] [--res 512] [--force]          # source renders only

# 2. overrides (every edit needs --reason; colours are palette names or 'clear')
.venv/bin/python tools/pixel/px.py set    --dir S --frame 3 30,41,outline 31,41,red_2 --reason "close cuff outline"
.venv/bin/python tools/pixel/px.py erase  --dir S --frame 3 44,60 --reason "1px spur on hem"
.venv/bin/python tools/pixel/px.py line   --dir S --frame 3 40,50,44,54,outline --reason "straighten sleeve edge"
.venv/bin/python tools/pixel/px.py revert --dir S --frame 3 30,41 --reason "..."     # or --all
.venv/bin/python tools/pixel/px.py copy   --dir S --frame 3 --to 4,5 --reason "same fix, held pose"
.venv/bin/python tools/pixel/px.py show   [--dir S] [--frame 3]                       # with STALE / conflict marks
.venv/bin/python tools/pixel/px.py stale                                              # exit 1 if anything is stale
.venv/bin/python tools/pixel/px.py approve --dir S --frame 3 --reason "re-checked on round 7"
.venv/bin/python tools/pixel/px.py apply  [--dir S] [--frame 3]                       # -> pixel/clean
#   (--anim defaults to idle; PX_AUTHOR=name sets --author)

# 3. review sheets: CLEAN | BASE | DIFF | SOURCE | FLAGS, plus palette legend; strip.png per dir
.venv/bin/python tools/pixel/review.py --anim idle --dir S [--frames 0,3] [--zoom 12] [--src clean|base]

# 4. detector (reports only)
.venv/bin/python tools/pixel/lint.py --anim idle [--dir S] [--src clean|base] [--frame 3]

# 5. GIFs: per dir 1x/4x, grey + grass, all8 2x4 grid at 4x, before/after
.venv/bin/python tools/pixel/gif.py --anim idle [--src clean|base] [--no-shadow]

# 6. editor
.venv/bin/python tools/pixel/server.py            # http://127.0.0.1:8778/   (--port N)
```

## Palette names (docs/palette.json, locked)
`outline` (#1a1220, also accepted as `leather_0` / `dark_0`), `skin_0..2`, `hair_0..2`, `red_0..3`, `leather_1..2`, `dark_1`, `steel_0..2`, `eye_0..1`, `pink_0..1`, `purple_0`, and `clear`.

A `#hex` value is accepted only if it is already in the palette. Anything else is rejected, so the tools can never add a colour.

## Overrides and staleness
- One entry per pixel. A later edit at the same (x, y) replaces the earlier one.
- Setting a pixel to its base colour drops the override.
- `base_hash` is the hash of the decoded RGBA of the base frame the edit was made on. `base_color` is the base pixel it replaced.
- After a re-snapshot (a new model round), `px.py stale` and `apply` warn when a frame's base hash changed.
  - **conflict**: the base pixel under an edit changed, so re-check that fix.
  - `approve` re-binds the overrides to the new base and drops the pixels the new base already produces.
- With zero overrides, `apply` copies the base file, so `clean == base` byte for byte. This was verified on all 64 idle frames.

## Editor
This is a port of the pixelart editor. It loads `pixel/base` frames and the matching `pixel/source` render, which can be shown as an underlay with **U**.

| Feature | How |
|---|---|
| Tools | pencil, erase (clear), fill, picker, revert-to-base |
| View | onion skin, lint-flag overlay (**L**), pivot cross-hair |
| Navigation | compass for direction, frame strip |
| Preview | 1-dir or 8-dir, with spec timings |

Saving needs the **reason** field filled in. The server keeps the old reason/author for unchanged pixels and stamps new or changed pixels with the current reason.

**Apply + lint** runs `px.py apply` and `lint.py --src clean`. The server writes only under `pixel/overrides`, `pixel/clean`, `pixel/lint` and `pixel/feedback`.

## Lint flags
| flag | meaning |
|---|---|
| off_palette / semi_alpha | RGB not in palette / alpha not 0 or 255 (errors) |
| orphan | no same-colour 8-neighbour. Eye glints are legit, so judge each one. |
| outline_gap | silhouette-edge pixel in a mid/light tone, i.e. not `outline`, a selective-outline dark tone (SELOUT in lint.py) or `pink_0` rim |
| notch / spur | 1 px dent (transparent with 3+ opaque 4-neighbours) / 1 px tooth (opaque with 3+ transparent 4-neighbours) |
| double | outline L-corner whose removal keeps the line 8-connected (pixel-perfect doubles) |
| jaggy | irregular run in a monotone stair on the silhouette profile (e.g. 3-1-3, 1-4-1) |
| banding | 5+ px band of one ramp tone squeezed between the outline and another tone of the same ramp |
| inner_break | 1 px gap between two end-points of an interior outline line |
| flicker | A->B->A toggle across consecutive frames while the 5x5 neighbourhood is static (loops wrap) |
| pivot | feet baseline (lowest body row, sword excluded) and feet centre per frame. Drift and offset are reported per direction. |
| colours | colours per frame |

Sword and kagi pixels (from the ID pass) are reported as `info` for thin-line checks, because the blade is a 1 px diagonal by design.

## Notes
- **Frame-count mismatch.** `anim_spec.json` idle has 6 frames at 150 ms, but the rig renders 8. `gif.py` and the editor use the spec mean (150 ms) for every frame and print a warning.
- **Source renders and the current model.** Source renders come from the current `model/character.blend`. If the blend is newer than the snapshotted round, `snapshot.py` warns and records `blend.newer_than_renders` in SNAPSHOT.json.
- **Source vs sprite differences.** The source shows the hero katana and the inverted-hull outline; the sprite shows the sprite katana. Use the source to understand intent (shapes, folds), not as a pixel-exact target.
