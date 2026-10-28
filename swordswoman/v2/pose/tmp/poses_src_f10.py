# poses_src.py: POSE TABLE source (edit here, then `pt.py export` -> poses.json).
# Conventions = hy3d keys_parts.json: Euler deg (X,Y,Z) about rest axes. X+: down-pointing limb swings BACK / up-pointing bone leans FORWARD;
# Y+: down-pointing limb swings to her right; Z+: turns her front to her left. lean = pelvis pitch (thighs compensated). sq = squash (+) / stretch (-),
# sy = stretch along travel, lift = root height (absz = airborne). New (rig_lib.py): yaw (whole body), roll (screen-plane tilt, + = top to screen right),
# cheat (legs+blade yaw toward screen-x in SE/NE), headv (head-to-camera cheat), blade_scr [screen angle (0 right, 90 up), depth].
# Frame = {"name", "ms", "base": {...}, "<VIEW>": {... per-view override, '+key' additive}, "smear", "air"}.
DOC = ("POSE strand pose table. action -> keys (frames, in order) -> view -> pose (bone Euler deg, conventions of hy3d keys_parts.json) + ms. "
       "Extra rig keys from v2/pose/scripts/rig_lib.py: yaw, roll (screen-plane lean), cheat, headv, blade_scr [screen angle, depth]. "
       "W/SW/NW = mirrored E/SE/NE. Render: pose/scripts/pt.py render <act> <views>.")
VIEWS = ["S", "SE", "E", "NE", "N"]
VIEW_DEFAULT = {"SE": {"cheat": 0}, "E": {}, "S": {}, "NE": {}, "N": {}}
INHERIT = {"S": ["SE"], "NE": ["SE"], "N": ["SE"]}  # unfinished views start from the SE overrides
def M(p, arm_swap=True):
    """mirror a stride pose: swap legs, mirror torso twist/roll, swap off-arm swing sign (sword arm kept)"""
    o = {}
    for k, v in p.items():
        if k.startswith(("thigh.", "shin.", "foot.")): o[k[:-1] + ("L" if k[-1] == "R" else "R")] = [v[0], -v[1], -v[2]]
        elif k in ("spine", "chest", "hips"): o[k] = [v[0], -v[1], -v[2]]
        elif k == "upper_arm.L" and arm_swap: o[k] = [-v[0], v[1], v[2]]
        elif k == "scr":
            o[k] = {}
            for b, a in v.items():
                if b.startswith(("thigh.", "shin.", "foot.")): o[k][b[:-1] + ("L" if b[-1] == "R" else "R")] = a
                elif b == "upper_arm.L" and arm_swap: o[k][b] = [-180 - a[0]] + list(a[1:])
                else: o[k][b] = a
        else: o[k] = v
    return o
# Legs: "ik.R"/"ik.L" = [x, y, depth, knee] foot target from the hip joint in LEG LENGTHS, in the camera-facing vertical plane
# (x + = screen right, y + = up, depth + = away from camera, knee +1 = knee points screen right). Arms/blade: "scr" {bone: [screen angle, depth]}.
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
# ------------------------------------------------------------------ IDLE (6 f) ready stance, contrapposto, blade low outside the body
def idle(t):  # t 0 = up, 1 = down. Feet PLANTED (ikg = absolute ground targets), body drops by `drop` leg lengths
    return P({"ikg.L": [0.36, 0, 0.06, 1, -0.6], "ikg.R": [-0.36, 0, -0.06, 0.2, -1], "drop": 0.03 + 0.04 * t},
             arms(R=[-136 + 4 * t, -10], L=[-30 + 8 * t, 0], blade=[-138 - 22 * t, 0]),
             {"spine": [2 + 3 * t, 6, -12], "chest": [0, 4, 0], "head": [-2 + 12 * t, -6, -6], "hips": [0, -8 - 4 * t, 0], "sq": -0.01 + 0.05 * t})
def idle_E(t):  # E: own sword carry, tip forward and slightly up, clear in front of the knees; feet locked ~10 px apart
    return P(arms(R=[-40 + 3 * t, -10], L=[-155, 0], blade=[18 + 14 * t, 0]), {"ikg.R": [-0.20, 0, -0.06, 1], "ikg.L": [0.24, 0, 0.06, 1]})
