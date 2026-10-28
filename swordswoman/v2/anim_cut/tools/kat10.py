#!/usr/bin/env python3
"""R10 katana cleanup: draws every parts/common katana char-map with strict rules.
Blade: 2px band (w core on the up/left side, n edge on the axis), single 4-neighbour # outline,
constant euclidean length (~18px), periodic step pattern for the slope, 1px n tip.
Hilt: 1px-thick k guard (4px across), 2px handle d (lit side) / D (axis). Pivot = axis pixel 2 behind guard.
"""
import os, sys, math, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cm
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
BLADE, HILT = 18.0, 4.2   # euclidean px

# name -> (dx, dy) screen direction of blade (integer slope)
D16 = [(1, 0), (2, -1), (1, -1), (1, -2), (0, -1), (-1, -2), (-1, -1), (-2, -1),
       (-1, 0), (-2, 1), (-1, 1), (-1, 2), (0, 1), (1, 2), (1, 1), (2, 1)]
FILES = {'kat_%02d' % i: (v, {}) for i, v in enumerate(D16)}
FILES.update({
    'kat_iw6_095': ((-3, 2), {}),
    'kat_iw7_b': ((-3, 2), {}),
    'kat_run7_105': ((-2, 3), {}),
    'dash9_kat_10': ((-1, 1), {}),
    'kat14_slash10_flash': ((1, 1), {'w': 'x', 'n': 'w'}),
})


def make(v, recol):
    vx, vy = v
    sx, sy = (vx > 0) - (vx < 0), (vy > 0) - (vy < 0)
    majx = abs(vx) >= abs(vy)
    a, b = (abs(vx), abs(vy)) if majx else (abs(vy), abs(vx))
    f = math.hypot(a, b) / a
    L, H = round(BLADE / f), round(HILT / f)
    ph = 0
    if b:
        for ph in range(a):
            if ((L * b + ph) // a) != ((L + 1) * b + ph) // a:
                break

    def P(k, side=0):   # axis pixel at major step k, shifted 'side' px toward lit side (up / left)
        m = (k * b + ph) // a if b else 0
        if majx:
            return (k * sx, m * sy - side)
        return (m * sx - side, k * sy)
    px = {}
    for k in range(-H, 0):            # handle
        px[P(k)] = 'D'
        px[P(k, 1)] = 'd'
    if a == b:                        # 1:1 guard = 4-connected zigzag across the blade
        ex, ey = (sy, -sx) if -sx < 0 else (-sy, sx)
        (ax_, ay_), (lx, ly) = P(0), P(0, 1)
        for q in ((ax_, ay_), (lx, ly), (lx + ex, ly), (ax_ - ex, ay_)):
            px[q] = 'k'
    else:
        for s in (-1, 0, 1, 2):       # guard
            px[P(0, s)] = 'k'
    for k in range(1, L + 1):         # blade
        px[P(k)] = 'n'
        if k < L:
            px[P(k, 1)] = 'w'
    px = {p: recol.get(c, c) for p, c in px.items()}
    allp = {}
    for (x, y) in px:
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            if (x + dx, y + dy) not in px:
                allp[(x + dx, y + dy)] = '#'
    allp.update(px)
    xs = [p[0] for p in allp]; ys = [p[1] for p in allp]
    x0, y0 = min(xs), min(ys)
    g = np.full((max(ys) - y0 + 1, max(xs) - x0 + 1), '.', dtype='<U1')
    for (x, y), c in allp.items():
        g[y - y0, x - x0] = c
    gx, gy = P(-2)
    return g, (gx - x0, gy - y0)


if __name__ == '__main__':
    for name, (v, rc) in FILES.items():
        g, piv = make(v, rc)
        cm.write_cm(os.path.join(ROOT, 'parts', 'common', name + '.txt'), g, {'pivot': piv, 'anchors': {}})
        print(name, g.shape, piv)
