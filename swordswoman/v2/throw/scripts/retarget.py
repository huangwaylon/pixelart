# retarget.py: mocap (canonical joints from mc.py) -> rig E pose dicts (rig_lib.pose keys: per-bone Euler deg, Q = D_parent^-1 D_child in armature axes)
# Direction-based retarget (scale free): torso/neck/head = deltas vs the actor's neutral reference frame, limbs = absolute segment directions,
# arms split at the elbow (ELBOW=1 rig), katana direction from the mocap hand frame (grip axis calibrated on two-handed frames) or a forearm-relative carry.
# Root: auto-grounded by rig_lib, root offset `off` = scaled pelvis xy motion, air frames absz + lift; foot locks by 2-bone IK on contact frames.
# Camera layer (light, per view): upper-body yaw toward the camera, arm/blade depth flattened toward the screen plane.
import json, os, math
import numpy as np
import mc
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
RJ = json.load(open(os.path.join(ROOT, "rest_F.json"))); B = RJ["bones"]; PT = RJ["parts"]
ELB_T = float(os.environ.get("ELB_T", "0.5")); KL = 0.74
def V(x): return np.array(x, float)
H = lambda n: V(B[n]["head"])
REST = {"pelvis": H("hips"), "spine": H("spine"), "chest": H("chest"), "neck": H("neck"), "head": H("head")}
for s in "RL":
    REST["hip." + s] = H("thigh." + s); REST["kn." + s] = H("shin." + s); REST["an." + s] = H("foot." + s)
    REST["toe." + s] = V(PT["shin_" + s]["toe"]); REST["heel." + s] = V(PT["shin_" + s]["heel"])
    REST["sh." + s] = H("upper_arm." + s); REST["wr." + s] = H("hand." + s); REST["el." + s] = REST["sh." + s] + ELB_T * (REST["wr." + s] - REST["sh." + s])
LEG = np.linalg.norm(REST["kn.R"] - REST["hip.R"]) + np.linalg.norm(REST["an.R"] - REST["kn.R"])  # hip->ankle 0.622
VIEWS = ["S", "SE", "E", "NE", "N"]
AZ = {"SE": (-1, -1), "E": (-1, 0), "S": (0, -1), "NE": (-1, 1), "N": (0, 1)}
def nz(v): n = np.linalg.norm(v, axis=-1, keepdims=True); return v / np.maximum(n, 1e-9)
def Rz(a):
    c, s = math.cos(a), math.sin(a); return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])
def frame_up(up, x):  # columns x, y, z with z = up (primary), x from the side vector
    z = nz(up); x = nz(x - z * (x @ z)); y = np.cross(z, x); return np.stack([x, y, z], 1)
def frame_x(x, up):  # x primary (hip line), z from up
    x = nz(x); z = nz(up - x * (up @ x)); y = np.cross(z, x); return np.stack([x, y, z], 1)
def frame_ab(a, b):  # a primary, b secondary (generic)
    a = nz(a); b = nz(b - a * (b @ a)); return np.stack([a, b, np.cross(a, b)], 1)
def swing(u, v):  # minimal rotation u -> v
    u, v = nz(u), nz(v); c = float(u @ v); ax = np.cross(u, v); s = np.linalg.norm(ax)
    if s < 1e-8: return np.eye(3) if c > 0 else rot_axis(np.array([1.0, 0, 0]) if abs(u[0]) < .9 else np.array([0, 1.0, 0]), math.pi)
    return rot_axis(ax / s, math.atan2(s, c))
def rot_axis(a, t):
    a = nz(a); K = np.array([[0, -a[2], a[1]], [a[2], 0, -a[0]], [-a[1], a[0], 0]]); return np.eye(3) + math.sin(t) * K + (1 - math.cos(t)) * K @ K
def euler_xyz(R):  # R = Rz Ry Rx (Blender 'XYZ')
    y = math.asin(max(-1, min(1, -R[2, 0]))); x = math.atan2(R[2, 1], R[2, 2]); z = math.atan2(R[1, 0], R[0, 0])
    return [round(math.degrees(x), 1), round(math.degrees(y), 1), round(math.degrees(z), 1)]