# ------------------------------------------------------------------ WALK (6 f @100)
WALK_C = P(legs([0.54, -0.82], [-0.50, -0.82]), arms(R=[-112, -10], L=[-55, 0], blade=[-140, 0]), {"lean": 6, "spine": [6, 0, -6], "head": [-4, 0, -4], "roll": 3, "sq": 0.03})
WALK_D = P(legs([0.56, -0.80], [-0.56, -0.72]), arms(R=[-116, -10], L=[-60, 0], blade=[-148, 0]), {"lean": 4, "spine": [6, 0, -8], "head": [-2, 0, -2], "roll": 3, "sq": 0.07})
WALK_P = P(legs([-0.14, -0.84], [0.56, -0.28]), arms(R=[-104, -10], L=[-25, 0], blade=[-134, 0]), {"lean": 7, "spine": [3, 0, -12], "head": [-4, 0, 0], "roll": 2, "sq": -0.04})
WALK_E = {"contact": P(arms(R=[-36, -10], L=[-150, 0], blade=[22, 0]), {"+lean": 3}), "down": arms(R=[-40, -10], L=[-125, 0], blade=[8, 0]), "pass": P(arms(R=[-50, -10], L=[-70, 0], blade=[32, 0]), {"ik.R": [0.62, -0.30, 0, 1], "ik.L": [-0.28, -0.84, 0, 1]})}
# ------------------------------------------------------------------ RUN (6 f @70, contact 80)
RUN_C = P(legs([0.42, -0.86], [-0.55, -0.48]), arms(R=[-165, -10], L=[-150, 0], blade=[-176, 0]), {"lean": 12, "spine": [8, 0, -12], "head": [-14, 0, -4], "roll": 9, "sq": 0.08})
RUN_P = P(legs([-0.62, -0.62], [0.56, -0.26]), arms(R=[-172, -10], L=[-90, 0], blade=[-200, 0]), {"lean": 14, "spine": [10, 0, -16], "head": [-22, 0, 0], "roll": 10, "sq": -0.02})
RUN_A = P(legs([-0.72, -0.26], [0.64, -0.40]), arms(R=[-150, -10], L=[10, 0], blade=[-162, 0]), {"lean": 12, "spine": [10, 0, -18], "head": [-18, 0, 2], "roll": 14, "absz": 1, "lift": 0.44, "sq": -0.08})
RUN_E = {"+roll": 6, "+lean": 4, "blade_scr": [-198, 0]}
RUN_AE = {"+roll": -4, "+lean": -4, "blade_scr": [-180, 0], "lift": 0.12, "ik.L": [-0.80, -0.30, 0, 1], "ik.R": [0.80, -0.20, 0, 1]}
# ------------------------------------------------------------------ JUMP (8 f)
JUMP = {
 "antic": P(legs([0.22, -0.64], [-0.22, -0.64], 1, 1), arms(R=[-170, 0], L=[-5, 0], blade=[-160, 0]), {"spine": [16, 0, -8], "head": [-22, 0, 0], "roll": -6, "sq": 0.14}),
 "crouch": P(legs([0.48, -0.36], [-0.46, -0.36], 1, 1), arms(R=[-165, 10], L=[45, 10], blade=[-165, 0]), {"spine": [30, 0, -8], "head": [-56, 0, 0], "roll": -4, "sq": 0.30}),
 "launch": P(legs([0.22, -0.74], [-0.16, -1.0]), arms(R=[125, 0], L=[40, 0], blade=[148, 0]), {"spine": [-14, 0, -10], "head": [-18, 0, 0], "roll": -4, "lift": 0.1, "sq": -0.24}),
 "rise": P(legs([0.10, -0.70], [-0.12, -0.90]), arms(R=[140, 0], L=[30, 0], blade=[140, 0]), {"spine": [-2, 0, -8], "head": [-10, 0, 0], "absz": 1, "lift": 0.44, "sq": -0.1}),
 "apex": P(legs([0.30, -0.36], [-0.06, -0.64]), arms(R=[165, 0], L=[25, 0], blade=[160, 0]), {"spine": [14, 0, -8], "head": [-16, 0, 0], "absz": 1, "lift": 0.6, "sq": 0.08}),
 "fall": P(legs([0.34, -1.0], [-0.20, -0.74]), arms(R=[140, 0], L=[70, 0], blade=[150, 0]), {"spine": [-6, 0, -8], "head": [2, 0, 0], "absz": 1, "lift": 0.3, "sq": -0.12}),
 "land": P(legs([0.52, -0.46], [-0.50, -0.44]), arms(R=[-150, 0], L=[30, 0], blade=[140, 0]), {"spine": [24, 0, -8], "head": [-50, 0, 0], "sq": 0.32}),
 "recover": P(legs([0.22, -0.84], [-0.20, -0.84]), arms(R=[-132, 0], L=[-60, 0], blade=[-146, 0]), {"spine": [8, 0, -8], "head": [-10, 0, 0], "sq": 0.04}),
}
JUMP_E = {"antic": arms(blade=[-150, 0]), "crouch": P(legs([0.56, -0.30], [-0.54, -0.30]), arms(L=[60, 0], blade=[-140, 0]), {"head": [-62, 0, 0], "spine": [34, 0, -8]}),
          "apex": P(legs([0.30, -0.26], [0.0, -0.40]), arms(R=[175, 0], L=[30, 0], blade=[150, 0])), "land": arms(R=[-50, 0], blade=[15, 0]), "recover": P(idle_E(0.5))}
