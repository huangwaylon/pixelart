#!/usr/bin/env python3
"""48px finisher: Gemini candidate frames (64 cell) -> locked, cleaned, FX'd animation + GIF/sheet.
fin48.py PLAN.json
plan: {"action", "name", "ms_default", "lift_scale", "x_scale", "frames": [{
    "src": "cand/af00_k0.png", "ms": 80, "head": "neutral|squash|stretch|lean|back|blink", "bow": [dx, dy],
    "head_dx"/"head_dy": stamp nudge, "dx"/"dy": body nudge, "lift": px (override guide lift), "meta": guide frame idx,
    "blade": 0 | {"hilt": [x, y] cell px (default r6 meta), "ang": deg (default meta), "len": 17, "behind": 0, "dx", "dy"},
    "fx": [{"t": "smear", ...}, ...], "shake": [dx, dy], "decrawl": 1}]}
Per frame: palette grid -> keep main body -> erase steel -> pin feet (FOOT - lift) + x pin (obi centre vs guide torso)
-> master head stamp (template-matched to Gemini head) -> procedural 2px katana -> outer-outline repair -> orphan clean
-> temporal de-crawl -> FX -> frames/fNN.png, gifs/<name>.gif (6x, #6e6e6e), sheets/<name>.png."""
import json, math, os, sys
import numpy as np
from PIL import Image
ROOT = '/Users/waylonhuang/Documents/other/pixelart/swordswoman'; A = ROOT + '/v2/anim_redraw'
PAL = {k: v[0] for k, v in json.load(open(ROOT + '/v2/pixel/palette.json'))['colors'].items()}
RGB = {k: tuple(int(v[i:i + 2], 16) for i in (1, 3, 5)) for k, v in PAL.items()}
CH = list(RGB); CARR = np.array([RGB[c] for c in CH])
PT, PS = (int(v) for v in os.environ.get('FIN_PAD', '0,0').split(','))   # tall cell for jumps: pad top/sides
FOOT, CELL = 59 + PT, 64 + 2 * PS
MASTER = A + '/m48/SE.png'
HEAD_ROWS = (10 + PT, 35 + PT)          # bow top .. chin outline in the master
DARK = set('#hDdr')


# ---------------------------------------------------------------- grid io
def to_grid(path):
    a = np.array(Image.open(path).convert('RGBA'))
    g = np.full(a.shape[:2], '.', dtype='<U1')
    op = a[..., 3] >= 128
    d = ((a[..., :3][:, :, None, :].astype(int) - CARR[None, None]) ** 2).sum(-1)
    g[op] = np.array(CH)[d.argmin(-1)][op]
    if g.shape == (64, 64) and (PT or PS):
        o = np.full((CELL, CELL), '.', dtype='<U1'); o[PT:PT + 64, PS:PS + 64] = g; g = o
    return g


def to_img(g, bg=None):
    a = np.zeros(g.shape + (4,), np.uint8)
    for c, rgb in RGB.items():
        mk = g == c; a[mk, :3] = rgb; a[mk, 3] = 255
    im = Image.fromarray(a)
    if bg:
        b = Image.new('RGBA', im.size, bg + (255,)); b.alpha_composite(im); im = b.convert('RGB')
    return im


def isin(g, s):
    return np.isin(g, list(s))


def comps(mask):
    from scipy import ndimage
    lab, n = ndimage.label(mask, structure=np.ones((3, 3)))
    return lab, n


def shift(g, dx, dy):
    o = np.full_like(g, '.'); H, W = g.shape
    ys, xs = np.nonzero(g != '.'); ny, nx = ys + dy, xs + dx
    ok = (ny >= 0) & (ny < H) & (nx >= 0) & (nx < W)
    o[ny[ok], nx[ok]] = g[ys[ok], xs[ok]]; return o


def line(x0, y0, x1, y1):
    pts = []; dx, dy = abs(x1 - x0), -abs(y1 - y0); sx = 1 if x0 < x1 else -1; sy = 1 if y0 < y1 else -1; e = dx + dy
    while True:
        pts.append((x0, y0))
        if x0 == x1 and y0 == y1: break
        e2 = 2 * e
        if e2 >= dy: e += dy; x0 += sx
        if e2 <= dx: e += dx; y0 += sy
    return pts


