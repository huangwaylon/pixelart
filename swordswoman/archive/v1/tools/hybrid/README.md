# tools/hybrid: shared pipeline for the hybrid sprites

The visible art is Gemini illustrations or Claude hand pixels. The 3D rig is only a hidden guide.
These tools turn hi-res art into palette-locked 128-cell sprites, let Claude artists draw exact
pixels, measure consistency and motion across the whole set, and build sheets and GIFs so the set
can be reviewed as a whole.

Run everything from the project root with `.venv/bin/python`. The cell is 128x128. The pivot (the
root between the feet) is (64, 104), and the lowest body row sits on y = 104 or a pixel or two
below it. The palette is locked to `docs/palette.json`: every tool rejects colours outside it.

End-to-end test (writes only under `hybrid/_pipeline_test/`): `tools/hybrid/selftest.sh`

## Files
| file | what |
|---|---|
| `hylib.py` | Shared library: palette, ramps and base classes, Lab classification and quantization, the `Guide` loader, sprite feature detection, naming and sequences, timing lookup |
| `pixelize.py` | hi-res image to sprite (+ `--regress`) |
| `pixgrid.py` | `.pix` text grids. This is a port of `~/Documents/other/pixelart/pipeline/pixgrid.py` (the original was only read, never edited), with palette names and a standard legend |
| `draw.py` | Exact-pixel drawing ops for Claude artists: lines, arcs, fills, copies, smears, motion lines |
| `metrics.py` | Silhouette IoU, feature drift, colour/ramp drift, flicker/boil, palette/orphans, motion |
| `sheets.py` | Contact sheet (1x / 4x / hi-res / guide), 8-direction grid, whole-set sheet |
| `gifs.py` | Turntable, 2x4 grid, per-direction animations (real timing + holds), slow-motion, labelled compare |
| `make_fixture.py` | Builds a STANDARD TEST SET fixture from round-9 cells and masks. Test data only, not art |
| `selftest.sh` | Runs everything above |

## Naming (STANDARD TEST SET)
`turn_<DIR>.png` (S SE E NE N NW W SW), `walk_SE_k{0..3}.png`, `slash_SE_k{0..3}.png`,
`jump_E_{crouch,apex,land}.png`. In general a name is `<anim>_<DIR>[_<key>].png`, where the anim can
contain `_` (`overhead_slash_SE_k2`) and the key is `kN`, `fNN` or a word such as apex.

Sequences are grouped by (anim, DIR) and sorted by key (k0 < k1 ...; crouch < apex < land).
Files that sit next to a sprite are skipped as auxiliary: `<stem>_4x.png`, `_hires.png`, `_dbg.png`,
`_meta.json`, `_src.png`, `_mat.png`, `_guide.png`, `_cmp.png`. The hi-res source of a sprite is
`<stem>_hires.png` (or `_src.png`).

## Guides
A guide is a file prefix `P`. Any of these files may exist:
- `P_mask.png`: silhouette.
- `P_id.png`: object-ID pass, with R = id x 10. The groups come from `P_groups.json`, else from
  `<dir>/id_groups.json`, else from `pixel/base/idle/_id/id_groups.json`.
- `P_body.png` + `P_sword.png`: the round-9 `_masks` layout, i.e.
  `renders/model_round_9/_masks/anim_<anim>_<DIR>_f<N>_64`.
- `P.png`: a colour sprite.
  - Its alpha gives the mask.
  - Its palette tones give the material prior.
  - Its steel components give the sword.
  - Its features (eyes, bow, guard) are the drift reference.
- `P_joints.json`: `{"joints": {name: [x, y]}, "space": "cell"|"px", "size": [W, H]}`.

Images are 128 px, or k x 128 square (512 = 4x). Missing joints are derived from the masks.
`metrics` and `sheets` look up guides in this order: `--guide-map {stem: prefix}`, then
`<guide-dir>/<stem>`, then `<sprite dir>/guide/<stem>`.

