# blkcheck.py VIEW : render rig F rest (48 px game camera) -> code grid (prop/blockout codes) -> prop/tools/verify.check vs template + diff vs prop/blockout/<V>.txt
import sys, os, json, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, "/Users/waylonhuang/Documents/other/pixelart/swordswoman/v2/prop/tools")
import pt, metrics as MX
import verify as VF, builtins
VF.max = lambda it, *a, **k: builtins.max(it, *a, **k) if a else builtins.max(list(it) or [0], **k)  # empty neck rows -> 0 px
v = sys.argv[1] if len(sys.argv) > 1 else "SE"; out = os.path.join(pt.ROOT, "tmp", "blk"); os.makedirs(out, exist_ok=True)
pose = json.loads(os.environ.get("POSE", "{}")); pose["katana"] = 0
pt.run([{"id": "rest", "view": v, "pose": pose}], out)
fr = json.load(open(os.path.join(out, "rest.json")))["frames"][0]; m, d = MX.metrics(os.path.join(out, "rest"), fr)
mat = d["matid"][..., :3]; al = d.get("vis", d["alpha"])
cols = {}
for y in range(64):
    for x in range(64):
        if al[y, x]: cols[tuple(mat[y, x])] = cols.get(tuple(mat[y, x]), 0) + 1
print("colours", sorted(cols.items(), key=lambda t: -t[1])[:14])
C = {(61, 50, 53): "hair", (248, 218, 194): "skin", (247, 217, 193): "skin", (192, 59, 61): "dress", (142, 34, 44): "sleeve", (232, 96, 79): "bow", (42, 34, 42): "boots", (69, 56, 73): "obi", (85, 128, 162): "eyes"}
part = d["part"]; G = np.full((64, 64), ".", dtype="<U1"); Bd = G.copy()
def code(p, c):
    if p in (4, 5): return {"sleeve": "A", "skin": "h", "dress": "A"}.get(c, "A")
    if p == 1: return {"hair": "H", "bow": "W", "skin": "F", "eyes": "e"}.get(c, "H")
    if p == 2: return {"skin": "N", "dress": "D", "obi": "O", "sleeve": "A"}.get(c, "D")
    if p == 3: return "D"
    if p in (6, 7): return {"skin": "L", "boots": "T"}.get(c, "L")
    return {"hair": "H", "skin": "L", "dress": "D"}.get(c, ".")
for y in range(64):
    for x in range(64):
        if al[y, x]:
            c = C.get(tuple(int(t) for t in mat[y, x]), "dress"); k = code(int(part[y, x]), c); G[y, x] = k
            Bd[y, x] = "." if k in "Ah" else k
open(os.path.join(out, f"F_{v}.txt"), "w").write("\n".join("".join(r) for r in G))
H, mm, w, rep, bad = VF.check(v, G, Bd); print(v, "H", H, "PASS" if not bad else "FAIL", " ".join(rep))
ref = np.array([list(l.rstrip("\n")) for l in open(f"/Users/waylonhuang/Documents/other/pixelart/swordswoman/v2/prop/blockout/{v}.txt")])
rb = np.array([list(l.rstrip("\n")) for l in open(f"/Users/waylonhuang/Documents/other/pixelart/swordswoman/v2/prop/blockout/{v}_body.txt")])
H2, m2, w2, rep2, _ = VF.check(v, ref, rb); print("blockout", v, "H", H2, " ".join(rep2))
print("diff F-blockout rows:", {k: (mm[k] - m2[k]) if (mm.get(k) is not None and m2.get(k) is not None) else None for k in m2}, "widths:", {k: w[k] - w2[k] for k in w2})
a1 = G != "."; a2 = ref != "."; print("sil IoU", round(float((a1 & a2).sum() / (a1 | a2).sum()), 3), "F px", int(a1.sum()), "blk px", int(a2.sum()))
