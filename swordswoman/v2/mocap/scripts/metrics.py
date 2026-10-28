# metrics.py: readability metrics + strips for render_jobs.py output (1x = 64 cell crop of the 96 render cell, pivot (32,60), feet bottom row 61)
import os, json, math
import numpy as np
from PIL import Image, ImageDraw
BG = (0x6e, 0x6e, 0x6e)
CROP = (16, 16)  # 96 cell -> 64 cell offset
def _blocks(im, k): return im.reshape(96, k, 96, k, *im.shape[2:])
def load1x(stem):
    """returns dict: alpha(64,64 bool), part(64,64 int), core(bool), blade(bool), matid (64,64,4 uint8)"""
    out = {}
    for kind in ("matid", "part", "core", "blade"):
        a = np.asarray(Image.open(f"{stem}_{kind}.png").convert("RGBA")); k = a.shape[0] // 96
        al = a[..., 3] > 127
        cov = al.reshape(96, k, 96, k).mean((1, 3)) > 0.5
        if kind == "part":
            ids = np.where(al, np.round(a[..., 0] / 25.0).astype(int), 0)
            b = ids.reshape(96, k, 96, k).transpose(0, 2, 1, 3).reshape(96, 96, k * k)
            cnt = np.stack([(b == g).sum(-1) for g in range(1, 11)], -1); maj = cnt.argmax(-1) + 1
            out["part"] = np.where(cov, maj, 0)
        elif kind == "matid":
            # majority colour of the opaque subpixels (centre-weighted): take the most common rgb per block
            b = a.reshape(96, k, 96, k, 4).transpose(0, 2, 1, 3, 4).reshape(96, 96, k * k, 4)
            key = (b[..., 0].astype(np.int64) << 16) | (b[..., 1].astype(np.int64) << 8) | b[..., 2]
            key = np.where(b[..., 3] > 127, key, -1)
            m = np.zeros((96, 96, 4), np.uint8)
            for y in range(96):
                for x in range(96):
                    if not cov[y, x]: continue
                    v, c = np.unique(key[y, x][key[y, x] >= 0], return_counts=True); kk = int(v[c.argmax()])
                    m[y, x] = ((kk >> 16) & 255, (kk >> 8) & 255, kk & 255, 255)
            out["matid"] = m
            out["alpha"] = cov
        else:
            out[kind] = cov
    if os.path.exists(f"{stem}_smear.png"):  # VFX smear composited BEHIND the body (1x)
        a = np.asarray(Image.open(f"{stem}_smear.png").convert("RGBA")); k = a.shape[0] // 96
        sm = (a[..., 3] > 127).reshape(96, k, 96, k).mean((1, 3)) > 0.4
        add = sm & ~out["alpha"]; out["matid"][add] = (240, 242, 255, 255); out["smear"] = add
    y0, x0 = CROP
    full = {k: v[y0:y0 + 64, x0:x0 + 64] for k, v in out.items()}
    full["vis"] = full["alpha"] | full["smear"] if "smear" in full else full["alpha"]
    full["clip"] = int(out["alpha"].sum() - full["alpha"].sum())
    return full
def loa(pts, air):
    P = {k: np.array(v) - np.array(CROP[::-1]) for k, v in pts.items()}
    ft = P["foot.R"] if P["foot.R"][1] > P["foot.L"][1] else P["foot.L"]  # support (lowest) foot
    if air: ft = (P["foot.R"] + P["foot.L"]) / 2
    top = P["head_top"]; d = ft - top; L = np.linalg.norm(d) + 1e-6
    tilt = math.degrees(math.atan2(d[0], d[1]))  # + = head leans left of the foot? (x of foot - x of head)
    nrm = np.array([-d[1], d[0]]) / L
    dev = [float(np.dot(P[k] - top, nrm)) for k in ("chest", "hips")]
    shape = "S" if dev[0] * dev[1] < -0.25 else ("C" if max(abs(dev[0]), abs(dev[1])) > 1.0 else "I")
    return {"tilt": round(-tilt, 1), "bend_px": round(max(abs(dev[0]), abs(dev[1])), 1), "shape": shape}
def metrics(stem, fr, prev=None):
    d = load1x(stem); al, part, core, bl = d["alpha"], d["part"], d["core"], d["blade"]
    if "smear" in d: al = al & ~d["smear"]
    area = int(al.sum()); limbs = np.isin(part, (4, 5, 6, 7, 8, 9))
    neg = int((limbs & ~core).sum()); bladevis = int(((part == 8) | (part == 9)).sum()); bladeall = int(bl.sum())
    head = part == 1
    ov = int((bl & core).sum())
    rows = np.where(al.any(1))[0]; cols = np.where(al.any(0))[0]
    bottom = int(rows.max()) if len(rows) else 0; top = int(rows.min()) if len(rows) else 0
    gap = round(fr["pts"].get("zmin_px", 61 - bottom), 1)
    m = {"area": area, "neg": neg, "neg_frac": round(neg / max(1, area), 3), "blade_vis": bladevis, "blade_all": bladeall,
         "blade_hidden": max(0, bladeall - bladevis), "blade_over_body": ov, "ground_gap": gap, "foot_px": int(al[bottom].sum()) if len(rows) else 0,
         "h": bottom - top + 1, "bottom": bottom, "w": int(cols.max() - cols.min() + 1) if len(cols) else 0, "clip": d["clip"]}
    p = fr["pts"]
    if "blade_tip" in p: m["blade_len"] = round(float(np.hypot(*(np.array(p["blade_tip"]) - np.array(p["blade_pommel"])))), 1)
    m.update(loa(p, fr.get("air", False)))
    if prev is not None:
        u = (al | prev).sum(); m["delta"] = round(float((al ^ prev).sum() / max(1, u)), 3)
    return m, d