## 1. pixelize.py
```sh
.venv/bin/python tools/hybrid/pixelize.py IN_hires.png --guide <prefix|none> --out OUT.png [--height 60]
   [--pick K]                  # multi-figure Gemini sheet: keep figure K (0 = leftmost)
   [--crop x0,y0,x1,y1] [--bg auto|alpha|flood|legacy] [--tol 11]
   [--fit iou|joints|none] [--src-joints J.json]
   [--down box|mode] [--quant material|ramp|nearest] [--penalty 6] [--no-guide-mat]
   [--outline auto|inner|outer|keep] [--no-clean] [--baseline 104] [--pivot-x 64]
.venv/bin/python tools/hybrid/pixelize.py --regress
```
Steps:
1. **Background removal.**
   - If the input has alpha, alpha is used.
   - Otherwise the background is flood-filled from the median border colour (Lab tolerance).
   - Enclosed background holes (between the legs, for example) are removed.
   - So are the flat grey ground shadow under the feet (the silver blade survives) and small specks.
2. **Alignment.**
   - The body height (sword excluded: steel-classified blade components are dropped) is scaled to
     the guide's body height, or to `--height` when there is no guide.
   - The bottom row goes onto the guide's bottom row, or onto `--baseline`.
   - x: with a guide, the body centroid matches the guide's. With no guide, the feet centre goes to `--pivot-x`.
   - `--fit iou` (the default) then searches scale x0.94-1.06 and dx +-4 / dy +-1 for the best IoU.
   - `--fit joints` uses a least-squares scale + shift on named joints shared with the guide, then refines by IoU.
3. **BOX/area downsample** of the premultiplied crop. Alpha is binarized at 50 % coverage.
   `--down mode` quantizes per pixel at hi-res first, then takes the most-covered tone per cell.
4. **Per-material quantization.**
   - Each pixel is classified to the ramp whose polyline (dark to light, in Lab, chroma x0.8) is
     closest. Ambiguous pixels use 3x3-smoothed costs.
   - Guide materials add a soft `--penalty` (Lab) for ramps the guide does not allow there. It is
     soft because Gemini shapes differ from the 3D guide; 6 works best, 14 broke the faces.
   - Steel is kept only on blade-like (elongated, neutral) components and tiny buckles. Other greys
     go to their next class: blue goes to eye, warm goes to pink.
   - The tone is then the nearest tone inside the ramp, value-weighted. Outline loses ties to the
     ramp's own darkest tone.
   - `--quant nearest` is the old global nearest-colour method, kept only for comparison.
5. **Clean 1 px exterior outline with sel-out** (cleanup guide R9).
   - The bottom, the right and the ground contact use `outline`.
   - The lit top/left uses the material's dark tone: red_1, skin_0, hair_0, pink_0; leather and dark use outline.
   - Steel is left untouched (R20).
   - Parts 1-2 px thin keep their colour. With `auto`, the outline is added outside them.
6. **Safe auto-clean.**
   - Orphans are merged into the neighbouring tone. Glint, mouth, blush, buckle, lace, eye and sword pixels are kept.
   - 1 px notches and holes are filled. 1 px channels, such as the gap between the legs, are left.
   - 1 px hanging spurs are removed (not on the ground row).
   - Doubled outline bumps are removed.
7. **Outputs:**
   - `OUT.png`
   - `OUT_4x.png`
   - `OUT_hires.png`: the aligned hi-res at 4x the cell, 512 px.
   - `OUT_dbg.png`: hi-res | sprite | ramp classes | guide outline in cyan.
   - `OUT_meta.json`: scale, offset, IoU, clean counts, height.

**Regression (passes):** `--regress` rebuilds `docs/palette_v1_vs_v2_terrain.png` from
`concept/chibi_iso_v5.png`. It uses the design-bible snippet path: legacy background removal, crop,
BOX to 56 px, then global nearest colour, with the v2 warm-pixel dark[1] block. The rebuild matches
**pixel-exactly (0 of 514,750 px differ)** and is written to
`hybrid/_pipeline_test/regress_terrain_rebuild.png`. The same run writes
`regress_terrain_new_vs_legacy.png`, which shows the legacy v2 strip next to the new pipeline (flood
background, per-material ramps, sel-out, clean) and the `mode` variant on the same three terrains.

