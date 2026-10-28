# actions.py: per-action clip choice + key selection + game timing -> ../work/act.json (pt.py table) and ../poses_mocap.json
#   .venv/bin/python -I actions.py [act,act]   (default all)
import sys, os, json, math
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import retarget as RT
ROOT = os.path.dirname(HERE); MC = os.path.join(os.path.dirname(os.path.dirname(ROOT)), ".scratch", "mocap")
VIEWS = RT.VIEWS
# light camera layer (per view): upper-body yaw toward the camera (deg, - = her front turns to screen/camera side), arm/blade depth flatten (0..1)
CAM = {"turn": {"S": 0, "SE": -8, "E": -12, "NE": -8, "N": 0},
       "flat_arm": {"S": 0.25, "SE": 0.25, "E": 0.3, "NE": 0.25, "N": 0.25},
       "flat_blade": {"S": 0.45, "SE": 0.45, "E": 0.5, "NE": 0.45, "N": 0.45},
       "carry": [-0.45, 0.75, -0.45], "carry_k": 0.2, "carry_view": {"S": [-0.8, 0.35, -0.5], "N": [-0.8, 0.35, -0.5]},
       "flat_blade_away": {"S": 0.9, "SE": 0.9, "E": 0.9, "NE": 0.6, "N": 0.6}}  # blade pointing away from the camera is laid (almost) into the screen plane -> stays visible
def zlow(c, s): return (np.minimum(c["an." + s][:, 2], c["toe." + s][:, 2]) - c["_floor"][s]) / c["_L"]
def events_gait(c, a, b):
    """gait events in [a, b): R/L strikes, pelvis min/max, passing (ankle y cross) -- printed to choose keys"""
    zR, zL = zlow(c, "R"), zlow(c, "L"); pz = c["pelvis"][:, 2] / c["_L"]; dy = (c["an.R"][:, 1] - c["an.L"][:, 1]) / c["_L"]
    ev = []
    for t in range(a + 1, b):
        if zR[t] < 0.03 <= zR[t - 1]: ev.append((t, "R_strike"))
        if zL[t] < 0.03 <= zL[t - 1]: ev.append((t, "L_strike"))
        if zR[t] >= 0.03 > zR[t - 1]: ev.append((t, "R_off"))
        if zL[t] >= 0.03 > zL[t - 1]: ev.append((t, "L_off"))
        if np.sign(dy[t]) != np.sign(dy[t - 1]): ev.append((t, "pass"))
        if 1 < t < b - 1 and pz[t] < pz[t - 1] and pz[t] <= pz[t + 1]: ev.append((t, "pel_min"))
        if 1 < t < b - 1 and pz[t] > pz[t - 1] and pz[t] >= pz[t + 1]: ev.append((t, "pel_max"))
    return ev
def gen(act, c, keys, opt, loop=False, note="", segs=None):
    """segs: optional list of (clip, keys, opt) for multi-clip actions (frames concatenated in order)"""
    segs = segs or [(c, keys, opt)]; frames = []
    for c_, keys_, opt_ in segs:
        o = dict(CAM); o.update(opt_)
        if o.get("blade") == "grip" and "grip" not in o: o["grip"], _ = RT.grip_axis(c_, range(c_["_T"]))
        fr = [{"name": k["name"], "ms": k["ms"], "smear": k.get("smear", 0), "arc": k.get("arc", 1), "expr": k.get("expr", "neutral"), "t": k["t"], "src": c_["_src"]} for k in keys_]
        for v in VIEWS:
            ps, _ = RT.build(c_, keys_, v, o)
            for f, p_ in zip(fr, ps): f[v] = p_
        frames += fr
    return {"loop": loop, "frames": frames, "src": sorted({f["src"] for f in frames}), "note": note}
def P(path, **kw):
    c = RT.prep(os.path.join(MC, path), **kw); c["_src"] = path; return c
# ------------------------------------------------------------------ actions
def walk():
    c = P("bandai1/dataset-1_walk_active_001.bvh", travel=True, ref=0)
    a, b = 58, 90  # one cycle R strike -> R strike (32 f @30 = 1.07 s real)
    vel = -(c["pelvis"][b, 1] - c["pelvis"][a, 1]) / ((b - a) / c["_fps"]) / c["_L"]
    ev = events_gait(c, a, b + 1); print("walk events", ev, "vel", round(vel, 2))
    return c, a, b, vel, ev
