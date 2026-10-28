# START HERE: snowpeak character sprites (status for review)

All files live under `/Users/waylonhuang/Documents/other/pixelart`. GIFs play in any browser or Preview. Each board has a matching `_slow.gif` (3× slower) and a `_keys.png` (crouch / apex / land / ready stills).

## 1. Judge these boards (all animated, synced)
| Board | What it compares |
|---|---|
| `out/boards/1_proportions.gif` | **Proportions**, same outfit: A chibi 2.5 heads · B Pokémon-overworld ~2.2 heads · C semi-chibi ~3.4 heads · D trainer ~4 heads · E "puffball" |
| `out/boards/2a_outfits_A.gif` | **6 outfits × 6 colourways** on the A body (parka/puffer/duffle, skirt+tights, tall boots, slouch beanie…) |
| `out/boards/2b_outfits_B.gif` | The same 6 outfits on the B body |
| `out/boards/3_resolution.gif` | **Resolution**: ~24 px (32×40 cell) · ~32 px (48×48) · ~42 px (64×64) · ~56 px (80×80) |
| `out/boards/4_finalists.gif` | The two finalists at the chosen resolution, all 8 directions |
| `out/boards/5_hero_v1_vs_v2.gif` | Hero: v1.1 (570 hand-fixed px) vs **v2.4 final** (generator rules + 98 reviewed px) |

Per-variant 8-direction GIFs are in `out/variants/<name>/preview/jump_8dir.gif`, and per direction `jump_<DIR>.gif`.

## 2. Team recommendation (panel round 5, docs/review/r5_*.md)
* **Resolution: R2, 48×48 cell, character ~29–36 px tall.** The art director and game director agree. With tiles scaled to match, every resolution shows the same play area, so bigger sprites add memory (15 → 25–39 MB) and cleanup cost (~8 → 14–26 h per animation) without adding gameplay.
* **Outfit / colour: O1, charcoal parka, red beanie, scarf and mittens, cream pom and cuffs.** Unanimous. It has the highest value contrast on snow, and red is the only saturated hue, so the eye goes to the face and the scarf motion. It's colour-blind safe.
* **Body: split.** The art director and designer prefer **B (Pokémon overworld)** for the bold Gen 3/4 silhouette. The game director prefers **A (chibi)** for facing readability at small size. The lead picked **B as hero (H1)** with tuned crouch and landing poses (from the animator), and kept **A as alternate (H2)**. **This is your call.**

## 3. Hero deliverable: `releases/HERO` → `releases/H1_v2_4/` (art director SIGNED, game director ACCEPTED)
* `jump_sheet.png` + `jump_sheet.json`: game sheet 8 dirs × 12 frames, 48×48, pivot (24,41), with engine metadata (z_px, events, input lock 590 ms, cancel f10–f12).
* `jump_shadow.png`, `jump_fx_back.png`, `jump_fx_front.png`: engine layers. Draw order: shadow → fxBack → character (offset −z_px) → fxFront.
* `preview/jump_8dir.gif`, `preview/jump_<DIR>.gif`, `preview/slowmo/`, `preview/jump_contact_sheet.png`, `preview/greyscale_check.png`.
* `reference/`: character sheet, 3D turnaround, key poses, expressions, palette, **grounding_3d_vs_pixel.png**. `guide/guide.json` holds the projected 3D joints per frame.

**How it got here:**
1. Four pixel artists reviewed all 96 frames (`docs/review/pixel/H1_*.md`).
2. The art director cross-checked and locked 8 style rules (`H1_AD_signoff.md`).
3. Those rules and the recurring fixes were encoded into the generator over 4 review rounds (`H1_v2_vs_v1.md`). Hand pixels went from **570 → 254 → 170 → 100 → 98**, each with a recorded reason (`overrides/variants/H1v2_B_final/`).
4. A last-minute blocker (mittens recoloured as boots) was caught by the art director and fixed at the root.
5. The game director's engine simulator passes 16/16 (`docs/review/r6_game_director_acceptance.md`).

Older cuts are kept for comparison: `releases/H1_v1` (hand-fixed v1.1), `H1_v2_1`, `H1_v2_3`.

## 4. How the system works (reproducible + iterable)
* `README.md` covers the full pipeline. `docs/DECISIONS.md` holds the locked decisions, and `docs/review/` has every team round.
* The 3D model is the maintained reference. The generator (`pipeline/chargen.py`) builds the rigged mannequin from a variant spec. Every direction comes from that one model and one animation, so the views stay consistent.
* Feedback loop: edit numbers in `data/variants/*.json`, `data/palettes/*.json` or `data/animations/jump.json`, then `python -m pipeline.build --variant <name>`. Or paint fixes in the editor (`python -m pipeline.server` → http://127.0.0.1:8777/editor/?variant=H1v2_B_final).
* Builds are versioned by input hash, and `--verify` checks that the output is byte-identical.

## 5. Decisions waiting on you
1. Body: **B** (hero now) or **A**?
2. Confirm resolution **R2 (48×48)**.
3. Confirm the **charcoal/red** colourway. `cw_navy` is the runner-up.
4. Next animations (idle, walk, run…) will reuse this rig, palette and review process.
