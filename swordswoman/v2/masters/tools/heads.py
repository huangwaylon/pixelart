#!/usr/bin/env python3
"""heads.py: expression head stamps for S/SE/E from heads/<V>_neutral.txt (cut from the masters) using the FACE_GUIDE compact
grammar (v2/face/tools/faces.py EYE3 / MOUTH3; FACE_GUIDE section 9). Writes heads/<V>_<expr>.txt (+ '; origin X Y' = cell
position of the stamp's top-left in the 64x64 master) and heads/expr_sheet.png."""
import sys
sys.path.insert(0, '/Users/waylonhuang/Documents/other/pixelart/swordswoman/v2/face/tools'); sys.path.insert(0, '/Users/waylonhuang/Documents/other/pixelart/swordswoman/v2/masters/tools')
import faces
from mm import render
from PIL import Image
D = '/Users/waylonhuang/Documents/other/pixelart/swordswoman/v2/masters/heads/'
# anchors in stamp coords: eye box top-left (lash row) X,Y ; far: 'm3' = mirrored 3-wide, 'f2' = mirrored, foreshortened 2-wide
A = {'S':  dict(near=(8, 13), far=(14, 13, 'm3'), mouth=(12, 18), blush=[(7, 16), (17, 16)], squash=9),
     'SE': dict(near=(9, 13), far=(15, 13, 'f2'), mouth=(13, 17), blush=[(8, 16), (17, 16)], squash=9),
     'E':  dict(near=(19, 13), far=None, mouth=(21, 17), blush=[(18, 16)], squash=9)}
def load(v):
    L = [l.rstrip('\n') for l in open(D + f'{v}_neutral.txt')]
    meta = [l for l in L if l.startswith(';')]; g = [list(l) for l in L if l and not l.startswith(';')]
    return meta, g
def put(g, st, x0, y0):
    for dy, row in enumerate(st):
        for dx, c in enumerate(row):
            if c != '.': g[y0+dy][x0+dx] = c
def clear(g, x0, y0, w, h, chars='KWiIr'):
    for y in range(y0, y0 + h):
        for x in range(x0, x0 + w):
            if g[y][x] in chars: g[y][x] = 's'
def build(v, ex):
    meta, g = load(v); a = A[v]
    st = faces.EYE3[ex]
    X, Y = a['near']; clear(g, X - 1, Y - 1, 4, 4); put(g, st, X - 1, Y - 1)
    if a['far']:
        X, Y, kind = a['far']; m = [r[::-1] for r in st]
        if kind == 'f2': m = [r[0] + r[2:] for r in m]; m = [r if i < 2 else r[:3] + ('.' if r[3] == 'K' else r[3]) for i, r in enumerate(m)]
        clear(g, X - 1, Y - 1, len(m[0]) - 1, 4); put(g, m, X - 1, Y - 1)
    x, y = a['mouth']; clear(g, x - 1, y, 3, 2); put(g, faces.MOUTH3[ex], x - 1, y)
    if ex in faces.BLUSH:
        for bx, by in a['blush']:
            if g[by][bx] in 'sS': g[by][bx] = 'e'
    if ex == 'squash':
        r = a['squash']; g = [['.'] * len(g[0])] + g[:r] + g[r+1:]
    return meta, g
if __name__ == '__main__':
    tiles = []
    for v in A:
        _, g0 = load(v); _, g1 = build(v, 'neutral')
        print(v, 'neutral rebuild diffs vs master cut:', sum(a != b for r0, r1 in zip(g0, g1) for a, b in zip(r0, r1)))
        for ex in faces.EXPR:
            meta, g = build(v, ex)
            if ex == 'neutral': g = load(v)[1]  # neutral = the master cut itself
            if ex != 'neutral': open(D + f'{v}_{ex}.txt', 'w').write('\n'.join(meta + [f'; expr {ex}'] + [''.join(r) for r in g]) + '\n')
            tiles.append(render([''.join(r) for r in g], 6, (190, 190, 190, 255)))
    W = max(t.width for t in tiles); H = max(t.height for t in tiles); n = len(faces.EXPR)
    sh = Image.new('RGBA', (W * n, H * 3), (190, 190, 190, 255))
    for i, t in enumerate(tiles): sh.paste(t, ((i % n) * W, (i // n) * H))
    sh.save(D + 'expr_sheet.png'); print(sh.size)
