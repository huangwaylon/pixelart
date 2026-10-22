# r12 HD model (S4_hd) - Game Director review

**Verdict: ADOPT-WITH-FIXES**

## Checked
- **Phone readability.** All 8 directions of idle, run, carry_walk, throw and jump_sc composited over snow (#ECF2F8) and rock (#423E4A) at 1x, 2x and 4x. Silhouettes are as readable as legacy or better: bow, bangs and boot soles all read. Facing reads clearly in all 8 directions. The E/W ponytail is slightly smaller but its direction is still obvious. Every sheet stays on the palette (`frost_r3_oatmeal`, 9-16 colours, no semi-alpha).
- **Contract.** All 13 clips match `releases/S4_actions_v1`: frameSize 48x64, pivot (24,57), frame counts, durations, events, cancel windows, root_px/z_px, and the hand_R, hand_L and carry anchors. Shadow and fx strips are byte-identical. hand_R lands on mitten pixels (within 0.7 px) in every frame.
- **Height.** QA passes on all 13 clips. Standing height is about +1 px (34 to 35) and more even across directions. max_height_delta is the same as legacy or lower.

## Fixes
1. **Prop data is not identical. Correct the README.**
   - In `throw_sheet.json` the prop layer tag changed from front/back to split in three places: frame 0 E and W, frame 1 E.
   - In all 5 prop clips, prop_front/prop_back put pixels in different layers than legacy, though the total prop pixels are unchanged. Occlusion is re-derived from the new body.
   - So the HD body sheet, its json and its prop strips must ship together as one set. Never pair HD bodies with v1 prop strips.
2. **Cut a new release** `releases/S4_hd_actions_v1` that includes the sheet json and every layer. Leave v1 untouched so the engine can roll back.
3. **Fix 1 px of foot jitter.** The sole hits y=59 in walk S1, S5, SE5, SW1 and carry_walk SE4, SW0. Legacy never goes below 58 in these clips. Clamp locomotion soles to 58 or below so feet don't dip below the ground on flat tiles.
4. **Even out run height.** Run is 33 px facing E/W but 35 px facing N/NE. Bring this to a spread of 1 px or less, like the other clips.
5. **Hem contrast (AD).** The warm dark hem band from legacy is lighter now, so at 1x the coat and legs merge into one tan block, worst in E/W. Keep a single dark hem row.
6. **Engine: +1 px height.** Raise the head-clearance and occlusion-sort budget by 1 px. Nothing else in the engine changes.
7. **Separate ticket, not HD-specific.** The light-blue shadow looks like a glowing patch on rock. Tint the shadow per biome.

Once fixes 1-4 are in, S4_hd can replace S4_halfup_bow as the in-game hero.
