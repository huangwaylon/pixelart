# uactions.py: UNARMED re-pick of the mocap actions (on top of v2/mocap/scripts/actions.py + retarget.py)
#   .venv/bin/python -I uactions.py [act,act]  -> ../work/act.json (pt.py table, same format as mocap/work/act.json); unchanged acts copied from mocap/work/act.json
# arm layer (opt "arm"): rotation-only edit of upper_arm/forearm after the retarget (no stretching):
#   gain/c0: sagittal swing about c0 deg (0 = hanging, + forward); bias: + forward pitch; abd: + outward; el: min elbow flex deg; per-side dicts "R"/"L" override
import sys, os, json, math, copy
import numpy as np
U = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); V2 = os.path.dirname(U)
sys.path.insert(0, os.path.join(V2, "mocap", "scripts"))
import retarget as RT, actions as AC
from retarget import nz, rot_axis, REST
_solve = RT.solve
def _frame(D):
    fw = D["hips"] @ np.array([0, -1.0, 0]); fw[2] = 0; fw = nz(fw); lf = nz(np.cross([0, 0, 1.0], fw)); return fw, lf
def pitch(u, fw): return math.degrees(math.atan2(float(u @ fw), float(-u[2])))
def arm_layer(D, A):
    fw, lf = _frame(D)
    for s in "RL":
        o = dict(A); o.update(A.get(s, {}))
        ru = REST["el." + s] - REST["sh." + s]; rf = REST["wr." + s] - REST["el." + s]
        if o.get("set"):  # absolute arm: [pitch fwd deg, abd deg, elbow flex deg] in her yaw frame (forearm flexes forward/up)
            p_, ab_, el_ = o["set"]; out = -lf if s == "R" else lf
            u0 = nz(math.cos(math.radians(p_)) * np.array([0, 0, -1.0]) + math.sin(math.radians(p_)) * fw)
            Ra = rot_axis(fw, math.radians(ab_)); Ra = Ra if (Ra @ u0) @ out >= (Ra.T @ u0) @ out else Ra.T
            us = Ra @ u0; hz = Ra @ lf; Rf = rot_axis(hz, math.radians(el_)); f1, f2 = Rf @ us, Rf.T @ us
            fs = f1 if pitch(f1, fw) > pitch(f2, fw) else f2
            D["upper_arm." + s] = RT.swing(D["upper_arm." + s] @ ru, us) @ D["upper_arm." + s]
            Df = RT.swing(D["forearm." + s] @ rf, fs) @ D["forearm." + s]; dR = Df @ D["forearm." + s].T
            D["forearm." + s] = Df; D["hand." + s] = dR @ D["hand." + s]; continue
        u = D["upper_arm." + s] @ ru
        th = pitch(u, fw); c0 = o.get("c0", 0.0); tgt = c0 + o.get("gain", 1.0) * (th - c0) + o.get("bias", 0.0)
        R = rot_axis(lf, -math.radians(tgt - th))
        if abs(pitch(R @ u, fw) - tgt) > abs(th - tgt) + 1e-6: R = R.T
        if o.get("abd"):
            out = -lf if s == "R" else lf; Ra = rot_axis(fw, math.radians(o["abd"]))
            if (Ra @ (R @ u)) @ out < (R @ u) @ out: Ra = Ra.T
            R = Ra @ R
        for b in ("upper_arm.", "forearm.", "hand."): D[b + s] = R @ D[b + s]
        if o.get("el"):
            u = D["upper_arm." + s] @ ru; f = D["forearm." + s] @ rf
            ang = math.degrees(math.acos(max(-1, min(1, float(nz(u) @ nz(f))))))
            if ang < o["el"]:
                n = np.cross(u, f); n = nz(n) if np.linalg.norm(n) > 1e-4 * np.linalg.norm(u) * np.linalg.norm(f) and ang > 3 else nz(np.cross(u, fw))
                Re = rot_axis(n, math.radians(o["el"] - ang))
                if (Re @ f) @ fw < f @ fw - 1e-6 and ang <= 3: Re = Re.T
                D["forearm." + s] = Re @ D["forearm." + s]; D["hand." + s] = Re @ D["hand." + s]