Reference IoUs (selftest):
- Round-9 iso renders against their own 64 px cells: 0.87-0.91. The outline ring and the
  re-quantization explain the gap to 1.0.
- Gemini `dir_SE_a` (middle figure) against the 3D SE guide: 0.67. Here the shapes really are
  different, which is expected.

## 2. pixgrid.py (text grids) and draw.py (exact pixels)
Standard legend (always loaded; lower case = darker):
```
. transparent   K outline
m skin_0  s skin_1  S skin_2      h hair_0  H hair_1  J hair_2
v red_0   r red_1   R red_2  C red_3     l leather_1  L leather_2   d dark_1
t steel_0 T steel_1 w steel_2     e eye_0  E eye_1     p pink_0  P pink_1   u purple_0
```
A `legend:` block can add chars mapped to palette names, aliases or in-palette `#hex`. Anything
else is rejected; `--free` allows it for exploration only. `extends:` accepts a `.pix` or a `.png`,
so you can patch over a pixelized sprite. `patch: x y` overlays a block, and `_` keeps the pixel
underneath.
```sh
.venv/bin/python tools/hybrid/pixgrid.py fromimg sprite.png --out sprite.pix [--crop x0,y0,x1,y1] [--snap]
.venv/bin/python tools/hybrid/pixgrid.py render a.pix --out DIR --zoom 8 --grid      # 1x + zoomed preview, stats
.venv/bin/python tools/hybrid/pixgrid.py topng a.pix --out a.png [--cell [--at X Y]]
.venv/bin/python tools/hybrid/pixgrid.py sheet a.pix b.png ... --out sheet.png
.venv/bin/python tools/hybrid/pixgrid.py stats a.pix|a.png       # colours, off_palette, semi_alpha, orphans
.venv/bin/python tools/hybrid/pixgrid.py diff a.pix b.png        # changed pixels with palette names
.venv/bin/python tools/hybrid/pixgrid.py legend
```
`draw.py` applies ops in order to a PNG or `.pix` (or to `new --new 128x128`) and writes PNG or
`.pix`. Ops come as positional strings or from `--ops FILE`. `--preview 8` also writes a zoomed
image with a grid. Colours are legend chars, palette names or `clear`.
```sh
.venv/bin/python tools/hybrid/draw.py in.png --out out.png --preview 8 \
  "line 10,10 20,15 K"  "poly 1,1 5,3 9,4 R"  "curve 2,2 16,10 30,2 p" \
  "arc 64,80 14 180 270 K"          # midpoint ellipse arc (rx[,ry]), 0 deg = right, 90 = down; prints run lengths
  "rect 1,1 5,5 l fill"  "fill 3,3 L [8]"  "cluster 5,50 C XX/XXX/.X"  "stamp 5,60 KwK/_K_" \
  "replace x0,y0 x1,y1 r R"  "erase x0,y0 x1,y1 [C]"  "copy x0,y0 x1,y1 tx,ty [src=f.png] [opaque]" \
  "shift x0,y0 x1,y1 dx,dy [only=R,r]"  "mirror x0,y0 x1,y1 h|v [to=tx,ty]" \
  "smear 66,80 30,16 190 345 6 tones=w,P,p taper=lead"   # blade-arc crescent, thick at the lead end
  "streak 20,118 50,114 4 tones=w,p"                     # straight tapered run/dash/limb smear
  "echo 50,60 70,100 -12,0 2 tone=p"                     # afterimage / multiple-limb copies, behind
  "speed 104,60 -1,0 3 8 3 p"                            # 3 motion lines, length 8, gap 3, behind
  "outline K"
```
- Arcs use the midpoint ellipse algorithm, then the pixel-perfect pass (L-corners removed), so run
  lengths come out monotone (R17). The tool prints them, e.g. `arc runs [4, 2, 2, 1, 1, 2, 2, 4]`.
- Smears, streaks, echoes and motion lines paint **behind** the character (transparent pixels only)
  unless you add `over`.
- Smear tones default to the palette's `roles.smear_arc`: steel_2 core, pink_1, then pink_0 outer edge.
- `grow=out|in|mid` sets which side of the arc the band grows on.
- `taper=lead|tail|both|none` sets the thickness profile along the arc.

