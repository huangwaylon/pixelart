"""SMEAR KIT (shared round-2 foundation; S3 owns it, S5 consumes it).  tools/hybrid/fx/smear.py

Everything works on CHAR grids (STANDARD pixgrid legend, '.' = empty) with an optional OWNER grid (layer name per
pixel; 'HEAD' pixels are protected: smears never cover the face stamp). Hard edges, palette-only, no outline on
smears (ANIM_DIRECTION 4). Each effect is a function; `apply(g, owner, fx)` runs a list of ('name', {params}).

  arc        blade-arc crescent on a cut-plane ellipse. FAR side behind the body (paints empty px only), NEAR side
             over the body (front=lower|upper|none|all), 1 px clear of the head. Monotone taper along the arc
             1 / 2 / 4 / 5-6 px (lead `lead`, capped at 7), one solid band: steel_2 rim on the outer edge over the
             leading 70 %, pink_1 body, pink_0 inner edge + the whole trailing 30 %. Optional thin pink_0 echo arc.
             The span runs from the k0 blade tip (a0, tail) to just short of the k2 tip (a1, lead).
  sliver     the impact-frame remnant: the leading `keep` fraction of an arc, thin (1-2 px), pink only.
  wisps      follow-through: 0-3 short pink_0 curls at the arc tail.
  limb       stretched-limb smear: the sleeve/cuff dragged back along a path (lead = the real cuff): tapered band in
             2-3 red tones (red_3 leading edge, red_2 body, red_1 tail) + an optional pink_0 hand echo.
  echo       multiple-limb / afterimage copies of a region (or the whole sprite) as flat silhouettes in a tone,
             offset back along the motion, behind the body; steps=[2,3] turns copies into scan-streak afterimages.
  stretch    vertical (or horizontal) stretch of a band of rows: legs + skirt elongated for take-off / dash.
  lines      motion lines: n parallel 1 px lines of length L along a direction, gap px apart, behind.
  dust       landing / contact dust puffs: steel_1 core + steel_0 underside clusters, sized by `stage` (0..2).
  spark      hit spark: steel_2 star (arm length r) + pink_1 burst ticks around it.
"""
import math
import numpy as np

N = 128
NB4 = ((1, 0), (-1, 0), (0, 1), (0, -1))


def _inb(x, y): return 0 <= x < N and 0 <= y < N


def head_guard(owner, pad=1):
    if owner is None: return np.zeros((N, N), bool)
    m = owner == 'HEAD'
    out = m.copy()
    for _ in range(pad):
        o2 = out.copy()
        o2[1:] |= out[:-1]; o2[:-1] |= out[1:]; o2[:, 1:] |= out[:, :-1]; o2[:, :-1] |= out[:, 1:]
        out = o2
    return out


def _paint(g, pts, guard, mode):
    """mode 'behind': only empty px; 'over': anything but the guard"""
    for (x, y), c in pts.items():
        if not _inb(x, y): continue
        if mode == 'behind' and g[y, x] != '.': continue
        if guard[y, x]: continue
        g[y, x] = c


def taper(f, lead=6.0, cap=7):
    """monotone thickness along the arc (f = 0 tail .. 1 lead): 1 -> 2 (30 %) -> 4 (65 %) -> 5..lead (90 %),
    then a short rounded lead end"""
    if f < 0.30: t = 1 + f / 0.30
    elif f < 0.65: t = 2 + 2 * (f - 0.30) / 0.35
    elif f < 0.90: t = 4 + (lead - 1 - 4 + 1) * (f - 0.65) / 0.25
    else: t = lead
    if f > 0.965: t *= max(0.35, 1 - (f - 0.965) / 0.035 * 0.65)   # blunt round lead
    return min(cap, t)


def arc_pixels(cx, cy, rx, ry, a0, a1, lead=6.0, cap=7, rim=True):
    """-> {(x,y): tone} for the crescent. Angles in degrees, screen space (0 = right, 90 = down); a0 = tail."""
    span = a1 - a0
    out = {}
    R = max(rx, ry) + 2
    for y in range(int(cy - R), int(cy + R) + 1):
        for x in range(int(cx - R), int(cx + R) + 1):
            u, v = (x - cx) / rx, (y - cy) / ry
            rho = math.hypot(u, v)
            if rho > 1.0 or rho < 0.2: continue
            ang = math.degrees(math.atan2(v, u))
            # map ang into the span direction
            f = None
            for k in range(-2, 3):
                a = ang + 360 * k
                ff = (a - a0) / span
                if 0 <= ff <= 1: f = ff; break
            if f is None: continue
            ar = math.radians(a0 + f * span)
            reff = math.hypot(rx * math.cos(ar), ry * math.sin(ar))
            d = (1 - rho) * reff
            t = taper(f, lead, cap)
            if d >= t: continue
            if f < 0.30: c = 'p'
            elif d < 1.0 and rim: c = 'w'
            elif d >= t - 1.0 and t >= 3: c = 'p'
            else: c = 'P'
            out[(x, y)] = c
    return out