def solve(c, t, view=None, opt=None):
    D, J = _solve(c, t, view, opt)
    if opt and opt.get("arm"): arm_layer(D, opt["arm"])
    return D, J
RT.solve = solve
P = AC.P; amp = AC.amp; gen = AC.gen
# ------------------------------------------------------------------ idle: CMU 13_11 relaxed stand + procedural contrapposto / breath / hand on hip
UP = ("spine", "chest", "neck", "head", "head_end", "sh", "el", "wr", "hd")
def synth_idle(c, t0, keys):
    """synthetic clip, one frame per key: base = mean of CMU frames t0-8..t0+8; params per key: b bob 0..1, br breath 0..1, w weight on R 0..1, h head tilt, sw L-arm sway deg"""
    L = c["_L"]; fr = range(t0 - 8, t0 + 9); base = {k: np.mean(c[k][list(fr)], 0) for k in c if not k.startswith(("_", "G_"))}
    S = {k: [] for k in base}; G = {k: [] for k in ("G_head", "G_pelvis", "G_wr.R", "G_wr.L")}
    lup = {s: np.linalg.norm(base["el." + s] - base["sh." + s]) for s in "RL"}; lfo = {s: np.linalg.norm(base["wr." + s] - base["el." + s]) for s in "RL"}
    for k in keys:
        b, br, w, h, sw = k["b"], k["br"], k["w"], k["h"], k["sw"]; J = {n: v.copy() for n, v in base.items()}
        dx = -0.075 * w * L  # weight over her right leg (w>0) / left leg (w<0); her right = -x
        for n in J:
            j = n.split(".")[0]
            if n.startswith(("an", "toe")): continue
            f = 1.0 if j in ("pelvis", "hip", "kn") else 0.8 if j == "spine" else 0.6 if j == "chest" else 0.5
            J[n][0] += f * dx; J[n][2] -= 0.15 * b * L
        J["hip.R"][2] += 0.028 * w * L; J["hip.L"][2] -= 0.028 * w * L  # stance hip up
        for n in J:
            if n.split(".")[0] in UP[1:]: J[n][2] += 0.03 * br * L
        for s in "RL": J["sh." + s][2] += 0.012 * br * L
        # arms: R hand on hip (elbow out-back, wrist at the waist side), L relaxed, slight bend, lagged sway
        a = math.radians(sw); ab = 0.27 + 0.05 * w  # relaxed arms, slightly out, elbows soft; pendulum sway lags the weight shift
        uR = nz(np.array([-(ab + 0.05 * w), -0.06 - math.sin(a), -1.0])); fR = nz(np.array([-(ab - 0.1), -0.3 - 1.2 * math.sin(a), -1.0]))
        uL = nz(np.array([ab - 0.05 * w, -0.06 + math.sin(a), -1.0])); fL = nz(np.array([ab - 0.1, -0.3 + 1.2 * math.sin(a), -1.0]))
        for s, u_, f_ in (("R", uR, fR), ("L", uL, fL)):
            J["el." + s] = J["sh." + s] + lup[s] * u_; J["wr." + s] = J["el." + s] + lfo[s] * f_; J["hd." + s] = J["wr." + s] + 0.1 * L * f_
        for n in J: S[n].append(J[n])
        Gh = c["G_head"][t0]; tilt = rot_axis(np.array([0, 1.0, 0]), math.radians(7 * h)) @ rot_axis(np.array([1.0, 0, 0]), math.radians(-3 * b))
        G["G_head"].append(tilt @ Gh)
        for g in ("G_pelvis", "G_wr.R", "G_wr.L"): G[g].append(c[g][t0])
    out = {n: np.array(v) for n, v in S.items()}; out.update({g: np.array(v) for g, v in G.items()})
    for k in ("_FR", "_Gh", "_L", "_fps", "_s", "_floor"): out[k] = c[k]
    out["_T"] = len(keys); out["_src"] = c["_src"]; return out