## 3. metrics.py
```sh
.venv/bin/python tools/hybrid/metrics.py SET_DIR_OR_FILES... [--guide-dir G] [--guide-map m.json] --json out.json
```
- **Per sprite:**
  - Palette: off_palette, semi_alpha, colours, orphans (minus the whitelist and the sword), plus
    the `tools/pixel/lint.py` counts: outline_gap, notch, spur, double, jaggy, banding.
  - Geometry: height, body_height, baseline and feet_cx offsets from the pivot.
  - Guide: IoU and IoU_body, and drift (dx, dy, d) of eyes / eye_row / bow / guard / sword_tip
    against the guide's features or joints.
  - Normalized eye_row_rel and bow_rel.
- **Set level:**
  - Colour drift: the L1 distance of each sprite's tone mix per ramp from the set median, reported
    with the worst sprite; plus ramp area shares.
  - Direction spread over the turn set: height, eye row, bow and baseline.
- **Per sequence:**
  - flicker (A->B->A toggles with a static 5x5 neighbourhood).
  - boil: px that change inside guide-static id regions.
  - **Motion:**
    - Body h/w ratio per frame against the rest pose (`turn_<DIR>`), and squash / stretch extremes.
    - Head and bow displacement, overlap (bow movement relative to the body) and lag (frames, by
      cyclic cross-correlation).
    - Sword-tip path length, smoothness, and circle-fit (arc) RMS.
    - smear px per frame (smear tones outside the guide silhouette).
  - Flags:
    - `stiff`: idle/walk head moves at most 1 px, which is the rejected "1 px bob".
    - `no_smear`: slash k1 has fewer than 15 smear px.
    - `weak squash/stretch`: the jump height range is under 8 %.

Caveats:
- Smear pixels count toward the body width (in the selftest the smear frame reads w_ratio 2.0).
- Smears have no outline, so they show up as `outline_gap` lint. Both are expected.
- Without guides, eye/bow positions come from colour alone (eye ramp; red in the head zone above the eyes).

## 4. sheets.py and gifs.py
```sh
.venv/bin/python tools/hybrid/sheets.py contact SET... --out contact.png [--guide-dir G] [--cols 4]   # 1x | 4x | hi-res | guide
.venv/bin/python tools/hybrid/sheets.py dirs    SET... --out dirs8.png [--bg grass]                   # 2x4 at 4x + 1x row
.venv/bin/python tools/hybrid/sheets.py set     SET... --out set.png --zoom 3                         # whole set, one row per sequence

.venv/bin/python tools/hybrid/gifs.py all SET... --out-dir D [--jump-z] [--slow 4] [--no-shadow]
.venv/bin/python tools/hybrid/gifs.py turntable|grid|anim SET... --out-dir D [--only slash_SE] [--ms 220,50,160,240]
.venv/bin/python tools/hybrid/gifs.py compare SET_A SET_B ... --labels A,B --out-dir D [--zoom 3]
```
- `all` writes:
  - `turntable_{1x,4x}_{grey,grass}.gif` (S SE E NE N NW W SW)
  - `dirs8_4x_{grey,grass}.gif/.png`, and `<anim>_dirs8_*` once an anim exists in all 8 directions
  - `<anim>_<DIR>_{1x,4x}_{grey,grass}.gif`
  - `<anim>_<DIR>_slow_4x_grey.gif`: x4 slower, with the key and ms stamped on each frame
