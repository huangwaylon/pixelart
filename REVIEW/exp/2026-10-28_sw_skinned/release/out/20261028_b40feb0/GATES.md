# GATES — build 20261028_b40feb0

Gates (reported, not blocking): pxeval seq on the final 1x frames (P chain + F face) — boil ≤ 0.02, shade_swap ≤ 0.015, feet_range ≤ 2 px (loops only; in SE/E/NE and the other off-axis views a real stride projects ~5–7 px lower at 30° elevation, so FEET there is partly perspective, P notes), seam_ratio ≤ 1.5 (loops); P's limb audit (VANISHED/SPLIT/THIN/DETACHED, failed frames / frames); GIF = render/gifcheck.py (loop=0, ≥20 ms, disposal/ghosting, seam, dup frames) + REVIEW/build.py gif_check on the per-direction 4x GIF.

| clip | boil | shade_swap | feet px | seam | limb audit | GIF | bangs (skin px above brow, max / bad frames) | other pxeval flags | notes |
|---|---|---|---|---|---|---|---|---|---|
| walk S | 0.017 PASS | 0.027 **FAIL** | 3 **FAIL** | 0.94 PASS | PASS | PASS | 92 / 8/8 **FAIL** |  |  |
| walk SE | 0.022 **FAIL** | 0.026 **FAIL** | 5 FAIL (persp.) | 0.75 PASS | **FAIL** 1/8 DETACHED | PASS | 49 / 8/8 **FAIL** |  |  |
| walk E | 0.042 **FAIL** | 0.028 **FAIL** | 5 FAIL (persp.) | 0.77 PASS | PASS | PASS | 1 / 1/8 **FAIL** |  |  |
| walk NE | 0.038 **FAIL** | 0.028 **FAIL** | 6 FAIL (persp.) | 0.82 PASS | PASS | PASS | 0 / 0/8 PASS |  |  |
| walk N | 0.018 PASS | 0.031 **FAIL** | 6 **FAIL** | 0.92 PASS | PASS | PASS | 0 / 0/8 PASS |  |  |
| walk NW | 0.038 **FAIL** | 0.029 **FAIL** | 5 FAIL (persp.) | 0.97 PASS | PASS | PASS | 0 / 0/8 PASS |  |  |
| walk W | 0.043 **FAIL** | 0.025 **FAIL** | 4 FAIL (persp.) | 0.91 PASS | PASS | PASS | 0 / 0/8 PASS |  |  |
| walk SW | 0.024 **FAIL** | 0.025 **FAIL** | 5 FAIL (persp.) | 0.87 PASS | PASS | PASS | 46 / 7/8 **FAIL** |  |  |
| run S | 0.036 **FAIL** | 0.039 **FAIL** | 10 **FAIL** | 0.99 PASS | PASS | PASS | 150 / 8/8 **FAIL** |  |  |
| run SE | 0.080 **FAIL** | 0.030 **FAIL** | 9 FAIL (persp.) | 0.79 PASS | **FAIL** 2/8 SPLIT | PASS | 120 / 8/8 **FAIL** |  |  |
| run E | 0.147 **FAIL** | 0.029 **FAIL** | 7 FAIL (persp.) | 0.89 PASS | PASS | PASS | 0 / 0/8 PASS |  |  |
| run NE | 0.126 **FAIL** | 0.027 **FAIL** | 6 FAIL (persp.) | 0.89 PASS | PASS | PASS | 0 / 0/8 PASS |  |  |
| run N | 0.042 **FAIL** | 0.043 **FAIL** | 9 **FAIL** | 0.99 PASS | PASS | PASS | 0 / 0/8 PASS |  |  |
| run NW | 0.128 **FAIL** | 0.031 **FAIL** | 6 FAIL (persp.) | 0.97 PASS | PASS | PASS | 0 / 0/8 PASS |  |  |
| run W | 0.149 **FAIL** | 0.029 **FAIL** | 7 FAIL (persp.) | 0.94 PASS | **FAIL** 1/8 THIN | PASS | 0 / 0/8 PASS |  |  |
| run SW | 0.078 **FAIL** | 0.039 **FAIL** | 9 FAIL (persp.) | 0.97 PASS | **FAIL** 1/8 SPLIT | PASS | 110 / 8/8 **FAIL** |  |  |
| idle S | 0.016 PASS | 0.018 **FAIL** | 2 PASS | 0.63 PASS | PASS | PASS | 146 / 12/12 **FAIL** |  |  |
| idle SE | 0.017 PASS | 0.016 **FAIL** | 2 PASS | 0.60 PASS | PASS | PASS | 156 / 12/12 **FAIL** |  |  |
| idle E | 0.015 PASS | 0.015 **FAIL** | 1 PASS | 0.68 PASS | PASS | PASS | 96 / 4/12 **FAIL** |  |  |
| idle NE | 0.013 PASS | 0.017 **FAIL** | 2 PASS | 0.62 PASS | PASS | PASS | 0 / 0/12 PASS |  |  |
| idle N | 0.015 PASS | 0.020 **FAIL** | 3 **FAIL** | 0.55 PASS | PASS | PASS | 0 / 0/12 PASS |  |  |
| idle NW | 0.015 PASS | 0.017 **FAIL** | 1 PASS | 0.54 PASS | PASS | PASS | 0 / 0/12 PASS |  |  |
| idle W | 0.014 PASS | 0.018 **FAIL** | 2 PASS | 0.60 PASS | PASS | PASS | 0 / 0/12 PASS |  |  |
| idle SW | 0.017 PASS | 0.018 **FAIL** | 2 PASS | 0.61 PASS | PASS | PASS | 117 / 11/12 **FAIL** |  |  |
| jump S | 0.091 **FAIL** | 0.037 **FAIL** | n/a | 0.20 n/a | **FAIL** 5/16 DETACHED/SPLIT | PASS | 149 / 16/16 **FAIL** |  |  |
| jump SE | 0.084 **FAIL** | 0.029 **FAIL** | n/a | 0.25 n/a | **FAIL** 1/16 SPLIT | PASS | 99 / 15/16 **FAIL** |  |  |
| jump E | 0.062 **FAIL** | 0.031 **FAIL** | n/a | 0.28 n/a | PASS | PASS | 0 / 0/16 PASS |  |  |
| jump NE | 0.069 **FAIL** | 0.027 **FAIL** | n/a | 0.26 n/a | **FAIL** 2/16 THIN | PASS | 0 / 0/16 PASS |  |  |
| jump N | 0.077 **FAIL** | 0.028 **FAIL** | n/a | 0.21 n/a | PASS | PASS | 0 / 0/16 PASS |  |  |
| jump NW | 0.073 **FAIL** | 0.029 **FAIL** | n/a | 0.28 n/a | **FAIL** 1/16 THIN | PASS | 0 / 0/16 PASS |  |  |
| jump W | 0.064 **FAIL** | 0.034 **FAIL** | n/a | 0.29 n/a | PASS | PASS | 0 / 0/16 PASS |  |  |
| jump SW | 0.081 **FAIL** | 0.033 **FAIL** | n/a | 0.21 n/a | PASS | PASS | 94 / 16/16 **FAIL** |  |  |
| dash S | 0.014 PASS | 0.018 **FAIL** | n/a | 0.32 n/a | **FAIL** 4/13 DETACHED/SPLIT | PASS | 146 / 13/13 **FAIL** |  |  |
| dash SE | 0.037 **FAIL** | 0.018 **FAIL** | n/a | 0.28 n/a | PASS | PASS | 79 / 13/13 **FAIL** |  |  |
| dash E | 0.039 **FAIL** | 0.022 **FAIL** | n/a | 0.32 n/a | PASS | PASS | 0 / 0/13 PASS |  |  |
| dash NE | 0.040 **FAIL** | 0.024 **FAIL** | n/a | 0.27 n/a | PASS | PASS | 0 / 0/13 PASS |  |  |
| dash N | 0.039 **FAIL** | 0.025 **FAIL** | n/a | 0.23 n/a | PASS | PASS | 0 / 0/13 PASS |  |  |
| dash NW | 0.045 **FAIL** | 0.023 **FAIL** | n/a | 0.28 n/a | PASS | PASS | 0 / 0/13 PASS |  |  |
| dash W | 0.042 **FAIL** | 0.023 **FAIL** | n/a | 0.27 n/a | PASS | PASS | 0 / 0/13 PASS |  |  |
| dash SW | 0.039 **FAIL** | 0.025 **FAIL** | n/a | 0.26 n/a | **FAIL** 1/13 SPLIT | PASS | 79 / 11/13 **FAIL** |  |  |
| hurt S | 0.103 **FAIL** | 0.015 **FAIL** | n/a | 0.22 n/a | **FAIL** 3/9 DETACHED/SPLIT | PASS | 146 / 9/9 **FAIL** |  |  |
| hurt SE | 0.096 **FAIL** | 0.016 **FAIL** | n/a | 0.20 n/a | PASS | PASS | 108 / 9/9 **FAIL** |  |  |
| hurt E | 0.042 **FAIL** | 0.025 **FAIL** | n/a | 0.22 n/a | PASS | PASS | 0 / 0/9 PASS |  |  |
| hurt NE | 0.046 **FAIL** | 0.025 **FAIL** | n/a | 0.19 n/a | PASS | PASS | 0 / 0/9 PASS |  |  |
| hurt N | 0.064 **FAIL** | 0.019 **FAIL** | n/a | 0.32 n/a | PASS | PASS | 0 / 0/9 PASS |  |  |
| hurt NW | 0.055 **FAIL** | 0.028 **FAIL** | n/a | 0.23 n/a | PASS | PASS | 0 / 0/9 PASS |  |  |
| hurt W | 0.064 **FAIL** | 0.029 **FAIL** | n/a | 0.14 n/a | PASS | PASS | 93 / 2/9 **FAIL** |  |  |
| hurt SW | 0.100 **FAIL** | 0.019 **FAIL** | n/a | 0.16 n/a | PASS | PASS | 136 / 9/9 **FAIL** |  |  |

