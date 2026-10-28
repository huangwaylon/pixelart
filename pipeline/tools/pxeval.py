#!/usr/bin/env python3
"""pxeval: one shared, deterministic evaluator for pixel-art sprites and animations (numpy / scipy / pillow only).

Runs under any team venv with `-I`, e.g.
  .models/pixtools/venv/bin/python -I pipeline/tools/pxeval.py still CAND.png --ref REF.png --illus ILLUS.png --pal palette.json
  ... seq REVIEW/swordswoman/anim96/walk_SE.gif
  ... seq releases/S4_hd_actions_v1/walk/walk_sheet.png --row SE         (cell + rows read from walk_sheet.json)
  ... seq frames_dir/ --mask moving.png --viz viz.png
  ... board OUT.png --row "illus:a.png" --row "ours:b.png,c.gif" --scale 4 --bg 808080
  ... gif OUT.gif f1.png f2.png ... --scale 4 --ms 100

Every subcommand prints one JSON object to stdout (and writes it to --json PATH if given). Output keys are stable
(`"pxeval": 1`); new keys may be added, existing keys will not be renamed. Definitions: REVIEW/exp/2026-10-28_pxeval/NOTES.md.

Compatibility: `still --illus` is a port of swordswoman/v2/pixelize/tools/metrics.py (ssim, ssim_b, dE, sil, bloat,
iou_*, line_f, kcomp, orph, face_ssim) incl. its pzlib.load / seg2 / materials illustration handling; SSIM and
CIEDE2000 are ports of scikit-image (structural_similarity win 7, deltaE_ciede2000) so no skimage is needed.
Orphans / jaggies follow pipeline/qa.py (orphan_count) and pipeline/render.py (jaggy_count).
"""
import argparse, glob, json, math, os, re, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage as nd

VERSION = 1


# ----------------------------------------------------------------------------------------------------------- helpers
def rnd(v, k=4):
    if isinstance(v, (bool, np.bool_)): return bool(v)
    if isinstance(v, (int, np.integer)): return int(v)
    if isinstance(v, (float, np.floating)):
        v = float(v)
        return None if math.isnan(v) or math.isinf(v) else round(v, k)
    if isinstance(v, dict): return {k2: rnd(v2, k) for k2, v2 in v.items()}
    if isinstance(v, (list, tuple)): return [rnd(x, k) for x in v]
    if isinstance(v, np.ndarray): return rnd(v.tolist(), k)
    return v


def parse_hex(h):
    h = h.strip().lstrip('#')
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def rgb2lab(x):
    """sRGB 0-255 -> CIE Lab (D65). Identical to swordswoman/v2/pixelize/tools/pzlib.rgb2lab."""
    x = np.asarray(x, float) / 255.
    x = np.where(x > 0.04045, ((x + 0.055) / 1.055) ** 2.4, x / 12.92)
    M = np.array([[0.4124, 0.3576, 0.1805], [0.2126, 0.7152, 0.0722], [0.0193, 0.1192, 0.9505]])
    xyz = x @ M.T / np.array([0.95047, 1.0, 1.08883])
    f = np.where(xyz > 0.008856, np.cbrt(xyz), 7.787 * xyz + 16 / 116)
    return np.stack([116 * f[..., 1] - 16, 500 * (f[..., 0] - f[..., 1]), 200 * (f[..., 1] - f[..., 2])], -1)


def ciede2000(lab1, lab2, kL=1, kC=1, kH=1):
    """port of skimage.color.deltaE_ciede2000 (same branch handling)."""
    lab1 = np.asarray(lab1, float); lab2 = np.asarray(lab2, float)
    L1, a1, b1 = np.moveaxis(lab1, -1, 0); L2, a2, b2 = np.moveaxis(lab2, -1, 0)
    Cbar = 0.5 * (np.hypot(a1, b1) + np.hypot(a2, b2))
    c7 = Cbar ** 7
    G = 0.5 * (1 - np.sqrt(c7 / (c7 + 25 ** 7)))
    scale = 1 + G
    C1, h1 = np.hypot(a1 * scale, b1), np.arctan2(b1, a1 * scale) % (2 * np.pi)
    C2, h2 = np.hypot(a2 * scale, b2), np.arctan2(b2, a2 * scale) % (2 * np.pi)
    Lbar = 0.5 * (L1 + L2)
    tmp = (Lbar - 50) ** 2
    SL = 1 + 0.015 * tmp / np.sqrt(20 + tmp)
    L_term = (L2 - L1) / (kL * SL)
    Cbar = 0.5 * (C1 + C2)
    SC = 1 + 0.045 * Cbar
    C_term = (C2 - C1) / (kC * SC)
    h_diff = h2 - h1; h_sum = h1 + h2; CC = C1 * C2
    dH = h_diff.copy()
    dH[h_diff > np.pi] -= 2 * np.pi
    dH[h_diff < -np.pi] += 2 * np.pi
    dH[CC == 0.0] = 0.0
    dH_term = 2 * np.sqrt(CC) * np.sin(dH / 2)
    Hbar = h_sum.copy()
    mask = (CC != 0.0) & (np.abs(h_diff) > np.pi)
    Hbar[mask & (h_sum < 2 * np.pi)] += 2 * np.pi
    Hbar[mask & (h_sum >= 2 * np.pi)] -= 2 * np.pi
    Hbar[CC == 0.0] *= 2
    Hbar *= 0.5
    T = (1 - 0.17 * np.cos(Hbar - np.deg2rad(30)) + 0.24 * np.cos(2 * Hbar) + 0.32 * np.cos(3 * Hbar + np.deg2rad(6))
         - 0.20 * np.cos(4 * Hbar - np.deg2rad(63)))
    SH = 1 + 0.015 * Cbar * T
    H_term = dH_term / (kH * SH)
    c7 = Cbar ** 7
    Rc = 2 * np.sqrt(c7 / (c7 + 25 ** 7))
    dtheta = np.deg2rad(30) * np.exp(-((np.rad2deg(Hbar) - 275) / 25) ** 2)
    R_term = -np.sin(2 * dtheta) * Rc * C_term * H_term
    dE2 = L_term ** 2 + C_term ** 2 + H_term ** 2 + R_term
    return np.sqrt(np.maximum(dE2, 0))


def ssim(X, Y, data_range=100.0, win=7):
    """port of skimage.metrics.structural_similarity (uniform window, sample covariance, K1 .01, K2 .03)."""
    X = np.asarray(X, np.float64); Y = np.asarray(Y, np.float64)
    if min(X.shape) < win: return float('nan')
    NP = win * win; cn = NP / (NP - 1)
    uf = lambda a: nd.uniform_filter(a, size=win)
    ux, uy = uf(X), uf(Y)
    vx = cn * (uf(X * X) - ux * ux); vy = cn * (uf(Y * Y) - uy * uy); vxy = cn * (uf(X * Y) - ux * uy)
    C1 = (0.01 * data_range) ** 2; C2 = (0.03 * data_range) ** 2
    S = ((2 * ux * uy + C1) * (2 * vxy + C2)) / ((ux ** 2 + uy ** 2 + C1) * (vx + vy + C2))
    p = (win - 1) // 2
    return float(S[p:-p, p:-p].mean(dtype=np.float64))


# ----------------------------------------------------------------------------------------------------------- loading
def _frames_of(im):
    out, durs = [], []
    n = getattr(im, 'n_frames', 1)
    for i in range(n):
        im.seek(i)
        out.append(np.array(im.convert('RGBA')))
        durs.append(im.info.get('duration'))
    return out, durs


