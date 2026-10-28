"""h3 common helpers: char-grid <-> RGBA, palette legend (STANDARD pixgrid chars), zoom views."""
import json, os, sys
import numpy as np
from PIL import Image, ImageDraw

ROOT = '/Users/waylonhuang/Documents/other/pixelart/swordswoman'
PAL = json.load(open(f'{ROOT}/docs/palette.json'))['ramps']
def hx(h): return tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))
C = {'K': hx('#1a1220'), 'm': hx(PAL['skin'][0]), 's': hx(PAL['skin'][1]), 'S': hx(PAL['skin'][2]),
     'h': hx(PAL['hair'][0]), 'H': hx(PAL['hair'][1]), 'J': hx(PAL['hair'][2]),
     'v': hx(PAL['red'][0]), 'r': hx(PAL['red'][1]), 'R': hx(PAL['red'][2]), 'C': hx(PAL['red'][3]),
     'l': hx(PAL['leather'][1]), 'L': hx(PAL['leather'][2]), 'd': hx(PAL['dark'][1]),
     't': hx(PAL['steel'][0]), 'T': hx(PAL['steel'][1]), 'w': hx(PAL['steel'][2]),
     'e': hx(PAL['eye'][0]), 'E': hx(PAL['eye'][1]), 'p': hx(PAL['pink'][0]), 'P': hx(PAL['pink'][1]),
     'u': hx(PAL['purple'][0])}
INV = {v: k for k, v in C.items()}
MAT = {}
for m, cs in {'red': 'vrRC', 'skin': 'msS', 'hair': 'hHJ', 'leather': 'lL', 'dark': 'd', 'steel': 'tTw',
              'eye': 'eE', 'pink': 'pP', 'outline': 'K', 'purple': 'u'}.items():
    for c in cs: MAT[c] = m


def read_grid(path):
    """.pix-like text: optional 'size:' line, 'grid:' then rows. Returns char array."""
    rows, on = [], False
    for ln in open(path).read().splitlines():
        if ln.startswith('grid:'): on = True; continue
        if on:
            if not ln.strip() or ln.startswith('#'): continue
            rows.append(ln.rstrip())
    w = max(len(r) for r in rows)
    bad = [i for i, r in enumerate(rows) if len(r) != w]
    if bad: raise SystemExit(f'{path}: rows {bad} not width {w}')
    return np.array([list(r) for r in rows])


def write_grid(g, path, comment=''):
    with open(path, 'w') as f:
        if comment: f.write(''.join('# ' + l + '\n' for l in comment.splitlines()))
        f.write(f'size: {g.shape[1]} {g.shape[0]}\ngrid:\n')
        for r in g: f.write(''.join(r) + '\n')


def to_rgba(g):
    a = np.zeros(g.shape + (4,), np.uint8)
    for y in range(g.shape[0]):
        for x in range(g.shape[1]):
            c = g[y, x]
            if c in '._': continue
            a[y, x, :3] = C[c]; a[y, x, 3] = 255
    return a


def to_chars(a):
    H, W = a.shape[:2]
    g = np.full((H, W), '.', dtype='<U1')
    for y in range(H):
        for x in range(W):
            if a[y, x, 3] > 0: g[y, x] = INV.get(tuple(int(v) for v in a[y, x, :3]), '?')
    return g


def load(p): return np.array(Image.open(p).convert('RGBA'))
def save(a, p): Image.fromarray(a).save(p)


def zoom(a, z=8, bg=(120, 120, 128), grid=True):
    H, W = a.shape[:2]
    im = Image.new('RGB', (W * z, H * z), bg)
    big = Image.fromarray(a).resize((W * z, H * z), Image.NEAREST)
    im.paste(big, (0, 0), big)
    if grid and z >= 6:
        d = ImageDraw.Draw(im)
        for x in range(0, W * z, z): d.line([(x, 0), (x, H * z)], fill=(100, 100, 108))
        for y in range(0, H * z, z): d.line([(0, y), (W * z, y)], fill=(100, 100, 108))
    return im


def strip(images, z=6, bg=(120, 120, 128), labels=None, gap=6, grid=False):
    ims = [zoom(a, z, bg, grid) for a in images]
    W = sum(i.width for i in ims) + gap * (len(ims) + 1)
    H = max(i.height for i in ims) + gap * 2 + (14 if labels else 0)
    out = Image.new('RGB', (W, H), (36, 32, 44))
    d = ImageDraw.Draw(out); x = gap
    for k, i in enumerate(ims):
        out.paste(i, (x, gap + (14 if labels else 0)))
        if labels: d.text((x, 2), labels[k], fill=(230, 230, 230))
        x += i.width + gap
    return out


def crop_box(a, pad=2):
    ys, xs = np.nonzero(a[..., 3])
    return max(0, xs.min() - pad), max(0, ys.min() - pad), min(a.shape[1], xs.max() + pad + 1), min(a.shape[0], ys.max() + pad + 1)
