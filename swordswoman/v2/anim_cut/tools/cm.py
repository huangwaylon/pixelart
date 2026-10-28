#!/usr/bin/env python3
"""ANIM_CUT char-map toolkit.

Char-map (.txt) format: rows of palette chars ('.' = transparent). Lines starting with ';' are meta:
  ; pivot X Y            part pivot (attach point) in local coords
  ; anchor NAME X Y      extra named anchor (e.g. hand, neck, hip)
Palette: v2/pixel/palette.json (char -> hex).

CLI:
  cm.py png   in.txt out.png [--s N]          render (1x default)
  cm.py zoom  in.(txt|png) out.png [--s 14]   zoomed grid with coordinates (for hand editing)
  cm.py grid  in.png out.txt                  png -> char-map (nearest palette char)
  cm.py lint  in.(txt|png)                    orphans / colours / outline doubles
"""
import json, os, sys
import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
PAL_PATH = os.path.join(HERE, '..', '..', 'pixel', 'palette.json')

_pal = json.load(open(PAL_PATH))['colors']
EXTRA = {  # anim_cut additions (VFX / smear)
    'x': '#ffffff',   # pure white flash
    'y': '#ffe6a0',   # smear warm core
    'Y': '#f0b060',   # smear warm band
    'o': '#3a2a30',   # speed line / ground shadow dark (alpha handled in compose)
}
PAL = {c: v[0] for c, v in _pal.items()}
PAL.update(EXTRA)
RGB = {c: tuple(int(h[i:i + 2], 16) for i in (1, 3, 5)) for c, h in PAL.items()}
OUT = '#'


def read_cm(path):
    meta = {'anchors': {}}
    rows = []
    for l in open(path):
        l = l.rstrip('\n')
        if l.startswith(';'):
            t = l[1:].split()
            if not t:
                continue
            if t[0] == 'pivot':
                meta['pivot'] = (int(t[1]), int(t[2]))
            elif t[0] == 'anchor':
                meta['anchors'][t[1]] = (int(t[2]), int(t[3]))
            else:
                meta[t[0]] = t[1:]
            continue
        if l.strip() == '' and not rows:
            continue
        rows.append(l)
    while rows and rows[-1].strip() == '':
        rows.pop()
    W = max(len(r) for r in rows)
    g = np.full((len(rows), W), '.', dtype='<U1')
    for y, r in enumerate(rows):
        for x, ch in enumerate(r):
            g[y, x] = '.' if ch == ' ' else ch
    meta.setdefault('pivot', (0, 0))
    return g, meta


def write_cm(path, g, meta=None):
    with open(path, 'w') as f:
        if meta:
            if 'pivot' in meta:
                f.write('; pivot %d %d\n' % tuple(meta['pivot']))
            for k, v in meta.get('anchors', {}).items():
                f.write('; anchor %s %d %d\n' % (k, v[0], v[1]))
        for row in g:
            f.write(''.join(row).rstrip('.') .ljust(0) + '\n' if False else ''.join(row) + '\n')


def to_rgba(g):
    H, W = g.shape
    a = np.zeros((H, W, 4), np.uint8)
    for y in range(H):
        for x in range(W):
            c = g[y, x]
            if c == '.':
                continue
            if c not in RGB:
                raise SystemExit(f'unknown char {c!r} at {x},{y}')
            a[y, x, :3] = RGB[c]; a[y, x, 3] = 255
    return a


def from_rgba(a):
    chars = list(RGB)
    pal = np.array([RGB[c] for c in chars], float)
    H, W = a.shape[:2]
    g = np.full((H, W), '.', dtype='<U1')
    d = ((a[..., None, :3].astype(float) - pal[None, None]) ** 2).sum(-1)
    idx = d.argmin(-1)
    for y in range(H):
        for x in range(W):
            if a[y, x, 3] >= 128:
                g[y, x] = chars[idx[y, x]]
    return g


def load_any(p):
    if p.endswith('.txt'):
        return read_cm(p)[0]
    return from_rgba(np.array(Image.open(p).convert('RGBA')))


def upscale(a, s, bg=(0x6e, 0x6e, 0x6e)):
    im = Image.fromarray(a, 'RGBA').resize((a.shape[1] * s, a.shape[0] * s), Image.NEAREST)
    if bg is None:
        return im
    b = Image.new('RGBA', im.size, bg + (255,))
    b.alpha_composite(im)
    return b.convert('RGB')


def zoom(g, s=14, pivot=None):
    a = to_rgba(g)
    H, W = g.shape
    m = 18
    im = Image.new('RGB', (W * s + m, H * s + m), (0x6e, 0x6e, 0x6e))
    im.paste(upscale(a, s), (m, m))
    d = ImageDraw.Draw(im)
    for x in range(W + 1):
        col = (40, 40, 40) if x % 5 == 0 else (90, 90, 90)
        d.line([(m + x * s, m), (m + x * s, m + H * s)], fill=col)
        if x % 5 == 0 and x < W:
            d.text((m + x * s + 1, 2), str(x), fill=(255, 255, 0))
    for y in range(H + 1):
        col = (40, 40, 40) if y % 5 == 0 else (90, 90, 90)
        d.line([(m, m + y * s), (m + W * s, m + y * s)], fill=col)
        if y % 5 == 0 and y < H:
            d.text((1, m + y * s + 1), str(y), fill=(255, 255, 0))
    if pivot:
        px, py = pivot
        d.rectangle([m + px * s + s // 3, m + py * s + s // 3, m + px * s + 2 * s // 3, m + py * s + 2 * s // 3], outline=(0, 255, 0))
    return im


def lint(g):
    H, W = g.shape
    orph = []
    for y in range(H):
        for x in range(W):
            c = g[y, x]
            if c == '.':
                continue
            n = 0
            for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                yy, xx = y + dy, x + dx
                if 0 <= yy < H and 0 <= xx < W and g[yy, xx] == c:
                    n += 1
            if n == 0:
                orph.append((x, y, c))
    cols = sorted(set(g.flatten()) - {'.'})
    return orph, cols


if __name__ == '__main__':
    a = sys.argv[1:]
    cmd = a[0]
    if cmd == 'png':
        s = int(a[a.index('--s') + 1]) if '--s' in a else 1
        g, _ = read_cm(a[1])
        arr = to_rgba(g)
        (Image.fromarray(arr, 'RGBA') if s == 1 else upscale(arr, s)).save(a[2])
    elif cmd == 'zoom':
        s = int(a[a.index('--s') + 1]) if '--s' in a else 14
        piv = read_cm(a[1])[1]['pivot'] if a[1].endswith('.txt') else None
        zoom(load_any(a[1]), s, piv).save(a[2])
    elif cmd == 'grid':
        g = load_any(a[1]); write_cm(a[2], g)
    elif cmd == 'lint':
        o, c = lint(load_any(a[1]))
        print('colours', len(c), ''.join(c)); print('orphans', len(o), o[:30])
