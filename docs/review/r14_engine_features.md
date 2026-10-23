# r14 Engine features (SWE)

Everything is opt-in. Clips that don't use these keys build byte-identically (checked: S4_hd + S4_halfup_bow idle, jump_sc, throw, walk).

## Frame keys
- `hold_of: "<earlier frame>"` reuses that pose. Channels on the hold merge on top (tremble). The hold inherits `root_px`, prop placement/visibility and `smear`. The body holds still while the chains keep simulating.
- `ease: linear|in|out|inout|hold` shapes the segment to the next key. `out` = slow out of this key, `in` = slow into the next. It affects in-betweens only (chains).
- `skippable: true` is exported. It is an error on airborne frames. `loop_while_held: true` is exported.
- `smear: true` allows squash 0.84-1.18 (other keys 0.86-1.15, out of range is a warning). It is exempt from the height-delta gate and needs ms >= 30. As an object, `{streak: bone|"carry", from, layer, tail, stretch, arc}`, it also draws a streak into the prop layers (id `smear`). With `from` it goes bone to bone; without it, it trails from the previous key.
- `ms` must be a multiple of 5. Names must be unique.

## Clip keys
- `derived.frames` and `spawn_anchor_frame` accept names or indices. The sheet adds `sourceIndices` / `spawn_anchor_index`.
- `budget`: `max_total_ms`, `max_lock_ms`, `loop_ms`, `events {ev: deadline}`, `events_min_pct`, `intervals`, `root_px_end`, `root_px_monotonic`, `spawn_anchor_last_visible`, `min_rise_px_s`, `engine_speed_u_s`. A violation is a QA error, so the build exits 1 and the `--release` gate fails. The GD budgets are in every clip. **Retune `engine_speed_u_s` when a loop's cycle changes.**
- `engine_speed_u_s` turns on the treadmill check: stance feet must move speed x frame_ms between keys, within 0.5 px.

## Sim
Segments into or out of a short (< 40 ms) or smear key run 4 substeps per 5 ms step, with damping and velocity rescaled. Tune with `sim.short_frame_substeps`, `sim.short_frame_ms` or clip `sim_substeps`.

`inputLockEnd_ms` still comes from the cancel flags.
