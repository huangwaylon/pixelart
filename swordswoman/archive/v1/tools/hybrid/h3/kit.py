"""h3 KIT: the merged production compositor (S3 cels + S1 bodykit transforms + S6-style FX + lock2 heads).

A FRAME is built from hand-typed LAYERS (char grids in the STANDARD pixgrid legend) plus the lock2 head stamp:

  layer text (inside a cel module's LAYERS dict, or a frame's 'replace' / 'insert'):
      = X Y                 start a grid block at cell (X, Y); following lines starting with '|' are rows
      |..KRRK..             ('.' and '_' skip, 'X' clears what earlier layers painted)
      Y X0 STRING           one row segment
      @katana FX FY ANG LEN [hook=+1|-1] [hilt=5] [fist=s|none]
      @limb x,y,r x,y,r ... [tone=skin|red|dark|skinsh]   capsule chain, ramp-shaded, outlined
      @leg HIPX,HIPY KNEEX,KNEEY ANKX,ANKY [foot=KIND] [flip=1] [w=3] [strap=1]   3 px leg, strap row, heel
      @foot KIND X Y [flip=1]
      @ribbon x,y x,y ... [side=+1|-1] [over=1] [ol=1]     2 px pink scarf, tapered, K outline where it crosses red
      @px X Y C

  frame dict (anim specs):
      base='turn_SE'                cel module in tools/hybrid/h3/cels/
      drop=(names), replace={name: text}, add={name: text}, insert=[(pos, name, text)]  pos: back|front|before:L|after:L
      off={layer: (dx, dy)}         integer layer offsets (S1 bodykit: torso rides the bounce)
      xf={layer: [ops]}             per-layer pixel transforms, applied in order on the layer canvas:
                                     ('sq', y0, y1, n)      remove n rows evenly inside rows y0..y1 (squash, content above drops)
                                     ('st', y0, y1, n)      duplicate n rows evenly inside y0..y1 (stretch, content above rises)
                                     ('wd', x, n)           duplicate column x n times (widen to the right of x)
                                     ('sh', y0, y1, dx)     shear: row y0 moves dx, row y1 stays (lean)
                                     ('fl',)                nothing (placeholder)
      head=(dx, dy), expr='calm', tilt=0, sink=0, bow=(dx, dy), head_dir='SE'
      fx=[draw ops]  (tools/hybrid/draw.py strings, or ('smear', {...}) dicts for tools/hybrid/fx/smear.py)
      clean=True     per-material orphan merge on the body (head / eyes / katana / FX protected)
"""
import copy, importlib.util, math, os, subprocess, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import C, MAT, load, save, to_rgba, to_chars
import heads as HEADS

CELS = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cels')
N = 128


# ---------------------------------------------------------------- parsing
def parse_layer(text):
    """-> list of ops: ('grid', x, y, rows) | ('row', y, x0, s) | ('sp', args)"""
    ops, blk = [], None
    for raw in text.splitlines():
        line = raw.rstrip()
        s = line.strip()
        if not s or s.startswith('#'):
            continue
        if s.startswith('|'):
            blk[3].append(s[1:]); continue
        if s.startswith('='):
            x, y = s[1:].split()[:2]
            blk = ['grid', int(x), int(y), []]; ops.append(blk); continue
        if s.startswith('@'):
            ops.append(('sp', s[1:].split('#')[0].split())); continue
        y, x0, st = s.split(None, 2)
        ops.append(('row', int(y), int(x0), st.split('  #')[0].strip()))
    return ops


def load_cel(name):
    p = os.path.join(CELS, name + '.py')
    sp = importlib.util.spec_from_file_location('cel_' + name, p)
    m = importlib.util.module_from_spec(sp); sp.loader.exec_module(m)
    return m


# ---------------------------------------------------------------- canvas helpers
def blank(): return np.full((N, N), '.', dtype='<U1')


def put(g, x, y, c):
    if 0 <= x < N and 0 <= y < N:
        g[y, x] = c


def line_px(x0, y0, x1, y1):
    n = max(abs(x1 - x0), abs(y1 - y0), 1)
    return [(round(x0 + (x1 - x0) * k / n), round(y0 + (y1 - y0) * k / n)) for k in range(n + 1)]


def render_layer(ops, g=None):
    """paint ops onto char canvas g (new if None). 'X' writes a clear marker '~'."""
    g = blank() if g is None else g
    for op in ops:
        if op[0] == 'grid':
            _, x0, y0, rows = op
            for j, r in enumerate(rows):
                for i, ch in enumerate(r):
                    if ch in '._ ': continue
                    put(g, x0 + i, y0 + j, '~' if ch == 'X' else ch)
        elif op[0] == 'row':
            _, y, x0, st = op
            for i, ch in enumerate(st):
                if ch in '._ ': continue
                put(g, x0 + i, y, '~' if ch == 'X' else ch)
        else:
            special(g, op[1])
    return g


# ---------------------------------------------------------------- specials
def special(g, args):
    k = args[0]
    if k == 'px': put(g, int(args[1]), int(args[2]), args[3]); return
    if k == 'limb': return limb(g, args[1:])
    if k == 'ribbon': return ribbon(g, args[1:])
    if k == 'foot': return foot(g, args[1:])
    if k == 'leg': return leg(g, args[1:])
    if k == 'katana': return katana(g, args[1:])
    if k == 'cuff': return cuff(g, args[1:])
    raise SystemExit('unknown special ' + k)


