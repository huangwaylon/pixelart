#!/usr/bin/env python3
"""masters toolkit: render char-maps with pk_palette, build rig guides.
  mm.py png in.txt out.png [scale]
  mm.py guide VIEW out.txt [total_h]
"""
import json, sys
import numpy as np
from PIL import Image
V2 = '/Users/waylonhuang/Documents/other/pixelart/swordswoman/v2'
PAL = {c: v[0] for c, v in json.load(open(V2 + '/style/pk_palette.json'))['colors'].items()}
def hx(h): return tuple(int(h[i:i+2], 16) for i in (1, 3, 5))
def read(p):
    g = [l.rstrip('\n') for l in open(p) if l.strip() and not l.startswith(';')]
    w = max(map(len, g)); return [l.ljust(w, '.') for l in g]
def render(g, s=1, bg=None):
    h, w = len(g), len(g[0]); im = Image.new('RGBA', (w, h), (0, 0, 0, 0) if bg is None else bg)
    px = im.load()
    for y, r in enumerate(g):
        for x, c in enumerate(r):
            if c in PAL: px[x, y] = hx(PAL[c]) + (255,)
    return im.resize((w*s, h*s), Image.NEAREST) if s > 1 else im
def cls(r, g, b):
    if b > r + 15 and b > 110: return 'I'
    if r > 150 and g > 120: return 's'
    if r > g + 50 and r > 90: return 'E'
    if b > g + 12 and r < 120: return 'd'
    return 'H'
def guide(view, out, total=52, feet=61, cell=64):
    im = np.array(Image.open(f'{V2}/design/turnE/rigref/iso_{view}.png').convert('RGB')).astype(int)
    m = im.sum(2) < 735
    ys, xs = np.where(m); y0, y1, x0, x1 = ys.min(), ys.max(), xs.min(), xs.max()
    sc = total / (y1 - y0 + 1)
    W = max(1, round((x1 - x0 + 1) * sc))
    rgb = Image.fromarray(im[y0:y1+1, x0:x1+1].astype(np.uint8)).resize((W, total), Image.BOX)
    al = Image.fromarray((m[y0:y1+1, x0:x1+1]*255).astype(np.uint8)).resize((W, total), Image.BOX)
    rgb, al = np.array(rgb).astype(int), np.array(al)
    cands = 'HhsSERdI'
    cols = np.array([hx(PAL[c]) for c in cands])
    grid = [['.'] * cell for _ in range(cell)]
    ox = cell // 2 - W // 2; oy = feet - total + 1
    for y in range(total):
        for x in range(W):
            if al[y, x] > 110:
                grid[oy+y][ox+x] = cls(*rgb[y, x])
    g2 = [r[:] for r in grid]
    for y in range(cell):
        for x in range(cell):
            if grid[y][x] != '.':
                for dx, dy in ((1,0),(-1,0),(0,1),(0,-1)):
                    X, Y = x+dx, y+dy
                    if not (0 <= X < cell and 0 <= Y < cell) or grid[Y][X] == '.': g2[y][x] = 'K'; break
    open(out, 'w').write('\n'.join(''.join(r) for r in g2) + '\n')
if __name__ == '__main__':
    a = sys.argv
    if a[1] == 'png': render(read(a[2]), int(a[4]) if len(a) > 4 else 1).save(a[3])
    elif a[1] == 'guide': guide(a[2], a[3], int(a[4]) if len(a) > 4 else 52)

def cls2(r, g, b):
    lum = 0.3*r + 0.59*g + 0.11*b
    if lum < 45: return 'K'
    if b > r + 15 and b > 90 and g < 160: return 'I' if lum > 70 else 'i'
    if abs(r-g) < 30 and abs(g-b) < 30 and lum > 140: return 'n' if lum < 225 else 'W'
    if r > 150 and g > 110 and r - b > 30: return 's' if lum > 175 else 'S'
    if r > g + 60 and r > 100: return 'e' if lum > 120 else ('E' if lum > 85 else 'R')
    if r > g + 40: return 'r'
    if b >= g and abs(r - b) < 40 and lum > 90: return 'd'
    return 'H' if lum > 60 else 'h'
def dguide(src, out, total=52, feet=61, cell=64):
    im = np.array(Image.open(src).convert('RGB')).astype(int)
    m = im.sum(2) < 720
    ys, xs = np.where(m); y0, y1, x0, x1 = ys.min(), ys.max(), xs.min(), xs.max()
    sc = total / (y1 - y0 + 1); W = max(1, round((x1 - x0 + 1) * sc))
    rgb = np.array(Image.fromarray(im[y0:y1+1, x0:x1+1].astype(np.uint8)).resize((W, total), Image.BOX)).astype(int)
    al = np.array(Image.fromarray((m[y0:y1+1, x0:x1+1]*255).astype(np.uint8)).resize((W, total), Image.BOX))
    # centre on the feet (bottom 4 rows)
    fx = np.where(al[-4:].max(0) > 110)[0]; c = (fx.min() + fx.max()) // 2
    ox = cell // 2 - c; oy = feet - total + 1
    grid = [['.'] * cell for _ in range(cell)]
    for y in range(total):
        for x in range(W):
            if al[y, x] > 110 and 0 <= ox + x < cell: grid[oy+y][ox+x] = cls2(*rgb[y, x])
    open(out, 'w').write('\n'.join(''.join(r) for r in grid) + '\n')
if __name__ == '__main__' and sys.argv[1] == 'dguide': dguide(sys.argv[2], sys.argv[3], int(sys.argv[4]) if len(sys.argv) > 4 else 52)
