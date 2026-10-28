# search96.py STATE.json WORKDIR [ROUNDS] [VIEWS=S,SE,E] : greedy pattern search (as rigcal/scripts/search.py) on the 96 px master sections
# score = 10 * fails(|r|>1 px or missing) + sum(excess over 1 px) (+ W_CHECK * same for NE/N if VIEWS includes them)
import sys, os, json, copy, shutil
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import cal96
P = [("head", "scale", .03), ("head", "wx", .03), ("head", "wz", .04), ("head", "fringe", .03), ("eyes", "dy", .02), ("neck", "extra", .02), ("neck", "r", .008),
     ("torso", "height", .04), ("torso", "width", .04), ("torso", "depth", .05), ("torso", "waist", .05), ("torso", "sh", .05), ("torso", "sq", .1),
     ("arms", "dy", .02), ("arms", "shoulder_x", .03), ("arms", "thickness", .05), ("arms", "length", .04), ("arms", "flare", .15), ("arms", "flarez", .15), ("arms", "flare0", .05), ("hands", "scale", .05),
     ("skirt", "width", .04), ("skirt", "depth", .05), ("skirt", "height", .04), ("skirt", "flare", .04), ("skirt", "flarez", .05),
     ("legs", "thigh", .02), ("legs", "shin", .02), ("legs", "spread", .06), ("legs", "prof0", .015), ("legs", "prof1", .015), ("legs", "prof2", .015), ("legs", "prof3", .015), ("legs", "sock", .03),
     ("boots", "top", .02), ("boots", "sx", .05), ("boots", "sz", .05), ("boots", "ankle", .03), ("boots", "dz", .02), ("_env", "PPU", .25), ("_pose", "abd", 2), ("_pose", "cheat", 4)]
FIX = set(os.environ.get("FIX", "").split(",")); P = [p for p in P if f"{p[0]}.{p[1]}" not in FIX]
DEF0 = ("dy", "extra", "fringe", "sq", "r", "flare0")
def get(st, a, b):
    if a == "legs" and b.startswith("prof"): return st["spec"]["legs"]["prof"][int(b[4])]
    if a == "_env": return float(st["env"][b])
    if a == "_pose": return float(st["pose"].get(b, 0))
    if a == "head" and b == "wz": return float(st["spec"]["head"].get("wz", st["spec"]["head"].get("wx", 1.0)))
    if a == "skirt" and b == "flarez": return float(st["spec"]["skirt"].get("flarez", st["spec"]["skirt"].get("flare", 1.0)))
    if a == "arms" and b == "flare0": return float(st["spec"]["arms"].get("flare0", 0.35))
    if a == "arms" and b == "flarez": return float(st["spec"]["arms"].get("flarez", st["spec"]["arms"].get("flare", 1.0)))
    return float(st["spec"].get(a, {}).get(b, 0.0 if b in DEF0 else 1.0))
def put(st, a, b, x):
    st = copy.deepcopy(st); x = round(float(x), 4)
    if a == "legs" and b.startswith("prof"): st["spec"]["legs"]["prof"][int(b[4])] = x
    elif a == "_env": st["env"][b] = str(x)
    elif a == "_pose": st["pose"][b] = x
    else: st["spec"].setdefault(a, {})[b] = x
    return st
V = (sys.argv[4] if len(sys.argv) > 4 else "S,SE,E").split(","); MAIN = {"S", "SE", "E"}; WCHK = float(os.environ.get("W_CHECK", "0.3"))
def evaluate(st, wd, tag):
    od = os.path.join(wd, "e_" + tag)
    try: m = cal96.run(st, od, V)
    except (SystemExit, Exception): return 1e9, {"fails": 99, "bad": ["render"]}
    finally: shutil.rmtree(od, ignore_errors=True)
    tot, fl, bad = 0.0, 0, []
    for v in V:
        s, f, b = cal96.score(m, [v]); b = [x for x in b if not x.endswith((".H", ))]
        w = 1.0 if v in MAIN else WCHK; tot += w * s
        if v in MAIN: fl += f; bad += b
    return tot, {"fails": fl, "bad": bad}
def main():
    st = json.load(open(sys.argv[1])); wd = sys.argv[2]; RN = int(sys.argv[3]) if len(sys.argv) > 3 else 10; os.makedirs(wd, exist_ok=True)
    pool = ThreadPoolExecutor(int(os.environ.get("NPAR", "9"))); best, info = evaluate(st, wd, "x0"); print("x0", round(best, 2), info["fails"], flush=True)
    scale = float(os.environ.get("SCALE0", "1.0"))
    for r in range(RN):
        cands = []
        for a, b, s in P:
            x = get(st, a, b)
            for sg in (-1, 1): cands.append((f"{a}.{b}{'+' if sg > 0 else '-'}", put(st, a, b, x + sg * s * scale)))
        res = list(pool.map(lambda t: evaluate(t[1][1], wd, f"c{t[0]}"), enumerate(cands)))
        order = sorted(range(len(cands)), key=lambda i: res[i][0]); imp = [i for i in order if res[i][0] < best - 1e-6]
        if not imp:
            scale *= 0.5; print("round", r, "no improvement, scale", scale, flush=True)
            if scale < 0.2: break
            continue
        used, comb = set(), st
        for i in imp[:5]:
            k = cands[i][0][:-1]
            if k in used: continue
            used.add(k); a, b = k.split(".", 1); comb = put(comb, a, b, get(cands[i][1], a, b))
        sc, inf = evaluate(comb, wd, "comb")
        if sc < res[imp[0]][0]: st, best, info, how = comb, sc, inf, "comb" + str(sorted(used))
        else: st, best, info, how = cands[imp[0]][1], res[imp[0]][0], res[imp[0]][1], cands[imp[0]][0]
        json.dump(st, open(os.path.join(wd, "best.json"), "w"), indent=1)
        print("round", r, round(best, 2), "fails", info["fails"], how, " ".join(info["bad"]), flush=True)
        if info["fails"] == 0 and best < 1: break
if __name__ == "__main__":
    main()