def katana(g, args):
    """canonical katana held at fist (FX,FY), blade toward ANG deg (0 right, 90 down): 2 px diamond-wrap hilt,
    guard bar + crescent kagi (hook side), habaki, 2 px blade (steel_2 edge + steel_0 spine), 1 px tip."""
    fx, fy, ang, L = int(args[0]), int(args[1]), float(args[2]), int(args[3])
    opt = dict(v.split('=') for v in args[4:])
    hook = int(opt.get('hook', 1)); hl = int(opt.get('hilt', 5))
    base = [0, 18.435, 26.565, 45, 63.435, 71.565, 90]
    cands = [q * 90 + b for q in range(-4, 5) for b in base]
    if opt.get('snap', '1') == '1':
        ang = min(cands, key=lambda c: abs(c - ang))
    ux, uy = math.cos(math.radians(ang)), math.sin(math.radians(ang))
    px_, py_ = -uy, ux
    def P(t, s=0.0): return (round(fx + ux * t + px_ * s), round(fy + uy * t + py_ * s))
    own = set(); pts = []
    if opt.get('hiltonly', '0') != '2':
        for i in range(1, hl + 1):
            for s, c0 in ((0, 'd'), (1, 'R')):
                x, y = P(-i, s * 0.9)
                pts.append((x, y, ('R' if c0 == 'd' else 'd') if i % 2 else c0))
        pts += [P(2, s) + ('T',) for s in (-1.5, -0.5, 0.5, 1.5)]
        hk = P(2.6, 1.6 * hook); hk2 = P(1.4, 2.2 * hook)
        pts += [hk + ('T',), hk2 + ('T',)]
    for x, y, c in pts:
        put(g, x, y, c); own.add((x, y))
    for x, y in list(own):
        for ex, ey in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            q = (x + ex, y + ey)
            if q not in own and 0 <= q[0] < N and 0 <= q[1] < N and g[q[1], q[0]] == '.': put(g, q[0], q[1], 'K')
    b0, b1 = P(3, 0), P(L, 0)
    edge = line_px(b0[0], b0[1], b1[0], b1[1])
    so = (0, 1 if py_ > 0 else -1) if abs(ux) >= abs(uy) else (1 if px_ > 0 else -1, 0)
    for i, (x, y) in enumerate(edge):
        put(g, x, y, 'w')
        if i < len(edge) - 2: put(g, x + so[0], y + so[1], 't')
    if opt.get('fist', 's') != 'none':
        for x, y, c in ((fx, fy, 's'), (fx - 1, fy, 's'), (fx, fy + 1, 'm'), (fx - 1, fy + 1, 's')):
            put(g, x, y, c)
        for x, y in ((fx - 2, fy), (fx - 2, fy + 1), (fx - 1, fy + 2), (fx, fy + 2), (fx + 1, fy + 1)):
            if 0 <= x < N and 0 <= y < N and g[y, x] == '.': put(g, x, y, 'K')


def _caps(pts, H=N, W=N):
    yy, xx = np.mgrid[0:H, 0:W]
    M = np.zeros((H, W), bool); D = np.zeros((H, W), float)
    for (x0, y0, r0), (x1, y1, r1) in zip(pts, pts[1:]):
        vx, vy = x1 - x0, y1 - y0; L2 = max(vx * vx + vy * vy, 1e-6)
        t_ = np.clip(((xx - x0) * vx + (yy - y0) * vy) / L2, 0, 1)
        px, py = x0 + t_ * vx, y0 + t_ * vy
        r = r0 + (r1 - r0) * t_
        d = np.hypot(xx - px, yy - py)
        inside = d <= r
        side = ((xx - px) * 1.0 + (yy - py) * 0.4) / np.maximum(r, 0.5)
        newp = inside & ~M
        D[newp] = side[newp]; M |= inside
    return M, D


def limb(g, args):
    pts = [tuple(float(v) for v in p.split(',')) for p in args if ',' in p]
    opt = dict(v.split('=') for v in args if '=' in v)
    tone = opt.get('tone', 'skin')
    base, dark, light = {'skin': ('s', 'm', 'S'), 'red': ('R', 'r', 'C'), 'dark': ('d', 'K', 'd'),
                         'skinsh': ('m', 'm', 's'), 'redsh': ('r', 'v', 'R'), 'leather': ('l', 'K', 'L')}[tone]
    if len(pts) == 1: pts = pts * 2
    M, D = _caps(pts)
    for y, x in zip(*np.nonzero(M)):
        edge = any(not (0 <= x + ex < N and 0 <= y + ey < N) or not M[y + ey, x + ex]
                   for ex, ey in ((1, 0), (-1, 0), (0, 1), (0, -1)))
        if edge: g[y, x] = 'K' if opt.get('ol', '1') == '1' else dark
        elif D[y, x] > 0.35: g[y, x] = dark
        elif D[y, x] < -0.55 and opt.get('hl', '1') == '1': g[y, x] = light
        else: g[y, x] = base


