# r12 S4_hd round 2 + r13: Animation Director re-review

**Verdict: FIXES** (round-1 fixes pass; r13 bow and sway need one more pass)

Method: all 13 clips compared with S4_halfup_bow at 5-14x nearest. I measured one-frame blips (total, silhouette, hair, teal) and loop seams.

## Round-1 fixes
1. **idle NE waist strobe: PASS.** The brown waist run is gone in NE and NW. NE hair blips are 13 vs 24 legacy.
2. **Idle crown flicker: PASS.** Hair blips HD vs legacy: S 18/13, N 23/45, NE 13/24.
3. **Bow vs raised mitten: PASS.** carry_idle, pick_up 6-8 and carry_throw 0 all keep a 1 px dark gap.
4. **throw N/NE f4: PASS.** The NE mitten is clear. N shows the sleeve, as legacy does.

Total and silhouette flicker are at or below legacy in 11/13 clips. Seams are equal or lower, except walk NE (164 vs 124).

## r13 checks
- **Sway:** the ponytail sways counter to the hips with about 1 frame of lag. Phase and follow-through are good, with no penetration and clean seams. Measured centroid amplitude: walk N +/-1.15 px, run +/-1.5 px (legacy +/-0.2). At 1x the walk sway still reads as barely there.
- **Bow:** it bounces with overlap and settles on land f3-4.

## Fixes
1. **Bow volume:** the bow uses 0 px of #6ACBB6 in any clip, so it is still a 2-tone, flat slab in the back views. Add a 1-2 px #6ACBB6 highlight on the top of each loop, and keep the dark knot. This is the user's "less flat" request.
2. **jump_sc S f1-2:** the bow drops out. Teal head pixels go 29 -> 0 -> 0 -> 9 (legacy 17/10/11/10). The loops sink behind the crown. Clamp the lag so at least 2 px of each ear stays above the crown in S/SE/SW.
3. **Idle bow jitter:** teal blips are S 51/36, SE 41/22 and W 47/29. The W loop changes shape every frame. Extend `temporal_hold` to the bow loops in idle and carry_idle, or zero the spring in idle.
4. **Walk sway amplitude:** raise the walk force about 1.5x so the ponytail tip reaches +/-2 px in N/S, with a 1-frame hold at each extreme. Keep run as it is.
5. **New skin pops in NW:** a #D07C74 sliver appears at the hair edge in carry_idle f0 (6 px, which strobes in a 4-frame loop), throw f4 (3 px) and climb f7 (5 px). Legacy has 0 in these frames. The new jaw or cheek pokes through, so tuck it behind the curtain.
6. **Carry-over:** Anim5, the back-view ponytail merging with the curtain, is still open.
