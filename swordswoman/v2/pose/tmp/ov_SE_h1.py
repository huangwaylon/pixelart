# ov_SE.py: SE-only final tweaks (POST, applied after everything; NOT inherited by S/NE/N, which inherit the SE base table).
from poses_src_helpers import P, legs, arms, ML
def _idle(t):
    return P({"ikg.L": [0.18, 0, 0.06, 1, -0.6], "ikg.R": [-0.20, 0, -0.06, 0.2, -1], "drop": 0.01 + 0.02 * t}, arms(L=[-14 + 8 * t, 0]))
PRE = {}
POST = {
 "idle": {k: _idle(t) for k, t in (("up", 0), ("settle", 0.5), ("down", 0.7), ("down_hold", 1.0), ("rise", 0.55), ("up2", 0.1))},
 "walk": {"pass": P(legs([-0.14, -0.84], [0.10, -0.66, -0.25]), arms(L=[-40, 0], blade=[-145, 0])), "pass2": P(legs([0.10, -0.66, -0.25], [-0.14, -0.84]), arms(L=[-75, 0], blade=[-145, 0])),
          "contact": arms(blade=[-145, 0]), "contact2": arms(blade=[-145, 0]), "down": arms(blade=[-145, 0]), "down2": arms(blade=[-145, 0])},
 "run": {"contact": arms(blade=[-160, 0]), "contact2": arms(blade=[-160, 0]), "push": legs([-0.78, -0.52], [0.56, -0.26]), "push2": legs([0.56, -0.26], [-0.78, -0.52])},
 "dash": {"skid": P(legs([0.96, -0.60], [-0.40, -0.48]), arms(blade=[160, 0]))},
 "overhead": {"raise": arms(R=[135, 0], L=[60, 0], blade=[95, 0])},
 "hurt": {"stagger": P(legs([0.42, -0.78], [-0.70, -0.62, 0.2]), arms(blade=[-160, 0]))},
}