- `compare` writes `compare_<seq>_3x.gif`: the same names across several sets, side by side, labelled.
- Every GIF of a set uses one fixed crop, so the pivot never moves. A 2:1 ground shadow (20x10,
  #1a1220 at 35 %) sits under the pivot.
- `--jump-z` lifts jump keys by the anim_spec `engine_z_offset_px` and scales the shadow, as the
  engine will. Use it only for root-locked sprites.
- **Timing (holds):** looked up in this order (`hylib.timing_for`):
  1. `hybrid/ANIM_DIRECTION.md`: a fenced json block `{"timing": {"slash_SE": [..], "walk": [..]}}`,
     or lines such as `timing slash_SE: 220,50,160,240`.
  2. `docs/anim_spec.json`, if the frame count matches.
  3. The key-pose defaults: walk 140/110/140/110; slash 220/50/160/240 (anticipation hold, smear,
     hit-stop, follow-through hold); jump 160/220/200.
  4. The spec mean.
- `--ms` overrides all of these.

## Known limits
- With no guide (`--guide none`), the corset (leather_1) and dark hair (hair_0) are almost the same
  value, so the classifier picks hair for the corset. Use a guide: an id pass, or a palette-coloured
  guide sprite, which gives the material prior.
- The pixelized result is a base for Claude paint-over, not a finished sprite. Faces, the hook
  guard, the 2 px blade, ribbons and hems still need hand work (`pixgrid` / `draw`).

## 5. FX kit (S7, round 3): `tools/hybrid/fx/kit.py` + `acting.py`
One palette-locked smear / FX language for every action and direction. S3 (run, dash) and S5 (slash, jump, run,
dash) call it instead of hand-rolling FX. The old `fx/smear.py` (r2) is untouched for old builds.
Grids are the standard char legend (`kit.to_grid(rgba)` / `kit.to_rgba(g)`); every call paints into `g` and returns
the painted `{(x, y): tone}`. Everything is hard-edged, outline-free, no dither, no semi-alpha, never paints the
`guard` (face stamp, `kit.head_guard(owner)`) or the `cut` mask, and de-clusters its output (no FX pixel without a
same-tone 8-neighbour). When an FX paints OVER the body, `heal()` re-merges body slivers it orphaned.
Colour roles: smears = steel_2 rim + pink_0 body (0 px of pink_1, the ribbon tone); dust = steel ramp; limb
multiples = the limb's own material, flattened (red: coral near copy, red_2 fading copy).
```python
import kit as K, acting as A          # sys.path += tools/hybrid/fx
K.crescent(g, (cx, cy), r_or_(rx, ry), a0_tail, a1_lead, lead_px=6, tail_px=1, rim_px=2, echo=True,
           cut=hand_mask, guard=K.head_guard(owner), front=lambda x, y: y >= 84, front_rows=2)  # moon profile
K.sliver(g, c, r, a0, a1, keep=0.35, thick=2)            # impact-frame remnant;  K.wisps(...) follow-through
K.limb_multiples(g, src, mask, [(-5, -1), (-10, -4)], n=2, mode='multiples' | 'stretch')
K.speed_bands(g, (-1, 0), n=3, lengths=(12, 9, 14), body=mask)          # rimmed, tapered, auto-rooted
K.afterimage(g, sil, offsets=((-8, -2), (-17, -4)), far_mask=head_mask, travel=(1, 0))  # contour multiples
K.impact_star(g, (x, y), stage=0 | 1 | 2, star='plus' | 'x', rot=cut_dir_deg, skip=((140, 250),))
K.dust(g, A.feet_points(g), stage=0 | 1 | 2)                             # foot-attached puffs + grit
K.streaks(g, [(x, y_sole)], vector=(0, 1) | (-1, 0), n=3)                # under-foot rise / ground streaks
A.HEAD_ACT['slash'][k], A.head_for('jump', 'apex', body)                 # head acting offsets (rigid head)
A.lag(driver_per_key, overshoot=2, holds=(hitstop_key,))                 # bow / bun: 1-key lag, overshoot, settle
A.ribbon(roots, rest_dir, travel, rest_shape=cel_chain, holds=(...))     # ribbon chains for h3 ribbonN / ribbonF
```
Boards: `.venv/bin/python tools/hybrid/fx/boards.py` -> `hybrid/S7_fxkit/r3/kit/<fx>_6x.png` (slate / grass),
`<fx>_1x.png`, `kit_board_6x.png`, `kit_strip_1x.png`. Unit test (must PASS): `.venv/bin/python tools/hybrid/fx/test_kit.py`.
Standard-set demo build: `tools/hybrid/s7/build.py` (bodies: S3 r2 polished turns/walk, S5 r2 acted keys re-rendered
FX-free through h3; all FX from the kit).
