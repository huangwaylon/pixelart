# r14 Retiming plan (Animation Director)

Checked against `r14_gameplay_timing.md` (GD). One frame = one sampled key, so a hold is a repeated pose and spacing = frame ms plus pose distance. Format: `name ms` (NEW = added frame, H = hold that repeats a pose, S = `skippable`, X = smear/impact).

## Responsive

**jump_sc** 840 -> **890** (takeoff 120, airtime 430, land lock 100)
`dip 30 · coil 90` (deeper, squash 0.90->0.86, pelvis 3.2->3.8; *bigger, not longer*) `· spring 40 X` (stretch 1.14->1.18) `· rise 50 · float_up 50 · peak 80 · peak_hold 120 · fall 40 · reach 50 · touchdown 40 X` (squash 0.84) `· touch_hold 60 NEW H · hop 50 · plop 70 S · settle 70 S · ready 50 S`
Change: the rise is quicker and the extra time goes to the apex hang (slow-in at the top, quick fall). The impact squash is now held. peak_hold is airborne, so it is NOT skippable (skipping it would cut airtime).

**land** (derived) -> **340**, frames [9,14]. Remove the `hop cancelable:false` override, or the lock becomes 150 ms. Lock is then 100 ms (touchdown + touch_hold).

**throw** 520 -> **610** (release 280)
`scoop 50 · pack 50 · cock 90 · cock_hold 60 NEW H` (counter-twist overshoot; loops while the button is held) `· step 30 X` (lunge stretch) `· release 100` (hold the extended arm; existing snow smear) `· follow 90` (overshoot past the line) `· recover 70 · ready 70 S`
Change: scoop/pack get shorter and the time moves into the cock. That makes a slow build, a 30 ms snap, then a held release.

**fall** loop 320 -> **340**
`flap_up 60 · flap_top 110 · flap_down 60 · flap_low 110`. Slower at the extremes, quick strokes between.

## Contextual (can get longer)

**pick_up** 700 -> **940** (grab 210)
`eye_dip 90 · squat_reach 120 · grab 110 H-ish` (contact hold) `· heave 140` (strain, squash 0.94) `· heave_strain 60 NEW H` (+1 px tremble) `· clean 50 · drive 40` (fast pop after the slow strain) `· press 60 · lockout 140 S` (stretch 1.05) `· settle 130` (overshoot squash 0.95). The last 2 frames are cancelable into carry_walk.

**carry_throw** 540 -> **720** (release 290)
`dip 160 · dip_hold 90 NEW H` (squash 0.94->0.90) `· push 40 X` (stretch 1.10; last frame with the crate drawn = spawn anchor) `· release 100` (arms-up hold) `· follow 130` (overshoot forward) `· recover 100 · ready 100 S`

**climb_top** 720 uniform -> **860** (step_up at 520 = 60.5%)
`hang 140` (gather) `· elbows 80 · press 170` (strain hold) `· knee_up 70 · roll_over 60` (fast) `· step_up 90 · rise 120 · stand 130` (overshoot settle).
root_px y re-keyed: 0, -5, -11, -18, -24, -28, -30, -30. Still monotonic; small steps at the ends, big steps in the middle.

## Loops: do NOT lengthen for drama

GD speed rule: stance frames stay uniform; only passing/flight frames change; contrast comes from the poses.
- **walk** 800 (no change). Uniform 100 ms. pelvis_drop on down 1.4->1.8, up stretch 1.02. Speed unchanged.
- **run** 560 -> **600**. contact/down/push 70, flight 90 (hang time). down squash 0.94, flight 1.06. Engine 56 u/s.
- **carry_walk** 960 -> **1000**, uniform 125. Heavier down (pelvis 1.25->1.6). Engine 14.4 u/s.
- **climb** 960 (no change), 120 uniform. Ease with `rise_weights` (pull1 0.45, pull2 0.35, grip/swap 0.10). grip squash 1.05 snap.
- **idle** 1600 -> **2000**: `rest 260 · inhale 260 · inhale_top 300 S · hold_shift 280 · exhale 220 · blink 70 · settle 300 · settle_b 310 S`.
- **carry_idle** 800 uniform -> **960**: `up 300 · sink 160 · low 320 · rise 180`. Holds at the top and bottom, fast between. pick_up still hands off at index 3.

## Budget check

| clip | total / max | event / limit |
|---|---|---|
| jump_sc | 890/950 | takeoff 120/130, air 430 |
| land | 340/350 | lock 100/120 |
| throw | 610/650 | release 280/300 |
| fall | 340/480 | - |
| pick_up | 940/1000 | grab 210/350 |
| carry_throw | 720/800 | release 290/400 |
| climb_top | 860/1000 | step_up 60.5% |

## Rig / engine features needed

1. **`hold_of: "<frame>"`**: reuse a pose without copying it. The chain sim keeps running, so ponytail/scarf follow-through comes free.
2. **`skippable`** (GD contract) and **`loop_while_held`** on throw `cock_hold`.
3. **`smear: true`**: allows squash 0.84-1.18 on that frame and exempts it from QA `max_height_delta_px`. Generalise `add_release_smears` (build.py) into an optional streak FX for jump spring, carry push and throw step. Minimum frame 30 ms.
4. **Per-key `ease`** (`in`/`out`/`hold` -> Hermite tangents): only shapes the chain sim and slow-mo previews. Not blocking.
5. Frame indices move: update land `derived.frames` and `prop.spawn_anchor_frame`, and remap overrides by frame name (the only HD override, carry_idle NW/00, keeps its index).
6. Events move: takeoff 120, throw_release 280, grab 210, carry release 290, step_up 520. Regenerate `inputLockEnd_ms`.
7. Re-check chain penetration on 30-40 ms smear frames. The velocity spikes there will whip the ponytail.

## Reconciled with GD

- All clips are inside budget (table above). Jump wind-up stays at 120 ms and gets deeper instead of longer.
- **Conflict 1, peak_hold skippable:** GD lists it as skippable. I say no. It is airborne, and collapsing it would push airtime below 430-30. Only plop/settle/ready/lockout/inhale_top/settle_b are skippable.
- **Conflict 2, land override:** today's `hop cancelable:false` override would make the light-land lock 150 ms against GD's 120 cap. Drop the override.
- **Heavy land (P1, <=550, lock <=300):** `touchdown 40 X` (squash 0.80) `· crumple 120 H · push_up 90 · hop 60 · plop 90 S · settle 100 S` = 500. Lock is 250 (to the end of hop); run-cancel from settle.
- **Loops:** new cycle_ms walk 800, run 600, carry_walk 1000, climb 960, fall 340, idle 2000, carry_idle 960.
