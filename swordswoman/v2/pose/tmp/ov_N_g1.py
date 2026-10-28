# ov_N.py: per-view overrides for view N (owned by the N sub-strand). PRE = before VIEW_XFORM (SE screen terms; S/N: stride x becomes depth), POST = final pose keys after VIEW_XFORM (N: screen angles already mirrored).
# N notes: her LEFT leg/arm is on screen LEFT; forward = up-screen (depth +). Walk/run legs are authored as final IK targets [x screen, y, depth, knee x, knee depth]
# so each foot stays on its own side (the generic xform's screen diagonal made mirrored strides cross).
from poses_src_helpers import P, legs, arms, ML
_IT = {"up": 0, "settle": 0.5, "down": 0.9, "down_hold": 1.0, "rise": 0.55, "up2": 0.1}
_WL = {"contact": -152, "down": -128, "pass": -100, "contact2": -40, "down2": -52, "pass2": -80}  # small free-arm swing, opposite the legs
def _k(x, y, d): return [x, y, d, -0.2 if x < 0 else 0.2, 1]
def _lg(l, r): return {"ik.L": _k(*l), "ik.R": _k(*r)}
_WALKIK = {"contact": _lg((-0.22, -0.82, 0.45), (0.22, -0.82, -0.40)), "down": _lg((-0.24, -0.74, 0.38), (0.24, -0.68, -0.36)), "pass": _lg((-0.16, -0.84, -0.05), (0.18, -0.34, 0.15)),
           "contact2": _lg((-0.22, -0.82, -0.40), (0.22, -0.82, 0.45)), "down2": _lg((-0.24, -0.68, -0.36), (0.24, -0.74, 0.38)), "pass2": _lg((-0.18, -0.34, 0.15), (0.16, -0.84, -0.05))}
_RUNIK = {"contact": _lg((-0.28, -0.86, 0.30), (0.30, -0.48, -0.40)), "push": _lg((-0.40, -0.40, -0.45), (0.18, -0.28, 0.35)), "air": _lg((-0.26, -0.30, -0.50), (0.20, -0.40, 0.42)),
          "contact2": _lg((-0.30, -0.48, -0.40), (0.28, -0.86, 0.30)), "push2": _lg((-0.18, -0.28, 0.35), (0.40, -0.40, -0.45)), "air2": _lg((-0.20, -0.40, 0.42), (0.26, -0.30, -0.50))}
_RUNBL = {"contact": -15, "push": -28, "air": -5, "contact2": -15, "push2": -28, "air2": -5}
PRE = {
 "idle": {k: {"+sq": 0.05 * t, "drop": 0.03 + 0.11 * t, "ikg.L": [-0.30, 0, 0.06, -0.3, 1], "ikg.R": [0.30, 0, -0.06, 0.3, 1]} for k, t in _IT.items()},
 "run": {k: {"+lean": 6} for k in ("push", "air", "push2", "air2")},
 "walk": {"down": {"+sq": 0.04}, "down2": {"+sq": 0.04}},
 "dash": {"smear": {"lift": 0.0, "absz": 0, "+sq": 0.10, "+lean": 10, "head": [4, 0, 0]}, "burst": {"+lean": 6}, "skid": {"+sq": 0.08, "+lean": 8}},
 "slash": {"antic": {"+sq": 0.06}},
 "overhead": {"follow": {"+sq": 0.16, "+lean": 10}},
 "hurt": {"recoil": {"+lean": -6, "+sq": -0.12}},
}
POST = {
 "idle": {k: P(arms(L=[-120, 0], blade=[-35 - 14 * t, 0])) for k, t in _IT.items()},
 "walk": {k: P(arms(R=[-45, -10], L=[_WL[k], 0], blade=[-28, 0]), {"bs": {"upper_arm.L": 1.2}}, _WALKIK[k]) for k in _WALKIK},
 "run": {k: P(arms(L=[200, 0] if k.startswith("push") else ([150, 0] if k.startswith("air") else None), blade=[_RUNBL[k], 0]), _RUNIK[k]) for k in _RUNIK},
 "jump": {"rise": {"ik.L": [-0.20, -0.50, 0.05, -0.5, 1], "ik.R": [0.18, -0.55, -0.05, -0.5, 1]},
          "apex": P(arms(R=[70, 0], blade=[75, 0]), {"ik.L": [-0.22, -0.12, 0.10, -0.5, 1], "ik.R": [0.20, -0.14, -0.05, -0.5, 1]}),
          "recover": P(arms(R=[-20, 0], blade=[-5, 0]), {"ik.L": [-0.42, -0.84, 0.20, -0.3, 1], "ik.R": [0.25, -0.80, -0.30, 0.3, 1]})},
 "dash": {"burst": P(arms(blade=[-35, 0]), {"ik.L": [-0.42, -0.42, 0.50, -0.5, 1], "ik.R": [0.45, -0.20, -0.70, -0.5, 1]}),
          "smear": P(arms(L=[150, 0], blade=[-30, 0]), {"bs": {"upper_arm.L": 1.3}, "ik.L": [-0.85, -0.36, 0.50, -0.5, 1], "ik.R": [0.85, -0.08, -0.60, -0.5, 1]})},
 "slash": {"antic": {"roll": -6}, "windup": P(arms(R=[120, 10], blade=[150, 0]), {"bs": {"upper_arm.R": 1.6}}), "smear": P(arms(R=[-110, -10], blade=[-120, 0]), {"bs": {"upper_arm.R": 1.4}}),
           "impact": P(arms(R=[-45, -10], blade=[-18, 0]), {"bs": {"upper_arm.R": 1.4}}), "follow": P(arms(R=[-10, -10], blade=[10, 0]), {"bs": {"upper_arm.R": 1.4}, "roll": -10})},
 "overhead": {"raise": arms(blade=[80, 0]), "impact": P(arms(R=[-168, 0], L=[-163, 0], blade=[-150, 0]), {"bs": {"upper_arm.R": 1.8, "upper_arm.L": 1.8}, "+ik.R": [0.10, 0, -0.10, 0, 0]}),
              "follow": P(arms(R=[-165, 0], L=[-160, 0], blade=[-162, 0]), {"bs": {"upper_arm.R": 2.2, "upper_arm.L": 2.2}})},
 "hurt": {"recoil": P(arms(R=[30, 0], L=[150, 0], blade=[60, 0]), {"bs": {"upper_arm.L": 1.3}, "head": [-14, 0, -4], "ik.L": [-0.42, -0.85, 0.0, -0.5, 1], "ik.R": [0.42, -0.85, 0.0, 0.5, 1]}),
          "stagger": P(arms(R=[-10, 0], blade=[-20, 0]), {"roll": -22}),
          "recover": {"roll": -6, "ik.L": [-0.32, -0.78, 0.0, -0.5, 1]}},
}
