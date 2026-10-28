"""char-map helpers for heads96"""
import json, os
from PIL import Image
ROOT = '/Users/waylonhuang/Documents/other/pixelart/swordswoman/v2'
PAL = {k: v['hex'] for k, v in json.load(open(f'{ROOT}/pixelize/palette.json'))['colors'].items()}
def rgb(h): return tuple(int(h[i:i+2], 16) for i in (1, 3, 5))
PALRGB = {k: rgb(v) for k, v in PAL.items()}
def load(path):
    meta = {}; rows = []
    for l in open(path):
        l = l.rstrip('\n')
        if l.startswith(';'):
            p = l[1:].split()
            if p: meta[p[0]] = p[1:]
            continue
        if l: rows.append(l)
    return rows, meta
def save(path, rows, meta=None):
    with open(path, 'w') as f:
        for k, v in (meta or {}).items(): f.write('; %s %s\n' % (k, ' '.join(map(str, v))))
        f.write('\n'.join(rows) + '\n')
def to_img(rows, scale=1, bg=None):
    h = len(rows); w = max(len(r) for r in rows)
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0) if bg is None else rgb(bg) + (255,))
    px = im.load()
    for y, r in enumerate(rows):
        for x, c in enumerate(r):
            if c in PALRGB: px[x, y] = PALRGB[c] + (255,)
    return im.resize((w * scale, h * scale), Image.NEAREST) if scale > 1 else im
def crop(rows, x0, y0, x1, y1):
    return [r[x0:x1].ljust(x1 - x0, '.') for r in rows[y0:y1]]
