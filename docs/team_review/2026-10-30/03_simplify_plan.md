# 03: Simplify plan (production lead / technical director), 2026-10-30

> Owner: *"Take a step back. We're not making solid progress. It's still not polished nor production ready. Can we simplify things."*
> Face: eyes + eyebrows only, consistent colours. Line art must be clean and beautiful.

**Verdict.** The swordswoman skinned-rig effort (`REVIEW/exp/2026-10-28_sw_skinned/`) has spent 11 builds over about 36 hours
improving the wrong thing. Each round tried to fix 48 clips, 5 owners and a 96-flag pixel chain all at once. It had no frozen
target and no definition of "done". Panel scores have been flat at 4-6/10 since round 4. The fix isn't another round. Cut scope
until one clip can be made beautiful, then scale it up with the snowpeak tooling, which has already shipped 13 clips.

---

## 1. What the owner values (from their own words)

| Theme | Owner quote (CONTRACT.md) | What it means |
|---|---|---|
| Solid, connected forms | "body parts are not connected" (r1) · "I still see disconnected parts like legs, thighs" (r2) · "Check limbs" (r3) | Readable, closed shapes. No flicker. |
| Life, not stiffness | "need more dynamic movement… bouncing parts" (r1) · "not stiff" (r2) · "more expression, bouncy, liveliness" (r3) | Clear key poses and follow-through on a *few* things |
| Natural, feminine posture | "confident, feminine" (r2) · "leaning back too much… natural, human, feminine" (r5) · "head unnaturally jutted back" (r5) | Silhouette and gesture |
| On-model face | "faces are all messed up… follow the head's movements" (r3) · "much much worse than before, it regressed severely" (r7) | Identity first. Now cut down to **eyes + brows, consistent colours** |
| Hair that looks designed | "longer, more consistent bangs, she looks like she's balding" (r5) | One solid fringe shape |
| Smooth loops | "Make sure the GIFs run and loop smoothly" (r3) | Timing and the loop seam |
| **Polish** | "not polished nor production ready… simplify" (now) · "clean and beautiful" line art | Hand-quality pixels, not more systems |

The owner has never asked for 48 clips, 17 expressions, 8 skirt panels or illustration textures. They asked for a character
that looks *on-model, clean, alive and natural*. They judge it by eye, against the approved art. The 2026-10-28 review found the
same thing: the only reliable predictor of the owner's verdict was side-by-side fidelity to the approved design
(`00_SUMMARY.md`, "Critics").

## 2. Why ten rounds didn't converge

**2.1 Too many moving parts.** Every build re-rolled all of the following:
- The rig: 13 rest-skeleton revisions (`rig/rest_skeleton_r10…r13.json`), head re-sculpts and fringe re-cuts.
- The head *method*: about 39 secondary spring bones (bangs 6, side locks 6, back 3, bun 1, bow 5, sleeves 4, skirt 16, obi 2).
- 6 actions × 8 directions = **48 clips per build**.
- The pixel chain: `render/pixel_chain.py` is 1,023 lines. The experiment reads **96 distinct env flags** across render/rig/face.
- Textured vs flat materials, PZCLEAN, and the E2 path.
- 66 expression variants × 3 views, with Gemini edits followed by programmatic bulges.
- 10+ gates.

A defect can come from any of those layers, and no one can tell which one caused it.

**2.2 Reversals, mostly on the head.** The head went through:
1. projected master pixels (r2)
2. 2D decal face (r3)
3. 3D hand textures + "don't special case it" (r5)
4. back to the r4 head as a "hybrid best" (r7a)
5. illustration-textured 3D (r7)
6. baked UV (r8)
7. eye bulge warps (r9)
8. almond eyes (r10)

That is seven head pipelines in four days, and the **r4 head is still the most readable front face** (panel 7-8 vs 5-6 for
r10). Posture also reversed: "chest lifted, chin up" in r2 made her lean back, which r5 corrected. Run lean went from "< 8°" to
"12-18°". The fringe went "longer" in r5, then "lift 1-2 px" in r8, r9 and r11. Each reversal invalidated downstream work.

**2.3 Metrics that don't measure taste.**
- **shade_swap fails on 0/48 clips in every build from r5 to r10**, and it fails on the owner-preferred r4 head as well. A gate
  that never passes on any variant can't tell good from bad. It's the wrong gate, or the wrong threshold for a 3-tone textured
  chain.
