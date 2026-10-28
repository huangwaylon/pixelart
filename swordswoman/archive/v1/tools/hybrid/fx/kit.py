"""S7 FX KIT (round 3, lead-owned, Claude-authored).  tools/hybrid/fx/kit.py

ONE palette-locked, parameterised smear / FX language for every action and direction.  S3 (run, dash) and S5
(slash, jump, run, dash) call this module instead of hand-rolling FX.  (The r2 `smear.py` stays as-is for old builds.)

Grids: 128x128 numpy '<U1' char grids in the STANDARD pixgrid legend ('.' = empty; w steel_2, T steel_1, t steel_0,
p pink_0, P pink_1, R/r/v/C reds, s/m skin, d dark_1, K outline ...).  `to_grid(rgba)` / `to_rgba(grid)` convert.
Every effect:
  - builds its own pixel set, keeps only what may be painted (mode 'behind' = empty px only; 'over' = anything),
    never touches `guard` (the face stamp, dilated 1 px) or `cut` (hand / hilt cut-mask, dilated 1 px);
  - then DE-CLUSTERS the visible pixels: no FX pixel is left without a same-tone 8-neighbour (cluster size >= 2,
    lint orphans 0), so the language stays crisp at 1x;
  - is hard-edged, solid, outline-free, no dither, no semi-alpha (ANIM_DIRECTION section 4);
  - returns the dict {(x, y): tone} it actually painted (for tests / metrics).

Colour roles (r2 DECISION, Pixel lead): smears = steel_2 RIM + pink_0 BODY, white (steel_2) is the only core/rim
light.  pink_1 is the RIBBON tone and is never a dominant smear tone (kit default: 0 px of pink_1 in any smear).
Dust = steel ramp.  Limb multiples keep the limb's own material, flattened (darker = fading, saint11).

  crescent(g, center, r, a0, a1, lead_px=6, tail_px=1, rim_px=1, echo=True, cut=None, front=None, ...)
  sliver(g, center, r, a0, a1, keep=0.35, thick=2, ...)            impact-frame remnant of the arc
  wisps(g, center, r, a0, a1, n=2, ...)                             follow-through: short broken arc pieces
  limb_multiples(g, src, mask, path, n=2, mode='multiples'|'stretch', ...)
  speed_bands(g, vector, n=3, lengths=(12, 9, 14), origins=None|'auto', body=mask, ...)
  afterimage(g, sil, offsets=((-6,0), (-12,0)), tone='p', ...)      2 hard multiples: full, then partial
  impact_star(g, c, core=3, cardinal=7, diag=3, strokes=4, shock=True, stage=0, ...)
  dust(g, feet=[(x, y, dir)], stage=1, grit=True, ...)              flat 3-row puffs attached to the feet
  streaks(g, feet=[(x, y)], vector=(0, 1), n=3, lengths=(6, 9, 5), ...)
The head-acting table and the ribbon / bow lag driver live in tools/hybrid/fx/acting.py.
Angles: degrees, screen space, 0 = +x (right), 90 = +y (down).  a0 = TAIL end of an arc, a1 = LEAD end (the blade).
"""
import json
import math
import os

import numpy as np

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..'))
N = 128
_PAL = json.load(open(os.path.join(ROOT, 'docs', 'palette.json')))
_R = _PAL['ramps']
LEGEND = {'K': _PAL['outline'], 'm': _R['skin'][0], 's': _R['skin'][1], 'S': _R['skin'][2],
          'h': _R['hair'][0], 'H': _R['hair'][1], 'J': _R['hair'][2],
          'v': _R['red'][0], 'r': _R['red'][1], 'R': _R['red'][2], 'C': _R['red'][3],
          'l': _R['leather'][1], 'L': _R['leather'][2], 'd': _R['dark'][1],
          't': _R['steel'][0], 'T': _R['steel'][1], 'w': _R['steel'][2],
          'e': _R['eye'][0], 'E': _R['eye'][1], 'p': _R['pink'][0], 'P': _R['pink'][1], 'u': _R['purple'][0]}
RGB = {k: tuple(int(v[i:i + 2], 16) for i in (1, 3, 5)) for k, v in LEGEND.items()}
INV = {v: k for k, v in RGB.items()}
MAT = {}
for _m, _cs in {'red': 'vrRC', 'skin': 'msS', 'hair': 'hHJ', 'leather': 'lL', 'dark': 'dK', 'steel': 'tTw',
                'eye': 'eE', 'pink': 'pP', 'purple': 'u'}.items():
    for _c in _cs: MAT[_c] = _m
# flattened multiples per material: (near body, near edge, far tone).  Darker = fading (saint11 motion blur).
FLAT = {'red': ('C', 'r', 'R'), 'skin': ('s', 'm', 'm'), 'hair': ('H', 'h', 'h'), 'leather': ('l', 'K', 'l'),
        'dark': ('d', 'K', 'd'), 'steel': ('w', 'T', 'T'), 'eye': ('E', 'e', 'e'), 'pink': ('p', 'p', 'p'),
        'purple': ('u', 'u', 'u')}