def _front_pred(front, cy):
    if front == 'lower': return lambda x, y: y > cy
    if front == 'upper': return lambda x, y: y < cy
    if front == 'all': return lambda x, y: True
    if callable(front): return front
    return lambda x, y: False


def arc(g, owner, cx, cy, rx, ry, a0, a1, lead=6.0, cap=7, front='lower', echo=False, rim=True, clear_px=None):
    guard = head_guard(owner, 1)
    px = arc_pixels(cx, cy, rx, ry, a0, a1, lead, cap, rim)
    if echo:   # thin pink_0 echo arc, inset, over the leading half
        span = a1 - a0
        for k in range(0, 200):
            f = 0.45 + 0.5 * k / 199
            a = math.radians(a0 + f * span)
            t = taper(f, lead, cap) + 2
            reff = math.hypot(rx * math.cos(a), ry * math.sin(a))
            s = max(0.2, 1 - t / reff)
            p = (round(cx + rx * s * math.cos(a)), round(cy + ry * s * math.sin(a)))
            px.setdefault(p, 'p')
    fp = _front_pred(front, cy)
    fr = {p: c for p, c in px.items() if fp(*p)}
    bk = {p: c for p, c in px.items() if not fp(*p)}
    _paint(g, bk, guard, 'behind')
    _paint(g, fr, guard, 'over')
    return px


def sliver(g, owner, cx, cy, rx, ry, a0, a1, keep=0.35, thick=2, front='lower'):
    guard = head_guard(owner, 1)
    span = a1 - a0
    b0 = a1 - keep * span
    out = {}
    for y in range(int(cy - ry - 2), int(cy + ry + 3)):
        for x in range(int(cx - rx - 2), int(cx + rx + 3)):
            u, v = (x - cx) / rx, (y - cy) / ry
            rho = math.hypot(u, v)
            if rho > 1.0: continue
            ang = math.degrees(math.atan2(v, u))
            f = None
            for k in range(-2, 3):
                ff = (ang + 360 * k - b0) / (a1 - b0)
                if 0 <= ff <= 1: f = ff; break
            if f is None: continue
            ar = math.radians(b0 + f * (a1 - b0))
            d = (1 - rho) * math.hypot(rx * math.cos(ar), ry * math.sin(ar))
            t = 1 + (thick - 1) * f
            if d < t: out[(x, y)] = 'P' if (d < 1 and f > 0.4) else 'p'
    fp = _front_pred(front, cy)
    _paint(g, {p: c for p, c in out.items() if not fp(*p)}, guard, 'behind')
    _paint(g, {p: c for p, c in out.items() if fp(*p)}, guard, 'over')


def wisps(g, owner, pts):
    """pts: list of polylines [(x,y),...] -> 1 px pink_0 curls, behind"""
    guard = head_guard(owner, 1)
    out = {}
    for pl in pts:
        for (x0, y0), (x1, y1) in zip(pl, pl[1:]):
            n = max(abs(x1 - x0), abs(y1 - y0), 1)
            for k in range(n + 1):
                out[(round(x0 + (x1 - x0) * k / n), round(y0 + (y1 - y0) * k / n))] = 'p'
    _paint(g, out, guard, 'behind')


def _polyline(path):
    pts = []
    for (x0, y0), (x1, y1) in zip(path, path[1:]):
        n = max(abs(x1 - x0), abs(y1 - y0), 1)
        for k in range(n + 1):
            p = (x0 + (x1 - x0) * k / n, y0 + (y1 - y0) * k / n)
            pts.append(p)
    return pts


def limb(g, owner, path, w0=4.0, w1=1.0, tones='CRr', hand=None, mode='behind', ol_lead=True):
    """stretched-limb smear along `path` (lead first = the real cuff end, then back along the swing).
    Width w0 at the lead tapering to w1. Tone bands along the path: tones[0] for the leading third, then [1],
    [2]. K outline only on the leading third (trailing copies have no outline). hand=(x,y) -> pink_0 2x2 echo."""
    guard = head_guard(owner, 1)
    pts = _polyline(path)
    L = len(pts)
    M = {}
    for i, (px, py) in enumerate(pts):
        f = i / max(1, L - 1)
        r = (w0 + (w1 - w0) * f) / 2
        c = tones[0] if f < 0.34 else (tones[1] if f < 0.67 else tones[min(2, len(tones) - 1)])
        for y in range(int(py - r - 1), int(py + r + 2)):
            for x in range(int(px - r - 1), int(px + r + 2)):
                if math.hypot(x - px, y - py) <= r + 0.15 and (x, y) not in M:
                    M[(x, y)] = (c, f)
    out = {}
    for (x, y), (c, f) in M.items():
        edge = any((x + a, y + b) not in M for a, b in NB4)
        out[(x, y)] = 'K' if (edge and ol_lead and f < 0.34) else c
    if hand:
        hx, hy = hand
        for p in ((hx, hy), (hx + 1, hy), (hx, hy + 1), (hx + 1, hy + 1)): out.setdefault(p, 'p')
    _paint(g, out, guard, mode)