def A_idle():
    c = P("cmu/13_11.bvh", ref=44, yaw_frames=range(2, 87))
    K = [dict(name="up", ms=300, b=0.15, br=1.0, w=1.0, h=1.0, sw=-7, expr="smile"), dict(name="settle", ms=150, b=0.7, br=0.5, w=0.45, h=0.8, sw=2),
         dict(name="down", ms=150, b=1.0, br=0.1, w=-0.45, h=-0.2, sw=8), dict(name="down_hold", ms=300, b=0.15, br=1.0, w=-1.0, h=-1.0, sw=7, expr="smile"),
         dict(name="rise", ms=150, b=0.7, br=0.5, w=-0.45, h=-0.8, sw=-2), dict(name="up2", ms=150, b=1.0, br=0.1, w=0.45, h=0.2, sw=-8)]
    cs = synth_idle(c, 44, K)
    for i, k in enumerate(K): k["t"] = i
    g = gen("idle", cs, K, {"root": "none", "turn": {"S": 0, "SE": -16, "E": -18, "NE": -12, "N": 0}, "lock": {"R": [list(range(6))], "L": [list(range(6))]}}, loop=True,
            note="CMU 13_11 relaxed standing (frames 36-52 mean) + procedural layer: side-to-side weight transfer (hold on R leg / hold on L leg, 300 ms each = PMD idle holds) with a knee dip ~2 px through each transfer, breath, head tilt following the weight, relaxed soft-elbow arms with lagged pendulum sway")
    for f in g["frames"]: f["src"] = "cmu/13_11.bvh"
    return g
# ------------------------------------------------------------------ run: CMU 02_03 jog + arm pump layer
ARM_RUN = {"gain": 1.35, "c0": 0, "bias": 24, "el": 100, "abd": 8}
def A_run():
    c = P("cmu/02_03.bvh", travel=True, ref=0); a, b = 10, 104
    vel = -(c["pelvis"][b, 1] - c["pelvis"][a, 1]) / ((b - a) / c["_fps"]) / c["_L"]
    K = [dict(name="contact", t=10, ms=80, expr="determined"), dict(name="pass", t=24, ms=70, expr="determined"), dict(name="air", t=46, ms=70, air=1, expr="determined"),
         dict(name="contact2", t=58, ms=80, expr="determined"), dict(name="pass2", t=70, ms=70, expr="determined"), dict(name="air2", t=92, ms=70, air=1, expr="determined")]
    return gen("run", c, K, {"vel": vel, "center": True, "amp_base": amp(c, range(a, b), 1.5, 1.6), "lean": 14, "air_gain": 2.2, "arm": ARM_RUN, "lock": {"R": [[0, 1]], "L": [[3, 4]]}}, loop=True,
               note="CMU 02_03 jog cycle R strike 10 -> 104 (0.78 s real -> 440 ms); swing x1.5 about the cycle mean, +14 deg lean, flight x2.2; arm layer: pump gain 1.35, +22 deg forward bias, elbow >= 85")
# ------------------------------------------------------------------ dash / jump: same clips + arm layer
def A_dash():
    a = P("cmu/143_03.bvh", ref=0, travel=True, f0=120, f1=230); b = P("cmu/127_05.bvh", ref=0, yaw_frames=[96]); b2 = P("cmu/127_05.bvh", ref=0, yaw_frames=[230])  # skid/recover re-faced forward (travel-aligned 127_05 is turned 53/21 deg = read as a spin)
    oa = {"amp_base": amp(a, [100], 1.4), "lean": 8}
    Ka = [dict(name="antic", t=160, ms=100, expr="determined", opt={"amp_base": amp(a, [100], 1.3), "arm": {"R": {"set": [-35, 12, 80]}, "L": {"set": [55, 10, 100]}}}), dict(name="burst", t=180, ms=40, smear=1, arc=0, expr="effort", opt=dict(oa, arm={"R": {"set": [75, 10, 105]}, "L": {"set": [-50, 14, 80]}})),
          dict(name="smear", t=200, ms=40, smear=1, arc=0, expr="effort", opt=dict(oa, amp_base=amp(a, [100], 1.6), arm={"R": {"set": [-50, 14, 80]}, "L": {"set": [75, 10, 105]}}))]
    Kb = [dict(name="skid", t=96, ms=120, expr="determined", opt={"amp_base": amp(b, [300], 1.0), "head_level": 1.0, "lean": -6, "arm": {"set": [-20, 42, 30]}})]
    Kc = [dict(name="recover", t=230, ms=120, expr="smile", opt={"arm": {"set": [6, 14, 25]}})]
    oc = {"root": "none"}
    return gen("dash", None, None, None, segs=[(a, Ka, oc), (b, Kb, dict(oc, lock={"R": [[0]], "L": [[0]]})), (b2, Kc, oc)],
               note="CMU 143_03 start-to-run (antic/drive) + CMU 127_05 run-to-quick-stop (skid/rise); drive x1.4 + 8 deg lean; arm layer (set): sprint pump alternating fwd 75/elbow 105 vs back -50/elbow 80 in phase with the mocap legs; skid/recover each faced forward (no spin); skid balancing arms out-back (set -20/42/30), relaxed recover")
