# show.py SPEC OUT [rows] : cal.run S,SE,E (calib pose) -> 1x residuals (|r|>1 marked) + code grids beside the blockout
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import cal
os.environ.setdefault("FIG_PX", "48")
V = ["S", "SE", "E"]; POSE = json.loads(os.environ.get("POSE", '{"upper_arm.R": [0, -20, 0], "upper_arm.L": [0, 20, 0]}'))
m = cal.run(sys.argv[1], sys.argv[2], V, POSE); rp = cal.report(m, V)
nf = 0
for v in V:
    d = rp[""][v]; bad = [k for k, x in d.items() if k != "crown" and (x is None or abs(x) > 1)]; nf += len(bad)
    print(v, " ".join(f"{k}{'' if x is None else format(float(x), '+.0f')}{'!' if k in bad else ''}" for k, x in d.items()), "| 4x", " ".join(f"{k}{float(x):+.2f}" for k, x in rp["4"][v].items() if x is not None and k[0] == "w"))
print("FAILS", nf)
if len(sys.argv) > 3:
    a, b = map(int, sys.argv[3].split("-"))
    B = {v: open(cal.R + f"prop/blockout/{v}.txt").read().split("\n") for v in V}
    for i in range(a, b + 1): print("%2d" % i, "  ".join(m[v]["codes"][i][20:44] + "|" + B[v][i][20:44] for v in V))
