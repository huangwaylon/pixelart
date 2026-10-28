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
}


SPRING = {  # per-action overrides of msim.GROUPS. Rule: natural freq < ~0.4 x sprite fps or the springs alias into jitter
    # avoid resonance with the step bob (walk 2.4 Hz, run 3.6 Hz): stiff parts above it, long hair below it
    "walk": {},
    "run": {"hair_front": dict(f=2.6, z=0.45, gain=0.5), "bow": dict(f=2.3, gain=0.35), "bun": dict(f=2.5, z=0.4), "hair_side": dict(gain=0.5), "hair_back": dict(gain=0.5), "sleeve": dict(gain=0.4), "skirt": dict(gain=1.6)},
    "idle": {"bow": dict(f=1.6, z=0.5, gain=1.4), "bun": dict(f=1.8, z=0.5), "hair_side": dict(f=1.5, z=0.55), "hair_back": dict(f=1.4, z=0.55),
             "hair_front": dict(f=2.0, z=0.5, gain=0.4), "skirt": dict(f=1.8, z=0.5, gain=1.5), "sleeve": dict(f=1.5, z=0.5)},
    "jump": {"hair_side": dict(f=1.7, z=0.35, cd=5.0), "hair_back": dict(f=1.6, z=0.35, cd=5.0), "bow": dict(f=2.2, z=0.25, cd=4.0),
             "bun": dict(f=2.5, cd=2.0), "skirt": dict(f=2.2, cd=5.0), "sleeve": dict(f=1.8, mx=35, cd=5.0), "hair_front": dict(cd=3.0)},
}
BASE_GROUPS = {k: dict(v) for k, v in msim.GROUPS.items()}


def build(action, tune=None):
    msim.GROUPS.clear(); msim.GROUPS.update({k: dict(v) for k, v in BASE_GROUPS.items()})
    for g, o in SPRING.get(action, {}).items(): msim.GROUPS[g].update(o)
    sk = Skel(); po = Poser(sk)
    A = ACTIONS[action]
    if action in ("walk", "run"):
        P = dict(getattr(mbody, action.upper())); P.update(tune or {})
        gen = mbody.Gait(P, po)
        if P.get("geo"): gen.build_geo()
        else: mbody.auto_base(gen)
        T = P["T"]
        times = [(k + P.get("frame_off", 0.0)) * T / A["n"] for k in range(A["n"])]
        if P.get("frame_ms"):   # uneven display times (holds on key poses), sampled phase-correctly
            ms = list(P["frame_ms"]) * 2; sc = T * 1000 / sum(ms); times = [0.0]
            for d in ms[:-1]: times.append(times[-1] + d * sc / 1000); pre = 6
    elif action == "idle":
        gen = mbody.Idle(po); T = gen.T; times = A["times"]; pre = 2
    else:
        gen = mbody.Jump(po); T = 1.40; times = A["times"]; pre = 0
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
    # pass 1: neck-base path -> head lag spring
    neck = []
    for sp in specs:
        _, _, _, (D, H, T_) = po.solve(sp); neck.append(H["neck"].copy())
    neck = np.array(neck); acc = np.zeros_like(neck); acc[1:-1] = (neck[2:] - 2 * neck[1:-1] + neck[:-2]) / dt ** 2
    HL = {"walk": dict(k_up=30, k_fwd=40, k_side=250), "run": dict(k_up=55, k_fwd=30, k_side=120),
          "idle": dict(k_up=100, k_fwd=40, k_side=300), "jump": dict(k_up=25, k_fwd=10, k_side=20)}
    hl = msim.HeadLag(**HL[action])
    for i, sp in enumerate(specs):
        th = hl.step(char_acc(po, acc[i]), dt)
        y, p, r = sp["head"]; sp["head"] = (y, p + th[0], r + th[1])
        cy, cp, cr = sp["chest"]; sp["chest"] = (cy, cp + 0.25 * th[0], cr + 0.25 * th[1])
    # pass 2: body pose + secondary chains
    cs = msim.ChainSim(sk)
    samp = {int(round((t0 + ts) / dt)): k for k, ts in enumerate(times)}
    frames = [None] * len(times); ref = {}
    nT = int(round(T / dt)); i_ref = {i - nT: k for i, k in samp.items()} if A["loop"] else {}
    for i, (t, sp) in enumerate(zip(tt, specs)):
        r, root, sc, (D, H, T_) = po.solve(sp)
        cs.step(D, H, T_, dt, travel=sp.get("travel", 0.0))
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
    for k, (r, root, sc, rc, pts) in enumerate(frames):
        bones = {}
        allr = dict(r); allr.update(rc)
        for n in sk.order:
            if n == "root": continue
            bones[n] = {"rot": sk.local_quat(n, allr.get(n, np.eye(3)))}
        fr = {"t": round(times[k] * 24, 3), "key": A["keys"][k], "root": {"loc": [round(float(v), 5) for v in root]}, "bones": bones}
        if sc: fr["scale"] = {b: [round(float(x), 4) for x in v] for b, v in sc.items()}
        out["frames"].append(fr)
    tl = list(times) + ([times[0] + T] if A["loop"] else [times[-1] + 0.25])
    out["timing_ms"] = [int(round((tl[k + 1] - tl[k]) * 1000)) for k in range(len(times))]
    if not A["loop"]: out["timing_ms"][-1] = 250
    trav = specs[-1].get("travel", 0.0)
    out["travel_m_per_s"] = round(trav, 4)
    out["notes"] = (f"M {time.strftime('%Y-%m-%d %H:%M')}: skeleton={os.path.relpath(sk.path, EXP)}; cycle {T:.3f}s; in place (root.loc = bob/sway only). "
                    f"Game travel speed {trav:.3f} m/s = {trav * 67.88 * out["timing_ms"][0] / 1000:.2f} px/frame at 1x (67.88 px/m, R camera) for planted feet to hold still. "
                    "Secondary chains spring-baked (motion/scripts/msim.py). t = source frame at 24 fps (may be fractional).")
    if A["loop"]: out["cycle_s"] = T; out["seam_mm"] = round(perr * 1000, 2) if perr is not None else None
    path = os.path.join(MOT, f"{action}.json")
    json.dump(out, open(path, "w"), indent=0)
    return path


if __name__ == "__main__":
    act = sys.argv[1]
    t = time.time(); p = build(act); print("wrote", p, f"{time.time() - t:.1f}s")
    if "--noprev" not in sys.argv:
        import mprev
        mprev.preview(p, "SE")