SMEAR_TONES = ('w', 'p')          # the smear language: steel_2 rim / core, pink_0 body
N8 = [(-1, -1), (0, -1), (1, -1), (-1, 0), (1, 0), (-1, 1), (0, 1), (1, 1)]
N4 = [(1, 0), (-1, 0), (0, 1), (0, -1)]


# ------------------------------------------------------------------------------------------------ grid utils
def blank():
    return np.full((N, N), '.', dtype='<U1')


def to_grid(a):
    """RGBA uint8 (128x128x4, locked palette) -> char grid"""
    g = blank()
    ys, xs = np.nonzero(a[..., 3] > 0)
    for y, x in zip(ys, xs):
        c = INV.get(tuple(int(v) for v in a[y, x, :3]))
        if c is None: raise ValueError(f'off-palette pixel at {x},{y}: {a[y, x, :3]}')
        g[y, x] = c
    return g


def to_rgba(g):
    a = np.zeros(g.shape + (4,), np.uint8)
    for c, rgb in RGB.items():
        m = g == c
        a[m, :3] = rgb; a[m, 3] = 255
    return a


def load(path):
    from PIL import Image
    return to_grid(np.array(Image.open(path).convert('RGBA')))


def save(g, path, zoom=None):
    from PIL import Image
    im = Image.fromarray(to_rgba(g))
    im.save(path)
    if zoom: im.resize((N * zoom, N * zoom), Image.NEAREST).save(path[:-4] + f'_{zoom}x.png')


def dilate(m, k=1):
    m = m.copy()
    for _ in range(k):
        o = m.copy()
        o[1:] |= m[:-1]; o[:-1] |= m[1:]; o[:, 1:] |= m[:, :-1]; o[:, :-1] |= m[:, 1:]
        m = o
    return m


def erode(m, k=1):
    return ~dilate(~m, k)


def _mask(x):
    if x is None: return np.zeros((N, N), bool)
    if isinstance(x, np.ndarray) and x.dtype == bool: return x
    m = np.zeros((N, N), bool)
    for item in x:                     # list of rects (x0,y0,x1,y1) or points (x,y)
        if len(item) == 4:
            x0, y0, x1, y1 = item; m[max(0, y0):y1 + 1, max(0, x0):x1 + 1] = True
        else:
            px, py = item
            if 0 <= px < N and 0 <= py < N: m[py, px] = True
    return m


def head_guard(owner, pad=1):
    if owner is None: return np.zeros((N, N), bool)
    return dilate(np.asarray(owner) == 'HEAD', pad)


def declust(pts, ctx=None):
    """No FX pixel without a same-tone 8-neighbour.  A lone pixel takes the tone of its FX neighbours (majority)
    or of a same-tone ctx (body) neighbour; if it has no FX neighbour at all it is dropped.  Repeats to a fixpoint."""
    pts = dict(pts)
    for _ in range(6):
        changed = False
        for (x, y), c in list(pts.items()):
            nb = [pts.get((x + i, y + j)) for i, j in N8]
            if c in nb: continue
            if ctx is not None and any(0 <= x + i < N and 0 <= y + j < N and ctx[y + j, x + i] == c for i, j in N8):
                continue
            tones = [t for t in nb if t]
            if not tones:
                del pts[(x, y)]
            else:
                pts[(x, y)] = max(set(tones), key=tones.count)
            changed = True
        if not changed: break
    return pts


def commit(g, pts, mode='behind', guard=None, cut=None, front=None, over_pred=None, clean=True):
    """Paint pts {(x,y): tone} into g.  mode 'behind' paints empty px only, 'over' paints anything.
    over_pred(x, y) -> True forces that pixel 'over' (front-plane part of an arc).  guard / cut px are never painted.
    Returns the painted dict."""
    gd = dilate(_mask(guard), 1) if guard is not None else np.zeros((N, N), bool)
    ct = dilate(_mask(cut), 1) if cut is not None else np.zeros((N, N), bool)
    vis = {}
    for (x, y), c in pts.items():
        if not (0 <= x < N and 0 <= y < N): continue
        if gd[y, x] or ct[y, x]: continue
        ov = mode == 'over' or (over_pred is not None and over_pred(x, y))
        if not ov and g[y, x] != '.': continue
        vis[(x, y)] = c
    if clean:
        vis = declust(vis, ctx=None)
    over_any = False
    for (x, y), c in vis.items():
        if g[y, x] != '.': over_any = True
        g[y, x] = c
    if over_any:
        heal(g, vis, gd)
    return vis


KEEP_ORPHAN = set('eEwu')          # eye tones, glints, the purple ornament may stand alone


