# r14 Gameplay timing budget (GD)

Rule: build-up goes **after** the commit point (apex hang, impact squash, follow-through) or in **skippable** holds, never between input and effect. Touch adds ~50-80 ms, so budgets are tight (Celeste, Super Mario Run, Oddmar: jump leaves the ground on the press).

## Responsive (player-triggered)

| clip | now | max total | input -> event | cancel |
|---|---|---|---|---|
| jump_sc | 840, takeoff 120 | 950 | `takeoff` <= 130 ms | from hop; airtime takeoff->`land` 430 +-30 ms (gap clearance); add drama by redistributing to peak_hold, not by extending airtime |
| throw | 520, release 270 | 650 | `throw_release` <= 300 ms | recover onward; a buffered throw cancels from follow |
| land (light) | 290, lock 120 | 350 | `land` on f0 | lock <= 120 ms, then run/jump |
| fall | 320 loop | 480 loop | - | any frame -> land |

Throw build-up: a held button loops `cock` (aim); release <= 100 ms after button-up. A tap plays straight through.

## Contextual / cinematic (longer build-up is fine)

| clip | now | max total | event constraint | cancel |
|---|---|---|---|---|
| pick_up | 700, grab 160 | 1000 | `grab` <= 350 ms (crate snaps to the carry bone) | last 2 frames -> carry_walk |
| carry_throw | 540, release 200 | 800 | `throw_release` <= 400 ms; spawn anchor = last frame with the crate drawn | recover onward |
| climb_top | 720 | 1000 | `root_px` monotonic, ends (0,-30); `step_up` >= 60% through | none (jump buffered) |
| land (heavy, P1 variant) | - | 550 | after fall > 400 ms | lock <= 300 ms; run-cancel from settle |

## Loops (foot slide)

| clip | now | allowed cycle | engine speed |
|---|---|---|---|
| walk | 800 | 700-900 | 21.5 u/s x 800/new |
| run | 560 | 480-620 | 60 u/s x 560/new; keep >= 54 u/s |
| carry_walk | 960 | 880-1040 | 15 u/s x 960/new |
| climb | 960 | <= 1100 | rise >= 22 px/s; ease via `rise_weights`, not durations |
| idle / carry_idle | 1600 / 800 | free (<= 4 s) | - |

Uneven **stance** durations break the linear treadmill: keep stance frames uniform and ease only passing/flight, or re-solve the feet. QA gate: slide <= 0.5 px. Footsteps stay on contacts; climb_top entry stays on `grip_R`/`grip_L`.

## Engine contract

1. **Input buffer 150 ms**: jump/throw pressed during a lock fires on the first cancelable frame.
2. **Move-cancel**: stick input on a `cancelable` frame goes straight to walk/run (Dead Cells, Hollow Knight).
3. **New flag `skippable: true`** on ground holds (plop, settle, lockout, ready; never airborne frames): any input collapses the remaining duration.
4. **Coyote time 80 ms.**
5. `inputLockEnd_ms` is generated from the cancel flags; the build fails on any budget violation.

## On r14_retiming_plan.md

Not yet written. Animation: check each retime against these tables. Jump anticipation stays <= 130 ms; put drama in peak_hold and skippable plop/settle, a held throw `cock`, and freely in pick_up, carry_throw, climb_top. For loops, state the new cycle_ms so we retune speed. I'll review once it's in.
