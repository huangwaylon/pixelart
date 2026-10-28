# GATES — build 20261028_09af554

Gates (reported, not blocking): pxeval seq on the final 1x frames (P chain + F face) — boil ≤ 0.02, shade_swap ≤ 0.015, feet_range ≤ 2 px (loops only; in SE/E/NE and the other off-axis views a real stride projects ~5–7 px lower at 30° elevation, so FEET there is partly perspective, P notes), seam_ratio ≤ 1.5 (loops); P's limb audit (VANISHED/SPLIT/THIN/DETACHED, failed frames / frames); GIF = render/gifcheck.py (loop=0, ≥20 ms, disposal/ghosting, seam, dup frames) + REVIEW/build.py gif_check on the per-direction 4x GIF.

| clip | boil | shade_swap | feet px | seam | limb audit | GIF | other pxeval flags | notes |
|---|---|---|---|---|---|---|---|---|
| walk S | 0.014 PASS | 0.029 **FAIL** | 3 **FAIL** | 1.01 PASS | PASS | PASS |  |  |
| walk SE | 0.018 PASS | 0.041 **FAIL** | 5 FAIL (persp.) | 0.74 PASS | **FAIL** 1/8 THIN | PASS |  |  |
| walk E | 0.040 **FAIL** | 0.033 **FAIL** | 5 FAIL (persp.) | 0.72 PASS | PASS | PASS |  |  |
| walk NE | 0.033 **FAIL** | 0.037 **FAIL** | 6 FAIL (persp.) | 0.75 PASS | PASS | PASS |  |  |
| walk N | 0.015 PASS | 0.035 **FAIL** | 6 **FAIL** | 0.90 PASS | PASS | PASS |  | preview failed: ValueError('min() iterable argument is empty') |
| walk NW | 0.033 **FAIL** | 0.040 **FAIL** | 5 FAIL (persp.) | 0.96 PASS | PASS | PASS |  |  |
| walk W | 0.041 **FAIL** | 0.033 **FAIL** | 4 FAIL (persp.) | 0.93 PASS | PASS | PASS |  |  |
| walk SW | 0.019 PASS | 0.040 **FAIL** | 5 FAIL (persp.) | 0.80 PASS | PASS | PASS |  |  |
| run S | 0.037 **FAIL** | 0.042 **FAIL** | 10 **FAIL** | 0.94 PASS | **FAIL** 1/8 THIN | PASS |  |  |
| run SE | 0.073 **FAIL** | 0.046 **FAIL** | 9 FAIL (persp.) | 0.75 PASS | **FAIL** 3/8 SPLIT | PASS |  |  |
| run NE | 0.116 **FAIL** | 0.042 **FAIL** | 6 FAIL (persp.) | 0.89 PASS | PASS | PASS |  |  |
| run N | 0.031 **FAIL** | 0.060 **FAIL** | 9 **FAIL** | 1.00 PASS | PASS | PASS |  | preview failed: ValueError('min() iterable argument is empty') |
| run NW | 0.120 **FAIL** | 0.045 **FAIL** | 6 FAIL (persp.) | 0.89 PASS | PASS | PASS |  |  |
| run W | 0.146 **FAIL** | 0.040 **FAIL** | 7 FAIL (persp.) | 0.90 PASS | PASS | PASS |  |  |
| run SW | 0.069 **FAIL** | 0.051 **FAIL** | 9 FAIL (persp.) | 0.90 PASS | **FAIL** 2/8 SPLIT | PASS |  |  |
| idle S | 0.015 PASS | 0.018 **FAIL** | 2 PASS | 0.64 PASS | **FAIL** 1/12 DETACHED/SPLIT | PASS |  |  |
| idle SE | 0.014 PASS | 0.031 **FAIL** | 2 PASS | 0.68 PASS | PASS | PASS |  |  |
| idle E | 0.013 PASS | 0.029 **FAIL** | 1 PASS | 0.73 PASS | PASS | PASS |  |  |
| idle NE | 0.013 PASS | 0.027 **FAIL** | 2 PASS | 0.73 PASS | PASS | PASS |  |  |
| idle N | 0.016 PASS | 0.029 **FAIL** | 3 **FAIL** | 0.62 PASS | PASS | PASS |  | preview failed: ValueError('min() iterable argument is empty') |
| idle NW | 0.014 PASS | 0.026 **FAIL** | 1 PASS | 0.60 PASS | PASS | PASS |  |  |
| idle W | 0.014 PASS | 0.030 **FAIL** | 3 FAIL (persp.) | 0.66 PASS | PASS | PASS |  |  |
| idle SW | 0.013 PASS | 0.029 **FAIL** | 2 PASS | 0.64 PASS | PASS | PASS |  |  |
| jump S | 0.094 **FAIL** | 0.034 **FAIL** | n/a | 0.29 n/a | **FAIL** 7/16 DETACHED/SPLIT/THIN | PASS |  |  |
| jump SE | 0.082 **FAIL** | 0.047 **FAIL** | n/a | 0.47 n/a | **FAIL** 2/16 SPLIT/THIN | PASS |  |  |
| jump E | 0.072 **FAIL** | 0.046 **FAIL** | n/a | 0.58 n/a | **FAIL** 2/16 THIN | PASS |  |  |
| jump NE | 0.076 **FAIL** | 0.040 **FAIL** | n/a | 0.50 n/a | **FAIL** 3/16 THIN | PASS |  |  |
| jump N | 0.064 **FAIL** | 0.038 **FAIL** | n/a | 0.37 n/a | PASS | PASS |  | preview failed: ValueError('min() iterable argument is empty') |
| jump NW | 0.076 **FAIL** | 0.046 **FAIL** | n/a | 0.54 n/a | **FAIL** 1/16 THIN | PASS |  |  |
| jump W | 0.063 **FAIL** | 0.046 **FAIL** | n/a | 0.49 n/a | **FAIL** 2/16 THIN | PASS |  |  |
| jump SW | 0.076 **FAIL** | 0.049 **FAIL** | n/a | 0.44 n/a | **FAIL** 1/16 THIN | PASS |  |  |
| dash S | 0.018 PASS | 0.019 **FAIL** | n/a | 0.27 n/a | **FAIL** 4/13 DETACHED/SPLIT | PASS |  |  |
| dash SE | 0.039 **FAIL** | 0.030 **FAIL** | n/a | 0.24 n/a | **FAIL** 3/13 SPLIT/THIN | PASS |  |  |
| dash E | 0.043 **FAIL** | 0.034 **FAIL** | n/a | 0.35 n/a | **FAIL** 1/13 SPLIT | PASS |  |  |
| dash NE | 0.043 **FAIL** | 0.040 **FAIL** | n/a | 0.27 n/a | PASS | PASS |  |  |
| dash N | 0.042 **FAIL** | 0.037 **FAIL** | n/a | 0.24 n/a | PASS | PASS |  | preview failed: ValueError('min() iterable argument is empty') |
| dash W | 0.049 **FAIL** | 0.035 **FAIL** | n/a | 0.35 n/a | PASS | PASS |  |  |
| dash SW | 0.043 **FAIL** | 0.034 **FAIL** | n/a | 0.32 n/a | **FAIL** 2/13 SPLIT | PASS |  |  |
| hurt S | 0.118 **FAIL** | 0.012 PASS | n/a | 0.18 n/a | **FAIL** 3/9 DETACHED/SPLIT | PASS |  |  |
| hurt SE | 0.108 **FAIL** | 0.023 **FAIL** | n/a | 0.16 n/a | PASS | PASS |  |  |
| hurt E | 0.048 **FAIL** | 0.035 **FAIL** | n/a | 0.21 n/a | PASS | PASS |  |  |
| hurt NE | 0.047 **FAIL** | 0.034 **FAIL** | n/a | 0.28 n/a | PASS | PASS |  |  |
| hurt N | 0.055 **FAIL** | 0.033 **FAIL** | n/a | 0.20 n/a | PASS | PASS |  | preview failed: ValueError('min() iterable argument is empty') |
| hurt NW | 0.047 **FAIL** | 0.047 **FAIL** | n/a | 0.20 n/a | PASS | PASS |  |  |
| hurt W | 0.045 **FAIL** | 0.044 **FAIL** | n/a | 0.23 n/a | **FAIL** 1/9 THIN | PASS |  |  |
| hurt SW | 0.097 **FAIL** | 0.025 **FAIL** | n/a | 0.18 n/a | **FAIL** 1/9 SPLIT | PASS |  |  |
| run E | - n/a | - n/a | n/a | - n/a | n/a | **FAIL** NOT_BUILT |  | P pixel_chain failed (see clip.log): ValueError: zero-size array to reduction operation minimum which has no identity |
| dash NW | - n/a | - n/a | n/a | - n/a | n/a | **FAIL** NOT_BUILT |  | P pixel_chain failed (see clip.log): ValueError: zero-size array to reduction operation minimum which has no identity |

**Totals (pass / gated clips):** boil 13/46, shade 1/46, feet 6/23, seam 23/23, limbs 27/46, gif 46/48

## All GIFs in the build: 98 checked, 0 flagged

- none flagged (loop=0, min frame ≥ 20 ms, disposal 2 full frames, seam ok).