# ---------------------------------------------------------------- body prep
def keep_main(g, min_px=6):
    lab, n = comps(g != '.')
    if n <= 1: return g
    sizes = np.bincount(lab.ravel()); sizes[0] = 0; big = sizes.argmax()
    o = g.copy()
    for k in range(1, n + 1):
        if k != big and sizes[k] < max(min_px, sizes[big] * 0.04):
            o[lab == k] = '.'
    # ground lines: long thin horizontal runs at the bottom
    for y in range(o.shape[0] - 1, o.shape[0] - 8, -1):
        row = o[y] != '.'
        if row.sum() >= 14 and (o[y - 1] != '.').sum() <= row.sum() * 0.5:
            o[y] = '.'
    return o


def erase_steel(g):
    o = g.copy(); o[isin(o, 'mnkuU')] = '.'
    lab, n = comps(o == 'w')
    for k in range(1, n + 1):
        if (lab == k).sum() > 2: o[lab == k] = '.'
    for _ in range(3):                          # bare outline strands left by the erased blade
        H, W = o.shape; kill = []
        for y, x in zip(*np.nonzero(o == '#')):
            nb = o[max(0, y - 1):y + 2, max(0, x - 1):x + 2]
            if not ((nb != '.') & (nb != '#')).any(): kill.append((y, x))
        for y, x in kill: o[y, x] = '.'
    return o


HEADS = A + '/m48/heads'


def head_file(name):
    p = f'{HEADS}/{name}.txt'
    if not os.path.exists(p): return None
    L = open(p).read().split('\n'); org = [l for l in L if l.startswith('; origin')]
    ox, oy = [int(v) for v in org[0].split()[2:4]] if org else (14, 10)
    return ox, oy, [l for l in L if l and not l.startswith(';')]


