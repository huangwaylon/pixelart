#!/usr/bin/env python3
"""r4: outer-outline straight-run report. usage: runs.py [names...] (default: all png/*_full.txt + head files)
Outer outline = opaque pixels whose 4-neighbour in a direction is EXTERIOR transparency (flood-filled from the border).
Wall runs: L/R = vertical runs of pixels with exterior to the left/right; T/B = horizontal runs with exterior above/below.
Also reports enclosed transparent holes."""
import sys, os, glob
H = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
def grid(p):
    L = [l for l in open(p).read().split('\n') if l.strip() and not l.startswith(';')]
    w = max(map(len, L)) + 2
    return ['.' * w] + ['.' + l.ljust(w - 1, '.') for l in L] + ['.' * w]
def report(p, lim=3):
    g = grid(p); h, w = len(g), len(g[0])
    ext = {(0, 0)}; st = [(0, 0)]
    while st:
        y, x = st.pop()
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            Y, X = y + dy, x + dx
            if 0 <= Y < h and 0 <= X < w and (Y, X) not in ext and g[Y][X] == '.': ext.add((Y, X)); st.append((Y, X))
    holes = [(y - 1, x - 1) for y in range(h) for x in range(w) if g[y][x] == '.' and (y, x) not in ext]
    op = lambda y, x: g[y][x] != '.'
    res = {}
    for k, (dy, dx), vert in (('L', (0, -1), 1), ('R', (0, 1), 1), ('T', (-1, 0), 0), ('B', (1, 0), 0)):
        on = lambda y, x: op(y, x) and (y + dy, x + dx) in ext
        runs = []
        if vert:
            for x in range(w):
                y = 0
                while y < h:
                    if on(y, x):
                        y0 = y
                        while y < h and on(y, x): y += 1
                        runs.append((y - y0, f'col{x-1} rows{y0-1}-{y-2}'))
                    else: y += 1
        else:
            for y in range(h):
                x = 0
                while x < w:
                    if on(y, x):
                        x0 = x
                        while x < w and on(y, x): x += 1
                        runs.append((x - x0, f'row{y-1} cols{x0-1}-{x-2}'))
                    else: x += 1
        res[k] = sorted(runs, reverse=True)
    bad = {k: [r for r in v if r[0] > lim] for k, v in res.items()}
    print(f'{os.path.relpath(p, H):24s} max L{res["L"][0][0]} R{res["R"][0][0]} T{res["T"][0][0]} B{res["B"][0][0]} holes{len(holes)}',
          ' | >%d: ' % lim + ('; '.join(f'{k}{n}@{s}' for k, v in bad.items() for n, s in v) or 'none'), holes[:6] or '')
args = sys.argv[1:]
paths = [f'{H}/png/{a}_full.txt' if not a.endswith('.txt') else a for a in args] or sorted(glob.glob(f'{H}/se/head_*.txt') + glob.glob(f'{H}/e/head_*.txt') + glob.glob(f'{H}/png/*_full.txt'))
for p in paths: report(p)
