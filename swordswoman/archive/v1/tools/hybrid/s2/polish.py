#!/usr/bin/env python3
"""S2 polish pass (Claude pixel paint-over) on pixelized Gemini panels.

  polish.py SPEC.json

SPEC: {"src_dir": px dir, "slice_dir": .., "out_dir": .., "sprites": {name: {
    "head": "head_SE" | null,         lock stamp to paste (byte-identical cel)
    "head_dxy": [dx, dy],             manual nudge after the auto class-match fit
    "head_at": [x, y],                absolute top-left (overrides the fit)
    "bow_lag": [dx, dy],              shift the bow cel (bow_<DIR>) against the head for secondary motion
    "katana": true|false,             redraw the blade (2 px: steel_0 spine + steel_2 edge), guard + hilt
    "blade": [[gx, gy], [tx, ty]],    manual guard/tip (overrides detection)
    "erase": [[x0,y0,x1,y1], ...],    clear boxes before drawing (e.g. pixelized Gemini smear junk)
    "ops": ["smear ...", ...]          draw.py ops, run last
}}}
"""
import json, os, subprocess, sys
import numpy as np
from PIL import Image
from scipy import ndimage as ndi
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
import hylib as H  # noqa
import pixelize as P  # noqa
import draw as D  # noqa
sys.path.insert(0, HERE)
from px_sheet_lib import my_body  # noqa

PAL = H.palette()
I = {n: PAL.index[PAL.resolve(n)] for n in ["outline", "hair_0", "hair_1", "hair_2", "red_0", "red_1", "red_2", "red_3",
                                            "skin_0", "skin_1", "skin_2", "steel_0", "steel_1", "steel_2", "dark_1",
                                            "eye_0", "eye_1", "pink_0", "pink_1", "leather_1", "leather_2"]}
STAMPS = "hybrid/lock/pixel"


def base_of(i):
    return H.name_base(PAL.names[i]) if i >= 0 else None


def load_idx(p):
    return H.index_of(H.load_rgba(p))


def save_idx(idx, p):
    o = H.rgba_of(np.where(idx < 0, 0, idx)); o[idx < 0] = 0
    H.save_rgba(o, p)


def fit_head(idx, st):
    """search the stamp offset that best matches materials (hair/bow red/face skin) of the old head."""
    sh, sw = st.shape
    sb = np.vectorize(lambda i: base_of(i) or "")(st)
    ob = np.vectorize(lambda i: base_of(i) or "")(idx)
    op = idx >= 0
    rows = np.nonzero(op.any(1))[0]
    top = rows.min()
    best = (-1e9, 0, 0)
    for y in range(top - 6, top + 12):
        for x in range(10, 128 - sw - 10):
            o = ob[y:y + sh, x:x + sw]; m = st >= 0
            if o.shape != st.shape:
                continue
            same = (o == sb) & m & (sb != "outline")
            score = same.sum() * 2 + ((o != "") & m).sum() - ((o == "") & m).sum() * 1.5
            if score > best[0]:
                best = (score, x, y)
    return best[1], best[2]


