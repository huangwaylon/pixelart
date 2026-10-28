#!/usr/bin/env python3
"""view.py in.(txt|png)[,more...] out.png [--s 8] [--grid]  : crop to union bbox(+2), zoom NN side by side, max 1000px wide."""
import sys, os, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cm
from PIL import Image
a = sys.argv[1:]
s = int(a[a.index('--s') + 1]) if '--s' in a else 8
ins = a[0].split(',')
gs = [cm.load_any(p) for p in ins]
H = max(g.shape[0] for g in gs); W = max(g.shape[1] for g in gs)
m = np.zeros((H, W), bool)
for g in gs:
    m[:g.shape[0], :g.shape[1]] |= (g != '.')
ys, xs = np.where(m)
y0, y1, x0, x1 = max(ys.min() - 2, 0), ys.max() + 3, max(xs.min() - 2, 0), xs.max() + 3
tiles = []
for g in gs:
    gg = np.full((H, W), '.', dtype='<U1'); gg[:g.shape[0], :g.shape[1]] = g
    c = gg[y0:y1, x0:x1]
    if '--grid' in a:
        tiles.append(cm.zoom(c, s))
    else:
        tiles.append(cm.upscale(cm.to_rgba(c), s))
while sum(t.size[0] + 4 for t in tiles) > 1000 and s > 2:
    s -= 1
    tiles = [cm.zoom(np.full((1,1),'.'),1)]  # recompute below
    tiles = []
    for g in gs:
        gg = np.full((H, W), '.', dtype='<U1'); gg[:g.shape[0], :g.shape[1]] = g
        c = gg[y0:y1, x0:x1]
        tiles.append(cm.zoom(c, s) if '--grid' in a else cm.upscale(cm.to_rgba(c), s))
TW = sum(t.size[0] + 4 for t in tiles); TH = max(t.size[1] for t in tiles)
out = Image.new('RGB', (TW, TH), (40, 40, 40))
x = 0
for t in tiles:
    out.paste(t, (x, 0)); x += t.size[0] + 4
out.save(a[1]); print(out.size, 'offset', x0, y0)
