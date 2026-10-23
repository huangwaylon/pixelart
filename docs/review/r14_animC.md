# r14 Animator C: climb_top, climb, loops

Copies: `data/animations/<clip>_r14.json`. All clips pass QA and their budgets. Review: `00_REVIEW/r14_retime/<clip>_r14/`, `compare/<clip>_old_vs_new.gif`.

| clip | ms | notes |
|---|---|---|
| climb_top | 860: hang 140, elbows 80, press 110, **press_strain 60** (hold_of, tremble), knee_up 70, roll_over 60, step_up 90, rise 120, stand 130 | step_up at 520 ms (60.5%). root_px monotonic to -30. Hang stretched to 1.06, rise overshoot squash 0.95 |
| climb | 960 uniform | rise_weights .10/.45/.35/.10, grip stretch 1.05, deeper pull1. 25 px/s |
| run | 600 (flight 90) | down 0.94, flight 1.06. **56 u/s** |
| walk | 800 uniform | down drop 1.8, up 1.02. Ponytail sway kept |
| carry_walk | 1000 (125 each) | down drop 1.6. **14.4 u/s** |
| idle | **2100** (plan said 2000) | at 2000 ms the scarf loop seam is 0.89 px; at 2100 ms it is 0.09 px |
| carry_idle | 960: 300/160/320/180 | low sags more. The handoff frame (index 3) is unchanged |

The legs on the deeper keys were re-solved so the ankles keep their r13 paths. Treadmill slide stays at about 0.01 px. Ease only affects the chains.

## Engine issues
1. Chain `sway` and sdf `by_clip` look up `anim["name"]`. A copy named `walk_r14` loses the ponytail sway (±2.2 to ±0.25 px). My copies keep the base name. The other `_r14` copies don't, so check them.
2. `temporal_hold` and overrides look up the CLI clip name. I built the previews with `/tmp/animc/b.py`, which strips `_r14`.
3. The early `BUDGET` print ignores the `root_px` that hold_of frames inherit, so it reports a false "not monotonic".
4. Run overrides W/01 and W/05 are stale on the new poses and leave stray pixels. Without them the tips are clean, so retire them.