def heal(g, fx, guard=None):
    """after an FX painted OVER the body: body pixels next to it that became orphans (a corset / outline sliver
    cut off by the smear) take the majority tone of their 8-neighbours, so the frame stays lint-clean."""
    gd = guard if guard is not None else np.zeros((N, N), bool)
    cand = set()
    for (x, y) in fx:
        for i, j in N8:
            q = (x + i, y + j)
            if q not in fx and 0 <= q[0] < N and 0 <= q[1] < N: cand.add(q)
    for _ in range(3):
        ch = False
        for x, y in cand:
            c = g[y, x]
            if c == '.' or c in KEEP_ORPHAN or gd[y, x]: continue
            nb = [g[y + j, x + i] for i, j in N8 if 0 <= x + i < N and 0 <= y + j < N]
            if c in nb: continue
            tones = [t for t in nb if t != '.']
            if not tones: g[y, x] = '.'; ch = True; continue
            g[y, x] = max(set(tones), key=tones.count); ch = True
        if not ch: break


def _line(x0, y0, x1, y1):
    n = max(abs(round(x1) - round(x0)), abs(round(y1) - round(y0)), 1)
    out = []
    for k in range(n + 1):
        p = (round(x0 + (x1 - x0) * k / n), round(y0 + (y1 - y0) * k / n))
        if not out or out[-1] != p: out.append(p)
    return out


def _angf(ang, a0, a1):
    """position of angle `ang` along the arc a0 -> a1 (either sense), 0..1, or None"""
    span = a1 - a0
    for k in range(-3, 4):
        f = (ang + 360 * k - a0) / span
        if 0 <= f <= 1: return f
    return None


def _ell(r):
    return (float(r), float(r)) if np.isscalar(r) else (float(r[0]), float(r[1]))


# ------------------------------------------------------------------------------------------------ (1) crescent
def moon_profile(f, lead, tail=1.0, span=150.0):
    """crescent-moon thickness along the arc (f 0 tail .. 1 lead): the profile of two offset circles, i.e.
    T = (cos((1-f)D) - cos D) / (1 - cos D) * (lead - tail) + tail with D = min(span, 170).  Smooth and monotone, so
    the inner edge rasterizes with even stair runs like the outer ellipse."""
    D = math.radians(min(170.0, max(40.0, abs(span))))
    return tail + (lead - tail) * (math.cos((1 - f) * D) - math.cos(D)) / (1 - math.cos(D))


def crescent_pts(center, r, a0, a1, lead_px=6, tail_px=1, rim_px=1, echo=True, echo_gap=2, echo_frac=0.5,
                 echo_px=2, tail_zone=0.2, cap=True, body='p', rim='w', ext=0):
    """-> (band pts, echo pts, depth map {(x,y): screen px in from the outer edge}).
    The outer edge is the blade-tip ellipse (centre, r).  The band grows inward with the crescent-moon profile
    (moon_profile, measured in SCREEN px so flat iso ellipses keep their thickness): tail_px at the tail (a0),
    lead_px at the lead (a1).  Both edges are smooth curves -> even stair runs.  steel_2 rim = the outer 1 px
    (rim_px over the leading 40 %), none in the trailing tail_zone (fade); body pink_0.  Echo = a thinner moon
    inside, echo_gap px clear of the band, over the leading echo_frac, max echo_px thick.  cap rounds the lead end."""
    cx, cy = center
    rx, ry = _ell(r)
    k = ry / rx
    span = a1 - a0
    sgn = 1 if span > 0 else -1
    Ro = rx - 0.42

    def sc(theta):
        t = math.radians(theta)
        return math.hypot(math.cos(t), k * math.sin(t))

    arc_len = abs(span) / 57.2958 * (rx + ry) / 2
    band, ech, depth = {}, {}, {}
    for y in range(int(cy - ry - 2), int(cy + ry) + 3):
        for x in range(int(cx - rx - 2), int(cx + rx) + 3):
            u, v = x - cx, (y - cy) / k
            rho = math.hypot(u, v)
            if rho > Ro or rho < 2: continue
            ang = math.degrees(math.atan2(v, u))
            f = _angf(ang, a0, a1 + sgn * ext)
            if f is None: continue
            f = min(1.0, f * (abs(span) + ext) / abs(span))
            dpx = (Ro - rho) * sc(ang)
            T = moon_profile(f, lead_px, tail_px, span)
            if cap:                                   # round blunt lead over the last ~lead_px of arc
                rem = (1 - f) * arc_len + ext * arc_len / abs(span) * 0
                cp = lead_px * 1.3
                if rem < cp: T *= 0.2 + 0.8 * math.sqrt(max(0.0, 1 - (1 - rem / cp) ** 2))   # rounded nose
            if dpx < T:
                # rim grows 1 -> rim_px toward the lead (0 px over the trailing 40 %), so the white edge and the
                # inner edge never step in lockstep (no ribbed / banded look)
                rp = 0 if f < max(tail_zone, 0.4) else 1 + (rim_px - 1) * min(1.0, (f - 0.4) / 0.45)
                c = rim if (dpx < rp and T >= 2.5) else body
                band[(x, y)] = c; depth[(x, y)] = dpx
            elif echo and f >= 1 - echo_frac and f < 0.985:
                fe = (f - (1 - echo_frac)) / echo_frac
                Te = moon_profile(fe, echo_px, 1.0, span * echo_frac)
                if T + echo_gap <= dpx < T + echo_gap + Te:
                    ech[(x, y)] = body
    return band, ech, depth


