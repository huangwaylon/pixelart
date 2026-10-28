# meas96.py: 96px section measures (same section set as v2/rigcal/scripts/cal.py, adapted to the pixel masters' palette)
# Common class grid (128x128, 96px figure, soles on the master sole line): '.' bg, K outline (masters only), H hair, B bow, F skin,
# e eye, D red (dress + sleeves), O obi, X sock, T boot.  Masters: v2/pixelize/top1/EC0_<V>_96.txt (palette v2/pixelize/palette.json).
# Rig: 4x render of the 96 cell at FIG_PX ~ 48 (render_cal.py) -> 2x2 majority -> 192 px = 2x of the 96 cell -> crop the 64 cell (x16..80, y16..80) = 128x128.
import os, json
import numpy as np
R = "/Users/waylonhuang/Documents/other/pixelart/swordswoman/v2/"
MAN = json.load(open(R + os.environ.get("G96_MANUAL", "g96/master_manual.json")))
MDIR = os.environ.get("G96_MASTERS", "m96/masters")  # rig H used pixelize/top1 + g96/master_manual_H.json
MC = {}
for c in "hHgL": MC[c] = "H"
for c in "sSmk": MC[c] = "F"
for c in "eER": MC[c] = "D"
for c in "QOo": MC[c] = "O"
for c in "Dd": MC[c] = "X"
MC["W"] = "e"; MC["K"] = "K"; MC["."] = "."
def master(v):
    g = np.array([list(l.rstrip("\n")) for l in open(R + f"{MDIR}/EC0_{v}_96.txt")])[:128, :128]
    G = np.vectorize(lambda c: MC.get(c, "."))(g)
    m = MAN[v]; ys, xs = np.nonzero(G == "D")
    for y, x in zip(ys, xs):
        if y < m["bowcut"]: G[y, x] = "B"
        elif y >= 93 and MDIR.startswith("m96"): G[y, x] = "X"  # polished masters: red sock cuff band -> sock
    xr = [x for x in range(128) if (G[:, x] != ".").any()]
    # boots: hair-coloured pixels below the sock top; eyes: hair-coloured / K pixels inside the face rows handled via manual eye row
    X_ = np.nonzero((G == "X").any(1))[0]; st = int(X_.min())
    st = [r for r in range(70, 124) if all((G[r + i] == "X").sum() >= 1 for i in range(4))][0]
    G[st:][G[st:] == "H"] = "T"
    return G, g
RC = {(61, 50, 53): "H", (61, 50, 52): "H", (248, 218, 194): "F", (247, 217, 193): "F", (192, 59, 61): "D", (142, 34, 44): "D",
      (232, 96, 79): "b", (42, 34, 42): "T", (69, 56, 73): "O", (85, 128, 162): "e"}
SOCK_RGB = None  # filled from the render (sock vertex colour (5,6,16) -> sRGB ~ (40,44,70))
def rigclass(rgb):
    t = tuple(int(x) for x in rgb[:3])
    if t == (250, 0, 250): return "N"
    if t in RC: return RC[t]
    best = min(list(RC) + [(40, 44, 70)], key=lambda c: sum((a - b) ** 2 for a, b in zip(c, t)))
    return "X" if best == (40, 44, 70) else RC[best]
def rig(path4x, sole_row=None):
    from PIL import Image
    pp = np.asarray(Image.open(path4x.replace("_matid.png", "_part.png")).convert("RGBA"))
    a = np.asarray(Image.open(path4x).convert("RGBA")).copy()
    neck = (pp[..., 3] > 127) & (np.round(pp[..., 0] / 25.0) == 2) & np.all(a[..., :3] == (248, 218, 194), -1)
    a[neck, :3] = (250, 0, 250); k4 = a.shape[0] // 96; f = k4 // 2  # 2x of the 96 cell
    H = a.shape[0] // f; b = a.reshape(H, f, H, f, 4).transpose(0, 2, 1, 3, 4).reshape(H, H, f * f, 4)
    G = np.full((H, H), ".", dtype="<U1"); cache = {}
    for y in range(H):
        for x in range(H):
            bl = b[y, x]; bl = bl[bl[:, 3] > 127]
            if len(bl) * 2 < f * f: continue
            cols, cnt = np.unique(bl[:, :3], axis=0, return_counts=True); c = tuple(int(t) for t in cols[cnt.argmax()])
            if c not in cache: cache[c] = rigclass(c)
            G[y, x] = cache[c]
    pr0 = np.where(pp[..., 3] > 127, np.round(pp[..., 0] / 25.0).astype(int), 0)
    kb = (pr0 == 10).reshape(H, f, H, f).sum((1, 3)) * 2 > f * f
    if os.environ.get("G96_BUNB") == "1": G[kb & (G != ".")] = "B"  # rig H rule (bun = knot excluded); H2: bun keeps its hair class like the polished masters' knot
    arm_ = np.isin(pr0, [2, 3, 4, 5]).reshape(H, f, H, f).sum((1, 3)) * 2 > f * f  # bow-coloured blends on the body/arms = red, else bow
    G[(G == "b") & arm_] = "D"; G[G == "b"] = "B"  # bow + bun (knot) group -> excluded from the crown
    ob = [y for y in range(H) if (G[y] == "O").sum() >= 3]
    if ob:  # colour-blend noise below the obi (skin/sock/boot edges): stray obi/eye ids -> sock
        y1 = max(ob) + 2; low = G[y1:]; low[np.isin(low, ["O", "e"])] = "X"
    G = G[32:160, 32:160]
    pr = np.where(pp[..., 3] > 127, np.round(pp[..., 0] / 25.0).astype(int), 0)
    pb = pr.reshape(H, f, H, f).transpose(0, 2, 1, 3).reshape(H, H, f * f)
    P = np.zeros((H, H), int)
    for g_ in range(1, 11):
        c_ = (pb == g_).sum(-1); P = np.where(c_ * 2 > f * f, g_, P)
    global LAST_PART; LAST_PART = P[32:160, 32:160]
    return G
