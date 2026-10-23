# r16 - slimmer face + layered bangs (S4_hd)

User: "The face looks a bit too fat ... more realistic, pointy, curved face. at least, the bangs should be more volumous and come off the forehead more, for a more layered, dynamic look".

Write-up and AD reasoning: [docs/review/r16_face_bangs.md](../../docs/review/r16_face_bangs.md).

## Files
- **[options_x10.png](options_x10.png)**: mockups (pixel edits on real r15 idle S / SE / E frames, at 10x, 1x and 2x).
  - Face options: F0 current, FA trim, **FB V-taper +1 row (chosen)**, FC curve with a forward chin.
  - Bang options: B0 current, **B1 two layers + cast shadow (chosen)**, B2 flicked tips, B3 dark shell underside.
  - The bottom row is the real r16 build.
- **[before_after.png](before_after.png)**: S / SE / E / SW / W at 8x, for idle f1, run f4, jump_sc f7 and throw f3.
- **[head_hires_before_after.png](head_hires_before_after.png)**: smooth hi-res render of the model head: front, 3/4 and profile.
- **idle / walk 8-dir GIFs**: `*_8dir_before.gif` (r15) and `*_8dir_after.gif` (r16).

## What changed (model first, then the face rules)
- **Head SDF** (`pipeline/tools/make_s4_hd.py`, `HEAD`):
  - The cranium is unchanged, so the eye rows keep their width.
  - The jaw is narrower (6.5 to 5.5) and sits lower.
  - The chin comes 1.55 further down and ends in a sharper point.
  - The face blend is tighter.
  - Result below the eyes: S rows 10-8-5-2 (chin 2 px), 3/4 8-8-6-1 (chin 1 px), and the profile chin sits 1 px forward-down.
- **Bangs** (`LAYERED_BANGS`):
  - The single row of hime clumps is replaced by a two-layer shell.
  - The front clumps use the mid hair tone and get the highlight ring. They stand 0.7-0.75 off the forehead, and their tips curl forward and flick outward.
  - The back clumps use a new `hair_dk` material (dark ramp). They start under the hair cap, so only their longer, staggered tips show between the front clumps.
  - The temple bangs and sloped sides from r15 are kept.
- **Face rules** (`pipeline/face.py`, `face_eyes.hem_shadow`, `hem_layer_mat`):
  - The pinned gap row under the fringe is now a 1-row skin shadow cast by the shell.
  - The visible back-layer pixels are drawn in the dark tone and protected from despeckle.
  - The hem fill uses each clump's own tone.
  - Everything from r15 still holds: the hem is pinned, eyes are never covered, lone face-hair pixels are cut, and closed eyes keep skin on their open side.

## Status
- Rebuilt the 13 base clips and the 14 `*_r14` copies. QA: 27/27 PASS, no warnings.
- Three ponytail-tip overrides were re-approved; their pixels are unchanged.
- Flicker scan on run, walk and carry_walk (plus r14 copies), S / SE / SW: the gap between the bang hem and the lashes stays at 1 row in every interior column of every frame. Only the outer edge column steps, as it did in r15.
- Lone face-hair pixels: 0.
- Eye pixels hidden by hair: 0 in idle, walk, run, jump, carry_walk and pick_up. The exception is pick_up E f8 (joyful), 1 px.
- Legacy S4_halfup_bow idle, walk and throw are byte-identical.
- Gemini was skipped because auth expired (OIDC/mTLS).
- Not committed.

## Round 2 (AD r16 review: the S fringe read as a comb over a headband)
- **[round2_S_fringe.png](round2_S_fringe.png)**: round 1 vs round 2 S frames (idle f1, walk f1, run f4, throw f3, jump_sc f7) at 8x, plus 1x / 2x. The other boards and GIFs have been regenerated from the round 2 build.
- **Fix 1-4 as a front-view fringe rule** (`face_eyes.s_fringe`, `pipeline/face.py _s_fringe`). The rule is drawn relative to the pinned hem and the locked S eye pair, so it holds in every S frame of every clip.
  - Three mid-tone clumps: left | 4-px centre clump (centred on the eyes) | right.
  - Dark V-notches only in the 2 gaps, one row above the hem, with forehead skin showing in the notch at the hem row. There is no dark on the hem row.
  - One 2-px highlight per clump at hem-1, and none over the gaps.
  - The row above the lashes is skin shadow only under the clump tips (at most 4 px); elsewhere it is base skin.
  - Idle S matches the AD's coordinates exactly: gaps at x21/x26; highlights at x18-19, x23-24, x28-29; shadow at x18-19 and x22-25.
