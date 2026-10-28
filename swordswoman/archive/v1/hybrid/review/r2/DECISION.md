# Round 2 decision (LEAD synthesis)

Inputs:
- the 4 r2 compare boards (I re-checked compare_slash.png and compare_walk.png at zoom);
- both polished sets (S3_editchain, S5_pixelnative);
- five director-style judges (Art, Game, Animation, Pixel-art lead, Consistency analyst) plus Gemini Argon (via the liaison).

User priority this round: "Smears are important for fast movement."

## Pass gate
Rule: a strategy passes only if EVERY non-Gemini judge passes it AND Gemini overall >= 7.5.
No judge passed anything. The best director overall is 6.5, and Gemini's best is 5.
**passed_keys = [] (none).**

## Scoreboard (overall)
| key | Art | Game | Anim | Pixel | Consist | Gemini |
|---|---|---|---|---|---|---|
| S5_pixelnative | 6.4 | 6.4 | 6.3 | 6.1 | 6.0 | 5 |
| S3_editchain   | 5.9 | 6.2 | 6.2 | 5.8 | 6.5 | 4 |

Both strategies are up from r1 (S3 was 5.8-6.6, S5 5.3-5.9). The r1 merge worked: one shared body base, and the smears are now the place where the two strategies compete.

## What the judges agree on (both sets, because they share the S3 lock2 cels)
1. **The 8-direction identity is solved, more or less.**
   - One character, a three-circle head cluster, and a consistent bow.
   - Body height 62 and pivot spread 0.88 (S3).
   - The hand-authored W/NW/SW match the rest.
   - This base should be FROZEN, not re-invented.
2. **The walk is the weakest animation in both sets (all 5 directors).**
   - The legs are hidden under the hem, so it reads as a hover-shuffle.
   - The upper body is frozen.
   - Bow lag is 1 px. Ribbons do not overlap.
   - S3 also has sword-angle jitter (horizontal in k0, steep in k2).
3. **Smears and impact: S5's polished FX are the standard (all 5 directors).**
   - k1: a tapered double crescent with a steel_2 rim, 321 px, arc rms 0.16.
   - k2: an 8-point impact star.
   - jump: under-foot apex streaks and landing dust.
   - S3's k1 is a thin, low "pink line", and its k2 is a poke with a 5 px spark.
4. **The head is a rigid stamp.**
   - It never tilts or sinks on the action keys, and the spine is upright.
   - The k0 coil is just the blade drawn back. There is no torso twist (Art, Game, Anim, Pixel).