def master_head(variant='neutral', bow=(0, 0)):
    M = to_grid(MASTER); y0, y1 = HEAD_ROWS
    used = None
    if variant in ('up', 'squash') and head_file(variant):
        fx0, fy0, rows = head_file(variant); used = variant
        M = M.copy(); M[y0:y1 + 1, PS + 14:PS + 46] = '.'
        for k, r in enumerate(rows):
            for x, c in enumerate(r[:32]):
                M[PT + fy0 + k, PS + fx0 + x] = c if c in RGB else '.'
    Hd = M[y0:y1 + 1].copy()
    while used and not (Hd[0] != '.').any(): Hd = Hd[1:]
    # drop collar/body pixels that sit in the chin rows (keep head colours only)
    Hd[~isin(Hd, 'hHjrREe123iIpw#')] = '.'
    xs = np.nonzero((Hd != '.').any(0))[0]; Hd = Hd[:, xs.min():xs.max() + 1]
    bowrows = 7                                       # rows 0..6 = bow
    bow = (bow[0], max(-1, min(2, bow[1])))          # never let the bow float off the skull
    if bow != (0, 0):
        b = Hd[:bowrows].copy(); rest = Hd.copy()
        bm = isin(b, 'rREe#') & ~isin(Hd[:bowrows], 'hH')
        bx0 = np.nonzero(isin(b[:5], 'rREe').any(0))[0].min() - 1; bm[:, :bx0] = False   # bun stays put
        rest[:bowrows][bm] = '.'
        for y in range(1, rest.shape[0]):                 # re-close the skull top under the removed bow
            for x in range(rest.shape[1]):
                if rest[y, x] in 'hH' and rest[y - 1, x] == '.': rest[y - 1, x] = '#'
        pad = 2; big = np.full((Hd.shape[0] + 2 * pad, Hd.shape[1] + 2 * pad), '.', dtype='<U1')
        big[pad:-pad, pad:-pad] = rest
        ys, xs = np.nonzero(bm)
        for y, x in zip(ys, xs):
            big[y + pad + bow[1], x + pad + bow[0]] = b[y, x]
        Hd = big; trim = (Hd != '.')
        ys, xs = np.nonzero(trim); Hd = Hd[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    if used:
        pass
    elif variant == 'squash':
        r = bowrows + 6; Hd = np.delete(Hd, r, axis=0)
    elif variant == 'stretch' and not head_file('neutral'):
        r = bowrows + 6; Hd = np.insert(Hd, r, Hd[r], axis=0)
    elif variant in ('lean', 'back') and not head_file('neutral'):
        s = 1 if variant == 'lean' else -1
        o = np.full((Hd.shape[0], Hd.shape[1] + 1), '.', dtype='<U1')
        cut = bowrows + 9
        for y in range(Hd.shape[0]):
            off = (1 if s > 0 else 0) if y < cut else (0 if s > 0 else 1)
            o[y, off:off + Hd.shape[1]] = Hd[y]
        Hd = o
    elif variant == 'blink':
        Hd = Hd.copy()
        for y in range(Hd.shape[0]):
            for x in range(Hd.shape[1]):
                if Hd[y, x] in 'iIw':
                    above = Hd[y - 1, x] if y else '.'
                    Hd[y, x] = '#' if above == '#' else '2'
        # eyes: the lash row stays, iris rows -> skin, one lid line
    return Hd


def head_match(g, Hd, guess):
    """slide master hair mask over candidate hair mask; best IoU near guess (oy, ox)."""
    hm = isin(Hd, 'hHj'); cm = isin(g, 'hHj')
    best = (-1, guess)
    for dy in range(-7, 8):
        for dx in range(-7, 8):
            oy, ox = guess[0] + dy, guess[1] + dx
            sub = np.zeros_like(cm)
            y0, x0 = max(0, oy), max(0, ox); y1, x1 = min(CELL, oy + Hd.shape[0]), min(CELL, ox + Hd.shape[1])
            if y1 <= y0 or x1 <= x0: continue
            sub[y0:y1, x0:x1] = hm[y0 - oy:y1 - oy, x0 - ox:x1 - ox]
            inter = (sub & cm).sum(); uni = (sub | cm).sum()
            s = inter / max(uni, 1) - 0.004 * (abs(dx) + abs(dy))
            if s > best[0]: best = (s, (oy, ox))
    return best


def stamp(g, Hd, oy, ox):
    o = g.copy(); hh, hw = Hd.shape; chin = oy + hh - 1
    box = np.zeros(g.shape, bool)
    box[max(0, oy - 1):min(CELL, chin + 2), max(0, ox - 2):min(CELL, ox + hw + 2)] = True
    top = np.zeros(g.shape, bool); top[:max(0, oy + 9)] = True
    above = np.zeros(g.shape, bool); above[:chin + 1] = True
    kill = (above & isin(o, 'hHjiIwp')) | (box & isin(o, '123#')) | (box & top & isin(o, 'rREe'))
    o[kill] = '.'
    hm = np.zeros(g.shape, bool)
    for y in range(hh):
        for x in range(hw):
            if Hd[y, x] != '.' and 0 <= oy + y < CELL and 0 <= ox + x < CELL:
                o[oy + y, ox + x] = Hd[y, x]; hm[oy + y, ox + x] = True
    # neck: Gemini skin below the chin outside the master neck columns -> dress/transparent; then master neck pixels
    M = to_grid(MASTER); hx0 = np.nonzero((M[HEAD_ROWS[0]:HEAD_ROWS[1] + 1] != '.').any(0))[0].min()
    neck = [(dy, x - hx0, M[HEAD_ROWS[1] + 1 + dy, x]) for dy in (0, 1) for x in range(CELL)
            if M[HEAD_ROWS[1] + 1 + dy, x] in '123']
    ncols = {ox + dx for _, dx, _ in neck}
    for y in range(chin + 1, min(CELL, chin + 4)):
        for x in range(max(0, ox - 3), min(CELL, ox + hw + 3)):
            if o[y, x] in '123' and x not in ncols:
                below = o[min(CELL - 1, y + 1), x]
                o[y, x] = below if below in 'rREe' else ('#' if below != '.' else '.')
    if not getattr(stamp, 'noneck', False):
        for dy, dx, c in neck:
            y, x = chin + 1 + dy, ox + dx
            if 0 <= y < CELL and 0 <= x < CELL and (o[y, x] != '.' or dy == 0):
                o[y, x] = c
    # stray outline/red specks hugging the stamp above the chin
    lab, n = comps((o != '.') & ~hm)
    for k in range(1, n + 1):
        mk = lab == k
        if mk.sum() <= 4 and np.nonzero(mk)[0].max() <= chin:
            o[mk] = '.'
    return o, hm


def body_ops(g, fr):
    """vsq: +n delete n rows at the waist (squash), -n duplicate the waist row (stretch); shear: top leans k px."""
    o = g.copy(); ys, xs = np.nonzero(o != '.')
    if not len(ys): return o
    n = fr.get('vsq', 0)
    if n:
        ob = np.nonzero(isin(o, 'dD').any(1))[0]; ob = ob[(ob > ys.min() + 15) & (ob < ys.max() - 4)]
        w = int(ob.mean()) if len(ob) else (ys.min() + ys.max()) // 2
        if n > 0:
            o = np.vstack([np.full((n, CELL), '.', dtype=o.dtype), np.delete(o, range(w - n, w), axis=0)])
        else:
            o = np.vstack([np.delete(o, range(0, -n), axis=0)[:w + n], np.repeat(o[w:w + 1], -n, 0), o[w:]])[:CELL]
            o = np.vstack([o[:w], o[w:]]) if o.shape[0] == CELL else o
    k = fr.get('shear', 0)
    if k:
        ys, xs = np.nonzero(o != '.'); top, bot = ys.min(), ys.max(); r = np.full_like(o, '.')
        for y in range(top, bot + 1):
            d = int(round(k * (bot - y) / max(1, bot - top)))
            row = o[y]
            if d > 0: r[y, d:] = row[:-d]
            elif d < 0: r[y, :d] = row[-d:]
            else: r[y] = row
        o = r
    return o


# ---------------------------------------------------------------- katana
def blade(g, hilt, ang, L=17, behind=False, protect=None, flash=False):
    o = g.copy(); hx, hy = hilt; c, s = math.cos(math.radians(ang)), math.sin(math.radians(ang))
    occ = (g != '.') if behind else np.zeros(g.shape, bool)
    if protect is not None: occ = occ | protect
    def P(x, y, col):
        if 0 <= x < CELL and 0 <= y < CELL and not occ[y, x]:
            o[y, x] = col
    steep = abs(s) > abs(c)
    # blade: 2px (light edge + dark edge) from guard to tip
    pts = line(int(round(hx + c * 2)), int(round(hy + s * 2)), int(round(hx + c * L)), int(round(hy + s * L)))
    lt, dk = ('w', 'w') if flash else ('w', 'n')
    for i, (x, y) in enumerate(pts):
        if steep: P(x, y, lt); P(x + 1, y, dk)
        else: P(x, y, lt); P(x, y + 1, dk)
    x, y = pts[-1]; P(x, y, 'w')
    # handle: 4px dark wrap behind the hilt
    for (x, y) in line(int(round(hx - c * 4)), int(round(hy - s * 4)), int(round(hx)), int(round(hy))):
        P(x, y, 'd')
    # guard: 3px perpendicular
    gx, gy = hx + c * 1, hy + s * 1
    for t in (-1, 0, 1):
        P(int(round(gx - s * t)), int(round(gy + c * t)), '#')
    return o


KAT_DIR = ROOT + '/v2/anim_cut/parts/common'
_KAT = {}


def kat_sprites():
    """16 pre-drawn katana sprites (anim_cut kat_DD.txt, pivot = grip). -> {d: (screen_angle_deg, grid, px, py)}"""
    if _KAT: return _KAT
    base = [(1, 0), (2, 1), (1, 1), (1, 2)]
    for d in range(16):
        vx, vy = base[d % 4]
        for _ in range(d // 4): vx, vy = -vy, vx
        ang = math.degrees(math.atan2(-vy, vx)) % 360          # y-up dir -> screen angle (y down)
        L = open(f'{KAT_DIR}/kat_{d:02d}.txt').read().split('\n')
        px, py = [int(v) for v in L[0].split()[2:4]]
        rows = [r for r in L[1:] if r and not r.startswith(';')]
        _KAT[d] = (ang, np.array([list(r) for r in rows]), px, py)
    return _KAT


def kat_dir(ang):
    K = kat_sprites(); a = ang % 360
    return min(K, key=lambda d: abs((K[d][0] - a + 180) % 360 - 180))


def kat_place(g, hilt, ang, behind=False, protect=None, flash=False):
    """paste the nearest-angle katana sprite with its grip pivot on `hilt`. behind: never over body px; never over the face."""
    o = g.copy(); a, S, px, py = kat_sprites()[kat_dir(ang)]
    for y in range(S.shape[0]):
        for x in range(S.shape[1]):
            c = S[y, x]
            if c == '.': continue
            X, Y = hilt[0] + x - px, hilt[1] + y - py
            if not (0 <= X < CELL and 0 <= Y < CELL): continue
            if protect is not None and protect[Y, X] and (behind or g[Y, X] in '123iIw'): continue
            if behind and g[Y, X] != '.': continue
            if c == '#' and g[Y, X] != '.' and not behind: continue   # sprite outline never cuts into the body
            o[Y, X] = 'w' if (flash and c == 'n') else c
    return o


def apply_legs(g, path, hm):
    """rows from a char-map (first line '; y0 N') replace grid rows y0.. (head stamp pixels are kept)."""
    L = open(path).read().split('\n'); y0 = int([l for l in L if l.startswith('; y0')][0].split()[2])
    rows = [l for l in L if l and not l.startswith(';')]
    o = g.copy()
    for k, r in enumerate(rows):
        y = y0 + k
        if y >= CELL: break
        r = (r + '.' * CELL)[:CELL]
        for x, c in enumerate(r):
            if not hm[y, x]: o[y, x] = c if c in RGB or c == '.' else o[y, x]
    return o


def find_hand(g, hm, near, maxd=12):
    """skin clusters (mitten hands) below the head, outside the stamp; return the centre nearest to `near`."""
    sk = isin(g, '123') & ~hm
    chin = np.nonzero(hm.any(1))[0].max(); sk[:chin + 2] = False
    lab, n = comps(sk); best = None
    for k in range(1, n + 1):
        ys, xs = np.nonzero(lab == k)
        if len(ys) > 8 or np.ptp(ys) > 3 or np.ptp(xs) > 3: continue      # legs / big skin areas are not hands
        if ys.max() >= FOOT - 3 and not isin(g[max(0, ys.min() - 1):ys.max() + 2, max(0, xs.min() - 1):xs.max() + 2], 'rREe').any(): continue
        cx, cy = xs.mean(), ys.mean(); d = math.hypot(cx - near[0], cy - near[1])
        if d <= maxd and (best is None or d < best[0]): best = (d, [cx, cy])
    return None if best is None else best[1]


def fit_blade(g, key_hand=None, key_ang=None):
    """Gemini katana -> (grip(x,y), angle deg, length) from the largest steel component (PCA line fit)."""
    st = isin(g, 'mnw')
    lab, n = comps(st)
    if n == 0: return None
    sizes = np.bincount(lab.ravel()); sizes[0] = 0; k = sizes.argmax()
    if sizes[k] < 5: return None
    ys, xs = np.nonzero(lab == k); pts = np.stack([xs, ys], 1).astype(float); c = pts.mean(0)
    u, sv, vt = np.linalg.svd(pts - c); d = vt[0]
    t = (pts - c) @ d; e0, e1 = c + d * t.min(), c + d * t.max()
    # grip end: nearer the keyed hand, else nearer dark hilt pixels
    if key_hand is not None:
        grip, tip = (e0, e1) if np.hypot(*(e0 - key_hand)) < np.hypot(*(e1 - key_hand)) else (e1, e0)
    else:
        dk = np.argwhere(isin(g, 'dDk'))[:, ::-1]
        dist = lambda e: np.min(np.hypot(*(dk - e).T)) if len(dk) else 0
        grip, tip = (e0, e1) if dist(e0) < dist(e1) else (e1, e0)
    ang = math.degrees(math.atan2(tip[1] - grip[1], tip[0] - grip[0]))
    return [float(grip[0]), float(grip[1])], ang, float(np.hypot(*(tip - grip)))


# ---------------------------------------------------------------- cleanup
def outer_outline(g, prot):
    """transparent px 4-adjacent to a light body px with no dark neighbour -> '#' (closes outline gaps)."""
    o = g.copy(); H, W = g.shape
    light = (g != '.') & ~isin(g, DARK | set('wnm')) & ~prot
    n = 0
    for y in range(H):
        for x in range(W):
            if g[y, x] != '.': continue
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                X, Y = x + dx, y + dy
                if 0 <= X < W and 0 <= Y < H and light[Y, X]:
                    o[y, x] = '#'; n += 1; break
    return o, n


def orphans(g, prot):
    o = g.copy(); H, W = g.shape; n = 0
    for y in range(H):
        for x in range(W):
            c = g[y, x]
            if c == '.' or prot[y, x] or c in 'w': continue
            nb = [g[Y, X] for Y in range(max(0, y - 1), min(H, y + 2)) for X in range(max(0, x - 1), min(W, x + 2))
                  if (Y, X) != (y, x)]
            if c not in nb:
                vals, cnt = np.unique(nb, return_counts=True); o[y, x] = vals[cnt.argmax()]; n += 1
    return o, n


def decrawl(cur, prev, prot):
    """revert isolated 1-3px changes (pixel shimmer) where the 5x5 neighbourhood is otherwise unchanged."""
    o = cur.copy(); diff = cur != prev; H, W = cur.shape; n = 0
    ys, xs = np.nonzero(diff & ~prot)
    for y, x in zip(ys, xs):
        win = diff[max(0, y - 2):y + 3, max(0, x - 2):x + 3]
        if win.sum() <= 3:
            o[y, x] = prev[y, x]; n += 1
    return o, n


# ---------------------------------------------------------------- FX
def fx_apply(g, fx, hist, prot):
    o = g.copy()
    def P(x, y, col, over=False):
        x, y = int(round(x)), int(round(y))
        if 0 <= x < CELL and 0 <= y < CELL and (over or o[y, x] == '.'):
            o[y, x] = col
    t = fx['t']
    if t == 'smear':          # crescent blade arc: centre c, radius r, from a0 to a1 deg, thickness th (tapers)
        cx, cy = fx['c']; r = fx['r']; a0, a1 = fx['a0'], fx['a1']; th = fx.get('th', 4); fl = fx.get('flat', 0.75)
        n = max(8, int(abs(a1 - a0) / 3))
        for i in range(n + 1):
            u = i / n; a = math.radians(a0 + (a1 - a0) * u)
            w = th * (0.25 + 0.75 * u)        # thin trailing end -> thick leading end
            for k in np.arange(0, w, 0.5):
                rr = r - k
                x, y = cx + rr * math.cos(a), cy + rr * math.sin(a) * fl
                col = 'w' if k < 1.0 else ('n' if k < w * 0.7 else 'm')
                if u < fx.get('dith', 0.35) and (int(x) + int(y)) % 2: continue      # dithered tail
                xi, yi = int(round(x)), int(round(y))
                if fx.get('over') and 0 <= xi < CELL and 0 <= yi < CELL and prot[yi, xi] and o[yi, xi] in '123iIw': continue   # never over the face (hair ok)
                P(x, y, col, over=fx.get('over', False))
    elif t == 'afterimage':   # copies of previous frames' silhouettes, dithered red
        for j, (dx, dy, col, dith) in enumerate(fx.get('ghosts', [[-5, 0, 'E', 0], [-10, 0, 'R', 1]])):
            src = hist[-1] if fx.get('src') == 'prev' and hist else g
            ys, xs = np.nonzero(src != '.')
            if dith == 'outline':              # hollow ghost: only the silhouette edge
                m = src != '.'; e = m & ~(np.roll(m, 1, 0) & np.roll(m, -1, 0) & np.roll(m, 1, 1) & np.roll(m, -1, 1))
                ys, xs = np.nonzero(e)
            for y, x in zip(ys + dy, xs + dx):
                if dith == 1 and (x + y) % 2: continue
                P(x, y, col)
    elif t == 'speed':        # horizontal speed lines behind the body
        for (x0, y0, L) in fx['lines']:
            for x in range(L): P(x0 - x, y0, 'w' if x < L // 2 else 'n')
    elif t == 'dust':         # puff: list of [x, y, r, stage]
        for (x0, y0, r, st) in fx['puffs']:
            for y in range(-r, r + 1):
                for x in range(-r - 1, r + 2):
                    d = (x / (r + 1)) ** 2 + (y / r) ** 2 if r else 0
                    if d <= 1.0:
                        if st >= 2 and d < 0.35: continue          # dissipating ring
                        P(x0 + x, y0 + y, 'u' if (y < 0 or d < 0.5) else 'U')
    elif t == 'spark':        # impact starburst: 3x3 white core, 4 long tapered rays (w->n), 4 short diagonals (e/E warm)
        x0, y0, r = fx['x'], fx['y'], fx.get('r', 3)
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                if abs(dx) + abs(dy) < 2: P(x0 + dx, y0 + dy, 'w', True)
        for k in range(2, r + 1):
            c = 'w' if k <= r * 0.6 else 'n'
            for ux, uy in ((1, 0), (-1, 0), (0, 1), (0, -1)): P(x0 + ux * k, y0 + uy * k, c, True)
        for k in range(1, max(2, r // 2 + 1)):
            c = 'e' if k == 1 else 'E'
            for ux, uy in ((1, 1), (-1, 1), (1, -1), (-1, -1)): P(x0 + ux * k, y0 + uy * k, c, True)
    elif t == 'lines':        # arbitrary motion lines [[x0,y0,x1,y1,col]]
        for (x0, y0, x1, y1, col) in fx['l']:
            for (x, y) in line(x0, y0, x1, y1): P(x, y, col)
    return o


# ---------------------------------------------------------------- guide helpers
def guide_info(gd, i):
    a = np.array(Image.open(f'{gd}/f{i:02d}.png').convert('RGBA'))[..., 3] > 0
    ys, xs = np.nonzero(a)
    y0, y1 = ys.min(), ys.max()
    band = (ys > y0 + (y1 - y0) * 0.45) & (ys < y0 + (y1 - y0) * 0.75)
    return dict(foot=y1, torso_x=xs[band].mean() if band.any() else xs.mean())


def main():
    plan = json.load(open(sys.argv[1])); act = plan['action']; name = plan['name']
    W = f'{A}/work48/{act}'; out = f'{W}/{plan.get("ver", "v1")}'; os.makedirs(out, exist_ok=True)
    mine = plan.get('mine', 1)
    if mine:
        mf = json.load(open(f'{W}/guide/frames.json'))['frames']
    else:
        gd = f"{ROOT}/v2/anim/guides/{plan.get('guide', act + '_SE')}"
        mf = json.load(open(gd + '/frames.json'))['frames']
        idle = guide_info(f'{ROOT}/v2/anim/guides/idle_SE', 0)
    M = to_grid(MASTER)
    m_obi = np.nonzero(isin(M, 'dD')[38 + PT:46 + PT])[1].mean()
    frames, durs, hist, log = [], [], [], []
    prev = None
    for i, fr in enumerate(plan['frames']):
        mi = fr.get('meta', i); md = mf[mi]
        src = fr['src'] if os.path.isabs(fr['src']) else f'{W}/{fr["src"]}'
        g0 = keep_main(to_grid(src))
        kh = None
        if mine and md.get('blade') is not None:
            kh = np.array(md['hand'])                       # rough: keyed hand (pre-pin coords ~ same panel)
        fb = fit_blade(g0, kh, md.get('blade') if mine else None)
        g = keep_main(erase_steel(g0))
        # ---- pin: feet to FOOT - lift; obi centre x to master obi x + root motion
        ys, xs = np.nonzero(g != '.')
        if mine:
            lift = md['lift'] * plan.get('lift_scale', 1.0); rx = md['pelvis_x'] - 30.5
        else:
            gi = guide_info(gd, mi); lift = max(0.0, (idle['foot'] - gi['foot'])) * plan.get('lift_scale', 1.0)
            rx = gi['torso_x'] - idle['torso_x']
        lift = fr.get('lift', lift)
        dy = int(round(FOOT - lift - ys.max())) + fr.get('dy', 0)
        ob = np.nonzero(isin(g, 'dD'))
        ocx = ob[1].mean() if len(ob[1]) > 5 else xs.mean()
        tx = m_obi + plan.get('x_scale', 1.0) * rx
        dx = int(round(tx - ocx)) + fr.get('dx', 0)
        g = shift(g, dx, dy)
        g = body_ops(g, fr)
        # ---- head stamp
        Hd = master_head(fr.get('head', md.get('head', 'neutral') if mine else 'neutral'),
                         tuple(fr.get('bow', md.get('bow', [0, 0]) if mine else [0, 0])))
        hair = np.nonzero(isin(g, 'hHj'))
        guess = (hair[0].min() - 7, int(round(hair[1].mean() - Hd.shape[1] / 2))) if len(hair[0]) else (10, 18)
        sc, (oy, ox) = head_match(g, Hd, guess)
        if plan.get('head_lock'):                         # head x locked to the pinned obi (no sideways boil)
            hx_m = np.nonzero((M[HEAD_ROWS[0]:HEAD_ROWS[1] + 1] != '.').any(0))[0].min()
            ox = int(round(hx_m + (tx - m_obi))) + plan.get('head_lock_dx', 0)
        oy += fr.get('head_dy', 0); ox += fr.get('head_dx', 0)
        hv = fr.get('head', md.get('head', 'neutral') if mine else 'neutral')
        if hv == 'lean' and head_file('neutral'): oy += 1; ox += 1
        g, hm = stamp(g, Hd, oy, ox)
        g = keep_main(g)
        if fr.get('legs'):                                   # hand-pixelled leg rows (Opus) replace the lower body
            lp = fr['legs'] if os.path.isabs(fr['legs']) else f'{W}/{fr["legs"]}'
            g = apply_legs(g, lp, hm)
        to_img(g).save(f'{out}/b{i:02d}.png')               # body stage (pre-katana) for leg redraws
        # ---- katana (grip = Gemini fist nearest the keyed hand; angle = keyed)
        bl = fr.get('blade', plan.get('blade', 1))
        if bl:
            bl = bl if isinstance(bl, dict) else {}
            hilt, ang = None, None
            if mine and md.get('blade') is not None:
                hilt = [md['hand'][0] + (m_obi - 30.5) + dx * 0, md['hand'][1]]
                hilt = [md['hand'][0] + (tx - m_obi - rx) + (m_obi - 30.5), md['hand'][1] - (59.5 - FOOT)]
                ang = md['blade']
            elif not mine and 'blade_cell_px' in md:
                h = md['blade_cell_px']['hilt']; hilt = [h[0] - 17 + m_obi - (idle['torso_x'] - 17), h[1] - 15]
                b = md['blade']; ang = math.degrees(math.atan2(b['tip'][1] - b['hilt'][1], b['tip'][0] - b['hilt'][0]))
            src_b = 'key'
            if fb is not None and not bl.get('keyed') and ang is not None:
                da = (fb[1] - ang + 180) % 360 - 180
                if abs(da) <= plan.get('fit_tol', 35):          # trust Gemini's grip; angle = mostly Gemini, nudged to key
                    hilt = [fb[0][0] + dx - math.cos(math.radians(fb[1])) * 1.5, fb[0][1] + dy - math.sin(math.radians(fb[1])) * 1.5]
                    ang = ang + da * plan.get('fit_w', 0.6); src_b = 'fit'
            if 'hilt' in bl: hilt = bl['hilt']
            if 'ang' in bl: ang = bl['ang']
            if hilt is not None and ang is not None:
                if src_b == 'key' and not bl.get('guide_hilt') and 'hilt' not in bl:
                    hd = find_hand(g, hm, hilt)
                    if hd is not None: hilt = hd
                hilt = [hilt[0] + bl.get('dx', 0), hilt[1] + bl.get('dy', 0)]
                if plan.get('kat', 1):
                    g = kat_place(g, [int(round(hilt[0])), int(round(hilt[1]))], ang + bl.get('rot', 0),
                                  behind=bl.get('behind', 0), protect=hm, flash=bl.get('flash', 0))
                else:
                    g = blade(g, [int(round(hilt[0])), int(round(hilt[1]))], ang + bl.get('rot', 0),
                              L=bl.get('len', plan.get('blade_len', 17)), behind=bl.get('behind', 0),
                              protect=hm if bl.get('behind', 0) else None, flash=bl.get('flash', 0))
                fr['_hilt'] = hilt; fr['_ang'] = round(ang, 1); fr['_bsrc'] = src_b
        steel = isin(g, 'wnm') & ~hm
        # ---- cleanup
        g, n_ol = outer_outline(g, hm | steel) if plan.get('outline', 1) else (g, 0)
        g, n_or = orphans(g, hm | steel)
        n_dc = 0
        if prev is not None and fr.get('decrawl', plan.get('decrawl', 0)):
            g, n_dc = decrawl(g, prev, steel)
        prev = g.copy(); hist.append(g.copy())
        to_img(g).save(f'{out}/c{i:02d}.png')
        # ---- FX (on a copy; FX never feed back into cleanup/decrawl)
        f = g.copy()
        for e in fr.get('fx', []) + (md.get('fx', []) if mine and not fr.get('nofx') else []):
            f = fx_apply(f, e, hist[:-1], hm)
        if fr.get('shake'):
            f = shift(f, *fr['shake'])
        to_img(f).save(f'{out}/f{i:02d}.png')
        frames.append(f); durs.append(fr.get('ms', md['ms']))
        log.append(dict(f=i, dx=dx, dy=dy, hilt=([round(float(v)) for v in fr['_hilt']] + [fr['_bsrc']]) if '_hilt' in fr else None,
                        head=[int(oy), int(ox), round(float(sc), 2)], ol=n_ol, orph=n_or, dc=n_dc))
    json.dump(log, open(f'{out}/log.json', 'w'))
    export(frames, durs, name)
    print(' '.join(f"{l['f']}:{l['dx']},{l['dy']} h{l['head'][2]} g{l['hilt']}" for l in log))


def export(frames, durs, name, S=6):
    frames = [f[max(0, PT - 16 if PT else 0):, PS:PS + 64] if (PT or PS) else f for f in frames]
    Hh, Ww = frames[0].shape
    ims = [to_img(f, (110, 110, 110)).resize((Ww * S, Hh * S), Image.NEAREST) for f in frames]
    os.makedirs(f'{A}/gifs', exist_ok=True); os.makedirs(f'{A}/sheets', exist_ok=True)
    ims[0].save(f'{A}/gifs/{name}.gif', save_all=True, append_images=ims[1:], duration=durs, loop=0, disposal=1)
    s3 = 3; cols = 4; rows = (len(frames) + cols - 1) // cols
    sh = Image.new('RGB', (cols * (Ww * s3 + 2), rows * (Hh * s3 + 2) + Hh + 4), (40, 40, 40))
    for k, f in enumerate(frames):
        sh.paste(to_img(f, (110, 110, 110)).resize((Ww * s3, Hh * s3), Image.NEAREST),
                 ((k % cols) * (Ww * s3 + 2), (k // cols) * (Hh * s3 + 2)))
    for k, f in enumerate(frames):                                 # 1x strip for readability
        sh.paste(to_img(f, (110, 110, 110)), (k * (Ww + 2), rows * (Hh * s3 + 2) + 2))
    sh.save(f'{A}/sheets/{name}.png')


if __name__ == '__main__':
    main()