def detect_scale(frames):
    """integer nearest-neighbour upscale factor + offset (gcd of colour-change positions over all frames)."""
    res = []
    for ax in (1, 0):
        pos = set()
        for f in frames:
            d = np.any(f[:, 1:] != f[:, :-1], axis=(0, 2)) if ax == 1 else np.any(f[1:] != f[:-1], axis=(1, 2))
            pos |= set((np.nonzero(d)[0] + 1).tolist())
        pos = sorted(pos)
        if len(pos) < 2: res.append((1, 0)); continue
        g = 0
        for a, b in zip(pos, pos[1:]): g = math.gcd(g, b - a)
        res.append((max(1, g), pos[0] % max(1, g)))
    k = math.gcd(res[0][0], res[1][0])
    if k <= 1: return 1, (0, 0)
    return k, (res[0][1] % k, res[1][1] % k)


def unscale(frames, mode='auto'):
    if mode in ('1', 'none', None): return frames, 1
    if mode == 'auto': k, (ox, oy) = detect_scale(frames)
    else: k, ox, oy = int(mode), 0, 0
    if k <= 1: return frames, 1
    return [f[oy::k, ox::k] for f in frames], k


def load_frames(spec, cell=None, row=None, scale='auto'):
    """spec: image / GIF / sheet / directory / glob. returns (frames RGBA list, info dict)."""
    info = {'src': spec}
    if os.path.isdir(spec):
        paths = sorted(glob.glob(os.path.join(spec, '*.png')))
    elif any(c in spec for c in '*?['):
        paths = sorted(glob.glob(spec))
    else:
        paths = [spec]
    if not paths: raise SystemExit(f'pxeval: no frames for {spec}')
    frames, durs = [], []
    for p in paths:
        f, d = _frames_of(Image.open(p))
        frames += f; durs += d
    meta = None
    if len(paths) == 1 and paths[0].lower().endswith('.png'):
        js = os.path.splitext(paths[0])[0] + '.json'
        if os.path.exists(js):
            try: meta = json.load(open(js))
            except Exception: meta = None
    if cell is None and meta and isinstance(meta, dict) and 'frameSize' in meta and len(frames) == 1 and row is not None:
        cell = tuple(meta['frameSize'])
    if cell is not None and len(frames) == 1:
        W, H = cell; sh = frames[0]
        nr, nc = sh.shape[0] // H, sh.shape[1] // W
        dirs = (meta or {}).get('directions') if isinstance(meta, dict) else None
        if row is None: row = 0
        if isinstance(row, str) and not row.lstrip('-').isdigit():
            if not dirs or row not in dirs: raise SystemExit(f'pxeval: row {row!r} not in sheet directions {dirs}')
            ri = dirs.index(row)
        else: ri = int(row)
        frames = [sh[ri * H:(ri + 1) * H, c * W:(c + 1) * W] for c in range(nc)]
        while frames and frames[-1][..., 3].max() == 0 and len(frames) > 1: frames.pop()  # empty trailing cells
        info.update(cell=[W, H], row=ri, row_name=(dirs[ri] if dirs and ri < len(dirs) else None), rows=nr)
        mf = (meta or {}).get('frames') if isinstance(meta, dict) else None
        durs = [fr.get('duration_ms') for fr in mf][:len(frames)] if mf else [None] * len(frames)
        if isinstance(meta, dict) and 'loop' in meta: info['loop'] = bool(meta['loop'])
    elif len(paths) > 1:
        info['files'] = len(paths)
    frames, k = unscale(frames, scale)
    info['scale_removed'] = k
    info['durations_ms'] = durs if any(d is not None for d in durs) else None
    info['n_frames'] = len(frames)
    info['size'] = [int(frames[0].shape[1]), int(frames[0].shape[0])]
    return frames, info


def fg_mask(rgba, mode='auto', bg=None):
    """foreground mask. auto: alpha if any pixel is not opaque, else the border's most common colour is background
    (exact match for <=256-colour images, tolerance 24 for rendered/AA images)."""
    a = rgba[..., 3]
    if mode == 'alpha' or (mode == 'auto' and bg is None and a.min() < 255):
        return a > 0, None
    rgb = rgba[..., :3].astype(int)
    if bg is None:
        if mode not in ('auto', 'alpha') and re.fullmatch(r'#?[0-9a-fA-F]{6}', mode): bg = parse_hex(mode)
        elif mode == 'white': bg = (255, 255, 255)
        else:
            b = np.concatenate([rgb[0], rgb[-1], rgb[:, 0], rgb[:, -1]])
            v, c = np.unique(b, axis=0, return_counts=True)
            bg = tuple(int(t) for t in v[c.argmax()])
    ncol = len(np.unique(rgb.reshape(-1, 3), axis=0))
    tol = 0 if ncol <= 256 else 24
    return (np.abs(rgb - np.array(bg)).max(-1) > tol) & (a > 0), bg


def index_frames(frames, masks):
    """common colour index over all frames: -1 = background; returns idx list, palette rgb (N,3)."""
    allc = np.concatenate([f[..., :3][m] for f, m in zip(frames, masks)] + [np.zeros((0, 3), np.uint8)])
    pal, inv = np.unique(allc.reshape(-1, 3), axis=0, return_inverse=True)
    out, o = [], 0
    for f, m in zip(frames, masks):
        idx = np.full(m.shape, -1, int)
        n = int(m.sum()); idx[m] = inv.ravel()[o:o + n]; o += n
        out.append(idx)
    return out, pal.astype(float)


def load_palette(path):
    """swordswoman {"colors": {K: {"hex"}|[hex,..]}}, snowpeak {"colors": [{"name","hex"}]}, sheet {"palette": [hex]},
    or a bare list. returns (names, rgb (N,3) float)."""
    j = json.load(open(path))
    c = j.get('colors', j.get('palette')) if isinstance(j, dict) else j
    names, cols = [], []
    if isinstance(c, dict):
        for k, v in c.items():
            hx = v['hex'] if isinstance(v, dict) else (v[0] if isinstance(v, list) else v)
            names.append(k); cols.append(parse_hex(hx))
    else:
        for i, v in enumerate(c):
            if isinstance(v, dict): names.append(v.get('name', str(i))); cols.append(parse_hex(v['hex']))
            else: names.append(str(i)); cols.append(parse_hex(v))
    return names, np.array(cols, float)


# ----------------------------------------------------------------------------------------------- pixel-art cleanliness
def orphan_count(idx):
    """pipeline/qa.py orphan_count: opaque pixels with no same-colour 8-neighbour (transparent pad)."""
    H, W = idx.shape
    pad = np.full((H + 2, W + 2), -9, int); pad[1:-1, 1:-1] = idx
    same = np.zeros((H, W), bool); diff4 = np.ones((H, W), bool)
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            if dy == 0 and dx == 0: continue
            eq = pad[1 + dy:H + 1 + dy, 1 + dx:W + 1 + dx] == idx
            same |= eq
            if dy == 0 or dx == 0: diff4 &= ~eq
    return int(((idx >= 0) & ~same).sum()), int(((idx >= 0) & diff4).sum())


def _extent_spikes(e):
    n = 0
    for k in range(1, len(e) - 1):
        if e[k - 1] is None or e[k] is None or e[k + 1] is None: continue
        if e[k - 1] == e[k + 1] and e[k] != e[k - 1]: n += 1
    return n