def run():
    c = P("cmu/09_01.bvh", travel=True, ref=0)
    a, b = 43, 131
    vel = -(c["pelvis"][b, 1] - c["pelvis"][a, 1]) / ((b - a) / c["_fps"]) / c["_L"]
    ev = events_gait(c, a, b + 1); print("run events", ev, "vel", round(vel, 2))
    return c, a, b, vel, ev
def amp(c, frames, g, gz=None): b = RT.base_pose(c, frames); b["g"] = g; b["gz"] = g if gz is None else gz; return b
def A_walk():  # Bandai1 walk_active, one cycle; stride/arm swing pushed x1.25 about the cycle mean
    c, a, b, vel, ev = walk()
    K = [dict(name="contact", t=58, ms=110), dict(name="down", t=61, ms=100), dict(name="pass", t=66, ms=110),
         dict(name="contact2", t=74, ms=110), dict(name="down2", t=77, ms=100), dict(name="pass2", t=82, ms=110)]
    return gen("walk", c, K, {"vel": vel, "center": True, "amp_base": amp(c, range(a, b), 1.45, 1.6), "lean": 4, "carry_k": 0.05, "spread": 0.03, "lock": {"R": [[0, 1, 2, 3]], "L": [[3, 4, 5]]}}, loop=True,
               note="Bandai1 walk_active cycle 58-90; contact/down/pass keys at gait events; swing x1.25 about the cycle mean")
def A_run():
    c, a, b, vel, ev = run()
    K = [dict(name="contact", t=43, ms=80, expr="determined"), dict(name="pass", t=55, ms=70, expr="determined"), dict(name="air", t=68, ms=70, air=1, expr="determined"),
         dict(name="contact2", t=87, ms=80, expr="determined"), dict(name="pass2", t=99, ms=70, expr="determined"), dict(name="air2", t=112, ms=70, air=1, expr="determined")]
    return gen("run", c, K, {"vel": vel, "center": True, "amp_base": amp(c, range(a, b), 1.7, 1.6), "lean": 20, "air_gain": 2.2, "carry": [-0.35, 0.85, 0.3], "carry_k": 0.1, "lock": {"R": [[0, 1]], "L": [[3, 4]]}}, loop=True,
               note="CMU 09_01 cycle 43-131 (0.73 s real -> 440 ms); swing x1.3 about the cycle mean, +12 deg lean, flight x1.6")
def A_idle():
    c = P("bandai1/dataset-1_slash_normal_001.bvh", ref=0, yaw_frames=range(120, 170))
    K = [dict(name="up", t=138, ms=300), dict(name="settle", t=144, ms=150), dict(name="down", t=150, ms=150),
         dict(name="down_hold", t=162, ms=300), dict(name="rise", t=156, ms=150), dict(name="up2", t=144, ms=150)]
    return gen("idle", c, K, {"blade": "grip", "amp": (162, 8.0), "spread": 0.07, "blade_pitch": 20, "turn": {"S": 0, "SE": -16, "E": -18, "NE": -12, "N": 0}, "root": "none", "lock": {"R": [list(range(6))], "L": [list(range(6))]}}, loop=True,
               note="Bandai guard (chudan) settling 126->162 ping-ponged, real micro-motion x4 about guard frame 162, stance +0.07 L per foot")
def A_jump():
    c = P("cmu/16_03.bvh", ref=0, yaw_frames=range(100, 300)); st = amp(c, [100], 1.9)
    o = {"amp_base": st}
    K = [dict(name="antic", t=126, ms=120, expr="determined"), dict(name="crouch", t=153, ms=80, expr="effort", opt=o), dict(name="launch", t=181, ms=50, expr="effort"),
         dict(name="rise", t=196, ms=80, air=1, expr="determined", opt=o), dict(name="apex", t=216, ms=160, air=1, opt={"amp_base": amp(c, [100], 2.4)}), dict(name="fall", t=240, ms=80, air=1, expr="determined", opt=o),
         dict(name="land", t=266, ms=140, expr="squash", opt=o), dict(name="recover", t=294, ms=120)]
    return gen("jump", c, K, {"root": "none", "air_gain": 2.0, "carry_k": 0.25, "carry": [-0.7, 0.5, -0.3], "lock": {"R": [[0, 1, 2], [6, 7]], "L": [[0, 1, 2], [6, 7]]}},
               note="CMU 16_03 high jump; crouch/air/land pushed x1.35 (apex tuck x1.6) about standing frame 100; height x1.8")
