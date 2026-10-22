# r11 Review 3: Game Director

I updated `/tmp/gd_r11/check_r11.py` for the depth-split schema and re-ran it on the current builds. Output: `/tmp/gd_r11/report_r3.txt`. The script now checks:
- `layers.propBack` and `layers.propFront` are on the body grid
- each frame's `layer[dir]` agrees with the pixels: `front` means the back strip is empty, `back` means the front strip is empty, `split` means at least one strip has pixels, and `null` means both are empty
- no pixel is in both strips
- the held prop disappears from the release frame on
- the spawn anchor exists in every direction at `spawn_anchor_frame`

## Script results

**All 13 clips pass with 0 failures.** The warnings:

- **propFront over the head:** the crate's front part still covers the hair top by about 33 px (55 px on pick_up `drive`, the frame where the crate goes up under the chin). Round 2 was about 48 px everywhere. This is the crate resting on the head, which is expected.
- **walk to run:** the ground contact row shifts by 2 px. This is the new crouched lean (run is 2-3 px shorter), and it's fine.
- **Squash and anticipation pops:** fall to land, idle to throw, and carry_idle to carry_throw. All intended.
- **`smear`:** throw and carry_throw `prop.ids` contain `smear`, which isn't declared in `props[]` or `data/props/`.

## Round-2 items

| item | status |
|---|---|
| Exit pop into idle | FIXED. land, jump_sc, throw and carry_throw `ready` frames are within 0-1 px of idle; carry and pick_up are within 0-1 px |
| Crate reads as part of the hair | FIXED. The lighter tan wood separates clearly from the hair at 4x in every direction |
| carry_throw prop visible on the release frame | FIXED. Release is on f3, the crate is gone from f3, and it spawns at `anchors.carry[*][1]` (`push`) |
| run: lean, stride, arms | FIXED. The forward crouch shows, the legs split clearly on flight frames in E/SE/W, and the run no longer reads as a walk |

## New issues

1. **Undeclared `smear`** (non-blocking, data only). Add `data/props/smear.json`, or list it in `props[]` with `fx: true`, so the engine can look it up by `ids` without a special case.

## Verdicts

| clip | verdict |
|---|---|
| idle | APPROVE |
| walk | APPROVE |
| run | APPROVE |
| jump_sc | APPROVE |
| fall | APPROVE |
| land | APPROVE |
| climb | APPROVE |
| climb_top | APPROVE |
| pick_up | APPROVE |
| carry_idle | APPROVE |
| carry_walk | APPROVE |
| throw | APPROVE (declare `smear` as a follow-up) |
| carry_throw | APPROVE (declare `smear` as a follow-up) |

The S4 P0 action set is approved to ship. Also update the plan table for pick_up (9 frames / 700 ms) and carry_throw (540 ms).
