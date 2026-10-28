# GATES — build 20261029_29614c2

Gates (reported, not blocking): pxeval seq on the final 1x frames (P chain + F face) — boil ≤ 0.02, shade_swap ≤ 0.015, feet_range ≤ 2 px (loops only; in SE/E/NE and the other off-axis views a real stride projects ~5–7 px lower at 30° elevation, so FEET there is partly perspective, P notes), seam_ratio ≤ 1.5 (loops); P's limb audit (VANISHED/SPLIT/THIN/DETACHED, failed frames / frames); GIF = render/gifcheck.py (loop=0, ≥20 ms, disposal/ghosting, seam, dup frames) + REVIEW/build.py gif_check on the per-direction 4x GIF.

| clip | boil | shade_swap | feet px | seam | limb audit | GIF | bangs (skin px above brow, max / bad frames) | other pxeval flags | notes |
|---|---|---|---|---|---|---|---|---|---|
| walk S | 0.018 PASS | 0.025 **FAIL** | 3 **FAIL** | 0.98 PASS | PASS | PASS | 89 / 8/8 **FAIL** |  |  |
| walk SE | 0.022 **FAIL** | 0.026 **FAIL** | 5 FAIL (persp.) | 0.82 PASS | **FAIL** 1/8 DETACHED | PASS | 41 / 7/8 **FAIL** |  |  |
| walk E | 0.042 **FAIL** | 0.026 **FAIL** | 5 FAIL (persp.) | 0.73 PASS | PASS | PASS | 0 / 0/8 PASS |  |  |
| walk NE | 0.038 **FAIL** | 0.028 **FAIL** | 6 FAIL (persp.) | 0.82 PASS | PASS | PASS | 0 / 0/8 PASS |  |  |
| walk N | 0.015 PASS | 0.035 **FAIL** | 6 **FAIL** | 0.88 PASS | PASS | PASS | 0 / 0/8 PASS |  |  |
| walk NW | 0.035 **FAIL** | 0.029 **FAIL** | 5 FAIL (persp.) | 0.93 PASS | PASS | PASS | 0 / 0/8 PASS |  |  |
| walk W | 0.043 **FAIL** | 0.024 **FAIL** | 4 FAIL (persp.) | 0.93 PASS | PASS | PASS | 0 / 0/8 PASS |  |  |
| walk SW | 0.022 **FAIL** | 0.028 **FAIL** | 5 FAIL (persp.) | 0.86 PASS | PASS | PASS | 53 / 8/8 **FAIL** |  |  |
| run S | 0.035 **FAIL** | 0.039 **FAIL** | 10 **FAIL** | 1.01 PASS | PASS | PASS | 164 / 8/8 **FAIL** |  |  |
| run SE | 0.080 **FAIL** | 0.029 **FAIL** | 9 FAIL (persp.) | 0.78 PASS | **FAIL** 2/8 SPLIT | PASS | 127 / 8/8 **FAIL** |  |  |
| run E | 0.148 **FAIL** | 0.027 **FAIL** | 7 FAIL (persp.) | 0.88 PASS | PASS | PASS | 0 / 0/8 PASS |  |  |
| run NE | 0.130 **FAIL** | 0.027 **FAIL** | 6 FAIL (persp.) | 0.89 PASS | PASS | PASS | 0 / 0/8 PASS |  |  |
| run N | 0.038 **FAIL** | 0.048 **FAIL** | 9 **FAIL** | 0.96 PASS | PASS | PASS | 0 / 0/8 PASS |  |  |
| run NW | 0.129 **FAIL** | 0.031 **FAIL** | 6 FAIL (persp.) | 0.95 PASS | PASS | PASS | 0 / 0/8 PASS |  |  |
| run W | 0.148 **FAIL** | 0.028 **FAIL** | 7 FAIL (persp.) | 0.93 PASS | **FAIL** 1/8 THIN | PASS | 0 / 0/8 PASS |  |  |
| run SW | 0.079 **FAIL** | 0.039 **FAIL** | 9 FAIL (persp.) | 0.96 PASS | **FAIL** 1/8 SPLIT | PASS | 126 / 8/8 **FAIL** |  |  |
| idle S | 0.015 PASS | 0.016 **FAIL** | 1 PASS | 0.61 PASS | **FAIL** 2/12 SPLIT | PASS | 155 / 12/12 **FAIL** |  |  |
| idle SE | 0.020 PASS | 0.018 **FAIL** | 2 PASS | 0.61 PASS | PASS | PASS | 163 / 12/12 **FAIL** |  |  |
| idle E | 0.013 PASS | 0.016 **FAIL** | 1 PASS | 0.62 PASS | PASS | PASS | 102 / 4/12 **FAIL** |  |  |
| idle NE | 0.015 PASS | 0.016 **FAIL** | 2 PASS | 0.59 PASS | PASS | PASS | 0 / 0/12 PASS |  |  |
| idle N | 0.011 PASS | 0.017 **FAIL** | 3 **FAIL** | 0.55 PASS | PASS | PASS | 0 / 0/12 PASS |  |  |
| idle NW | 0.013 PASS | 0.018 **FAIL** | 1 PASS | 0.55 PASS | PASS | PASS | 0 / 0/12 PASS |  |  |
| idle W | 0.017 PASS | 0.018 **FAIL** | 2 PASS | 0.57 PASS | PASS | PASS | 0 / 0/12 PASS |  |  |
| idle SW | 0.019 PASS | 0.016 **FAIL** | 2 PASS | 0.61 PASS | PASS | PASS | 124 / 11/12 **FAIL** |  |  |
| jump S | 0.090 **FAIL** | 0.037 **FAIL** | n/a | 0.20 n/a | **FAIL** 4/16 DETACHED/SPLIT | PASS | 157 / 16/16 **FAIL** |  |  |
| jump SE | 0.081 **FAIL** | 0.030 **FAIL** | n/a | 0.26 n/a | PASS | PASS | 104 / 16/16 **FAIL** |  |  |
| jump E | 0.065 **FAIL** | 0.026 **FAIL** | n/a | 0.30 n/a | PASS | PASS | 0 / 0/16 PASS |  |  |
| jump NE | 0.075 **FAIL** | 0.023 **FAIL** | n/a | 0.28 n/a | **FAIL** 2/16 THIN | PASS | 0 / 0/16 PASS |  |  |
| jump N | 0.080 **FAIL** | 0.031 **FAIL** | n/a | 0.20 n/a | PASS | PASS | 0 / 0/16 PASS |  |  |
| jump NW | 0.077 **FAIL** | 0.029 **FAIL** | n/a | 0.31 n/a | **FAIL** 1/16 THIN | PASS | 0 / 0/16 PASS |  |  |
| jump W | 0.063 **FAIL** | 0.034 **FAIL** | n/a | 0.31 n/a | PASS | PASS | 0 / 0/16 PASS |  |  |
| jump SW | 0.085 **FAIL** | 0.032 **FAIL** | n/a | 0.21 n/a | **FAIL** 3/16 SPLIT | PASS | 97 / 16/16 **FAIL** |  |  |
| dash S | 0.011 PASS | 0.019 **FAIL** | n/a | 0.31 n/a | **FAIL** 4/13 DETACHED/SPLIT | PASS | 136 / 13/13 **FAIL** |  |  |
| dash SE | 0.035 **FAIL** | 0.018 **FAIL** | n/a | 0.27 n/a | PASS | PASS | 88 / 13/13 **FAIL** |  |  |
| dash E | 0.040 **FAIL** | 0.024 **FAIL** | n/a | 0.30 n/a | **FAIL** 1/13 SPLIT | PASS | 0 / 0/13 PASS |  |  |
| dash NE | 0.040 **FAIL** | 0.025 **FAIL** | n/a | 0.27 n/a | PASS | PASS | 0 / 0/13 PASS |  |  |
| dash N | 0.040 **FAIL** | 0.025 **FAIL** | n/a | 0.23 n/a | PASS | PASS | 0 / 0/13 PASS |  |  |
| dash NW | 0.045 **FAIL** | 0.021 **FAIL** | n/a | 0.28 n/a | PASS | PASS | 0 / 0/13 PASS |  |  |
| dash W | 0.045 **FAIL** | 0.024 **FAIL** | n/a | 0.25 n/a | PASS | PASS | 0 / 0/13 PASS |  |  |
| dash SW | 0.037 **FAIL** | 0.023 **FAIL** | n/a | 0.26 n/a | **FAIL** 3/13 SPLIT | PASS | 84 / 13/13 **FAIL** |  |  |
| hurt S | 0.106 **FAIL** | 0.015 **FAIL** | n/a | 0.23 n/a | **FAIL** 3/9 DETACHED/SPLIT | PASS | 146 / 9/9 **FAIL** |  |  |
| hurt SE | 0.094 **FAIL** | 0.018 **FAIL** | n/a | 0.20 n/a | PASS | PASS | 111 / 8/9 **FAIL** |  |  |
| hurt E | 0.044 **FAIL** | 0.025 **FAIL** | n/a | 0.20 n/a | PASS | PASS | 0 / 0/9 PASS |  |  |
| hurt NE | 0.046 **FAIL** | 0.026 **FAIL** | n/a | 0.19 n/a | **FAIL** 2/9 VANISHED | PASS | 0 / 0/9 PASS |  |  |
| hurt N | 0.067 **FAIL** | 0.023 **FAIL** | n/a | 0.32 n/a | PASS | PASS | 0 / 0/9 PASS |  |  |
| hurt NW | 0.057 **FAIL** | 0.031 **FAIL** | n/a | 0.22 n/a | PASS | PASS | 0 / 0/9 PASS |  |  |
| hurt W | 0.062 **FAIL** | 0.033 **FAIL** | n/a | 0.17 n/a | PASS | PASS | 102 / 3/9 **FAIL** |  |  |
| hurt SW | 0.102 **FAIL** | 0.017 **FAIL** | n/a | 0.18 n/a | PASS | PASS | 131 / 9/9 **FAIL** |  |  |