# ---------------------------------------------------------------- clip preparation
def prep(path, ref=0, f0=0, f1=None, fps=None, yaw_frames=None, travel=False):
    """load + canonical joints, aligned so the character faces -Y (her forward) over yaw_frames (or travels along -Y if travel)."""
    cl = mc.load(path); c = mc.canon(cl); fps = fps or (120 if mc.kind(path) == "cmu" else cl["fps"]); L = mc.leglen(c)
    T = len(c["pelvis"]); f1 = T if f1 is None else f1
    def facing(t):
        x = c["hip.L"][t] - c["hip.R"][t] + c["sh.L"][t] - c["sh.R"][t]; f = np.cross(x, [0, 0, 1.0]); return math.atan2(f[1], f[0])
    if travel:
        d = c["pelvis"][f1 - 1] - c["pelvis"][f0]; ang = math.atan2(d[1], d[0])
    else:
        fr = yaw_frames or range(f0, f1); ang = math.atan2(np.mean([math.sin(facing(t)) for t in fr]), np.mean([math.cos(facing(t)) for t in fr]))
    R = Rz(-math.pi / 2 - ang)  # rotate facing -> -Y
    o = c["pelvis"][f0].copy(); o[2] = 0
    out = {k: (v - o) @ R.T for k, v in c.items() if not k.startswith("G_")}
    for k in ("G_head", "G_pelvis", "G_wr.R", "G_wr.L"): out[k] = R @ c[k]
    if ref == "zero":
        z = mc.canon(cl, zero=True); FR = torso_frames(z, 0); Gh = z["G_head"][0]
    else:
        rr = Rz(-math.pi / 2 - facing(ref)) @ R.T  # aligned coords -> ref-facing coords
        tmp = {k: v for k, v in out.items()}; FR = {b: rr @ M for b, M in torso_frames(tmp, ref).items()}; Gh = rr @ out["G_head"][ref]
    out["_FR"] = FR; out["_Gh"] = Gh; out["_L"] = L; out["_fps"] = fps; out["_s"] = LEG / L; out["_T"] = T
    floor = {s: np.percentile(np.minimum(out["an." + s][:, 2], out["toe." + s][:, 2]), 3) for s in "RL"}
    out["_floor"] = floor
    return out
def torso_frames(c, t):
    hipx = c["hip.L"][t] - c["hip.R"][t]; shx = c["sh.L"][t] - c["sh.R"][t]
    return {"hips": frame_x(hipx, c["spine"][t] - c["pelvis"][t] + c["chest"][t] - c["pelvis"][t]),
            "spine": frame_up(c["chest"][t] - c["spine"][t], hipx / np.linalg.norm(hipx) + shx / np.linalg.norm(shx)),
            "chest": frame_up(c["neck"][t] - c["chest"][t], shx), "neck": frame_up(c["head"][t] - c["neck"][t], shx)}
def grip_axis(c, frames, dist=0.4):
    """blade direction in the right-hand (wrist joint) local frame, from two-handed frames (blade ~ L wrist -> R wrist)."""
    acc = []
    for t in frames:
        d = c["wr.R"][t] - c["wr.L"][t]
        if np.linalg.norm(d) < dist * c["_L"]: acc.append(c["G_wr.R"][t].T @ nz(d))
    if not acc: return None, 0
    g = nz(np.mean(acc, 0)); spread = float(np.mean([a @ g for a in acc])); return g, spread
