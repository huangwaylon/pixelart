"""legfix.py STEM [Y0 Y1]: skin band / skirt hem cleanup: d/g (sock/hair greys) and k touching skin -> S / s; d/g inside red -> R; rows Y0..Y1"""
import sys, os, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import m96 as M, pzlib as Z
st = sys.argv[1]; y0, y1 = (int(sys.argv[2]), int(sys.argv[3])) if len(sys.argv) > 3 else (84, 100)
g, meta = Z.read(st); keys, rgb, _ = Z.load_pal(M.PAL); n = 0
# sock top: first row (from the bottom up) where D dominates the legs; band ends there
for it in range(3):
    o = g.copy()
    for y in range(y0, y1):
        for x in range(1, 127):
            c = g[y, x]
            if c not in 'dgk': continue
            nb = [g[y + dy, x + dx] for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1))]
            sk = sum(t in 'sSm' for t in nb); rd = sum(t in 'eER' for t in nb); dk = sum(t in 'Dd' for t in nb)
            if c == 'k' and sk: o[y, x] = 's'
            elif c in 'dg' and dk >= 3 and c == 'd': continue  # real sock light
            elif c in 'dg' and sk >= rd and sk: o[y, x] = 'S'
            elif c in 'dg' and rd: o[y, x] = 'R'
    n += (o != g).sum(); g = o
Z.save(g, st, keys, rgb, meta); print(st, n, 'px')
