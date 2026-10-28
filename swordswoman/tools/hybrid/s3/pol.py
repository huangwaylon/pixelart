"""S3 polish helpers (exact-pixel). Palette by legend char."""
import json, subprocess, sys
import numpy as np
from PIL import Image
PAL = json.load(open('docs/palette.json'))['ramps']
def hx(h): return tuple(int(h[i:i+2], 16) for i in (1, 3, 5))
C = {'K': hx('#1a1220'), 'm': hx(PAL['skin'][0]), 's': hx(PAL['skin'][1]), 'S': hx(PAL['skin'][2]),
     'h': hx(PAL['hair'][0]), 'H': hx(PAL['hair'][1]), 'J': hx(PAL['hair'][2]),
     'v': hx(PAL['red'][0]), 'r': hx(PAL['red'][1]), 'R': hx(PAL['red'][2]), 'C': hx(PAL['red'][3]),
     'l': hx(PAL['leather'][1]), 'L': hx(PAL['leather'][2]), 'd': hx(PAL['dark'][1]),
     't': hx(PAL['steel'][0]), 'T': hx(PAL['steel'][1]), 'w': hx(PAL['steel'][2]),
     'e': hx(PAL['eye'][0]), 'E': hx(PAL['eye'][1]), 'p': hx(PAL['pink'][0]), 'P': hx(PAL['pink'][1])}
INV = {v: k for k, v in C.items()}
def load(p): return np.array(Image.open(p).convert('RGBA'))
def save(a, p): Image.fromarray(a).save(p)
def ch(a, x, y):
    if a[y, x, 3] == 0: return '.'
    return INV.get(tuple(a[y, x, :3]), '?')
def put(a, x, y, c):
    if c == '.': a[y, x] = 0
    else: a[y, x, :3] = C[c]; a[y, x, 3] = 255
def chars(a):
    H, W = a.shape[:2]
    return np.array([[ch(a, x, y) for x in range(W)] for y in range(H)])
def draw(inp, out, ops):
    r = subprocess.run(['.venv/bin/python', 'tools/hybrid/draw.py', inp, '--out', out] + ops, capture_output=True, text=True)
    if r.returncode: print(r.stdout, r.stderr); raise SystemExit(1)
    return r.stdout
def stamp_mask(meta_path, name_dir):
    m = json.load(open(meta_path))['s3']
    st = np.array(Image.open(f"hybrid/lock/pixel/head_{name_dir}.png").convert('RGBA'))[..., 3] > 0
    M = np.zeros((128, 128), bool)
    t, l = m['stamp_top'], m['stamp_left']
    M[t:t + st.shape[0], l:l + st.shape[1]] = st
    return M

DARK = {'r': 'v', 'R': 'r', 'C': 'R', 'v': 'v', 's': 'm', 'S': 's', 'm': 'm', 'l': 'K', 'L': 'l',
        'h': 'h', 'H': 'h', 'J': 'H', 'd': 'K', 'p': 'p', 'P': 'p'}
NOEDIT = set('KtTwEePp.?')
def body_pass(a, protect):
    """orphan merge, pale-skin tone-down, closed selective outline on the body edge (not the stamp)."""
    H, W = a.shape[:2]
    c = chars(a)
    # 1 orphans: no same-char 4-neighbour -> majority of 4-neighbours (body only)
    for y in range(1, H - 1):
        for x in range(1, W - 1):
            if protect[y, x] or c[y, x] in NOEDIT: continue
            n4 = [c[y-1, x], c[y+1, x], c[y, x-1], c[y, x+1]]
            if c[y, x] not in n4 and all(v != '.' for v in n4):
                vals = [v for v in n4 if v not in 'Kw']
                if vals:
                    best = max(set(vals), key=vals.count)
                    if vals.count(best) >= 2: put(a, x, y, best)
    c = chars(a)
    # 2 skin: S highlight is too pale on legs/arms -> s (keep S only as 1-px top highlights)
    for y in range(H):
        for x in range(W):
            if not protect[y, x] and c[y, x] == 'S' and y + 1 < H and c[y-1, x] in 'sS':
                put(a, x, y, 's')
    c = chars(a)
    # 3 selective outline: edge pixels (4-adjacent to transparency) of materials >= 2 px thick
    out = a.copy()
    for y in range(1, H - 1):
        for x in range(1, W - 1):
            v = c[y, x]
            if protect[y, x] or v in NOEDIT or v == '.': continue
            for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                if c[y + dy, x + dx] == '.':
                    inward = c[y - dy, x - dx]
                    if inward == '.' or inward in 'Kw': break
                    lit = (dy == -1 or dx == -1)
                    put(out, x, y, DARK.get(v, 'K') if lit else 'K')
                    break
    return out

