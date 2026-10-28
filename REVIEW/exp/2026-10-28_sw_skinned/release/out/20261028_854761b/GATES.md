# GATES — build 20261028_854761b

Gates (reported, not blocking): pxeval seq on the final 1x frames (P chain + F face) — boil ≤ 0.02, shade_swap ≤ 0.015, feet_range ≤ 2 px (loops only; in SE/E/NE and the other off-axis views a real stride projects ~5–7 px lower at 30° elevation, so FEET there is partly perspective, P notes), seam_ratio ≤ 1.5 (loops); P's limb audit (VANISHED/SPLIT/THIN/DETACHED, failed frames / frames); GIF = render/gifcheck.py (loop=0, ≥20 ms, disposal/ghosting, seam, dup frames) + REVIEW/build.py gif_check on the per-direction 4x GIF.

| clip | boil | shade_swap | feet px | seam | limb audit | GIF | bangs (skin px above brow, max / bad frames) | other pxeval flags | notes |
|---|---|---|---|---|---|---|---|---|---|
| walk S | 0.014 PASS | 0.029 **FAIL** | 3 **FAIL** | 1.01 PASS | PASS | PASS | 16 / 8/8 **FAIL** |  |  |
| walk SE | 0.018 PASS | 0.041 **FAIL** | 5 FAIL (persp.) | 0.74 PASS | **FAIL** 1/8 THIN | PASS | 24 / 8/8 **FAIL** |  |  |
| walk E | 0.040 **FAIL** | 0.033 **FAIL** | 5 FAIL (persp.) | 0.72 PASS | PASS | PASS | 0 / 0/8 PASS |  |  |
| walk NE | 0.033 **FAIL** | 0.037 **FAIL** | 6 FAIL (persp.) | 0.75 PASS | PASS | PASS | 0 / 0/8 PASS |  |  |
| walk N | 0.015 PASS | 0.035 **FAIL** | 6 **FAIL** | 0.90 PASS | PASS | PASS | 0 / 0/8 PASS |  |  |
| walk NW | 0.033 **FAIL** | 0.040 **FAIL** | 5 FAIL (persp.) | 0.96 PASS | PASS | PASS | 0 / 0/8 PASS |  |  |
| walk W | 0.041 **FAIL** | 0.033 **FAIL** | 4 FAIL (persp.) | 0.93 PASS | PASS | PASS | 0 / 0/8 PASS |  |  |
| walk SW | 0.019 PASS | 0.039 **FAIL** | 5 FAIL (persp.) | 0.80 PASS | PASS | PASS | 7 / 7/8 **FAIL** |  |  |
| run S | 0.038 **FAIL** | 0.041 **FAIL** | 10 **FAIL** | 0.94 PASS | **FAIL** 1/8 THIN | PASS | 12 / 8/8 **FAIL** |  |  |
| run SE | 0.073 **FAIL** | 0.046 **FAIL** | 9 FAIL (persp.) | 0.75 PASS | **FAIL** 3/8 SPLIT | PASS | 30 / 8/8 **FAIL** |  |  |
| run NE | 0.117 **FAIL** | 0.043 **FAIL** | 6 FAIL (persp.) | 0.89 PASS | PASS | PASS | 0 / 0/8 PASS |  |  |
| run N | 0.031 **FAIL** | 0.060 **FAIL** | 9 **FAIL** | 0.99 PASS | PASS | PASS | 0 / 0/8 PASS |  |  |
| run NW | 0.119 **FAIL** | 0.045 **FAIL** | 6 FAIL (persp.) | 0.90 PASS | PASS | PASS | 0 / 0/8 PASS |  |  |
| run SW | 0.069 **FAIL** | 0.051 **FAIL** | 9 FAIL (persp.) | 0.90 PASS | **FAIL** 2/8 SPLIT | PASS | 15 / 5/8 **FAIL** |  |  |
| idle S | 0.015 PASS | 0.018 **FAIL** | 2 PASS | 0.64 PASS | **FAIL** 1/12 DETACHED/SPLIT | PASS | 15 / 12/12 **FAIL** |  |  |
| idle SE | 0.014 PASS | 0.031 **FAIL** | 2 PASS | 0.68 PASS | PASS | PASS | 30 / 11/12 **FAIL** |  |  |
| idle E | 0.013 PASS | 0.029 **FAIL** | 1 PASS | 0.73 PASS | PASS | PASS | 8 / 1/12 **FAIL** |  |  |
| idle NE | 0.013 PASS | 0.027 **FAIL** | 2 PASS | 0.73 PASS | PASS | PASS | 0 / 0/12 PASS |  |  |
| idle N | 0.016 PASS | 0.029 **FAIL** | 3 **FAIL** | 0.62 PASS | PASS | PASS | 0 / 0/12 PASS |  |  |
| idle NW | 0.014 PASS | 0.026 **FAIL** | 1 PASS | 0.60 PASS | PASS | PASS | 0 / 0/12 PASS |  |  |
| idle W | 0.014 PASS | 0.030 **FAIL** | 3 FAIL (persp.) | 0.66 PASS | PASS | PASS | 0 / 0/12 PASS |  |  |
| idle SW | 0.013 PASS | 0.028 **FAIL** | 2 PASS | 0.63 PASS | PASS | PASS | 23 / 11/12 **FAIL** |  |  |
| jump S | 0.094 **FAIL** | 0.034 **FAIL** | n/a | 0.29 n/a | **FAIL** 7/16 DETACHED/SPLIT/THIN | PASS | 20 / 16/16 **FAIL** |  |  |
| jump SE | 0.081 **FAIL** | 0.046 **FAIL** | n/a | 0.47 n/a | **FAIL** 2/16 SPLIT/THIN | PASS | 26 / 16/16 **FAIL** |  |  |
| jump E | 0.072 **FAIL** | 0.046 **FAIL** | n/a | 0.58 n/a | **FAIL** 2/16 THIN | PASS | 0 / 0/16 PASS |  |  |
| jump NE | 0.076 **FAIL** | 0.040 **FAIL** | n/a | 0.50 n/a | **FAIL** 3/16 THIN | PASS | 0 / 0/16 PASS |  |  |
| jump N | 0.064 **FAIL** | 0.038 **FAIL** | n/a | 0.37 n/a | PASS | PASS | 0 / 0/16 PASS |  |  |
| jump NW | 0.076 **FAIL** | 0.046 **FAIL** | n/a | 0.54 n/a | **FAIL** 1/16 THIN | PASS | 0 / 0/16 PASS |  |  |
| jump W | 0.063 **FAIL** | 0.046 **FAIL** | n/a | 0.49 n/a | **FAIL** 2/16 THIN | PASS | 0 / 0/16 PASS |  |  |
| jump SW | 0.076 **FAIL** | 0.049 **FAIL** | n/a | 0.44 n/a | **FAIL** 1/16 THIN | PASS | 26 / 14/16 **FAIL** |  |  |
| dash S | 0.018 PASS | 0.019 **FAIL** | n/a | 0.27 n/a | **FAIL** 4/13 DETACHED/SPLIT | PASS | 16 / 13/13 **FAIL** |  |  |
| dash SE | 0.039 **FAIL** | 0.030 **FAIL** | n/a | 0.24 n/a | **FAIL** 2/13 THIN | PASS | 22 / 13/13 **FAIL** |  |  |
| dash E | 0.043 **FAIL** | 0.034 **FAIL** | n/a | 0.36 n/a | PASS | PASS | 0 / 0/13 PASS |  |  |
| dash N | 0.042 **FAIL** | 0.037 **FAIL** | n/a | 0.24 n/a | PASS | PASS | 0 / 0/13 PASS |  |  |
| dash SW | 0.042 **FAIL** | 0.034 **FAIL** | n/a | 0.32 n/a | **FAIL** 2/13 SPLIT | PASS | 25 / 9/13 **FAIL** |  |  |
| hurt S | 0.118 **FAIL** | 0.012 PASS | n/a | 0.18 n/a | **FAIL** 3/9 DETACHED/SPLIT | PASS | 14 / 9/9 **FAIL** |  |  |
| hurt SE | 0.108 **FAIL** | 0.023 **FAIL** | n/a | 0.16 n/a | PASS | PASS | 37 / 9/9 **FAIL** |  |  |
| hurt E | 0.048 **FAIL** | 0.035 **FAIL** | n/a | 0.21 n/a | PASS | PASS | 0 / 0/9 PASS |  |  |
| hurt NE | 0.047 **FAIL** | 0.034 **FAIL** | n/a | 0.28 n/a | PASS | PASS | 0 / 0/9 PASS |  |  |
| hurt N | 0.055 **FAIL** | 0.033 **FAIL** | n/a | 0.20 n/a | PASS | PASS | 0 / 0/9 PASS |  |  |
| hurt NW | 0.047 **FAIL** | 0.047 **FAIL** | n/a | 0.20 n/a | PASS | PASS | 0 / 0/9 PASS |  |  |
| hurt W | 0.045 **FAIL** | 0.044 **FAIL** | n/a | 0.23 n/a | **FAIL** 1/9 THIN | PASS | 8 / 1/9 **FAIL** |  |  |
| hurt SW | 0.097 **FAIL** | 0.025 **FAIL** | n/a | 0.18 n/a | **FAIL** 1/9 SPLIT | PASS | 21 / 7/9 **FAIL** |  |  |
| run E | - n/a | - n/a | n/a | - n/a | n/a | **FAIL** NOT_BUILT | n/a |  | P pixel_chain failed (see clip.log): ValueError: zero-size array to reduction operation minimum which has no identity |
| run W | - n/a | - n/a | n/a | - n/a | n/a | **FAIL** NOT_BUILT | n/a |  | P pixel_chain failed (see clip.log): ValueError: zero-size array to reduction operation minimum which has no identity |
| dash NE | - n/a | - n/a | n/a | - n/a | n/a | **FAIL** NOT_BUILT | n/a |  | P pixel_chain failed (see clip.log): ValueError: zero-size array to reduction operation minimum which has no identity |
| dash NW | - n/a | - n/a | n/a | - n/a | n/a | **FAIL** NOT_BUILT | n/a |  | P pixel_chain failed (see clip.log): ValueError: zero-size array to reduction operation minimum which has no identity |
| dash W | - n/a | - n/a | n/a | - n/a | n/a | **FAIL** NOT_BUILT | n/a |  | P pixel_chain failed (see clip.log): ValueError: zero-size array to reduction operation minimum which has no identity |