def cuff(g, args):
    """@cuff X0,Y0 X1,Y1 WTOP WBOT [side=-1|1] : detached bell sleeve from the elbow point (X0,Y0) to the cuff
    centre (X1,Y1), width WTOP -> WBOT (flare), red ramp, lit on the upper-left, open dark mouth (v) at the cuff end,
    outlined. side = which edge is lit (-1 = left)."""
    (x0, y0), (x1, y1) = [tuple(float(v) for v in a.split(',')) for a in args[:2]]
    wt, wb = float(args[2]), float(args[3])
    opt = dict(v.split('=') for v in args[4:] if '=' in v)
    vx, vy = x1 - x0, y1 - y0; L = max(math.hypot(vx, vy), 1e-6); ux, uy = vx / L, vy / L
    nx, ny = -uy, ux
    yy, xx = np.mgrid[0:N, 0:N]
    t = ((xx - x0) * ux + (yy - y0) * uy) / L
    s = (xx - x0) * nx + (yy - y0) * ny
    half = (wt + (wb - wt) * np.clip(t, 0, 1) ** 1.6) / 2
    M = (t >= -0.02) & (t <= 1.0) & (np.abs(s) <= half)
    mouth = M & (t > 1.0 - 1.6 / L)
    for y, x in zip(*np.nonzero(M)):
        edge = any(not M[y + ey, x + ex] for ex, ey in ((1, 0), (-1, 0), (0, 1), (0, -1)))
        rel = s[y, x] / max(half[y, x], 0.5)
        lit_side = rel * (1 if nx < 0 else -1)              # +: toward screen-left
        if edge: g[y, x] = 'K'
        elif mouth[y, x]: g[y, x] = 'v'
        elif lit_side > 0.45: g[y, x] = 'C'
        elif lit_side < -0.35: g[y, x] = 'r'
        else: g[y, x] = 'R'


def ribbon(g, args):
    """2 px pink scarf along the node path (root first): pink_1 body + pink_0 shadow edge on `side`; the last
    3 px taper to 1 px. ol=1: a K outline pixel where the ribbon edge would touch red (reads over the dress)."""
    pts = [tuple(float(v) for v in p.split(',')) for p in args if ',' in p]
    opt = dict(v.split('=') for v in args if '=' in v)
    side = int(opt.get('side', 1)); w = int(opt.get('w', 2)); over = opt.get('over', '1') == '1'
    ol = opt.get('ol', '1') == '1'
    path = []
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        for p in line_px(round(x0), round(y0), round(x1), round(y1)):
            if not path or path[-1] != p: path.append(p)
    # pixel-perfect: drop L-corners
    pp = []
    for i, p in enumerate(path):
        if 0 < i < len(path) - 1 and pp:
            a, b = pp[-1], path[i + 1]
            if (a[0] == p[0] or a[1] == p[1]) and (b[0] == p[0] or b[1] == p[1]) and a[0] != b[0] and a[1] != b[1]:
                continue
        pp.append(p)
    path = pp
    n = len(path); mine = set()
    for i, (x, y) in enumerate(path):
        j0, j1 = max(0, i - 2), min(n - 1, i + 2)
        tx, ty = path[j1][0] - path[j0][0], path[j1][1] - path[j0][1]
        ox, oy = (side, 0) if abs(ty) >= abs(tx) else (0, 1)
        if not (0 <= x < N and 0 <= y < N): continue
        if g[y, x] == '.' or over: g[y, x] = 'P'; mine.add((x, y))
        if w >= 2 and i < n - 3:
            sx, sy = x + ox, y + oy
            if 0 <= sx < N and 0 <= sy < N and (g[sy, sx] == '.' or over): g[sy, sx] = 'p'; mine.add((sx, sy))
    if ol:
        for x, y in list(mine):
            for ex, ey in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                q = (x + ex, y + ey)
                if q in mine or not (0 <= q[0] < N and 0 <= q[1] < N): continue
                if MAT.get(g[q[1], q[0]]) == 'red': g[q[1], q[0]] = 'K'


FEET = {   # strappy heels; anchor = top-left; d straps, s skin peeks, K sole / heel point
    's':     ['KdsdK', 'KdddK', 'KdKdK', 'KK.KK'],
    'sf':    ['KdsdK.', 'KddddK', 'KdKKKK', 'KK....'],
    'se':    ['KdsdK.', 'KddddK', 'KdKddK', 'KK.KK.'],
    'sef':   ['.KdsdK', 'KddddK', 'KddKdK', '.KK.KK'],
    'e':     ['KdsdK..', 'KddddK.', 'KdKdddK', 'KK.KKK.'],
    'w':     ['..KdsdK', '.KddddK', 'KdddKdK', '.KKK.KK'],
    'etoe':  ['KdsK.', 'KddK.', '.KddK', '..KKK'],
    'wtoe':  ['.KsdK', '.KddK', 'KddK.', 'KKK..'],
    'toe':   ['KdK', 'KdK', 'KdK', '.K.'],
    'n':     ['KdddK', 'KdsdK', 'KdddK', 'KKKKK'],
    'ne':    ['KdddK.', 'KdsdK.', 'KddddK', 'KKKKK.'],
    'heelup': ['KdK.', 'KddK', '.KdK', '..K.'],
}


