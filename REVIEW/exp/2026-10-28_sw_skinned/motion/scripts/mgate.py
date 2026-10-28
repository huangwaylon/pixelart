"""mgate.py (M, round 5): posture gate per frame in the E profile (her front = +Y):
  torso pitch  = pelvis-head -> neck-head line vs vertical (deg, + = forward)       gate: >= 0 on idle/walk/standing frames
  head pitch   = head forward vector below horizontal (deg, + = chin down)           gate: -3 .. +10 (level to slightly down)
  head offset  = head centre minus neck base along her front (cm and px at 1x)      gate: >= 0 every frame (head over/ahead of the neck)
  CoM offset   = body centre of mass (crude segment weights) minus the support centre (feet on the ground), along her front (cm)
usage: python mgate.py walk,run,... [--dir motion/view]"""
import sys, os, json, math
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mrig import Skel, EXP, UP, FWD, nrm
from mprev import fk_from_file
PPM = 52.608 / 0.775
STAND = ("stand", "settle", "end", "recover", "weight", "transfer")
SEGW = {"pelvis": .14, "spine": .10, "chest": .14, "neck": .02, "head": .22, "thigh.L": .07, "thigh.R": .07, "shin.L": .04, "shin.R": .04,
        "upper_arm.L": .025, "upper_arm.R": .025, "forearm.L": .015, "forearm.R": .015, "foot.L": .02, "foot.R": .02}


def gate(act, d=None):
    sk = Skel(); m = json.load(open(os.path.join(d or os.path.join(EXP, "motion"), f"{act}.json"))); rows = []
    base = act.split("_")[0]
    for k, fr in enumerate(m["frames"]):
        D, H, T = fk_from_file(sk, fr)
        w = H["neck"] - H["pelvis"]; tor = math.degrees(math.atan2(np.dot(w, FWD), np.dot(w, UP)))
        f = D["head"] @ FWD; hp = math.degrees(math.asin(max(-1, min(1, -np.dot(f, UP)))))
        hc = H["head"] + 0.45 * (T["head"] - H["head"]); off = float(np.dot(hc - H["neck"], FWD))
        com = sum(wt * (H[b] + T[b]) / 2 for b, wt in SEGW.items()) / sum(SEGW.values())
        sup = [H[f"toe.{s}"] for s in "LR" if H[f"toe.{s}"][2] < 0.05] + [H[f"foot.{s}"] for s in "LR" if H[f"foot.{s}"][2] < sk.head0[f"foot.{s}"][2] + 0.02]
        cof = float(np.dot(com - np.mean(sup, 0), FWD)) if sup else None
        key = fr.get("key", "")
        standing = base in ("idle", "walk") or key.startswith(STAND)
        ok = (not standing or tor >= 0) and -3.0 <= hp <= 10.0 and off >= 0
        rows.append(dict(f=k, key=key, torso=round(tor, 1), head=round(hp, 1), head_off_cm=round(off * 100, 1), head_off_px=round(off * PPM, 2),
                         com_cm=None if cof is None else round(cof * 100, 1), standing=standing, ok=ok))
    return rows


if __name__ == "__main__":
    dd = sys.argv[sys.argv.index("--dir") + 1] if "--dir" in sys.argv else None
    allok = True
    for act in sys.argv[1].split(","):
        rows = gate(act, dd); bad = [r["f"] for r in rows if not r["ok"]]; allok &= not bad
        print(f"{act:9s} torso {min(r['torso'] for r in rows):+5.1f}..{max(r['torso'] for r in rows):+5.1f}  head {min(r['head'] for r in rows):+5.1f}..{max(r['head'] for r in rows):+5.1f}"
              f"  head_off {min(r['head_off_cm'] for r in rows):+.1f}..{max(r['head_off_cm'] for r in rows):+.1f} cm  FAIL frames {bad}")
        if "-v" in sys.argv:
            for r in rows: print("   ", r)
    print("GATE", "PASS" if allok else "FAIL")
