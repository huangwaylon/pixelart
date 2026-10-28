# autoblade.py VIEW [THRESH] : for every key with blade_vis < THRESH, try blade screen-angle offsets +-30 and report the best (max visible blade px, least change)
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pt, metrics as MX
view = sys.argv[1]; th = int(sys.argv[2]) if len(sys.argv) > 2 else 30
S = pt.src(); jobs = []; meta = {}
OFF = [-30, -20, -10, 0, 10, 20, 30]
for act, A in S.ACT.items():
    for i, f in enumerate(A["frames"]):
        p = pt.resolve(S, act, i, view)
        if "blade_scr" not in p: continue
        for d in OFF:
            jid = f"{act}__{i}__{d}"; q = dict(p); q["blade_scr"] = [p["blade_scr"][0] + d] + list(p["blade_scr"][1:])
            jobs.append({"id": jid, "view": view, "pose": q}); meta[jid] = (act, f["name"], d, p["blade_scr"][0])
out = os.path.join(pt.ROOT, "tmp", "ab_" + view); pt.run(jobs, out); res = {}
for j in jobs:
    fr = json.load(open(os.path.join(out, j["id"] + ".json")))["frames"][0]; m, _ = MX.metrics(os.path.join(out, j["id"]), fr)
    a, n, d, b0 = meta[j["id"]]; res.setdefault((a, n), {})[d] = (m["blade_vis"], m["blade_over_body"], b0)
import shutil; shutil.rmtree(out)
rep = {}
for (a, n), r in res.items():
    v0 = r[0][0]
    if v0 >= th: continue
    best = max(r, key=lambda d: (r[d][0] - r[d][1] - 0.15 * abs(d)))
    rep[f"{a}.{n}"] = {"vis0": v0, "best_d": best, "vis": r[best][0], "angle": r[best][2] + best, "all": {d: r[d][0] for d in OFF}}
    print(f"{a}.{n}: vis {v0} -> {r[best][0]} at d{best:+d} (angle {r[best][2] + best})  " + " ".join(f"{d:+d}:{r[d][0]}" for d in OFF))
json.dump(rep, open(os.path.join(pt.ROOT, "tmp", f"autoblade_{view}.json"), "w"), indent=0)
