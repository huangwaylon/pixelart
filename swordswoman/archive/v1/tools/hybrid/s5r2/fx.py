"""S5 r2 FX kit (Claude-drawn exact pixels): blade-arc crescent smears on the cut-plane ellipse, double crescent,
front-plane rule, impact spark + ticks, stretched-limb / hand echo smears, speed lines, dust, take-off streaks.
Operates on a 128x128 RGBA (locked palette) and a protect mask (head stamp: smears never cover the face).

crescent(a, cx, cy, rx, ry, a0, a1, lead=6, prof=(1,2,4,5,6), front=None, over_rows=2, protect=None, echo=True)
  arc angles in degrees, screen space (0 = +x, 90 = +y down); the band runs from a0 (tail) to a1 (lead, where the
  real blade is). The outer edge of the band IS the blade-tip path; the band grows inward (toward the centre).
  Thickness grows monotone from the tail to the lead (profile steps). Tones: steel_2 rim on the outer 70 % toward
  the lead, pink_1 body, pink_0 inner edge. Parts of the arc in FRONT of the body (angles in `front`, i.e. the
  near half of the cut plane) paint only their `over_rows` outer rows over the character; the rest of the band
  goes behind (transparent px only). Far parts: behind only.
"""
import math, json
import numpy as np
PAL = json.load(open('/Users/waylonhuang/Documents/other/pixelart/swordswoman/docs/palette.json'))
def hx(h): return np.array([int(h[i:i + 2], 16) for i in (1, 3, 5)], np.uint8)
R = PAL['ramps']
T = {'w': hx(R['steel'][2]), 'T': hx(R['steel'][1]), 't': hx(R['steel'][0]), 'P': hx(R['pink'][1]), 'p': hx(R['pink'][0]),
     'S': hx(R['skin'][2]), 's': hx(R['skin'][1]), 'C': hx(R['red'][3]), 'R': hx(R['red'][2]), 'r': hx(R['red'][1]),
     'v': hx(R['red'][0]), 'K': hx(PAL['outline']), 'd': hx(R['dark'][1])}

def put(a, x, y, c, mode='behind', protect=None):
    if not (0 <= x < 128 and 0 <= y < 128): return False
    if protect is not None and protect[y, x]: return False
    if mode == 'behind' and a[y, x, 3] > 0: return False
    a[y, x, :3] = T[c]; a[y, x, 3] = 255
    return True

def in_range(ang, rng):
    for lo, hi in rng:
        lo, hi = min(lo, hi), max(lo, hi)
        for k in (-720, -360, 0, 360, 720):
            if lo <= ang + k <= hi: return True
    return False

def crescent(a, cx, cy, rx, ry, a0, a1, prof=(1, 2, 4, 5, 6), front=(), over_rows=2, protect=None,
             echo=True, echo_gap=2, echo_frac=0.55, rim_frac=0.7, tones=('w', 'P', 'p')):
    n = int(abs(a1 - a0) * max(rx, ry) / 57.3 * 3) + 8
    paint = {}                       # (x,y) -> (depth, s, ang)
    for k in range(n + 1):
        s = k / n                    # 0 tail -> 1 lead
        ang = a0 + (a1 - a0) * s
        th = prof[min(len(prof) - 1, int(s * len(prof)))]
        c, si = math.cos(math.radians(ang)), math.sin(math.radians(ang))
        for d10 in range(0, th * 10, 3):
            d = d10 / 10.0
            x = round(cx + (rx - d) * c); y = round(cy + (ry - d * ry / rx) * si)
            dd = int(d)
            if (x, y) not in paint or paint[(x, y)][0] > dd: paint[(x, y)] = (dd, s, ang, th)
    out = []
    for (x, y), (d, s, ang, th) in paint.items():
        if d == 0 and s >= 1 - rim_frac: c = tones[0]
        elif d >= th - 1 and th >= 3: c = tones[2]
        else: c = tones[1]
        isfront = in_range(ang, front)
        mode = 'over' if (isfront and d < over_rows) else 'behind'
        out.append((x, y, c, mode))
    for x, y, c, mode in sorted(out, key=lambda t: t[3] == 'over'):
        put(a, x, y, c, mode, protect)
    if echo:                         # thin pink_0 echo arc inside the band (the double crescent), lead part only
        e0 = a1 - (a1 - a0) * echo_frac
        m = int(abs(a1 - e0) * max(rx, ry) / 57.3 * 3) + 4
        for k in range(m + 1):
            s = k / m; ang = e0 + (a1 - e0) * s
            if s > 0.92: continue
            th = prof[-1] + echo_gap
            c, si = math.cos(math.radians(ang)), math.sin(math.radians(ang))
            x = round(cx + (rx - th) * c); y = round(cy + (ry - th * ry / rx) * si)
            put(a, x, y, 'p', 'behind', protect)
    return a