## Posture gates (E profile; round 5 B + addendum)

torso pitch = pelvis->neck base vs vertical, **+ = forward** (gate idle/walk: every frame >= 0); head pitch = head bone vs vertical, **+ = chin down** (gate idle/walk: -3..+8 = level to slightly down); both measured in Blender on the motion (release/rl_pose.py, same pose application as render_motion.py). head forward = E-view head centre x - neck base x (1x px, her front = +x), gate every frame of every action >= 0. torso(px) = the same angle from the E projection (cross-check).

| action (E motion) | torso pitch min / mean / max | torso (px) min | head pitch min / max | head fwd px min | head fwd mm min | torso gate | head gate | head-forward gate |
|---|---|---|---|---|---|---|---|---|
| walk (blender) | +3.0 / +3.3 / +3.6° | 2.9° | +1.2 / +5.2° | 2.1 | 30 | PASS | PASS | PASS |
| run (blender) | +12.3 / +13.2 / +14.2° | 12.3° | +0.7 / +9.8° | 2.6 | 38 | n/a | n/a | PASS |
| idle (blender) | +0.3 / +0.7 / +1.3° | 0.3° | +0.8 / +4.5° | 1.8 | 26 | PASS | PASS | PASS |
| jump (blender) | +0.0 / +3.8 / +12.0° | 0.0° | +1.3 / +9.3° | 1.8 | 26 | n/a | n/a | PASS |
| dash (blender) | -8.5 / +6.1 / +26.0° | -8.4° | +1.9 / +8.3° | 2.0 | 30 | n/a | n/a | PASS |
| hurt (blender) | -18.6 / -4.0 / +7.1° | -19.6° | +2.0 / +5.7° | 2.0 | 30 | n/a | n/a | PASS |

Per-frame values: gates.json -> posture.<act>.frames.

**Totals (pass / gated clips):** boil 11/48, shade 0/48, feet 7/24, seam 24/24, limbs 34/48, gif 48/48, bangs 28/48; posture (actions): torso 2/2, head 2/2, head_fwd 6/6

## All GIFs in the build: 108 checked, 0 flagged

- none flagged (loop=0, min frame ≥ 20 ms, disposal 2 full frames, seam ok).