def foot(g, args):
    if ',' in args[1]: args = [args[0]] + args[1].split(',') + list(args[2:])
    kind, x0, y0 = args[0], int(args[1]), int(args[2])
    opt = dict(v.split('=') for v in args[3:] if '=' in v)
    pat = FEET[kind]
    if opt.get('flip') == '1': pat = [r[::-1] for r in pat]
    for j, row in enumerate(pat):
        for i, ch in enumerate(row):
            if ch != '.': put(g, x0 + i, y0 + j, ch)


def leg(g, args):
    """@leg HX,HY KX,KY AX,AY [foot=KIND fx=dx fy=dy] [w=3] [strap=1] [shade=r|l]
    3 px skin leg hip->knee->ankle (skin_1 body, skin_0 shadow column on the shade side, K outline), a dark_1 strap
    row 1 px above the ankle, then a heel stamp whose top-left is at (AX-2+fx, AY+1+fy)."""
    pts = [tuple(int(v) for v in a.split(',')) for a in args if ',' in a and '=' not in a]
    opt = dict(v.split('=') for v in args if '=' in v)
    w = int(opt.get('w', 3)); shade = opt.get('shade', 'r')
    r = (w / 2.0) + 0.05
    vert = all(abs(x1 - x0) <= abs(y1 - y0) for (x0, y0), (x1, y1) in zip(pts, pts[1:]))
    if vert:   # mostly vertical leg: exact w-px rows (crisp 3 px legs)
        path = []
        for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
            for q in line_px(x0, y0, x1, y1):
                if not path or path[-1] != q: path.append(q)
        M = np.zeros((N, N), bool); S_ = np.zeros((N, N), bool)
        for (x, y) in path:
            lo = x - (w - 1) // 2
            for k in range(w):
                if 0 <= lo + k < N and 0 <= y < N: M[y, lo + k] = True
            sx = lo + w - 1 if shade == 'r' else lo
            if 0 <= sx < N and 0 <= y < N: S_[y, sx] = True
    else:      # bent / horizontal segments: capsule of radius w/2 (thickness perpendicular to the limb)
        M, D = _caps([(float(x), float(y), r) for x, y in pts])
        S_ = (D > 0.3) if shade == 'r' else (D < -0.3)
    ring = np.zeros_like(M)
    for y, x in zip(*np.nonzero(M)):
        for ex, ey in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            q = (x + ex, y + ey)
            if 0 <= q[0] < N and 0 <= q[1] < N and not M[q[1], q[0]]: ring[q[1], q[0]] = True
    for y, x in zip(*np.nonzero(ring)):
        if g[y, x] == '.' or opt.get('force', '0') == '1': g[y, x] = 'K'
    for y, x in zip(*np.nonzero(M)):
        g[y, x] = 'm' if S_[y, x] else 's'
    ax, ay = pts[-1]
    if opt.get('strap', '1') == '1':
        for k in range(w):
            put(g, ax - (w - 1) // 2 + k, ay - 2, 'd')
    if 'foot' in opt:
        foot(g, [opt['foot'], str(ax - 2 + int(opt.get('fx', 0))), str(ay + 1 + int(opt.get('fy', -1)))] +
             (['flip=1'] if opt.get('flip') == '1' else []))


# ---------------------------------------------------------------- per-layer transforms (S1 bodykit)
def xform(g, ops):
    for op in ops:
        k = op[0]
        if k == 'sq':            # remove n rows evenly in y0..y1; content ABOVE moves down (feet stay)
            _, y0, y1, n = op
            rows = list(range(y0, y1 + 1))
            kill = [rows[int((i + 0.5) * len(rows) / n)] for i in range(n)]
            keep = [y for y in range(N) if y not in kill]
            out = blank()
            src = [y for y in keep]
            # rows below y1 stay, rows above shift down by the count of killed rows below them
            for y in range(N):
                if y in kill: continue
                sh_ = sum(1 for kk in kill if kk > y) if y <= y1 else 0
                if 0 <= y + sh_ < N: out[y + sh_] = g[y]
            g = out
        elif k == 'st':          # duplicate n rows evenly in y0..y1; content ABOVE moves up
            _, y0, y1, n = op
            rows = list(range(y0, y1 + 1))
            dup = [rows[int((i + 0.5) * len(rows) / n)] for i in range(n)]
            out = blank()
            for y in range(N):
                sh_ = -sum(1 for d in dup if d > y) if y <= y1 else 0
                if 0 <= y + sh_ < N: out[y + sh_] = g[y]
                if y in dup:
                    up = -sum(1 for d in dup if d >= y)
                    if 0 <= y + up < N: out[y + up] = g[y]
            g = out
        elif k == 'wd':          # duplicate column x n times; content RIGHT of x moves right
            _, x, n = op
            out = blank()
            out[:, :x + 1] = g[:, :x + 1]
            for i in range(n): out[:, x + 1 + i] = g[:, x]
            out[:, x + 1 + n:] = g[:, x + 1:N - n]
            g = out
        elif k == 'wdc':         # widen about column x: n cols duplicated, left part moves left by n//2
            _, x, n = op
            g = xform(g, [('wd', x, n), ('mv', -(n // 2), 0)])
        elif k == 'mv':
            _, dx, dy = op
            g = shift(g, dx, dy)
        elif k == 'sh':          # shear: row y0 moves dx, row y1 stays, linear
            _, y0, y1, dx = op
            out = g.copy()
            for y in range(min(y0, y1), max(y0, y1) + 1):
                s = int(round(dx * (y1 - y) / (y1 - y0))) if y1 != y0 else dx
                if s: out[y] = np.roll(g[y], s) if True else g[y]
            if y0 < y1:
                for y in range(0, y0): out[y] = np.roll(g[y], dx)
            g = out
        elif k == 'flip':        # NOT for bodies (LOCK): only FX / props
            g = g[:, ::-1].copy()
    return g


def shift(g, dx, dy):
    out = blank()
    H, W = g.shape
    ys = slice(max(0, dy), H + min(0, dy)); xs = slice(max(0, dx), W + min(0, dx))
    ys2 = slice(max(0, -dy), H + min(0, -dy)); xs2 = slice(max(0, -dx), W + min(0, -dx))
    out[ys, xs] = g[ys2, xs2]
    return out


def over(dst, src):
    m = src != '.'
    clr = src == '~'
    dst[m] = src[m]
    dst[clr] = '.'
    return dst


# ---------------------------------------------------------------- frame
def build(fs):
    """fs: frame dict (see module doc) -> (chars, info)"""
    cel = load_cel(fs['base'])
    if hasattr(cel, 'make'):
        order, texts = cel.make(fs.get('pose', {}))
        order = list(order); texts = dict(texts)
    else:
        order = list(cel.ORDER)
        texts = dict(cel.LAYERS)
    for nm, pos in fs.get('move', ()):
        order.remove(nm)
        if pos == 'back': order.insert(0, nm)
        elif pos == 'front': order.append(nm)
        elif pos.startswith('before:'): order.insert(order.index(pos[7:]), nm)
        elif pos.startswith('after:'): order.insert(order.index(pos[6:]) + 1, nm)
    for nm in fs.get('drop', ()):
        if nm in order: order.remove(nm)
    for nm, t in fs.get('replace', {}).items():
        texts[nm] = t
        if nm not in order: order.append(nm)
    for nm, t in fs.get('add', {}).items():
        texts[nm] = texts.get(nm, '') + '\n' + t
    for pos, nm, t in fs.get('insert', ()):
        texts[nm] = t
        if pos == 'back': order.insert(0, nm)
        elif pos == 'front': order.append(nm)
        elif pos.startswith('before:'): order.insert(order.index(pos[7:]), nm)
        elif pos.startswith('after:'): order.insert(order.index(pos[6:]) + 1, nm)
    hd = fs.get('head_dir', cel.HEAD[0])
    hx, hy = cel.HEAD[1], cel.HEAD[2]                     # top-left of the calm stamp
    dhx, dhy = fs.get('head', (0, 0))
    sink = fs.get('sink', 0)
    canvas = blank()
    owner = np.full((N, N), '', dtype=object)
    glob = fs.get('xf_all', [])
    for nm in order:
        if nm == 'HEAD':
            hg = HEADS.head(hd, fs.get('expr', 'calm'), fs.get('tilt', 0))
            X, Y = hx + dhx, hy + dhy + sink
            bx, by = fs.get('bow', (0, 0))
            br = HEADS.BOW_ROWS.get(hd, HEADS.BOW_ROWS.get(HEADS.MIRROR.get(hd, ''), 7))
            hgl = blank()
            bx, by = fs.get('bow', (0, 0))
            for j in range(hg.shape[0]):                     # dome + (original) top: the original top stays
                for i in range(hg.shape[1]):                 # under the shifted one so no holes open up
                    if hg[j, i] != '.': put(hgl, X + i, Y + j, hg[j, i])
            if (bx, by) != (0, 0):
                for j in range(br + 1):
                    for i in range(hg.shape[1]):
                        if hg[j, i] != '.': put(hgl, X + i + bx, Y + j + by, hg[j, i])
                if by > 0:                                   # bow dropped onto the dome: re-cut its bottom outline
                    pass
            for x in fs.get('xf', {}).get('HEAD', []): pass
            m = hgl != '.'
            canvas[m] = hgl[m]; owner[m] = 'HEAD'
            continue
        g = render_layer(parse_layer(texts[nm]))
        dx, dy = cel.OFF.get(nm, (0, 0)) if hasattr(cel, 'OFF') else (0, 0)
        ex = fs.get('off', {}).get(nm, (0, 0))
        ops = list(glob if nm not in fs.get('xf_skip', ()) else []) + list(fs.get('xf', {}).get(nm, []))
        g = xform(g, ops)
        g = shift(g, dx + ex[0], dy + ex[1])
        m = g != '.'
        canvas = over(canvas, g); owner[m] = nm
        owner[g == '~'] = ''
    canvas[canvas == '~'] = '.'
    info = dict(head=(hd, hx + dhx, hy + dhy + sink), owner=owner)
    return canvas, info


def autoclean(g, owner, protect_layers=('HEAD', 'katana', 'fx')):
    """per-material orphan merge on body pixels: a tone pixel with no same-tone 4-neighbour whose 4-neighbours are
    mostly the same material gets the majority tone; isolated non-K specks inside K regions are left alone."""
    H, W = g.shape
    prot = np.isin(owner, list(protect_layers)) | np.isin(g, list('eEwtTuK.'))
    for _ in range(2):
        c = g.copy()
        for y in range(1, H - 1):
            for x in range(1, W - 1):
                if prot[y, x]: continue
                v = c[y, x]
                n4 = [c[y - 1, x], c[y + 1, x], c[y, x - 1], c[y, x + 1]]
                if v in n4: continue
                same = [q for q in n4 if MAT.get(q) == MAT.get(v)]
                if len(same) >= 2:
                    g[y, x] = max(set(same), key=same.count)
                elif len([q for q in n4 if q != '.']) == 4:
                    others = [q for q in n4 if q not in 'K.']
                    if others: g[y, x] = max(set(others), key=others.count)
    return g


OK_ORPH = set('wmpTueE')      # tools/pixel/lint ORPHAN_OK: steel_2 skin_0 pink_0 steel_1 purple_0 eye_0 eye_1
NB8 = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]


def orphan_fix(g, passes=3):
    """lint-exact orphan removal (no same-colour 8-neighbour), sword px (steel + 1 px) excluded like metrics.py:
    a stray outline px with >= 5 empty neighbours is erased, otherwise the px takes the most common same-MATERIAL
    neighbour tone, else the most common non-outline neighbour tone."""
    H, W = g.shape
    steel = np.isin(g, list('tTw'))
    sw = steel.copy()
    sw[1:] |= steel[:-1]; sw[:-1] |= steel[1:]; sw[:, 1:] |= steel[:, :-1]; sw[:, :-1] |= steel[:, 1:]
    for _ in range(passes):
        ch = 0
        for y in range(1, H - 1):
            for x in range(1, W - 1):
                v = g[y, x]
                if v == '.' or v in OK_ORPH or sw[y, x]: continue
                nb = [g[y + a, x + b] for a, b in NB8]
                if v in nb: continue
                if v == 'K':
                    if nb.count('.') >= 5: g[y, x] = '.'; ch += 1; continue
                    cand = [q for q in nb if q not in '.']
                else:
                    cand = [q for q in nb if MAT.get(q) == MAT.get(v)] or [q for q in nb if q not in '.K']
                    if not cand: cand = [q for q in nb if q != '.']
                if cand:
                    g[y, x] = max(set(cand), key=cand.count); ch += 1
        if not ch: break
    return g


def lint_fix(g, owner, passes=2):
    """silhouette clean-up with the tools/pixel/lint rules: fill 1 px NOTCHES (empty px with >= 3 opaque
    4-neighbours) with outline; remove outline SPURS (>= 3 empty 4-neighbours) and removable outline L-corner
    DOUBLES. The head stamp, steel and FX tones are never touched."""
    H, W = g.shape
    prot = (owner == 'HEAD') if owner is not None else np.zeros((H, W), bool)
    prot = prot.copy(); prot[101:] = True                 # never touch the feet / ground contact rows
    for _ in range(passes):
        op = g != '.'
        n4 = np.zeros((H, W), int)
        n4[1:] += op[:-1]; n4[:-1] += op[1:]; n4[:, 1:] += op[:, :-1]; n4[:, :-1] += op[:, 1:]
        for y, x in zip(*np.nonzero(~op & (n4 >= 3))):
            if 0 < x < W - 1 and 0 < y < H - 1 and not prot[y, x]:
                nb = [g[y + a, x + b] for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1))]
                if sum(c in 'tTwpP' for c in nb) >= 2: continue
                g[y, x] = 'K'
        op = g != '.'
        t4 = 4 - (np.pad(op, 1)[2:, 1:-1].astype(int) + np.pad(op, 1)[:-2, 1:-1] + np.pad(op, 1)[1:-1, 2:] + np.pad(op, 1)[1:-1, :-2])
        for y, x in zip(*np.nonzero(op & (t4 >= 3))):
            if g[y, x] == 'K' and not prot[y, x]: g[y, x] = '.'
        op = g != '.'
        for y in range(1, H - 1):
            for x in range(1, W - 1):
                if g[y, x] != 'K' or prot[y, x]: continue
                for hx_ in (-1, 1):
                    for vy in (-1, 1):
                        if g[y, x + hx_] == 'K' and g[y + vy, x] == 'K':
                            d = g[y + vy, x + hx_]
                            if d != '.' and d != 'K' and g[y, x - hx_] == '.' and g[y - vy, x] == '.':
                                g[y, x] = '.'
    return g


def draw_ops(png_in, png_out, ops):
    if not ops: return
    r = subprocess.run(['.venv/bin/python', 'tools/hybrid/draw.py', png_in, '--out', png_out] + list(ops),
                       capture_output=True, text=True)
    if r.returncode:
        print(r.stdout, r.stderr); raise SystemExit(1)


def render(fs, chars=False):
    """frame dict -> RGBA (and info). Order: build -> autoclean -> post px -> whole-frame SHIFT -> FX (smear kit)."""
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'fx'))
    import smear as SM
    g, info = build(fs)
    if fs.get('clean', True): g = autoclean(g, info['owner'])
    for x, y, c in fs.get('post', []):
        put(g, x, y, c)
    cel = load_cel(fs['base'])
    sx, sy = getattr(cel, 'SHIFT', (0, 0))
    ex = fs.get('shift', (0, 0))
    sx += ex[0]; sy += ex[1]
    if (sx, sy) != (0, 0):
        g = shift(g, sx, sy)
        o2 = np.full((N, N), '', dtype=object)
        H = info['owner']
        ys, xs = np.nonzero(H != '')
        for y, x in zip(ys, xs):
            if 0 <= y + sy < N and 0 <= x + sx < N: o2[y + sy, x + sx] = H[y, x]
        info['owner'] = o2
    info['shift'] = (sx, sy)
    if fs.get('fx'):
        fx = []
        for nm, prm in fs['fx']:
            if nm == 'echo_self':
                prm = dict(prm); src = g.copy()
                if prm.pop('body_only', True):
                    src[np.isin(src, list('tTw'))] = '.'
                fx.append(('echo', dict(src=src, **prm)))
            else:
                fx.append((nm, prm))
        g = SM.apply(g, info['owner'], fx)
    if fs.get('clean', True):
        g = orphan_fix(g)
        g = lint_fix(g, info['owner'])
        g = orphan_fix(g)
    info['chars'] = g
    a = to_rgba(g)
    return (a, info)


