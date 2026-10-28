"""Exact-pixel drawing helpers for Claude pixel artists (palette-locked).

  .venv/bin/python tools/hybrid/draw.py IN.png|IN.pix --out OUT.png|OUT.pix [--ops ops.txt] "OP ..." "OP ..."
        [--preview 8] [--new 128x128]

Ops run in order.  Coordinates are x,y (column,row) in the image.  Colours are STANDARD pixgrid chars
(K R r v C h H J m s S l L d t T w e E p P u), palette names (red_2, outline, ...) or 'clear'.
Anything off-palette is rejected.  `--ops FILE` reads one op per line ('#' comments).

  line     x0,y0 x1,y1 C [nopp]          Bresenham; pixel-perfect (L-corners removed) unless nopp
  poly     x0,y0 x1,y1 x2,y2 ... C        polyline, pixel-perfect
  curve    x0,y0 cx,cy x1,y1 C            quadratic Bezier (control point cx,cy), pixel-perfect
  arc      cx,cy rx[,ry] a0 a1 C          elliptical arc; angles in degrees, 0 = +x (right), 90 = down
                                          (screen clockwise); a1 < a0 draws counter-clockwise.
                                          Pixel-perfect, so runs come out monotone (1-1-2-2-3 ...)
  rect     x0,y0 x1,y1 C [fill]
  fill     x,y C [8]                      flood fill the same-colour region (4-conn; 8 = 8-conn)
  cluster  x,y C PATTERN                  PATTERN rows split by '/', 'X' paints C, '.' or '_' skips
  stamp    x,y PATTERN                    PATTERN of legend chars, '/' rows, '_' skips ('.' = clear)
  replace  x0,y0 x1,y1 FROM TO            recolour inside the box
  erase    x0,y0 x1,y1 [C]                clear the box (only colour C if given)
  copy     x0,y0 x1,y1 tx,ty [src=FILE] [opaque]   copy box (inclusive) to top-left tx,ty
  shift    x0,y0 x1,y1 dx,dy [only=C,C]   move box contents (vacated pixels -> clear)
  mirror   x0,y0 x1,y1 h|v [to=tx,ty]     flip a part in place (or into tx,ty)
  smear    cx,cy rx[,ry] a0 a1 W [tones=w,P,p] [taper=lead|both|tail|none] [grow=out|in|mid] [over]
                                          blade-arc smear: a crescent band along the arc, max
                                          thickness W px at the lead end (a1), tapering to 0 at the
                                          tail (a0); 2-3 tones across the band (first = core on the
                                          blade path, last = outer edge).  Default: behind (only
                                          transparent pixels), 'over' paints on top.
  streak   x0,y0 x1,y1 W [tones=...] [taper=...] [over]   straight tapered smear (run/dash/limb)
  echo     x0,y0 x1,y1 dx,dy N [tone=C]   N afterimage copies of the box offset by k*(dx,dy)/N
                                          (multiple-limb / dash smear), behind; tone flattens them
  speed    x,y dx,dy N LEN GAP C          N parallel motion lines of length LEN along (dx,dy),
                                          GAP px apart, behind; lines taper by 1 px each
  outline  [C] [only-new]                 1 px exterior outline around all opaque pixels
"""
import argparse
import math
import os
import shlex
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hylib as H  # noqa: E402
import pixgrid as PG  # noqa: E402


def col(c):
    """colour token -> RGBA tuple (palette-locked)."""
    pal = H.palette()
    c = c.strip()
    if c in PG.STD:
        c = PG.STD[c]
    if c in ("transparent", "clear", "."):
        return (0, 0, 0, 0)
    return pal.rgba(pal.resolve(c))


def pt(s):
    a, b = s.split(",")
    return float(a), float(b)


def ipt(s):
    a, b = pt(s)
    return int(round(a)), int(round(b))


# ---------------------------------------------------------------- rasterizers
def bresenham(x0, y0, x1, y1):
    pts = []
    dx, dy = abs(x1 - x0), -abs(y1 - y0)
    sx, sy = (1 if x0 < x1 else -1), (1 if y0 < y1 else -1)
    err = dx + dy
    while True:
        pts.append((x0, y0))
        if x0 == x1 and y0 == y1:
            break
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            x0 += sx
        if e2 <= dx:
            err += dx
            y0 += sy
    return pts


def dedupe(pts):
    out = []
    for p in pts:
        if not out or out[-1] != p:
            out.append(p)
    return out


