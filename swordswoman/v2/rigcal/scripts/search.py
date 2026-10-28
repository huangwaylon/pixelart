# search.py SPEC.json WORKDIR [ROUNDS]  (hunyuan venv)  greedy pattern search on the 1x verify-method sections (S, SE, E)
# score = 10 * fails(|r|>1 px or missing) + sum(excess over 1 px) + 0.05 * 4x cost; params: spec multipliers + calib env (FIG_PX, arm abduction)
import sys, os, json, copy, shutil
import numpy as np
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import cal
V = ["S", "SE", "E"]
P = [("head", "scale", .02), ("head", "wx", .03), ("head", "fringe", .03), ("eyes", "dy", .02), ("neck", "extra", .02), ("neck", "r", .008),
     ("torso", "height", .04), ("torso", "width", .04), ("torso", "depth", .05), ("torso", "waist", .05), ("torso", "sh", .05), ("torso", "sq", .1),
     ("arms", "dy", .02), ("arms", "shoulder_x", .03), ("arms", "thickness", .05),
     ("skirt", "width", .04), ("skirt", "depth", .05), ("skirt", "height", .04), ("skirt", "flare", .04),
     ("legs", "thigh", .02), ("legs", "shin", .02), ("legs", "spread", .05), ("legs", "prof0", .015), ("legs", "prof1", .015), ("legs", "prof2", .015), ("legs", "prof3", .015),
     ("boots", "top", .02), ("boots", "sx", .05), ("boots", "sz", .05), ("boots", "ankle", .03), ("boots", "toe", .1), ("boots", "dz", .02), ("_env", "FIG_PX", .25), ("_pose", "abd", 1.5), ("_pose", "cheat", 4)]
FIX = set(os.environ.get("FIX", "").split(","))
P = [p for p in P if f"{p[0]}.{p[1]}" not in FIX]
def get(st, a, b):
    if a == "legs" and b.startswith("prof"): return st["spec"]["legs"]["prof"][int(b[4])]
    if a == "_env": return float(st["env"][b])
    if a == "_pose": return float(st["pose"][b])
    return float(st["spec"].get(a, {}).get(b, 0.0 if b in ("dy", "extra", "fringe", "sq", "r") else 1.0))
def put(st, a, b, x):
    st = copy.deepcopy(st); x = round(float(x), 4)
    if a == "legs" and b.startswith("prof"): st["spec"]["legs"]["prof"][int(b[4])] = x
    elif a == "_env": st["env"][b] = str(x)
    elif a == "_pose": st["pose"][b] = x
    else: st["spec"].setdefault(a, {})[b] = x
    return st
def evaluate(st, wd, tag):
    sj = os.path.join(wd, f"s_{tag}.json"); json.dump(st["spec"], open(sj, "w")); od = os.path.join(wd, "e_" + tag)
    ab = st["pose"]["abd"]; pose = {"upper_arm.R": [0, -ab, 0], "upper_arm.L": [0, ab, 0]}
    env = dict(st["env"], POSEV=json.dumps({"SE": {"cheat": -st["pose"]["cheat"]}}))
    try: m = cal.run(sj, od, V, pose, xenv=env)
    except SystemExit: return 1e9, {}
    finally: shutil.rmtree(od, ignore_errors=True); os.path.exists(sj) and os.remove(sj)
    rp = cal.report(m, V); fails = 0; exc = 0.0; c4 = 0.0; bad = []
    for v in V:
        for k, x in rp[""][v].items():
            if k in ("crown", "sole"): continue
            if x is None: fails += 1; exc += 3; bad.append(f"{v}.{k}?"); continue
            if abs(x) > 1: fails += 1; exc += abs(x) - 1; bad.append(f"{v}.{k}{x:+.0f}")
        for k, x in rp["4"][v].items():
            if k in ("crown", "sole"): continue
            if k == "hip": x = m[v]["rows4"].get("_hipx", 0)
            c4 += 9 if x is None else min(abs(x), 4) ** 2
    return 10 * fails + exc + 0.05 * c4, {"fails": fails, "bad": bad, "r1": rp[""]}
def main():
    st = json.load(open(sys.argv[1])); wd = sys.argv[2]; R = int(sys.argv[3]) if len(sys.argv) > 3 else 10; os.makedirs(wd, exist_ok=True)
    pool = ThreadPoolExecutor(int(os.environ.get("NPAR", "9"))); best, info = evaluate(st, wd, "x0"); print("x0", round(best, 2), info["bad"], flush=True)
    scale = 1.0
    for r in range(R):
        cands = []
        for a, b, s in P:
            x = get(st, a, b)
            for sg in (-1, 1): cands.append((f"{a}.{b}{'+' if sg > 0 else '-'}", put(st, a, b, x + sg * s * scale)))
        res = list(pool.map(lambda t: evaluate(t[1][1], wd, f"c{t[0]}"), enumerate(cands)))
        order = sorted(range(len(cands)), key=lambda i: res[i][0])
        imp = [i for i in order if res[i][0] < best - 1e-6]
        if not imp:
            scale *= 0.5; print("round", r, "no improvement, scale", scale, flush=True)
            if scale < 0.2: break
            continue
        # try combining the top improving moves on distinct params
        used, comb = set(), st
        for i in imp[:4]:
            k = cands[i][0][:-1]
            if k in used: continue
            used.add(k); a, b = k.split(".", 1); comb = put(comb, a, b, get(cands[i][1], a, b))
        sc, inf = evaluate(comb, wd, "comb")
        if sc < res[imp[0]][0]: st, best, info, how = comb, sc, inf, "comb" + str(sorted(used))
        else: st, best, info, how = cands[imp[0]][1], res[imp[0]][0], res[imp[0]][1], cands[imp[0]][0]
        json.dump(st, open(os.path.join(wd, "best.json"), "w"), indent=1)
        print("round", r, round(best, 2), "fails", info["fails"], how, info["bad"], flush=True)
        if info["fails"] == 0 and best < 1: break
main()