# ---------------------------------------------------------------- parametric skirt (petal hem)
def skirt(g, args):
    """@skirt top=Y cx=X tw=W tips=x:y,x:y,... [slit=x:y:wl:wr] [shorts=Y] [lit=-1] [sway=dx] [slope=0.55]
    [wedge=5] [tone=front|back] [ol=1]
    Bell skirt from the waist row `top` (width tw centred on cx) to the petal TIPS (the hem points). Each tip is a
    point; between tips the hem rises (slope px per px), giving the iso_v5 petal hem. Shading: red_2 base,
    red_3 lit band on the upper-left edge and red_3 fold WEDGES rising from the lit-side tips, red_1 petal
    undersides and right third, red_0 creases above the notches and along the slit. The slit (x:y top,
    wl/wr widths at the hem) shows the black shorts down to row `shorts`, legs below."""
    o = dict(a.split('=') for a in args)
    top = int(o['top']); cx = float(o['cx']); tw = float(o['tw'])
    tips = [tuple(int(v) for v in t.split(':')) for t in o['tips'].split(',')]
    slope = float(o.get('slope', 0.55)); sway = float(o.get('sway', 0)); wl = int(o.get('wedge', 5))
    tips.sort()
    hem_max = max(t[1] for t in tips)
    xl0, xr0 = cx - tw / 2, cx + tw / 2
    xL, xR = tips[0][0], tips[-1][0]
    def edges(y):
        t = (y - top) / max(1, hem_max - top)
        f = t ** 0.75
        s = sway * t * t
        return xl0 + (xL - xl0) * f + s, xr0 + (xR - xr0) * f + s
    def hem_y(x):
        return max(ty - abs(x - tx) * slope for tx, ty in tips)
    M = np.zeros((N, N), bool)
    for y in range(top, hem_max + 1):
        a, b = edges(y)
        for x in range(int(math.floor(a)), int(math.ceil(b)) + 1):
            if a - 0.5 <= x <= b + 0.5 and y <= hem_y(x) + 0.3 and 0 <= x < N:
                M[y, x] = True
    slit = None
    if 'slit' in o:
        sx, sy, swl, swr = [int(v) for v in o['slit'].split(':')]
        slit = np.zeros_like(M)
        for y in range(sy, hem_max + 1):
            t = (y - sy) / max(1, hem_max - sy)
            a, b = sx - swl * t, sx + swr * t
            for x in range(int(math.floor(a)), int(math.ceil(b)) + 1):
                if a - 0.3 <= x <= b + 0.3 and 0 <= x < N: slit[y, x] = True
        shorts = int(o.get('shorts', sy + 4))
    lit = int(o.get('lit', -1))
    out = {}
    for y, x in zip(*np.nonzero(M)):
        a, b = edges(y)
        u = (x - a) / max(1, b - a)                         # 0 left .. 1 right
        c = 'R'
        if u > 0.72: c = 'r'
        hy = hem_y(x)
        if y >= hy - 1.2: c = 'r' if u > 0.25 else 'R'      # petal underside band
        if u < 0.12 and y < top + 7: c = 'C'
        for tx, ty in tips:                                  # fold wedges up from the tips
            dy = ty - y
            if 1 <= dy <= wl and abs(x - (tx + (cx - tx) * 0.12 * dy / wl)) <= max(0.5, (wl - dy) * 0.22):
                c = 'C' if tx < cx + 3 else 'r'
        out[(x, y)] = c
    # notch creases: just above the hem between tips
    for (t0, t1) in zip(tips, tips[1:]):
        nx = (t0[0] + t1[0]) / 2.0
        ny = hem_y(nx)
        for k in range(0, 3):
            p = (int(round(nx)), int(round(ny)) - k)
            if p in out: out[p] = 'v'
    if slit is not None:
        for y, x in zip(*np.nonzero(slit & M)):
            out[(x, y)] = 'd' if y <= shorts else None
        for (x, y), c in list(out.items()):                 # the overlapping panel edge: K + red_0
            if c is None or c == 'd': continue
            if slit[y, x - 1] if x > 0 else False:
                out[(x, y)] = 'K'
            elif x + 1 < N and slit[y, x + 1] and M[y, x + 1]:
                out[(x, y)] = 'v'
    keep = {p for p, c in out.items() if c is not None}
    for (x, y), c in out.items():
        if c is None: continue
        edge = any((x + ex, y + ey) not in keep for ex, ey in ((1, 0), (-1, 0), (0, 1), (0, -1)))
        top_edge = (x, y - 1) not in keep and y == top
        if edge and not top_edge and c != 'd' and o.get('ol', '1') == '1':
            # sel-out: lit upper-left edges keep a dark red, the rest K
            left_open = (x - 1, y) not in keep and (x + 1, y) in keep and (x, y + 1) in keep
            c = 'v' if (left_open and y < top + 4) else 'K'
        if c == 'd' and any((x + ex, y + ey) not in keep for ex, ey in ((0, 1),)):
            c = 'K'
        put(g, x, y, c)


