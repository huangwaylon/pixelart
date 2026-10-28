# mact.py (MOTION strand): key tables for the 7 actions -> v2/motion/work/act_M.json  (.venv python -I mact.py [act,act])
# Same retarget machinery as the UNARMED / MOCAP / THROW strands (v2/mocap/scripts/retarget.py + unarmed/scripts/uactions.py arm layer,
# v2/throw/scripts for the throw), re-keyed for whole-body mechanics (MECHANICS.md): 8-frame walk/run cycles at the gait events
# (contact / down / passing / up), a lively 11-frame idle (weight shift + breath + look + blink), extra settle frames for follow-through.
# Secondary motion (hair/ribbons/bow/skirt springs) and head/forearm overlap are added in the renderer (mrender.py).
import sys, os, json, math, subprocess
import numpy as np
V2 = "/Users/waylonhuang/Documents/other/pixelart/swordswoman/v2"; OUT = V2 + "/motion/work/act_M.json"
TUNE = json.load(open(V2 + "/motion/work/tune.json")) if os.path.exists(V2 + "/motion/work/tune.json") else {}
def T(act, k, d): return TUNE.get(act, {}).get(k, d)
if len(sys.argv) > 2 and sys.argv[2] == "--throw":
    sys.path.insert(0, V2 + "/throw/scripts"); import actions as TA
    c = TA.P("cmu/124_01.bvh", ref=300, travel=True, f0=300, f1=540); g = lambda k: TA.amp(c, [300], k); LG, LN = 0.7, -10
    K = [dict(name="ready", t=300, ms=200, expr="determined"), dict(name="coil", t=370, ms=120, expr="determined", opt={"amp_base": g(1.05)}),
         dict(name="windup", t=396, ms=140, expr="determined", opt={"amp_base": g(1.1)}),
         dict(name="stride", t=427, ms=60, expr="effort", opt={"amp_base": g(1.1), "leg_gain": LG}),
         dict(name="release", t=448, ms=50, expr="shout", opt={"amp_base": g(1.15), "leg_gain": LG, "lean": LN}),
         dict(name="follow", t=456, ms=120, expr="shout", opt={"amp_base": g(1.15), "leg_gain": LG, "lean": LN}),
         dict(name="follow2", t=490, ms=100, expr="determined", opt={"amp_base": g(1.1), "leg_gain": LG, "lean": LN / 2}),
         dict(name="recover", t=560, ms=140, expr="smile"), dict(name="settle", t=600, ms=200, expr="smile")]
    o = dict(TA.TCAM, blade="none", root="full", root_gain=[0.35, 0.35], lock={"R": [[0, 1, 2, 3, 4]], "L": [[3, 4, 5, 6, 7, 8]]})
    A = TA.gen("throw", c, K, o, note="CMU 124_01 overhand pitch, 9 keys (ready, coil, windup, stride, release, follow, follow2, recover, settle)")
    A["travel"] = 0.0; json.dump(A, open(sys.argv[1], "w")); raise SystemExit
sys.path.insert(0, V2 + "/unarmed/scripts"); import uactions as UA
RT, AC = UA.RT, UA.AC; nz, rot_axis = UA.nz, UA.rot_axis
def travel_speed(c, a, b, game_s):  # treadmill speed in rig units/s at game timing (one cycle a->b covers the mocap stride)
    d = abs(c["pelvis"][b, 1] - c["pelvis"][a, 1]) * c["_s"]; return float(d / game_s)
# ------------------------------------------------------------------ walk: Bandai walk_active, 8 keys at the gait events
def A_walk():
    c, a, b, vel, ev = AC.walk()
    ms = T("walk", "ms", 105)
    K = [dict(name="contact", t=58), dict(name="down", t=61), dict(name="pass", t=65), dict(name="up", t=69),
         dict(name="contact2", t=74), dict(name="down2", t=77), dict(name="pass2", t=81), dict(name="up2", t=86)]
    for k in K: k["ms"] = ms
    o = {"vel": vel, "center": True, "amp_base": AC.amp(c, range(a, b), T("walk", "amp", 1.3), T("walk", "ampz", 1.5)), "lean": T("walk", "lean", 4), "spread": 0.0,
         "lock": {"R": [[0, 1, 2, 3, 4]], "L": [[4, 5, 6, 7]]}, "arm": T("walk", "arm", {"gain": 1.15, "el": 18})}
    A = AC.gen("walk", c, K, o, loop=True, note="Bandai1 walk_active cycle 58-90, 8 keys at contact/down/pass/up (gait events), swing x1.3 about the cycle mean, pelvis bob x1.5")
    A["travel"] = travel_speed(c, a, b, 8 * ms / 1000.0) * T("walk", "travel_k", 1.0); return A