def jaggy_count(op):
    """pipeline/render.py jaggy_count: 1px bumps/notches on the outer silhouette extents (rows and columns)."""
    total = 0
    for m in (op, op.T):
        lo = [int(np.argmax(r)) if r.any() else None for r in m]
        hi = [int(len(r) - 1 - np.argmax(r[::-1])) if r.any() else None for r in m]
        total += _extent_spikes(lo) + _extent_spikes(hi)
    return total


def outline_index(pal_rgb, used, names=None, hexs=None):
    """the outline colour: --outline-hex, else palette entry 'K'/'outline', else darkest used colour."""
    if hexs:
        t = np.array(parse_hex(hexs), float)
        d = np.abs(pal_rgb - t).max(1)
        return int(d.argmin()) if d.min() == 0 else None
    if names is not None:
        for nm, rgb in names:
            if nm in ('K', 'outline'):
                d = np.abs(pal_rgb - rgb).max(1)
                if d.min() == 0 and d.argmin() in used: return int(d.argmin())
    if not used: return None
    L = rgb2lab(pal_rgb[list(used)])[:, 0]
    return int(list(used)[int(L.argmin())])


def cleanliness(idx, pal_rgb, pal=None, outline_hex=None):
    fg = idx >= 0
    used = sorted(set(np.unique(idx[fg]).tolist()))
    out = {'colours': len(used), 'figure_px': int(fg.sum())}
    if pal is not None:
        names, prgb = pal
        exact = np.array([np.abs(prgb - pal_rgb[u]).max(1).min() == 0 for u in used]) if used else np.zeros(0, bool)
        cnt = {u: int((idx == u).sum()) for u in used}
        out['off_palette_px'] = int(sum(cnt[u] for u, e in zip(used, exact) if not e))
        out['off_palette_colours'] = int((~exact).sum())
        if used:
            de = ciede2000(rgb2lab(pal_rgb[used])[:, None], rgb2lab(prgb)[None]).min(1)
            out['off_palette_px_dE3'] = int(sum(cnt[u] for u, d in zip(used, de) if d > 3))
        out['palette_size'] = len(prgb)
        nm = list(zip(names, prgb))
    else:
        nm = None
    o8, o4 = orphan_count(idx)
    out['orphans'] = o8; out['orphans4'] = o4
    out['jaggies'] = jaggy_count(fg)
    k = outline_index(pal_rgb, used, nm, outline_hex)
    if k is not None:
        dark = idx == k
        out['outline_hex'] = '#%02x%02x%02x' % tuple(int(v) for v in pal_rgb[k])
        p = np.pad(fg, 1)
        edge = fg & ~(p[:-2, 1:-1] & p[2:, 1:-1] & p[1:-1, :-2] & p[1:-1, 2:])
        out['outline_cov'] = float((edge & dark).sum() / max(1, edge.sum()))
        out['outline_gaps'] = int(nd.label(edge & ~dark, np.ones((3, 3)))[1])
        out['kcomp'] = int(nd.label(dark, np.ones((3, 3)))[1])
        dp = np.pad(dark, 1)
        U, D, Lf, R = dp[:-2, 1:-1], dp[2:, 1:-1], dp[1:-1, :-2], dp[1:-1, 2:]
        UL, UR, DL, DR = dp[:-2, :-2], dp[:-2, 2:], dp[2:, :-2], dp[2:, 2:]
        n8 = sum(a.astype(int) for a in (U, D, Lf, R, UL, UR, DL, DR))
        elbow = dark & (n8 == 2) & ((U & R) | (U & Lf) | (D & R) | (D & Lf))
        out['l_corners'] = int(elbow.sum())
        out['doubles_2x2'] = int((dark[:-1, :-1] & dark[1:, :-1] & dark[:-1, 1:] & dark[1:, 1:]).sum())
    else:
        dark = np.zeros_like(fg)
    # same-colour 4-connected clusters
    sizes = []
    for u in used:
        lab, n = nd.label(idx == u)
        if n: sizes += np.bincount(lab.ravel())[1:].tolist()
    sizes = np.array(sizes)
    out['clusters'] = int(len(sizes))
    out['clusters_1px'] = int((sizes == 1).sum()); out['clusters_le2px'] = int((sizes <= 2).sum())
    # banding: 1px-wide mid-tone step between two different, lightness-monotonic neighbours (non-outline)
    L = np.full(idx.shape, np.nan); L[fg] = rgb2lab(pal_rgb[idx[fg]])[:, 0]
    band = np.zeros_like(fg)
    for sa_, sc_ in (((slice(1, -1), slice(None, -2)), (slice(1, -1), slice(2, None))),
                     ((slice(None, -2), slice(1, -1)), (slice(2, None), slice(1, -1)))):
        a, b, c = idx[sa_], idx[1:-1, 1:-1], idx[sc_]
        la, lb, lc = L[sa_], L[1:-1, 1:-1], L[sc_]
        ok = (a >= 0) & (b >= 0) & (c >= 0) & (a != b) & (b != c) & (a != c) & ~dark[1:-1, 1:-1]
        if k is not None: ok &= (a != k) & (c != k)
        with np.errstate(invalid='ignore'):
            mono = ((la < lb) & (lb < lc)) | ((la > lb) & (lb > lc))
        band[1:-1, 1:-1] |= ok & mono
    inner = fg & ~dark
    out['banding_1px'] = float(band.sum() / max(1, inner.sum()))
    # pillow shading: lightness rising with distance from the silhouette edge (corr over interior pixels)
    dist = nd.distance_transform_cdt(np.pad(fg, 1), metric='taxicab')[1:-1, 1:-1]
    sel = inner & (dist >= 2)
    if sel.sum() > 20 and np.std(L[sel]) > 0 and np.std(dist[sel]) > 0:
        out['pillow_corr'] = float(np.corrcoef(L[sel], dist[sel])[0, 1])
    return out


# ------------------------------------------------------------------------------- illustration reference (metrics.py)
def _seg(x, m, y0, y1):
    """port of swordswoman/v2/final/tools/seg.py seg()"""
    r, g, b = x[..., 0], x[..., 1], x[..., 2]; mx = x.max(-1); mn = x.min(-1); sat = (mx - mn) / np.maximum(mx, 1)
    yy = (np.arange(x.shape[0])[:, None] - y0) / (y1 - y0) * np.ones(x.shape[:2])
    L = np.full(x.shape[:2], '', dtype='<U4'); L[m] = '?'
    K = m & (mx < 45); L[K] = 'K'
    red = m & ~K & (r > g * 1.6) & (r > 90) & (sat > 0.55) & (mx < 235); L[red] = 'red'
    skin = m & ~K & ~red & (r > 150) & (r > g) & (g > b * 0.95) & (sat < 0.5) & (sat > 0.15); L[skin] = 'skin'
    obi = m & ~K & ~red & ~skin & (b >= r * 0.95) & (mx > 80) & (mx < 235); L[obi] = 'obi'
    brown = m & ~K & ~red & ~skin & ~obi & (mx < 150)
    L[brown & (yy > 0.86)] = 'boot'; L[brown & (yy <= 0.86)] = 'hair'
    return L


SOCKS = (0.60, 0.86)


def _materials(x, m):
    L = _seg(x, m, 0, x.shape[0] - 1).astype('<U6')
    yy = np.arange(x.shape[0])[:, None] / max(1, x.shape[0] - 1) * np.ones(x.shape[:2])
    band = (yy > SOCKS[0]) & (yy <= SOCKS[1])
    L[(L == 'hair') & band] = 'socks'
    L[(L == 'K') & band & (x.max(-1) >= 30)] = 'socks'
    L[m & (x.min(-1) > 200) & (x.max(-1) - x.min(-1) < 40) & (L != 'obi')] = 'W'
    return L