def connect(pts):
    """make a sampled point list 8-connected (fill gaps with bresenham)."""
    out = []
    for p in pts:
        if out and max(abs(p[0] - out[-1][0]), abs(p[1] - out[-1][1])) > 1:
            out += bresenham(out[-1][0], out[-1][1], p[0], p[1])[1:]
        elif not out or out[-1] != p:
            out.append(p)
    return out


def pixel_perfect(pts):
    """drop L-corner pixels: p[i] where p[i-1] and p[i+1] are diagonal neighbours."""
    if len(pts) < 3:
        return pts
    out = [pts[0]]
    i = 1
    while i < len(pts) - 1:
        a, b, c = out[-1], pts[i], pts[i + 1]
        if (a[0] == b[0] or a[1] == b[1]) and (b[0] == c[0] or b[1] == c[1]) and a[0] != c[0] and a[1] != c[1]:
            i += 1
            continue
        out.append(b)
        i += 1
    out.append(pts[-1])
    return out


def ellipse_pts(cx, cy, rx, ry):
    """midpoint ellipse (integer centre / radii in half-pixel steps) -> set of points, all 4 quadrants.
    The midpoint algorithm gives monotone run lengths along every octant."""
    pts = set()
    rx2, ry2 = rx * rx, ry * ry
    x, y = 0.0, float(ry)
    px, py = 0.0, 2 * rx2 * y
    p = ry2 - rx2 * ry + 0.25 * rx2

    def add(x, y):
        for sx in (-1, 1):
            for sy in (-1, 1):
                pts.add((int(round(cx + sx * x)), int(round(cy + sy * y))))
    while px < py:
        add(x, y)
        x += 1
        px += 2 * ry2
        if p < 0:
            p += ry2 + px
        else:
            y -= 1
            py -= 2 * rx2
            p += ry2 + px - py
    p = ry2 * (x + 0.5) ** 2 + rx2 * (y - 1) ** 2 - rx2 * ry2
    while y >= 0:
        add(x, y)
        y -= 1
        py -= 2 * rx2
        if p > 0:
            p += rx2 - py
        else:
            x += 1
            px += 2 * ry2
            p += rx2 - py + px
    return pts


def arc_pts(cx, cy, rx, ry, a0, a1):
    """pixels of the midpoint ellipse whose angle lies in [a0, a1] (degrees, 0 = right, 90 = down),
    ordered from a0 to a1, made pixel-perfect."""
    pts = ellipse_pts(cx, cy, rx, ry)
    lo, hi = min(a0, a1), max(a0, a1)
    sel = []
    for (x, y) in pts:
        ang = math.degrees(math.atan2((y - cy) / max(ry, 1e-6), (x - cx) / max(rx, 1e-6)))
        while ang < lo:
            ang += 360
        while ang > lo + 360:
            ang -= 360
        if ang <= hi + 1e-9:
            sel.append((ang, x, y))
    sel.sort(reverse=a1 < a0)
    return pixel_perfect([(x, y) for _, x, y in sel])