5. **The jump has no air.** The apex feet sit on the crouch baseline (Anim, explicitly). The baseline_spread=0 gate is fighting the action.
6. **Red on red.** At 1x, the sleeves, arms and legs merge into the skirt. The arms are thin capsules, and the sword hand is hidden under the k1 smear.
7. **Shared craft defects, to fix ONCE in the shared cels:**
   - the hair is hatched with evenly spaced 1 px vertical stripes (comb banding);
   - the ribbons are 1-2 px squiggles that share the smear pink;
   - the NE/N bow loops are detached blobs;
   - the purple arm ornament is missing (0 px in all 38 sprites);
   - the kagi hook is 2 px (the bible's minimum is 3);
   - the corset nearly vanishes in E/W;
   - the jump keys drop the tall collar;
   - the idle blade tip goes below the foot baseline in S/SE/N/NE;
   - S vs SE and N vs NE/NW facing is weak at 1x.
8. **Specific S5 defects:**
   - k2: the mouth reads as a scar, and the burst dashes are confetti.
   - k3: snaps the blade up like a second wind-up, and the near ribbon crosses the chest.
   - walk k1-k3: off-model collar, dropped ribbons, foot slide (feet_cx 6 to 2.5).
   - turn_SW: 2 px off pivot.
   - The pipeline is built against S3's LIVE cels.
9. **Specific S3 defects:**
   - the dash afterimage is a feathery pink blob, the soft-blur look that ANIM_DIRECTION section 4 bans;
   - the apex streaks sit beside the body ("rain");
   - the jump_E_apex has a stray sleeve flag;
   - confetti in the action skirt;
   - slash flicker=2 and boil of 132-188 px.

## Team discussion and dissent
- **Which strategy is best.**
  - Art, Game, Anim and Pixel pick S5, for motion and smears, the user's stated priority.
  - Dissent (Consistency analyst): picks S3 (6.5 vs 6.0). S5's walk is off-model and its turntable pivot jumps.
  - Resolution: both are right, about different parts.
    - S5's identity problems are all in the parts S5 rebuilt or retraced (walk k1-k3, turn_SW).
    - S3's weaknesses are all in its action FX.
  - So the work is split by OWNERSHIP, not by winner:
    - S3 owns the frozen identity base, the walk, and the run/dash.
    - S5 owns the action keys (slash, jump) and the FX language.
- **Anim's margin.** The Animation director calls S5's lead "narrow (6.3 vs 6.2), on motion only" and credits S3 as the only strategy with run and dash smears. That is accepted. S5 must add run/dash smear parity, using the shared FX kit below. S3's run leg-smear echo is kept as the reference.
- **Baseline gate vs jump air.**
  - Anim and Game want the apex 8-12 px off the ground.
  - The consistency metrics enforce baseline_spread=0.
  - Resolution: the cell keeps its pivot and foot baseline. The apex BODY is drawn 10 px higher inside the cell, the shadow stays on the ground row, and anim meta records `air_px: 10`.
  - The gate is amended: the baseline check applies to grounded keys only (turn, walk, slash, crouch, land). Airborne keys must instead show feet >= 8 px above the baseline.
- **Head size (Gemini dissent).**
  - Argon again wants a bigger head and a higher camera, and says S3 is "3.5 heads tall".
  - The measured figure contradicts it (62 px tall, head 20-22 px wide).
  - Argon also claims "no head bounce in the walk", but the crown rows are 42/44/46/41.
  - Rejected. Gemini overrates and cannot pass anything, and the r1 proportion call stands.
  - Accepted from Gemini: a bigger bow (Art says each loop should be about 0.3 of the skull width; the Consistency band becomes 55-65 px) and a lower k3 follow-through.
- **k3 direction.**
  - Anim, Pixel and Gemini all want a LOWER recovery arc: blade low and across, about 30 deg below horizontal, body settling over the lead knee.
  - Art allows either that or a justified high arc with a settle frame.
  - Resolution: go low. It is the majority view and it matches saint11.
- **Dash afterimage style.**
  - Pixel lead: wedges plus one 50 % dither echo.
  - Anim: two hard-edged silhouette multiples plus 3 straight lines along the travel vector.
  - Resolution: use Anim's hard-edged multiples. Dither shimmers at 1x and the user wants crisp smears. The Pixel lead's rimmed wedges are used for the speed bands.
- **Smear colour role (Pixel lead, adopted).**
  - Smears use a steel_2 rim, a pink_0 body and white_ core highlights only.
  - Ribbons use pink_1 over a pink_0 underside with a dark outline at the collar root.
  - The two must never share a band at the same tone next to each other.
- **Hidden arms vs big smear.**
  - Game and Pixel want the hand and hilt visible at the crescent's lead. Art is happy with the smear as is.
  - Resolution: cut the crescent locally so a 3-4 px skin fist plus 2-3 hilt pixels sit at the lead end. The smear keeps at least 300 px.
- **Method honesty.** "S3_editchain" no longer runs a Gemini edit chain. The key is kept for continuity, but its role is now BASE / identity owner. Gemini is used only as an acting reference (S5).

## Decision
Two strategies continue, with explicit ownership. The new strategy S7_fxkit is a shared, Claude-authored FX and acting library that both consume.

### Sequencing (fixes the live-dependency problem)
1. **Phase A: S3 ships `hybrid/lock3/`.** This is the shared-cel repair, and S3 does it before anything else. It contains the head stamps with acting variants, the hair, the ribbons, the bow, the collar, the corset, the katana guard glyphs and the 8 turn cels.
   - Write `lock3/MANIFEST.json` with per-file sha256.
   - After that, lock3 is READ ONLY for everyone. Changes go only through a lead-approved lock3.1.
2. **Phase B, in parallel:**
   - S3: walk + run + dash.
   - S5: slash + jump + idle-blade check, rebuilt against lock3 only. build.sh must fail if a hash differs.
   - S7: the FX kit.
3. **Phase C:** the lead assembles ONE combined standard set (`hybrid/combined/r3/`), with S3's turns and walk and S5's slash and jump. Both strategies also submit their own full set for judging.

## Polish focus for r3 (both)
- Review the whole set in motion at 1x on grass and dirt, not only at 4x.
- Every fix is per-pixel and logged in edits.json.
- Orphans 0. Lint targets: outline_gap and jaggy each halved from r2.
- New gate checks (Consistency analyst):
  - bow 55-65 px (front up to 85);
  - head width 20-22;
  - collar present on every key;
  - ribbon px >= 50 % of the matching turn;
  - purple >= 1 px where the right arm is visible;
  - hook >= 3 px;
  - airborne keys: feet >= 8 px above the baseline;
  - smear >= 300 px on slash k1.

## Briefs (summary; the full text is in the workflow output)
- **S3_editchain**: BASE/identity owner.
  - lock3 repairs: hair strand clusters, 2-3 px ribbons, connected back-view bow, bigger bow, purple ornament, 3 px hook glyphs, E/W corset strip, diagonal facing offsets, idle blade above the baseline, sleeve lining and outline, head acting variants.
  - Rebuilt walk_SE with visible scissoring.
  - Run kept; dash rebuilt as hard multiples.
- **S5_pixelnative**: ACTION/FX owner.
  - Slash re-acted on lock3: k0 twist and squash, k1 crescent with hand and hilt visible, k2 cleaned star plus gritted mouth, k3 low recovery.
  - Jump with 10 px of real air.
  - Run/dash parity from S7.
  - No walk or turn authoring.
- **S7_fxkit (new)**: a shared Claude-authored smear and FX library (tools/hybrid/fx/).
  - Contents: crescent, multiple-limb, speed bands, afterimage multiples, impact star, dust, streaks, head-acting offsets.
  - Each has a unit preview board, and S3/S5 consume it.
