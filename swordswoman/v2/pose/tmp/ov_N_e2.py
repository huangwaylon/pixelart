# ov_N.py: per-view overrides for view N (owned by the N sub-strand). PRE = before VIEW_XFORM (SE screen terms; S/N: stride x becomes depth), POST = final pose keys after VIEW_XFORM (N: screen angles already mirrored).
# N notes: her LEFT leg/arm is on screen LEFT; forward = up-screen (depth +). Walk/run legs are authored as final IK targets [x screen, y, depth, knee x, knee depth]
# so each foot stays on its own side (the generic xform's screen diagonal made mirrored strides cross).
from poses_src_helpers import P, legs, arms, ML
_IT = {"up": 0, "settle": 0.5, "down": 0.9, "down_hold": 1.0, "rise": 0.55, "up2": 0.1}
_WL = {"contact": [-140, 40], "down": [-135, 25], "pass": [-128, 0], "contact2": [-132, -40], "down2": [-132, -25], "pass2": [-128, 0]}  # free-arm swing in DEPTH (fore/aft), arm stays on screen left
def _k(x, y, d): return [x, y, d, -0.2 if x < 0 else 0.2, 1]
def _lg(l, r): return {"ik.L": _k(*l), "ik.R": _k(*r)}
_WALKIK = {"contact": _lg((-0.22, -0.80, 0.60), (0.22, -0.80, -0.55)), "down": _lg((-0.24, -0.80, 0.55), (0.24, -0.78, -0.60)), "pass": _lg((-0.16, -0.84, -0.05), (0.20, -0.28, 0.25)),
           "contact2": _lg((-0.22, -0.80, -0.55), (0.22, -0.80, 0.60)), "down2": _lg((-0.24, -0.78, -0.60), (0.24, -0.80, 0.55)), "pass2": _lg((-0.20, -0.28, 0.25), (0.16, -0.84, -0.05))}
_RUNIK = {"contact": _lg((-0.24, -0.78, 0.35), (0.22, -0.40, -0.55)), "push": _lg((-0.22, -0.30, -0.70), (0.16, -0.55, 0.40)), "air": _lg((-0.30, -0.20, -0.65), (0.26, -0.62, 0.45)),
          "contact2": _lg((-0.22, -0.40, -0.55), (0.24, -0.78, 0.35)), "push2": _lg((-0.16, -0.55, 0.40), (0.22, -0.30, -0.70)), "air2": _lg((-0.26, -0.62, 0.45), (0.30, -0.20, -0.65))}