def A_dash():
    a = P("cmu/143_03.bvh", ref=0, travel=True, f0=120, f1=230); b = P("cmu/127_05.bvh", ref=0, travel=True, f0=0, f1=240)
    oa = {"amp_base": amp(a, [100], 1.4), "lean": 22}
    Ka = [dict(name="antic", t=160, ms=100, expr="determined", opt={"amp_base": amp(a, [100], 1.3)}), dict(name="burst", t=180, ms=40, smear=1, arc=0, expr="effort", opt=oa),
          dict(name="smear", t=200, ms=40, smear=1, arc=0, expr="effort", opt=dict(oa, amp_base=amp(a, [100], 1.6)))]
    Kb = [dict(name="skid", t=96, ms=120, expr="determined", opt={"amp_base": amp(b, [300], 1.0), "head_level": 0.6}), dict(name="recover", t=230, ms=120)]
    oc = {"root": "none", "carry": [-0.3, 0.92, 0.05], "carry_k": 0.1}
    return gen("dash", None, None, None, segs=[(a, Ka, oc), (b, Kb, dict(oc, lock={"R": [[0]], "L": [[0, 1]]}))],
               note="CMU 143_03 start-to-run (antic/drive) + CMU 127_05 run-to-quick-stop (skid/rise); drive pushed x1.4 + 14 deg lean")
def A_slash():
    c = P("bandai1/dataset-1_slash_normal_002.bvh", ref=0, yaw_frames=range(20, 30)); o = {"amp_base": amp(c, [20], 1.3)}
    K = [dict(name="antic", t=28, ms=160, expr="determined", opt={"blade_pitch": 15}), dict(name="windup", t=36, ms=100, expr="determined", opt=o), dict(name="smear", t=59, ms=40, smear=1, expr="shout", opt=o),
         dict(name="impact", t=62, ms=140, smear=1, expr="shout", opt=o), dict(name="follow", t=65, ms=80, expr="shout", opt=o), dict(name="recover", t=102, ms=100), dict(name="settle", t=126, ms=100, expr="smile")]
    return gen("slash", c, K, {"blade": "grip", "root": "full", "root_gain": [0.5, 0.5], "lock": {"L": [list(range(7))], "R": [[0, 1], [3, 4, 5, 6]]}},
               note="Bandai slash_normal_002 rising diagonal cut; windup..follow pushed x1.3 about the guard frame 20; zanshin hold 66-90 cut")
def A_slash_cmu():
    c = P("cmu/02_08.bvh", ref=0, yaw_frames=range(805, 830)); o = {"amp_base": amp(c, [740], 1.2)}
    K = [dict(name="antic", t=745, ms=160, expr="determined"), dict(name="windup", t=772, ms=100, expr="determined", opt=o), dict(name="smear", t=808, ms=40, smear=1, expr="shout", opt=o),
         dict(name="impact", t=826, ms=120, smear=1, expr="shout", opt=o), dict(name="follow", t=842, ms=80, expr="shout", opt=o), dict(name="recover", t=862, ms=120), dict(name="settle", t=885, ms=100, expr="smile")]
    return gen("slash", c, K, {"blade": "fore", "root": "full", "root_gain": [0.5, 0.5], "lock": {"L": [list(range(7))], "R": [list(range(7))]}},
               note="CMU 02_08 swordplay one-handed horizontal backhand sweep (left -> right, waist -> chest), ends in a two-handed high guard")