def load_illus(path):
    """pzlib.load: figure-bbox crop, white bg, small enclosed holes filled. RGBA inputs with transparency use alpha."""
    im = Image.open(path).convert('RGBA'); a = np.array(im)
    x = a[..., :3].astype(float)
    if a[..., 3].min() < 255:
        m = a[..., 3] > 127
    else:
        m = (x.min(-1) < 215) | (x.max(-1) - x.min(-1) > 30)
    lab, n = nd.label(~m)
    if n:
        sizes = np.bincount(lab.ravel())[1:]
        border = set(np.unique(np.r_[lab[0], lab[-1], lab[:, 0], lab[:, -1]]).tolist())
        small = [i for i in range(1, n + 1) if i not in border and sizes[i - 1] < m.size * 0.0015]
        if small: m[np.isin(lab, small)] = True
    ys, xs = np.where(m)
    y0, y1, x0, x1 = ys.min(), ys.max(), xs.min(), xs.max()
    x = x[y0:y1 + 1, x0:x1 + 1].copy(); m = m[y0:y1 + 1, x0:x1 + 1]
    x[~m] = 255
    return x, m


def _box(x, w, h):
    a = np.clip(x, 0, 255).astype(np.uint8)
    return np.array(Image.fromarray(a).resize((w, h), Image.BOX)).astype(float)


MATS = ['K', 'hair', 'boot', 'socks', 'skin', 'red', 'obi', 'W', '?']
C2M = {'K': 'K', **{c: 'hair' for c in 'hHgL'}, **{c: 'skin' for c in 'sSmk'}, **{c: 'red' for c in 'ReE'},
       **{c: 'obi' for c in 'oOQ'}, 'D': 'socks', 'd': 'socks', 'W': 'W'}
_IC = {}


def illus_ref(path, h, w):
    key = (os.path.abspath(path), h, w)
    if key in _IC: return _IC[key]
    x, m = load_illus(path)
    L = _materials(x, m)
    Hh, Ww = m.shape
    ry = np.arange(Hh) * h // Hh; rx = np.arange(Ww) * w // Ww
    cell = (ry[:, None] * w + rx[None, :])
    cnt = np.stack([np.bincount(cell[L == mt], minlength=h * w).reshape(h, w) for mt in MATS]).astype(float)
    tot = np.bincount(cell.ravel(), minlength=h * w).reshape(h, w).astype(float)
    alpha = cnt.sum(0) > 0.5 * tot
    nk = cnt.copy(); nk[0] *= 0.35
    mat = np.array(MATS, dtype='<U6')[nk.argmax(0)]; mat[~alpha] = ''
    line = cnt[0] >= 0.18 * tot
    r = dict(x=x, m=m, L=L, lo=_box(x, w, h), alpha=alpha, mat=mat, line=line)
    _IC[key] = r
    return r


