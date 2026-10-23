# r14 Animator A: jump_sc / land / fall / land_heavy (S4_hd)

These are copies. The release clips are untouched. Poses are generated from the release clips plus per-frame deltas.

## jump_sc_r14: 890/950 ms, takeoff 120/130, air 430 (400-460)
`dip 30 · coil 90 out` (squash 0.86, pelvis 3.8, tilt 22, arms -66) `· spring 40 X` (1.18) `· rise 50 · float_up 50 in · peak 80 inout · peak_hold 120 out` (z 21, a real hang) `· fall 40` (1.05) `· reach 50` (1.08) `· touchdown 40 X` (0.84) `· touch_hold 60 hold_of` (sinks to 3.8, arms and head follow through) `· hop 50 · plop 70 S · settle 70 S · ready 50 S`.
Rise spacing is z 3/12/18/22 (slow-in at the top). The fall is 21 to 11 to 4 in 90 ms.

## land_r14: 340/350, lock 100/120
Derived by frame names `["touchdown","ready"]`. The `hop cancelable:false` override is removed.

## fall_r14: loop 340/480
`flap_up 60 · flap_top 110 inout` (stretch 1.05) `· flap_down 60 · flap_low 110 inout` (0.98, knee tuck). The holds now carry a small bob. Loop seam 0.0.

## land_heavy_r14 (new, standalone): 500/550, lock 250/300
`touchdown 40 X` (0.84, pelvis 4.0) `· crumple 120 hold_of` (4.2, arms drop) `· push_up 90` (2.8, 0.92) `· hop 60` (z 1, small rebound) `· plop 90 S · settle 100 S`.

All four pass QA: 0 errors, 0 warnings, 0 chain penetrations, foot slide <= 0.45 (heavy land was 0.52 at pelvis 4.6, reduced).

| Clip | Frames / time | Dirs | Events | QA |
|---|---|---|---|---|
| jump_sc_r14 | 15 f / 890 ms | 8 | land, takeoff | PASS |
| land_r14 | 6 f / 340 ms | 8 | land | PASS |
| fall_r14 | 4 f / 340 ms loop | 8 | - | PASS |
| land_heavy_r14 | 6 f / 500 ms | 8 | land | PASS |

## Known issues
- **Engine bug:** `build_id` doesn't hash the derived source clip. land_r14 kept buildId `252a88aedffb` even after jump_sc_r14 changed. The output is re-rendered correctly, but the id is stale.
- Squash 0.80 for heavy land was not used. It is outside the smear range (0.84), so the depth comes from pelvis drop.
- I tested a spring streak (`smear.streak hand_L`). At 48x64 it read as stray dots, so I dropped it.
- The slow-mo GIFs show keys only, so in-between chain motion can't be reviewed there.
- publish.py overwrites README.md. These rows are duplicated here.