def A_overhead():
    c = P("bandai1/dataset-1_slash_normal_001.bvh", ref=0, yaw_frames=range(160, 170)); g = amp(c, [160], 1.4); g2 = amp(c, [160], 1.8); h = amp(c, [160], 1.4, 3.0)
    K = [dict(name="antic", t=176, ms=140, expr="determined"), dict(name="raise", t=196, ms=150, expr="determined", opt={"amp_base": g2, "lean": -8}), dict(name="smear", t=206, ms=40, smear=1, expr="shout", opt={"amp_base": g}),
         dict(name="impact", t=212, ms=160, smear=1, expr="shout", opt={"amp_base": h, "blade_pitch": 25}), dict(name="follow", t=218, ms=80, expr="shout", opt={"amp_base": h, "blade_pitch": 30}), dict(name="recover", t=240, ms=140, opt={"blade_pitch": 25})]
    return gen("overhead", c, K, {"blade": "grip", "root": "full", "lock": {"L": [list(range(6))], "R": [list(range(6))]}},
               note="Bandai slash_normal_001 two-handed vertical cut; raise x1.4, impact x1.3 (drop x2) about guard frame 160")
def A_hurt():
    c = P("lafan1/pushAndStumble1_subject5.bvh", ref=0, yaw_frames=range(540, 548)); o = {"amp_base": amp(c, [545], 2.0)}
    K = [dict(name="hit", t=553, ms=80, expr="pain", opt=dict(o, lean=-10)), dict(name="recoil", t=558, ms=110, expr="pain", opt=dict(o, lean=-15)), dict(name="stagger", t=568, ms=160, expr="pain", opt=o), dict(name="recover", t=588, ms=160, expr="blink_closed")]
    return gen("hurt", c, K, {"root": "full", "root_gain": [0.35, 0.35], "carry": [-0.5, 0.75, -0.2], "carry_k": 0.3}, note="LaFAN1 pushAndStumble1_subject5 pushed from the front (NC-ND reference); reaction x1.5 about pre-hit frame 545")

# ------------------------------------------------------------------ THROW strand
AY = float(os.environ.get("AY", "40"))
TCAM = {"arm_yaw": {"S": AY, "SE": AY / 2, "E": 0, "NE": AY / 2, "N": AY}, "turn": {"S": 0, "SE": -10, "E": -16, "NE": -10, "N": 0}, "flat_arm": {"S": 0.45, "SE": 0.35, "E": 0.3, "NE": 0.35, "N": 0.45}}
def A_throw():
    """CMU 124_01 baseball pitch (overhand). keys at the real extremes; release punch = short release + held follow-through"""
    c = P("cmu/124_01.bvh", ref=300, travel=True, f0=300, f1=540)
    g = lambda k: amp(c, [300], k)
    LG = float(os.environ.get("LG", "0.7")); LN = float(os.environ.get("LN", "-10"))
    K = [dict(name="ready", t=300, ms=220, expr="determined"),
         dict(name="windup", t=396, ms=160, expr="determined", opt={"amp_base": g(1.1)}),
         dict(name="stride", t=427, ms=60, expr="effort", opt={"amp_base": g(1.1), "leg_gain": LG}),
         dict(name="release", t=448, ms=50, expr="shout", opt={"amp_base": g(1.15), "leg_gain": LG, "lean": LN}),
         dict(name="follow", t=455, ms=140, expr="shout", opt={"amp_base": g(1.15), "leg_gain": LG, "lean": LN}),
         dict(name="follow2", t=490, ms=100, expr="determined", opt={"amp_base": g(1.1), "leg_gain": LG, "lean": LN / 2}),
         dict(name="recover", t=560, ms=140, expr="smile"),
         dict(name="settle", t=600, ms=200, expr="smile")]
    o = dict(TCAM, blade="none", root="full", root_gain=[0.35, 0.35], lock={"R": [[0, 1, 2, 3]], "L": [[2, 3, 4, 5, 6, 7]]})
    return gen("throw", c, K, o, note="CMU 124_01 baseball pitch: ready=set 300, windup=arm back/knee up/hips closed 396, stride=front foot plants + arm cocked high 432, release=hand in front of the head 444 (peak 13 L/s at 450), follow=arm down across 462, follow2=back leg swings 480, recover 534")
def save(acts):
    wp = os.path.join(ROOT, "work", "act.json"); W = json.load(open(wp)) if os.path.exists(wp) else {}; W = {k: v for k, v in W.items() if k in [a.split(":")[0] for a in acts] or k == "throw"}
    for a in acts: W[a.split(":")[0]] = globals()["A_" + a.split(":")[-1]]()
    json.dump(W, open(wp, "w"), indent=0); print("act.json", list(W))
if __name__ == "__main__":
    save((sys.argv[1] if len(sys.argv) > 1 else "throw").split(","))