def paste_head(idx, name, spec):
    st = load_idx(f"{STAMPS}/{name}.png")
    ys, xs = np.nonzero(st >= 0)
    st = st[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    if "head_at" in spec:
        x, y = spec["head_at"]
    else:
        x, y = fit_head(idx, st)
        dx, dy = spec.get("head_dxy", [0, 0]); x += dx; y += dy
    sh, sw = st.shape
    m = st >= 0
    # erase old head material around the stamp (outside it) above its chin rows
    chin = y + sh - 3
    ring = ndi.binary_dilation(np.pad(m, 4), iterations=4)
    full = np.zeros(idx.shape, bool)
    full[y - 4:y + sh + 4, x - 4:x + sw + 4] = ring
    stm = np.zeros(idx.shape, bool); stm[y:y + sh, x:x + sw] = m
    rr = np.arange(128)[:, None] < chin
    headmat = np.isin(idx, [I["hair_0"], I["hair_1"], I["hair_2"], I["skin_1"], I["skin_2"], I["eye_0"], I["eye_1"], I["outline"]])
    bowmat = np.isin(idx, [I["red_0"], I["red_1"], I["red_2"], I["red_3"]]) & (np.arange(128)[:, None] < y + 10)
    kill = full & ~stm & rr & (headmat | bowmat)
    idx[kill] = -1
    sub = idx[y:y + sh, x:x + sw]
    sub[m] = st[m]
    return idx, (x, y, sw, sh)


def bow_lag(idx, name, box, dxy):
    """move the bow cel (bow_<DIR>.png rows above the skull) by dxy, refilling under it from the stamp."""
    x, y, sw, sh = box
    bw = load_idx(f"{STAMPS}/bow_{name.split('_')[1]}.png") if os.path.exists(f"{STAMPS}/bow_{name.split('_')[1]}.png") else None
    if bw is None:
        return idx
    bm = bw >= 0
    bh = bm.shape[0]
    # bow pixels = the red pixels in the stamp's top bh rows
    region = idx[y:y + bh, x:x + sw].copy()
    red = np.isin(region, [I["red_0"], I["red_1"], I["red_2"], I["red_3"]])
    # include the outline ring around the red
    ring = ndi.binary_dilation(red) & (region == I["outline"]) & (np.arange(bh)[:, None] < bh - 3)
    cel = red | ring
    vals = region[cel]
    ys, xs = np.nonzero(cel)
    region[cel] = -1
    # fill vacated pixels that were over the hair dome with hair_0 (rows lower half), else clear
    idx[y:y + bh, x:x + sw] = region
    dx, dy = dxy
    for (yy, xx, v) in zip(ys, xs, vals):
        Y, X = y + yy + dy, x + xx + dx
        idx[Y, X] = v
    # patch holes inside the head silhouette: hole pixel with >=3 opaque 4-neighbours -> hair_0
    for _ in range(2):
        op = idx >= 0
        nb = sum(np.roll(op, s, a) for s in (-1, 1) for a in (0, 1))
        hole = (~op) & (nb >= 3)
        hole[:y] = False; hole[y + bh + 2:] = False
        idx[hole] = I["hair_0"]
    return idx


def blade_from_slice(sl_path, meta):
    rgb, mask, _ = P.remove_bg(Image.open(sl_path), "auto", 11.0)
    a = rgb.astype(float); mx = a.max(-1); mn = a.min(-1)
    inner = ndi.binary_erosion(mask, iterations=3)
    steel = inner & (mx - mn < 34) & (mx > 105)
    lab, n = ndi.label(steel, structure=np.ones((3, 3)))
    best = None
    for i in range(1, n + 1):
        yy, xx = np.nonzero(lab == i)
        if len(yy) < 0.0015 * mask.sum():
            continue
        cov = np.cov(np.stack([xx, yy]).astype(float))
        ev, evec = np.linalg.eigh(cov)
        el = np.sqrt(ev[1] / max(ev[0], 1e-6))
        if el >= 3 and (best is None or len(yy) > best[0]):
            v = evec[:, 1]; c = np.array([xx.mean(), yy.mean()])
            pr = (np.stack([xx, yy], 1) - c) @ v
            best = (len(yy), c + v * pr.min(), c + v * pr.max())
    if best is None:
        return None
    ys, xs = np.nonzero(mask); bx0, by0 = xs.min(), ys.min()
    s = meta["scale"]; ox, oy = meta["offset"]; dx, dy = meta.get("post_shift", [0, 0])
    f = lambda p: ((p[0] + 0.5 - bx0) * s + ox + dx - 0.5, (p[1] + 0.5 - by0) * s + oy + dy - 0.5)
    return f(best[1]), f(best[2])


def draw_katana(idx, guard, tip, hilt_len=5, behind=False):
    g = np.array(guard, float); t = np.array(tip, float)
    v = t - g; L = np.linalg.norm(v); u = v / max(L, 1e-6)
    nrm = np.array([-u[1], u[0]])
    if nrm[1] > 0:           # spine on the upper side
        nrm = -nrm
    # erase old blade pixels along the path (steel / dark / eye-misclass / outline thin)
    yy, xx = np.mgrid[0:128, 0:128]
    P_ = np.stack([xx - g[0], yy - g[1]], -1)
    sproj = P_ @ u; dist = np.abs(P_ @ nrm)
    near = (sproj > 0.5) & (sproj < L + 1.5) & (dist < 2.2)
    old = np.isin(idx, [I["steel_0"], I["steel_1"], I["steel_2"], I["dark_1"], I["eye_0"], I["eye_1"], I["outline"], I["pink_0"], I["pink_1"]])
    if not behind:
        idx[near & old] = -1
    keep = idx.copy()
    # blade: edge line (steel_2) + spine line (steel_0) offset by the normal
    e = D.pixel_perfect(D.bresenham(*map(int, np.round(g + u)), *map(int, np.round(t))))
    sp = D.pixel_perfect(D.bresenham(*map(int, np.round(g + u + nrm)), *map(int, np.round(t - u * 1.5 + nrm))))
    for (x, y) in sp:
        if 0 <= x < 128 and 0 <= y < 128:
            idx[y, x] = I["steel_0"]
    for (x, y) in e:
        if 0 <= x < 128 and 0 <= y < 128:
            idx[y, x] = I["steel_2"]
    # guard: bar across the blade (steel_1, 1 px each side) + crescent hook pixel (steel_0) on one end
    for k in (-1, 0, 1):
        p = np.round(g + nrm * k).astype(int)
        idx[p[1], p[0]] = I["steel_1"] if k else I["outline"]
    hk = np.round(g - nrm * 2 + u).astype(int)
    idx[hk[1], hk[0]] = I["steel_1"]
    # hilt: wrapped handle behind the guard, outline / red_2 diamonds; keep the fist (skin) on top
    for k in range(1, hilt_len + 1):
        p = np.round(g - u * k).astype(int)
        if not (0 <= p[0] < 128 and 0 <= p[1] < 128):
            continue
        if base_of(idx[p[1], p[0]]) == "skin":
            continue
        idx[p[1], p[0]] = I["red_2"] if k in (2, 4) else (I["steel_1"] if k == hilt_len else I["outline"])
    if behind:
        idx[keep >= 0] = keep[keep >= 0]
    return idx


def main():
    spec = json.load(open(sys.argv[1]))
    os.makedirs(spec["out_dir"], exist_ok=True)
    for name, sp in spec["sprites"].items():
        src = os.path.join(spec["src_dir"], name + ".png")
        meta = json.load(open(os.path.join(spec["src_dir"], name + "_meta.json")))
        idx = load_idx(src)
        for b in sp.get("erase", []):
            x0, y0, x1, y1 = b; idx[y0:y1 + 1, x0:x1 + 1] = -1
        for b in sp.get("erase_only", []):          # [x0,y0,x1,y1, [names]]
            x0, y0, x1, y1, ns = b
            sub = idx[y0:y1 + 1, x0:x1 + 1]
            sub[np.isin(sub, [I[n] for n in ns])] = -1
        if sp.get("keep_main"):
            op = idx >= 0
            lab, n = ndi.label(op, structure=np.ones((3, 3)))
            if n > 1:
                sz = ndi.sum(op, lab, range(1, n + 1))
                idx[~np.isin(lab, 1 + np.nonzero(sz >= sp["keep_main"])[0])] = -1
        if sp.get("shift"):
            dx, dy = sp["shift"]
            idx = np.roll(np.roll(idx, dy, 0), dx, 1)
        info = {}
        def do_katana(idx):
            bl = sp.get("blade") or blade_from_slice(os.path.join(spec["slice_dir"], name + "_genflat.png"), meta)
            if bl:
                g, t = bl
                if sp.get("swap_blade"):
                    g, t = t, g
                elif "blade" not in sp:
                    # tip = the end farther from the body centre (feet pivot, mid-height)
                    c = np.array([64, 80])
                    if np.linalg.norm(np.array(g) - c) > np.linalg.norm(np.array(t) - c):
                        g, t = t, g
                info["blade"] = [list(map(float, g)), list(map(float, t))]
                idx = draw_katana(idx, g, t, sp.get("hilt", 5), sp.get("katana_behind", False))
            return idx
        if sp.get("katana", True) and not sp.get("katana_after_head"):
            idx = do_katana(idx)
        if sp.get("head"):
            idx, box = paste_head(idx, sp["head"], sp)
            info["head_box"] = list(map(int, box))
            if sp.get("bow_lag"):
                idx = bow_lag(idx, sp["head"], box, sp["bow_lag"])
        if sp.get("katana", True) and sp.get("katana_after_head"):
            idx = do_katana(idx)
        out = os.path.join(spec["out_dir"], name + ".png")
        save_idx(idx, out)
        if sp.get("ops"):
            r = subprocess.run([sys.executable, os.path.join(HERE, "..", "draw.py"), out, "--out", out] + sp["ops"],
                               capture_output=True, text=True)
            if r.returncode:
                print(r.stderr[-800:])
        H.save_rgba(H.up(H.load_rgba(out), 4), out.replace(".png", "_4x.png"))
        json.dump(info, open(out.replace(".png", "_polish.json"), "w"))
        print(name, info)


if __name__ == "__main__":
    main()
