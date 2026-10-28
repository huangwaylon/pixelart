# ov_NE.py: per-view overrides for view NE (owned by the NE sub-strand). PRE = before VIEW_XFORM (SE screen terms; S/N: stride x becomes depth), POST = final pose keys after VIEW_XFORM (N: screen angles already mirrored).
from poses_src_helpers import P, legs, arms, ML
_DOWN = {"+drop": 0.04, "+head": [8, 0, 0], "+blade_scr": [-6, 0]}
_WB = {"contact": -160, "down": -164, "pass": -155}
PRE = {
 "idle": {"settle": {"+drop": 0.025, "+head": [4, 0, 0], "+blade_scr": [-3, 0]}, "down": _DOWN, "down_hold": P(_DOWN, {"+drop": 0.065, "+head": [18, 0, 0], "+blade_scr": [-10, 0], "hips": [0, -16, 0], "+roll": -2}),
          "rise": {"+blade_scr": [8, 0]}, "up2": {"+blade_scr": [10, 0]}},
 "walk": {k + s: P(arms(blade=[_WB[k], 0]), {"+sq": 0.08} if k == "down" else {}) for k in _WB for s in ("", "2")},
 "run": {"contact": P(arms(blade=[-150, 0]), {"+roll": 4}), "push": P(arms(blade=[-150, 0]), {"+roll": 4}), "air": P(arms(blade=[-150, 0]), {"lift": 0.14, "+roll": 10, "+lean": 4}),
         "contact2": P(arms(blade=[-150, 0]), {"+roll": 4}), "push2": P(arms(blade=[-150, 0]), {"+roll": 4}), "air2": P(arms(blade=[-150, 0]), {"lift": 0.14, "+roll": 10, "+lean": 4})},
 "jump": {"crouch": P(legs([0.76, -0.28], [-0.74, -0.28], 1, -1), {"+sq": 0.08}), "land": P(legs([0.76, -0.40], [-0.74, -0.38], 1, -1), {"+head": [8, 0, 0]}), "apex": {"lift": 1.0},
          "fall": P(legs([0.40, -0.90], [-0.30, -0.70]), arms(blade=[120, 0]))},
 "dash": {"antic": P(legs([0.36, -0.52], [-0.60, -0.50]), arms(blade=[150, 0])), "smear": P(arms(blade=[-180, 0]), {"lift": 0.0, "absz": 0, "+sq": 0.10}),
          "skid": P(legs([1.0, -0.52], [-0.60, -0.40]), arms(blade=[-135, 0]), {"head": [2, 0, -4], "+roll": 8})},
 "slash": {"windup": P(legs([0.36, -0.62], [-0.42, -0.80]), arms(R=[110, 10], blade=[140, 0])),
           "impact": P(legs([0.80, -0.58], [-0.72, -0.55]), arms(R=[18, -10], blade=[-14, 0]), {"bs": {"upper_arm.R": 1.5}}),
           "follow": P(arms(blade=[-74, 0]), {"bs": {"upper_arm.R": 1.3}, "spine": [6, 0, 55], "+sq": 0.04})},
 "overhead": {"raise": P(legs([0.58, -0.78], [-0.52, -0.80]), arms(R=[100, 0], L=[94, 0], blade=[95, 0]), {"spine": [-12, 0, -10], "roll": -6}),
              "smear": {"+sq": 0.08}, "impact": P(arms(blade=[-68, 0]), {"+head": [10, 0, 0]}),
              "follow": P(legs([0.62, -0.30], [-0.54, -0.32]), arms(blade=[-105, 0]))},
 "hurt": {"hit": P(legs([0.50, -0.58], [-0.46, -0.80]), arms(R=[-120, 0], L=[60, 0], blade=[-145, 0]), {"bs": {"upper_arm.L": 1.6}, "roll": -16, "spine": [-16, 0, -14], "head": [6, 0, -6], "lean": -4}),
          "recoil": P(legs([0.46, -0.80], [-0.56, -0.60]), arms(R=[-170, 0], L=[50, 0], blade=[-150, 0]), {"bs": {"upper_arm.L": 2.0}, "head": [-6, 0, -4], "spine": [-6, 0, -10], "roll": -6, "lean": -2}),
          "stagger": P(legs([0.58, -0.20], [-0.60, -0.62]), arms(blade=[-165, 0]))},
}
_p2 = PRE["walk"]["pass2"]; _p2.setdefault("scr", {})["upper_arm.L"] = [-70, 0]; _p2["+lean"] = 3
for _k in ("contact", "contact2"): PRE["walk"][_k]["scr"]["upper_arm.R"] = [-128, -10]
POST = {}