## Posture gates (E profile; round 5 B + addendum)

torso pitch = pelvis->neck base vs vertical, **+ = forward** (gate idle/walk: every frame >= 0); head pitch = head bone vs vertical, **+ = chin down** (gate idle/walk: -3..+8 = level to slightly down); both measured in Blender on the motion (release/rl_pose.py, same pose application as render_motion.py). head forward = E-view head centre x - neck base x (1x px, her front = +x), gate every frame of every action >= 0. torso(px) = the same angle from the E projection (cross-check).

| action (E motion) | torso pitch min / mean / max | torso (px) min | head pitch min / max | head fwd px min | head fwd mm min | torso gate | head gate | head-forward gate |
|---|---|---|---|---|---|---|---|---|
| walk (blender) | +1.4 / +1.7 / +2.0° | 1.4° | -0.6 / +5.2° | 1.4 | 21 | PASS | PASS | PASS |
| run (blender) | +12.3 / +13.2 / +14.2° | 12.3° | -1.4 / +7.8° | 2.1 | 31 | n/a | n/a | PASS |
| idle (blender) | +0.4 / +0.8 / +1.4° | 0.4° | +0.8 / +4.6° | 1.8 | 26 | PASS | PASS | PASS |
| jump (blender) | -5.3 / +2.4 / +12.0° | -5.3° | -1.0 / +9.3° | 1.4 | 21 | n/a | n/a | PASS |
| dash (blender) | -8.5 / +6.1 / +26.0° | -8.4° | +0.7 / +8.3° | 2.0 | 30 | n/a | n/a | PASS |
| hurt (blender) | -18.6 / -4.0 / +7.1° | -19.6° | +2.0 / +5.7° | 2.0 | 30 | n/a | n/a | PASS |

Per-frame values: gates.json -> posture.<act>.frames.

**Totals (pass / gated clips):** boil 11/48, shade 0/48, feet 7/24, seam 24/24, limbs 37/48, gif 48/48, bangs 27/48; posture (actions): torso 2/2, head 2/2, head_fwd 6/6

## All GIFs in the build: 108 checked, 0 flagged

- none flagged (loop=0, min frame ≥ 20 ms, disposal 2 full frames, seam ok).
