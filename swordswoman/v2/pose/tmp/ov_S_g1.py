# ov_S.py: per-view overrides for view S (owned by the S sub-strand). PRE = before VIEW_XFORM (SE screen terms; S/N: stride x becomes depth), POST = final pose keys after VIEW_XFORM (N: screen angles already mirrored).
from poses_src_helpers import P, legs, arms, ML
# final (POST) leg targets for S: [x screen-right, y up, depth (+ away), knee hint x, knee hint depth]; L leg = screen right in S
def lg(l, r, kl=(0.3, -1), kr=(-0.3, -1)):
    return {"ik.L": [l[0], l[1], l[2], kl[0], kl[1]], "ik.R": [r[0], r[1], r[2], kr[0], kr[1]]}
def sw(d):  # swap legs for the second half of a cycle (mirror x)
    o = dict(d); L, R = d["ik.L"], d["ik.R"]
    o["ik.L"] = [-R[0], R[1], R[2], -R[3], R[4]]; o["ik.R"] = [-L[0], L[1], L[2], -L[3], L[4]]; return o
PRE = {
 "dash": {"burst": {"+sq": 0.12, "+lean": 6, "head": [-20, 0, 0]}, "smear": {"+sq": 0.10, "lift": 0.02, "absz": 1, "+lean": 10, "head": [-28, 0, 0]}},
}
# WALK S: feet at/over hip width, alternate toward/away from the camera (near foot lower on screen), passing knee lifted toward camera
W_C = lg([0.38, -0.82, -0.46], [-0.36, -0.80, 0.44])
W_D = lg([0.46, -0.64, -0.46], [-0.44, -0.66, 0.44], kl=(0.6, -1))
W_P = P(lg([0.22, -0.88, 0.04], [-0.30, -0.22, -0.30], kr=(-0.4, -1)), {"sq": -0.08})
WARM = {"contact": -60, "down": -64, "pass": -50, "contact2": -40, "down2": -36, "pass2": -50}
# RUN S: drive leg under the body, rear heel kicked up behind, front knee up toward the camera, wide side spread
R_C = P(lg([0.26, -0.84, -0.20], [-0.54, -0.40, 0.35]), {"sq": 0.14})
R_P = lg([0.42, -0.92, 0.30], [-0.30, -0.28, -0.40], kr=(-0.2, -1))
R_A = lg([0.38, -0.40, 0.44], [-0.34, -0.32, -0.40], kr=(-0.2, -1))
POST = {
 "idle": {k: {"ikg.L": [0.30, 0, -0.16, 0.6, -1], "ikg.R": [-0.36, 0, 0.12, -0.3, -1], "head": [-2 + 10 * t, -6, -6], "scr": {"upper_arm.L": [-14 + 8 * t - (8 if k == "down_hold" else 0), 0]}, **({"sq": 0.07} if k == "down_hold" else {})} for k, t in
          (("up", 0), ("settle", 0.5), ("down", 0.9), ("down_hold", 1.0), ("rise", 0.55), ("up2", 0.1))},
 "walk": {**{k: P(v, {"blade_scr": [-140, 0], "scr": {"upper_arm.L": [WARM[k], 0]}}) for k, v in
             (("contact", W_C), ("down", W_D), ("pass", W_P), ("contact2", sw(W_C)), ("down2", sw(W_D)), ("pass2", sw(W_P)))}},
 "run": {k: P(v, {"blade_scr": [-155, 0]}) for k, v in (("contact", R_C), ("push", R_P), ("air", P(R_A, {"lift": 0.54})), ("contact2", sw(R_C)), ("push2", sw(R_P)), ("air2", P(sw(R_A), {"lift": 0.54})))},
 "jump": {"launch": P(lg([0.10, -1.0, 0.0], [-0.32, -0.70, 0.2]), arms(R=[110, 0], L=[72, 0], blade=[130, 0]), {"roll": 12}),
          "rise": arms(R=[150, 0], L=[45, 0], blade=[150, 0]),
          "apex": P(lg([0.24, -0.20, -0.30], [-0.24, -0.24, -0.24]), arms(R=[-140, 0], L=[-40, 0], blade=[-165, 0])),
          "fall": P(lg([0.36, -0.96, -0.20], [-0.38, -0.90, -0.10]), arms(R=[130, 0], L=[60, 0], blade=[145, 0])),
          "land": lg([0.56, -0.46, -0.20], [-0.56, -0.44, 0.20], kl=(1, -0.6), kr=(-1, -0.6))},
 "dash": {"antic": P(arms(L=[-60, 0], blade=[-130, 0]), {"bs": {"upper_arm.L": 1.0}, "roll": 6, "sq": 0.32, "head": [6, 0, -6]}), "burst": {"head": [-34, 0, 0], "ik.R": [-1.05, -0.05, 0.65, -0.5, -1]}, "smear": P(arms(R=[-178, 0], blade=[-178, 0]), {"ik.R": [-0.90, -0.05, 0.70, -0.5, -1]})},
 "slash": {"windup": arms(R=[140, 10], L=[-40, 0], blade=[120, 0]), "impact": P(arms(R=[-10, -10], blade=[-25, 0]), {"bs": {"upper_arm.R": 1.6}}),
           "follow": P(arms(R=[-5, -10]), {"blade_scr": [-10, -35], "bs": {"upper_arm.R": 1.6}, "spine": [6, 0, 20]})},
 "overhead": {"smear": {"blade_scr": [-20, -30]}, "raise": arms(R=[145, 0], L=[139, 0], blade=[110, 0]), "impact": P(lg([0.46, -0.55, -0.25], [-0.40, -0.58, 0.25], kl=(1, -0.6), kr=(-1, -0.6)), arms(R=[-20, 0], L=[-26, 0]), {"blade_scr": [-45, -45], "bs": {"upper_arm.R": 1.7, "upper_arm.L": 1.7}, "sq": 0.18, "lean": 6, "head": [-14, 0, -10]}),
              "follow": P(lg([0.46, -0.56, -0.25], [-0.40, -0.60, 0.25], kl=(1, -0.6), kr=(-1, -0.6)), arms(R=[-28, 0], L=[-34, 0]), {"blade_scr": [-12, -45], "bs": {"upper_arm.R": 1.6, "upper_arm.L": 1.6}, "sq": 0.16, "lean": 10, "head": [-18, 0, -10]})},
 "hurt": {"recoil": P(arms(R=[160, 0], L=[30, 0], blade=[150, 0]), {"bs": {"upper_arm.L": 1.3}, "roll": 9, "head": [-26, 0, -4], "spine": [-24, 0, -10]}),
          "stagger": P(lg([0.40, -0.50, -0.20], [-0.46, -0.44, 0.30], kl=(-0.4, -1), kr=(-1, -0.2)), arms(L=[40, 0]), {"bs": {"upper_arm.L": 1.3}, "head": [-26, 8, 0], "spine": [8, 0, -8], "roll": -14, "sq": 0.22})},
}