def bezier_pts(p0, c, p1):
    L = math.dist(p0, c) + math.dist(c, p1)
    n = max(8, int(L * 3))
    pts = []
    for k in range(n + 1):
        t = k / n
        x = (1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * c[0] + t * t * p1[0]
        y = (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * c[1] + t * t * p1[1]
        pts.append((int(round(x)), int(round(y))))
    return pixel_perfect(connect(dedupe(pts)))


def runs_of(pts):
    """pixel run lengths of a rasterized curve: a run = consecutive pixels sharing a row or a column.
    Clean arcs give monotone sequences such as 1-1-2-2-3 (anti-jaggy rule R17)."""
    runs, i = [], 0
    while i < len(pts):
        j = i
        if j + 1 < len(pts):
            if pts[j + 1][1] == pts[i][1]:
                while j + 1 < len(pts) and pts[j + 1][1] == pts[i][1]:
                    j += 1
            elif pts[j + 1][0] == pts[i][0]:
                while j + 1 < len(pts) and pts[j + 1][0] == pts[i][0]:
                    j += 1
        runs.append(j - i + 1)
        i = j + 1
    return runs


class Canvas:
    def __init__(self, a):
        self.a = a
        self.H, self.W = a.shape[:2]
        self.log = []

    def put(self, x, y, c, behind=False):
        if 0 <= x < self.W and 0 <= y < self.H:
            if behind and self.a[y, x, 3] > 0:
                return
            self.a[y, x] = c

    def pts(self, pts, c, behind=False):
        for x, y in pts:
            self.put(x, y, c, behind)


def tone_list(s):
    return [col(t) for t in s.split(",")]


def band_tone(frac, tones):
    k = min(int(frac * len(tones)), len(tones) - 1)
    return tones[k]


def taper_fn(kind):
    return {"lead": lambda t: t ** 0.8,                       # 0 at the tail -> 1 at the lead
            "tail": lambda t: (1 - t) ** 0.8,
            "both": lambda t: math.sin(math.pi * min(max(t, 0), 1)) ** 0.7,
            "none": lambda t: 1.0}[kind]


def smear_arc(cv, cx, cy, rx, ry, a0, a1, w, tones, taper="lead", grow="out", behind=True):
    """crescent band.  For every pixel near the ellipse compute its angle t along [a0, a1] and its
    radial offset d from the arc (in px, + = outward).  Paint where 0 <= d' < w*taper(t)."""
    tf = taper_fn(taper)
    lo, hi = min(a0, a1), max(a0, a1)
    R = max(rx, ry) + w + 2
    for y in range(int(cy - R), int(cy + R) + 1):
        for x in range(int(cx - R), int(cx + R) + 1):
            ex, ey = (x + 0.5 - cx - 0.5) / rx, (y + 0.5 - cy - 0.5) / ry
            ang = math.degrees(math.atan2(ey, ex))
            # unwrap into [lo, hi]
            while ang < lo:
                ang += 360
            while ang > lo + 360:
                ang -= 360
            if ang > hi:
                continue
            t = (ang - a0) / (a1 - a0) if a1 != a0 else 1.0
            rr = math.hypot(ex, ey)
            # radial px distance from the ellipse along the ray (approx: scale by local radius)
            rloc = math.hypot(rx * math.cos(math.radians(ang)), ry * math.sin(math.radians(ang)))
            d = (rr - 1.0) * rloc
            th = w * tf(t)
            if th < 0.5:
                continue
            if grow == "out":
                f = d / th
            elif grow == "in":
                f = -d / th
            else:
                f = (d + th / 2) / th
            if 0 <= f < 1:
                cv.put(x, y, band_tone(f, tones), behind)


def streak(cv, x0, y0, x1, y1, w, tones, taper="lead", behind=True):
    """straight tapered smear from (x0,y0) tail to (x1,y1) lead; tones from centre line outward."""
    tf = taper_fn(taper)
    L = math.hypot(x1 - x0, y1 - y0) or 1.0
    ux, uy = (x1 - x0) / L, (y1 - y0) / L
    for y in range(int(min(y0, y1) - w - 1), int(max(y0, y1) + w + 2)):
        for x in range(int(min(x0, x1) - w - 1), int(max(x0, x1) + w + 2)):
            px, py = x - x0, y - y0
            s = px * ux + py * uy
            if s < -0.5 or s > L + 0.5:
                continue
            d = abs(-px * uy + py * ux)
            th = w * tf(min(max(s / L, 0), 1)) / 2
            if th < 0.35 or d > th:
                continue
            cv.put(x, y, band_tone(d / max(th, 1e-6) * 0.999, tones), behind)


def run_op(cv, op, base_dir):
    tok = shlex.split(op)
    if not tok:
        return
    k, args = tok[0], tok[1:]
    bare = {"nopp", "fill", "opaque", "over", "h", "v", "8"}
    flags = {}
    pos = []
    for t in args:
        if "=" in t and not t.startswith("="):
            kk, vv = t.split("=", 1)
            flags[kk] = vv
        elif t in bare and k not in ("cluster", "stamp") and (t != "8" or k == "fill"):
            flags[t] = True
        else:
            pos.append(t)
    a = cv.a
    if k == "line":
        (x0, y0), (x1, y1), c = ipt(pos[0]), ipt(pos[1]), col(pos[2])
        p = bresenham(x0, y0, x1, y1)
        cv.pts(p if "nopp" in flags else pixel_perfect(p), c)
    elif k == "poly":
        c = col(pos[-1])
        P = [ipt(s) for s in pos[:-1]]
        pts = []
        for p0, p1 in zip(P, P[1:]):
            seg = bresenham(*p0, *p1)
            pts += seg if not pts else seg[1:]
        cv.pts(pixel_perfect(pts), c)
    elif k == "curve":
        cv.pts(bezier_pts(pt(pos[0]), pt(pos[1]), pt(pos[2])), col(pos[3]))
    elif k == "arc":
        cx, cy = pt(pos[0])
        r = [float(v) for v in pos[1].split(",")]
        rx, ry = r[0], r[-1]
        p = arc_pts(cx, cy, rx, ry, float(pos[2]), float(pos[3]))
        cv.pts(p, col(pos[4]))
        cv.log.append(f"arc runs {runs_of(p)}")
    elif k == "rect":
        (x0, y0), (x1, y1), c = ipt(pos[0]), ipt(pos[1]), col(pos[2])
        x0, x1 = sorted((x0, x1))
        y0, y1 = sorted((y0, y1))
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                if "fill" in flags or y in (y0, y1) or x in (x0, x1):
                    cv.put(x, y, c)
    elif k == "fill":
        (x, y), c = ipt(pos[0]), col(pos[1])
        tgt = tuple(a[y, x])
        if tgt == tuple(c):
            return
        nb = H.N8 if "8" in flags else H.N4
        st, seen = [(x, y)], {(x, y)}
        while st:
            px, py = st.pop()
            a[py, px] = c
            for dy, dx in nb:
                qx, qy = px + dx, py + dy
                if 0 <= qx < cv.W and 0 <= qy < cv.H and (qx, qy) not in seen and tuple(a[qy, qx]) == tgt:
                    seen.add((qx, qy))
                    st.append((qx, qy))
    elif k == "cluster":
        (x0, y0), c = ipt(pos[0]), col(pos[1])
        for j, row in enumerate(pos[2].split("/")):
            for i, ch in enumerate(row):
                if ch in "X#":
                    cv.put(x0 + i, y0 + j, c)
    elif k == "stamp":
        x0, y0 = ipt(pos[0])
        for j, row in enumerate(pos[1].split("/")):
            for i, ch in enumerate(row):
                if ch != "_":
                    cv.put(x0 + i, y0 + j, col(ch))
    elif k == "replace":
        (x0, y0), (x1, y1) = ipt(pos[0]), ipt(pos[1])
        f, t = np.array(col(pos[2])), np.array(col(pos[3]))
        sub = a[y0:y1 + 1, x0:x1 + 1]
        m = np.all(sub == f, -1)
        sub[m] = t
    elif k == "erase":
        (x0, y0), (x1, y1) = ipt(pos[0]), ipt(pos[1])
        sub = a[y0:y1 + 1, x0:x1 + 1]
        if len(pos) > 2:
            sub[np.all(sub == np.array(col(pos[2])), -1)] = 0
        else:
            sub[:] = 0
    elif k == "copy":
        (x0, y0), (x1, y1), (tx, ty) = ipt(pos[0]), ipt(pos[1]), ipt(pos[2])
        src = a.copy() if "src" not in flags else np.array(Image.open(os.path.join(base_dir, flags["src"])).convert("RGBA"))
        reg = src[y0:y1 + 1, x0:x1 + 1]
        for j in range(reg.shape[0]):
            for i in range(reg.shape[1]):
                if reg[j, i, 3] > 0 or "opaque" in flags:
                    cv.put(tx + i, ty + j, tuple(reg[j, i]))
    elif k == "shift":
        (x0, y0), (x1, y1), (dx, dy) = ipt(pos[0]), ipt(pos[1]), ipt(pos[2])
        reg = a[y0:y1 + 1, x0:x1 + 1].copy()
        m = reg[..., 3] > 0
        if "only" in flags:
            m &= np.any([np.all(reg == np.array(col(c)), -1) for c in flags["only"].split(",")], 0)
        sub = a[y0:y1 + 1, x0:x1 + 1]
        sub[m] = 0
        for j, i in zip(*np.nonzero(m)):
            cv.put(x0 + i + dx, y0 + j + dy, tuple(reg[j, i]))
    elif k == "mirror":
        (x0, y0), (x1, y1) = ipt(pos[0]), ipt(pos[1])
        reg = a[y0:y1 + 1, x0:x1 + 1].copy()
        reg = reg[:, ::-1] if "v" not in flags else reg[::-1]
        tx, ty = ipt(flags["to"]) if "to" in flags else (x0, y0)
        if "to" not in flags:
            a[y0:y1 + 1, x0:x1 + 1] = 0
        for j in range(reg.shape[0]):
            for i in range(reg.shape[1]):
                if reg[j, i, 3] > 0:
                    cv.put(tx + i, ty + j, tuple(reg[j, i]))
    elif k == "smear":
        cx, cy = pt(pos[0])
        r = [float(v) for v in pos[1].split(",")]
        tones = tone_list(flags.get("tones", "w,P,p"))
        smear_arc(cv, cx, cy, r[0], r[-1], float(pos[2]), float(pos[3]), float(pos[4]), tones,
                  flags.get("taper", "lead"), flags.get("grow", "out"), "over" not in flags)
    elif k == "streak":
        (x0, y0), (x1, y1) = pt(pos[0]), pt(pos[1])
        streak(cv, x0, y0, x1, y1, float(pos[2]), tone_list(flags.get("tones", "w,P,p")),
               flags.get("taper", "lead"), "over" not in flags)
    elif k == "echo":
        (x0, y0), (x1, y1), (dx, dy), n = ipt(pos[0]), ipt(pos[1]), pt(pos[2]), int(pos[3])
        reg = a[y0:y1 + 1, x0:x1 + 1].copy()
        tone = col(flags["tone"]) if "tone" in flags else None
        for kk in range(n, 0, -1):
            ox, oy = int(round(dx * kk / n)), int(round(dy * kk / n))
            for j, i in zip(*np.nonzero(reg[..., 3] > 0)):
                cv.put(x0 + i + ox, y0 + j + oy, tone or tuple(reg[j, i]), True)
    elif k == "speed":
        (x, y), (dx, dy), n, L, gap, c = pt(pos[0]), pt(pos[1]), int(pos[2]), float(pos[3]), float(pos[4]), col(pos[5])
        Ln = math.hypot(dx, dy) or 1
        ux, uy = dx / Ln, dy / Ln
        for i in range(n):
            off = (i - (n - 1) / 2) * gap
            sx, sy = x - uy * off, y + ux * off
            ll = max(1.0, L - abs(i - (n - 1) / 2))
            p = bresenham(int(round(sx)), int(round(sy)), int(round(sx + ux * ll)), int(round(sy + uy * ll)))
            cv.pts(pixel_perfect(p), c, True)
    elif k == "outline":
        c = col(pos[0]) if pos else col("K")
        op = a[..., 3] > 0
        grow = np.zeros_like(op)
        for dy, dx in H.N4:
            grow |= H.shift(op, dy, dx, False)
        grow &= ~op
        a[grow] = c
    else:
        raise SystemExit(f"unknown op {k!r} in {op!r}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("input", help="PNG or .pix ('new' with --new WxH for a blank canvas)")
    ap.add_argument("ops", nargs="*")
    ap.add_argument("--out", required=True)
    ap.add_argument("--ops-file", "--ops", dest="ops_file")
    ap.add_argument("--new", help="WxH blank canvas when input is 'new'")
    ap.add_argument("--preview", type=int, default=0, help="also write OUT_x<N>.png on grey with grid")
    a = ap.parse_args()
    if a.input == "new":
        w, h = (int(v) for v in (a.new or "128x128").split("x"))
        img = np.zeros((h, w, 4), np.uint8)
    else:
        img = PG.load(a.input)[0].copy()
    ops = list(a.ops)
    if a.ops_file:
        ops += [l.split("#", 1)[0].strip() for l in open(a.ops_file) if l.split("#", 1)[0].strip()]
    cv = Canvas(img)
    base_dir = os.path.dirname(os.path.abspath(a.input)) if a.input != "new" else os.getcwd()
    for op in ops:
        run_op(cv, op, base_dir)
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    if a.out.endswith(".pix"):
        tmp = a.out + ".tmp.png"
        Image.fromarray(cv.a, "RGBA").save(tmp)
        open(a.out, "w").write(PG.from_image(tmp))
        os.remove(tmp)
    else:
        Image.fromarray(cv.a, "RGBA").save(a.out)
    if a.preview:
        PG.to_image(cv.a, a.preview, "#8c8c8c", True).save(os.path.splitext(a.out)[0] + f"_x{a.preview}.png")
    st = PG.stats(cv.a)
    st.pop("orphan_xy")
    for l in cv.log:
        print(" ", l)
    print(f"draw: {len(ops)} ops -> {a.out} {st}")


if __name__ == "__main__":
    main()
