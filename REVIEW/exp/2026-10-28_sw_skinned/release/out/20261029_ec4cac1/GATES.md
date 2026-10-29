# GATES — build 20261029_ec4cac1

Gates (reported, not blocking): pxeval seq on the final 1x frames (P chain + F face) — boil ≤ 0.02, shade_swap ≤ 0.015, feet_range ≤ 2 px (loops only; in SE/E/NE and the other off-axis views a real stride projects ~5–7 px lower at 30° elevation, so FEET there is partly perspective, P notes), seam_ratio ≤ 1.5 (loops); P's limb audit (VANISHED/SPLIT/THIN/DETACHED, failed frames / frames); GIF = render/gifcheck.py (loop=0, ≥20 ms, disposal/ghosting, seam, dup frames) + REVIEW/build.py gif_check on the per-direction 4x GIF.

| clip | boil | shade_swap | feet px | seam | limb audit | GIF | bangs (skin px above brow, max / bad frames) | preview face integrity (max smear, bad frames; turned) | P pz cleanup | other pxeval flags | notes |
|---|---|---|---|---|---|---|---|---|---|---|---|
| walk S | 0.016 PASS | 0.048 **FAIL** | 4 **FAIL** | 0.97 PASS | PASS | PASS | 0 / 0/8 PASS | 0.014 PASS | ran (8/8 8x colour frames, 0 warnings) |  |  |
| walk SE | 0.019 PASS | 0.077 **FAIL** | 5 FAIL (persp.) | 0.82 PASS | PASS | PASS | 0 / 0/8 PASS | 0.024 PASS | ran (8/8 8x colour frames, 0 warnings) |  |  |
| walk E | 0.044 **FAIL** | 0.058 **FAIL** | 5 FAIL (persp.) | 0.69 PASS | PASS | PASS | 0 / 0/8 PASS | 0.099 **FAIL** f6 | ran (8/8 8x colour frames, 0 warnings) |  |  |
| walk NE | 0.035 **FAIL** | 0.062 **FAIL** | 6 FAIL (persp.) | 0.78 PASS | PASS | PASS | 0 / 0/8 PASS | n/a | ran (8/8 8x colour frames, 0 warnings) |  |  |
| walk N | 0.013 PASS | 0.058 **FAIL** | 6 **FAIL** | 0.95 PASS | PASS | PASS | 0 / 0/8 PASS | n/a | ran (8/8 8x colour frames, 0 warnings) |  |  |
| walk NW | 0.036 **FAIL** | 0.064 **FAIL** | 5 FAIL (persp.) | 0.95 PASS | PASS | PASS | 0 / 0/8 PASS | n/a | ran (8/8 8x colour frames, 0 warnings) |  |  |
| walk W | 0.044 **FAIL** | 0.048 **FAIL** | 4 FAIL (persp.) | 0.93 PASS | PASS | PASS | 0 / 0/8 PASS | 0.092 **FAIL** f2 | ran (8/8 8x colour frames, 0 warnings) |  |  |
| walk SW | 0.019 PASS | 0.082 **FAIL** | 5 FAIL (persp.) | 0.88 PASS | PASS | PASS | 0 / 0/8 PASS | 0.025 PASS | ran (8/8 8x colour frames, 0 warnings) |  |  |
| run S | 0.033 **FAIL** | 0.059 **FAIL** | 10 **FAIL** | 0.94 PASS | PASS | PASS | 0 / 0/8 PASS | 0.004 PASS | ran (8/8 8x colour frames, 0 warnings) |  |  |
| run SE | 0.072 **FAIL** | 0.087 **FAIL** | 9 FAIL (persp.) | 0.77 PASS | PASS | PASS | 0 / 0/8 PASS | 0.017 PASS | ran (8/8 8x colour frames, 0 warnings) |  |  |
| run E | 0.137 **FAIL** | 0.055 **FAIL** | 7 FAIL (persp.) | 0.88 PASS | PASS | PASS | 0 / 0/8 PASS | 0.138 **FAIL** f1,2,3,4,5,6 | ran (8/8 8x colour frames, 0 warnings) |  |  |
| run NE | 0.108 **FAIL** | 0.068 **FAIL** | 8 FAIL (persp.) | 0.89 PASS | PASS | PASS | 0 / 0/8 PASS | n/a | ran (8/8 8x colour frames, 0 warnings) |  |  |
| run N | 0.027 **FAIL** | 0.077 **FAIL** | 9 **FAIL** | 1.00 PASS | PASS | PASS | 0 / 0/8 PASS | n/a | ran (8/8 8x colour frames, 0 warnings) |  |  |
| run NW | 0.110 **FAIL** | 0.068 **FAIL** | 8 FAIL (persp.) | 0.94 PASS | PASS | PASS | 0 / 0/8 PASS | n/a | ran (8/8 8x colour frames, 0 warnings) |  |  |
| run W | 0.140 **FAIL** | 0.056 **FAIL** | 7 FAIL (persp.) | 0.93 PASS | PASS | PASS | 0 / 0/8 PASS | 0.143 **FAIL** f1,2,5,6 | ran (8/8 8x colour frames, 0 warnings) |  |  |
| run SW | 0.070 **FAIL** | 0.090 **FAIL** | 10 FAIL (persp.) | 0.91 PASS | PASS | PASS | 0 / 0/8 PASS | 0.036 **FAIL** f2 | ran (8/8 8x colour frames, 0 warnings) |  |  |
| idle S | 0.009 PASS | 0.036 **FAIL** | 1 PASS | 0.60 PASS | PASS | PASS | 0 / 0/12 PASS | 0.021 PASS; turned 4 (max 0.042) | ran (12/12 8x colour frames, 0 warnings) |  |  |
| idle SE | 0.007 PASS | 0.060 **FAIL** | 1 PASS | 0.68 PASS | PASS | PASS | 0 / 0/12 PASS | 0.020 PASS; turned 4 (max 0.088) | ran (12/12 8x colour frames, 0 warnings) |  |  |
| idle E | 0.009 PASS | 0.059 **FAIL** | 1 PASS | 0.75 PASS | PASS | PASS | 0 / 0/12 PASS | 0.242 **FAIL** f0,1,3,4,5,11; turned 4 (max 0.651) | ran (12/12 8x colour frames, 0 warnings) |  |  |
| idle NE | 0.008 PASS | 0.058 **FAIL** | 1 PASS | 0.71 PASS | PASS | PASS | 0 / 0/12 PASS | n/a | ran (12/12 8x colour frames, 0 warnings) |  |  |
| idle N | 0.005 PASS | 0.040 **FAIL** | 1 PASS | 0.60 PASS | PASS | PASS | 0 / 0/12 PASS | n/a | ran (12/12 8x colour frames, 0 warnings) |  |  |
| idle NW | 0.009 PASS | 0.049 **FAIL** | 1 PASS | 0.60 PASS | PASS | PASS | 0 / 0/12 PASS | n/a | ran (12/12 8x colour frames, 0 warnings) |  |  |
| idle W | 0.009 PASS | 0.044 **FAIL** | 1 PASS | 0.69 PASS | PASS | PASS | 0 / 0/12 PASS | 0.156 **FAIL** f0,1,2,5,10,11; turned 4 (max 0.601) | ran (12/12 8x colour frames, 0 warnings) |  |  |
| idle SW | 0.008 PASS | 0.064 **FAIL** | 1 PASS | 0.62 PASS | PASS | PASS | 0 / 0/12 PASS | 0.037 **FAIL** f5; turned 4 (max 0.229) | ran (12/12 8x colour frames, 0 warnings) |  |  |
| jump S | 0.091 **FAIL** | 0.057 **FAIL** | n/a | 0.22 n/a | PASS | PASS | 0 / 0/16 PASS | 0.038 **FAIL** f12 | ran (16/16 8x colour frames, 0 warnings) |  |  |
| jump SE | 0.074 **FAIL** | 0.084 **FAIL** | n/a | 0.29 n/a | PASS | PASS | 0 / 0/16 PASS | 0.010 PASS | ran (16/16 8x colour frames, 0 warnings) |  |  |
| jump E | 0.063 **FAIL** | 0.067 **FAIL** | n/a | 0.34 n/a | PASS | PASS | 0 / 0/16 PASS | 0.322 **FAIL** f4,13 | ran (16/16 8x colour frames, 0 warnings) |  |  |
| jump NE | 0.073 **FAIL** | 0.073 **FAIL** | n/a | 0.32 n/a | PASS | PASS | 0 / 0/16 PASS | n/a | ran (16/16 8x colour frames, 0 warnings) |  |  |
| jump N | 0.077 **FAIL** | 0.057 **FAIL** | n/a | 0.24 n/a | PASS | PASS | 0 / 0/16 PASS | n/a | ran (16/16 8x colour frames, 0 warnings) |  |  |
| jump NW | 0.071 **FAIL** | 0.076 **FAIL** | n/a | 0.34 n/a | PASS | PASS | 0 / 0/16 PASS | n/a | ran (16/16 8x colour frames, 0 warnings) |  |  |
| jump W | 0.058 **FAIL** | 0.068 **FAIL** | n/a | 0.35 n/a | **FAIL** 1/16 SPLIT | PASS | 0 / 0/16 PASS | 0.095 **FAIL** f4 | ran (16/16 8x colour frames, 0 warnings) |  |  |
| jump SW | 0.076 **FAIL** | 0.085 **FAIL** | n/a | 0.26 n/a | PASS | PASS | 0 / 0/16 PASS | 0.000 PASS | ran (16/16 8x colour frames, 0 warnings) |  |  |
| dash S | 0.014 PASS | 0.039 **FAIL** | n/a | 0.33 n/a | PASS | PASS | 0 / 0/13 PASS | 0.058 **FAIL** f8 | ran (13/13 8x colour frames, 0 warnings) |  |  |
| dash SE | 0.038 **FAIL** | 0.055 **FAIL** | n/a | 0.34 n/a | PASS | PASS | 0 / 0/13 PASS | 0.000 PASS | ran (13/13 8x colour frames, 0 warnings) |  |  |
| dash E | 0.066 **FAIL** | 0.049 **FAIL** | n/a | 0.39 n/a | PASS | PASS | 0 / 0/13 PASS | 0.084 **FAIL** f4,5 | ran (13/13 8x colour frames, 0 warnings) |  |  |
| dash NE | 0.055 **FAIL** | 0.059 **FAIL** | n/a | 0.37 n/a | PASS | PASS | 0 / 0/13 PASS | n/a | ran (13/13 8x colour frames, 0 warnings) |  |  |
| dash N | 0.035 **FAIL** | 0.052 **FAIL** | n/a | 0.23 n/a | PASS | PASS | 0 / 0/13 PASS | n/a | ran (13/13 8x colour frames, 0 warnings) |  |  |
| dash NW | 0.070 **FAIL** | 0.055 **FAIL** | n/a | 0.32 n/a | PASS | PASS | 0 / 0/13 PASS | n/a | ran (13/13 8x colour frames, 0 warnings) |  |  |
| dash W | 0.071 **FAIL** | 0.043 **FAIL** | n/a | 0.35 n/a | PASS | PASS | 0 / 0/13 PASS | 0.123 **FAIL** f4,5,8 | ran (13/13 8x colour frames, 0 warnings) |  |  |
| dash SW | 0.037 **FAIL** | 0.056 **FAIL** | n/a | 0.31 n/a | PASS | PASS | 0 / 0/13 PASS | 0.024 PASS | ran (13/13 8x colour frames, 0 warnings) |  |  |
| hurt S | 0.029 **FAIL** | 0.036 **FAIL** | n/a | 0.29 n/a | PASS | PASS | 0 / 0/9 PASS | 0.028 PASS; turned 3 (max 0.017) | ran (9/9 8x colour frames, 0 warnings) |  |  |
| hurt SE | 0.034 **FAIL** | 0.055 **FAIL** | n/a | 0.28 n/a | PASS | PASS | 0 / 0/9 PASS | 0.000 PASS; turned 3 (max 0.169) | ran (9/9 8x colour frames, 0 warnings) |  |  |
| hurt E | 0.032 **FAIL** | 0.061 **FAIL** | n/a | 0.33 n/a | PASS | PASS | 0 / 0/9 PASS | 0.616 **FAIL** f3,4,5; turned 2 (max 0.733) | ran (9/9 8x colour frames, 0 warnings) |  |  |
| hurt NE | 0.026 **FAIL** | 0.062 **FAIL** | n/a | 0.29 n/a | PASS | PASS | 0 / 0/9 PASS | n/a | ran (9/9 8x colour frames, 0 warnings) |  |  |
| hurt N | 0.030 **FAIL** | 0.052 **FAIL** | n/a | 0.39 n/a | PASS | PASS | 0 / 0/9 PASS | n/a | ran (9/9 8x colour frames, 0 warnings) |  |  |
| hurt NW | 0.044 **FAIL** | 0.067 **FAIL** | n/a | 0.28 n/a | PASS | PASS | 0 / 0/9 PASS | n/a | ran (9/9 8x colour frames, 0 warnings) |  |  |
| hurt W | 0.047 **FAIL** | 0.074 **FAIL** | n/a | 0.35 n/a | PASS | PASS | 0 / 0/9 PASS | 0.205 **FAIL** f3,4,5; turned 2 (max 0.512) | ran (9/9 8x colour frames, 0 warnings) |  |  |
| hurt SW | 0.033 **FAIL** | 0.071 **FAIL** | n/a | 0.27 n/a | PASS | PASS | 0 / 0/9 PASS | 0.020 PASS; turned 3 (max 0.017) | ran (9/9 8x colour frames, 0 warnings) |  |  |

