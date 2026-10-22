# r12 S4_hd round 3: Animation Director final re-review

**Verdict: APPROVED** (release candidate `releases/S4_hd_actions_v1/`)

Method: 13 clips vs legacy at 5-7x, with the round-2 blip and seam metrics.

## Fixes 1-6
1. **Bow volume: PASS.** The teal_2 highlight and the dark knot read in every view, so the bow is no longer a flat slab.
2. **jump_sc S f1-2: PASS.** Both ears stay above the crown in the crouch for S, SE and SW, and the bow never drops out.
3. **Idle bow jitter: PASS.** Teal blips in idle are 51 vs 172 legacy, and 163 vs 330 in carry_idle.
4. **Walk sway: PASS.** The lower-ponytail centroid in walk N moves +/-0.73 px (legacy 0.26), with visible holds at f2-3 and f6-7. Run is unchanged at 1.08.
5. **NW skin: PASS.** #D07C74 is 0 px in carry_idle, throw and climb NW.
6. **Anim5: PASS.** The ponytail has its own plum line.

## Judgement calls
- **Idle without springs:** it still feels alive. Breathing, the blink and the scarf carry it, and a still bow at rest is correct.
- **Walk NE seam (154 vs 124): not blocking.** It is below the clip's own mean step diff of 167 px, so it does not pop.

## Non-blocking notes
- Total blips are within 10% of legacy (lower in 8/13). Teal blips in pick_up (+25%) and jump_sc (+15%) come from the third bow tone during spring motion; they read as motion.
- E/SE flat ponytail tip and climb NW strays: backlog.
