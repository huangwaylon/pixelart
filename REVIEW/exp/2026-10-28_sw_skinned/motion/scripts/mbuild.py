"""mbuild.py (M): bake an action -> motion/<action>.json (contract format), then preview it.
usage: python mbuild.py walk|run|idle|jump [--noprev]
"""
import sys, os, json, math, time
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mrig import Skel, EXP, UP, FWD
from mpose import Poser
import mbody, msim

MOT = os.path.join(EXP, "motion")


def char_acc(po, a):
    return np.array([np.dot(a, po.RIGHT), np.dot(a, FWD), np.dot(a, UP)])


ACTIONS = {
    # name: (generator factory, loop, sprite frame times (s, relative to the cycle/clip start), cycle T, preroll cycles, key names)
    "walk": dict(loop=True, n=8, keys=["contact L", "down L", "passing L", "up L", "contact R", "down R", "passing R", "up R"]),
    "run": dict(loop=True, n=8, keys=["contact L", "down L", "push-off L", "flight", "contact R", "down R", "push-off R", "flight"]),
    "idle": dict(loop=True, times=[0, .30, .60, .68, .80, .96, 1.20, 1.50, 1.80, 1.88, 2.00, 2.16],
                 keys=["weight L (hold)", "weight L blink-hold", "transfer", "transfer", "transfer", "settle R", "weight R look", "weight R blink-hold",
                       "transfer", "transfer", "transfer", "settle L"]),
    "jump": dict(loop=False, times=[0, .10, .18, .25, .30, .36, .44, .52, .64, .70, .74, .775, .85, .95, 1.03, 1.14],
                 keys=["stand", "anticipation", "crouch (hold)", "launch", "take-off stretch", "rise", "rise (slowing)", "apex (hang)", "fall",
                       "fall (reach)", "land contact (toes)", "land absorb", "squash (deepest)", "recover overshoot (toes)", "settle dip", "end"]),
    "dash": dict(loop=False, times=[0, .05, .09, .20, .24, .29, .37, .45, .53, .62, .74, .86, 1.0],
                 keys=["stand", "anticipation (lean back)", "anticipation (hold)", "burst SMEAR 1", "burst SMEAR 2", "glide", "glide",
                       "skid contact", "brake (hold)", "overshoot", "recover", "settle", "end"]),
    "hurt": dict(loop=False, times=[0, .045, .09, .22, .30, .42, .56, .72, .90],
                 keys=["stand", "HIT snap", "recoil (hold)", "recoil", "buckle", "stagger", "recover", "settle", "end"]),
}


SPRING = {  # per-action overrides of msim.GROUPS. Rule: natural freq < ~0.4 x sprite fps or the springs alias into jitter
    # avoid resonance with the step bob (walk 2.4 Hz, run 3.6 Hz): stiff parts above it, long hair below it
    "walk": {},
    "run": {"hair_front": dict(f=2.6, z=0.45, gain=0.5), "bow": dict(f=2.3, gain=0.35), "bun": dict(f=2.5, z=0.4), "hair_side": dict(gain=0.5), "hair_back": dict(gain=0.5), "sleeve": dict(gain=0.4), "skirt": dict(gain=1.6)},
    "idle": {"bow": dict(f=1.6, z=0.5, gain=1.4), "bun": dict(f=1.8, z=0.5), "hair_side": dict(f=1.5, z=0.55), "hair_back": dict(f=1.4, z=0.55),
             "hair_front": dict(f=2.0, z=0.5, gain=0.4), "skirt": dict(f=1.8, z=0.5, gain=1.5), "sleeve": dict(f=1.5, z=0.5)},
    "dash": {"hair_side": dict(f=1.8, z=0.4, cd=3.0), "hair_back": dict(f=1.6, z=0.45, cd=3.0), "bow": dict(f=2.4, z=0.3, cd=2.5, gain=1.0),
             "bun": dict(f=2.6, z=0.3), "skirt": dict(f=2.2, z=0.3, cd=3.0, gain=2.4), "sleeve": dict(f=1.8, z=0.35, cd=3.0, gain=0.8, mx=30), "hair_front": dict(cd=1.5)},
    "hurt": {"hair_side": dict(f=1.8, z=0.4), "hair_back": dict(f=1.7, z=0.4), "bow": dict(f=2.4, z=0.3, gain=1.0), "bun": dict(f=2.6, z=0.3),
             "skirt": dict(f=2.2, z=0.35), "sleeve": dict(f=1.8, z=0.35, mx=30), "hair_front": dict(cd=0.5, gain=0.5)},
    "jump": {"hair_side": dict(f=1.7, z=0.35, cd=5.0), "hair_back": dict(f=1.6, z=0.35, cd=5.0), "bow": dict(f=2.2, z=0.25, cd=4.0),
             "bun": dict(f=2.5, cd=2.0), "skirt": dict(f=2.2, cd=5.0), "sleeve": dict(f=1.8, mx=35, cd=5.0), "hair_front": dict(cd=3.0)},
}
BASE_GROUPS = {k: dict(v) for k, v in msim.GROUPS.items()}