## Posture gates (E profile; round 5 B + addendum)

torso pitch = pelvis->neck base vs vertical, **+ = forward** (gate idle/walk: every frame >= 0); head pitch = head bone vs vertical, **+ = chin down** (gate idle/walk: -3..+8 = level to slightly down); both measured in Blender on the motion (release/rl_pose.py, same pose application as render_motion.py). head forward = E-view head centre x - neck base x (1x px, her front = +x), gate every frame of every action >= 0. torso(px) = the same angle from the E projection (cross-check).

| action (E motion) | torso pitch min / mean / max | torso (px) min | head pitch min / max | head fwd px min | head fwd mm min | torso gate | head gate | head-forward gate |
|---|---|---|---|---|---|---|---|---|
| walk (blender) | +3.0 / +3.3 / +3.6° | 2.9° | +1.1 / +5.3° | 2.0 | 30 | PASS | PASS | PASS |
| run (blender) | +12.3 / +13.2 / +14.2° | 12.3° | +0.7 / +9.8° | 2.6 | 38 | n/a | n/a | PASS |
| idle (blender) | +1.6 / +1.6 / +1.8° | 1.6° | +1.0 / +4.5° | 1.9 | 28 | PASS | PASS | PASS |
| jump (blender) | +0.0 / +3.8 / +12.0° | 0.0° | +1.3 / +9.3° | 1.8 | 26 | n/a | n/a | PASS |
| dash (blender) | -8.5 / +6.1 / +26.0° | -8.4° | +1.9 / +8.3° | 2.0 | 30 | n/a | n/a | PASS |
| hurt (blender) | -18.6 / -4.0 / +7.0° | -19.5° | +2.0 / +5.7° | 2.0 | 30 | n/a | n/a | PASS |

Per-frame values: gates.json -> posture.<act>.frames.

**Totals (pass / gated clips):** boil 13/48, shade 0/48, feet 8/24, seam 24/24, limbs 47/48, gif 48/48, bangs 48/48, face_int 14/30, pzclean_ran 48/48; posture (actions): torso 2/2, head 2/2, head_fwd 6/6

## All GIFs in the build: 108 checked, 0 flagged

- none flagged (loop=0, min frame ≥ 20 ms, disposal 2 full frames, seam ok).