def score(m, want_air=False):
    s = 2.0 * min(m["neg_frac"], 0.35) * 10 + 0.06 * min(m.get("blade_len", 0), 26) - 0.08 * m["blade_over_body"] - 0.06 * m["blade_hidden"]
    s += 0.05 * min(abs(m["tilt"]), 25) + 0.15 * min(m["bend_px"], 4) + 0.01 * m["w"] - 0.05 * m["clip"]
    if not want_air and abs(m["ground_gap"]) > 0.5: s -= 2
    if want_air: s += 0.2 * min(m["ground_gap"], 8)
    return round(s, 2)
def tile(d, label="", sub=""):
    """cell: 1x sil (actual) | 4x sil | 4x matid, on #6e6e6e"""
    al = d["alpha"]; W = 64 * 4
    sil = np.where(al[..., None], np.array([20, 20, 24]), np.array(BG)).astype(np.uint8)
    mat = d["matid"].copy(); bg = np.zeros_like(mat); bg[..., :3] = BG; bg[..., 3] = 255; mat = np.where(d.get("vis", al)[..., None], mat, bg)
    s1 = Image.fromarray(sil); s4 = s1.resize((W, W), Image.NEAREST); m4 = Image.fromarray(mat[..., :3]).resize((W, W), Image.NEAREST)
    T = Image.new("RGB", (72 + 2 * W + 8, W + 30), BG); T.paste(s1, (4, 26)); T.paste(s4, (72, 26)); T.paste(m4, (72 + W + 8, 26))
    dr = ImageDraw.Draw(T); dr.text((4, 2), label, fill=(255, 255, 255)); dr.text((4, 13), sub, fill=(230, 230, 160))
    # ground line marker
    dr.line([(72, 26 + 62 * 4), (72 + W, 26 + 62 * 4)], fill=(90, 90, 90))
    return T
def strip(tiles, path, cols=3):
    w, h = tiles[0].size; n = len(tiles); r = (n + cols - 1) // cols
    S = Image.new("RGB", (w * min(cols, n), h * r), BG)
    for i, t in enumerate(tiles): S.paste(t, ((i % cols) * w, (i // cols) * h))
    S.save(path); return S.size
def ones_row(ds, path, scale=1, gap=4):
    """1x silhouettes + matid side by side (true size, then optional scale)"""
    n = len(ds); im = Image.new("RGB", (n * (64 + gap), 2 * 64 + gap), BG)
    for i, d in enumerate(ds):
        al = d["alpha"]; sil = np.where(al[..., None], np.array([20, 20, 24]), np.array(BG)).astype(np.uint8)
        mat = np.where(d.get("vis", al)[..., None], d["matid"][..., :3], np.array(BG)).astype(np.uint8)
        im.paste(Image.fromarray(sil), (i * (64 + gap), 0)); im.paste(Image.fromarray(mat), (i * (64 + gap), 64 + gap))
    if scale > 1: im = im.resize((im.width * scale, im.height * scale), Image.NEAREST)
    im.save(path); return im.size
def small(d, label=""):
    al = d["alpha"]; mat = np.where(d.get("vis", al)[..., None], d["matid"][..., :3], np.array(BG)).astype(np.uint8)
    sil = np.where(al[..., None], np.array([20, 20, 24]), np.array(BG)).astype(np.uint8)
    T = Image.new("RGB", (64 * 2 + 64 + 4, 64 * 2 + 12), BG); T.paste(Image.fromarray(mat).resize((128, 128), Image.NEAREST), (0, 12))
    T.paste(Image.fromarray(sil), (130, 12 + 64)); T.paste(Image.fromarray(mat), (130, 12)); ImageDraw.Draw(T).text((1, 0), label, fill=(255, 255, 0)); return T
def crit_strip(ds, names, path, title="", s=3):
    """critic sheet for one action/view: row A = 1x matid + 1x silhouette at TRUE size; row B = matid x s; row C = silhouette x s (all on #6e6e6e)"""
    n = len(ds); cw = 64 * s + 6; W = max(n * cw, n * 140 + 10); H = 16 + 70 + 14 + 2 * (64 * s + 4)
    O = Image.new("RGB", (W, H), BG); dr = ImageDraw.Draw(O); dr.text((4, 2), title, fill=(255, 255, 255))
    for i, d in enumerate(ds):
        al = d["alpha"]; mat = np.where(d.get("vis", al)[..., None], d["matid"][..., :3], np.array(BG)).astype(np.uint8)
        sil = np.where(al[..., None], np.array([20, 20, 24]), np.array(BG)).astype(np.uint8)
        O.paste(Image.fromarray(mat), (4 + i * 140, 18)); O.paste(Image.fromarray(sil), (4 + i * 140 + 68, 18))
        y = 18 + 70; dr.text((4 + i * cw, y), f"{i} {names[i]}", fill=(255, 255, 160))
        O.paste(Image.fromarray(mat).resize((64 * s, 64 * s), Image.NEAREST), (4 + i * cw, y + 14))
        O.paste(Image.fromarray(sil).resize((64 * s, 64 * s), Image.NEAREST), (4 + i * cw, y + 14 + 64 * s + 4))
    O.save(path); return O.size
