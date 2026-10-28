#!/usr/bin/env python3
"""side-by-side zoom of png/*_full.txt (+ old master) -> png/r2_view.png. usage: r2_view.py [S] names..."""
import sys, json, os
import numpy as np
from PIL import Image
H = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
PAL = {k: v[0] for k, v in json.load(open(H + '/../pixel/palette.json'))['colors'].items()}
RGB = {k: tuple(int(v[i:i + 2], 16) for i in (1, 3, 5)) for k, v in PAL.items()}
def load(p):
    rows = [l for l in open(p).read().split('\n') if l and not l.startswith(';')]
    w = max(map(len, rows)); return [r.ljust(w, '.') for r in rows]
S = int(sys.argv[1]); names = sys.argv[2:]
maps = [load(H + '/../anim_redraw/m48/heads/neutral.txt')] + [load(f'{H}/png/{n}_full.txt') for n in names]
th = max(len(m) for m in maps); tw = sum(len(m[0]) + 3 for m in maps)
a = np.zeros((th * S + th + 6, tw * S, 3), np.uint8); a[:] = (110, 110, 110)
x0 = 0; x1 = 2
for m in maps:
    for y, r in enumerate(m):
        for x, c in enumerate(r):
            if c in RGB:
                a[y * S:(y + 1) * S, (x0 + x) * S:(x0 + x + 1) * S] = RGB[c]
                a[th * S + 4 + y, x1 + x] = RGB[c]
    x0 += len(m[0]) + 3; x1 += len(m[0]) + 4
Image.fromarray(a).save(H + '/png/r2_view.png'); print('ok')
