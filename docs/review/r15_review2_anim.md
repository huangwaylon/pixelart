# r15 round 2 animation re-check (Animation Director)

**Verdict: APPROVED**

**Scope:** S/SE/SW for run, walk, carry_walk, idle, jump_sc and their r14 copies, compared with the v1 release. Measured per column across the eye span.

- **Bang hem:** the skin gap between hem and lash is a steady 1 row on every interior column in every frame (v1 drifted 1-2). The run/carry_walk S strobe and the walk S double flip are gone. Only the outermost tip column moves 0-2 px, a smaller edge wobble than v1's.
- **Eyes:** one eye pattern per expression per direction, with constant ink count, relative to the lash.
- **Blinks:** idle f5 only (gap 2), same as v1, in all three directions.
- **Seams:** face-band last-to-first diff is at or below v1 and within the per-step range.
- **jump_sc:** the 1/2 gap profile in the effort frames comes from the expression and is consistent.
