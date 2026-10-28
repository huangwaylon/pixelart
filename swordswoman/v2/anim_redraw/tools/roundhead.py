"""Round the skull dome of m48/SE_box_grid.txt -> m48/SE.png + SE_grid.txt (bow/face/body untouched)."""
import sys, numpy as np
sys.path.insert(0, '/Users/waylonhuang/Documents/other/pixelart/swordswoman/v2/anim_redraw/tools')
import fin48 as F
A = F.A
G = np.array([list(l) for l in open(A + '/m48/SE_box_grid.txt').read().split('\n') if l])
o = G.copy()
cx, cy, rx, ry, n = 29.5, 25.0, 10.6, 8.0, 2.4
bun = (20.2, 18.4, 3.0)
def inside(x, y):
    if y <= 27.0:
        dy = max(0.0, cy - y) if y < cy else 0.0
        hw = rx * max(0.0, 1 - (dy / ry) ** n) ** (1 / n)
        if abs(x - cx) <= hw: return True
    return (x - bun[0]) ** 2 + ((y - bun[1]) * 1.05) ** 2 <= bun[2] ** 2
HAIR = set('hHj')
for y in range(14, 30):
    for x in range(14, 46):
        if G[y, x] in 'rREe' and y <= 17: continue          # bow stays
        edge = G[y, x] == '#' and any(G[y + dy, x + dx] == '.' for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (-1, 1), (1, -1), (-1, -1)))
        if G[y, x] == '#' and not edge: continue             # interior lines (brow, bow) stay
        if G[y, x] not in '.#hHj': continue
        ins = inside(x + 0.5, y + 0.5)
        if y >= 27 and not ins: continue                     # lower bob/face: only add
        if ins:
            if G[y, x] in HAIR: continue
            o[y, x] = 'H'
        elif G[y, x] in HAIR or (G[y, x] == '#' and y >= 18):
            o[y, x] = '.'
# rim shade: right edge 'h', left lower edge 'h'
for y in range(18, 30):
    xs = [x for x in range(14, 46) if o[y, x] in HAIR]
    if not xs: continue
    if y >= 22: o[y, max(xs)] = 'h'
    if y >= 27: o[y, min(xs)] = 'h'
# outline
m = np.isin(o, list('hHjrREe123iIwp'))
for y in range(13, 30):
    for x in range(14, 46):
        if o[y, x] == '.' and any(m[y + dy, x + dx] for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
            o[y, x] = '#'
# bun/skull notch: inner outline line between bun and skull
for (x, y) in [(23, 20), (23, 21)]:
    if o[y, x] in HAIR: o[y, x] = '#'
open(A + '/m48/SE_grid.txt', 'w').write('\n'.join(''.join(r) for r in o) + '\n')
F.to_img(o).save(A + '/m48/SE.png')
for y in range(10, 38): print(''.join(o[y, 14:46]), '|', ''.join(G[y, 14:46]))
# manual bun/skull junction (slice cols 14..), rows 15-21
P = {15: '....####.', 16: '...#HHHH#.', 17: '..#HHHHHH#HHH', 18: '..#HHHHHH#H', 19: '...#HHHH#HH', 20: '....#HH#HHH', 21: '....#H#HHHH', 22: '....#HHH'}
for y, s in P.items():
    for i, c in enumerate(s): o[y, 14 + i] = c
open(A + '/m48/SE_grid.txt', 'w').write('\n'.join(''.join(r) for r in o) + '\n')
F.to_img(o).save(A + '/m48/SE.png')
print('---')
for y in range(14, 24): print(''.join(o[y, 14:46]))
