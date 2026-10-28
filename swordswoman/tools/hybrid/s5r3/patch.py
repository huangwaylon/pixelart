"""exact-pixel patch helper (Claude hand pixels). Grids are lists of strings in the STANDARD legend; '_' / ' ' keep
the pixel underneath, '.' clears it, 'X' clears too. apply(a, x0, y0, rows, mode='over'|'behind'|'onbody')
  over   = paint everywhere; behind = only on transparent px; onbody = only on opaque px.
Every call is appended to LOG (sprite, what, why) by the caller via note()."""
import json
import numpy as np
from PIL import Image
PAL = json.load(open('/Users/waylonhuang/Documents/other/pixelart/swordswoman/docs/palette.json'))
R = PAL['ramps']
LEG = {'K': PAL['outline'], 'm': R['skin'][0], 's': R['skin'][1], 'S': R['skin'][2], 'h': R['hair'][0], 'H': R['hair'][1],
       'J': R['hair'][2], 'v': R['red'][0], 'r': R['red'][1], 'R': R['red'][2], 'C': R['red'][3], 'l': R['leather'][1],
       'L': R['leather'][2], 'd': R['dark'][1], 't': R['steel'][0], 'T': R['steel'][1], 'w': R['steel'][2],
       'e': R['eye'][0], 'E': R['eye'][1], 'p': R['pink'][0], 'P': R['pink'][1], 'u': R['purple'][0]}
RGB = {k: tuple(int(v[i:i + 2], 16) for i in (1, 3, 5)) for k, v in LEG.items()}
INV = {v: k for k, v in RGB.items()}
def load(p): return np.array(Image.open(p).convert('RGBA'))
def save(a, p): Image.fromarray(a).save(p)
def ch(a, x, y):
    if not (0 <= x < a.shape[1] and 0 <= y < a.shape[0]) or a[y, x, 3] == 0: return '.'
    return INV.get(tuple(int(v) for v in a[y, x, :3]), '?')
def put(a, x, y, c, mode='over'):
    if not (0 <= x < a.shape[1] and 0 <= y < a.shape[0]): return
    if mode == 'behind' and a[y, x, 3] > 0: return
    if mode == 'onbody' and a[y, x, 3] == 0: return
    if c in '.X': a[y, x] = 0; return
    a[y, x, :3] = RGB[c]; a[y, x, 3] = 255
def apply(a, x0, y0, rows, mode='over'):
    n = 0
    for j, r in enumerate(rows):
        for i, c in enumerate(r):
            if c in '_ ': continue
            put(a, x0 + i, y0 + j, c, mode); n += 1
    return n
def dump(a, x0, y0, x1, y1):
    print('     ' + ''.join(str((x // 10) % 10) for x in range(x0, x1 + 1)))
    print('     ' + ''.join(str(x % 10) for x in range(x0, x1 + 1)))
    for y in range(y0, y1 + 1): print('%3d  ' % y + ''.join(ch(a, x, y) for x in range(x0, x1 + 1)))
def line(a, p0, p1, c, mode='over'):
    (x0, y0), (x1, y1) = p0, p1; n = max(abs(x1 - x0), abs(y1 - y0), 1)
    for k in range(n + 1): put(a, round(x0 + (x1 - x0) * k / n), round(y0 + (y1 - y0) * k / n), c, mode)
def spec(a, text, mode='over', protect=None):
    """render h4 kit layer text (@cuff / @limb / @katana / rows / grids) in FINAL coords and composite it"""
    import sys
    sys.path.insert(0, '/Users/waylonhuang/Documents/other/pixelart/swordswoman/tools/hybrid/h4')
    import kit
    g = kit.render_layer(kit.parse_layer(text))
    n = 0
    for y, x in zip(*np.nonzero(g != '.')):
        c = g[y, x]
        if c == '~': a[y, x] = 0; continue
        if protect is not None and protect[y, x]: continue
        if mode == 'behind' and a[y, x, 3] > 0: continue
        put(a, x, y, c); n += 1
    return n