def A_jump():
    c = P("cmu/16_03.bvh", ref=0, yaw_frames=range(100, 300)); st = amp(c, [100], 1.9)
    o = {"amp_base": st}
    K = [dict(name="antic", t=126, ms=120, expr="determined"), dict(name="crouch", t=153, ms=80, expr="effort", opt=o), dict(name="launch", t=181, ms=50, expr="effort", opt={"arm": {"set": [75, 15, 30]}}),
         dict(name="rise", t=196, ms=80, air=1, expr="determined", opt=dict(o, arm={"set": [55, 70, 25]})), dict(name="apex", t=216, ms=160, air=1, expr="smile", opt={"amp_base": amp(c, [100], 2.4), "arm": {"set": [20, 135, 20]}}),
         dict(name="fall", t=240, ms=80, air=1, expr="determined", opt=dict(o, arm={"set": [20, 85, 25]})),
         dict(name="land", t=266, ms=140, expr="squash", opt=dict(o, arm={"set": [20, 40, 40]})), dict(name="recover", t=294, ms=120, expr="smile")]
    return gen("jump", c, K, {"root": "none", "air_gain": 2.0, "lock": {"R": [[0, 1, 2], [6, 7]], "L": [[0, 1, 2], [6, 7]]}},
               note="CMU 16_03 high jump (keys/timing as mocap strand); arm layer (absolute set pitch/abd/elbow): arms swing up from launch (fwd 75) through rise (55/70) to a cheerful V arms-up apex (abd 135), arms out to the sides on the fall (abd 85), soft balance on land (abd 40)")
def A_hurt():
    c = P("lafan1/pushAndStumble1_subject5.bvh", ref=0, yaw_frames=range(540, 548)); o = {"amp_base": amp(c, [545], 2.0)}
    K = [dict(name="hit", t=553, ms=80, expr="pain", opt=dict(o, lean=-10)), dict(name="recoil", t=558, ms=110, expr="pain", opt=dict(o, lean=-15, arm={"set": [70, 55, 100]})),
         dict(name="stagger", t=568, ms=160, expr="pain", opt=dict(o, amp_base=amp(c, [545], 1.2), lean=-12, arm={"set": [35, 50, 60]})), dict(name="recover", t=588, ms=160, expr="blink_closed")]
    return gen("hurt", c, K, {"root": "full", "root_gain": [0.35, 0.35]}, note="LaFAN1 pushAndStumble1_subject5 pushed from the front (NC-ND reference); reaction x2 about pre-hit frame 545; arm layer: startled flinch (hands up beside the head, set 70/55/100) on recoil, arms out for balance on the stagger (35/50/60), stagger leans back 12 deg with the step amp x1.2 (x2 read as a forward lunge)")
FIXED = ["idle", "run", "dash", "jump", "hurt"]
def save(acts):
    W = json.load(open(os.path.join(V2, "mocap", "work", "act.json")))
    W = {k: W[k] for k in ("idle", "walk", "run", "jump", "dash", "hurt")}
    wp = os.path.join(U, "work", "act.json"); os.makedirs(os.path.dirname(wp), exist_ok=True)
    if os.path.exists(wp): W.update(json.load(open(wp)))
    for a in acts: W[a] = globals()["A_" + a]()
    json.dump(W, open(wp, "w"), indent=0); print("act.json", list(W))
if __name__ == "__main__":
    save((sys.argv[1] if len(sys.argv) > 1 else ",".join(FIXED)).split(","))