- boil stayed at 13/48 for six builds whatever anyone changed.
- face_ssim became "not comparable" the moment R turned the head 10°.
- "feet" fails in perspective views by construction (P's own note).
- Meanwhile the gates that *did* move (limbs 25→47/48, bangs 23→48/48) didn't move the panel or the owner.

So the gates measure defect absence, not beauty. Nothing measures "clean line art" or "consistent eye colour". Those are the
two things the owner just asked for.

**2.4 Too many parallel changes per round.** Each round shipped 6-7 ranked proposals across R/F/P/M at once, then a full
48-clip rebuild and one Opus A/B. When the r8 limbs gate fell from 44 to 33/48 (PZCLEAN), it took a round to find out why.
Nothing was attributable, so nothing was learnable.

**2.5 No frozen reference.** Every round compared against "the previous build" and "r4 head". Neither is a target. No one ever
made the single frame that says *this is what done looks like*. Snowpeak had one (the r13 hand-pixel canon), and so did m96 (the
approved masters). The skinned effort has always measured relative progress toward nothing.

**2.6 What the pixels show.** Looking at `release/out/20261030_66119a7/walk/SE_strip1x.png` at 4x next to `swordswoman/v2/m96/sheet.png`:
- The m96 master has a closed dark outline, readable sleeves, an obi and a clean 3-tone dress.
- The r10 walk has a dress that is one flat red blob with no interior line (sleeves have vanished into the torso), an obi
  reduced to a grey slash, speckled hair, a broken outline on the dress edge and skirt hem, and brown "blob" eyes with dithered
  pink cheeks.
- The hybrid `20261029_3831ac8` reads better in the face and cleaner in the hair, but its body has the same mush.

The motion is decent. The *drawing* is what isn't production quality, and procedural chain tuning will not make it so.

## 3. Cut / freeze list

| Area | Now | Cut to | Why |
|---|---|---|---|
| **Face** | 17 expressions × open/half/blink × mouth; blush, nose, mouth, catchlight rules; Gemini expression illustrations | **Eyes + brows only.** Two eye states (open, closed) per view, plus one brow shape per view. Colours are fixed palette indices (lash/pupil K, iris one tone, catchlight W, brow g). No mouth, blush or nose. | The owner's spec. It removes F's 102-texture set and most face-integrity failures. |
| **Face method** | textured 3D head through the chain | Eye/brow **pixel parts placed on R's 3D face anchors** (snowpeak `pipeline/face.py`, already proven; anchors exist in `rig/face_anchors.json`) | 4 tiny shapes can't survive pixelizing a texture at 96 px. Ten rounds prove it (front face 4-6 vs 7-8 for the stamped r4 head). **Owner decision needed:** this lifts the r5 "don't special case the face" rule for these shapes only. |
| **Palette** | 18-colour EC0 palette, plus textured k-centroid colours | **One locked palette of ≤ 14 indices**, from `swordswoman/v2/pixelize/palette.json`. The build fails on any off-palette pixel. | "Consistent colours" |
| **Shading** | 3-tone ramps + textured hair/face + PZCLEAN | **2-tone flat** (base + shadow) per material, fixed screen light. Hair is flat material on the r13 geometry, not an illustration texture. | Fewer bands mean fewer swaps, less boil and no speckle, by construction |
| **Line spec** | outline emerges from the chain | A written spec. The silhouette is a closed 1 px outline in per-material dark (sel-out allowed only on the lit side). No doubles, no orphan pixels, no L-corners on curves. Interior lines only at sleeve/torso, obi edges, hem/leg and fringe/face. Lint-checked. | "Clean and beautiful". The other reports in `line_art/` and `face_palette/` own the details. |
| **Secondary chains** | about 39 spring bones | **Bow lobes (2), side locks (2), skirt as 4 panels, sleeves (2).** Bangs, bun, back hair and obi are rigid with the head/pelvis. | Owner wants "bouncing parts", not boiling parts. The fringe must stay one solid mass. |
| **Directions** | 8 native per build | **SE first**, then S and E. SW/W are **mirrors** (the design is symmetric; check the bow/bun side once). N/NE/NW last, with no face. | Removes 5/8 of the face work |
| **Actions** | 6 per build | **Walk only** until it ships. Then idle, then run/jump/dash/hurt one at a time. | One polished clip beats 48 at 5/10 |
| **Gates** | 10+, mostly reported not blocking | **Blocking:** palette-exact; line lint (outline gaps, orphans, doubles); limbs connected; eye/brow colour indices identical every frame; loop seam; posture (torso ≥ 0°, head-forward ≥ 0); determinism `--verify`; overrides not stale. **Drop:** shade_swap, face_ssim, boil as a blocker, perspective feet, Opus scores as a target. | Each blocking gate maps to an owner sentence |
| **Critics** | one Opus 3-role panel per build | At most one per milestone, A/B against the **gold frame**, never on its own | Panel scores were flat for 7 builds and didn't predict the owner |
| **Hand polish** | forbidden ("never pixel-paint the result", r5) | **Allowed, in the snowpeak override layer**: sparse pixels, a reason per edit, stale detection, the editor | Snowpeak shipped 13 clips this way. Recurring fixes get promoted to rules (`pipeline/pixelrules.py`; H1 hand pixels went 570→98). |

## 4. Staged plan

**Rule for every milestone:** one variable changes per iteration. Builds are SE-only (minutes, not the 6-minute 48-clip run).
The owner reviews one board: gold frame | current frame | m96 master, at 1x and 4x.

### M0: Freeze (0.5 day). Owner: lead. Cost: $0.
- Write `DESIGN_LOCK.md` on one page: palette indices, the 2-tone rule, the line spec, the face spec (eye open/closed and brow
  per view, with exact colours), the chain list, the head method (eyes/brows as anchored parts) and the action/direction order.
- Archive every head variant except r13 geometry + flat materials. Set `release/actions.json` to walk only and `DIRS=SE`.
- Port the frame hand-off into the snowpeak override format (`overrides/<anim>/<DIR>/<NN>.json` with base hash). Fix the known
  `pipeline/server.py:_out()` variant-path bug so the editor opens the clip. Owner: I/P.
- **Exit:** the owner signs DESIGN_LOCK. Any later design change needs a new sign-off and restarts the current milestone, on purpose.

### M1: Walk SE, production quality (3 days). Owners: AD/pixel artist (gold + polish), P (chain), R (anchors, chains), M (motion frozen except fixes). Cost: about $0 API, plus an optional single Opus A/B.
1. **Gold frame (day 1).** Build walk SE f00 (contact) and f02 (passing) from the rig pose, and hand-polish them in the editor to
   the m96 SE master's quality. They must follow DESIGN_LOCK: 2-tone, clean line, eyes + brows. **The owner approves these two
   frames.** They are the target from then on.
2. **Tune to the gold (day 2).** P adjusts the flat 2-tone chain and line rules to minimise the palette-index diff against the gold
   frames. Every rule change gets measured as "diff px vs gold". F's role folds into the AD: 2 eye states + 1 brow × 1 view.
3. **Polish (day 3).** Run the remaining frames through the pipeline. The AD applies overrides with reasons, with a budget of
   **≤ 120 override px per frame**. Snowpeak S4_hd shipped with 3 override files. Any fix repeated in 3 or more frames becomes a rule.
- **Exit (visual checklist, from the owner's words), at 1x and 4x:**
  - [ ] every limb is connected in every frame, and no leg vanishes
  - [ ] closed, unbroken outline with no stray or doubled pixels
  - [ ] sleeves, obi and hem read as separate shapes
  - [ ] eyes and brows are the same colours and the same shape in every frame, and they follow the head
  - [ ] the fringe is one solid mass above the eyes
  - [ ] upright, feminine walk with no lean-back
  - [ ] the bow, side locks and skirt bounce at least 1 px and don't boil
  - [ ] seamless loop
  - [ ] `--verify` is byte-identical, and no override is stale
  - [ ] **the owner says "ship it"**

### M2: Walk, 8 directions (2-3 days). Same owners. Cost: about $0.
- Do S and E natively, each with its own gold contact frame first. Mirror SW and W, then do NE, N and NW (no face).
- **Exit:** the M1 checklist per direction, ≤ 120 override px per frame, and the 8-dir sheet and JSON export (snowpeak `export.py` metadata).

### M3: Other actions (about 1.5 days each). Order: idle, run, jump, dash, hurt.
- Each action gets one gold key pose (the action's signature frame) approved first, then SE, then the M2 fan-out.
- Smears for dash/jump are authored as override frames, not simulated.
- **Exit per action:** the checklist plus owner sign-off. Also confirm with the owner: slash with katana, or the unarmed set
  (an open question since 2026-10-28)?

**Total:** about 2 weeks to a full shippable set. The first owner-approvable clip comes in **3.5 days**. API spend is
near zero, compared with $500/day hit in round 10.

## 5. What we stop doing
- Full 48-clip rebuilds to test a single change.
- Ranking 6-7 fixes across four owners per round.
- Gating on metrics that every variant fails.
- Treating hand pixels as failure.
- Changing the head method again.

The remaining procedural layers (rig, motion, springs, chain) are kept because they give us consistency across frames and
directions. Beauty comes from a gold frame and a reasoned override pass, which is how snowpeak got its shipped set.
