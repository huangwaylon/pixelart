"""gemsnap.py: Gemini 'pixel art' -> grid detection + per-cell mode -> low-res RGB with figure bbox exactly h tall.
gemlow(path, h) -> (lo RGB float (h,w,3), alpha (h,w), w). CLI: gemsnap.py img.png  (prints detected grid)"""
import sys, os, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pzlib as Z
from PIL import Image


def period(prof, lo=2, hi=48):
    """autocorrelation peak of the edge profile -> (period, phase, score)"""
    q = prof - prof.mean()
    ac = np.array([(q[:-k] * q[k:]).mean() for k in range(1, hi + 1)]) / max(1e-9, (q * q).mean())
    cand = [k for k in range(lo, hi) if ac[k - 1] >= ac[k - 2] and ac[k - 1] >= ac[k]]
    if not cand: return 1, 0, 0.0
    mx = max(ac[k - 1] for k in cand)
    p = min(k for k in cand if ac[k - 1] >= 0.75 * mx)
    f = max(range(p), key=lambda f: prof[f::p].mean())
    return p, f, float(ac[p - 1])


def grid(x, m):
    g = x @ np.array([.299, .587, .114])
    dx = np.abs(np.diff(g, axis=1))[m[:, 1:]].sum() if False else (np.abs(np.diff(g, axis=1)) * m[:, 1:]).sum(0)
    dy = (np.abs(np.diff(g, axis=0)) * m[1:, :]).sum(1)
    px, fx, sx = period(dx); py, fy, sy = period(dy)
    return px, fx + 1, py, fy + 1, sx, sy


def mode_cells(x, p, fx, py, fy):
    H, W = x.shape[:2]
    q = (x // 8).astype(int); code = q[..., 0] * 1024 + q[..., 1] * 32 + q[..., 2]
    ys = list(range(fy % py - py if fy % py else 0, H, py)); xs = list(range(fx % p - p if fx % p else 0, W, p))
    out = np.full((len(ys), len(xs), 3), 255.)
    for i, y in enumerate(ys):
        for j, xx in enumerate(xs):
            c = code[max(0, y):y + py, max(0, xx):xx + p].ravel()
            if len(c) == 0: continue
            v, n = np.unique(c, return_counts=True); best = v[n.argmax()]
            sel = code[max(0, y):y + py, max(0, xx):xx + p] == best
            out[i, j] = x[max(0, y):y + py, max(0, xx):xx + p][sel].mean(0)
    return out


def gemlow(path, h):
    x = np.array(Image.open(path).convert('RGB')).astype(float)
    m = Z.fgmask(x)
    px, fx, py, fy, sx, sy = grid(x, m)
    nat = mode_cells(x, px, fx, py, fy)
    na = Z.fgmask(nat)
    ys, xs = np.where(na); nat = nat[ys.min():ys.max() + 1, xs.min():xs.max() + 1]; na = na[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    hn, wn = na.shape
    w = max(1, round(wn * h / hn))
    if abs(hn - h) / h < 0.12:
        lo = Z.resize(nat, w, h, Image.NEAREST); al = Z.resize(na * 255., w, h, Image.NEAREST) > 127
        how = 'native-grid'
    else:  # native grid far from target: k-centroid of the snapped native image at target size
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from pz import kcentroid, P
        hi = Z.resize(nat, w * P, h * P, Image.NEAREST)
        lo = kcentroid(hi, 3, line=False, prefilter=False); al = Z.fgmask(lo)
        how = 'kcentroid-of-native'
    print(f'gemsnap {os.path.basename(path)}: grid {px}x{py} (score {sx:.2f}/{sy:.2f}) native fig {hn}px -> {h} via {how}', file=sys.stderr)
    return lo, al, w


if __name__ == '__main__':
    for p in sys.argv[1:]:
        x = np.array(Image.open(p).convert('RGB')).astype(float); m = Z.fgmask(x)
        px, fx, py, fy, sx, sy = grid(x, m); ys = np.where(m.any(1))[0]
        print(os.path.basename(p), 'grid', px, py, 'scores %.2f %.2f' % (sx, sy), 'native fig h ~', (ys.max() - ys.min() + 1) / py)
