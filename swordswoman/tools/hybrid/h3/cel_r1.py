"""Hand-typed pixel CELS (Claude pixel artist), composited in order, head stamp on top.

.cel text format (STANDARD pixgrid legend, '.' and '_' = skip):
    head: SE 49 41            # locked stamp hybrid/lock/pixel/head_<DIR>.png at top-left x y
    head_png: path.png        # optional alternative head cel (expression variant)
    [layer name] [dx dy]      # optional integer offset for the whole layer
    y x0 STRING               # one row segment
    ops:                      # draw.py ops after the head (one per line)
    pre:                      # draw.py ops before the head
Layers are painted in file order; later layers cover earlier ones. Row segments may repeat a y.
'X' in a row clears a pixel (erase what earlier layers painted). 'include: file.cel' pulls in layers.
"""
import sys, os, subprocess
import numpy as np
from PIL import Image
sys.path.insert(0, 'tools/hybrid/s3')
from pol import C, load, save, put

def parse(path, out=None, base_off=(0, 0)):
    out = out if out is not None else dict(layers=[], ops=[], pre=[], head=None, head_png=None)
    mode, cur = None, None
    for raw in open(path).read().splitlines():
        line = raw.split('#', 1)[0].rstrip() if not raw.lstrip().startswith(('ops:', 'pre:')) else raw.strip()
        if not line.strip(): continue
        s = line.strip()
        if s.startswith('include:'):
            parse(os.path.join(os.path.dirname(path), s.split(':', 1)[1].strip()), out); continue
        if s.startswith('head:'):
            d, x, y = s.split(':', 1)[1].split(); out['head'] = (d, int(x), int(y)); continue
        if s.startswith('base:'):
            a_ = s.split(':', 1)[1].split()
            out['base'] = dict(path=os.path.join(os.path.dirname(path), a_[0]), **dict(v.split('=') for v in a_[1:])); continue
        if s.startswith('head_png:'):
            out['head_png'] = s.split(':', 1)[1].strip(); continue
        if s == 'ops:': mode = 'ops'; continue
        if s == 'pre:': mode = 'pre'; continue
        if s.startswith('['):
            nm, _, rest = s[1:].partition(']')
            off = tuple(int(v) for v in rest.split()) if rest.strip() else (0, 0)
            cur = dict(name=nm, off=off, rows=[]); out['layers'].append(cur); mode = 'layer'; continue
        if mode in ('ops', 'pre'):
            out[mode].append(s); continue
        if s.startswith('@'):
            cur['rows'].append(('@', s[1:].split(), None)); continue
        y, x0, st = s.split(None, 2)
        cur['rows'].append((int(y), int(x0), st))
    return out