## Posture gates (E profile; round 5 B + addendum)

torso pitch = pelvis->neck base vs vertical, **+ = forward** (gate idle/walk: every frame >= 0); head pitch = head bone vs vertical, **+ = chin down** (gate idle/walk: -3..+8 = level to slightly down); both measured in Blender on the motion (release/rl_pose.py, same pose application as render_motion.py). head forward = E-view head centre x - neck base x (1x px, her front = +x), gate every frame of every action >= 0. torso(px) = the same angle from the E projection (cross-check).

| action (E motion) | torso pitch min / mean / max | torso (px) min | head pitch min / max | head fwd px min | head fwd mm min | torso gate | head gate | head-forward gate |
|---|---|---|---|---|---|---|---|---|
| walk (E projection (no motion snapshot)) | -3.2 / -2.9 / -2.5° | -3.2° | -10.1 / -2.3° | -3.0 | - | **FAIL** | **FAIL** | **FAIL** |
| run (E projection (no motion snapshot)) | +12.0 / +12.9 / +14.1° | 12.0° | -12.2 / -1.0° | -2.2 | - | n/a | n/a | **FAIL** |
| idle (E projection (no motion snapshot)) | -7.2 / -6.1 / -4.7° | -7.2° | -7.1 / +2.2° | -3.4 | - | **FAIL** | **FAIL** | **FAIL** |
| jump (E projection (no motion snapshot)) | -12.4 / -0.6 / +11.9° | -12.4° | -12.9 / +1.2° | -4.8 | - | n/a | n/a | **FAIL** |
| dash (E projection (no motion snapshot)) | -16.6 / +3.6 / +25.6° | -16.6° | -18.7 / -1.3° | -3.9 | - | n/a | n/a | **FAIL** |
| hurt (E projection (no motion snapshot)) | -21.2 / -6.7 / +5.3° | -21.2° | -27.2 / +2.8° | -7.0 | - | n/a | n/a | **FAIL** |

Per-frame values: gates.json -> posture.<act>.frames.

**Totals (pass / gated clips):** boil 13/43, shade 1/43, feet 6/22, seam 22/22, limbs 25/43, gif 43/48, bangs 23/43; posture (actions): torso 0/2, head 0/2, head_fwd 0/6

## All GIFs in the build: 98 checked, 0 flagged

- none flagged (loop=0, min frame ≥ 20 ms, disposal 2 full frames, seam ok).