def echo(g, owner, src, offsets, tones, region=None, mode='behind', steps=None):
    """flat silhouette copies of src chars (region = (x0,y0,x1,y1) or None = whole) at offsets, one tone each.
    Painted behind (empty px only), far copies first."""
    guard = head_guard(owner, 0)
    m = src != '.'
    if region:
        x0, y0, x1, y1 = region
        r = np.zeros_like(m); r[y0:y1 + 1, x0:x1 + 1] = True; m &= r
    ys, xs = np.nonzero(m)
    steps = steps or [1] * len(offsets)
    for (dx, dy), c, st in sorted(zip(offsets, tones, steps), key=lambda t: -abs(t[0][0]) - abs(t[0][1])):
        # st > 1: scan-streak afterimage (every st-th row of the silhouette), reads as speed, never as a blob
        out = {(x + dx, y + dy): c for y, x in zip(ys, xs) if (y + dy) % st == 0}
        _paint(g, out, guard, mode)


def stretch(g, y0, y1, n, axis='y', keep_bottom=True):
    """duplicate n rows evenly inside rows y0..y1 (content above moves up when keep_bottom)"""
    rows = list(range(y0, y1 + 1))
    dup = [rows[int((i + 0.5) * len(rows) / n)] for i in range(n)]
    out = np.full_like(g, '.')
    for y in range(N):
        shift = -sum(1 for d in dup if d > y) if y <= y1 else 0
        if 0 <= y + shift < N: out[y + shift] = g[y]
        if y in dup:
            up = -sum(1 for d in dup if d >= y)
            if 0 <= y + up < N: out[y + up] = g[y]
    return out


def lines(g, owner, x, y, dx, dy, n, L, gap, tones='p', mode='behind', perp=None):
    """n motion lines starting at (x,y), direction (dx,dy) unit-ish, length L (list allowed), spaced `gap` px
    along the perpendicular (or `perp`)."""
    guard = head_guard(owner, 1)
    if perp is None: perp = (-dy, dx)
    out = {}
    for i in range(n):
        Li = L[i] if isinstance(L, (list, tuple)) else L
        sx, sy = x + perp[0] * gap * i, y + perp[1] * gap * i
        c = tones[i % len(tones)]
        for k in range(Li):
            out[(round(sx + dx * k), round(sy + dy * k))] = c
    _paint(g, out, guard, mode)


DUST = [  # stage 0 (contact), 1 (spread), 2 (fading)  — anchor = bottom-centre
    ['.TT.', 'TTTt', '.tt.'],
    ['..TT..', '.TTTT.', 'TTTTTt', '.tttt.'],
    ['.T..T.', 'T.TT.t', '.t..t.'],
]


def dust(g, owner, x, y, stage=1, flip=False, mode='over'):
    pat = DUST[stage]
    if flip: pat = [r[::-1] for r in pat]
    h = len(pat); w = len(pat[0])
    out = {}
    for j, r in enumerate(pat):
        for i, c in enumerate(r):
            if c != '.': out[(x - w // 2 + i, y - h + 1 + j)] = c
    _paint(g, out, head_guard(owner, 0), mode)


def spark(g, owner, x, y, r=3, ticks=True):
    out = {(x, y): 'w'}
    for k in range(1, r + 1):
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            out[(x + dx * k, y + dy * k)] = 'w' if k < r else 'P'
    out[(x + 1, y + 1)] = 'w'; out[(x - 1, y - 1)] = 'w'; out[(x + 1, y - 1)] = 'w'; out[(x - 1, y + 1)] = 'w'
    if ticks:   # burst ticks on the diagonals, 2 px, detached
        for dx, dy in ((1, 1), (-1, -1), (1, -1), (-1, 1)):
            for k in (r + 0, r + 1):
                out[(x + dx * k, y + dy * k)] = 'P' if k == r else 'p'
    _paint(g, out, head_guard(owner, 1), 'over')


def apply(g, owner, fx):
    g = g.copy()
    for name, p in fx:
        if name == 'arc': arc(g, owner, **p)
        elif name == 'sliver': sliver(g, owner, **p)
        elif name == 'wisps': wisps(g, owner, **p)
        elif name == 'limb': limb(g, owner, **p)
        elif name == 'echo': echo(g, owner, **p)
        elif name == 'lines': lines(g, owner, **p)
        elif name == 'dust': dust(g, owner, **p)
        elif name == 'spark': spark(g, owner, **p)
        elif name == 'px':
            for x, y, c in p['pts']:
                if _inb(x, y): g[y, x] = c
        else: raise SystemExit('unknown fx ' + name)
    return g
