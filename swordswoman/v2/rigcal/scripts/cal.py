# cal.py SPEC.json OUTDIR [VIEWS=S,SE,E,NE,N] [--keep]   (hunyuan venv python: trimesh + PIL)
# RIGCAL measurement loop: SPEC -> repro_g.py (partsAB4f + best/skel.txt) -> OUTDIR/parts -> render rest (pose {}, no katana)
# through the game cameras at 48 px (FIG_EXCL=bow,bun: 48 px = hair crown -> sole, soles row 61; HEADS_SE=1.0) ->
# prop/blockout code grids (1x as metrics.load1x, and 4x for sub-pixel measures) -> prop/tools/verify-style sections.
# Writes OUTDIR/meas.json {view: {rows, widths, rows4, widths4, codes}} and prints residuals vs prop/blockout.
import sys, os, json, subprocess, shutil
import numpy as np
from PIL import Image
R = "/Users/waylonhuang/Documents/other/pixelart/swordswoman/v2/"; HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, R + "throw/scripts"); sys.path.insert(0, R + "prop/tools")
import metrics as MX
import verify as VF
PY = sys.executable; BL = "/Applications/Blender.app/Contents/MacOS/Blender"
C = {(61, 50, 53): "hair", (61, 50, 52): "hair", (248, 218, 194): "skin", (247, 217, 193): "skin", (192, 59, 61): "dress", (142, 34, 44): "sleeve",
     (232, 96, 79): "bow", (42, 34, 42): "boots", (69, 56, 73): "obi", (85, 128, 162): "eyes"}
def code(p, c):
    if p == 10: return "W"
    if p in (4, 5): return {"skin": "h"}.get(c, "A")
    if p == 1: return {"hair": "H", "bow": "W", "skin": "F", "eyes": "e"}.get(c, "H")
    if p == 2: return {"skin": "N", "obi": "O", "sleeve": "A", "hair": "H"}.get(c, "D")
    if p == 3: return "D"
    if p in (6, 7): return {"boots": "T"}.get(c, "L")
    return "."
def grids(mat, part, al):
    G = np.full(al.shape, ".", dtype="<U1")
    ys, xs = np.nonzero(al)
    for y, x in zip(ys, xs): G[y, x] = code(int(part[y, x]), C.get(tuple(int(t) for t in mat[y, x, :3]), "dress"))
    B = G.copy(); B[np.isin(G, ["A", "h"])] = "."
    return G, B
def runs(row, codes):
    m = np.isin(row, list(codes)).astype(int); d = np.diff(np.concatenate([[0], m, [0]])); s = np.nonzero(d == 1)[0]; e = np.nonzero(d == -1)[0]
    return list(e - s)
def width(row, codes):
    xs = np.nonzero(np.isin(row, list(codes)))[0]; return int(xs.max() - xs.min() + 1) if len(xs) else 0
