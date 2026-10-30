"""Vector outline (copied from docs/team_review/2026-10-30/line_art/proto_vecline.py and generalised to any cell size N and
supersample factor P).  Trace the hi-res silhouette, smooth it along the curve, pin sharp corners, Douglas-Peucker, redraw
each segment with uniform clean-slope runs (1:k / k:1), make the path pixel-perfect.  Returns (line, inside) at 1x."""
import numpy as np, cv2
from scipy import ndimage as nd


def bres(p0, p1):
    (y0, x0), (y1, x1) = p0, p1
    dy, dx = abs(y1 - y0), abs(x1 - x0); sy = 1 if y1 > y0 else -1; sx = 1 if x1 > x0 else -1
    err = dx - dy; pts = []
    while True:
        pts.append((y0, x0))
        if (y0, x0) == (y1, x1): break
        e2 = 2 * err
        if e2 > -dy: err -= dy; x0 += sx
        if e2 < dx: err += dx; y0 += sy
    return pts


def clean_seg(p0, p1, tol=0.25):
    (y0, x0), (y1, x1) = p0, p1
    dy, dx = y1 - y0, x1 - x0
    ady, adx = abs(dy), abs(dx)
    if ady == 0 or adx == 0: return bres(p0, p1)
    sy, sx = (1 if dy > 0 else -1), (1 if dx > 0 else -1)
    long_, short = max(ady, adx), min(ady, adx)
    r = long_ / short; k = max(1, int(round(r)))
    if abs(r - k) / r > tol: return bres(p0, p1)
    pts = [(y0, x0)]; y, x = y0, x0
    for i in range(short):
        for j in range(k):
            if adx >= ady:
                x += sx
                if j == 0: y += sy
            else:
                y += sy
                if j == 0: x += sx
            pts.append((y, x))
    return pts


def pixel_perfect(path):
    out = []
    for p in path:
        if not out or out[-1] != p: out.append(p)
    changed = True
    while changed and len(out) > 4:
        changed = False
        n = len(out); keep = [True] * n
        for i in range(n):
            a, b, c = out[i - 1], out[i], out[(i + 1) % n]
            if not keep[i - 1]: continue
            if abs(a[0] - c[0]) == 1 and abs(a[1] - c[1]) == 1 and (a[0] == b[0] or a[1] == b[1]) and (c[0] == b[0] or c[1] == b[1]):
                keep[i] = False; changed = True
        out = [p for p, k in zip(out, keep) if k]
    return out


def smooth_closed(c, sig, P):
    if sig <= 0 or len(c) < 8: return c
    s = sig * P; r = int(3 * s) + 1
    if 2 * r + 1 > len(c): r = (len(c) - 1) // 2
    k = np.exp(-0.5 * (np.arange(-r, r + 1) / s) ** 2); k /= k.sum()
    cp = np.concatenate([c[-r:], c, c[:r]], 0)
    return np.stack([np.convolve(cp[:, j], k, 'valid') for j in range(2)], 1)


def vec_line(alpha, N, P, sig=0.9, eps=0.8, pin=100.0, hole_min=6):
    """alpha: (N*P, N*P) bool hi-res silhouette (already eroded).  -> (line, inside) bool (N, N)."""
    cs, hier = cv2.findContours(alpha.astype(np.uint8), cv2.RETR_CCOMP, cv2.CHAIN_APPROX_NONE)
    line = np.zeros((N, N), bool)
    if hier is None: return line, line.copy()
    for c, h in zip(cs, hier[0]):
        area = cv2.contourArea(c) / float(P * P)
        if area < (hole_min if h[3] >= 0 else 2): continue
        pts = c[:, 0, :].astype(float)
        pts = (pts + 0.5) / P
        sm = smooth_closed(pts, sig, P)
        if pin > 0 and len(pts) > 5 * P:
            k = max(2, int(1.5 * P))
            a = np.roll(pts, k, 0) - pts; b = np.roll(pts, -k, 0) - pts
            cosang = (a * b).sum(1) / (np.linalg.norm(a, axis=1) * np.linalg.norm(b, axis=1) + 1e-9)
            sharp = cosang > np.cos(np.radians(pin))
            w = nd.maximum_filter1d(sharp.astype(float), 2 * k + 1, mode='wrap')
            w = nd.uniform_filter1d(w, k, mode='wrap')[:, None]
            sm = w * pts + (1 - w) * sm
        ap = cv2.approxPolyDP(sm.astype(np.float32).reshape(-1, 1, 2), eps, True)[:, 0, :]
        v = [(int(np.floor(y)), int(np.floor(x))) for x, y in ap]
        v = [p for i, p in enumerate(v) if p != v[i - 1]] or v
        path = []; cur = v[0]
        for b in v[1:] + v[:1]:
            sg = clean_seg(cur, b); path += sg[:-1]; cur = sg[-1]
        if cur != v[0]: path += bres(cur, v[0])[:-1]
        path = pixel_perfect(path)
        for y, x in path:
            if 0 <= y < N and 0 <= x < N: line[y, x] = True
    cov = alpha.reshape(N, P, N, P).mean((1, 3))
    lab, n = nd.label(~line, nd.generate_binary_structure(2, 1))
    border = set(np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]]))) - {0}
    inside = np.zeros((N, N), bool)
    for i in range(1, n + 1):
        if i in border: continue
        m = lab == i
        if cov[m].mean() >= 0.5: inside |= m
    p = np.pad(inside, 1)
    n8 = p[:-2, 1:-1] | p[2:, 1:-1] | p[1:-1, :-2] | p[1:-1, 2:] | p[:-2, :-2] | p[:-2, 2:] | p[2:, :-2] | p[2:, 2:]
    line &= n8      # a stroke pixel that bulges into the background with no fill next to it is dropped
    return line, inside