# ---------------------------------------------------------------- per-frame retarget
def solve(c, t, view=None, opt=None):
    """returns (D dict bone -> world 3x3, targets) for mocap frame t (fractional frames are lerped on joints)"""
    opt = opt or {}
    t0 = int(math.floor(t)); a = t - t0; t1 = min(t0 + 1, c["_T"] - 1)
    J = {k: (v[t0] * (1 - a) + v[t1] * a) for k, v in c.items() if not k.startswith(("_", "G_"))}
    Gh = c["G_head"][t0]; Gw = c["G_wr.R"][t0]
    amp = opt.get("amp")  # idle: amplify the real micro-motion about a base frame (joints relative to the pelvis, rotations by power)
    if amp:
        tb, g = amp; Jb = {k: c[k][tb] for k in J}
        Pb, P0 = Jb["pelvis"], J["pelvis"]; Pn = Pb + g * (P0 - Pb)
        J = {k: (Pn if k == "pelvis" else Pn + (Jb[k] - Pb) + g * ((J[k] - P0) - (Jb[k] - Pb))) for k in J}
        Gh = scale_rot(Gh @ c["G_head"][tb].T, g) @ c["G_head"][tb]; Gw = scale_rot(Gw @ c["G_wr.R"][tb].T, g) @ c["G_wr.R"][tb]
    ab = opt.get("amp_base")  # push the extremes: joint offsets (relative to the pelvis) amplified about a base pose (cycle mean or a neutral frame); pelvis height too
    if ab:
        Jb, g, gz = ab["J"], ab["g"], ab.get("gz", ab["g"]); P0 = J["pelvis"]; Pn = P0.copy(); Pn[2] = ab["pz"] + gz * (P0[2] - ab["pz"])
        J = {k: (Pn if k == "pelvis" else Pn + Jb[k] + g * ((J[k] - P0) - Jb[k])) for k in J}
    lg = opt.get("leg_gain")  # THROW: damp/push the legs only (knee/ankle/toe offsets from the hip) about the amp_base pose
    if lg is not None and ab:
        Jb = ab["J"]
        for s_ in "RL":
            for k in ("kn", "an", "toe", "heel"):
                kk = f"{k}.{s_}"
                if kk in J: J[kk] = J["hip." + s_] + (Jb[kk] - Jb["hip." + s_]) + lg * ((J[kk] - J["hip." + s_]) - (Jb[kk] - Jb["hip." + s_]))
    ln = opt.get("lean", 0.0)  # extra forward lean of the upper body about the pelvis (deg, + = forward)
    if ln:
        fw = J["chest"] - J["pelvis"]; hipx = nz(J["hip.L"] - J["hip.R"]); Rl = rot_axis(hipx, math.radians(ln))  # about her left axis: + tips the top forward (-y)
        for k in list(J):
            if k.split(".")[0] in ("spine", "chest", "neck", "head", "head_end", "sh", "el", "wr", "hd"): J[k] = J["pelvis"] + Rl @ (J[k] - J["pelvis"])
        Gh = Rl @ Gh; Gw = Rl @ Gw
    sp = opt.get("spread", 0.0)  # widen the stance (fraction of mocap leg length per foot, knees half)
    if sp:
        hipx = nz(J["hip.L"] - J["hip.R"]); hipx[2] = 0; hipx = nz(hipx)
        for s_, sg in (("R", -1), ("L", 1)):
            for k, f in (("kn", 0.5), ("an", 1.0), ("toe", 1.0)): J[f"{k}.{s_}"] = J[f"{k}.{s_}"] + sg * f * sp * c["_L"] * hipx
    cj = {k: v[None] for k, v in J.items()}
    F = torso_frames(cj, 0); FR = c["_FR"]
    # camera layer: upper-body yaw toward camera + depth flatten (applied to the joint targets)
    beta = opt.get("turn", {}).get(view, 0.0) if view else 0.0
    D = {}
    for b in ("hips", "spine", "chest", "neck"):
        D[b] = F[b] @ FR[b].T
    # torso amplification / damping (keep realistic; default 1)
    for b, k in opt.get("torso_gain", {}).items():
        D[b] = scale_rot(D[b], k)
    Rb = Rz(math.radians(beta))
    D["spine"] = rot_mix(Rb, 0.5) @ D["spine"]; D["chest"] = Rb @ D["chest"]; D["neck"] = Rb @ D["neck"]
    D["head"] = Rb @ Gh @ c["_Gh"].T
    if opt.get("head_level"):  # (D neck/head computed above)  # keep the eyes readable: blend head toward the neck orientation (removes extreme nods)
        D["head"] = rot_lerp(D["head"], D["neck"], opt["head_level"])
    h = None
    if view:
        cz = np.array([*AZ[view], 0.0]); cz /= np.linalg.norm(cz); h = np.array([-cz[1], cz[0], 0.0])  # unused (screen right)
    def flat(v, k, away=None):  # remove a fraction k of the depth component (camera horizontal axis); `away` = fraction used when pointing away from the camera
        if not view or not k: return v
        d = -np.array([*AZ[view], 0.0]); d /= np.linalg.norm(d)  # d = viewing direction (camera -> scene)
        dep = v @ d; kk = away if (away is not None and dep > 0) else k
        return v - kk * dep * d
    ka = opt.get("flat_arm", {}).get(view, 0.0) if view else 0.0; kb = opt.get("flat_blade", {}).get(view, 0.0) if view else 0.0
    # FK of our torso to get shoulder positions (needed only for directions -> not needed); limbs from mocap segment directions
    for s in "RL":
        up = J["el." + s] - J["sh." + s]; fo = J["wr." + s] - J["el." + s]
        if beta: up = Rb @ up; fo = Rb @ fo
        ay = opt.get("arm_yaw", {}).get(view, 0.0) if (view and s == "R") else 0.0  # THROW cheat: rotate the throwing arm's arc about world Z (depth -> screen plane)
        if ay: Ra = Rz(math.radians(ay)); up = Ra @ up; fo = Ra @ fo
        up = flat(up, ka); fo = flat(fo, ka)
        if s == "R": fo_R = fo
        Dp = D["chest"]; rest_up = REST["el." + s] - REST["sh." + s]; rest_fo = REST["wr." + s] - REST["el." + s]
        D["upper_arm." + s] = swing(Dp @ rest_up, up) @ Dp
        D["forearm." + s] = swing(D["upper_arm." + s] @ rest_fo, fo) @ D["upper_arm." + s]
        D["hand." + s] = D["forearm." + s]
        th = J["kn." + s] - J["hip." + s]; sh = J["an." + s] - J["kn." + s]; ft = J["toe." + s] - J["an." + s]
        D["thigh." + s] = swing(D["hips"] @ (REST["kn." + s] - REST["hip." + s]), th) @ D["hips"]
        D["shin." + s] = frame_ab(sh, ft) @ frame_ab(REST["an." + s] - REST["kn." + s], REST["toe." + s] - REST["an." + s]).T
        D["foot." + s] = D["shin." + s]
    # katana
    bm = opt.get("blade", "carry")
    if bm == "none":  # THROW: unarmed, hand continues the forearm (wrist flex from the mocap hand frame is not trusted: CMU finger sites)
        return D, J
    if bm == "grip":
        b = Gw @ opt["grip"]
    elif bm == "fore":  # one-handed cut: blade continues the forearm, cocked a little toward her up/forward
        fw_ = D["hips"] @ np.array([0, -1.0, 0]); fw_[2] = 0; fw_ = nz(fw_)
        b = nz(nz(fo_R) + opt.get("fore_up", 0.3) * np.array([0, 0, 1.0]) + opt.get("fore_fwd", 0.0) * fw_)
    elif bm == "two":
        b = nz(J["wr.R"] - J["wr.L"])
    else:
        # carry: blade trailing back-down in her yaw frame (x her left, y back, z up), swung by a fraction of the forearm pitch (rigid-ish wrist)
        fw = D["hips"] @ np.array([0, -1.0, 0]); fw[2] = 0; fw = nz(fw); back = -fw; left = nz(np.cross([0, 0, 1.0], fw))
        fa = nz(fo_R); pitch = math.atan2(float(fa @ fw), float(-fa[2]))
        cv = opt.get("carry_view", {}).get(view) if view else None  # per-view carry (S/N: more outward so the blade is not a depth stub)
        cv = cv if cv is not None else opt.get("carry", [-0.3, 0.6, -0.75])
        b0 = np.stack([left, back, np.array([0, 0, 1.0])], 1) @ nz(np.array(cv))
        b = rot_axis(left, -opt.get("carry_k", 0.45) * pitch) @ b0
    if beta and bm != "carry": b = Rb @ b
    bp = opt.get("blade_pitch", 0.0)  # game cheat: tip forward-down (+) / back-up (-) about her left axis
    if bp:
        fw_ = D["hips"] @ np.array([0, -1.0, 0]); fw_[2] = 0; lf_ = nz(np.cross([0, 0, 1.0], nz(fw_))); b = rot_axis(lf_, math.radians(bp)) @ b
    b = nz(flat(b, kb, opt.get("flat_blade_away", {}).get(view) if view else None))
    D["hand.R"] = swing(D["forearm.R"] @ np.array([0, -1.0, 0]), b) @ D["forearm.R"]
    return D, J