# ---------------------------------------------------------------- round 3: frame counts / timing feels / expression track
# half-cycle phase lists for gaits (contact = 0). "snappy" puts the samples on the key poses so the display times become holds
# (phase-correct: a longer gap = the pose is held, then the motion jumps); "even" = uniform.
GAIT_SNAPPY = {
    "walk": {3: [0.0, 0.22, 0.55], 4: [0.0, 0.17, 0.45, 0.75], 5: [0.0, 0.14, 0.30, 0.50, 0.75], 6: [0.0, 0.12, 0.24, 0.42, 0.56, 0.78]},
    "run":  {3: [0.0, 0.22, 0.62], 4: [0.0, 0.214, 0.5, 0.714], 5: [0.0, 0.16, 0.36, 0.56, 0.76]},
}
IDLE_PH = {"holds": {8: [0, .12, .26, .34, .5, .62, .76, .84], 12: [0, .125, .25, .283, .333, .40, .5, .625, .75, .783, .833, .9],
                     16: [0, .08, .16, .23, .27, .31, .36, .42, .5, .58, .66, .73, .77, .81, .86, .92]}}


def gait_times(action, n, feel, T):
    h = n // 2
    ph = GAIT_SNAPPY[action].get(h) if feel == "snappy" else None
    if ph is None: ph = [k / h for k in range(h)]
    return [p * T / 2 for p in ph] + [(0.5 + p / 2) * T for p in ph]


def gait_key(action, p):
    """pose name for a cycle phase p (L contact at 0)"""
    side = "L" if p < 0.5 else "R"; h = (2 * p) % 1.0
    names = {"walk": [(0.0, "contact"), (0.1, "down"), (0.36, "passing"), (0.62, "up")],
             "run": [(0.0, "contact"), (0.1, "down"), (0.38, "push-off"), (0.6, "flight")]}[action]
    nm = [n for x, n in names if h >= x - 1e-6][-1]
    return f"{nm} {side}" if nm != "flight" else "flight"


def expression(action, key, k, n):
    """per-frame expression track for F (face artist): face name, blink (0 open, 0.5 half, 1 closed), mouth"""
    if action == "walk":
        return {"face": "smile", "blink": 0.0, "mouth": "closed"}
    if action == "run":
        eff = key.startswith("down") or key.startswith("push-off")
        return {"face": "effort" if eff else "determined", "blink": 0.0, "mouth": "open" if eff else "closed"}
    if action == "idle":
        f = {"face": "neutral", "blink": 0.0, "mouth": "closed"}
        if "blink" in key: f["blink"] = 1.0
        if key.startswith("weight R"): f["face"] = "smile"   # look-at-camera smile spans the 2 R-hold frames (>= 2 frames)
        return f
    if action == "dash":
        D = [("stand", "neutral", "closed"), ("anticipation", "focused", "closed"), ("burst", "effort", "closed"), ("glide", "focused", "closed"),
             ("skid", "determined", "open"), ("brake", "determined", "open"), ("overshoot", "determined", "closed"), ("recover", "smile", "closed"),
             ("settle", "smile", "closed"), ("end", "smile", "closed")]
        for kk, fc, mo in D:
            if key.startswith(kk): return {"face": fc, "blink": 0.0, "mouth": mo}
    if action == "hurt":
        H = [("stand", "neutral", "closed", 0.0), ("HIT", "pained", "open", 1.0), ("recoil", "pained", "open", 1.0), ("buckle", "wince", "closed", 0.5),
             ("stagger", "wince", "closed", 0.5), ("recover", "determined", "closed", 0.0), ("settle", "neutral", "closed", 0.0), ("end", "neutral", "closed", 0.0)]
        for kk, fc, mo, bl in H:
            if key.startswith(kk): return {"face": fc, "blink": bl, "mouth": mo}
    # jump beats
    J = {"stand": ("neutral", "closed"), "anticipation": ("determined", "closed"), "crouch": ("determined", "closed"),
         "launch": ("effort", "open"), "take-off": ("effort", "open"), "rise": ("joyful", "open"), "apex": ("joyful", "open"),
         "fall": ("surprised", "open"), "land": ("squint", "closed"), "squash": ("squint", "closed"), "recover": ("smile", "open"),
         "settle": ("smile", "closed"), "end": ("smile", "closed")}
    for kk, (fc, mo) in J.items():
        if key.startswith(kk): return {"face": fc, "blink": 0.5 if fc == "squint" else 0.0, "mouth": mo}
    return {"face": "neutral", "blink": 0.0, "mouth": "closed"}