def crescent(g, center, r, a0, a1, lead_px=6, tail_px=1, rim_px=1, echo=True, cut=None, front=None, front_rows=2,
             guard=None, mode='behind', echo_gap=2, echo_frac=0.5, echo_px=2, tail_zone=0.2, body='p', rim='w', ext=0):
    """BLADE-ARC CRESCENT.  center (cx, cy), r = radius or (rx, ry) of the blade-tip path; a0 tail -> a1 lead.
    lead_px: thickness at the lead (max 6, ANIM 4: 'no smear wider than 6 px'); tail_px: at the tail.
    front(x, y) -> True where the arc is on the camera side of her body: there only the outer `front_rows` rows
    paint OVER the body (the bulk stays behind so the body still reads).  cut = mask / rects / points of the hand
    and hilt that must stay visible at the lead (dilated 1 px, never painted)."""
    lead_px = min(8, lead_px)                      # ANIM 4: 6 px is the slash cap; 8 only for the heavy overhead
    band, ech, depth = crescent_pts(center, r, a0, a1, lead_px, tail_px, rim_px, echo, echo_gap, echo_frac, echo_px,
                                    tail_zone, True, body, rim, ext)
    pts = dict(ech); pts.update(band)
    if front is not None:
        op = lambda x, y: front(x, y) and depth.get((x, y), 99) < front_rows
    else:
        op = None
    return commit(g, pts, mode, guard, cut, over_pred=op)


def sliver(g, center, r, a0, a1, keep=0.35, thick=2, guard=None, cut=None, front=None, mode='behind'):
    """impact frame (k2): the leading `keep` fraction of the k1 arc as a thin pink_0 sliver with a steel_2 rim at
    its lead (the 'slowly stabilize' frame).  Thickness 1 -> thick."""
    b0 = a1 - keep * (a1 - a0)
    band, _, depth = crescent_pts(center, r, b0, a1, lead_px=thick, tail_px=1, rim_px=1, echo=False,
                                  tail_zone=0.55)
    op = (lambda x, y: front(x, y) and depth.get((x, y), 99) < 1) if front else None
    return commit(g, band, mode, guard, cut, over_pred=op)


def wisps(g, center, r, a0, a1, n=2, guard=None, cut=None, mode='behind'):
    """follow-through (k3): the arc tail breaking up into n short 1-2 px pink_0 pieces (each >= 3 px long)."""
    out = {}
    cx, cy = center; rx, ry = _ell(r)
    for i in range(n):
        f0 = 0.15 + 0.8 * i / max(1, n)
        f1 = f0 + 0.55 / max(1, n)
        for k in range(24):
            f = f0 + (f1 - f0) * k / 23
            a = math.radians(a0 + (a1 - a0) * f)
            out[(round(cx + rx * math.cos(a)), round(cy + ry * math.sin(a)))] = 'p'
            if k > 8 and i == n - 1:
                out[(round(cx + (rx - 1) * math.cos(a)), round(cy + (ry - 1) * math.sin(a)))] = 'p'
    return commit(g, out, mode, guard, cut)


# ------------------------------------------------------------------------------------------------ (2) limbs
def _sample_path(path, n):
    """n points evenly along a polyline of offsets (first = nearest to the real limb)"""
    if n == 1: return [path[-1]]
    L = [0.0]
    for (x0, y0), (x1, y1) in zip(path, path[1:]): L.append(L[-1] + math.hypot(x1 - x0, y1 - y0))
    out = []
    for i in range(n):
        s = L[-1] * (i + 1) / n
        for k in range(1, len(L)):
            if L[k] >= s - 1e-9:
                t = (s - L[k - 1]) / max(1e-9, L[k] - L[k - 1])
                out.append((round(path[k - 1][0] + (path[k][0] - path[k - 1][0]) * t),
                            round(path[k - 1][1] + (path[k][1] - path[k - 1][1]) * t)))
                break
    return out


def limb_mask(src, region=None, chars=None, owner=None, layers=None):
    """helper: a limb's pixel mask from a grid: bbox region (x0,y0,x1,y1), material chars (e.g. 'vrRCK') and / or
    owner layer names."""
    m = src != '.'
    if region is not None:
        x0, y0, x1, y1 = region
        r = np.zeros((N, N), bool); r[y0:y1 + 1, x0:x1 + 1] = True; m &= r
    if chars is not None: m &= np.isin(src, list(chars))
    if owner is not None and layers is not None: m &= np.isin(np.asarray(owner), list(layers))
    return m


