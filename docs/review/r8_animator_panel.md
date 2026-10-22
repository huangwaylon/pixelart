# r8 animator panel: jump_v2

Method: contact sheets plus a ChainSim re-run per build. Numbers are tip offset from rest (fraction of length) or tip direction (-1 hanging, +1 up).

**All except C4:** `scarf_front` flips up over the chin on f9-10 (+0.74) and again on f12. Cause: damping of 0.10-0.30 per 5 ms step kills the chain's velocity, so it lags when the anchor drops. Fix: `scarf_front {stiffness 250, damping 0.08, gravity 1200}` (f10 down to +0.29).

| | Score | Notes | chain_overrides |
|---|---|---|---|
| C1_twintails | **4** | Best follow-through: tails flare sideways on touchdown, cute. But stiff on launch (0.14), and the f10 flare snaps back in one frame (0.52 to 0.06), a pop. Hair hides the face in E/NE f1-2 and f10. | `tail_L/R {stiffness 300, damping 0.08, gravity 900}`: launch lag 0.34, softer f10, second flick on the f12 plop. |
| C2_hime_beret | **2** | Locks read as one block from N/NE. They flip fully up beside the cheeks on f10 (+0.92) and flick again on f12, which is noisy. | `lock_0/1/2 {stiffness 450, damping 0.08, gravity 1200}`: f10 +0.04, launch lag kept. |
| C3_sidepony_cat | **3** | Good launch lag (0.62), and the apex line curves. Pony points straight up in E/NE on f10 (+0.57). Mitten lost against the pony in W f3-7. | `pony {stiffness 200, damping 0.06, gravity 750}`: f10 +0.20. |
| C4_snow_hood | **2** | Clean squash and stretch, face always clear. No chains, so no overlap. | None possible. Needs an added chain (tassel or scarf tail). |
| C5_buns_ribbon | **3** | Clearest faces and gestures. Buns are rigid; the scarf is the only secondary motion. | Scarf fix only. A ribbon-tail chain would help. |
| C6_bob_nohat | **3** | Charming ahoge, but it droops below horizontal on f3-5. The bob pieces are single-segment and pinned by the collider (offset about 1.0 every frame), so they are rigid. | `ahoge {stiffness 420, damping 0.06}`. `bob_L/R {rest_dir [±0.5,-1,0.2], segments 2, seg_len 2.2, widths [3.18,2.8], damping 0.06}` gives real swing; AD to check silhouette. |

**Ranking:** C1 > C3 = C5 = C6 > C2 = C4. All values are sim-only; rebuild and QA before adopting.