IDLE_KEYS = [(0.0, "weight L (hold)"), (0.10, "weight L blink-hold"), (0.22, "transfer"), (0.38, "settle R"), (0.47, "weight R look"),
             (0.60, "weight R blink-hold"), (0.72, "transfer"), (0.88, "settle L")]


def jump_warp(antic=1.0, hang=1.0):
    """real-time duration factors for the crouch hold [.14,.22] and the apex [.44,.60] of the jump timeline -> (tau(real), real(tau), length)"""
    seg = [(0.0, 0.14, 1.0), (0.14, 0.22, antic), (0.22, 0.44, 1.0), (0.44, 0.60, hang), (0.60, 1.40, 1.0)]
    R0 = [0.0]
    for a, b, f in seg: R0.append(R0[-1] + (b - a) * f)
    def real(tau):
        for (a, b, f), r0 in zip(seg, R0):
            if tau <= b: return r0 + (min(max(tau, a), b) - a) * f
        return R0[-1]
    def tau(rt):
        for (a, b, f), r0, r1 in zip(seg, R0, R0[1:]):
            if rt <= r1: return a + (rt - r0) / f
        return 1.40
    return tau, real, R0[-1]


def min_runs(frames, loop, keys=("face", "mouth"), n=2):
    """ROUND 4 (F): an expression change must last >= n frames. A shorter run takes the value of its longer neighbour
    (the previous one if tied); blinks stay free (a blink is a 1-frame event by design)."""
    N = len(frames)
    for key in keys:
        for _ in range(N):
            vals = [f[key] for f in frames]; changed = False
            runs = []; i = 0
            while i < N:
                j = i
                while j + 1 < N and vals[j + 1] == vals[i]: j += 1
                runs.append((i, j)); i = j + 1
            if loop and len(runs) > 1 and vals[0] == vals[-1]:   # wrap-around run
                (a0, b0), (a1, b1) = runs[0], runs[-1]; runs = [(a1, b0 + N)] + runs[1:-1]
            for r, (a_, b_) in enumerate(runs):
                if b_ - a_ + 1 >= n or len(runs) == 1: continue
                prev = runs[r - 1] if r > 0 else (runs[-1] if loop else None); nxt = runs[(r + 1) % len(runs)] if (r + 1 < len(runs) or loop) else None
                cand = [c for c in (prev, nxt) if c is not None]
                best = max(cand, key=lambda c: c[1] - c[0]); v = vals[best[0] % N]
                for k in range(a_, b_ + 1): frames[k % N][key] = v
                changed = True; break
            if not changed: break


