# r14 Animator B: throw, carry_throw, pick_up

Copies only: `data/animations/{throw,carry_throw,pick_up}_r14.json`. All three are QA PASS with 0 warnings and pass their budgets. Slide is at most 0.43 px, with 0 chain penetrations.

| clip | total/max | event/limit |
|---|---|---|
| throw_r14 | 610/650 | release 280/300 |
| carry_throw_r14 | 720/800 | release 290/400 |
| pick_up_r14 | 940/1000 | grab 210/350 |

**throw**: `scoop 50 · pack 50 · cock 90 · cock_hold 60 · step 30 X · release 100 · follow 90 · recover 70 · ready 70 S`.
- `cock_hold` holds `cock` (`loop_while_held`) with more twist and the arm further back.
- `step` stretches to 1.08 with a hand_R streak; the hand starts rising so it moves on an arc.
- `follow` overshoots further and sinks.
- The snowball shows on frames 0-4.

**carry_throw**: `dip 160 · dip_hold 90 · push 40 X · release 100 · follow 130 · recover 100 · ready 100 S`.
- `dip_hold` holds the dip with squash 0.90 and a squint.
- `push` stretches to 1.10 with a carry streak. The crate offset is y 17->16 so the crate stays on the hands.
- The spawn anchor `"push"` resolves to index 2, the last visible frame.

**pick_up**: `eye_dip 90 · squat_reach 120 · grab 110 · heave 140 · heave_strain 60 · clean 50 · drive 40 · press 60 · lockout 140 S · overshoot 70 · settle 60`.
- `heave_strain` holds `heave` and trembles 1 px (pelvis, spine and elbows).
- **Deviation from plan:** `settle` must stay equal to carry_idle `low` for the index-3 hand-off. So the 0.955 overshoot squash is a new `overshoot` frame, and the total is unchanged.
- The last 2 frames are cancelable.

**Review:** `00_REVIEW/r14_retime/<clip>_r14/` and `compare/<clip>_old_vs_new.gif` (S+SE, x3 slow, time-synced). The shared README is not updated.

**Issues in the release build (not fixed):**
- pick_up N, heave frames: the "split" layer draws a crate band over the legs.
- E/NE overhead crate: it floats about 1 px above the hands at lockout.
