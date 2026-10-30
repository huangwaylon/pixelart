# Team review 2026-10-30: step back, simplify, make it clean

The owner said: *"Take a step back. We're not making solid progress. It's still not polished nor production ready. Can we simplify
things... face: nothing but eyes/eyebrows... keep the colors consistent... be careful with the line art and weights... the lines need
to be clean and beautiful."*

Reports: `01_line_art.md` (line-art audit + prototype), `02_face_and_palette.md` (eyes/brows face + palette audit), `03_simplify_plan.md`
(production retrospective + staged plan).

## Why ten rounds didn't converge (03)
- **Too many moving parts per build.** About 39 spring bones, 48 clips, a 1,000-line pixel chain with 96 flags, 66 expression variants and 10+ gates,
  all re-rolled every round, so no defect could be traced to a single cause.
- **Reversals.** The head went through seven pipelines in four days, and the round-4 head is still the most readable face.
- **Wrong gates.** shade_swap failed 0/48 on every build, the owner's preferred head included. 78 % of "swaps" are between five
  near-identical darks (02). Nothing measured clean line art or consistent eye colour.
- **No frozen target.** Every round fixed 6–7 things against "the previous build". No single frame ever defined "done".
- **The motion is fine; the drawing is the problem.**

## Findings
| Area | What's wrong | Fix shown in a prototype |
|---|---|---|
| **Line art** (01) | Outline closed and mostly 1 px, but **irregular slopes** (≈7 zigzags/frame vs masters 4–5) because it's a ring around a thresholded 3D silhouette. 30–50 **flickering interior lines**/frame (hair/face). Hair and socks so dark that **45–49 % of the SE silhouette is a 3+ px black band**. | Trace the 8x silhouette, smooth it, redraw at 1x with uniform slope runs (1:1, 1:2, 1:3): zigzags 6.7 → 0.7, regular curves 48 % → 77 % (masters 57 %). Still needs frame-to-frame smoothing and interior lines from 3D part edges. |
| **Face** (02) | Detailed illustration eyes turn to mush at 96 px; textures break blinks. | **Eyes + brows only**, 4 colours (K lash/pupil, g iris, W catchlight always on the left, h brow), 7 expressions from eye shape + brow angle. Placed as **exact pixel shapes at a 3D-tracked surface point** (≤ 0.5 px off, identical every frame, hidden by hair/hands from the 3D depth). The texture variant failed. |
| **Colour** (02) | 10–18 colours per frame. Skin uses 8 (incl. red, blush and hair dark). Hair borrows sock colours. SE/SW hair a shade darker and faces pinker than other views. Eye whites render as holes (bug). | **Locked 14-colour palette** (K; h H g L hair/boots/socks; s S skin, face always flat s; e E R red; Q O o obi; W). Tone chosen by normal-vs-light band, not texture. Recolour alone: shade_swap −35–41 %, 16 → 12 colours/frame. |
| **Silhouette** (lead, from the boards) | Next to the master, the 3D body reads as a **red poncho**: sleeves merge into the dress, arms vanish, legs merge into dark columns. Clean lines won't fix that. | Needs shape decisions: narrower sleeves, a visible waist/obi break, arms that read outside the sleeves, a lighter sock/boot ramp so the legs separate. |

## Recommended plan (03, adjusted)
- **M0, design lock (½ day, owner sign-off):**
  - Face: eyes + brows only.
  - Palette: the locked 14 colours.
  - Lines: the line spec (1 px closed near-black outline; sel-out only on red, skin and obi; interior lines only at listed overlaps, ≥ 4 px long; clean slope runs).
  - Shading: 2-tone flat.
  - Springs: cut to about 10 bones.
  - Silhouette: fixes above.
  - Result: written as `DESIGN_LOCK.md`.
- **M1, walk SE only (≈3 days):**
  - The owner approves two **hand-polished gold frames** (contact and passing) as the target.
  - The pipeline is tuned to match them.
  - Remaining fixes go through the snowpeak **override layer** (sparse, reasoned, stale-checked).
  - Exit is a visual checklist written from the owner's own words, plus the line gates.
- **M2, walk in 8 directions (2–3 days):** SE/S/E rendered, SW/W mirrored, NE/N/NW.
- **M3, other actions one at a time (≈1.5 days each).** Decide katana slash vs unarmed first.
- **Process:** one owner change set per round, a frozen reference, and only gates that map to the owner's words block a build. Near-zero API spend (no multi-agent fan-outs).

## Decisions needed from the owner
1. **Face:** eyes and brows as exact pixel shapes placed from a 3D-tracked point (the most readable option). This relaxes the round-5 "don't special-case the face" rule *for the eye/brow shapes only*; their position and hiding still come from the 3D model.
2. **Palette:** adopt the locked 14 colours (drops the extra sock darks, mouth and blush).
3. **Gold frames:** approve hand-polished target frames for walk SE before the pipeline is tuned, so "done" has a definition.
4. **Silhouette:** allow simplifying the bell sleeves and separating the legs (a lighter sock/boot ramp).
