"""mview.py (M, round 4): per-view lean cheat. A forward lean points at the camera in the 3/4 views (SE/SW/NE/NW) and does not read
on screen. For each view the lean axis is turned (lean_yaw, max 35 deg) toward the side the character travels on screen, so the
torso visibly tips toward screen-right (SE/NE) or screen-left (SW/NW). Side views (E/W) need none; S/N (travel along the view
axis) get none. Writes motion/view/<act>_<VIEW>.json (same as motion/<act>.json except the lean direction).
usage: python mview.py run[,dash]"""
import sys, os, json, math
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mbuild
from mrig import EXP, UP, FWD, nrm, axang, Skel

AZ = {"SE": (1, 1), "E": (1, 0), "S": (0, 1), "SW": (-1, 1), "NE": (1, -1), "N": (0, -1), "W": (-1, 0), "NW": (-1, -1)}
ALIGN = json.load(open(os.path.join(EXP, "rig", "align.json")))


def lean_yaw_for(view, sk, cap=55.0):
    yaw = float(ALIGN.get(view, {}).get("yaw", 0.0))
    c = nrm(np.array([AZ[view][0], AZ[view][1], 0.0]))
    c = axang(UP, -yaw) @ c                         # camera direction in the rig's own frame (rig turned by yaw)
    e = math.radians(30); f = -(math.cos(e) * c + math.sin(e) * UP); rs = nrm(np.cross(f, UP))
    side = float(np.dot(FWD, rs))
    if abs(side) < 0.15 or abs(side) > 0.97: return 0.0          # facing along the view axis, or a side view
    best = 0.0; bv = side * np.sign(side)
    for a in np.arange(-cap, cap + 0.1, 1.0):
        d = axang(UP, a) @ FWD     # + = toward +Z rotation; Poser maps lean_yaw sign the same way through YAW axis
        v = float(np.dot(d, rs)) * np.sign(side)
        if v > bv + 1e-6: bv, best = v, a
    # Poser.W turns the pitch axis by lean_yaw about UP with sign(YAW . UP); convert the world rotation angle accordingly
    from mpose import Poser
    po = Poser(sk); sg = 1 if np.dot(po.YAW, UP) > 0 else -1
    return float(best * sg)


if __name__ == "__main__":
    sk = Skel(); os.makedirs(os.path.join(EXP, "motion", "view"), exist_ok=True)
    for act in sys.argv[1].split(","):
        for v in AZ:
            ly = lean_yaw_for(v, sk)
            tune = {"track": 1.0} if (act == "run" and v in ("SE", "SW", "NE", "NW")) else None   # R9: wider diagonal run stride (legs separate)
            p = mbuild.build(act, tune=tune, var=dict(name=f"{act}_{v}", lean_yaw=ly, lean_gain=1.3 if ly else 1.0))
            m = json.load(open(p)); m["action"] = f"{act}_{v}"; m["view_cheat"] = {"view": v, "lean_yaw_deg": ly, "lean_gain": 1.3 if ly else 1.0}
            out = os.path.join(EXP, "motion", "view", f"{act}_{v}.json"); json.dump(m, open(out, "w"), indent=0); os.remove(p)
            print(act, v, "lean_yaw", round(ly, 1), out)
