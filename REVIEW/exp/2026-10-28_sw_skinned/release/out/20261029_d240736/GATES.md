# GATES — build 20261029_d240736

Gates (reported, not blocking): pxeval seq on the final 1x frames (P chain + F face) — boil ≤ 0.02, shade_swap ≤ 0.015, feet_range ≤ 2 px (loops only; in SE/E/NE and the other off-axis views a real stride projects ~5–7 px lower at 30° elevation, so FEET there is partly perspective, P notes), seam_ratio ≤ 1.5 (loops); P's limb audit (VANISHED/SPLIT/THIN/DETACHED, failed frames / frames); GIF = render/gifcheck.py (loop=0, ≥20 ms, disposal/ghosting, seam, dup frames) + REVIEW/build.py gif_check on the per-direction 4x GIF.

| clip | boil | shade_swap | feet px | seam | limb audit | GIF | bangs (skin px above brow, max / bad frames) | other pxeval flags | notes |
|---|---|---|---|---|---|---|---|---|---|
| walk S | 0.018 PASS | 0.039 **FAIL** | 3 **FAIL** | 0.96 PASS | PASS | PASS | 0 / 0/8 PASS |  |  |
| walk SE | 0.015 PASS | 0.082 **FAIL** | 5 FAIL (persp.) | 0.84 PASS | PASS | PASS | 0 / 0/8 PASS |  |  |
| walk E | 0.037 **FAIL** | 0.052 **FAIL** | 5 FAIL (persp.) | 0.68 PASS | PASS | PASS | 0 / 0/8 PASS |  |  |
| walk NE | 0.027 **FAIL** | 0.067 **FAIL** | 6 FAIL (persp.) | 0.78 PASS | PASS | PASS | 0 / 0/8 PASS |  |  |
| walk N | 0.012 PASS | 0.057 **FAIL** | 6 **FAIL** | 0.94 PASS | PASS | PASS | 0 / 0/8 PASS |  |  |
| walk NW | 0.025 **FAIL** | 0.069 **FAIL** | 5 FAIL (persp.) | 0.96 PASS | PASS | PASS | 0 / 0/8 PASS |  |  |
| walk W | 0.035 **FAIL** | 0.050 **FAIL** | 4 FAIL (persp.) | 0.91 PASS | PASS | PASS | 0 / 0/8 PASS |  |  |
| walk SW | 0.017 PASS | 0.085 **FAIL** | 5 FAIL (persp.) | 0.85 PASS | PASS | PASS | 0 / 0/8 PASS |  |  |
| run S | 0.036 **FAIL** | 0.052 **FAIL** | 10 **FAIL** | 0.96 PASS | PASS | PASS | 0 / 0/8 PASS |  |  |
| run SE | 0.071 **FAIL** | 0.086 **FAIL** | 9 FAIL (persp.) | 0.79 PASS | PASS | PASS | 0 / 0/8 PASS |  |  |
| run E | 0.136 **FAIL** | 0.053 **FAIL** | 7 FAIL (persp.) | 0.88 PASS | PASS | PASS | 0 / 0/8 PASS |  |  |
| run NE | 0.107 **FAIL** | 0.069 **FAIL** | 6 FAIL (persp.) | 0.90 PASS | PASS | PASS | 0 / 0/8 PASS |  |  |
| run N | 0.030 **FAIL** | 0.076 **FAIL** | 9 **FAIL** | 1.01 PASS | PASS | PASS | 0 / 0/8 PASS |  |  |
| run NW | 0.108 **FAIL** | 0.071 **FAIL** | 6 FAIL (persp.) | 0.95 PASS | PASS | PASS | 0 / 0/8 PASS |  |  |
| run W | 0.139 **FAIL** | 0.056 **FAIL** | 7 FAIL (persp.) | 0.91 PASS | **FAIL** 1/8 THIN | PASS | 0 / 0/8 PASS |  |  |
| run SW | 0.069 **FAIL** | 0.092 **FAIL** | 9 FAIL (persp.) | 0.90 PASS | PASS | PASS | 0 / 0/8 PASS |  |  |
| idle S | 0.009 PASS | 0.027 **FAIL** | 3 **FAIL** | 0.61 PASS | PASS | PASS | 0 / 0/12 PASS |  |  |
| idle SE | 0.008 PASS | 0.062 **FAIL** | 2 PASS | 0.65 PASS | PASS | PASS | 0 / 0/12 PASS |  |  |
| idle E | 0.008 PASS | 0.047 **FAIL** | 1 PASS | 0.69 PASS | **FAIL** 1/12 VANISHED | PASS | 0 / 0/12 PASS |  |  |
| idle NE | 0.008 PASS | 0.058 **FAIL** | 2 PASS | 0.68 PASS | PASS | PASS | 0 / 0/12 PASS |  |  |
| idle N | 0.005 PASS | 0.039 **FAIL** | 3 **FAIL** | 0.61 PASS | PASS | PASS | 0 / 0/12 PASS |  |  |
| idle NW | 0.009 PASS | 0.056 **FAIL** | 1 PASS | 0.68 PASS | PASS | PASS | 0 / 0/12 PASS |  |  |
| idle W | 0.008 PASS | 0.047 **FAIL** | 1 PASS | 0.62 PASS | PASS | PASS | 0 / 0/12 PASS |  |  |
| idle SW | 0.008 PASS | 0.065 **FAIL** | 2 PASS | 0.60 PASS | PASS | PASS | 0 / 0/12 PASS |  |  |
| jump S | 0.089 **FAIL** | 0.047 **FAIL** | n/a | 0.20 n/a | PASS | PASS | 0 / 0/16 PASS |  |  |
| jump SE | 0.072 **FAIL** | 0.080 **FAIL** | n/a | 0.30 n/a | PASS | PASS | 0 / 0/16 PASS |  |  |
| jump E | 0.060 **FAIL** | 0.066 **FAIL** | n/a | 0.35 n/a | PASS | PASS | 0 / 0/16 PASS |  |  |
| jump NE | 0.071 **FAIL** | 0.075 **FAIL** | n/a | 0.34 n/a | **FAIL** 2/16 THIN | PASS | 0 / 0/16 PASS |  |  |
| jump N | 0.073 **FAIL** | 0.055 **FAIL** | n/a | 0.24 n/a | PASS | PASS | 0 / 0/16 PASS |  |  |
| jump NW | 0.071 **FAIL** | 0.079 **FAIL** | n/a | 0.37 n/a | **FAIL** 1/16 SPLIT | PASS | 0 / 0/16 PASS |  |  |
| jump W | 0.059 **FAIL** | 0.068 **FAIL** | n/a | 0.37 n/a | PASS | PASS | 0 / 0/16 PASS |  |  |
| jump SW | 0.074 **FAIL** | 0.083 **FAIL** | n/a | 0.26 n/a | PASS | PASS | 0 / 0/16 PASS |  |  |
| dash S | 0.013 PASS | 0.029 **FAIL** | n/a | 0.31 n/a | PASS | PASS | 0 / 0/13 PASS |  |  |
| dash SE | 0.038 **FAIL** | 0.057 **FAIL** | n/a | 0.35 n/a | PASS | PASS | 0 / 0/13 PASS |  |  |
| dash E | 0.067 **FAIL** | 0.048 **FAIL** | n/a | 0.38 n/a | PASS | PASS | 0 / 0/13 PASS |  |  |
| dash NE | 0.056 **FAIL** | 0.059 **FAIL** | n/a | 0.38 n/a | PASS | PASS | 0 / 0/13 PASS |  |  |
| dash N | 0.035 **FAIL** | 0.051 **FAIL** | n/a | 0.23 n/a | PASS | PASS | 0 / 0/13 PASS |  |  |
| dash NW | 0.070 **FAIL** | 0.057 **FAIL** | n/a | 0.34 n/a | PASS | PASS | 0 / 0/13 PASS |  |  |
| dash W | 0.071 **FAIL** | 0.043 **FAIL** | n/a | 0.33 n/a | PASS | PASS | 0 / 0/13 PASS |  |  |
| dash SW | 0.037 **FAIL** | 0.058 **FAIL** | n/a | 0.32 n/a | PASS | PASS | 0 / 0/13 PASS |  |  |
| hurt S | 0.038 **FAIL** | 0.026 **FAIL** | n/a | 0.21 n/a | PASS | PASS | 0 / 0/9 PASS |  |  |
| hurt SE | 0.034 **FAIL** | 0.058 **FAIL** | n/a | 0.26 n/a | PASS | PASS | 0 / 0/9 PASS |  |  |
| hurt E | 0.032 **FAIL** | 0.057 **FAIL** | n/a | 0.29 n/a | PASS | PASS | 0 / 0/9 PASS |  |  |
| hurt NE | 0.025 **FAIL** | 0.061 **FAIL** | n/a | 0.30 n/a | PASS | PASS | 0 / 0/9 PASS |  |  |
| hurt N | 0.032 **FAIL** | 0.052 **FAIL** | n/a | 0.37 n/a | PASS | PASS | 0 / 0/9 PASS |  |  |
| hurt NW | 0.051 **FAIL** | 0.066 **FAIL** | n/a | 0.27 n/a | PASS | PASS | 0 / 0/9 PASS |  |  |
| hurt W | 0.047 **FAIL** | 0.065 **FAIL** | n/a | 0.31 n/a | PASS | PASS | 0 / 0/9 PASS |  |  |
| hurt SW | 0.034 **FAIL** | 0.067 **FAIL** | n/a | 0.26 n/a | PASS | PASS | 0 / 0/9 PASS |  |  |

