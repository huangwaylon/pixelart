"""mskirt.py (M): skirt flare check per frame: outward (radial) angle of every panel's hem segment vs its pelvis-carried rest,
and the SE 1x hem width (screen px between the outermost hem tips) vs rest.  usage: python mskirt.py walk [dir]"""
import sys, os, json, math
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mrig import Skel, EXP, nrm
from mprev import fk_from_file
import mpx


def check(act, d=None):
    sk = Skel(); m = json.load(open(os.path.join(d or os.path.join(EXP, "motion"), f"{act}.json")))
    rs, us = mpx.cam("SE", sk); Ry = mpx.axang(mpx.UP, mpx.YAW.get("SE", 0.0))
    P = lambda p: np.array([np.dot(Ry @ p, rs), -np.dot(Ry @ p, us)]) * mpx.PPM
    panels = [n.split(".")[1] for n in sk.order if n.startswith("skirt.") and n.endswith(".1")]
    D0, H0, T0 = sk.fk({}); w0 = max(P(T0[f"skirt.{k}.2"])[0] for k in panels) - min(P(T0[f"skirt.{k}.2"])[0] for k in panels)
    out = []
    for fr in m["frames"]:
        D, H, T = fk_from_file(sk, fr); mx = {}
        for k in panels:
            b = f"skirt.{k}.2"; d = nrm(T[b] - H[b]); d0 = nrm(D["pelvis"] @ (sk.tail0[b] - sk.head0[b]))
            r0 = sk.head0[f"skirt.{k}.1"] - sk.head0["pelvis"]; r0[2] = 0; r = nrm(D["pelvis"] @ nrm(r0)); rp = nrm(r - np.dot(r, d0) * d0)
            mx[k] = math.degrees(math.atan2(np.dot(d, rp), np.dot(d, d0)))
        w = max(P(T[f"skirt.{k}.2"])[0] for k in panels) - min(P(T[f"skirt.{k}.2"])[0] for k in panels)
        out.append((max(mx.values()), max(v for k, v in mx.items() if k not in ("F", "B")), w - w0))
    return out


if __name__ == "__main__":
    for act in sys.argv[1].split(","):
        o = check(act, sys.argv[2] if len(sys.argv) > 2 else None)
        print(act, "max outward deg (all / sides):", round(max(x[0] for x in o), 1), "/", round(max(x[1] for x in o), 1),
              "| hem width vs rest px (SE 1x) max:", round(max(x[2] for x in o), 1), "per frame:", [round(x[2], 1) for x in o])