_old_special = special
def special(g, args):  # noqa: F811
    if args[0] == 'skirt': return skirt(g, args[1:])
    return _old_special(g, args)


# ---------------------------------------------------------------- draped bell sleeve (raised / swinging arms)
def sleeve(g, args):
    """@sleeve EX,EY WX,WY DX,DY [w0=3] : detached bell sleeve on a posed forearm. Top edge runs along the forearm
    elbow (E) -> wrist (W); the open bell end hangs from the wrist by the drop vector D (gravity + drag), so the
    sleeve is a quad E_top, W_top, W+D, E_bot. red_3 lit band on the upper/left edge, red_2 body, red_1 lower third,
    red_0 open mouth along the wrist edge, K outline."""
    from PIL import Image, ImageDraw
    (ex, ey), (wx, wy), (dx, dy) = [tuple(float(v) for v in a.split(',')) for a in args[:3]]
    o = dict(a.split('=') for a in args[3:] if '=' in a)
    w0 = float(o.get('w0', 3))
    vx, vy = wx - ex, wy - ey; L = max(1e-6, math.hypot(vx, vy)); ux, uy = vx / L, vy / L
    nx, ny = -uy, ux
    if nx * dx + ny * dy < 0: nx, ny = -nx, -ny             # normal toward the hanging side
    hb = float(o.get('bell', w0 / 2 + 1.2))
    DL = max(1e-6, math.hypot(dx, dy)); qx, qy = -dy / DL, dx / DL     # bell mouth runs across the drop
    pts = [(ex - nx * 1.1, ey - ny * 1.1), (wx - nx * 1.3, wy - ny * 1.3), (ex + nx * 1.1, ey + ny * 1.1),
           (wx + dx + qx * hb, wy + dy + qy * hb), (wx + dx - qx * hb, wy + dy - qy * hb),
           (ex + dx * 0.3 + nx * 1.2, ey + dy * 0.3 + ny * 1.2)]
    # convex hull (monotone chain) -> no self-intersection
    P = sorted(set(pts))
    def cross(o_, a_, b_): return (a_[0] - o_[0]) * (b_[1] - o_[1]) - (a_[1] - o_[1]) * (b_[0] - o_[0])
    lo, up = [], []
    for q in P:
        while len(lo) >= 2 and cross(lo[-2], lo[-1], q) <= 0: lo.pop()
        lo.append(q)
    for q in reversed(P):
        while len(up) >= 2 and cross(up[-2], up[-1], q) <= 0: up.pop()
        up.append(q)
    hull = lo[:-1] + up[:-1]
    im = Image.new('L', (N, N), 0); ImageDraw.Draw(im).polygon(hull, fill=255, outline=255)
    M = np.array(im) > 0
    b1 = (wx + dx + qx * hb, wy + dy + qy * hb); b2 = (wx + dx - qx * hb, wy + dy - qy * hb)
    sx, sy = b2[0] - b1[0], b2[1] - b1[1]; SL = max(1e-6, sx * sx + sy * sy)
    for y, x in zip(*np.nonzero(M)):
        t = max(0, min(1, ((x - b1[0]) * sx + (y - b1[1]) * sy) / SL))
        dm = math.hypot(x - (b1[0] + t * sx), y - (b1[1] + t * sy))
        t2 = max(0, min(1, ((x - ex) * vx + (y - ey) * vy) / (L * L)))
        dt = (x - (ex + t2 * vx)) * nx + (y - (ey + t2 * vy)) * ny     # depth below the forearm line
        lit = (x - (ex + t2 * vx)) * (-1) + (y - (ey + t2 * vy)) * (-1)  # toward screen up-left
        edge = any(not (0 <= x + a_ < N and 0 <= y + b_ < N) or not M[y + b_, x + a_] for a_, b_ in ((1, 0), (-1, 0), (0, 1), (0, -1)))
        if edge: c = 'K'
        elif dm < 1.7: c = 'v'
        elif dt < 0.8 or lit > 1.6: c = 'C'
        elif dt > math.hypot(dx, dy) * 0.62: c = 'r'
        else: c = 'R'
        g[y, x] = c


_old_special2 = special
def special(g, args):  # noqa: F811
    if args[0] == 'sleeve': return sleeve(g, args[1:])
    return _old_special2(g, args)
