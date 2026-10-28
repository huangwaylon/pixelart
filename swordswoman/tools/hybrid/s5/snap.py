"""Snap a Gemini pixel-native image to its exact grid, majority-vote each cell, register to the seed,
quantize per material (seed material prior), write a 128-cell sprite.
snap.py NAME MODE TAG [--out path]  ->  snap/<name>_<mode>_<tag>.png (+ _dbg.json)"""
import sys, json
import numpy as np
from PIL import Image
from common import *
import hylib as H
from template import win

def is_bg(a):
    r, g, b = [a[..., i].astype(int) for i in range(3)]
    return (g > r + 50) & (g > b + 50)

def edge_profile(a, axis):
    f = a.astype(float)
    d = np.abs(np.diff(f, axis=axis)).sum(-1)
    return d.sum(axis=1 - axis)  # profile along the axis

def detect(prof, exp):
    """best (pitch, offset): edges at offset + i*pitch."""
    L = len(prof); best = (-1, exp, 0)
    prof = prof / (prof.mean() + 1e-9)
    for p in np.arange(exp * 0.9, exp * 1.1, 0.02):
        n = int(L / p) + 1
        for o in np.arange(0, p, 0.25):
            pos = np.round(o + np.arange(n) * p - 0.5).astype(int)
            pos = pos[(pos >= 0) & (pos < L)]
            s = prof[pos].mean()
            if s > best[0]: best = (s, p, o)
    return best