# ------------------------------------------------------------------ DASH (5 f) low lunge, blade trailing flat behind (smear = VFX layer, no arc)
DASH = {
 "antic": P(legs([0.36, -0.52], [-0.22, -0.60]), arms(R=[-140, 0], L=[10, 0], blade=[-150, 0]), {"bs": {"upper_arm.L": 1.35}, "lean": 0, "spine": [4, 0, -16], "head": [-12, 0, -6], "roll": -16, "sq": 0.28}),
 "burst": P(legs([0.86, -0.40], [-0.98, -0.12]), arms(R=[-172, 0], L=[-10, 0], blade=[-163, 0]), {"lean": 16, "spine": [8, 0, -6], "head": [-24, 0, 0], "roll": 15, "sy": 1.1, "sq": 0.12}),
 "smear": P(legs([0.88, -0.38], [-0.98, -0.12]), arms(R=[-176, 0], L=[0, 0], blade=[-166, 0]), {"lean": 12, "spine": [2, 0, -6], "head": [-16, 0, 0], "roll": 8, "absz": 1, "lift": 0.03, "sy": 1.25, "sq": 0.06}),
 "skid": P(legs([0.86, -0.62], [-0.40, -0.48]), arms(R=[-150, 0], L=[40, 0], blade=[-190, 0]), {"lean": 0, "spine": [-14, 0, -10], "head": [6, 0, -4], "roll": -26, "sq": 0.16}),
 "recover": P(legs([0.30, -0.74], [-0.26, -0.72]), arms(R=[-125, 0], L=[-50, 0], blade=[-146, 0]), {"spine": [10, 0, -8], "head": [-10, 0, -4], "sq": 0.08}),
}
DASH_E = {"antic": {"roll": -22, "spine": [-8, 0, -16], "head": [-4, 0, -6]}, "skid": P(legs([0.95, -0.62], [-0.62, -0.42]), arms(R=[0, 0], blade=[35, 0]), {"roll": -10, "spine": [-8, 0, -10], "head": [-10, 0, -4]}), "recover": idle_E(0.3)}
# ------------------------------------------------------------------ SLASH (7 f) coil -> unwind, wide arc high-back -> low-front
SLASH = {
 "antic": P(legs([0.28, -0.74], [-0.26, -0.70]), arms(R=[-165, 10], L=[-30, 0], blade=[-150, 0]), {"spine": [8, 0, -40], "chest": [0, 0, -12], "head": [-12, 0, 16], "roll": -10, "sq": 0.16}),
 "windup": P(legs([0.26, -0.62], [-0.32, -0.80]), arms(R=[125, 10], L=[-20, 0], blade=[140, 0]), {"bs": {"upper_arm.R": 2.0}, "spine": [-8, 0, 30], "chest": [-6, 0, 10], "head": [-2, 0, -34], "roll": -12, "sq": -0.06}),
 "smear": P(legs([0.58, -0.66], [-0.58, -0.62]), arms(R=[30, -10], L=[-150, 0], blade=[10, 0]), {"lean": 6, "spine": [8, 0, 16], "chest": [4, 0, 8], "head": [-16, 0, -10], "roll": 10, "sq": 0.04}),
 "impact": P(legs([0.82, -0.50], [-0.74, -0.48]), arms(R=[-8, -10], L=[-165, 0], blade=[-25, 0]), {"lean": 4, "spine": [4, 0, 32], "chest": [2, 0, -6], "head": [-22, 0, -24], "roll": 18, "sq": 0.14}),
 "follow": P(legs([0.80, -0.44], [-0.70, -0.42]), arms(R=[0, -10], L=[-170, 0], blade=[-28, 0]), {"bs": {"upper_arm.R": 1.2}, "lean": 4, "spine": [6, 0, 45], "chest": [2, 0, 10], "head": [-14, 0, -36], "roll": 12, "sq": 0.12}),
 "recover": P(legs([0.56, -0.70], [-0.50, -0.66]), arms(R=[-120, -10], L=[-90, 0], blade=[-145, 0]), {"lean": 4, "spine": [6, 0, 12], "head": [-10, 0, -8], "roll": 4, "sq": 0.05}),
 "settle": P(legs([0.26, -0.88], [-0.24, -0.86]), arms(R=[-125, -10], L=[-62, 0], blade=[-146, 0]), {"spine": [2, 0, -8], "head": [-4, 0, -2], "sq": 0.02}),
}
SLASH_E = {"antic": P(arms(R=[165, 10], blade=[150, 0]), {"bs": {"upper_arm.R": 1.2}, "spine": [-12, 0, -20], "roll": -12}), "windup": P(arms(R=[160, 10], blade=[140, 0]), {"bs": {"upper_arm.R": 1.4}, "chest": [-6, 0, 16]}), "impact": P(arms(R=[-2, -10], blade=[-20, 0]), {"head": [-26, 0, -24]}),
           "follow": arms(R=[-10, -10], blade=[-15, 0]), "recover": idle_E(0.2), "settle": idle_E(0.5)}
