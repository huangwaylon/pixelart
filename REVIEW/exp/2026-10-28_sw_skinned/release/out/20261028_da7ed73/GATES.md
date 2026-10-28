# GATES — build 20261028_da7ed73

Gates (reported, not blocking): pxeval seq on the final 1x frames (P chain + F face) — boil ≤ 0.02, shade_swap ≤ 0.015, feet_range ≤ 2 px (loops only; in SE/E/NE and the other off-axis views a real stride projects ~5–7 px lower at 30° elevation, so FEET there is partly perspective, P notes), seam_ratio ≤ 1.5 (loops); P's limb audit (VANISHED/SPLIT/THIN/DETACHED, failed frames / frames); GIF = render/gifcheck.py (loop=0, ≥20 ms, disposal/ghosting, seam, dup frames) + REVIEW/build.py gif_check on the per-direction 4x GIF.

| clip | boil | shade_swap | feet px | seam | limb audit | GIF | other pxeval flags | notes |
|---|---|---|---|---|---|---|---|---|
| walk S | 0.014 PASS | 0.029 **FAIL** | 3 **FAIL** | 1.00 PASS | PASS | PASS |  |  |
| walk SE | 0.018 PASS | 0.041 **FAIL** | 5 FAIL (persp.) | 0.73 PASS | **FAIL** 1/8 THIN | PASS |  |  |
| walk E | 0.040 **FAIL** | 0.034 **FAIL** | 5 FAIL (persp.) | 0.72 PASS | PASS | PASS |  |  |
| run S | 0.037 **FAIL** | 0.041 **FAIL** | 10 **FAIL** | 0.94 PASS | **FAIL** 1/8 THIN | PASS |  |  |
| run SE | 0.076 **FAIL** | 0.044 **FAIL** | 9 FAIL (persp.) | 0.83 PASS | **FAIL** 2/8 SPLIT/THIN | PASS |  |  |
| idle S | 0.015 PASS | 0.018 **FAIL** | 2 PASS | 0.64 PASS | **FAIL** 1/12 DETACHED/SPLIT | PASS |  |  |
| idle SE | 0.014 PASS | 0.031 **FAIL** | 2 PASS | 0.68 PASS | PASS | PASS |  |  |
| idle E | 0.012 PASS | 0.029 **FAIL** | 1 PASS | 0.73 PASS | **FAIL** 1/12 SPLIT | PASS |  |  |
| jump S | 0.095 **FAIL** | 0.034 **FAIL** | n/a | 0.28 n/a | **FAIL** 7/16 DETACHED/SPLIT/THIN | PASS |  |  |
| jump SE | 0.081 **FAIL** | 0.047 **FAIL** | n/a | 0.48 n/a | **FAIL** 2/16 SPLIT/THIN | PASS |  |  |
| jump E | 0.071 **FAIL** | 0.046 **FAIL** | n/a | 0.58 n/a | **FAIL** 2/16 THIN | PASS |  |  |
| dash S | 0.023 **FAIL** | 0.018 **FAIL** | n/a | 0.27 n/a | **FAIL** 5/13 DETACHED/SPLIT/THIN | PASS |  |  |
| dash SE | 0.036 **FAIL** | 0.025 **FAIL** | n/a | 0.30 n/a | **FAIL** 2/13 SPLIT | PASS |  |  |
| dash E | 0.069 **FAIL** | 0.034 **FAIL** | n/a | 0.35 n/a | **FAIL** 1/13 SPLIT | PASS |  |  |
| hurt S | 0.125 **FAIL** | 0.011 PASS | n/a | 0.16 n/a | **FAIL** 3/9 DETACHED/SPLIT | PASS |  |  |
| hurt SE | 0.106 **FAIL** | 0.023 **FAIL** | n/a | 0.15 n/a | PASS | PASS |  |  |
| hurt E | 0.044 **FAIL** | 0.034 **FAIL** | n/a | 0.31 n/a | **FAIL** 1/9 SPLIT | PASS |  |  |
| run E | - n/a | - n/a | n/a | - n/a | n/a | **FAIL** NOT_BUILT |  | P pixel_chain failed (see clip.log): ValueError: zero-size array to reduction operation minimum which has no identity |

**Totals (pass / gated clips):** boil 5/17, shade 1/17, feet 3/8, seam 8/8, limbs 4/17, gif 17/18

## All GIFs in the build: 46 checked, 0 flagged

- none flagged (loop=0, min frame ≥ 20 ms, disposal 2 full frames, seam ok).