def vote(a, bg, px, ox, py, oy):
    nx, ny = int((a.shape[1] - ox) / px), int((a.shape[0] - oy) / py)
    out = np.zeros((ny, nx, 4), np.uint8); agree = []
    for j in range(ny):
        for i in range(nx):
            x0, x1 = ox + i * px, ox + (i + 1) * px; y0, y1 = oy + j * py, oy + (j + 1) * py
            xs = slice(int(x0 + 0.25 * px), max(int(x0 + 0.25 * px) + 1, int(x1 - 0.25 * px)))
            ys = slice(int(y0 + 0.25 * py), max(int(y0 + 0.25 * py) + 1, int(y1 - 0.25 * py)))
            blk = a[ys, xs, :3].reshape(-1, 3).astype(int); bb = bg[ys, xs].reshape(-1)
            if bb.mean() > 0.5: continue
            blk = blk[~bb]
            q = (blk // 12)
            keys, inv, cnt = np.unique(q, axis=0, return_inverse=True, return_counts=True)
            k = cnt.argmax(); agree.append(cnt[k] / len(blk))
            out[j, i, :3] = blk[inv.reshape(-1) == k].mean(0); out[j, i, 3] = 255
    return out, float(np.mean(agree)) if agree else 0

SEED_MAT = {"hair": "hair", "red": "red", "skin": "skin", "leather": "leather", "dark": "dark", "steel": "sword",
            "eye": "face", "pink": "pink", "purple": "purple"}

def mat_prior(seed):
    """material index map from the seed's palette tones, grown 3 px outward (nearest)."""
    idx = H.index_of(seed); pal = H.palette()
    mat = np.full(idx.shape, -1, int)
    for i, n in enumerate(pal.names):
        b = H.name_base(n)
        if b in SEED_MAT: mat[idx == i] = H.MAT_NAMES.index(SEED_MAT[b])
    # the head region is "face" (skin/eye/pink) + hair + red bow: let it be free
    for _ in range(4):
        z = mat < 0
        for dy, dx in H.N4:
            sh = H.shift(mat, dy, dx, fill=-1); mat = np.where(z & (sh >= 0), sh, mat); z = mat < 0
    return mat

def snap(name, mode, tag):
    src = np.array(Image.open(f"{OUT}/gem/{name}_{mode}_{tag}.png").convert("RGB").resize((1024, 1024), Image.NEAREST))
    bg = is_bg(src)
    n = 80 if mode == "1x" else 160
    exp = 1024 / n
    sx, px, ox = detect(edge_profile(src, 1), exp)
    sy, py, oy = detect(edge_profile(src, 0), exp)
    grid, agree = vote(src, bg, px, ox, py, oy)
    if mode == "2x":   # block 2x2 downsample: mode colour of the 4 sub-cells (alpha if >= 2 opaque)
        g2 = np.zeros((grid.shape[0] // 2, grid.shape[1] // 2, 4), np.uint8)
        for j in range(g2.shape[0]):
            for i in range(g2.shape[1]):
                b = grid[2*j:2*j+2, 2*i:2*i+2].reshape(-1, 4)
                op = b[b[:, 3] > 0]
                if len(op) < 2: continue
                # prefer the darkest when it is an outline-ish pixel (keeps 1px lines), else mode
                q = [tuple((c[:3] // 16).tolist()) for c in op]
                best = max(set(q), key=q.count)
                if q.count(best) == 1:
                    best_c = op[np.argmin(op[:, :3].sum(1))]
                else:
                    best_c = op[[k for k, t in enumerate(q) if t == best]].mean(0)
                g2[j, i, :3] = best_c[:3]; g2[j, i, 3] = 255
        grid = g2
    # register against the seed window (integer shift)
    WIN = win(name)
    seed = load(f"{OUT}/seed/{name}.png")
    sw = seed[WIN[1]:WIN[3], WIN[0]:WIN[2], 3] > 0
    gm = np.zeros((80, 80), bool); gg = np.zeros((80, 80, 4), np.uint8)
    hh, ww = min(80, grid.shape[0]), min(80, grid.shape[1])
    gm[:hh, :ww] = grid[:hh, :ww, 3] > 0; gg[:hh, :ww] = grid[:hh, :ww]
    best = (-1, 0, 0)
    for dy in range(-10, 11):
        for dx in range(-10, 11):
            m = np.roll(np.roll(gm, dy, 0), dx, 1)
            iou = (m & sw).sum() / max((m | sw).sum(), 1)
            if iou > best[0]: best = (iou, dx, dy)
    import os
    if os.environ.get("S5_REG") == "head":
        # anchor on the hair mass: Gemini hair tones vs the locked head stamp's hair tones
        st = load(f"{ROOT}/hybrid/lock/pixel/head_{dir_of(name)}.png"); hx_, hy_ = head_xy(name)
        sm = np.zeros((128, 128), bool)
        hs = np.zeros(st.shape[:2], bool)
        for k in ("hair_0", "hair_1", "hair_2"): hs |= np.all(st[..., :3] == TRGB[k], -1) & (st[..., 3] > 0)
        sm[hy_:hy_+st.shape[0], hx_:hx_+st.shape[1]] = hs
        sm = sm[WIN[1]:WIN[3], WIN[0]:WIN[2]]
        lab = H.srgb_to_lab(gg[..., :3].astype(float))
        hp = H.pal_lab(["hair_0", "hair_1", "hair_2"])
        dmin = np.min(np.linalg.norm(lab[..., None, :] - hp[None, None], axis=-1), -1)
        gh = (gg[..., 3] > 0) & (dmin < 12)
        best = (-1, 0, 0)
        for dy in range(-12, 13):
            for dx in range(-12, 13):
                m = np.roll(np.roll(gh, dy, 0), dx, 1)
                v = (m & sm).sum() / max((m | sm).sum(), 1)
                if v > best[0]: best = (v, dx, dy)
    iou, dx, dy = best
    g2 = np.zeros_like(gg)
    ys0, ys1 = max(0, dy), min(80, 80 + dy); xs0, xs1 = max(0, dx), min(80, 80 + dx)
    g2[ys0:ys1, xs0:xs1] = gg[ys0 - dy:ys1 - dy, xs0 - dx:xs1 - dx]
    gg = g2
    cell = np.zeros((128, 128, 4), np.uint8); cell[WIN[1]:WIN[3], WIN[0]:WIN[2]] = gg
    # per-material quantize
    a = cell[..., 3] > 0
    mat = mat_prior(seed)
    cls, _ = H.classify(cell[..., :3], allowed=np.where(a, mat, -1), penalty=6.0)
    q = H.quantize_tones(cell[..., :3], cls)
    q[~a] = -1
    out = H.rgba_of(q)
    meta = dict(name=name, mode=mode, tag=tag, pitch=[px, py], offset=[ox, oy], edge_score=[sx, sy],
                vote_agree=agree, grid=list(grid.shape[:2]), reg_shift=[dx, dy], iou_seed=iou)
    return out, meta

if __name__ == "__main__":
    name, mode, tag = sys.argv[1:4]
    out, meta = snap(name, mode, tag)
    p = f"{OUT}/snap/{name}_{mode}_{tag}.png"
    save(out, p); json.dump(meta, open(p[:-4] + "_meta.json", "w"), indent=1)
    print(json.dumps({k: (round(v, 3) if isinstance(v, float) else v) for k, v in meta.items()}))