LAST_PART = None
def runs(row, ok):
    m = ok(row).astype(int); d = np.diff(np.concatenate([[0], m, [0]])); s = np.nonzero(d == 1)[0]; e = np.nonzero(d == -1)[0]
    return list(zip(s, e))
def maxrun(row, cs):
    r = runs(row, lambda q: np.isin(q, list(cs))); return max([e - s for s, e in r] or [0])
def extent(row, cs):
    xs = np.nonzero(np.isin(row, list(cs)))[0]; return int(xs.max() - xs.min() + 1) if len(xs) else 0
SIL = "KHBFNeDOXT"
def dil(m, n):
    o = m.copy()
    for _ in range(n): o = o | np.roll(o, 1, 0) | np.roll(o, -1, 0) | np.roll(o, 1, 1) | np.roll(o, -1, 1)
    return o
def measure(G, v, man=None, knee_px=None, part=None):
    """rows (edge positions in px, 0 = top of the 128 cell) + widths (px). man = manual eye/chin for masters."""
    side = v == "E"; back = v in ("NE", "N")
    sil = np.isin(G, list(SIL)); rw = lambda cs: list(np.nonzero(np.isin(G, list(cs)).any(1))[0])
    m, w = {}, {}
    bowm = dil(G == "B", 1); s2 = sil & ~bowm
    m["sole"] = int(np.nonzero(sil.any(1))[0].max()) + 1
    top = int(np.nonzero(s2.any(1))[0].min()); hw = max(extent(s2[r] * 1, [1]) for r in range(top, top + 30))
    rl = lambda r: max([e - s for s, e in runs(s2[r] * 1, lambda q: q == 1)] or [0])
    m["crown"] = next(r for r in range(top, top + 40) if rl(r) >= 0.5 * hw)
    T_ = [r for r in rw("T") if (G[r] == "T").sum() >= 2]; m["ankle"] = min(T_)
    D_ = [r for r in rw("D")]
    m["shoulder"] = min(D_)
    if man is not None:
        m["eye"] = man.get("eye"); m["chin"] = man.get("chin")
    else:
        e = [r for r in rw("e") if r < m["shoulder"] and (G[r] == "e").sum() >= 2]  # H2: >= 2 eye px per row, largest contiguous block (fringe blend noise)
        if e:
            bl_, cu_ = [], [e[0]]
            for r in e[1:]:
                if r == cu_[-1] + 1: cu_.append(r)
                else: bl_.append(cu_); cu_ = [r]
            bl_.append(cu_); e = max(bl_, key=len)
        m["eye"] = (min(e) + max(e) + 1) / 2 if (e and not back) else None
        # chin = bottom edge of the head skin: last row (above the shoulder) with skin wider than the neck, +1
        N_ = rw("N"); F_ = [r for r in rw("F") if r < m["shoulder"] + 2]
        m["chin"] = min(N_) if N_ else ((max(F_) + 1) if F_ else None)
        if back: m["chin"] = None
    O_ = [r for r in rw("O") if r > m["shoulder"]]
    if O_:  # largest contiguous block of obi rows
        blocks, cur = [], [O_[0]]
        for r in O_[1:]:
            if r == cur[-1] + 1: cur.append(r)
            else: blocks.append(cur); cur = [r]
        blocks.append(cur); O_ = max(blocks, key=len)
    m["waist"] = (min(O_) + max(O_) + 1) / 2 if O_ else None
    cnt = lambda r, c: int((G[r] == c).sum())
    r = int(max(O_)) if O_ else m["shoulder"] + 10
    while r < 127 and cnt(r, "D") >= 3: r += 1
    m["hem"] = r
    if part is not None and (part == 3).any(): m["hem"] = int(np.nonzero((part == 3).any(1))[0].max()) + 1  # rig: skirt part bottom
    X_ = [r for r in range(m["hem"], 124) if all(cnt(r + i, "X") >= 1 for i in range(4))]; m["socktop"] = min(X_) if X_ else None
    m["armpit"] = None
    if not side:
        for r in range(m["shoulder"] + 3, m["hem"]):
            if len(runs(G[r], lambda q: np.isin(q, list(SIL)))) >= 3: m["armpit"] = r; break
    # legs: per-row max silhouette run below the hem
    lg = lambda r: max([e - s for s, e in runs(G[r], lambda q: np.isin(q, list(SIL)))] or [0])
    st = m["socktop"] if m["socktop"] is not None else m["hem"] + 4
    w["band"] = lg(st - 1) if st - 1 >= m["hem"] else 0  # skin band (thigh) width just above the sock top
    w["sock"] = lg(st + 1)
    if side:  # side view: knee = most forward/back narrowing hard to define; use leg depth profile minimum below sock top
        prof = {r: lg(r) for r in range(st + 2, m["ankle"])}
    else:
        prof = {r: lg(r) for r in range(st + 2, m["ankle"])}
    # knee: masters = manual (crease / outline bump, master_manual.json); rig = projected knee joints (render json pts knee.R/L)
    m["knee"] = (man or {}).get("knee") if man is not None else knee_px
    kk = int(round(m["knee"])) if m["knee"] is not None else (m["ankle"] - 6)
    w["calf"] = lg(min(kk + 3, m["ankle"] - 1))
    w["foot"] = maxrun(G[m["sole"] - 2], "TK") if (G[m["sole"] - 2] == "K").any() else maxrun(G[m["sole"] - 2], "T")
    w["foot"] = lg(m["sole"] - 2)
    hr = range(m["crown"], (m["chin"] or m["shoulder"]))
    w["head"] = max(extent(s2[r] * 1, [1]) for r in hr)
    w["shoulder"] = max(extent(G[r], SIL) for r in range(m["shoulder"], m["shoulder"] + 4))
    w["sleeves"] = max(extent(G[r], SIL) for r in range(m["shoulder"] + 4, m["hem"]))  # widest arm/sleeve span
    if O_: w["obi"] = max(maxrun(G[r], "O") for r in O_)
    w["hem"] = extent(G[m["hem"] - 2], SIL) if side else max(e - s for s, e in runs(G[m["hem"] - 2], lambda q: np.isin(q, list(SIL))))  # skirt width just above the hem (central run)
    nk = [r for r in range(m["chin"] or m["shoulder"], m["shoulder"])] if m["chin"] else []
    w["neck"] = max([maxrun(G[r], "FN") for r in nk] or [0])
    return m, w