_RUNBL = {"contact": -15, "push": -28, "air": -5, "contact2": -15, "push2": -28, "air2": -5}
PRE = {
 "idle": {k: {"+sq": 0.05 * t, "drop": 0.03 + 0.16 * t, "ikg.L": [-0.28, 0, 0.20, -0.3, 1], "ikg.R": [0.28, 0, -0.10, 0.3, 1]} for k, t in _IT.items()},
 "run": {k: {"+lean": 16 if k.startswith("air") else 10} for k in ("contact", "push", "air", "contact2", "push2", "air2")},
 "walk": {"down": {"+sq": 0.04}, "down2": {"+sq": 0.04}},
 "dash": {"smear": {"lift": 0.0, "absz": 0, "+sq": 0.14, "+lean": 18, "head": [4, 0, 0]}, "burst": {"+lean": 14, "+sq": 0.12}, "skid": {"+sq": 0.08, "+lean": 8}},
 "slash": {"antic": {"+sq": 0.06}, "windup": {"+sq": 0.06}},
 "overhead": {"follow": {"+sq": 0.16, "+lean": 10}},
 "hurt": {"hit": {"+lean": -8, "+sq": 0.06}, "recoil": {"+lean": -6, "+sq": -0.12}},
}
POST = {
 "idle": {k: P(arms(L=[-150, 0], blade=[-35 - 14 * t, 0]), {"bs": {"upper_arm.L": 1.2}}) for k, t in _IT.items()},
 "walk": {k: P(arms(R=[-45, -10], L=_WL[k], blade=[{"contact": -28, "down": -22, "pass": -34}[k.rstrip("2")], 0]), {"bs": {"upper_arm.L": 1.2}}, _WALKIK[k]) for k in _WALKIK},
 "run": {k: P(arms(L=[200, 0] if k.startswith("push") else ([150, 0] if k.startswith("air") else None), blade=[_RUNBL[k], 0]), _RUNIK[k]) for k in _RUNIK},
 "jump": {"rise": {"ik.L": [-0.20, -0.50, 0.05, -0.5, 1], "ik.R": [0.18, -0.55, -0.05, -0.5, 1]},
          "apex": P(arms(R=[50, 0], blade=[40, 0]), {"ik.L": [-0.30, -0.55, 0.10, -0.5, 1], "ik.R": [0.20, -0.14, -0.05, -0.5, 1]}),
          "recover": P(arms(R=[-20, 0], blade=[-5, 0]), {"ik.L": [-0.42, -0.84, 0.20, -0.3, 1], "ik.R": [0.25, -0.80, -0.30, 0.3, 1]})},
 "dash": {"burst": P(arms(blade=[-35, 0]), {"roll": 0, "ik.L": [-0.15, -0.40, 0.75, -0.5, 1], "ik.R": [0.20, -0.20, -0.85, -0.5, 1]}),
          "smear": P(arms(L=[150, 0], blade=[-30, 0]), {"bs": {"upper_arm.L": 1.3}, "roll": 0, "ik.L": [-0.25, -0.30, 1.0, -0.5, 1], "ik.R": [0.30, -0.05, -1.1, -0.5, 1]}), "skid": P(arms(blade=[-60, 0]), {"head": [-14, 0, 0]})},
 "slash": {"antic": {"roll": -6}, "windup": P(arms(R=[70, 10], blade=[60, 0]), {"bs": {"upper_arm.R": 1.6}}), "smear": P(arms(R=[-110, -10], blade=[-120, 0]), {"bs": {"upper_arm.R": 1.4}}),
           "impact": P(arms(R=[-40, -10], blade=[-8, 0]), {"bs": {"upper_arm.R": 1.6}}), "follow": P(arms(R=[15, -10], blade=[35, 0]), {"bs": {"upper_arm.R": 1.4}, "roll": -16})},
 "overhead": {"raise": arms(R=[72, 0], L=[78, 0], blade=[88, 0]), "smear": P(arms(R=[-20, 0], L=[-25, 0], blade=[-25, 0]), {"bs": {"upper_arm.R": 1.5, "upper_arm.L": 1.5}}),
              "impact": P(arms(R=[-35, 0], L=[-40, 0], blade=[-40, 0]), {"bs": {"upper_arm.R": 1.8, "upper_arm.L": 1.8}, "+ik.L": [-0.08, 0, 0, 0, 0], "+ik.R": [0.08, 0, 0, 0, 0]}),
              "follow": P(arms(R=[-40, 0], L=[-45, 0], blade=[-36, 0]), {"bs": {"upper_arm.R": 1.8, "upper_arm.L": 1.8}})},
 "hurt": {"hit": P(arms(L=[160, 0]), {"head": [-12, 0, 0]}), "recoil": P(arms(R=[30, 0], L=[150, 0], blade=[60, 0]), {"bs": {"upper_arm.L": 1.3}, "head": [-14, 0, -4], "ik.L": [-0.42, -0.85, 0.0, -0.5, 1], "ik.R": [0.42, -0.60, 0.0, 0.5, 1]}),
          "stagger": P(arms(R=[-10, 0], L=[150, 0], blade=[-20, 0]), {"roll": -22, "head": [-12, 0, 0]}),
          "recover": {"roll": -6, "ik.L": [-0.32, -0.78, 0.0, -0.5, 1]}},
}

# N overhead: the smear must sweep CLOCKWISE (over the top, down the right side) in N; the frame flag lives in poses_src,
# so set it here on import (poses_src imports this module after ACT is defined). Parent: move to poses_src as cw_N=True on overhead.smear.
import sys as _s
_ps = _s.modules.get("poses_src")
if _ps is not None and hasattr(_ps, "ACT"):
    for _f in _ps.ACT["overhead"]["frames"]:
        if _f["name"] == "smear": _f["cw_N"] = True