MATS = ['vrRC', 'msS', 'lL', 'hHJ', 'pP', 'd', 'tTw', 'eE']
def relight(a):
    """after a horizontal mirror the key light sits top-RIGHT: reverse the tone order inside every horizontal
    run of one material (outline K and transparency are run breaks), which puts it back top-left."""
    from pol import chars
    c = chars(a); out = a.copy()
    fam = {ch: i for i, m in enumerate(MATS) for ch in m}
    for y in range(a.shape[0]):
        x = 0
        while x < a.shape[1]:
            f = fam.get(c[y, x])
            if f is None or f in (6, 7): x += 1; continue
            x1 = x
            while x1 + 1 < a.shape[1] and fam.get(c[y, x1 + 1]) == f: x1 += 1
            n = x1 - x + 1; k = min(3, n // 3)
            if k:                                   # swap only the edge bands; interior folds stay mirrored
                seg = a[y, x:x1 + 1]
                out[y, x:x + k] = seg[n - k:][::-1]
                out[y, x1 + 1 - k:x1 + 1] = seg[:k][::-1]
            x = x1 + 1
    return out

def render(cel, layer_off=None):
    a = np.zeros((128, 128, 4), np.uint8)
    if cel.get('base'):
        b = cel['base']; src = parse(b['path'])
        skip = set(b.get('skip', '').split(','))
        src['layers'] = [L for L in src['layers'] if L['name'] not in skip]
        src['head'] = None; src['ops'] = []
        a = render(src)
        if 'mirror' in b:
            A = int(b['mirror']); m = np.zeros_like(a)
            for x in range(128):
                if 0 <= A - x < 128: m[:, A - x] = a[:, x]
            a = relight(m) if b.get('relight', '1') == '1' else m
    layer_off = layer_off or {}
    for L in cel['layers']:
        dx, dy = L['off']
        ex = layer_off.get(L['name'], (0, 0))
        dx, dy = dx + ex[0], dy + ex[1]
        for y, x0, st in L['rows']:
            if y == '@':
                special(a, x0, dx, dy); continue
            for i, ch in enumerate(st):
                x, yy = x0 + i + dx, y + dy
                if ch in '._' or not (0 <= x < 128 and 0 <= yy < 128): continue
                if ch == 'X': a[yy, x] = 0; continue
                put(a, x, yy, ch)
    tmp = '/tmp/_cel_%d.png' % os.getpid()
    save(a, tmp)
    if cel['pre']: draw(tmp, tmp, cel['pre'])
    a = load(tmp)
    if cel['head']:
        d, hx, hy = cel['head']
        h = np.array(Image.open(cel['head_png'] or f'hybrid/lock/pixel/head_{d}.png').convert('RGBA'))
        m = h[..., 3] > 0
        a[hy:hy + h.shape[0], hx:hx + h.shape[1]][m] = h[m]
    save(a, tmp)
    if cel['ops']: draw(tmp, tmp, cel['ops'])
    return load(tmp)

def line_px(x0, y0, x1, y1):
    n = max(abs(x1 - x0), abs(y1 - y0), 1)
    return [(round(x0 + (x1 - x0) * k / n), round(y0 + (y1 - y0) * k / n)) for k in range(n + 1)]

def special(a, args, dx, dy):
    """@katana FX FY ANG LEN [hook=+1|-1] [hilt=5] [fist=s|none] : canonical katana held at fist (FX,FY), blade
    toward ANG degrees (0 right, 90 down). Hilt: 2-px dark_1/red_2 diamond wrap, outlined; guard bar + crescent
    hook (kagi); habaki steel_1; blade 2 px (steel_2 edge, steel_0 spine), 1-px tip.
    @px X Y C : single pixel (after offsets)."""
    import math
    kind = args[0]
    if kind == 'px':
        put(a, int(args[1]) + dx, int(args[2]) + dy, args[3]); return
    if kind == 'limb':
        return limb(a, args[1:], dx, dy)
    if kind == 'ribbon':
        return ribbon(a, args[1:], dx, dy)
    if kind == 'foot':
        return foot(a, args[1:], dx, dy)
    fx, fy, ang, L = int(args[1]) + dx, int(args[2]) + dy, float(args[3]), int(args[4])
    opt = dict(v.split('=') for v in args[5:])
    hook = int(opt.get('hook', 1)); hl = int(opt.get('hilt', 5))
    # snap to clean pixel-line ratios (0, 1:3, 1:2, 1:1, 2:1, 3:1, 90 deg) so the rigid blade has even steps
    base = [0, 18.435, 26.565, 45, 63.435, 71.565, 90]
    cands = [q * 90 + b for q in range(-4, 5) for b in base]
    ang = min(cands, key=lambda c: abs(c - ang))
    ux, uy = math.cos(math.radians(ang)), math.sin(math.radians(ang))
    px_, py_ = -uy, ux                                   # perpendicular
    def P(t, s=0.0): return (round(fx + ux * t + px_ * s), round(fy + uy * t + py_ * s))
    H, W = a.shape[:2]
    def ok(x, y): return 0 <= x < W and 0 <= y < H
    hilt = []
    for i in range(1, hl + 1):
        for s, c0 in ((0, 'd'), (1, 'R')):
            x, y = P(-i, s * 0.9)
            hilt.append((x, y, ('R' if c0 == 'd' else 'd') if i % 2 else c0))
    blade = []
    b0, b1 = P(3, 0), P(L, 0)
    edge = line_px(b0[0], b0[1], b1[0], b1[1])
    if abs(ux) >= abs(uy): so = (0, 1 if py_ > 0 else -1)
    else: so = (1 if px_ > 0 else -1, 0)
    for i, (x, y) in enumerate(edge):
        blade.append((x, y, 'w'))
        if i < len(edge) - 2: blade.append((x + so[0], y + so[1], 't'))
    guard = [P(2, s) + ('T',) for s in (-1.5, -0.5, 0.5, 1.5)]
    hk = P(2.6, 1.6 * hook); hk2 = P(1.4, 2.2 * hook)
    own = set()
    for x, y, c in hilt + guard:
        if ok(x, y): put(a, x, y, c); own.add((x, y))
    for x, y in (hk, hk2):
        if ok(x, y): put(a, x, y, 'T'); own.add((x, y))
    for x, y in own.copy():                               # outline the hilt + guard only
        for ex, ey in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            q = (x + ex, y + ey)
            if q not in own and ok(*q) and a[q[1], q[0], 3] == 0: put(a, q[0], q[1], 'K')
    for x, y, c in blade:
        if ok(x, y): put(a, x, y, c)
    if opt.get('fist', 's') != 'none':
        for x, y, c in ((fx, fy, 's'), (fx - 1, fy, 's'), (fx, fy + 1, 'm'), (fx - 1, fy + 1, 's')):
            if ok(x, y): put(a, x, y, c)

def limb(a, args, dx, dy):
    """@limb x,y,r x,y,r ... [tone=skin] : capsule chain through the points (radius r, float), filled with the
    material ramp (shadow on the right/bottom third, 1 px light on the upper-left edge), K outline inside the
    edge. Painted over whatever is in the layer."""
    import math
    pts = [tuple(float(v) for v in p.split(',')) for p in args if ',' in p]
    opt = dict(v.split('=') for v in args if '=' in v)
    tone = opt.get('tone', 'skin')
    base, dark, light = {'skin': ('s', 'm', 'S'), 'red': ('R', 'r', 'C'), 'dark': ('d', 'K', 'd'),
                         'skinsh': ('m', 'm', 's')}[tone]
    H, W = a.shape[:2]
    M = np.zeros((H, W), bool); D = np.zeros((H, W), float)
    yy, xx = np.mgrid[0:H, 0:W]
    for (x0, y0, r0), (x1, y1, r1) in zip(pts, pts[1:]):
        x0 += dx; x1 += dx; y0 += dy; y1 += dy
        vx, vy = x1 - x0, y1 - y0; L2 = max(vx * vx + vy * vy, 1e-6)
        t_ = np.clip(((xx - x0) * vx + (yy - y0) * vy) / L2, 0, 1)
        px, py = x0 + t_ * vx, y0 + t_ * vy
        r = r0 + (r1 - r0) * t_
        d = np.hypot(xx - px, yy - py)
        inside = d <= r
        # signed side: + = right of travel direction in screen (normal (vy,-vx)/|v| rotated) -> use x offset
        side = ((xx - px) * 1.0 + (yy - py) * 0.4) / np.maximum(r, 0.5)
        newp = inside & ~M
        D[newp] = side[newp]; M |= inside
    for y, x in zip(*np.nonzero(M)):
        edge = any(not (0 <= x + ex < W and 0 <= y + ey < H) or not M[y + ey, x + ex]
                   for ex, ey in ((1, 0), (-1, 0), (0, 1), (0, -1)))
        if edge: put(a, x, y, 'K')
        elif D[y, x] > 0.35: put(a, x, y, dark)
        elif D[y, x] < -0.55 and opt.get('hl', '1') == '1': put(a, x, y, light)
        else: put(a, x, y, base)

def ribbon(a, args, dx, dy):
    """@ribbon x,y x,y ... [w=2] : pink scarf ribbon along the hand-placed node path (root first). 2 px: pink_1
    body with a pink_0 shadow edge on the side given by side=+1|-1 (screen x); the last 3 px taper to 1 px."""
    pts = [tuple(float(v) for v in p.split(',')) for p in args if ',' in p]
    opt = dict(v.split('=') for v in args if '=' in v)
    side = int(opt.get('side', 1)); w = int(opt.get('w', 2))
    path = []
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        for p in line_px(round(x0), round(y0), round(x1), round(y1)):
            if not path or path[-1] != p: path.append(p)
    n = len(path)
    H, W = a.shape[:2]
    over = opt.get('over') == '1'
    for i, (x, y) in enumerate(path):
        j0, j1 = max(0, i - 2), min(n - 1, i + 2)
        tx, ty = path[j1][0] - path[j0][0], path[j1][1] - path[j0][1]
        # perpendicular offset toward `side` (screen x sign); horizontal runs thicken downward
        ox, oy = (side, 0) if abs(ty) >= abs(tx) else (0, 1)
        x += dx; y += dy
        if not (0 <= x < W and 0 <= y < H): continue
        if a[y, x, 3] == 0 or over: put(a, x, y, 'P')
        if w >= 2 and i < n - 2:
            sx, sy = x + ox, y + oy
            if 0 <= sx < W and 0 <= sy < H and (a[sy, sx, 3] == 0 or over): put(a, sx, sy, 'p')

FEET = {   # strappy heels, anchor = top-left of the pattern; dark_1 straps, skin peeks, K sole
    'se':    ['KdddK.', 'KsdsdK', 'KdddddK', '.KKKKK'],
    'sef':   ['KdddK', 'KsdsdK', 'KddddK', '.KKKK'],
    'toe':   ['KddK', 'KsdK', '.KdK', '..KK'],
    'e':     ['KdmdK..', 'KddddK.', 'KdKdddK', 'KK.KKK.'],
    'en':    ['KdsdK..', 'KdsddK.', 'KdKddddK', 'KK.KKKK.'],
    'etoe':  ['KddK.', '.KddK', '..KdK', '...KK'],
    'point': ['KdK', 'KdK', '.KK'],
    's':     ['KdddK', 'KsdsK', 'KddddK', '.KKKK'],
}
def foot(a, args, dx, dy):
    """@foot KIND x y [flip=1]"""
    if ',' in args[1]:
        args = [args[0]] + args[1].split(',') + list(args[2:])
    kind, x0, y0 = args[0], int(args[1]) + dx, int(args[2]) + dy
    opt = dict(v.split('=') for v in args[3:] if '=' in v)
    pat = FEET[kind]
    if opt.get('flip') == '1': pat = [r[::-1] for r in pat]
    for j, row in enumerate(pat):
        for i, ch in enumerate(row):
            if ch != '.' and 0 <= x0 + i < 128 and 0 <= y0 + j < 128: put(a, x0 + i, y0 + j, ch)

def draw(inp, out, ops):
    r = subprocess.run(['.venv/bin/python', 'tools/hybrid/draw.py', inp, '--out', out] + list(ops),
                       capture_output=True, text=True)
    if r.returncode:
        print(r.stdout, r.stderr); raise SystemExit(1)

if __name__ == '__main__':
    save(render(parse(sys.argv[1])), sys.argv[2])
