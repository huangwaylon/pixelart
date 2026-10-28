"""plib: char-grid helpers for the S2 polish pass (Claude hand pixel edits).
A sprite is a 128x128 numpy array of legend chars ('.' = transparent)."""
import json, os, sys
import numpy as np
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
import hylib as H  # noqa
PAL = H.palette()
LEG = {'K': 'outline', 'm': 'skin_0', 's': 'skin_1', 'S': 'skin_2', 'h': 'hair_0', 'H': 'hair_1', 'J': 'hair_2',
       'v': 'red_0', 'r': 'red_1', 'R': 'red_2', 'C': 'red_3', 'l': 'leather_1', 'L': 'leather_2', 'd': 'dark_1',
       't': 'steel_0', 'T': 'steel_1', 'w': 'steel_2', 'e': 'eye_0', 'E': 'eye_1', 'p': 'pink_0', 'P': 'pink_1',
       'u': 'purple_0'}
_PJ = json.load(open(os.path.join(HERE, '..', '..', '..', 'docs', 'palette.json')))


def _hex(n):
    if n == 'outline':
        return _PJ['outline']
    b, i = n.rsplit('_', 1)
    return _PJ['ramps'][b][int(i)]


HEX = {c: _hex(n) for c, n in LEG.items()}
RGB = {c: tuple(int(h[i:i + 2], 16) for i in (1, 3, 5)) for c, h in HEX.items()}
INV = {}
for _c in 'tTwemsSdhHJvrRClLKEpPu':
    INV.setdefault(RGB[_c], _c)
INV[RGB['K']] = 'K'


def load(p):
    a = np.array(Image.open(p).convert('RGBA'))
    g = np.full(a.shape[:2], '.', dtype='<U1')
    for y, x in zip(*np.nonzero(a[..., 3] >= 128)):
        g[y, x] = INV[tuple(a[y, x, :3])]
    return g


def save(g, p, zoom4=True):
    a = np.zeros(g.shape + (4,), np.uint8)
    for c, rgb in RGB.items():
        m = g == c
        a[m, :3] = rgb; a[m, 3] = 255
    Image.fromarray(a).save(p)
    if zoom4:
        Image.fromarray(a).resize((512, 512), Image.NEAREST).save(p[:-4] + '_4x.png')


def dump(g, x0, y0, x1, y1):
    """print a region with coordinates for hand editing"""
    print('     ' + ''.join(str((x // 10) % 10) for x in range(x0, x1)))
    print('     ' + ''.join(str(x % 10) for x in range(x0, x1)))
    for y in range(y0, y1):
        print(f'{y:4d} ' + ''.join(g[y, x0:x1]))


def put(g, x0, y0, rows, log=None, reason=''):
    """overlay rows of chars at (x0,y0); '_' keeps, '.' clears"""
    n = 0
    for dy, row in enumerate(rows):
        for dx, c in enumerate(row):
            if c == '_':
                continue
            y, x = y0 + dy, x0 + dx
            if g[y, x] != c:
                g[y, x] = c; n += 1
    if log is not None:
        log.append({'op': 'put', 'at': [x0, y0], 'rows': rows, 'px': n, 'reason': reason})
    return n


def to_rgba(g):
    a = np.zeros(g.shape + (4,), np.uint8)
    for c, rgb in RGB.items():
        m = g == c
        a[m, :3] = rgb; a[m, 3] = 255
    return a


def from_rgba(a):
    g = np.full(a.shape[:2], '.', dtype='<U1')
    for y, x in zip(*np.nonzero(a[..., 3] >= 128)):
        g[y, x] = INV[tuple(a[y, x, :3])]
    return g


def ops(g, op_list, log, reason):
    """run tools/hybrid/draw.py ops on the grid; logs every op + changed px count"""
    import draw as D
    cv = D.Canvas(to_rgba(g))
    for op in op_list:
        before = from_rgba(cv.a)
        D.run_op(cv, op, '.')
        n = int((from_rgba(cv.a) != before).sum())
        if log is not None:
            log.append({'op': op, 'px': n, 'reason': reason})
    g[:] = from_rgba(cv.a)


def setpx(g, pts, c, log=None, reason=''):
    n = 0
    for x, y in pts:
        if g[y, x] != c:
            g[y, x] = c; n += 1
    if log is not None:
        log.append({'op': 'set', 'pts': [list(p) for p in pts], 'to': c, 'px': n, 'reason': reason})


def erase_where(g, box, chars, log=None, reason='', keep=None):
    x0, y0, x1, y1 = box
    n = 0
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            if g[y, x] in chars and not (keep is not None and keep(x, y)):
                g[y, x] = '.'; n += 1
    if log is not None:
        log.append({'op': 'erase', 'box': list(box), 'chars': chars, 'px': n, 'reason': reason})
