# shared pose helpers (copied from poses_src.py)
def P(*dicts, **kw):
    o = {}
    for d in dicts:
        for k, v in d.items(): o[k] = ({**o[k], **v} if isinstance(v, dict) and isinstance(o.get(k), dict) else v)
    o.update(kw); return o
def legs(l, r, kl=1, kr=1):
    return {"ik.L": [l[0], l[1], l[2] if len(l) > 2 else 0, kl], "ik.R": [r[0], r[1], r[2] if len(r) > 2 else 0, kr]}
def arms(R=None, L=None, blade=None):
    o = {"scr": {}}
    if R is not None: o["scr"]["upper_arm.R"] = list(R) if isinstance(R, (list, tuple)) else [R, 0]
    if L is not None: o["scr"]["upper_arm.L"] = list(L) if isinstance(L, (list, tuple)) else [L, 0]
    if blade is not None: o["blade_scr"] = list(blade) if isinstance(blade, (list, tuple)) else [blade, 0]
    return o
def ML(p):
    """mirror a stride: swap leg IK targets, swap off-arm screen swing around vertical"""
    o = dict(p)
    if "ik.L" in p: o["ik.L"], o["ik.R"] = list(p["ik.R"]), list(p["ik.L"])
    if "scr" in p and "upper_arm.L" in p["scr"]:
        sc = dict(p["scr"]); a = sc["upper_arm.L"]; sc["upper_arm.L"] = [-180 - a[0]] + list(a[1:]); o["scr"] = sc
    for k in ("spine", "chest"):
        if k in p: o[k] = [p[k][0], -p[k][1], p[k][2] * 0.4]
    return o
TURN = {"spine": [0, 0, -8]}  # SE: torso turned a little toward the camera
