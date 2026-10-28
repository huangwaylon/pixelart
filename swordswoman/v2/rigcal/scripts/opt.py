# opt.py BASE_SPEC.json WORKDIR [ITERS]  (hunyuan venv python)
# RIGCAL solver: damped Gauss-Newton (finite-difference Jacobian, parallel Blender renders via cal.py) on the 4x sub-pixel
# section residuals vs prop/blockout for S, SE and E. Writes WORKDIR/best.json (spec) + WORKDIR/log.jsonl.
import sys, os, json, copy, shutil
import numpy as np
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cal
VIEWS = ["S", "SE", "E"]
TR = float(os.environ.get("TR", "1.5"))
POSE = json.loads(os.environ.get("POSE", '{"upper_arm.R": [0, -20, 0], "upper_arm.L": [0, 20, 0]}'))
PAR = [("head", "scale", 0.05), ("head", "wx", 0.06), ("eyes", "dy", 0.05), ("neck", "extra", 0.04), ("neck", "r", 0.015),
       ("torso", "height", 0.08), ("torso", "width", 0.08), ("torso", "depth", 0.1), ("torso", "waist", 0.12),
       ("arms", "dy", 0.04), ("arms", "shoulder_x", 0.08), ("arms", "thickness", 0.1),
       ("skirt", "width", 0.08), ("skirt", "depth", 0.1), ("skirt", "height", 0.1),
       ("legs", "thigh", 0.05), ("legs", "shin", 0.05), ("legs", "thigh_w", 0.12), ("legs", "shin_w", 0.12), ("legs", "spread", 0.15),
       ("boots", "top", 0.04), ("boots", "sx", 0.12), ("boots", "sz", 0.12)]
FIX = [p.split(".") for p in os.environ.get("FIX", "").split(",") if p]
PAR = [p for p in PAR if [p[0], p[1]] not in FIX]
DEF = {("eyes", "dy"): 0.0, ("neck", "extra"): 0.0, ("neck", "r"): 0.0, ("arms", "dy"): 0.0, ("boots", "top"): 0.3}
LO = {("neck", "r"): 0.02, ("boots", "top"): 0.12, ("eyes", "dy"): -0.08}
HI = {("eyes", "dy"): 0.08}
def getp(sp): return np.array([float(sp.get(a, {}).get(b, DEF.get((a, b), 1.0))) for a, b, _ in PAR])
def setp(sp, x):
    sp = copy.deepcopy(sp)
    for (a, b, _), v in zip(PAR, x): sp.setdefault(a, {})[b] = round(float(min(max(v, LO.get((a, b), -9)), HI.get((a, b), 9))), 4)
    return sp
KEYS = None
def resvec(meas, k="4"):
    global KEYS
    out, keys = [], []
    for v in VIEWS:
        mm = {v: {"rows": meas[v]["rows" + k], "widths": meas[v]["widths" + k]}}; d = cal.residuals(mm, [v])[v]
        if k == "4": d["hip"] = meas[v]["rows4"].get("_hipx", 0.0)  # smooth proxy (0 when the widest body row is at/below the template hip row)
        for s, x in d.items():
            if s in ("crown", "sole"): continue
            keys.append(v + "." + s); out.append(np.nan if x is None else float(x))
    KEYS = keys; return np.array(out)
def cost(r, r1=None):
    rr = np.where(np.isnan(r), 3.0, r); c = float(np.sum(np.minimum(np.abs(rr), 4) ** 2))
    if r1 is not None: c += 2.0 * float(np.sum(np.isnan(r1) | (np.abs(np.nan_to_num(r1)) > 1)))
    return c
def evaluate(sp, wd, tag):
    sj = os.path.join(wd, f"spec_{tag}.json"); json.dump(sp, open(sj, "w"), indent=1); od = os.path.join(wd, "e_" + tag)
    try: m = cal.run(sj, od, VIEWS, POSE)
    except SystemExit as e: print("eval fail", tag, e); return None, None
    r4, r1 = resvec(m, "4"), resvec(m, ""); shutil.rmtree(od, ignore_errors=True); os.remove(sj); return r4, r1
def main():
    base = json.load(open(sys.argv[1])); wd = sys.argv[2]; its = int(sys.argv[3]) if len(sys.argv) > 3 else 6; os.makedirs(wd, exist_ok=True)
    x = getp(base); steps = np.array([s for *_, s in PAR]); log = open(os.path.join(wd, "log.jsonl"), "a")
    pool = ThreadPoolExecutor(int(os.environ.get("NPAR", "8")))
    r4, r1 = evaluate(setp(base, x), wd, "x0"); best = (cost(r4, r1), x.copy(), r4, r1)
    print("x0 cost", round(best[0], 2), "1x>1:", [k for k, v in zip(KEYS, r1) if np.isnan(v) or abs(v) > 1], flush=True)
    for it in range(its):
        x, r = best[1], best[2]
        futs = [pool.submit(evaluate, setp(base, x + np.eye(len(x))[i] * steps[i]), wd, f"j{i}") for i in range(len(x))]
        J = np.zeros((len(r), len(x)))
        for i, f in enumerate(futs):
            ri, _ = f.result()
            if ri is None: continue
            col = (ri - r) / steps[i]; col[np.isnan(col)] = 0; J[:, i] = col
        rr = np.where(np.isnan(r), 0, np.clip(r, -4, 4)); JS = J * steps  # scaled problem (unit = one step)
        cands = []
        for lam in (0.01, 0.1, 1.0, 10.0):
            A = JS.T @ JS + lam * np.diag(np.diag(JS.T @ JS) + 1e-3); d = -np.linalg.solve(A, JS.T @ rr); d = np.clip(d, -TR, TR); cands.append(x + d * steps)
        res = list(pool.map(lambda t: evaluate(setp(base, t[1]), wd, f"c{t[0]}"), enumerate(cands)))
        for c, (ra, rb) in zip(cands, res):
            if ra is None: continue
            co = cost(ra, rb)
            if co < best[0]: best = (co, c.copy(), ra, rb)
        bad = [f"{k}{v:+.0f}" if not np.isnan(v) else k + "?" for k, v in zip(KEYS, best[3]) if np.isnan(v) or abs(v) > 1]
        print("it", it, "cost", round(best[0], 2), "1x fails", len(bad), bad, flush=True)
        sp = setp(base, best[1]); json.dump(sp, open(os.path.join(wd, "best.json"), "w"), indent=1)
        log.write(json.dumps({"it": it, "cost": best[0], "x": dict(zip([a + "." + b for a, b, _ in PAR], best[1].round(4).tolist())), "r4": dict(zip(KEYS, np.round(best[2], 2).tolist())), "r1": dict(zip(KEYS, best[3].tolist()))}) + "\n"); log.flush()
        if not bad and best[0] < 2: break
main()