def collar_bridge(a, M, maxgap=4):
    """fill the gap between the stamp's jaw and the body with the red collar band (design: 2-3 px red collar round the jaw)."""
    c = chars(a)
    ys, xs = np.nonzero(M)
    bot = ys.max()
    jaw = sorted(set(xs[ys >= bot - 1]))
    for x in jaw[1:-1]:
        ylow = max(ys[xs == x])
        gap = []
        for y in range(ylow + 1, min(127, ylow + 1 + maxgap)):
            if c[y, x] == '.' : gap.append(y)
            else: break
        else:
            gap = []          # nothing below within maxgap: do not grow a collar into the void
        for y in gap: put(a, x, y, 'R')
    return a

def ribbon_bridge(a, M, reach=4):
    """pink islands (scarf ribbons whose root the head stamp covered): link to the nearest body/stamp pixel with
    a 1 px pink_0 line if within reach, else drop tiny ones."""
    import math
    c = chars(a)
    pink = np.isin(c, ['p', 'P'])
    lab, sz = ccl(pink)
    other = (c != '.') & ~pink
    oy, ox = np.nonzero(other)
    for i in range(1, len(sz)):
        comp = lab == i
        yy, xx = np.nonzero(comp)
        touch = False
        for y, x in zip(yy, xx):
            if other[max(0, y-1):y+2, max(0, x-1):x+2].any(): touch = True; break
        if touch: continue
        best = None
        for y, x in zip(yy, xx):
            d = (oy - y) ** 2 + (ox - x) ** 2; j = int(np.argmin(d))
            if best is None or d[j] < best[0]: best = (d[j], x, y, ox[j], oy[j])
        if best and math.sqrt(best[0]) <= reach:
            _, x0, y0, x1, y1 = best
            n = max(abs(x1 - x0), abs(y1 - y0))
            for k in range(1, n):
                xi = round(x0 + (x1 - x0) * k / n); yi = round(y0 + (y1 - y0) * k / n)
                if c[yi, xi] == '.': put(a, xi, yi, 'p')
        elif sz[i] < 6:
            a[comp] = 0
    return a

def ccl(m):
    sys_path = __import__('sys').path
    if 'tools/hybrid' not in sys_path: sys_path.insert(0, 'tools/hybrid')
    import pixelize as PX
    return PX.label_cc(m, 8)

BOWCEL = {'S': (3, 0), 'SE': (8, 0), 'E': (5, 0), 'N': (1, 0)}
def find_head(a, d, guess, r=5):
    h = np.array(Image.open(f'hybrid/lock/pixel/head_{d}.png').convert('RGBA')).astype(int)
    m = h[..., 3] > 0; best = None
    gx, gy = guess
    for y in range(gy - r, gy + r + 1):
        for x in range(gx - r, gx + r + 1):
            sub = a[y:y + h.shape[0], x:x + h.shape[1]].astype(int)
            if sub.shape[:2] != h.shape[:2]: continue
            s = (np.abs(sub[m] - h[m]).sum(1) == 0).sum()
            if best is None or s > best[0]: best = (s, x, y)
    return best[1], best[2]
def bow_lag(a, meta_path, d, dx, dy):
    """shift the locked bow cel (hybrid/lock/pixel/bow_<d>.png) by (dx,dy) px for secondary lag."""
    if (dx, dy) == (0, 0) or d not in BOWCEL: return a
    m = json.load(open(meta_path))['s3']
    hx, hy = find_head(a, d, (m['stamp_left'], m['stamp_top']))
    b = np.array(Image.open(f'hybrid/lock/pixel/bow_{d}.png').convert('RGBA'))
    bm = b[..., 3] > 0
    ox, oy = hx + BOWCEL[d][0], hy + BOWCEL[d][1]
    H, W = bm.shape
    old = np.zeros((128, 128), bool); old[oy:oy + H, ox:ox + W] = bm
    new = np.zeros((128, 128), bool); new[oy + dy:oy + dy + H, ox + dx:ox + dx + W] = bm
    vac = old & ~new
    c = chars(a)
    for y, x in zip(*np.nonzero(vac)):
        outside = any(c[y + j, x + i] == '.' for i, j in ((1, 0), (-1, 0), (0, 1), (0, -1)))
        if outside and y < oy + 6: a[y, x] = 0
        else: put(a, x, y, 'h')
    sub = a[oy + dy:oy + dy + H, ox + dx:ox + dx + W]
    sub[bm] = b[bm]
    # re-close the outline above a lifted bow
    return a