## Posture gates (E profile; round 5 B + addendum)

torso pitch = pelvis->neck base vs vertical, **+ = forward** (gate idle/walk: every frame >= 0); head pitch = head bone vs vertical, **+ = chin down** (gate idle/walk: -3..+8 = level to slightly down); both measured in Blender on the motion (release/rl_pose.py, same pose application as render_motion.py). head forward = E-view head centre x - neck base x (1x px, her front = +x), gate every frame of every action >= 0. torso(px) = the same angle from the E projection (cross-check).

| action (E motion) | torso pitch min / mean / max | torso (px) min | head pitch min / max | head fwd px min | head fwd mm min | torso gate | head gate | head-forward gate |
|---|---|---|---|---|---|---|---|---|
| walk (blender) | +3.0 / +3.3 / +3.6° | 2.9° | +1.2 / +5.2° | 2.1 | 30 | PASS | PASS | PASS |
| run (blender) | +12.3 / +13.2 / +14.2° | 12.3° | +0.7 / +9.8° | 2.6 | 38 | n/a | n/a | PASS |
| idle (blender) | +0.3 / +0.8 / +1.3° | 0.3° | +1.1 / +4.5° | 1.8 | 27 | PASS | PASS | PASS |
| jump (blender) | +0.0 / +3.8 / +12.0° | 0.0° | +1.3 / +9.3° | 1.8 | 26 | n/a | n/a | PASS |
| dash (blender) | -8.5 / +6.1 / +26.0° | -8.4° | +1.9 / +8.3° | 2.0 | 30 | n/a | n/a | PASS |
| hurt (blender) | -18.6 / -4.0 / +7.1° | -19.6° | +2.0 / +5.7° | 2.0 | 30 | n/a | n/a | PASS |

Per-frame values: gates.json -> posture.<act>.frames.

**Totals (pass / gated clips):** boil 13/48, shade 0/48, feet 6/24, seam 24/24, limbs 44/48, gif 48/48, bangs 48/48; posture (actions): torso 2/2, head 2/2, head_fwd 6/6

## All GIFs in the build: 108 checked, 0 flagged

- none flagged (loop=0, min frame ≥ 20 ms, disposal 2 full frames, seam ok).