def build(action, tune=None, var=None):
    """var (round 3): dict(name, n, feel, T, antic, hang, head_hold) -> motion/variants/<name>.json"""
    var = var or {}
    msim.GROUPS.clear(); msim.GROUPS.update({k: dict(v) for k, v in BASE_GROUPS.items()})
    for g, o in SPRING.get(action, {}).items(): msim.GROUPS[g].update(o)
    sk = Skel(); po = Poser(sk)
    A = dict(ACTIONS[action]); pre = 6; warp = None
    if action in ("walk", "run"):
        P = dict(getattr(mbody, action.upper())); P.update(tune or {})
        if var.get("T"): P["T"] = var["T"]
        gen = mbody.Gait(P, po)
        if P.get("geo"): gen.build_geo()
        else: mbody.auto_base(gen)
        T = P["T"]
        n = var.get("n", A["n"]); feel = var.get("feel", "snappy" if P.get("frame_ms") else "even")
        times = gait_times(action, n, feel, T)
        times = [t + P.get("frame_off", 0.0) * T / n for t in times]
        keys = [gait_key(action, (t / T) % 1.0) for t in times]
    elif action == "idle":
        T = var.get("T", 2.4); gen = mbody.Idle(po, T=T); n = var.get("n", 12); feel = var.get("feel", "holds")
        xs = IDLE_PH["holds"][n] if feel == "holds" else [k / n for k in range(n)]
        times = [x * T for x in xs]; pre = 2
        keys = [[nm for x0, nm in IDLE_KEYS if x >= x0 - 1e-6][-1] for x in xs]
    elif action in ("dash", "hurt"):
        gen = mbody.Dash(po) if action == "dash" else mbody.Hurt(po); T = A["times"][-1] + 0.2; pre = 0
        times = list(A["times"]); keys = A["keys"]
    else:
        tau, real, L = jump_warp(var.get("antic", 1.0), var.get("hang", 1.0))
        gen0 = mbody.Jump(po)
        class _G:   # time-warped jump: springs see real time
            def spec(self, t): return gen0.spec(tau(t))
        gen = _G(); T = L; pre = 0
        times = [real(t) for t in A["times"]]; keys = A["keys"]; warp = (tau, real)
    A["keys"] = keys
    dt = 1.0 / 400
    # time grid: preroll cycles then the output cycle; one-shots get a 1.2 s still preroll
    if A["loop"]:
        t0 = pre * T; t_end = t0 + T
        tt = np.arange(0, t_end + 1e-9, dt)
        tclip = lambda t: t
    else:
        t0 = 1.2; t_end = t0 + T; tt = np.arange(0, t_end + 1e-9, dt)
        tclip = lambda t: max(0.0, t - t0)
    specs = [gen.spec(tclip(t)) for t in tt]
    if var.get("lean_yaw"):
        lg = var.get("lean_gain", 1.0)
        for sp in specs:
            sp["lean_yaw"] = var["lean_yaw"]
            if lg != 1.0:   # 3/4-view cheat: a bit more lean so it survives foreshortening
                for part in ("pelvis", "chest"):
                    y_, p_, r_ = sp[part]; sp[part] = (y_, p_ * lg, r_)
    trv = np.array([sp.get("travel", 0.0) for sp in specs]); facc = np.gradient(trv, dt) if action in ("dash", "hurt") else np.zeros_like(trv)
    facc_k = {"dash": 1.0, "hurt": 0.5}.get(action, 0.0)
    # pass 1: neck-base path -> head lag spring
    neck = []
    for sp in specs:
        _, _, _, (D, H, T_) = po.solve(sp); neck.append(H["neck"].copy())
    neck = np.array(neck); acc = np.zeros_like(neck); acc[1:-1] = (neck[2:] - 2 * neck[1:-1] + neck[:-2]) / dt ** 2
    HL = {"walk": dict(k_up=30, k_fwd=40, k_side=250), "run": dict(k_up=55, k_fwd=30, k_side=120),
          "idle": dict(k_up=100, k_fwd=40, k_side=300), "jump": dict(k_up=25, k_fwd=10, k_side=20),
          "dash": dict(k_up=25, k_fwd=12, k_side=20), "hurt": dict(k_up=15, k_fwd=8, k_side=10)}
    hl = msim.HeadLag(**HL[action])
    for i, sp in enumerate(specs):
        th = hl.step(char_acc(po, acc[i] + FWD * facc[i] * facc_k), dt)
        y, p, r = sp["head"]; sp["head"] = (y, p + th[0], r + th[1])
        cy, cp, cr = sp["chest"]; sp["chest"] = (cy, cp + 0.25 * th[0], cr + 0.25 * th[1])
    # pass 2: body pose + secondary chains
    cs = msim.ChainSim(sk)
    samp = {int(round((t0 + ts) / dt)): k for k, ts in enumerate(times)}
    frames = [None] * len(times); ref = {}
    nT = int(round(T / dt)); i_ref = {i - nT: k for i, k in samp.items()} if A["loop"] else {}
    for i, (t, sp) in enumerate(zip(tt, specs)):
        r, root, sc, (D, H, T_) = po.solve(sp)
        cs.step(D, H, T_, dt, travel=sp.get("travel", 0.0) * (0.3 if action == "hurt" else 1.0), frame_acc=FWD * facc[i] * facc_k if facc_k else None)
        if i in samp or i in i_ref:
            rc, pts = cs.output(D, H, T_)
            if i in samp: frames[samp[i]] = (r, root, sc, rc, pts)
            else: ref[i_ref[i]] = pts
    print("saturation:", {g: round(a / max(1, b), 2) for g, (a, b) in msim.SAT.items()}); msim.SAT.clear()
    perr = None
    if ref:
        errs = {c: max(float(np.abs(ref[k][c] - frames[k][4][c]).max()) for k in ref) for c in ref[0]}; perr = max(errs.values())
        print("seam per chain (mm):", {c: round(e * 1000, 1) for c, e in errs.items() if e > 0.002})
        print(f"loop seam: max chain point change vs previous cycle = {perr * 1000:.1f} mm")
    # write
    out = dict(action=action, fps=24, loop=A["loop"], frames=[], timing_ms=[], notes="")
    hold = var.get("head_hold", action == "idle")
    for k, (r, root, sc, rc, pts) in enumerate(frames):
        bones = {}
        allr = dict(r); allr.update(rc)
        if hold and k % 2 == 1:   # head turn/tilt held >= 2 frames (P: avoids tex-head resample swaps); body and springs keep moving
            for hb in ("neck", "head"): allr[hb] = frames[k - 1][0][hb]
        for n in sk.order:
            if n == "root": continue
            bones[n] = {"rot": sk.local_quat(n, allr.get(n, np.eye(3)))}
        fr = {"t": round(times[k] * 24, 3), "key": A["keys"][k], "root": {"loc": [round(float(v), 5) for v in root]}, "bones": bones}
        fr.update(expression(action, A["keys"][k], k, len(frames)))
        if "SMEAR" in A["keys"][k]:   # ROUND 4: smear cue for P (stretched pose is in the bones; P paints the streaks)
            fr["smear"] = {"strength": 1.0 if A["keys"][k].endswith("1") else 0.6, "dir_world": [0.0, 1.0, 0.0], "parts": ["body", "arms", "legs", "hair", "skirt"]}
        if sc: fr["scale"] = {b: [round(float(x), 4) for x in v] for b, v in sc.items()}
        out["frames"].append(fr)
    min_runs(out["frames"], A["loop"])
    tl = list(times) + ([times[0] + T] if A["loop"] else [times[-1] + 0.25])
    out["timing_ms"] = [int(round((tl[k + 1] - tl[k]) * 1000)) for k in range(len(times))]
    if not A["loop"]: out["timing_ms"][-1] = 250
    if var.get("name"): out["action"] = var["name"]; out["variant"] = {k: v for k, v in var.items()}
    trav = specs[-1].get("travel", 0.0)
    out["travel_m_per_s"] = round(trav, 4)
    out["notes"] = (f"M {time.strftime('%Y-%m-%d %H:%M')}: skeleton={os.path.relpath(sk.path, EXP)}; cycle {T:.3f}s; in place (root.loc = bob/sway only). "
                    f"Game travel speed {trav:.3f} m/s = {trav * 67.88 * out["timing_ms"][0] / 1000:.2f} px/frame at 1x (67.88 px/m, R camera) for planted feet to hold still. "
                    "Secondary chains spring-baked (motion/scripts/msim.py). t = source frame at 24 fps (may be fractional).")
    if A["loop"]: out["cycle_s"] = T; out["seam_mm"] = round(perr * 1000, 2) if perr is not None else None
    if var.get("name"):
        os.makedirs(os.path.join(MOT, "variants"), exist_ok=True); path = os.path.join(MOT, "variants", f"{var['name']}.json")
    else:
        path = os.path.join(MOT, f"{action}.json")
    json.dump(out, open(path, "w"), indent=0)
    return path


if __name__ == "__main__":
    act = sys.argv[1]
    t = time.time(); p = build(act); print("wrote", p, f"{time.time() - t:.1f}s")
    if "--noprev" not in sys.argv:
        import mprev
        mprev.preview(p, "SE")