def _majority_mat(src, m):
    vals = [MAT.get(c, 'red') for c in src[m] if c != 'K']
    return max(set(vals), key=vals.count) if vals else 'red'


def _moved(m, d):
    o = np.zeros((N, N), bool); dx, dy = d
    ys, xs = np.nonzero(m)
    k = (ys + dy >= 0) & (ys + dy < N) & (xs + dx >= 0) & (xs + dx < N)
    o[ys[k] + dy, xs[k] + dx] = True
    return o


def limb_multiples(g, src, mask, path, n=2, mode='multiples', mat=None, guard=None, cut=None, paint='behind',
                   erode_tail=2, gap=1):
    """MULTIPLE-LIMB or STRETCHED-LIMB smear for fast swings and run legs.
    src/mask: the limb pixels (from the frame before FX).  path: offsets (dx, dy) BACK along the motion, nearest
    first.  'multiples': n hard flat copies along the path - near = the material's body tone, farther = its
    darker fading tone, each `gap` px clear of the nearer one and of the body (they read as separate limbs, never
    a blob).  'stretch': the limb swept along the path into ONE elongated shape narrowing toward the tail
    (erode_tail px): body tone over the near half, darker fading tone over the far half.  No outline.  Behind."""
    mat = mat or _majority_mat(src, mask)
    nb, ne, ft = FLAT.get(mat, FLAT['red'])
    pts = {}
    body = g != '.'
    if mode == 'multiples':
        offs = _sample_path(path, n)
        taken = body.copy()
        for i, d in enumerate(offs):
            m = _moved(mask, d)
            if i > 0 and m.sum() > 24: m = erode(m, 1)
            m &= ~dilate(taken, gap) if i > 0 else ~taken
            for y, x in zip(*np.nonzero(m)): pts[(x, y)] = nb if i == 0 else ft
            taken |= m
    else:
        L = 0.0; steps = []
        for (x0, y0), (x1, y1) in zip([(0, 0)] + list(path), list(path)):
            seg = max(1, round(math.hypot(x1 - x0, y1 - y0)))
            for k in range(1, seg + 1):
                steps.append((L + k, round(x0 + (x1 - x0) * k / seg), round(y0 + (y1 - y0) * k / seg)))
            L += seg
        for s_, dx, dy in reversed(steps):            # far first, near overwrites
            m = _moved(mask, (dx, dy))
            e = int(round(erode_tail * s_ / max(1.0, L)))
            if e and erode(m, e).any(): m = erode(m, e)
            tone = nb if s_ <= L * 0.5 else ft
            for y, x in zip(*np.nonzero(m)):
                if not mask[y, x]: pts[(x, y)] = tone
    return commit(g, pts, paint, guard, cut)


# ------------------------------------------------------------------------------------------------ (3) speed bands
def _norm(v):
    L = math.hypot(*v) or 1.0
    return (v[0] / L, v[1] / L)


def _perp_up(v):
    """perpendicular pointing up-screen (the lit side gets the rim)"""
    p = (-v[1], v[0])
    if p[1] > 0 or (p[1] == 0 and p[0] > 0): p = (-p[0], -p[1])
    return p


def auto_origins(body, vector, n, fr=(0.22, 0.42, 0.62, 0.82), gap=2):
    """band roots on the TRAILING silhouette edge of `body` (mask): n rows (horizontal-ish travel) or columns,
    spread over the body; root = trailing-most body px + gap px along the band vector."""
    v = _norm(vector)
    ys, xs = np.nonzero(body)
    out = []
    horiz = abs(v[0]) >= abs(v[1])
    lo, hi = (ys.min(), ys.max()) if horiz else (xs.min(), xs.max())
    for i in range(n):
        q = round(lo + (hi - lo) * fr[i % len(fr)])
        if horiz:
            row = xs[ys == q]
            if not len(row): continue
            x = row.min() if v[0] < 0 else row.max()
            out.append((x + v[0] * gap, q + v[1] * gap))
        else:
            col = ys[xs == q]
            if not len(col): continue
            y = col.min() if v[1] < 0 else col.max()
            out.append((q + v[0] * gap, y + v[1] * gap))
    return out


def band_pts(o, v, L, thick_frac=0.6, rim='w', body='p', root_taper=True):
    """one tapered rimmed band: 2 px (rim row on the lit side + body row) for thick_frac of its length, then a
    1 px body-tone point.  Lines are stepped on the dominant axis so the rows never gap."""
    v = _norm(v)
    pu = _perp_up(v)
    horiz = abs(v[0]) >= abs(v[1])
    off = (0, -1 if pu[1] < 0 else 1) if horiz else (-1 if pu[0] < 0 else 1, 0)
    pts = {}
    ln = _line(o[0], o[1], o[0] + v[0] * (L - 1), o[1] + v[1] * (L - 1))
    for k, (x, y) in enumerate(ln):
        f = k / max(1, len(ln) - 1)
        pts[(x, y)] = body
        lo = 0.15 if root_taper else 0.0
        if lo <= f < thick_frac and len(ln) >= 4:
            pts[(x + off[0], y + off[1])] = rim
    return pts