# ------------------------------------------------------------------ OVERHEAD SLASH (6 f): vertical chop, both hands, tip to the floor in front
OVH = {
 "antic": P(legs([0.30, -0.56], [-0.30, -0.54]), arms(R=[-60, 0], L=[-65, 0], blade=[40, 0]), {"spine": [14, 0, -10], "head": [-24, 0, 0], "roll": -6, "sq": 0.2}),
 "raise": P(legs([0.36, -0.82], [-0.30, -0.84]), arms(R=[118, 0], L=[112, 0], blade=[95, 0]), {"bs": {"upper_arm.R": 1.9, "upper_arm.L": 1.9}, "spine": [-26, 0, -20], "chest": [-8, 0, 0], "head": [-4, 0, 10], "roll": -16, "lift": 0.04, "sq": -0.22}),
 "smear": P(legs([0.54, -0.52], [-0.46, -0.54]), arms(R=[14, 0], L=[9, 0], blade=[-35, 0]), {"bs": {"upper_arm.R": 1.5, "upper_arm.L": 1.5}, "lean": 12, "spine": [20, 0, 36], "head": [-30, 0, -14], "roll": 7, "sq": 0.1}),
 "impact": P(legs([0.70, -0.46], [-0.58, -0.48]), arms(R=[10, 0], L=[5, 0], blade=[-50, 0]), {"bs": {"upper_arm.R": 1.5, "upper_arm.L": 1.5}, "lean": 12, "spine": [20, 0, 40], "head": [-52, 0, -16], "roll": 8, "sq": 0.28}),
 "follow": P(legs([0.58, -0.40], [-0.50, -0.42]), arms(R=[12, 0], L=[7, 0], blade=[-55, 0]), {"bs": {"upper_arm.R": 1.4, "upper_arm.L": 1.4}, "lean": 10, "spine": [16, 0, 40], "head": [-34, 0, -16], "roll": 6, "sq": 0.12}),
 "recover": P(legs([0.30, -0.84], [-0.24, -0.82]), arms(R=[-120, 0], L=[-70, 0], blade=[-146, 0]), {"lean": 4, "spine": [6, 0, -8], "head": [-8, 0, 0], "sq": 0.03}),
}
OVH_E = {"raise": P(arms(R=[100, 0], L=[96, 0], blade=[90, 0]), {"bs": {"upper_arm.R": 1.9, "upper_arm.L": 1.9}, "spine": [-24, 0, -20], "roll": -12, "head": [8, 0, 10]}),
         "impact": P(legs([0.66, -0.30], [-0.56, -0.34]), arms(R=[15, 0], L=[10, 0], blade=[-38, 0]), {"head": [-52, 0, -16]}), "follow": P(legs([0.56, -0.46], [-0.48, -0.48]), {"blade_scr": [-25, 0]}), "recover": idle_E(0.3)}