# ------------------------------------------------------------------ run: CMU 02_03 jog, 8 keys
def A_run():
    c = AC.P("cmu/02_03.bvh", travel=True, ref=0); a, b = 11, 104
    vel = -(c["pelvis"][b, 1] - c["pelvis"][a, 1]) / ((b - a) / c["_fps"]) / c["_L"]
    E = "determined"; ms = T("run", "ms", [70, 60, 65, 70, 70, 60, 65, 70])
    K = [dict(name="contact", t=11), dict(name="down", t=22), dict(name="push", t=34), dict(name="air", t=48, air=1),
         dict(name="contact2", t=57), dict(name="down2", t=68), dict(name="push2", t=80), dict(name="air2", t=93, air=1)]
    for k, m in zip(K, ms): k.update(ms=m, expr=E)
    o = {"vel": vel, "center": True, "amp_base": AC.amp(c, range(a, b), T("run", "amp", 1.45), T("run", "ampz", 1.6)), "lean": T("run", "lean", 12), "air_gain": T("run", "air", 2.0),
         "arm": T("run", "arm", UA.ARM_RUN), "lock": {"R": [[0, 1, 2]], "L": [[4, 5, 6]]}}
    A = AC.gen("run", c, K, o, loop=True, note="CMU 02_03 jog cycle 11-104, 8 keys contact/down/push/air; swing x1.45, bob x1.6, lean 12, flight x2, arm pump layer")
    A["travel"] = travel_speed(c, a, b, sum(ms) / 1000.0) * T("run", "travel_k", 1.0); return A
# ------------------------------------------------------------------ idle: CMU 13_11 relaxed stand + procedural weight shift / breath / look / blink
def synth_idle(c, t0, keys):
    L = c["_L"]; fr = range(t0 - 8, t0 + 9); base = {k: np.mean(c[k][list(fr)], 0) for k in c if not k.startswith(("_", "G_"))}
    S = {k: [] for k in base}; G = {k: [] for k in ("G_head", "G_pelvis", "G_wr.R", "G_wr.L")}
    lup = {s: np.linalg.norm(base["el." + s] - base["sh." + s]) for s in "RL"}; lfo = {s: np.linalg.norm(base["wr." + s] - base["el." + s]) for s in "RL"}
    for k in keys:
        b, br, w, h, sw, y = k["b"], k["br"], k["w"], k["h"], k["sw"], k.get("y", 0.0); J = {n: v.copy() for n, v in base.items()}
        dx = -T("idle", "shift", 0.085) * w * L
        for n in J:
            j = n.split(".")[0]
            if n.startswith(("an", "toe", "heel")): continue
            f = 1.0 if j in ("pelvis", "hip", "kn") else 0.8 if j == "spine" else 0.6 if j == "chest" else 0.5
            J[n][0] += f * dx; J[n][2] -= T("idle", "bob", 0.13) * b * L
        J["hip.R"][2] += 0.032 * w * L; J["hip.L"][2] -= 0.032 * w * L  # stance hip up (contrapposto)
        J["sh.R"][2] -= 0.018 * w * L; J["sh.L"][2] += 0.018 * w * L    # shoulders counter-tilt
        for n in J:
            if n.split(".")[0] in UA.UP[1:]: J[n][2] += 0.03 * br * L
        for s in "RL": J["sh." + s][2] += 0.015 * br * L
        a = math.radians(sw); ab = 0.27 + 0.05 * w
        uR = nz(np.array([-(ab + 0.05 * w), -0.06 - math.sin(a), -1.0])); fR = nz(np.array([-(ab - 0.1), -0.3 - 1.4 * math.sin(a), -1.0]))
        uL = nz(np.array([ab - 0.05 * w, -0.06 + math.sin(a), -1.0])); fL = nz(np.array([ab - 0.1, -0.3 + 1.4 * math.sin(a), -1.0]))
        for s, u_, f_ in (("R", uR, fR), ("L", uL, fL)):
            J["el." + s] = J["sh." + s] + lup[s] * u_; J["wr." + s] = J["el." + s] + lfo[s] * f_; J["hd." + s] = J["wr." + s] + 0.1 * L * f_
        for n in J: S[n].append(J[n])
        Gh = c["G_head"][t0]
        tilt = rot_axis(np.array([0, 0, 1.0]), math.radians(y)) @ rot_axis(np.array([0, 1.0, 0]), math.radians(7 * h)) @ rot_axis(np.array([1.0, 0, 0]), math.radians(-3 * b))
        G["G_head"].append(tilt @ Gh)
        for g in ("G_pelvis", "G_wr.R", "G_wr.L"): G[g].append(c[g][t0])
    out = {n: np.array(v) for n, v in S.items()}; out.update({g: np.array(v) for g, v in G.items()})
    for k in ("_FR", "_Gh", "_L", "_fps", "_s", "_floor"): out[k] = c[k]
    out["_T"] = len(keys); out["_src"] = c["_src"]; return out