def scale_rot(R, k):
    from scipy.spatial.transform import Rotation as SR
    return SR.from_rotvec(SR.from_matrix(R).as_rotvec() * k).as_matrix()
def rot_mix(R, k): return scale_rot(R, k)
def rot_lerp(A, Bm, k):  # k=0 -> A, k=1 -> B
    return scale_rot(Bm @ A.T, k) @ A
PARENT = {"hips": None, "spine": "hips", "chest": "spine", "neck": "chest", "head": "neck"}
for s in "RL":
    PARENT.update({f"upper_arm.{s}": "chest", f"forearm.{s}": f"upper_arm.{s}", f"hand.{s}": f"forearm.{s}", f"thigh.{s}": "hips", f"shin.{s}": f"thigh.{s}", f"foot.{s}": f"shin.{s}"})
def fk(D, root=np.zeros(3)):
    P = {"pelvis": root + REST["pelvis"]}
    P["spine"] = P["pelvis"] + D["hips"] @ (REST["spine"] - REST["pelvis"]); P["chest"] = P["spine"] + D["spine"] @ (REST["chest"] - REST["spine"])
    P["neck"] = P["chest"] + D["chest"] @ (REST["neck"] - REST["chest"]); P["head"] = P["neck"] + D["neck"] @ (REST["head"] - REST["neck"])
    for s in "RL":
        P["hip." + s] = P["pelvis"] + D["hips"] @ (REST["hip." + s] - REST["pelvis"]); P["kn." + s] = P["hip." + s] + D["thigh." + s] @ (REST["kn." + s] - REST["hip." + s])
        for k in ("an", "toe", "heel"): P[f"{k}.{s}"] = P["kn." + s] + D["shin." + s] @ (REST[f"{k}.{s}"] - REST["kn." + s])
        P["sh." + s] = P["chest"] + D["chest"] @ (REST["sh." + s] - REST["chest"]); P["el." + s] = P["sh." + s] + D["upper_arm." + s] @ (REST["el." + s] - REST["sh." + s])
        P["wr." + s] = P["el." + s] + D["forearm." + s] @ (REST["wr." + s] - REST["el." + s])
    P["tip"] = P["wr.R"] + D["hand.R"] @ np.array([0, -(0.12 + KL), 0])
    return P
