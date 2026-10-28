"""S4 animation / FX layer: bow-lag cels, expression edits, blade-arc + limb smears, sparks, dust.
All exact pixels, palette-locked, hard alpha.  Used by build_set.py recipes."""
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import draw as D  # noqa: E402
import celrender as CR  # noqa: E402

RED = {tuple(CR.tone(n)[:3]) for n in ("red_0", "red_1", "red_2", "red_3")}
HAIR = {tuple(CR.tone(n)[:3]) for n in ("hair_0", "hair_1", "hair_2")}
K = tuple(CR.tone("K")[:3])


def shift_bow(st, dx, dy, rows=10):
    """move the bow cel (red pixels in the top rows + their outline) by (dx, dy) against the head."""
    if dx == 0 and dy == 0:
        return st
    h, w = st.shape[:2]
    rgb = [[tuple(st[y, x, :3]) if st[y, x, 3] else None for x in range(w)] for y in range(h)]
    m = np.zeros((h, w), bool)
    for y in range(min(rows, h)):
        for x in range(w):
            if rgb[y][x] in RED:
                m[y, x] = True
    # outline pixels touching the bow (8-conn) in the bow rows that do not border hair below/side only
    mo = m.copy()
    for y in range(min(rows, h)):
        for x in range(w):
            if rgb[y][x] == K and not m[y, x]:
                if m[max(0, y - 1):y + 2, max(0, x - 1):x + 2].any():
                    mo[y, x] = True
    out = st.copy()
    for y, x in zip(*np.nonzero(mo)):
        # vacate: hair underneath if this px sits on the hair mass, else clear
        hair_nb = any(0 <= y + a < h and 0 <= x + b < w and rgb[y + a][x + b] in HAIR and not mo[y + a, x + b]
                      for a, b in ((1, 0), (0, 1), (0, -1)))
        out[y, x] = CR.tone("hair_0") if hair_nb and y >= 6 else (0, 0, 0, 0)
    for y, x in zip(*np.nonzero(mo)):
        Y, X = y + dy, x + dx
        if 0 <= Y < h and 0 <= X < w:
            out[Y, X] = st[y, x]
    return out