def _face_ssim(R, la, lb, pad, h, w):
    x, m, L = R['x'], R['m'], R['L']; Hh, Ww = m.shape
    sk = L == 'skin'; sk[int(Hh * 0.42):] = False
    hull = nd.binary_fill_holes(nd.binary_closing(sk, iterations=max(3, Ww // 60)))
    lab_, n_ = nd.label(hull)
    if n_:
        sz = nd.sum(hull, lab_, range(1, n_ + 1)); hull = lab_ == 1 + sz.argmax()
    if not hull.any(): return None
    hullg = _box(hull * 255., w, h) / 255. > 0.5
    if not hullg.any(): return None
    fy, fx = np.where(hullg); bb = (slice(fy.min(), fy.max() + 1), slice(fx.min(), fx.max() + 1))
    fl, fr = la[pad:pad + h, pad:pad + w, 0][bb], lb[pad:pad + h, pad:pad + w, 0][bb]
    ws = min(7, min(fl.shape)); ws -= (ws % 2 == 0)
    return ssim(fl, fr, 100, ws) if ws >= 3 else float('nan')


def vs_illus(rgba, fg, illus, pal=None, bbox=None, outline_k=None, save_grid=None):
    """metrics.py metrics() on a rendered sprite: region = figure bbox (h, w at ox, oy) padded 2, white bg."""
    if bbox is None:
        ys, xs = np.where(fg); bbox = (int(xs.min()), int(ys.min()), int(xs.max() - xs.min() + 1), int(ys.max() - ys.min() + 1))
    ox, oy, w, h = bbox
    pad = 2
    Hc, Wc = fg.shape
    P = np.full((h + 2 * pad, w + 2 * pad, 3), 255.); sa = np.zeros((h + 2 * pad, w + 2 * pad), bool)
    y0, x0 = oy - pad, ox - pad
    ys0, xs0 = max(0, y0), max(0, x0); ys1, xs1 = min(Hc, y0 + h + 2 * pad), min(Wc, x0 + w + 2 * pad)
    sub = (slice(ys0 - y0, ys1 - y0), slice(xs0 - x0, xs1 - x0))
    sa[sub] = fg[ys0:ys1, xs0:xs1]
    P[sub] = np.where(fg[ys0:ys1, xs0:xs1, None], rgba[ys0:ys1, xs0:xs1, :3].astype(float), 255.)
    R = illus_ref(illus, h, w)
    Rlo = np.full(P.shape, 255.); Rlo[pad:pad + h, pad:pad + w] = R['lo']
    ra = np.zeros(sa.shape, bool); ra[pad:pad + h, pad:pad + w] = R['alpha']
    rmat = np.full(sa.shape, '', dtype='<U6'); rmat[pad:pad + h, pad:pad + w] = R['mat']
    rline = np.zeros(sa.shape, bool); rline[pad:pad + h, pad:pad + w] = R['line']
    la, lb = rgb2lab(P), rgb2lab(Rlo)
    if save_grid:  # the reference the sprite is scored against, on the candidate's canvas (transparent outside alpha)
        g = np.zeros((Hc, Wc, 4), np.uint8)
        full = np.zeros((h + 2 * pad, w + 2 * pad, 4), np.uint8); full[..., :3] = Rlo.astype(np.uint8); full[..., 3] = ra * 255
        g[ys0:ys1, xs0:xs1] = full[sub]
        Image.fromarray(g, 'RGBA').save(save_grid)
    out = {'grid': [w, h], 'bbox_xywh': [ox, oy, w, h]}
    out['ssim'] = ssim(la[..., 0], lb[..., 0])
    out['ssim_b'] = ssim(nd.gaussian_filter(la[..., 0], 1), nd.gaussian_filter(lb[..., 0], 1))
    u = sa | ra
    out['dE'] = float(ciede2000(la[u], lb[u]).mean())
    out['sil'] = float((sa & ra).sum() / u.sum()); out['bloat'] = float(sa.sum() / max(1, ra.sum()))
    # char grid (swordswoman palette keys) -> per-material IoU + K line
    gp = None
    if pal is not None and all(len(n) == 1 for n in pal[0]):
        gp = np.full(sa.shape, '.', dtype='<U1')
        for nm, c in zip(*pal):
            gp[sa & (np.abs(P - c).max(-1) == 0)] = nm
        gp[sa & (gp == '.')] = '?'
        smat = np.vectorize(lambda c: C2M.get(c, '?' if c != '.' else ''))(gp).astype('<U6')
        rr = np.arange(gp.shape[0])[:, None] - pad
        smat[(smat == 'hair') & (rr > 0.86 * h)] = 'boot'
        smat[(smat == 'hair') & (rr > SOCKS[0] * h) & (rr <= SOCKS[1] * h)] = 'socks'
        for mt in ['hair', 'red', 'skin', 'obi', 'boot', 'socks']:
            a, b = smat == mt, rmat == mt
            out['iou_' + mt] = float((a & b).sum() / max(1, (a | b).sum()))
        sk = gp == 'K'
    elif outline_k is not None:
        sk = sa & (np.abs(P - outline_k).max(-1) == 0)
    else:
        sk = None
    if sk is not None:
        d1 = lambda b: nd.binary_dilation(b, np.ones((3, 3)))
        rec = (rline & d1(sk)).sum() / max(1, rline.sum()); pre = (sk & d1(rline)).sum() / max(1, sk.sum())
        out['line_f'] = float(2 * rec * pre / max(1e-6, rec + pre))
        out['kcomp'] = int(nd.label(sk, np.ones((3, 3)))[1])
    # orphans exactly as metrics.py (region interior; same-colour 8-neighbour count == 1)
    cid = np.full(sa.shape, -1, int)
    if sa.any():
        _, inv = np.unique(P[sa].reshape(-1, 3), axis=0, return_inverse=True); cid[sa] = inv.ravel()
    orph = 0
    Hh, Ww = cid.shape
    same = np.zeros((Hh - 2, Ww - 2), int)
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            same += cid[1 + dy:Hh - 1 + dy, 1 + dx:Ww - 1 + dx] == cid[1:-1, 1:-1]
    orph = int(((cid[1:-1, 1:-1] >= 0) & (same == 1)).sum())
    out['orph'] = orph
    try:
        out['face_ssim'] = _face_ssim(R, la, lb, pad, h, w)
    except ValueError:
        out['face_ssim'] = None
    return out


# ------------------------------------------------------------------------------------------------ sprite vs sprite
def _bbox(m):
    ys, xs = np.where(m)
    if len(ys) == 0: return None
    return int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())


def sil_stats(m):
    b = _bbox(m)
    if b is None: return None
    ys, xs = np.where(m)
    return {'area': int(m.sum()), 'cx': float(xs.mean()), 'cy': float(ys.mean()), 'top': b[1], 'feet': b[3],
            'left': b[0], 'right': b[2], 'height': b[3] - b[1] + 1, 'width': b[2] - b[0] + 1}


def vs_ref(ca, cm, ra, rm, align='auto'):
    """candidate vs reference sprite on a common canvas. align: cell (same canvas coords) | feet (bbox bottom-centre)."""
    if align == 'auto': align = 'cell' if ca.shape == ra.shape else 'feet'
    cb, rb = _bbox(cm), _bbox(rm)
    dx = dy = 0
    if align == 'feet':
        dx = int(round((rb[0] + rb[2]) / 2 - (cb[0] + cb[2]) / 2)); dy = rb[3] - cb[3]
    H = max(ra.shape[0], ca.shape[0] + abs(dy)) + 8; W = max(ra.shape[1], ca.shape[1] + abs(dx)) + 8
    oy, ox = 4 + max(0, -dy), 4 + max(0, -dx)

    def put(img, m, sy, sx):
        P = np.full((H, W, 3), 255.); M = np.zeros((H, W), bool)
        P[sy:sy + img.shape[0], sx:sx + img.shape[1]] = np.where(m[..., None], img[..., :3].astype(float), 255.)
        M[sy:sy + img.shape[0], sx:sx + img.shape[1]] = m
        return P, M
    Pr, Mr = put(ra, rm, oy, ox)
    Pc, Mc = put(ca, cm, oy + dy, ox + dx)
    u = Mr | Mc
    x0, y0, x1, y1 = _bbox(u)
    sl = (slice(max(0, y0 - 2), y1 + 3), slice(max(0, x0 - 2), x1 + 3))
    Pr, Mr, Pc, Mc = Pr[sl], Mr[sl], Pc[sl], Mc[sl]; u = Mr | Mc
    la, lb = rgb2lab(Pc), rgb2lab(Pr)
    sc, sr = sil_stats(Mc), sil_stats(Mr)
    same = (np.abs(Pc - Pr).max(-1) == 0) & u
    out = {'align': align, 'shift_applied': [dx, dy],
           'ssim': ssim(la[..., 0], lb[..., 0]),
           'ssim_b': ssim(nd.gaussian_filter(la[..., 0], 1), nd.gaussian_filter(lb[..., 0], 1)),
           'dE': float(ciede2000(la[u], lb[u]).mean()),
           'sil': float((Mr & Mc).sum() / u.sum()), 'bloat': float(Mc.sum() / max(1, Mr.sum())),
           'same_px': float(same.sum() / u.sum()),
           'height_delta': sc['height'] - sr['height'], 'width_delta': sc['width'] - sr['width'],
           'centroid_offset': [sc['cx'] - sr['cx'], sc['cy'] - sr['cy']], 'feet_delta': sc['feet'] - sr['feet']}
    # area-weighted per-colour IoU (reference colours)
    inter = 0; tot = 0
    cols = np.unique(Pr[Mr].reshape(-1, 3), axis=0)
    for c in cols:
        a = Mr & (np.abs(Pr - c).max(-1) == 0); b = Mc & (np.abs(Pc - c).max(-1) == 0)
        inter += (a & b).sum(); tot += (a | b).sum()
    out['colour_iou'] = float(inter / max(1, tot))
    return out


# ---------------------------------------------------------------------------------------------------------- still
def load_still(path, frame=0, mask_bg='auto', scale='auto'):
    frames, info = load_frames(path, scale=scale)
    f = frames[min(frame, len(frames) - 1)]
    m, bg = fg_mask(f, mask_bg)
    return f, m, info, bg


def cmd_still(a):
    ca, cm, cinfo, cbg = load_still(a.candidate, a.frame, a.mask_bg, a.unscale)
    pal = load_palette(a.pal) if a.pal else None
    idx, prgb = index_frames([ca], [cm])
    res = {'pxeval': VERSION, 'cmd': 'still', 'candidate': a.candidate, 'size': [int(ca.shape[1]), int(ca.shape[0])],
           'scale_removed': cinfo['scale_removed'], 'bg': (None if cbg is None else '#%02x%02x%02x' % cbg)}
    res['silhouette'] = sil_stats(cm)
    res['clean'] = cleanliness(idx[0], prgb, pal, a.outline_hex)
    if a.ref:
        ra, rm, _, _ = load_still(a.ref, a.frame, a.mask_bg, a.unscale)
        res['ref'] = a.ref
        res['vs_ref'] = vs_ref(ca, cm, ra, rm, a.align)
    if a.illus:
        bbox = None; src = 'alpha'
        js = os.path.splitext(a.candidate)[0] + '.json'
        if a.meta != 'none' and cinfo['scale_removed'] == 1:
            mp = a.meta if a.meta not in ('auto', None) else (js if os.path.exists(js) else None)
            if mp:
                try:
                    mj = json.load(open(mp))
                    if all(k in mj for k in ('h', 'w', 'ox', 'oy')): bbox = (mj['ox'], mj['oy'], mj['w'], mj['h']); src = 'meta:' + os.path.basename(mp)
                except Exception: pass
        ok = res['clean'].get('outline_hex')
        res['illus'] = a.illus
        res['vs_illus'] = vs_illus(ca, cm, a.illus, pal, bbox, None if ok is None else np.array(parse_hex(ok), float), a.save_illus_grid)
        res['vs_illus']['bbox_source'] = src
    return res


# ------------------------------------------------------------------------------------------------------------ seq
def _shift(a, dy, dx, fill=-1):
    out = np.full_like(a, fill)
    H, W = a.shape
    ys, yd = (slice(0, H - dy), slice(dy, H)) if dy >= 0 else (slice(-dy, H), slice(0, H + dy))
    xs, xd = (slice(0, W - dx), slice(dx, W)) if dx >= 0 else (slice(-dx, W), slice(0, W + dx))
    out[yd, xd] = a[ys, xs]
    return out


def motion_comp(prev, cur, R=2, win=5):
    """per-pixel best local translation (|d|<=R) of a win x win patch from prev to cur. returns (mismatch at best
    shift, |shift|, shift id, patch-rigid) - mismatching pixels after compensation = changes not explained by coherent
    motion; patch-rigid = the whole win x win patch matches exactly under the best shift."""
    best_cost = best_mis = best_mag = best_id = None
    k = 0
    for dy in range(-R, R + 1):
        for dx in range(-R, R + 1):
            s = _shift(prev, dy, dx)
            mis = (s != cur)
            raw = nd.uniform_filter(mis.astype(float), win, mode='constant')
            cost = raw + 1e-4 * (abs(dy) + abs(dx))
            if best_cost is None:
                best_cost, best_mis, best_raw = cost, mis, raw
                best_mag = np.full(cur.shape, math.hypot(dy, dx)); best_id = np.full(cur.shape, k)
            else:
                b = cost < best_cost
                best_cost = np.where(b, cost, best_cost); best_mis = np.where(b, mis, best_mis)
                best_raw = np.where(b, raw, best_raw)
                best_mag = np.where(b, math.hypot(dy, dx), best_mag); best_id = np.where(b, k, best_id)
            k += 1
    return best_mis, best_mag, best_id, best_raw < 0.5 / (win * win)


def seq_metrics(frames, info, mask_bg='auto', moving=None, loop=None):
    masks, bg = [], None
    m0, bg = fg_mask(frames[0], mask_bg)
    masks = [m0] + [fg_mask(f, mask_bg, bg)[0] for f in frames[1:]]
    idx, prgb = index_frames(frames, masks)
    lab = rgb2lab(prgb) if len(prgb) else np.zeros((0, 3))
    n = len(idx)
    if loop is None: loop = info.get('loop', True)
    st = [sil_stats(m) for m in masks]
    if any(s is None for s in st): raise SystemExit('pxeval seq: empty frame')
    area = np.array([s['area'] for s in st], float); A = area.mean()
    pairs = [(t, t + 1) for t in range(n - 1)]
    per = []
    for t, u in pairs + [(n - 1, 0)]:
        a, b = idx[t], idx[u]
        U = (a >= 0) | (b >= 0)
        ch = (a != b) & U
        mis, mag, sid, _ = motion_comp(a, b)
        resid = mis & ch
        coh = ch & ~resid
        dom = np.bincount(sid[coh]).argmax() if coh.any() else -1
        both = (a >= 0) & (b >= 0) & ch
        swap = both & resid
        if swap.any():
            de = ciede2000(lab[a[swap]], lab[b[swap]])
            near = np.zeros_like(swap); near[swap] = de < 12
        else:
            near = swap
        rec = {'pair': [t, u], 'changed': float(ch.sum() / U.sum()), 'resid': float(resid.sum() / U.sum()),
               'motion_px': float((mag * coh).sum() / A), 'articulation': float((coh & (sid != dom)).sum() / A),
               'moving': float(coh.sum() / A),
               'sil_xor': float(((a >= 0) ^ (b >= 0)).sum() / U.sum()), 'shade_swap': float(near.sum() / U.sum()),
               'identical': bool(not ch.any())}
        if moving is not None:
            out = ~moving
            rec['static_changed'] = float((ch & out).sum() / max(1, (U & out).sum()))
        per.append((rec, resid))
    seam = per[-1][0]; per_pairs = per[:-1] if not loop else per
    # flicker: a pixel changes at t and reverts to its t-1 value within 2 frames (includes blinks / 2-key oscillation).
    # boil: a change at t that no local shift explains, on a patch that is rigid (exactly shift-matched) between t-1
    # and t+1 (or t+2) - i.e. the region did not really move/deform, the in-between frame was just redrawn noisily.
    T = range(n) if loop else range(1, n - 1)
    fl = bo = 0; cnt = 0; boil_map = [np.zeros(idx[0].shape, bool) for _ in range(n)]
    resid_of = {tuple(r['pair']): m for r, m in per}
    for t in T:
        p, c = idx[(t - 1) % n], idx[t]
        nx1 = idx[(t + 1) % n]
        ch = (p != c) & ((p >= 0) | (c >= 0))
        rev = ch & (nx1 == p)
        rigid = motion_comp(p, nx1)[3]
        if loop or t + 2 < n:
            nx2 = idx[(t + 2) % n]
            rev |= ch & (nx1 != p) & (nx2 == p)
            rigid = rigid | motion_comp(p, nx2)[3]
        rm = resid_of.get(((t - 1) % n, t))
        if rm is None: rm = motion_comp(p, c)[0] & ch
        b = rm & rigid
        fl += rev.sum(); bo += b.sum(); cnt += 1
        boil_map[t] = b
    agg = lambda k: [r[k] for r, _ in per_pairs]
    mean = lambda v: float(np.mean(v)) if len(v) else 0.0
    ious = []
    for i in range(n):
        for j in range(i + 1, n):
            ious.append(((masks[i] & masks[j]).sum() / max(1, (masks[i] | masks[j]).sum())))
    # head track: centroid of the top 25% (of the median figure height) rows of each frame
    hmed = np.median([s['height'] for s in st])
    heads = []
    for m, s in zip(masks, st):
        sub = m.copy(); sub[int(s['top'] + 0.25 * hmed):] = False
        ys, xs = np.where(sub); heads.append((xs.mean(), ys.mean()))
    heads = np.array(heads); cent = np.array([(s['cx'], s['cy']) for s in st])

    def jerk(p):
        if n < 3: return 0.0
        q = np.concatenate([p[-1:], p, p[:1]]) if loop else p
        d2 = q[2:] - 2 * q[1:-1] + q[:-2]
        return float(np.hypot(d2[:, 0], d2[:, 1]).mean())
    sd = lambda k: float(np.std([s[k] for s in st]))
    rg = lambda k: float(max(s[k] for s in st) - min(s[k] for s in st))
    res = {
        'n_frames': n, 'loop': bool(loop), 'figure_px_mean': float(A), 'colours': int(len(prgb)),
        'durations_ms': info.get('durations_ms'),
        'changed_mean': mean(agg('changed')), 'changed_max': float(max(agg('changed') or [0])),
        'resid_mean': mean(agg('resid')),
        'flicker': float(fl / max(1, cnt) / A), 'boil': float(bo / max(1, cnt) / A),
        'shade_swap': mean(agg('shade_swap')),
        'motion_px': mean(agg('motion_px')), 'articulation': mean(agg('articulation')),
        'rigid_share': float(1 - mean(agg('articulation')) / max(1e-9, mean(agg('moving')))) if mean(agg('moving')) > 0 else None,
        'sil_change': mean(agg('sil_xor')),
        'pose_range': float(1 - min(ious)) if ious else 0.0,
        'holds': int(sum(r['identical'] for r, _ in per[:-1])),
        'area_cv': float(area.std() / A), 'centroid_std': [sd('cx'), sd('cy')],
        'feet_range': rg('feet'), 'top_range': rg('top'), 'height_range': rg('height'), 'width_range': rg('width'),
        'head_range': [float(np.ptp(heads[:, 0])), float(np.ptp(heads[:, 1]))],
        'head_jerk': jerk(heads), 'centroid_jerk': jerk(cent),
        'seam_changed': seam['changed'], 'seam_resid': seam['resid'],
        'seam_ratio': float(seam['changed'] / max(1e-9, max([r['changed'] for r, _ in per[:-1]]))) if n > 2 else None,
    }
    durs = info.get('durations_ms')
    if durs and all(d for d in durs[:n]):
        cyc = sum(durs[:n]) / 1000.0
        res['cycle_ms'] = int(sum(durs[:n]))
        res['articulation_per_s'] = float(sum(agg('articulation')) / cyc); res['motion_px_per_s'] = float(sum(agg('motion_px')) / cyc)
    if moving is not None:
        res['static_changed'] = mean(agg('static_changed'))
    res['flags'] = flags(res)
    res['pairs'] = [r for r, _ in per]
    res['frames'] = st
    return res, idx, masks, boil_map, per


THRESH = {  # proposed gates (NOTES.md "Proposed thresholds"); calibrated on the 2026-10-28 back-test
    'boil_max': 0.02,           # shipped snowpeak walk/run/idle <= .017; rejected pilot walk .031; 3D-render guides .06-.18
    'shade_swap_max': 0.015,    # snowpeak <= .013; pilot walk .030
    'stiff_articulation': 0.03, # per transition, used when frame durations are unknown
    'stiff_articulation_per_s': 0.15,  # pilot idle 0.10/s (GIF and 1x strip agree; critics: "virtually zero motion"),
                                       # snowpeak idles 0.01-0.06/s, unarmed idle 0.39/s, snowpeak walk/run >= 0.5/s
    'frozen_motion_px': 0.02, 'frozen_articulation': 0.005,
    'feet_range_max': 2,        # px; snowpeak walk 1, run 2 (flight phase); not meaningful for jump/dash/hurt
    'seam_ratio_max': 1.5}      # loop-seam change vs the largest in-cycle step


def flags(r):
    f = []
    if r['motion_px'] < THRESH['frozen_motion_px'] and r['articulation'] < THRESH['frozen_articulation']: f.append('FROZEN')
    elif (r['articulation_per_s'] < THRESH['stiff_articulation_per_s']) if r.get('articulation_per_s') is not None \
            else (r['articulation'] < THRESH['stiff_articulation']): f.append('STIFF')
    if r['boil'] > THRESH['boil_max']: f.append('BOILING')
    if r['shade_swap'] > THRESH['shade_swap_max']: f.append('SHADE_SWAP')
    if r['feet_range'] > THRESH['feet_range_max']: f.append('FEET_JITTER')
    if r['loop'] and r['seam_ratio'] is not None and r['seam_ratio'] > THRESH['seam_ratio_max']: f.append('SEAM')
    return f


def _composite(f, bg):
    out = np.empty(f.shape[:2] + (3,), np.uint8); out[:] = bg
    a = f[..., 3:4].astype(float) / 255.
    return (f[..., :3] * a + out * (1 - a)).astype(np.uint8)


def seq_viz(path, frames, idx, per, boil_map, s=3, bg=(128, 128, 128)):
    """row 1: frames; row 2: changes vs previous frame (cyan = explained by motion, red = not explained, magenta = boil)."""
    n = len(frames); H, W = frames[0].shape[:2]
    can = Image.new('RGB', (n * (W * s + 4) + 4, 2 * (H * s + 4) + 4), (40, 40, 40))
    for t in range(n):
        img = _composite(frames[t], bg)
        can.paste(Image.fromarray(img).resize((W * s, H * s), Image.NEAREST), (4 + t * (W * s + 4), 4))
        p = (t - 1) % n
        rec, resid = [(r, m) for r, m in per if r['pair'] == [p, t]][0] if any(r['pair'] == [p, t] for r, _ in per) else (None, None)
        g = (0.35 * img + 0.65 * 60).astype(np.uint8)
        if rec is not None:
            ch = (idx[p] != idx[t]) & ((idx[p] >= 0) | (idx[t] >= 0))
            g[ch & ~resid] = (0, 200, 220); g[resid] = (230, 40, 40)
        g[boil_map[t]] = (255, 0, 255)
        can.paste(Image.fromarray(g).resize((W * s, H * s), Image.NEAREST), (4 + t * (W * s + 4), 8 + H * s))
    can.save(path)


def cmd_seq(a):
    cell = tuple(a.cell) if a.cell else None
    rows = [a.row]
    if a.row == 'all':
        frames, info = load_frames(a.source, cell, 0, a.unscale)
        rows = list(range(info.get('rows', 1)))
    out = {'pxeval': VERSION, 'cmd': 'seq', 'source': a.source, 'rows': []}
    moving = None
    for r in rows:
        frames, info = load_frames(a.source, cell, r, a.unscale)
        if a.ms: info['durations_ms'] = (a.ms * len(frames))[:len(frames)] if len(a.ms) == 1 else a.ms[:len(frames)]
        if a.mask:
            mm = np.array(Image.open(a.mask).convert('RGBA'))
            moving = (mm[..., 3] > 0) & (mm[..., :3].max(-1) > 127)
            if moving.shape != frames[0].shape[:2]:
                moving = np.array(Image.fromarray(moving.astype(np.uint8) * 255).resize(frames[0].shape[1::-1], Image.NEAREST)) > 0
        loop = None if a.loop == 'auto' else a.loop == 'yes'
        res, idx, masks, boil_map, per = seq_metrics(frames, info, a.mask_bg, moving, loop)
        res = {**{k: info.get(k) for k in ('row', 'row_name', 'cell', 'scale_removed', 'size')}, **res}
        if a.viz:
            vp = a.viz if len(rows) == 1 else re.sub(r'(\.png)?$', f'_r{r}.png', a.viz, count=1)
            seq_viz(vp, frames, idx, per, boil_map, a.viz_scale); res['viz'] = vp
        if not a.full: res.pop('frames'); res.pop('pairs')
        out['rows'].append(res)
    if len(out['rows']) == 1:
        out.update(out.pop('rows')[0])
    else:
        keys = ['changed_mean', 'resid_mean', 'flicker', 'boil', 'shade_swap', 'motion_px', 'pose_range', 'feet_range', 'height_range', 'seam_ratio']
        out['summary'] = {k: {'mean': float(np.mean([x[k] for x in out['rows'] if x[k] is not None])),
                              'max': float(np.max([x[k] for x in out['rows'] if x[k] is not None]))} for k in keys}
        out['summary']['flags'] = sorted({f for x in out['rows'] for f in x['flags']})
    return out


# ---------------------------------------------------------------------------------------------------- board / gif
def _font(sz=12):
    try: return ImageFont.load_default(size=sz)
    except TypeError: return ImageFont.load_default()


def _strip(spec, a):
    """one board item: image / GIF / dir / sheet. 'sheet.png@48x64' or 'sheet.png@48x64rSE' = cell size + row."""
    cell = tuple(a.cell) if getattr(a, 'cell', None) else None
    row = a.sheet_row
    m = re.search(r'@(\d+)x(\d+)(?:r(\w+))?$', spec)
    if m:
        spec = spec[:m.start()]; cell = (int(m.group(1)), int(m.group(2))); row = m.group(3) or 0
    frames, info = load_frames(spec, cell, row if cell else None, a.unscale)
    frames = frames[:a.max_frames]
    H = max(f.shape[0] for f in frames); W = sum(f.shape[1] for f in frames) + 2 * (len(frames) - 1)
    can = np.zeros((H, W, 4), np.uint8); x = 0
    for f in frames:
        can[H - f.shape[0]:, x:x + f.shape[1]] = f; x += f.shape[1] + 2
    return can


def cmd_board(a):
    bg = parse_hex(a.bg); s = a.scale; font = _font(13); pad = 8
    rows = []
    for spec in a.row:
        label, _, imgs = spec.partition(':') if ':' in spec else ('', '', spec)
        rows.append((label, [_strip(p, a) for p in imgs.split(',') if p]))
    labw = max([int(ImageDraw.Draw(Image.new('RGB', (1, 1))).textlength(l, font=font)) for l, _ in rows] + [0]) + 2 * pad
    blocks = []
    for label, ims in rows:
        w = sum(i.shape[1] * (1 + s) + 3 * pad for i in ims); h = max(i.shape[0] * s for i in ims)
        blocks.append((label, ims, w, h))
    th = 24 if a.title else 0
    W = labw + max(b[2] for b in blocks) + pad; Hh = th + sum(b[3] + 2 * pad for b in blocks) + pad
    can = Image.new('RGB', (W, Hh), bg); d = ImageDraw.Draw(can)
    if a.title: d.text((pad, 6), a.title, fill=(255, 255, 255), font=font)
    y = th + pad
    for label, ims, w, h in blocks:
        d.text((pad, y + h // 2 - 7), label, fill=(255, 255, 255), font=font)
        x = labw
        for im in ims:
            c = Image.fromarray(_composite(im, bg))
            can.paste(c, (x, y + h - im.shape[0])); x += im.shape[1] + pad
            can.paste(c.resize((im.shape[1] * s, im.shape[0] * s), Image.NEAREST), (x, y + h - im.shape[0] * s))
            x += im.shape[1] * s + 2 * pad
        y += h + 2 * pad
    can.save(a.out)
    return {'pxeval': VERSION, 'cmd': 'board', 'out': a.out, 'size': list(can.size), 'rows': len(rows)}


def cmd_gif(a):
    frames = []
    cell = tuple(a.cell) if a.cell else None
    for spec in a.frames:
        f, _ = load_frames(spec, cell, a.sheet_row if cell else None, a.unscale); frames += f
    H = max(f.shape[0] for f in frames); W = max(f.shape[1] for f in frames)
    bg = parse_hex(a.bg)
    ims = []
    for f in frames:
        c = np.empty((H, W, 4), np.uint8); c[:] = (0, 0, 0, 0); c[H - f.shape[0]:, :f.shape[1]] = f
        ims.append(Image.fromarray(_composite(c, bg)).resize((W * a.scale, H * a.scale), Image.NEAREST))
    allc = np.unique(np.concatenate([np.array(i).reshape(-1, 3) for i in ims]), axis=0)
    if len(allc) <= 256:
        pal = Image.new('P', (1, 1)); flat = allc.ravel().tolist(); pal.putpalette(flat + [0] * (768 - len(flat)))
        ims = [i.quantize(palette=pal, dither=Image.Dither.NONE) for i in ims]
    ims[0].save(a.out, save_all=True, append_images=ims[1:], duration=a.ms, loop=0, disposal=1, optimize=False)
    return {'pxeval': VERSION, 'cmd': 'gif', 'out': a.out, 'frames': len(ims), 'size': [W * a.scale, H * a.scale],
            'exact_palette': bool(len(allc) <= 256)}


# ------------------------------------------------------------------------------------------------------------ CLI
def main(argv=None):
    ap = argparse.ArgumentParser(prog='pxeval', description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest='cmd', required=True)

    def common(p):
        p.add_argument('--mask-bg', default='auto', help='auto | alpha | white | RRGGBB (background for opaque images)')
        p.add_argument('--unscale', default='auto', help='auto | 1 | N: undo integer nearest upscaling (GIF previews)')
        p.add_argument('--json', help='also write the JSON result here')
        p.add_argument('--compact', action='store_true', help='one-line JSON')
    s = sub.add_parser('still', help='fidelity + pixel-art cleanliness of one sprite')
    s.add_argument('candidate'); s.add_argument('--ref'); s.add_argument('--illus'); s.add_argument('--pal')
    s.add_argument('--align', default='auto', choices=['auto', 'cell', 'feet'])
    s.add_argument('--meta', default='auto', help="auto: use CANDIDATE.json {h,w,ox,oy} for the --illus grid (metrics.py); none: alpha bbox")
    s.add_argument('--outline-hex'); s.add_argument('--frame', type=int, default=0)
    s.add_argument('--save-illus-grid', help='write the area-downsampled illustration (the --illus reference) as PNG')
    common(s)
    q = sub.add_parser('seq', help='temporal stability / motion of a frame sequence')
    q.add_argument('source', help='GIF, directory of PNGs, glob, or sprite sheet (with --cell or a sibling .json)')
    q.add_argument('--cell', type=int, nargs=2, metavar=('W', 'H')); q.add_argument('--row', default=None, help='sheet row index, direction name, or all')
    q.add_argument('--mask', help='PNG, white = region allowed to move; reports static_changed outside it')
    q.add_argument('--loop', default='auto', choices=['auto', 'yes', 'no'])
    q.add_argument('--ms', type=int, nargs='+', help='frame durations (one value or one per frame); overrides GIF/sheet timing')
    q.add_argument('--viz', help='write a frames + change-map PNG'); q.add_argument('--viz-scale', type=int, default=3)
    q.add_argument('--full', action='store_true', help='include per-pair and per-frame records')
    common(q)
    b = sub.add_parser('board', help='labelled side-by-side board at 1x + Nx nearest')
    b.add_argument('out'); b.add_argument('--row', action='append', required=True, help='"label:img1.png,img2.gif" (repeat)')
    b.add_argument('--scale', type=int, default=4); b.add_argument('--bg', default='808080'); b.add_argument('--title')
    b.add_argument('--cell', type=int, nargs=2); b.add_argument('--sheet-row', default=0); b.add_argument('--max-frames', type=int, default=12)
    common(b)
    g = sub.add_parser('gif', help='frames -> nearest-upscaled GIF')
    g.add_argument('out'); g.add_argument('frames', nargs='+'); g.add_argument('--scale', type=int, default=4)
    g.add_argument('--ms', type=int, default=100); g.add_argument('--bg', default='808080')
    g.add_argument('--cell', type=int, nargs=2); g.add_argument('--sheet-row', default=0)
    common(g)
    a = ap.parse_args(argv)
    if a.cmd == 'seq' and a.row is None and a.cell: a.row = '0'
    if a.cmd == 'seq' and a.row is None and a.source.lower().endswith('.png') and os.path.isfile(a.source) \
            and os.path.exists(os.path.splitext(a.source)[0] + '.json'):
        try:
            if 'frameSize' in json.load(open(os.path.splitext(a.source)[0] + '.json')): a.row = '0'
        except Exception: pass
    res = {'still': cmd_still, 'seq': cmd_seq, 'board': cmd_board, 'gif': cmd_gif}[a.cmd](a)
    res = rnd(res)
    txt = json.dumps(res, separators=(',', ':')) if a.compact else json.dumps(res, indent=1)
    if a.json:
        os.makedirs(os.path.dirname(os.path.abspath(a.json)), exist_ok=True)
        open(a.json, 'w').write(txt + '\n')
    print(txt)
    return res


if __name__ == '__main__':
    main()