def low(P): return min(P[f"{k}.{s}"][2] for k in ("toe", "heel") for s in "RL") - 0.03  # sole below the toe/heel landmarks (~0.03)
def leg_ik(D, P, s, A):
    """re-aim thigh/shin so the ankle reaches A (world), knee bends in the current knee plane, foot orientation kept"""
    hip = P["hip." + s]; L1 = np.linalg.norm(REST["kn." + s] - REST["hip." + s]); L2 = np.linalg.norm(REST["an." + s] - REST["kn." + s])
    dv = A - hip; Dd = min(np.linalg.norm(dv), 0.999 * (L1 + L2)); dn = nz(dv)
    kn0 = P["kn." + s] - hip; bend = kn0 - dn * (kn0 @ dn); bend = nz(bend) if np.linalg.norm(bend) > 1e-5 else nz(np.cross(dn, [1.0, 0, 0]) * -1)
    ca = (L1 * L1 + Dd * Dd - L2 * L2) / (2 * L1 * Dd); ca = max(-1, min(1, ca)); sa = math.sqrt(1 - ca * ca)
    knee = hip + dn * L1 * ca + bend * L1 * sa; ank = hip + dn * Dd
    ft = D["shin." + s] @ (REST["toe." + s] - REST["an." + s])
    D["thigh." + s] = swing(D["hips"] @ (REST["kn." + s] - REST["hip." + s]), knee - hip) @ D["hips"]
    D["shin." + s] = frame_ab(ank - knee, ft) @ frame_ab(REST["an." + s] - REST["kn." + s], REST["toe." + s] - REST["an." + s]).T
    D["foot." + s] = D["shin." + s]
