# GATES — build 20261029_3831ac8

Gates (reported, not blocking): pxeval seq on the final 1x frames (P chain + F face) — boil ≤ 0.02, shade_swap ≤ 0.015, feet_range ≤ 2 px (loops only; in SE/E/NE and the other off-axis views a real stride projects ~5–7 px lower at 30° elevation, so FEET there is partly perspective, P notes), seam_ratio ≤ 1.5 (loops); P's limb audit (VANISHED/SPLIT/THIN/DETACHED, failed frames / frames); GIF = render/gifcheck.py (loop=0, ≥20 ms, disposal/ghosting, seam, dup frames) + REVIEW/build.py gif_check on the per-direction 4x GIF.

| clip | boil | shade_swap | feet px | seam | limb audit | GIF | bangs (skin px above brow, max / bad frames) | other pxeval flags | notes |
|---|---|---|---|---|---|---|---|---|---|
| walk S | 0.021 **FAIL** | 0.026 **FAIL** | 3 **FAIL** | 0.96 PASS | PASS | PASS | 13 / 8/8 **FAIL** |  |  |
| walk SE | 0.015 PASS | 0.046 **FAIL** | 5 FAIL (persp.) | 0.85 PASS | **FAIL** 1/8 DETACHED | PASS | 26 / 7/8 **FAIL** |  |  |
| walk E | 0.044 **FAIL** | 0.045 **FAIL** | 5 FAIL (persp.) | 0.63 PASS | PASS | PASS | 0 / 0/8 PASS |  |  |
| walk NE | 0.032 **FAIL** | 0.048 **FAIL** | 6 FAIL (persp.) | 0.74 PASS | PASS | PASS | 0 / 0/8 PASS |  |  |
| walk N | 0.014 PASS | 0.052 **FAIL** | 6 **FAIL** | 0.92 PASS | PASS | PASS | 0 / 0/8 PASS |  |  |
| walk NW | 0.030 **FAIL** | 0.049 **FAIL** | 5 FAIL (persp.) | 0.92 PASS | PASS | PASS | 0 / 0/8 PASS |  |  |
| walk W | 0.044 **FAIL** | 0.039 **FAIL** | 4 FAIL (persp.) | 0.90 PASS | PASS | PASS | 0 / 0/8 PASS |  |  |
| walk SW | 0.016 PASS | 0.045 **FAIL** | 5 FAIL (persp.) | 0.88 PASS | PASS | PASS | 28 / 7/8 **FAIL** |  |  |
| run S | 0.041 **FAIL** | 0.037 **FAIL** | 10 **FAIL** | 0.92 PASS | PASS | PASS | 19 / 8/8 **FAIL** |  |  |
| run SE | 0.075 **FAIL** | 0.049 **FAIL** | 9 FAIL (persp.) | 0.70 PASS | **FAIL** 2/8 SPLIT | PASS | 25 / 8/8 **FAIL** |  |  |
| run E | 0.132 **FAIL** | 0.047 **FAIL** | 7 FAIL (persp.) | 0.87 PASS | PASS | PASS | 0 / 0/8 PASS |  |  |
| run NE | 0.107 **FAIL** | 0.053 **FAIL** | 6 FAIL (persp.) | 0.89 PASS | PASS | PASS | 0 / 0/8 PASS |  |  |
| run N | 0.030 **FAIL** | 0.072 **FAIL** | 9 **FAIL** | 0.98 PASS | PASS | PASS | 0 / 0/8 PASS |  |  |
| run NW | 0.106 **FAIL** | 0.056 **FAIL** | 6 FAIL (persp.) | 0.94 PASS | PASS | PASS | 0 / 0/8 PASS |  |  |
| run W | 0.134 **FAIL** | 0.048 **FAIL** | 7 FAIL (persp.) | 0.90 PASS | **FAIL** 1/8 THIN | PASS | 0 / 0/8 PASS |  |  |
| run SW | 0.072 **FAIL** | 0.055 **FAIL** | 9 FAIL (persp.) | 0.90 PASS | **FAIL** 2/8 SPLIT | PASS | 24 / 6/8 **FAIL** |  |  |
| idle S | 0.009 PASS | 0.017 **FAIL** | 3 **FAIL** | 0.59 PASS | PASS | PASS | 21 / 12/12 **FAIL** |  |  |
| idle SE | 0.009 PASS | 0.032 **FAIL** | 2 PASS | 0.65 PASS | PASS | PASS | 32 / 12/12 **FAIL** |  |  |
| idle E | 0.009 PASS | 0.036 **FAIL** | 1 PASS | 0.71 PASS | **FAIL** 1/12 VANISHED | PASS | 11 / 3/12 **FAIL** |  |  |
| idle NE | 0.011 PASS | 0.035 **FAIL** | 2 PASS | 0.66 PASS | PASS | PASS | 0 / 0/12 PASS |  |  |
| idle N | 0.006 PASS | 0.037 **FAIL** | 3 **FAIL** | 0.62 PASS | PASS | PASS | 0 / 0/12 PASS |  |  |
| idle NW | 0.011 PASS | 0.036 **FAIL** | 1 PASS | 0.68 PASS | PASS | PASS | 0 / 0/12 PASS |  |  |
| idle W | 0.011 PASS | 0.041 **FAIL** | 1 PASS | 0.63 PASS | PASS | PASS | 0 / 0/12 PASS |  |  |
| idle SW | 0.008 PASS | 0.032 **FAIL** | 2 PASS | 0.58 PASS | PASS | PASS | 27 / 11/12 **FAIL** |  |  |
| jump S | 0.087 **FAIL** | 0.036 **FAIL** | n/a | 0.15 n/a | **FAIL** 4/16 DETACHED/SPLIT | PASS | 19 / 16/16 **FAIL** |  |  |
| jump SE | 0.072 **FAIL** | 0.051 **FAIL** | n/a | 0.25 n/a | PASS | PASS | 25 / 15/16 **FAIL** |  |  |
| jump E | 0.064 **FAIL** | 0.054 **FAIL** | n/a | 0.25 n/a | **FAIL** 1/16 VANISHED | PASS | 0 / 0/16 PASS |  |  |
| jump NE | 0.071 **FAIL** | 0.048 **FAIL** | n/a | 0.24 n/a | **FAIL** 2/16 THIN | PASS | 0 / 0/16 PASS |  |  |
| jump N | 0.075 **FAIL** | 0.048 **FAIL** | n/a | 0.19 n/a | PASS | PASS | 0 / 0/16 PASS |  |  |
| jump NW | 0.071 **FAIL** | 0.057 **FAIL** | n/a | 0.27 n/a | PASS | PASS | 0 / 0/16 PASS |  |  |
| jump W | 0.061 **FAIL** | 0.058 **FAIL** | n/a | 0.25 n/a | **FAIL** 1/16 THIN | PASS | 0 / 0/16 PASS |  |  |
| jump SW | 0.075 **FAIL** | 0.049 **FAIL** | n/a | 0.21 n/a | PASS | PASS | 22 / 10/16 **FAIL** |  |  |
| dash S | 0.013 PASS | 0.021 **FAIL** | n/a | 0.29 n/a | **FAIL** 3/13 DETACHED/SPLIT | PASS | 20 / 13/13 **FAIL** |  |  |
| dash SE | 0.037 **FAIL** | 0.031 **FAIL** | n/a | 0.28 n/a | PASS | PASS | 24 / 12/13 **FAIL** |  |  |
| dash E | 0.063 **FAIL** | 0.040 **FAIL** | n/a | 0.35 n/a | PASS | PASS | 0 / 0/13 PASS |  |  |
| dash NE | 0.060 **FAIL** | 0.044 **FAIL** | n/a | 0.31 n/a | PASS | PASS | 0 / 0/13 PASS |  |  |
| dash N | 0.035 **FAIL** | 0.046 **FAIL** | n/a | 0.19 n/a | PASS | PASS | 0 / 0/13 PASS |  |  |
| dash NW | 0.071 **FAIL** | 0.041 **FAIL** | n/a | 0.31 n/a | PASS | PASS | 0 / 0/13 PASS |  |  |
| dash W | 0.069 **FAIL** | 0.037 **FAIL** | n/a | 0.30 n/a | PASS | PASS | 0 / 0/13 PASS |  |  |
| dash SW | 0.038 **FAIL** | 0.033 **FAIL** | n/a | 0.28 n/a | **FAIL** 2/13 SPLIT | PASS | 25 / 8/13 **FAIL** |  |  |
| hurt S | 0.041 **FAIL** | 0.017 **FAIL** | n/a | 0.16 n/a | **FAIL** 3/9 DETACHED/SPLIT | PASS | 27 / 9/9 **FAIL** |  |  |
| hurt SE | 0.038 **FAIL** | 0.029 **FAIL** | n/a | 0.14 n/a | PASS | PASS | 28 / 8/9 **FAIL** |  |  |
| hurt E | 0.036 **FAIL** | 0.041 **FAIL** | n/a | 0.17 n/a | PASS | PASS | 0 / 0/9 PASS |  |  |
| hurt NE | 0.026 **FAIL** | 0.042 **FAIL** | n/a | 0.21 n/a | PASS | PASS | 0 / 0/9 PASS |  |  |
| hurt N | 0.036 **FAIL** | 0.049 **FAIL** | n/a | 0.26 n/a | PASS | PASS | 0 / 0/9 PASS |  |  |
| hurt NW | 0.054 **FAIL** | 0.051 **FAIL** | n/a | 0.17 n/a | PASS | PASS | 0 / 0/9 PASS |  |  |
| hurt W | 0.047 **FAIL** | 0.053 **FAIL** | n/a | 0.18 n/a | PASS | PASS | 7 / 1/9 **FAIL** |  |  |
| hurt SW | 0.036 **FAIL** | 0.037 **FAIL** | n/a | 0.15 n/a | **FAIL** 1/9 SPLIT | PASS | 27 / 7/9 **FAIL** |  |  |