def arc_pts(cx, cy, rx, ry, a0, a1, n=12):
    return [(cx + rx * math.cos(math.radians(a0 + (a1 - a0) * k / n)), cy + ry * math.sin(math.radians(a0 + (a1 - a0) * k / n))) for k in range(n + 1)]

def spark(a, x, y, size=3, ticks=5, tick_r=(5, 7), protect=None, ang0=-90):
    """steel_2 4-point star (arms `size`) + pink_1 tips, and `ticks` short burst ticks around it."""
    for k in range(-size, size + 1):
        put(a, x + k, y, 'w', 'over', protect); put(a, x, y + k, 'w', 'over', protect)
    for dx, dy in ((1, 1), (-1, 1), (1, -1), (-1, -1)): put(a, x + dx, y + dy, 'P', 'over', protect)
    for e in ((size + 1, 0), (-size - 1, 0), (0, size + 1), (0, -size - 1)): put(a, x + e[0], y + e[1], 'P', 'behind', protect)
    for i in range(ticks):
        ang = math.radians(ang0 + 360.0 * i / ticks + 18)
        for r in range(tick_r[0], tick_r[1] + 1):
            put(a, round(x + r * math.cos(ang)), round(y + r * math.sin(ang)), 'w' if r == tick_r[0] else 'P', 'behind', protect)

def speed(a, x, y, dx, dy, n=3, length=8, gap=3, tones=('p',), stagger=2, protect=None):
    """n parallel motion lines starting at (x,y) running along (dx,dy) (unit-ish), spaced `gap` perpendicular."""
    L = math.hypot(dx, dy); ux, uy = dx / L, dy / L; px, py = -uy, ux
    for i in range(n):
        ln = length - (i % 2) * stagger
        sx, sy = x + px * gap * (i - (n - 1) / 2), y + py * gap * (i - (n - 1) / 2)
        for t in range(ln):
            c = tones[0] if t < ln - 2 or len(tones) == 1 else tones[-1]
            put(a, round(sx + ux * t), round(sy + uy * t), c, 'behind', protect)

def dust(a, x, y, side=1, size=2):
    """little landing puff: steel_1 body, steel_0 under-shadow, 2-4 px."""
    pat = ['.TT.', 'TTTT', 'tTTt'] if size >= 2 else ['TT', 'tT']
    for j, row in enumerate(pat):
        for i, ch in enumerate(row if side > 0 else row[::-1]):
            if ch != '.': put(a, x + i, y + j, ch, 'behind')

def tick(a, x0, y0, x1, y1, c='T'):
    n = max(abs(x1 - x0), abs(y1 - y0), 1)
    for k in range(n + 1): put(a, round(x0 + (x1 - x0) * k / n), round(y0 + (y1 - y0) * k / n), c, 'behind')

def silhouette_echo(a, src_mask, dx, dy, c='p', protect=None):
    """after-image / multiple-limb copy: paint src_mask shifted by (dx,dy) in one tone, behind."""
    ys, xs = np.nonzero(src_mask)
    for y, x in zip(ys, xs): put(a, x + dx, y + dy, c, 'behind', protect)

def limb_smear(a, pts, tones=('R', 'r', 'C'), r0=1.0, r1=2.6, protect=None):
    """stretched sleeve smear: tapered capsule along pts (tail -> hand), 3 red tones banded along the length,
    painted behind the character (no outline: smears are unlined)."""
    segs = list(zip(pts, pts[1:])); tot = sum(math.hypot(b[0] - a_[0], b[1] - a_[1]) for a_, b in segs) or 1
    acc = 0
    for (x0, y0), (x1, y1) in segs:
        L = math.hypot(x1 - x0, y1 - y0); n = max(2, int(L * 3))
        for k in range(n + 1):
            t = (acc + L * k / n) / tot; r = r0 + (r1 - r0) * t
            x, y = x0 + (x1 - x0) * k / n, y0 + (y1 - y0) * k / n
            for yy in range(int(y - r - 1), int(y + r + 2)):
                for xx in range(int(x - r - 1), int(x + r + 2)):
                    if (xx - x) ** 2 + (yy - y) ** 2 <= r * r:
                        c = tones[2] if t < 0.33 else (tones[0] if t < 0.75 else tones[1])
                        put(a, xx, yy, c, 'behind', protect)
        acc += L

def silhouette_echo_pts(a, pts, c='p', protect=None):
    for x, y in pts: put(a, x, y, c, 'behind', protect)