- **Model merge (fix 5) was tried first.** Three wide front ribbons (centre plus two sides) over one back clump per side were rendered.
  - At sprite size they still gave a dark centre block and split highlights in S.
  - They also changed the approved SE/SW fringe.
  - So the model keeps the round 1 fringe and S uses the rule, which is the fallback the AD allowed.
  - The hem pin, the 1-row gap to the lashes and the no-lone-pixel rule are unchanged. The lone-pixel cut now makes a second sweep, which catches a pixel orphaned by the first.
- **Optional cheek narrowing (10 to 8 at y34) was not applied.** The face sits off-centre by a sub-pixel, so the left cheek lost two rows and the left eye ended up against the side lock. It read pinched, not slimmer.
- **Determinism fix.** With two hair materials (`hair`, `hair_dk`), `_ring_trim` and the pixelrules hair pick iterated a hash-ordered set. Builds therefore varied run to run by a few ponytail and back-of-head pixels.
  - Both now iterate in sorted order.
  - Builds are byte-stable across `PYTHONHASHSEED`. I checked throw with two seeds.
  - The fringe rule's pixels are also exempt from the ring trim.
- **Checks:**
  - SE/SW/E/W/N/NE/NW are byte-identical to a deterministic rebuild of round 1 (HEAD) for idle, walk, run, throw, jump_sc, fall and carry_walk. Only S changed.
  - The S spec scan over all 176 S frames found 0 violations: no dark on the hem row and no shadow run over 4 px.
  - Flicker scan (run, walk, carry_walk and their r14 copies, S/SE/SW): the per-column gap pattern under the fringe is the same in every frame. In S, the 2 notch columns hold their 2-row notch, and only the outer edge column steps, as in round 1.
  - Lone face-hair pixels are 0 in run, walk and carry_walk. 3 remain in S, in throw and jump_sc, where the side lock meets the eye corner; the AD accepted the throw case in r15.
  - QA: 27/27 PASS, no warnings. Legacy S4_halfup_bow idle, walk and throw are byte-identical.

## Round 3 (Gemini r2 critique, checked against the sheets; AD r17 note 1)
- **[round3.png](round3.png):** round 2 vs round 3 for S / SE / SW / E in idle f1, run f4, throw f1 and jump_sc f7, at 8x plus 1x / 2x.
- **[round3_G1_dots_vs_band.png](round3_G1_dots_vs_band.png):** the two S highlight treatments at 8x and 1x / 2x.
- **G2, SE/SW balloon cheek (confirmed).** In SE idle the far contour ran x28, x28, x28, then snapped to x26.
  - A model jaw change was tried first. Narrowing the jaw doesn't move that edge, because the cranium sphere sets it, and changing the cranium would change every view. So this is a rule: `face_eyes.jaw_taper` (`_jaw_taper`).
  - Below the eyes, the far contour (or both sides in S) steps in at least 1 px per row, the outline moves in with it, and the new corner pixel is skin shadow.
  - A silhouette skin pixel that the later outline pass will darken is treated as outline, so SW (lit side) tapers the same way as SE.
  - SE idle is now 28 / 27 / 26; SW mirrors it.
  - Far-cheek vertical runs under the eyes, over all 176 frames: SE 0, SW 6. The 6 are carry frames and land_heavy, where the crate or arms sit against the chin.
- **G5, jump_sc squint chin (confirmed in S).** The rows went 8 / 7 / 3. The same taper rule now gives 8 / 6 / 3 with a centred tip.
- **G1, S comb at 1x (partly accepted).**
  - The isolated 2-px highlight dots are replaced by one clump-wide highlight run per clump (`s_fringe: "band"`). At 1x it reads as a continuous sheen with two notches.
  - The AD's notches, notch skin and tip shadow are unchanged. The spec scan over 176 S frames found no dark on the hem row and no shadow run over 4 px.
  - Rejected: side locks stepping up toward the temples. That would undo the user's "longer near the sides".
- **G3, E/W forehead wall.** In profile, the front-most skin pixel of the top forehead row under the lifted fringe is now skin shadow, so the face front curves in under the bang (`profile_brow`).
- **G4, SW run f4 visor (confirmed).** Where the 3/4 fringe overhangs the far contour, its tip now drops 1 px in the plum hair-outline tone on the lash row, so it arcs down.
- **AD r17-1, throw f0.** Hem-row skin outside the face columns, under hair, is folded into the clump: x18-19 are now hair.
- **Checks:**
  - Flicker scan (run, walk, carry_walk and their r14 copies, S/SE/SW): the per-column gap patterns are identical to round 2, and lone face-hair pixels are 0.
  - Eye pixels hidden by hair: 0 in idle, walk, run and jump; throw is unchanged at 3 (its pre-existing joyful frames).
  - QA: 27/27 PASS, no warnings. The jump_sc E f4 ponytail override was re-approved; its pixels are unchanged.
  - Legacy idle, walk and throw are byte-identical.
  - Builds are byte-identical across `PYTHONHASHSEED` (walk checked with two seeds).
