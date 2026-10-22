# r12 HD round 2: fix list -> change -> evidence

Data: `pipeline/tools/make_s4_hd.py` -> `S4_hd.json`. Shared code is opt-in; legacy `_sheet.png` (idle, throw, carry_walk, walk) is byte-identical to a fresh HEAD build. 13/13 QA PASS, 0 warnings. Crops: `00_REVIEW/r12_hd_model/fixes/`.

| # | Change | Evidence (before -> after, legacy) |
|---|---|---|
| 1 | Front side lock z 2.8 -> 0.6 | E+W glint frames 42 -> 104 (98); fix01 |
| 2 | Hem band 2 px tall (w 1.15); scallops refs-only | rust row + dark row; idle rust 342 -> 1792 (1176); fix02 |
| 3 | `vote` key lets hair_cap/hair_back join the clumps, so seams no longer blur the ring; ring_w 0.14 | full arc + nub as legacy; fix03 |
| 4 | Cuff r .35 / w .68, set back from the wrist | throw S2, jump N9, carry_walk S2 teal, no rust; fix04 |
| 5 | `torus.round` petal loops; `lineart.keep_selout_runs` keeps the teal_0 loop outline | S ears 2-3 px, SE outlined, N9 symmetric; fix05 |
| 6 | Belt clipped behind the hips | NE hair flicker 42 -> 13 (24), NW 35 -> 7; fix06 |
| 7 | `render.temporal_hold` (idle loops, crown rows, orphan-safe) | S 74 -> 18 (13), N 51 -> 23 (45), SE 43 -> 11; fix07 |
| 8 | `render.separate_materials` [ribbon, mitten]: teal_0 where they touch | fix08 |
| 9 | Follows from fix 4: the cuff no longer reads as hair | throw N4/NE4 mitten + plum separation; fix09 |
| 10 | Ankle-space sole clip + toe/heel spring | y=59 rows: walk 4 -> 0, carry_walk 2 -> 0; idle still on 58; fix10 |
| 11 | Crown clumps 0.12 closer to the cap + heel spring | run standing 33-35 -> 33-34; fix11 |
| 12 | README prop-layer claim corrected | `00_REVIEW/r12_hd_model/README.md` |

## r13 user requests (README "User requests r13", `r13/`)
A: jaw + pointed chin head. B: modelled eyes; `render.face_eyes` places each eye at its projected eye. C: puffy loops on spring chains. D: gait `sway`, ponytail +/-1.8 px walk (legacy +/-0.2). E: two 1-px overrides.

## Not done / caveats
- Rust is about 1.5x legacy (the hem top row is fully rust).
- Not touched: Anim5, Anim6, throw E bow mix, climb NW strays.
- Bouncing loops are excluded from the height QA.
- No `releases/S4_hd_actions_v1` yet.