# ------------------------------------------------------------------ HURT (4 f) hit from screen right: knocked off the ground, arms flung, head whips back
HURT = {
 "hit": P(legs([0.42, -0.58], [-0.38, -0.80]), arms(R=[-160, 0], L=[70, 0], blade=[-165, 0]), {"lean": -10, "spine": [-40, 0, -14], "head": [38, 0, -6], "roll": -30, "absz": 1, "lift": 0.12, "sq": -0.12}),
 "recoil": P(legs([0.38, -0.70], [-0.52, -0.66]), arms(R=[160, 0], L=[130, 0], blade=[150, 0]), {"lean": -8, "spine": [-20, 0, -10], "head": [-6, 0, -4], "roll": -12, "sq": 0.08}),
 "stagger": P(legs([0.42, -0.66], [-0.60, -0.54]), arms(R=[-150, 0], L=[60, 0], blade=[-130, 0]), {"spine": [14, 0, -8], "head": [-24, 8, 0], "roll": -8, "sq": 0.16}),
 "recover": P(legs([0.22, -0.86], [-0.20, -0.84]), arms(R=[-124, 0], L=[-65, 0], blade=[-146, 0]), {"spine": [8, 0, -8], "head": [-6, 0, -2], "sq": 0.04}),
}
HURT_E = {"hit": {"head": [6, 0, -14], "spine": [-22, 0, -14], "roll": -20}, "stagger": P(legs([0.38, -0.56], [-0.80, -0.46]), arms(R=[-140, 0], blade=[150, 0]), {"roll": -2, "spine": [16, 0, -8], "head": [-24, 0, -6]}), "recoil": P(legs([0.46, -0.88], [-0.52, -0.66]), arms(R=[170, 0], blade=[-165, 0]), {"head": [-20, 0, -12], "spine": [-28, 0, -10], "roll": -20}), "recover": idle_E(0.4)}
def F(name, ms, base, expr="neutral", **kw):
    d = {"name": name, "ms": ms, "base": base, "expr": expr}; d.update(kw); return d
def J(key, tab, etab, name=None):
    return {"E": etab.get(key, {})}
