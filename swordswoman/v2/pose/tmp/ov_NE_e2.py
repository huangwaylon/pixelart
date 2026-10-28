# ov_NE.py: per-view overrides for view NE (owned by the NE sub-strand). PRE = before VIEW_XFORM (SE screen terms; S/N: stride x becomes depth), POST = final pose keys after VIEW_XFORM (N: screen angles already mirrored).
from poses_src_helpers import P, legs, arms, ML
_DOWN = {"+drop": 0.04, "+head": [8, 0, 0], "+blade_scr": [-6, 0]}
_WB = {"contact": -160, "down": -164, "pass": -155}
PRE = {
 "idle": {"settle": {"+drop": 0.025, "+head": [4, 0, 0], "+blade_scr": [-3, 0]}, "down": _DOWN, "down_hold": P(_DOWN, {"+drop": 0.065, "+head": [18, 0, 0], "+blade_scr": [2, 0], "hips": [0, -16, 0], "+roll": -2}),
          "rise": {"+blade_scr": [8, 0], "+drop": 0.015, "+head": [3, 0, 0]}, "up2": {"+blade_scr": [10, 0]}},
 "walk": {k + s: P(arms(blade=[_WB[k], 0]), {"+sq": 0.08} if k == "down" else {}) for k in _WB for s in ("", "2")},
 "run": {"contact": P(arms(blade=[-150, 0]), {"+roll": 4}), "push": P(arms(blade=[-150, 0]), {"+roll": 6, "ik.L": [-0.80, -0.60, 0, 1]}), "air": P(arms(blade=[-150, 0]), {"lift": 0.14, "+roll": 10, "+lean": 4}),
         "contact2": P(arms(blade=[-150, 0]), {"+roll": 8}), "push2": P(arms(blade=[-150, 0]), {"+roll": 6, "ik.R": [-0.80, -0.60, 0, 1]}), "air2": P(arms(blade=[-150, 0]), {"lift": 0.14, "+roll": 10, "+lean": 4})},
 "jump": {"crouch": P(legs([0.76, -0.28], [-0.74, -0.28], 1, -1), {"+sq": 0.08}), "land": P(legs([0.86, -0.40], [-0.84, -0.38], 1, -1), {"+head": [8, 0, 0]}), "apex": {"lift": 1.0},
          "fall": P(legs([0.40, -0.90], [-0.30, -0.70]), arms(blade=[162, 0])), "antic": {"+sq": 0.06, "+lean": 4}},
 "dash": {"antic": P(legs([0.36, -0.52], [-0.74, -0.62]), arms(blade=[150, 0])), "smear": P(arms(blade=[-180, 0]), {"lift": 0.0, "absz": 0, "+sq": 0.10}),
          "skid": P(legs([1.0, -0.52], [-0.60, -0.40]), arms(blade=[-162, 0]), {"head": [-8, 0, -4], "+roll": 4})},
 "slash": {"windup": P(legs([0.36, -0.62], [-0.42, -0.80]), arms(R=[80, 10], blade=[110, 0])),
           "impact": P(legs([0.80, -0.58], [-0.72, -0.55]), arms(R=[5, -10], blade=[-30, 0]), {"bs": {"upper_arm.R": 1.8}}),
           "follow": P(arms(blade=[-74, 0]), {"bs": {"upper_arm.R": 1.3}, "spine": [6, 0, 55], "+sq": 0.04})},
 "overhead": {"raise": P(legs([0.58, -0.78], [-0.52, -0.80]), arms(R=[105, 30], L=[99, 30], blade=[120, 0]), {"spine": [-20, 0, -10], "roll": -6}),
              "smear": {"+sq": 0.08}, "impact": P(arms(blade=[-68, 0]), {"+head": [10, 0, 0]}),
              "follow": P(legs([0.62, -0.24], [-0.54, -0.26]), arms(blade=[-120, 0]))},
 "hurt": {"hit": P(legs([0.50, -0.58], [-0.46, -0.80]), arms(R=[-120, 0], L=[60, 0], blade=[-145, 0]), {"bs": {"upper_arm.L": 1.6}, "roll": -16, "spine": [-16, 0, -14], "head": [6, 0, -6], "lean": -4}),
          "recoil": P(legs([0.46, -0.80], [-0.56, -0.60]), arms(R=[-170, 0], L=[50, 0], blade=[-150, 0]), {"bs": {"upper_arm.L": 2.0}, "head": [-6, 0, -4], "spine": [-6, 0, -10], "roll": -6, "lean": -2}),
          "stagger": P(legs([0.70, -0.40, -0.45], [-0.60, -0.62]), arms(blade=[-140, 0]), {"head": [-10, 8, 0]})},
}
_p2 = PRE["walk"]["pass2"]; _p2.setdefault("scr", {})["upper_arm.L"] = [-70, 0]; _p2["+lean"] = 3; _p2["+roll"] = 9; _p2["+sq"] = 0.05; _p2["ik.L"] = [0.62, -0.50, -0.25, 1]; _p2["ik.R"] = [-0.30, -0.82, 0, 1]
for _k in ("contact", "contact2"): PRE["walk"][_k]["scr"]["upper_arm.R"] = [-128, -10]
_IF = {"ikg.L": [0.32, 0, 0.06, 1, -0.6], "ikg.R": [-0.34, 0, -0.06, 0.2, -1]}
for _k in ("up", "settle", "down", "down_hold", "rise", "up2"): PRE["idle"].setdefault(_k, {}).update(_IF)
POST = {}
