# r11: Action set plan (S4_halfup_bow)

Character: S4_halfup_bow, 48x64 cells, pivot (24,57), 8 directions. Clips follow the `jump_sc.json` conventions: durations in multiples of 10 ms, events fire on frame entry, sprites stay in place and the engine moves her.

## Discussion

**Director:** The core loop is run, grab, throw, jump, climb, so we ship that now and emotes wait. Most of the time on screen is idle and run, so those two need the most polish.

**Animator:** The risk is loops: the hair and bow have to match across the loop seam. I'll carry items overhead and slightly forward so hands stay off the face in E/W (the r9 rule). I can cut land from jump_sc f10-f14 without authoring anything new.

**Engineer:** Engine work needed:
- a `loop` flag, with secondary motion pre-rolled for 2 cycles and sampled on the 3rd, plus a seam QA gate
- props as prims on bones, visible or hidden per frame
- a prop strip export
- events per frame
- hand pixel anchors per direction and frame, for spawning projectiles
- `root_px` per frame
- derived clips (frame ranges taken from another clip)

## P0 set

| file | trigger | loop | frames/ms | dirs | key poses | events | cancel |
|---|---|---|---|---|---|---|---|
| idle | no input | loop | 8/1600 | 8 | breathe in/hold/out, blink f6 | - | any |
| walk | stick <50% | loop | 8/800 | 8 | contact, down, pass, up x2 | footstep_L f1, footstep_R f5 | any |
| run | stick >=50% | loop | 8/560 | 8 | contact, down, push, flight x2; lean 8, 1-2 px bob | footstep_L f1, footstep_R f5 | any |
| fall | falling >200 ms | loop | 4/320 | 8 | arms out flutter, knees tucked | - | on land |
| land | contact after fall | one-shot | 5/290 (jump_sc f10-14) | 8 | touchdown, hop, plop, settle, ready | land f1 | f3+ |
| pick_up | tap item in range | one-shot | 9/700 (final) | 8 | squat, reach, grab, lift, press overhead | grab f3 | none |
| carry_idle | holding, no input | loop | 4/800 | 8 | arms up, weight bob | - | any |
| carry_walk | holding, moving | loop | 8/960 | 8 | short stride, upright, no arm swing | footstep_L f1, footstep_R f5 | any |
| throw | throw, empty hands | one-shot | 8/520 | 8 | scoop, cock, step, release, follow-through, recover | prop_show f1, throw_release f5 | f7+ |
| carry_throw | throw while carrying | one-shot | 6/540 (final; release f3, spawn at push anchor) | 8 | dip, push up-forward, release, recover | throw_release f3 | f5+ |
| climb | touch climbable face | loop | 8/960 | N, NE, NW | reach R, pull, reach L, pull | grip_R f1, grip_L f5 | drop any |
| climb_top | top of climbable face | one-shot | 8/720 | N, NE, NW | elbows on ledge, knee up, roll over, stand | step_up f6 | none |

All files are `data/animations/<name>.json`. That is 11 clips; land is derived, so 10 need authoring.

**Directions.** Climbable surfaces are iso walls (NE/NW) or ladders (N), so she is always seen from behind.

**Root motion.**
- climb: in place, with `cycle_rise_px: 24` that the engine spreads across the cycle.
- climb_top: authored `root_px`, ending at (0,-30); the engine snaps her to the ledge tile on the last frame.
- fall and land: the engine owns z_px.

**Props.**
- Snowball: on `hand_R`, offset (0,-1.6,0.7).
- Crate/rock: on a virtual `carry` bone at the midpoint of the two hands, plus (0,3,1.5).
- At `throw_release` the engine hides the held prop and spawns the projectile at the anchor: `anchors.hand_R[dir][frame]` for throw, `anchors.carry` for carry_throw.

## P1 (next)

hurt (4/360), knockback (6/600, root_px), slide on ice (loop), push/pull crate (4 dirs), carry_jump, emote_wave, emote_cheer, idle_cold, ledge_hang.

## Sheet layout

- One PNG per clip: `<clip>_sheet.png`, rows = directions, cols = frames, no padding.
- Strips on the same grid: `_shadow`, `_fx_back`, `_fx_front`, `_prop`.
- The JSON extends `jump_sc_sheet.json`:

```
"loop": true, "inputLockEnd_ms": 0, "cycle_rise_px": 24,
"derivedFrom": {"clip": "jump_sc", "frames": [9, 13]},
"frames": [{"index", "name", "duration_ms", "events", "cancelable", "z_px",
            "root_px": [0, 0],
            "prop": {"id": "snowball", "bone": "hand_R", "visible": true, "layer": "front"}}],
"anchors": {"hand_L": [dir][frame][x, y], "hand_R": ..., "carry": ...}
```

The prop's `layer` is `back` when the holding hand is behind her torso, otherwise `front`.

## Work packages

| WP | clips | notes |
|---|---|---|
| A: Locomotion | idle, walk, run | 3 loops; run is the hardest |
| B: Vertical | climb, climb_top | 3 directions, but root_px and climb QA |
| C: Carry | pick_up, carry_idle, carry_walk | owns the carry bone spec (freeze on day 1) |
| D: Throw/Air | throw, carry_throw, fall, land cut | uses projectile anchors and the carry spec |

Order: the engine features ship first (loop pre-roll, props, anchors, events). WP A and B can start authoring right away.

## Acceptance

r9 gates, plus three new ones:
- loop seam ≤1 px for body, hair and bow
- props never clip the head
- every release frame has an anchor

Review output goes to `00_REVIEW/r11_<clip>/`.
