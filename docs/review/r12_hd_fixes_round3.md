# r12 HD round 3: fixes -> change -> evidence

Data: `pipeline/tools/make_s4_hd.py` -> `S4_hd.json`. New shared code is opt-in (S4_hd `render.*` keys). Legacy `_sheet.png` for idle, throw, carry_walk and walk is byte-identical to a fresh HEAD build. 13/13 QA PASS, 0 warnings, <= 16 colours. Crops: `00_REVIEW/r12_hd_model/fixes/r3_*.png`.

| # | Change | Evidence (legacy / round 2 / round 3) |
|---|---|---|
| 1 | `bow_shine`: 2 px teal_2 highlight + 1 teal_0 fold per loop | #6ACBB6 in idle: 0 / 0 / 160 px |
| 2 | Loops raised/tilted (y 11.8, 26 deg, length 3.4, taper .35); hair sel-out runs kept | S ears 4x2, mirrored, no nub |
| 3 | `follow.max_drop` clamp (world-up) | jump S f1 ears (L,R): (2,2) / (0,0) / (8,8) |
| 4 | Springs off in idle loops; hold covers the scarf tail | teal blips: S 36/51/8, SE 22/41/7, W 29/47/18 |
| 5 | Walk sway x1.15 with a flattened extreme | tip +/-2.0-2.2 px, held f2-3/f6-7; run unchanged |
| 6 | Cranium pulled in + `carry_idle/NW/00` override | NW skin_0: carry_idle f0 6 -> 0, throw f4 4 -> 0 |
| 7 | `ring_trim`: 2 px inside outline, 1 px off the bow, runs < 3 dropped | idle head rust 603 / 886 / 549; hem unchanged |
| 8 | `gap_front: 3` | S bridge 3 px in every frame of every clip |
| 9 | `mouth_bias: 1`; `skin_edge_dark` | SW far cheek outlined; SE stub gone |
| 10 | Ponytail is its own group (Anim5) | plum line separates it from the curtain |

**Release:** `releases/S4_hd_actions_v1/` (v1 untouched).

**Open:**
- Walk NE f7 -> f0 diff is 154 px vs legacy 124. It comes from the larger sway; the chain seam is 0.04 px.
- E/SE flat ponytail tip, throw E bow mix and climb NW strays are not done.