# H2: no SE armpit (near sleeve overlaps the torso in 3/4; the polished master's first 3-run row is the far hand's fingers)
VW = {"S": ("crown eye chin shoulder armpit waist hem socktop knee ankle", "head neck shoulder sleeves obi hem band sock calf foot"),
      "SE": ("crown eye chin shoulder waist hem socktop knee ankle", "head neck shoulder sleeves obi hem band sock calf foot"),
      "E": ("crown eye chin shoulder waist hem socktop knee ankle", "head sleeves hem band sock calf foot"),
      "NE": ("crown shoulder armpit waist hem socktop knee ankle", "head shoulder sleeves obi hem band sock calf foot"),
      "N": ("crown shoulder armpit waist hem socktop knee ankle", "head shoulder sleeves obi hem band sock calf foot")}
_MCACHE = {}
def master_meas(v):
    if v not in _MCACHE:
        G, _ = master(v); _MCACHE[v] = measure(G, v, MAN[v])
    return _MCACHE[v]
def residuals(rm, rw_, v):
    mm, mw = master_meas(v); sh = mm["sole"] - rm["sole"]; d = {"H": (rm["sole"] - rm["crown"]) - (mm["sole"] - mm["crown"])}
    rr, ws = VW[v]
    for s in rr.split(): d[s] = None if (rm.get(s) is None or mm.get(s) is None) else round(rm[s] + sh - mm[s], 2)
    for s in ws.split(): d["w" + s] = None if (s not in rw_ or s not in mw) else round(rw_[s] - mw[s], 2)
    return d
if __name__ == "__main__":
    for v in ["S", "SE", "E", "NE", "N"]:
        print(v, master_meas(v))