def focus_face(st, d):
    """'focused' combat expression: lids lowered 1 row over the inner half of each eye (brow-down
    slant).  Eye rows are found from the eye ramp in the stamp."""
    out = st.copy()
    eye = {tuple(CR.tone(n)[:3]) for n in ("eye_0", "eye_1", "steel_2")}
    h, w = st.shape[:2]
    rows = [y for y in range(h) if any(st[y, x, 3] and tuple(st[y, x, :3]) in eye for x in range(w))]
    if not rows:
        return out
    top = rows[0]
    xs = [x for x in range(w) if st[top, x, 3] and tuple(st[top, x, :3]) in eye]
    # split into eyes (gap > 1)
    groups, g = [], [xs[0]]
    for x in xs[1:]:
        if x - g[-1] > 1:
            groups.append(g)
            g = [x]
        else:
            g.append(x)
    groups.append(g)
    cx = w / 2
    for g in groups:
        inner = sorted(g, key=lambda x: abs(x - cx))[: max(1, len(g) // 2)]
        for x in inner:
            out[top, x] = CR.tone("K")
    return out


class Layer:
    """draw.py Canvas-compatible: collects pixels, composited later."""

    def __init__(self):
        self.px = {}

    def put(self, x, y, c, behind=False):
        x, y = int(x), int(y)
        if 0 <= x < 128 and 0 <= y < 128:
            self.px[(x, y)] = c


def composite(img, layer, mode="behind", protect=None, front_fn=None):
    """mode behind: only transparent px; over: everywhere except protect mask; front_fn(x, y) -> True
    paints over the body there, else behind."""
    for (x, y), c in layer.px.items():
        if protect is not None and protect[y, x]:
            continue
        over = mode == "over" or (front_fn is not None and front_fn(x, y))
        if over or img[y, x, 3] == 0:
            img[y, x] = c


def arc_layer(cx, cy, rx, ry, a0, a1, w, tones="w,P,p", taper="lead", grow="in"):
    L = Layer()
    D.smear_arc(L, cx, cy, rx, ry, a0, a1, w, D.tone_list(tones), taper=taper, grow=grow, behind=False)
    return L


def streak_layer(x0, y0, x1, y1, w, tones, taper="lead"):
    L = Layer()
    D.streak(L, x0, y0, x1, y1, w, D.tone_list(tones), taper=taper, behind=False)
    return L


def ang_of(x, y, cx, cy, rx, ry):
    return math.degrees(math.atan2((y - cy) / ry, (x - cx) / rx))


def in_range(a, lo, hi):
    lo, hi = min(lo, hi), max(lo, hi)
    while a < lo:
        a += 360
    while a > lo + 360:
        a -= 360
    return a <= hi


def spark(img, x, y, r=3):
    """1-frame steel_2 impact star (+ pink_1 tips), over everything."""
    x, y = int(round(x)), int(round(y))
    pts = [(0, 0)]
    for k in range(1, r + 1):
        pts += [(k, 0), (-k, 0), (0, k), (0, -k)]
    pts += [(1, 1), (-1, -1), (1, -1), (-1, 1)]
    for dx, dy in pts:
        X, Y = x + dx, y + dy
        if 0 <= X < 128 and 0 <= Y < 128:
            tip = max(abs(dx), abs(dy)) == r
            img[Y, X] = CR.tone("pink_1" if tip else "steel_2")


def dust(img, x, y, side):
    """landing dust ticks: 3 px arcs kicked out sideways from the foot, steel_1 / skin_2."""
    x, y = int(round(x)), int(round(y))
    pat = [(1, 0, "steel_1"), (2, -1, "steel_1"), (3, -1, "skin_2"), (4, -2, "skin_2"),
           (2, 0, "steel_1"), (5, -1, "steel_1")]
    for dx, dy, c in pat:
        X, Y = x + side * dx, y + dy
        if 0 <= X < 128 and 0 <= Y < 128 and img[Y, X, 3] == 0:
            img[Y, X] = CR.tone(c)


def speed_lines(img, x, y, dx, dy, n, length, gap, c="pink_0"):
    L = Layer()
    D_ = (dx * dx + dy * dy) ** 0.5
    ux, uy = dx / D_, dy / D_
    px, py = -uy, ux
    for i in range(n):
        ox, oy = x + px * gap * (i - (n - 1) / 2), y + py * gap * (i - (n - 1) / 2)
        ln = length - (i % 2) * 2
        for t in range(ln):
            L.put(round(ox + ux * t), round(oy + uy * t), CR.tone(c))
    composite(img, L, "behind")


def limb(img, pts, w=2, behind_mask=None, lit="skin_1", shade="skin_0"):
    """hand-drawn limb: a w-px skin stroke along the polyline (lit on top, shade on the bottom row),
    closed with a 1 px outline on transparent px.  behind_mask: px that must not be painted (front parts)."""
    path = []
    for a, b in zip(pts[:-1], pts[1:]):
        seg = CR.line_pts(a[0], a[1], b[0], b[1])
        path += seg if not path else seg[1:]
    body = set()
    for x, y in path:
        for k in range(w):
            body.add((x, y + k) if True else None)
    for (x, y) in body:
        if 0 <= x < 128 and 0 <= y < 128 and (behind_mask is None or not behind_mask[y, x]):
            img[y, x] = CR.tone(shade if (x, y - 1) in body else lit)
    for (x, y) in body:
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            X, Y = x + dx, y + dy
            if (X, Y) not in body and 0 <= X < 128 and 0 <= Y < 128 and img[Y, X, 3] == 0:
                img[Y, X] = CR.tone("K")


def heel(img, x, y, facing=1):
    """strappy heel at sprite scale (sole row y): 4 px long, skin strap gaps, heel point at the back."""
    x, y = int(round(x)), int(round(y))
    pat = {(0, 0): "K", (1, 0): "K", (2, 0): "K", (3, 0): "K", (-1, 0): "K",
           (0, -1): "K", (1, -1): "skin_1", (2, -1): "K", (3, -1): "K",
           (0, -2): "skin_1", (1, -2): "K", (-1, 1): "K"}
    for (dx, dy), c in pat.items():
        X, Y = x + dx * facing, y + dy
        if 0 <= X < 128 and 0 <= Y < 128:
            img[Y, X] = CR.tone(c)
