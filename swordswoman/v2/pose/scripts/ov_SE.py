# ov_SE.py: SE-only final tweaks (POST, applied after everything; NOT inherited by S/NE/N, which inherit the SE base table).
from poses_src_helpers import P, legs, arms, ML
_LAG = {"up": 0.1, "settle": 0.0, "down": 0.5, "down_hold": 0.85, "rise": 1.0, "up2": 0.55}  # blade tip + free hand lag the bob by ~1 frame
def _idle(k, t):
    tl = _LAG[k]
    return P({"ikg.L": [0.25, 0, 0.06, 1, -0.6], "ikg.R": [-0.27, 0, -0.06, 0.2, -1], "drop": 0.01 + 0.02 * t}, arms(L=[-18 + 16 * tl, 0], blade=[-138 - 18 * tl, 0]))
PRE = {}
_WB = {"contact": -132, "down": -138, "pass": -160}  # walk: blade swings against the legs (tip low on contact, high on pass)
POST = {
 "idle": {k: _idle(k, t) for k, t in (("up", 0), ("settle", 0.5), ("down", 0.7), ("down_hold", 1.0), ("rise", 0.55), ("up2", 0.1))},
 "walk": {"pass": P(legs([-0.14, -0.84], [0.24, -0.72, -0.25]), arms(L=[-40, 0], blade=[_WB["pass"], 0])), "pass2": P(legs([0.24, -0.72, -0.25], [-0.14, -0.84]), arms(L=[-75, 0], blade=[_WB["pass"], 0])),
          "contact": arms(blade=[_WB["contact"], 0]), "contact2": arms(blade=[_WB["contact"], 0]), "down": arms(blade=[_WB["down"], 0]), "down2": arms(blade=[_WB["down"], 0])},
 "run": {"contact": arms(blade=[-160, 0]), "contact2": arms(blade=[-160, 0]), "push": legs([-0.78, -0.52], [0.56, -0.26]), "push2": legs([0.56, -0.26], [-0.78, -0.52])},
 "dash": {"skid": P(legs([0.96, -0.60], [-0.40, -0.48]), arms(blade=[160, 0]))},
 "overhead": {"raise": arms(R=[135, 0], L=[60, 0], blade=[95, 0])},
 "hurt": {"stagger": P(legs([0.42, -0.78], [-0.70, -0.62, 0.2]), arms(blade=[-115, 0]), {"+spine": [8, 0, 0]})},
}