def A_idle():
    c = AC.P("cmu/13_11.bvh", ref=44, yaw_frames=range(2, 87))
    K = [dict(name="hold_R", ms=300, b=0.0, br=0.0, w=1.0, h=0.8, sw=-4, y=0),
         dict(name="breathe_R", ms=300, b=0.0, br=1.0, w=1.0, h=1.0, sw=-6, y=-3, expr="smile"),
         dict(name="shift", ms=150, b=0.7, br=0.6, w=0.35, h=0.6, sw=-2, y=-2),
         dict(name="cross", ms=150, b=1.0, br=0.3, w=-0.45, h=-0.2, sw=5, y=2),
         dict(name="land_L", ms=200, b=0.25, br=0.0, w=-1.05, h=-0.9, sw=8, y=6),
         dict(name="hold_L", ms=300, b=0.0, br=0.5, w=-1.0, h=-1.0, sw=5, y=12),
         dict(name="look", ms=250, b=0.0, br=1.0, w=-1.0, h=-0.8, sw=3, y=16),
         dict(name="blink", ms=100, b=0.0, br=0.9, w=-1.0, h=-0.8, sw=2, y=14, expr="blink_closed"),
         dict(name="shift2", ms=150, b=0.7, br=0.5, w=-0.35, h=-0.4, sw=-3, y=6),
         dict(name="cross2", ms=150, b=1.0, br=0.2, w=0.45, h=0.3, sw=-7, y=0),
         dict(name="land_R", ms=200, b=0.25, br=0.0, w=1.05, h=0.9, sw=-8, y=-2)]
    cs = synth_idle(c, 44, K)
    for i, k in enumerate(K): k["t"] = i
    n = len(K)
    g = AC.gen("idle", cs, K, {"root": "none", "turn": {"S": 0, "SE": -16, "E": -18, "NE": -12, "N": 0}, "lock": {"R": [list(range(n))], "L": [list(range(n))]}}, loop=True,
               note="CMU 13_11 relaxed standing (frames 36-52 mean) + procedural layer (MECHANICS idle): weight on R hold + breath, transfer with knee dip, land on L with overshoot, hold L + look-around (head turns ~16 deg) + blink, transfer back; contrapposto hip/shoulder counter-tilt, head tilt toward the free hip, arms pendulum lagging the shift")
    for f in g["frames"]: f["src"] = "cmu/13_11.bvh"
    g["travel"] = 0.0; return g