ACT = {
 "idle": {"loop": True, "frames": [F("up", 200, idle(0), E=idle_E(0)), F("settle", 150, idle(0.5), E=P(idle_E(0.5), {"hips": [0, -10, 0], "+roll": -2})), F("down", 150, idle(0.9), E=idle_E(0.9)),
                                   F("down_hold", 300, P(idle(1.0), {"scr": {"upper_arm.L": [-32, 0]}, "+head": [3, 0, 0]}), "blink", E=idle_E(1.0)), F("rise", 150, idle(0.55), E=idle_E(0.55)), F("up2", 150, idle(0.1), E=idle_E(0.1))]},
 "walk": {"loop": True, "frames": [F("contact", 100, WALK_C, E=WALK_E["contact"]), F("down", 100, WALK_D, E=WALK_E["down"]), F("pass", 100, WALK_P, E=WALK_E["pass"]),
                                   F("contact2", 100, ML(WALK_C), E=ML(WALK_E["contact"])), F("down2", 100, ML(WALK_D), E=ML(WALK_E["down"])), F("pass2", 100, ML(WALK_P), E=ML(WALK_E["pass"]))]},
 "run": {"loop": True, "frames": [F("contact", 80, RUN_C, "determined", E=RUN_E), F("push", 70, RUN_P, "determined", E=RUN_E), F("air", 70, RUN_A, "determined", air=True, E=RUN_AE),
                                  F("contact2", 80, ML(RUN_C), "determined", E=RUN_E), F("push2", 70, ML(RUN_P), "determined", E=RUN_E), F("air2", 70, ML(RUN_A), "determined", air=True, E=ML(RUN_AE))]},
 "jump": {"frames": [F(k, ms, JUMP[k], ex, **({"air": True} if k in ("rise", "apex", "fall") else {}), **J(k, JUMP, JUMP_E)) for k, ms, ex in
                     [("antic", 120, "determined"), ("crouch", 80, "strain"), ("launch", 50, "shout"), ("rise", 80, "joy"), ("apex", 160, "joy"), ("fall", 80, "surprised"), ("land", 100, "strain"), ("recover", 120, "neutral")]]},
 "dash": {"frames": [F("antic", 100, DASH["antic"], "determined", **J("antic", DASH, DASH_E)), F("burst", 40, DASH["burst"], "shout", smear=1, arc=0),
                     F("smear", 40, DASH["smear"], "shout", smear=1, arc=0, air=True), F("skid", 120, DASH["skid"], "strain", **J("skid", DASH, DASH_E)),
                     F("recover", 120, DASH["recover"], "determined", **J("recover", DASH, DASH_E))]},
 "slash": {"frames": [F(k, ms, SLASH[k], ex, **({"smear": 1, "plane_E": "h"} if k == "smear" else {}), **J(k, SLASH, SLASH_E)) for k, ms, ex in
                      [("antic", 160, "determined"), ("windup", 80, "determined"), ("smear", 40, "shout"), ("impact", 120, "shout"), ("follow", 80, "shout"), ("recover", 120, "determined"), ("settle", 100, "neutral")]]},
 "overhead": {"frames": [F(k, ms, OVH[k], ex, **({"smear": 1} if k == "smear" else {}), **J(k, OVH, OVH_E)) for k, ms, ex in
                         [("antic", 140, "determined"), ("raise", 100, "determined"), ("smear", 40, "shout"), ("impact", 140, "shout"), ("follow", 80, "shout"), ("recover", 140, "determined")]]},
 "hurt": {"frames": [F(k, ms, HURT[k], ex, **J(k, HURT, HURT_E)) for k, ms, ex in [("hit", 60, "pain"), ("recoil", 160, "pain"), ("stagger", 120, "pain"), ("recover", 160, "determined")]]},
}
# ------------------------------------------------------------------ per-view transforms (applied after all overrides)
def _xf_E(p):
    p = dict(p)
    for k, cap in (("spine", 12), ("chest", 6)):
        if k in p: v = list(p[k]); v[2] = min(v[2], cap); p[k] = v
    if "head" in p: v = list(p["head"]); v[2] = min(v[2], 0) - 6; p["head"] = v
    return p
def _legs_depth(p, sign, side):
    """S/N: the screen-authored stride x becomes DEPTH (S: toward the camera, N: away), feet spread sideways, knees toward travel"""
    p = dict(p)
    for s_, sd in (("L", side), ("R", -side)):
        k = "ik." + s_
        if k in p:
            x, y = p[k][0], p[k][1]; d = p[k][2] if len(p[k]) > 2 else 0
            p[k] = [sd * 0.10 + 0.45 * x * sign, y, -sign * 0.70 * x + d * 0.3, 0.5 * sign, -sign]
    return p
def _xf_S(p):
    p = _legs_depth(p, 1, 1)
    if "roll" in p: p["roll"] = 0.3 * p["roll"]
    for k in ("spine", "chest"):
        if k in p: v = list(p[k]); v[2] = max(-20, min(20, v[2])); p[k] = v
    return p
def _mirror_scr(p):
    p = dict(p)
    if "scr" in p: p["scr"] = {b: [180 - a[0]] + list(a[1:]) for b, a in p["scr"].items()}
    if "blade_scr" in p: p["blade_scr"] = [180 - p["blade_scr"][0]] + list(p["blade_scr"][1:])
    if "roll" in p: p["roll"] = -p["roll"]
    return p
def _xf_N(p):
    p = _mirror_scr(_legs_depth(p, -1, -1))
    if "roll" in p: p["roll"] = 0.3 * p["roll"]
    for k in ("spine", "chest"):
        if k in p: v = list(p[k]); v[2] = max(-20, min(20, v[2])); p[k] = v
    return p
VIEW_XFORM = {"E": _xf_E, "S": _xf_S, "N": _xf_N}
