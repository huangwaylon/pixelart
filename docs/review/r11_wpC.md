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