def speed_bands(g, vector, n=3, lengths=(12, 9, 14, 7), origins='auto', body=None, gap=2, guard=None, cut=None,
                mode='behind', rim='w', tone='p', thick_frac=0.6):
    """RIMMED SPEED BANDS: n (3-4) tapered bands trailing along `vector` (the direction AGAINST travel), rooted on the
    trailing silhouette edge (origins='auto' needs `body` mask) or at explicit origins."""
    if isinstance(origins, str):
        origins = auto_origins(body if body is not None else g != '.', vector, n, gap=gap)
    pts = {}
    for i, o in enumerate(origins[:n]):
        pts.update(band_pts((round(o[0]), round(o[1])), vector, lengths[i % len(lengths)], thick_frac, rim, tone))
    return commit(g, pts, mode, guard, cut)


# ------------------------------------------------------------------------------------------------ (4) afterimage
def smooth_mask(m, k=1):
    """close then open by k px: removes 1 px stair noise and slivers so a flat copy reads as a clean silhouette"""
    if not k: return m
    m = erode(dilate(m, k), k)
    return dilate(erode(m, k), k)


def afterimage(g, sil, offsets=((-8, -2), (-16, -4)), tone='p', far_tone=None, gap=1, body_gap=1, partial_open=2,
               guard=None, smooth=1, far_mask=None, style='ring', ring=1, travel=None):
    """2 HARD-EDGED AFTERIMAGE MULTIPLES of a silhouette mask `sil` (the pose she left), painted behind, flat
    pink_0, no dither, no interior detail:
      near = the FULL silhouette (smoothed: close+open `smooth` px, so 1 px ribbons / the blade drop out),
      far  = a PARTIAL copy: `far_mask` (e.g. the head + bun mass, her most recognisable shape) or the big masses
             of sil (opened by partial_open px).
    style 'ring' (default, r3): each copy is its silhouette CONTOUR, `ring` px thick (+1 px on the trailing side
    when `travel` is given) - the head dome, bun and skirt read as her ghost at 1x instead of a solid pink slab
    (the r3 judges called the solid slab 'bacon').  style 'solid': filled copies, near kept body_gap px clear of
    the body and the far copy `gap` px clear of the near one."""
    far_tone = far_tone or tone
    body = g != '.'
    base = smooth_mask(sil, smooth)
    fsrc = (smooth_mask(far_mask, smooth) if far_mask is not None
            else dilate(erode(sil, partial_open), partial_open)) if len(offsets) > 1 else None
    pts = {}
    if style == 'ring':
        tb = None
        if travel is not None:
            v = _norm(travel); tb = (-int(np.sign(round(v[0], 3))), -int(np.sign(round(v[1], 3))))
        def contour(m):
            r = m & ~erode(m, ring)
            if tb is not None:                       # heavier trailing edge: +1 px inward on the trailing side
                trail = m & ~_moved(m, (-tb[0], -tb[1]))
                r |= trail | (_moved(trail, (-tb[0], -tb[1])) & m)
            return r
        near = contour(_moved(base, offsets[0])) & ~dilate(body, body_gap)
        if fsrc is not None:
            fm = contour(_moved(fsrc, offsets[1])) & ~dilate(near | body, gap)
            for y, x in zip(*np.nonzero(fm)): pts[(x, y)] = far_tone
        for y, x in zip(*np.nonzero(near)): pts[(x, y)] = tone
    else:
        near = _moved(base, offsets[0]) & ~dilate(body, body_gap)
        if fsrc is not None:
            fm = _moved(fsrc, offsets[1]) & ~dilate(near | body, gap)
            for y, x in zip(*np.nonzero(fm)): pts[(x, y)] = far_tone
        for y, x in zip(*np.nonzero(near)): pts[(x, y)] = tone
    return commit(g, pts, 'behind', guard)


# ------------------------------------------------------------------------------------------------ (5) impact star
# Hand-typed stamps (Claude pixel art).  '+' star: 3x3 core, cardinal arms 7 px (steel_2, 2 px pink_0 tips),
# diagonals 3 px.  'x' = the same star turned 45 deg (for variety between hits).  Centre = the middle cell.
STAR = {
    'plus': [".......p.......",
             ".......p.......",
             ".......w.......",
             ".......w.......",
             "....w..w..w....",
             ".....w.w.w.....",
             "......www......",
             "ppwwwwwwwwwwwpp",
             "......www......",
             ".....w.w.w.....",
             "....w..w..w....",
             ".......w.......",
             ".......w.......",
             ".......p.......",
             ".......p......."],
    'x':    ["pp...........pp",
             ".pw.........wp.",
             "..w.........w..",
             "...w...w...w...",
             "....w..w..w....",
             ".....w.w.w.....",
             "......www......",
             "...wwwwwwwww...",
             "......www......",
             ".....w.w.w.....",
             "....w..w..w....",
             "...w...w...w...",
             "..w.........w..",
             ".pw.........wp.",
             "pp...........pp"],
    'bold': [".......p.......",                 # heavier hit: 5 px diamond core, 2 px arm roots
             ".......p.......",
             ".......w.......",
             "......www......",
             "....w.www.w....",
             ".....wwwww.....",
             "...wwwwwwwww...",
             "ppwwwwwwwwwwwpp",
             "...wwwwwwwww...",
             ".....wwwww.....",
             "....w.www.w....",
             "......www......",
             ".......w.......",
             ".......p.......",
             ".......p......."],
    'small': [".......",                     # stage 1: the star collapses to a 7 px cross
              "...w...",
              "...w...",
              ".wwwww.",
              "...w...",
              "...w...",
              "......."],
}
# 2:1-slope stroke directions (clean pixel lines), 4 between the star arms
STROKE_DIRS = [(2, 1), (-1, 2), (-2, -1), (1, -2)]