# ------------------------------------------------------------------ jump / dash / hurt: UNARMED keys + follow-through settle frames
def A_jump():
    c = AC.P("cmu/16_03.bvh", ref=0, yaw_frames=range(100, 300)); st = AC.amp(c, [100], 1.9); o = {"amp_base": st}
    K = [dict(name="antic", t=126, ms=110, expr="determined"), dict(name="crouch", t=153, ms=90, expr="effort", opt=dict(o, arm={"set": [-35, 18, 30]})),
         dict(name="launch", t=181, ms=50, expr="effort", opt={"arm": {"set": [75, 15, 30]}}),
         dict(name="rise", t=196, ms=70, air=1, expr="determined", opt=dict(o, arm={"set": [60, 60, 30]})), dict(name="apex", t=216, ms=170, air=1, expr="smile", opt={"amp_base": AC.amp(c, [100], 2.4), "arm": {"set": [25, 120, 25]}}),
         dict(name="fall", t=240, ms=80, air=1, expr="determined", opt=dict(o, arm={"set": [15, 80, 30]})),
         dict(name="land", t=266, ms=130, expr="squash", opt=dict(o, arm={"set": [25, 35, 45]})), dict(name="recover", t=294, ms=110, expr="smile", opt={"arm": {"set": [5, 20, 25]}}),
         dict(name="settle", t=330, ms=160, expr="smile")]
    g = AC.gen("jump", c, K, {"root": "none", "air_gain": 2.0, "lock": {"R": [[0, 1, 2], [6, 7, 8]], "L": [[0, 1, 2], [6, 7, 8]]}},
               note="CMU 16_03 jump; crouch with arms swung back (anticipation), launch arms forward-up, V-arms apex hang 170 ms, arms out on the fall, squash land, recover + settle (hair/skirt follow-through)")
    g["travel"] = 0.0; return g
def A_dash():
    g = UA.A_dash(); g["travel"] = 0.0
    for f, v in zip(g["frames"], T("dash", "trav", [0.3, 6.0, 6.0, 2.0, 0.2])): f["travel"] = v
    return g
def A_hurt():
    c = AC.P("lafan1/pushAndStumble1_subject5.bvh", ref=0, yaw_frames=range(540, 548)); o = {"amp_base": AC.amp(c, [545], 2.0)}
    K = [dict(name="hit", t=553, ms=70, expr="pain", opt=dict(o, lean=-12, arm={"set": [50, 40, 70]})), dict(name="recoil", t=558, ms=110, expr="pain", opt=dict(o, lean=-16, arm={"set": [70, 55, 100]})),
         dict(name="stagger", t=568, ms=150, expr="pain", opt=dict(o, amp_base=AC.amp(c, [545], 1.2), lean=-10, arm={"set": [35, 50, 60]})),
         dict(name="recover", t=588, ms=150, expr="blink_closed", opt={"arm": {"set": [10, 22, 30]}}), dict(name="settle", t=600, ms=160, expr="neutral")]
    g = AC.gen("hurt", c, K, {"root": "full", "root_gain": [0.35, 0.35]}, note="LaFAN1 pushAndStumble1_subject5 (NC-ND reference): snap hit, recoil with flinch arms, stagger with balance arms, recover, settle")
    g["travel"] = 0.0
    for f, v in zip(g["frames"], T("hurt", "trav", [-2.0, -1.5, -0.6, 0.0, 0.0])): f["travel"] = v
    return g
def A_throw():
    tmp = V2 + "/motion/work/_throw.json"
    r = subprocess.run([sys.executable, "-I", os.path.abspath(__file__), tmp, "--throw"], capture_output=True, text=True)
    if r.returncode: print(r.stderr[-1500:]); raise SystemExit("throw failed")
    g = json.load(open(tmp)); os.remove(tmp); return g
ACTS = ["idle", "walk", "run", "jump", "dash", "hurt", "throw"]
if __name__ == "__main__":
    acts = sys.argv[1].split(",") if len(sys.argv) > 1 else ACTS
    W = json.load(open(OUT)) if os.path.exists(OUT) else {}
    for a in acts: W[a] = globals()["A_" + a](); print(a, len(W[a]["frames"]), "keys", sum(f["ms"] for f in W[a]["frames"]), "ms travel", round(W[a].get("travel", 0), 3))
    json.dump(W, open(OUT, "w"))