def to_pose(D, extra=None):
    p = {}
    for b, par in PARENT.items():
        if b.startswith("foot") or b == "hand.L": continue
        Q = (D[par].T @ D[b]) if par else D[b]
        e = euler_xyz(Q)
        if b == "upper_arm.R": e[1] = round(e[1] - 12, 1)
        if b == "upper_arm.L": e[1] = round(e[1] + 12, 1)
        p[b] = e
    p.update(extra or {})
    return p
# ---------------------------------------------------------------- action builder
def contacts(c, s, h_thr=0.06, v_thr=0.9, vel=0.0):
    """per frame: foot s planted? (low + slow, in a frame moving with -vel along her forward axis)"""
    L = c["_L"]; fps = c["_fps"]; z = np.minimum(c["an." + s][:, 2], c["toe." + s][:, 2]) - c["_floor"][s]
    p = c["an." + s].copy(); p[:, 1] -= -vel * np.arange(len(p)) / fps * L  # treadmill frame
    v = np.linalg.norm(np.gradient(p[:, :2], axis=0), axis=-1) * fps / L
    return (z < h_thr * L) & (v < v_thr)
def build(c, keys, view, opt):
    """keys: list of dicts {t, name, ms, air, extra}. Returns rig_lib pose dicts for one view.
    opt: vel (treadmill speed, mocap leg lengths/s, removed from the root for in-place loops), root ('full'|'x'|'none'), lock {'R': [[key idx...], ...], 'L': [...]}"""
    s_ = c["_s"]; fps = c["_fps"]; vel = opt.get("vel", 0.0); t_ref = keys[0]["t"]
    Ds, offs = [], []
    for k in keys:
        t = k["t"]; D, J = solve(c, t, view, dict(opt, **k.get("opt", {})))
        off = (J["pelvis"][:2] - c["pelvis"][int(t_ref)][:2]) * s_; off[1] += vel * (t - t_ref) / fps * LEG
        rm = opt.get("root", "full"); off = off * {"full": [1, 1], "x": [1, 0], "none": [0, 0], "y": [0, 1]}[rm]
        off = off * np.array(opt.get("root_gain", [1.0, 1.0]))
        Ds.append(D); offs.append(off)
    if opt.get("center", False):  # loops: centre the root sway on the cell
        m = np.mean(offs, 0); offs = [o - m for o in offs]
    Ps = [fk(D, np.array([o[0], o[1], 0.0])) for D, o in zip(Ds, offs)]
    for s, groups in opt.get("lock", {}).items():
        for g in groups:
            tm = np.mean([keys[i]["t"] for i in g])
            A = np.mean([Ps[i]["an." + s][:2] - np.array([0, vel * (keys[i]["t"] - tm) / fps * LEG]) for i in g], 0)
            for i in g:
                tgt = Ps[i]["an." + s].copy(); tgt[:2] = A + np.array([0, vel * (keys[i]["t"] - tm) / fps * LEG])
                leg_ik(Ds[i], Ps[i], s, tgt); Ps[i] = fk(Ds[i], np.array([offs[i][0], offs[i][1], 0.0]))
    res = []
    for i, k in enumerate(keys):
        D, P = Ds[i], Ps[i]; ex = {"off": [round(float(offs[i][0]), 4), round(float(offs[i][1]), 4)], "katana": 0 if opt.get("blade") == "none" else 1}
        if k.get("air"):
            t0 = int(k["t"]); clr = min(min(c["an." + s][t0, 2], c["toe." + s][t0, 2]) - c["_floor"][s] for s in "RL")
            g = max(0.0, clr * s_) * opt.get("air_gain", 1.0); ex["absz"] = 1; ex["lift"] = round(float(g - low(P) + opt.get("lift_add", 0.0)), 4)
        ex.update(k.get("extra", {}))
        res.append(to_pose(D, ex))
    return res, Ps

def base_pose(c, frames):
    """mean joint offsets relative to the pelvis over frames (for amp_base)"""
    keys = [k for k in c if not k.startswith(("_", "G_"))]
    return {"J": {k: np.mean([c[k][t] - c["pelvis"][t] for t in frames], 0) for k in keys}, "pz": float(np.mean([c["pelvis"][t][2] for t in frames]))}