def _stamp_pts(rows, cx, cy):
    h, w = len(rows), len(rows[0])
    out = {}
    for j, r in enumerate(rows):
        for i, c in enumerate(r):
            if c != '.': out[(cx - w // 2 + i, cy - h // 2 + j)] = c
    return out


def _stroke(X, Y, d, r0, L, root=2, tones=('w', 'p'), thick=True):
    """a radial 2:1 stroke from radius r0, L px along the major axis; 2 px thick (minor axis) for `root` px, the
    first 2 px steel_2 then pink_0"""
    dx, dy = d
    major_x = abs(dx) >= abs(dy)
    sx, sy = (1 if dx > 0 else -1), (1 if dy > 0 else -1)
    nrm = math.hypot(dx, dy)
    x0 = X + dx / nrm * r0; y0 = Y + dy / nrm * r0
    out = {}
    for i in range(L):
        if major_x: x, y = round(x0) + i * sx, round(y0) + (i // 2) * sy
        else: x, y = round(x0) + (i // 2) * sx, round(y0) + i * sy
        c = tones[0] if i < 2 else tones[1]
        out[(x, y)] = c
        if thick and i < root:
            out[(x, y + sy) if major_x else (x + sx, y)] = c
    return out


def _ring(X, Y, r, a0, a1, w=2, tone='p'):
    out = {}
    R = r + 1
    for y in range(int(Y - R), int(Y + R) + 1):
        for x in range(int(X - R), int(X + R) + 1):
            d = math.hypot(x - X, y - Y)
            if r - w < d <= r:
                ang = math.degrees(math.atan2(y - Y, x - X))
                f = _angf(ang, a0, a1)
                if f is None: continue
                # tapered ends: the outer 1 px only near both tips
                if (f < 0.15 or f > 0.85) and d <= r - 1: continue
                out[(x, y)] = tone
    return out


def impact_star_pts(c, stage=0, star='plus', strokes=4, stroke_r=9, stroke_len=5, shock=True, shock_r=16,
                    shock_span=50, rot=0, skip=()):
    X, Y = c
    def skipped(a):
        return any(_angf(a, lo, hi) is not None for lo, hi in skip)
    pts = {}
    if stage == 0:
        pts.update(_stamp_pts(STAR[star], X, Y))
        for d in STROKE_DIRS[:strokes]:
            if not skipped(math.degrees(math.atan2(d[1], d[0]))): pts.update(_stroke(X, Y, d, stroke_r, stroke_len))
        if shock:
            pts.update(_ring(X, Y, shock_r, rot - shock_span / 2, rot + shock_span / 2, 2))
    elif stage == 1:
        pts.update(_stamp_pts(STAR['small'], X, Y))
        for d in STROKE_DIRS[:strokes]:
            if not skipped(math.degrees(math.atan2(d[1], d[0]))):
                pts.update(_stroke(X, Y, d, stroke_r + 4, stroke_len - 1, root=2, tones=('p', 'p')))
        if shock:
            pts.update(_ring(X, Y, shock_r + 3, rot - shock_span * 0.7, rot + shock_span * 0.7, 2))
    else:
        for d in STROKE_DIRS[:strokes]:
            if not skipped(math.degrees(math.atan2(d[1], d[0]))):
                pts.update(_stroke(X, Y, d, stroke_r + 8, 2, root=0, tones=('p', 'p'), thick=False))
    # skip ranges also mask the star / ring pixels (her arm / face side)
    if skip:
        pts = {q: t for q, t in pts.items()
               if math.hypot(q[0] - X, q[1] - Y) < 3 or not skipped(math.degrees(math.atan2(q[1] - Y, q[0] - X)))}
    return pts


def impact_star(g, c, stage=0, star='plus', strokes=4, stroke_r=9, stroke_len=5, shock=True, shock_r=16,
                shock_span=50, rot=0, skip=(), guard=None, cut=None):
    """IMPACT STAR at the contact point (stage 0 the hit, 1 the burst, 2 the fade - a 3-frame FX the engine may
    keep playing during hit-stop).  Stamp star (3x3 core, cardinal 7 px, diagonals 3 px) painted OVER everything
    (a flash); 3-4 radial 2:1 strokes (2 px root, steel_2 -> pink_0 taper) and ONE 2 px pink_0 shock arc centred on
    `rot` (the cut direction) painted behind.  skip = angle ranges kept clear (her arm / face)."""
    pts = impact_star_pts(c, stage, star, strokes, stroke_r, stroke_len, shock, shock_r, shock_span, rot, skip)
    X, Y = c
    near = {p: t for p, t in pts.items() if math.hypot(p[0] - X, p[1] - Y) <= 7.9}
    far = {p: t for p, t in pts.items() if p not in near}
    v1 = commit(g, near, 'over', guard, cut)
    v2 = commit(g, far, 'behind', guard, cut)
    v1.update(v2)
    return v1


# ------------------------------------------------------------------------------------------------ (6) dust
# Hand-typed flat puffs, kicked to the RIGHT (mirrored for dir -1).  Bottom row = the ground row.  Column 0 sits
# `tuck` px behind the foot's outer edge so the puff is ATTACHED (painted behind the shoe).
# w = lit top (steel_2), T = body (steel_1), t = ground shade (steel_0).  Every tone cluster >= 2 px.
DUST = {
    0: dict(rows=[".wwT..",
                  "wTTTT.",
                  "ttttt."], grit=[], tuck=2, lift=0),
    1: dict(rows=["..wwT....wT...",
                  ".wTTTT..wTTT..",
                  "wTTTTTTwTTTTT.",
                  "ttTTTTTTTTttt."], grit=[(15, -4), (18, -6)], tuck=2, lift=0),
    2: dict(rows=["..TT....TT..",
                  ".TTTT..TTTT."], grit=[(15, -6)], tuck=0, lift=1, shift=3),
}


def dust_pts(x, y, d=1, stage=1, grit=True):
    S = DUST[stage]
    rows = S['rows']; h = len(rows)
    x0 = x - d * S['tuck'] + d * S.get('shift', 0)
    pts = {}
    for j, r in enumerate(rows):
        for i, c in enumerate(r):
            if c != '.': pts[(x0 + d * i, y - (h - 1 - j) - S['lift'])] = c
    if grit:
        for gx, gy in S['grit']:
            pts[(x0 + d * gx, y + gy)] = 'T'; pts[(x0 + d * (gx + 1), y + gy)] = 'T'
    return pts


def dust(g, feet, stage=1, grit=True, guard=None, mode='behind'):
    """FOOT-ATTACHED DUST: feet = [(x, y, dir)] with x = the foot's outer edge column, y = the ground row,
    dir = +1 / -1 (the side the puff is kicked to; two entries for a landing).  Flat 3-row puffs + 2 px grit;
    stage 0 contact, 1 kick, 2 fading (2 rows, lifted, broken)."""
    pts = {}
    for x, y, d in feet:
        pts.update(dust_pts(x, y, d, stage, grit))
    return commit(g, pts, mode, guard)


# ------------------------------------------------------------------------------------------------ (7) streaks
def streaks(g, feet, vector=(0, 1), n=3, lengths=(6, 9, 5), spacing=3, gap=1, guard=None, mode='behind',
            thick_frac=0.4):
    """UNDER-FOOT STREAKS: take-off / rise streaks fanning from under the feet (vector (0,1) = down), or ground
    streaks behind the feet on run / dash (vector (-1,0)).  Each is 2 px (steel_2 rim + pink_0) at the root for
    thick_frac of its length, then a 1 px pink_0 point.  feet = [(x, y)] root points (the foot's bottom px);
    n streaks spread `spacing` px apart across the travel."""
    v = _norm(vector)
    pu = _perp_up(v) if abs(v[0]) >= abs(v[1]) else (1, 0)
    pts = {}
    k = 0
    for fx, fy in feet:
        for i in range(n):
            s = (i - (n - 1) / 2) * spacing
            o = (round(fx + pu[0] * s + v[0] * gap), round(fy + pu[1] * s + v[1] * gap))
            pts.update(band_pts(o, v, lengths[k % len(lengths)], thick_frac, 'w', 'p', root_taper=False))
            k += 1
    return commit(g, pts, mode, guard)


# ------------------------------------------------------------------------------------------------ checks
def stats(pts):
    """tone mix of a painted FX dict"""
    from collections import Counter
    return dict(Counter(pts.values()))


def orphans(g, only=None):
    """pixels with no same-tone 8-neighbour (restricted to `only` = iterable of (x, y) if given)"""
    out = []
    it = only if only is not None else [(x, y) for y, x in zip(*np.nonzero(g != '.'))]
    for x, y in it:
        c = g[y, x]
        if c == '.': continue
        if not any(0 <= x + i < N and 0 <= y + j < N and g[y + j, x + i] == c for i, j in N8): out.append((x, y))
    return out
