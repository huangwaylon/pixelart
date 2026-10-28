#!/usr/bin/env python3
"""v2/heads preview: compose head_<v>.txt + bun.txt + bow.txt by anchors (anim_cut cm.py char-map convention:
'; pivot X Y', '; anchor NAME X Y'; bun z behind head, bow z in front) -> png/<view>_<v>_1x.png, _6x.png,
png/<view>_<v>_full.txt (composited char-map, pivot = head pivot), and png/sheet.png (all variants at 6x + 1x, plus refs).
Usage: preview.py"""
import json, os, glob
import numpy as np
from PIL import Image
H = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
PAL = {k: v[0] for k, v in json.load(open(H + '/../pixel/palette.json'))['colors'].items()}
RGB = {k: tuple(int(v[i:i + 2], 16) for i in (1, 3, 5)) for k, v in PAL.items()}
def load(p):
    meta, rows = {}, []
    for l in open(p).read().split('\n'):
        if l.startswith(';'):
            t = l[1:].split()
            if t and t[0] == 'pivot': meta['pivot'] = (int(t[1]), int(t[2]))
            elif t and t[0] == 'anchor': meta[t[1]] = (int(t[2]), int(t[3]))
        elif l.strip(): rows.append(l)
    w = max(len(r) for r in rows)
    return np.array([list(r.ljust(w, '.')) for r in rows]), meta
def compose(view, v):
    hp = f'{H}/{view}/head_{v}.txt'
    hg, hm = load(hp)
    parts = [(hg, hm['pivot'], (0, 0), 1)]
    for name, z in (('bun', 0), ('bow', 2)):
        cand = [f'{H}/{view}/{name}_{v}.txt', f'{H}/{view}/{name}.txt']
        p = next((c for c in cand if os.path.exists(c)), None)
        if p and name in hm:
            g, m = load(p); parts.append((g, m['pivot'], hm[name], z))
    # canvas in head-local coords with margin
    M = 12; Hh, Ww = hg.shape; C = np.full((Hh + 2 * M, Ww + 2 * M), '.', dtype='<U1')
    hpx, hpy = hm['pivot']
    for g, (px, py), (ax, ay), z in sorted(parts, key=lambda t: t[3]):
        ox, oy = (ax - px, ay - py) if z != 1 else (0, 0)
        for y in range(g.shape[0]):
            for x in range(g.shape[1]):
                c = g[y, x]
                if c != '.': C[y + oy + M, x + ox + M] = c
    ys, xs = np.nonzero(C != '.'); y0, x0 = ys.min(), xs.min()
    C = C[y0:ys.max() + 1, x0:xs.max() + 1]
    return C, (hpx + M - x0, hpy + M - y0)
def img(C, bg=(110, 110, 110)):
    a = np.zeros(C.shape + (3,), np.uint8); a[:] = bg
    for c, rgb in RGB.items(): a[C == c] = rgb
    return Image.fromarray(a)
os.makedirs(H + '/png', exist_ok=True)
tiles = []
for view in ('se', 'e'):
    for hp in sorted(glob.glob(f'{H}/{view}/head_*.txt')):
        v = os.path.basename(hp)[5:-4]
        C, piv = compose(view, v)
        open(f'{H}/png/{view}_{v}_full.txt', 'w').write(f'; pivot {piv[0]} {piv[1]}\n; composed head+bun+bow ({view} {v})\n' + '\n'.join(''.join(r) for r in C) + '\n')
        im = img(C); im.save(f'{H}/png/{view}_{v}_1x.png'); im.resize((im.width * 6, im.height * 6), Image.NEAREST).save(f'{H}/png/{view}_{v}_6x.png')
        tiles.append((f'{view} {v}', im))
if tiles:
    S = 6; tw = max(t.width for _, t in tiles) * S + 8; th = max(t.height for _, t in tiles) * S + 8
    cols = min(5, len(tiles)); rows = (len(tiles) + cols - 1) // cols
    sh = Image.new('RGB', (cols * tw, rows * th + 50), (40, 40, 40))
    for k, (n, t) in enumerate(tiles):
        sh.paste(t.resize((t.width * S, t.height * S), Image.NEAREST), ((k % cols) * tw, (k // cols) * th))
        sh.paste(t, (k * (t.width + 6) + 4, rows * th + 10))
    sh.save(H + '/png/sheet.png'); print('sheet', sh.size, [n for n, _ in tiles])