## Posture gates (E profile; round 5 B + addendum)

torso pitch = pelvis->neck base vs vertical, **+ = forward** (gate idle/walk: every frame >= 0); head pitch = head bone vs vertical, **+ = chin down** (gate idle/walk: -3..+8 = level to slightly down); both measured in Blender on the motion (release/rl_pose.py, same pose application as render_motion.py). head forward = E-view head centre x - neck base x (1x px, her front = +x), gate every frame of every action >= 0. torso(px) = the same angle from the E projection (cross-check).

| action (E motion) | torso pitch min / mean / max | torso (px) min | head pitch min / max | head fwd px min | head fwd mm min | torso gate | head gate | head-forward gate |
|---|---|---|---|---|---|---|---|---|
| walk (blender) | +3.0 / +3.3 / +3.6° | 2.7° | +1.2 / +5.2° | 0.5 | 30 | PASS | PASS | PASS |
| run (blender) | +12.3 / +13.2 / +14.2° | 12.0° | +0.7 / +9.8° | 1.1 | 38 | n/a | n/a | PASS |
| idle (blender) | +0.3 / +0.8 / +1.3° | 0.1° | +1.1 / +4.5° | 0.3 | 27 | PASS | PASS | PASS |
| jump (blender) | +0.0 / +3.8 / +12.0° | -0.3° | +1.3 / +9.3° | 0.3 | 26 | n/a | n/a | PASS |
| dash (blender) | -8.5 / +6.1 / +26.0° | -8.7° | +1.9 / +8.3° | 0.5 | 30 | n/a | n/a | PASS |
| hurt (blender) | -18.6 / -4.0 / +7.1° | -19.9° | +2.0 / +5.7° | 0.5 | 30 | n/a | n/a | PASS |

Per-frame values: gates.json -> posture.<act>.frames.

**Totals (pass / gated clips):** boil 12/48, shade 0/48, feet 6/24, seam 24/24, limbs 35/48, gif 48/48, bangs 28/48; posture (actions): torso 2/2, head 2/2, head_fwd 6/6

## All GIFs in the build: 108 checked, 0 flagged

- none flagged (loop=0, min frame ≥ 20 ms, disposal 2 full frames, seam ok).
