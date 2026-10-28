# tryv.py BASE.json WORKDIR 'name:key=val,key=val' ... : evaluate manual variants in parallel (keys: spec a.b, legs.profN, _env.X, _pose.X)
import sys, os, json, shutil
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import cal96
from search96 import put, get  # noqa
V = os.environ.get("VIEWS", "S,SE,E,NE,N").split(",")
def ev(args):
    name, st, wd = args; od = os.path.join(wd, "v_" + name)
    try: m = cal96.run(st, od, V)
    except (SystemExit, Exception): return name, None, None
    sc = {v: cal96.score(m, [v]) for v in V}
    if os.environ.get("KEEP") != "1": shutil.rmtree(od, ignore_errors=True)
    return name, sc, m
base = json.load(open(sys.argv[1])); wd = sys.argv[2]; os.makedirs(wd, exist_ok=True); jobs = []
for spec in sys.argv[3:]:
    name, _, kv = spec.partition(":"); st = base
    for item in [x for x in kv.split(",") if x]:
        k, _, val = item.partition("="); a, b = k.split(".", 1); st = put(st, a, b, float(val))
    json.dump(st, open(os.path.join(wd, name + ".json"), "w"), indent=1); jobs.append((name, st, wd))
for name, sc, m in ThreadPoolExecutor(9).map(ev, jobs):
    if sc is None: print(name, "FAIL"); continue
    tot = sum(sc[v][0] * (1 if v in ("S", "SE", "E") else 0.3) for v in V); fl = sum(sc[v][1] for v in V if v in ("S", "SE", "E"))
    print(f"{name}: score {tot:.1f} fails(S/SE/E) {fl} | " + " | ".join(f"{v}:{sc[v][1]} " + " ".join(b.split('.', 1)[1] for b in sc[v][2]) for v in V))