def measure(g, side, body, k=1, href=None):
    n = g.shape[0]; rw = lambda cs: list(np.nonzero(np.isin(g, list(cs)).any(1))[0])
    m, w = {}, {}
    m["crown"] = min(rw("H")); T_ = rw("T"); m["sole"] = max(T_) + 1; m["ankle"] = min(T_)
    e = rw("e"); m["eye"] = (min(e) + max(e) + 1) / 2 if e else None
    nn = [r for r in rw("N") if r < 40 * k]; F_ = [r for r in rw("F") if r < 40 * k]
    m["shoulder"] = min(rw("DA"))
    m["chin"] = min(nn) if nn else (max(F_) + 1 if F_ else m["shoulder"])
    D = rw("D"); m["hem"] = max(D) + 1; m["crotch"] = m["hem"]; m["armpit"] = None
    if not side:
        for r in range(m["shoulder"], m["hem"]):
            if len(runs(g[r], "DOAh")) >= 3: m["armpit"] = r; break
    hz = range(m["shoulder"] + 3 * k, m["hem"]); bw = {r: max(runs(body[r], "DO") or [0]) for r in hz}
    mx = max(bw.values()); m["hip"] = min(r for r in hz if bw[r] == mx); w["hip"] = mx
    if href is not None:  # RIGCAL smooth proxy for the (argmax) hip row: how much wider the body is above the template hip row than at it
        up = [bw[r] for r in hz if r < (href - 1) * k]; at = [bw[r] for r in hz if (href - 1) * k <= r < (href + 2) * k]
        m["_hipx"] = max(0.0, ((max(up) if up else 0) - (max(at) if at else 0)) / k + 0.5)
    wz = [r for r in hz if r < m["hip"]] or [m["hip"]]; mn = min(bw[r] for r in wz); wr = [r for r in wz if bw[r] == mn]
    m["waist"] = (min(wr) + max(wr) + 1) / 2; w["waist"] = mn
    w["head"] = max(width(g[r], "H") for r in range(m["crown"], m["chin"]))
    w["neck"] = max([max(runs(g[r], "N") or [0]) for r in range(m["chin"], m["shoulder"])] or [0])
    w["shoulder"] = max(width(g[r], "DAO") for r in range(m["shoulder"], m["shoulder"] + 2 * k))
    lg = lambda r: max(runs(body[r], "L") or [0])
    w["thigh"] = lg(m["hem"] + (k // 2)); thr = w["thigh"] - (0 if k == 1 else k / 2)
    kr = [r for r in range(m["hem"] + k, m["ankle"]) if lg(r) < thr]
    m["knee"] = min(kr) if kr else None; w["calf"] = lg(m["knee"] + 2 * k + k // 2) if kr else lg(m["ankle"] - 2 * k)
    w["foot"] = max(runs(g[m["sole"] - 1 - k // 2], "T") or [0])
    if k > 1:
        m = {a: (None if b is None else b / k) for a, b in m.items()}  # edge position in 1x px (~ the 1x row after coverage > 0.5 rounding)
        w = {a: b / k for a, b in w.items()}
    return m, w
VW = {"S": ("eye chin shoulder armpit waist hip hem knee ankle", "head neck shoulder waist hip thigh calf foot"),
      "SE": ("eye chin shoulder armpit waist hip hem knee ankle", "head neck shoulder waist hip thigh calf foot"),
      "E": ("eye chin shoulder waist hip hem knee ankle", "head neck calf"),
      "NE": ("chin shoulder armpit waist hip hem knee ankle", "head neck shoulder waist hip thigh calf foot"),
      "N": ("chin shoulder armpit waist hip hem knee ankle", "head neck shoulder waist hip thigh calf foot")}
def blk(v):
    g = np.array([list(l.rstrip("\n")) for l in open(R + f"prop/blockout/{v}.txt")]); b = np.array([list(l.rstrip("\n")) for l in open(R + f"prop/blockout/{v}_body.txt")])
    return measure(g, v == "E", b)
ALIGN = os.environ.get("ALIGN", "0") == "1"
def residuals(meas, views):
    res = {}
    for v in views:
        bm, bw = blk(v); mm, ww = meas[v]["rows"], meas[v]["widths"]; rr, ws = VW[v]; d = {}
        H = mm["sole"] - mm["crown"]
        d["H"] = H - (bm["sole"] - bm["crown"]); d["crown"] = mm["crown"] - bm["crown"]; d["sole"] = mm["sole"] - bm["sole"]
        sh = bm["sole"] - mm["sole"] if ALIGN else 0  # rows compared with each view's soles on the template sole line (row 61)
        for s in rr.split(): d[s] = None if mm.get(s) is None else round(mm[s] + sh - bm[s], 2)
        for s in ws.split(): d["w" + s] = round(ww[s] - bw[s], 2)
        res[v] = d
    return res
def run(spec, out, views, pose=None, keep=False, xenv=None):
    os.makedirs(out, exist_ok=True); pd = os.path.join(out, "parts")
    r = subprocess.run([PY, "-I", os.path.join(HERE, "repro_g.py"), spec, R + "hy3d/partsAB4f", R + "hy3d/best/skel.txt", pd], capture_output=True, text=True)
    if r.returncode: print(r.stderr[-1500:]); raise SystemExit("repro failed")
    rd = os.path.join(out, "r"); os.makedirs(rd, exist_ok=True); pose = dict(pose or {}); pose["katana"] = 0
    PV = json.loads((xenv or {}).get("POSEV", os.environ.get("POSEV", "{}")))  # per-view pose extras, e.g. {"SE": {"cheat": 20}}
    ARMS = ["uarm_", "farm_", "elbow_", "arm_"]
    json.dump({"jobs": [{"id": v, "view": v, "pose": {**pose, **PV.get(v, {})}} for v in views] + [{"id": v + "_body", "view": v, "pose": {**pose, **PV.get(v, {})}, "hide": ARMS} for v in views]}, open(os.path.join(rd, "jobs.json"), "w"))
    env = dict(os.environ, MOCAP="1", ELBOW=os.environ.get("ELBOW", "1"), RIG_LIB_PATH=R + "throw/scripts/rig_lib.py", FIG_EXCL="bow,bun", HIDE=os.environ.get("HIDE", "bow,bun"), HEADS_SE=os.environ.get("HEADS_SE", "1.0")); env.update(xenv or {})
    b = subprocess.run([BL, "-b", "--factory-startup", "-P", os.path.join(HERE, "render_cal.py"), "--", pd, pd + "/skel.txt", rd + "/jobs.json", rd], capture_output=True, text=True, env=env)
    if "ALLDONE" not in b.stdout: print(b.stdout[-1500:], b.stderr[-800:]); raise SystemExit("render failed")
    ppu = [l for l in b.stdout.splitlines() if l.startswith("calib")]
    meas = {"_calib": ppu[0] if ppu else None}
    for v in views:
        stem = os.path.join(rd, v); d = MX.load1x(stem); y0, x0 = MX.CROP
        al, mat, part = d["alpha"], d["matid"], d["part"]  # load1x returns the 64 crop
        G, _ = grids(mat, part, al); db = MX.load1x(stem + "_body"); B, _ = grids(db["matid"], db["part"], db["alpha"])  # body grid = arms-hidden render (as blockout *_body.txt)
        m1, w1 = measure(G, v == "E", B)
        a4 = np.asarray(Image.open(stem + "_matid.png").convert("RGBA")); p4 = np.asarray(Image.open(stem + "_part.png").convert("RGBA")); k = a4.shape[0] // 96
        sl = slice(y0 * k, (y0 + 64) * k), slice(x0 * k, (x0 + 64) * k); al4 = a4[sl][..., 3] > 127
        G4, _ = grids(a4[sl], np.where(p4[sl][..., 3] > 127, np.round(p4[sl][..., 0] / 25.0).astype(int), 0), al4)
        b4 = np.asarray(Image.open(stem + "_body_matid.png").convert("RGBA")); q4 = np.asarray(Image.open(stem + "_body_part.png").convert("RGBA"))
        B4, _ = grids(b4[sl], np.where(q4[sl][..., 3] > 127, np.round(q4[sl][..., 0] / 25.0).astype(int), 0), b4[sl][..., 3] > 127)
        m4, w4 = measure(G4, v == "E", B4, k, href=blk(v)[0]["hip"])
        meas[v] = {"rows": m1, "widths": w1, "rows4": m4, "widths4": w4, "codes": ["".join(r) for r in G]}
    json.dump(meas, open(os.path.join(out, "meas.json"), "w"), indent=0, default=float)
    if not keep: shutil.rmtree(rd)
    return meas
def report(meas, views, key=""):
    out = {}
    for kk in ("", "4"):
        mm = {v: {"rows": meas[v]["rows" + kk], "widths": meas[v]["widths" + kk]} for v in views}; out[kk] = residuals(mm, views)
    return out
if __name__ == "__main__":
    spec, out = sys.argv[1:3]; views = (sys.argv[3] if len(sys.argv) > 3 and not sys.argv[3].startswith("-") else "S,SE,E,NE,N").split(",")
    meas = run(spec, out, views, json.loads(os.environ.get("POSE", "{}")), "--keep" in sys.argv); rp = report(meas, views)
    print(meas["_calib"])
    for v in views:
        bad = {k: x for k, x in rp[""][v].items() if x is None or abs(x) > 1}
        print(v, "1x", {k: (None if x is None else float(x)) for k, x in rp[""][v].items()}); print("  4x", {k: (None if x is None else float(x)) for k, x in rp["4"][v].items()}); print("  >1px:", sorted(bad))
