# r9 Designer C: S5_side_braid, S6_hood_down_long

Both extend S0 (cw_oatmeal). QA PASS on jump_v2 and jump_sc, `chain_penetrations` 0.

## S5_side_braid (8 builds)
**Intent:** a cosy, asymmetric look: one thick braid over the character's RIGHT shoulder (-x), a teal cat-ear beanie, and a red ribbon tie at the top and tip of the braid.
**Key params:** `hair: side_pony` with the `pony` chain re-rooted on the **chest** bone (`anchor [-4.8,8.6,1.2]`, `rest_dir [0.08,-1,0.9]`). It has 8 segs x 2.2 with alternating widths 4.0/2.4 (braid bumps), `stiffness 240`, `damping 0.2` and `max_swing 30`. Tip and `tie` use ribbon `crn_1/red_1/red_2`. Added `hair_back` and `hair_sweep` prims so the hair gathers toward the braid side from behind. `beanie_cuff` removed.
**Strengths:** reads clearly as a side braid in SE/E/W/SW. The braid stays on the right side in all 8 views, and the right-shoulder bump survives in the N silhouette. The braid balances the scarf knot on the left. The red tie is a small, effective accent.
**Weaknesses:** in N/S the long hair reads only as a shoulder bump, not a long mass. At 48x64 the braid texture barely shows. It sticks forward slightly in E/W.

## S6_hood_down_long (7 builds)
**Intent:** a soft winter princess. Waist-length hair over a teal fur capelet (the hood is down) and cream earmuffs. No scarf.
**Key params:** a ring of 12 `fur_k` prims on the neck bone (`material hat` = teal, `group torso` so hair collides with it), tilted down at the front so the chin stays clear. Also a `hood_down` lump on the back of the chest, a cream `clasp`, and `pom` remapped to `oat_1/oat_2/snow_2`. The muffs are enlarged. Lock widths are 3.6 to 2.0. `collar` removed.
**Strengths:** strongest long-hair silhouette in every view, a wide capelet at the shoulders, and the earmuffs read clearly. Teal stays dominant even without a hat.
**Weaknesses:** the head reads as a large brown mass from the back. Teal shows through gaps between the hair locks. The capelet could be mistaken for a scarf.

## Generator limits hit
- No `add_chains`, so a style can't get extra hair locks or a second chain.
- Chains rooted on the head follow head pitch, so the braid shot out sideways in the crouch frames. Re-rooting it on the chest fixed this.
- No per-segment material, so braid strands/bands can't alternate colour.
- Collision runs before the swing limit, so a tight `max_swing` can push a chain back into the arm. The working settings are narrow: a less forward rest direction got the braid ejected out of frame.
