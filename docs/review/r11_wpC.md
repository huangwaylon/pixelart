# r11 WP C (Carry): pick_up, carry_idle, carry_walk

## Carry prop spec (frozen, for WP D)
- **Canonical block:** `data/animations/carry_idle.json` → `props[0]`. Copy it verbatim and change only `frames`.
- **Prop:** id `crate`, bone `carry`, offset `[0, 17.8, 0]`.
- **Shape:** a flat-faced "snow-crate" box of half-extents 9.0 × 4.6 × 5.0, built from clipped cap ellipsoids.
- **Materials:** faces `prop_snow`, end panels and band `coat_trim`, rope handles `pants`.
- **Hold pose:** arms `raise 176, spread 38, elbow 10–15`. If the elbow goes past about 16, the crate touches the hair.
- **Head clearance:** about 0.5 u.

## pick_up (8 frames / 640 ms, no cancel)
| f | name | ms | intent |
|---|---|---|---|
| 1 | eye_dip | 70 | look down, dip |
| 2 | squat_reach | 90 | deep squat, knees in |
| 3 | grab | 80 | **grab**; prop appears |
| 4 | heave | 80 | crate to knees, squint |
| 5 | clean | 80 | stand, crate at chest |
| 6 | press | 70 | crate above forehead |
| 7 | lockout | 90 | joyful stretch |
| 8 | settle | 80 | weight sinks into carry_idle |

- The world crate sits **12.7 u (9.5 px) in front of the pivot**. The engine hides it on `grab`.
- `qa.max_height_delta_px` is 5 because the crate counts toward height. Body alone is ≤1 px.

## carry_idle (loop, 4 × 200 ms)
up / sink / low / rise: a 1 px bob, elbows give under the weight, ±1° sway.

## carry_walk (loop, 8 × 120 ms)
- Frames: contact, down, pass, up, then mirrored. `footstep_L` on f1, `footstep_R` on f5.
- The planted foot travels 7.2 u per step (15 u/s), so engine speed should match.
- Down frames bob about 1 px. Upright torso, no arm swing.

## QA
All three PASS: penetrations 0, seam 0.0, orphans 0, slide ≤0.25.

## Known issues
- 18 colours per frame (warning only): the snow ramp adds 4.
- Raised forearms overlap the rigid sidelocks; QA doesn't check this.
- Chibi arms can't reach above the head, so the ropes bridge the gap.
- f5 → f6 is a deliberate snap.

## Round 1 fixes
**Crate (`data/props/crate.json`, shared via `{"ref": "crate"}`)**
- Box half-extents 7.2 × 3.7 × 5.5 (14 × 7 × 11 u, a cube-ish box from every side). Body `prop_wood`, slat band `coat_trim`, snow mound `prop_snow` (radii 4.9/1.2/4.9).
- Width is 7.2, not the suggested 5.5. With 5.5 the low-frame grip pulls her arms in, and scarf_front clips the arms in the squat (QA failed).
- Final carry offset `[0, 19.2, 0]` (was 17.8, +1.5 px): crate bottom clears the hair top by ≥ 2 u.
- The plan's `(0, 3, 1.5)` can't work: the hands only reach ear height, so it would sit inside the head.
- Ropes (tag `rope`) run 2 u behind the head plane, from the end panels to the mittens.
- Body colours ≤ 15 per frame (the prop is its own layer).

**Clips:** each has one `{"ref": "crate"}` declaration.
- **pick_up** (9 frames / 700 ms)
  - Added `drive` after clean: 60 ms, raise 100, spread 24, elbow 60, pelvis_drop 1.6, squash 0.96, squint. Crate sits under the chin.
  - press squash is now 1.05.
  - Low frames place the crate with frame-level `"prop": {"offset", "rot", "hide": ["rope"]}`.
  - The current engine ignores that key: **apply `docs/review/r11_wpC_frame_prop.patch`** (11 lines in `Scene._prop_prims`).
  - `settle` == carry_idle `low`. Per `engine_notes`, continue with carry_idle index 3 (`rise`); index 2 is also seamless.
  - The world crate spot moved to 13.4 u in front of the pivot.
- **carry_walk:** elbow lag (contact 10, down 12, pass 15, up 11); down_* squash 0.98.
- **carry_idle:** poses unchanged.

**QA:** all PASS. Penetrations 0, seam 0, height delta ≤ 2, slide ≤ 0.25. pick_up was verified with the patch applied.

**Note for animator D:** carry_throw already uses `ref: crate`, so it picks up the new crate. Use the hold arms 176/38/10–15, or recheck head clearance.

## Round 2 fixes
**Crate (`data/props/crate.json`)**
- **Rope:** rerouted in two segments.
  - Each rope drops from the crate's underside (x ±6.3) to a tuck point inside the hair cap (local (±3.5, 5.0, −1), about 2 u under the hair top). From there it runs to the mitten.
  - With the depth split, the part inside the hair draws behind the head. In E/W/SE/SW/NE/NW only a 2–3 px stub shows from the crate bottom into the hair top. Nothing reaches the eye line any more.
  - In S/N the ropes appear to tuck behind the hair.
  - Rope material is now `prop_wood` (colours already in the body palette).
- **Wood:** now `pom` (mauve/oat_1/oat_2 light wood), with the `coat_trim` slat band and snow mound kept. It is clearly lighter than the dark-brown hair. The prop strip's own outline gives a dark edge on every side, including the bottom.
- **Colours:** composite (back + body + front) is at most 16 per frame in all four clips.

**Rebuilt:** pick_up, carry_idle, carry_walk, carry_throw. All QA PASS.

**Note for animator D:** on carry_throw `push` the hands move forward, so the rope runs down over the hair. Add `"prop": {"hide": ["rope"]}` to that frame.
