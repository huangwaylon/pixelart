"""compose a sprite from hand-authored layers. usage: compose.py <name> (reads frames.py spec)"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from build import *

SRC = os.path.join(OUT, "src")


def read_body(fn):
    rows = []
    hdr = None
    for ln in open(os.path.join(SRC, fn)):
        ln = ln.rstrip("\n")
        if ln.startswith("#"):
            hdr = ln
            continue
        if ln.strip() == "":
            continue
        rows.append(ln)
    return rows


def blank():
    return np.full((128, 128), ".", "<U1")


def fist(cv, x, y, w=2, h=2, tones=("s", "m")):
    for dy in range(h):
        for dx in range(w):
            cv.put(x + dx, y + dy, tones[0] if dy == 0 else tones[1])
    for dy in range(-1, h + 1):
        for dx in range(-1, w + 1):
            if 0 <= dx < w and 0 <= dy < h:
                continue
            if (dx in (-1, w)) and (dy in (-1, h)):
                continue
            if cv.get(x + dx, y + dy) == ".":
                cv.put(x + dx, y + dy, "K")


def _pixel_perfect(pts):
    out = []
    for p in pts:
        if out and out[-1][:2] == p[:2]:
            continue
        out.append(p)
        if len(out) >= 3:
            (ax, ay, _), (bx, by, _), (cx, cy, _) = out[-3:]
            if (ax == bx or ay == by) and (bx == cx or by == cy) and abs(ax - cx) == 1 and abs(ay - cy) == 1:
                del out[-2]          # drop the L-corner pixel (R17 pixel-perfect)
    return out


def ribbon(cv, pts, tones=("P", "p"), behind=True, outline=False, root=3):
    """ribbon strip along a polyline: pixel-perfect 1 px line, doubled to 2 px (shadow tone, below)
    for the first `root` pixels so it tapers from the collar to a 1 px tip; tone alternates per
    segment so it reads as a twisting strip."""
    allp = []
    for i in range(len(pts) - 1):
        seg = line_pts(*pts[i], *pts[i + 1])
        if i:
            seg = seg[1:]
        allp += [(x, y, tones[i % len(tones)]) for x, y in seg]
    allp = _pixel_perfect(allp)
    for i, (x, y, c) in enumerate(allp):
        cv.put(x, y, c, behind)
        if i < root:
            cv.put(x, y + 1, "p", True)
    return allp


def katana_stamp(cv, name, x, y, rows=None, flip=False, behind=False):
    k = stamp(name)
    if rows:
        k = k[:rows]
    if flip:
        k = k[:, ::-1]
    cv.stamp(k, x, y, behind)


BOW_OFF = {"SE": (8, 0), "S": None, "E": None, "N": None}


def head(cv, d, x, y, bow_dy=0, bow_dx=0):
    """paste head_<d>; optionally offset the locked bow cel (bow_<d>) by (bow_dx, bow_dy) for lag."""
    h = stamp("head_" + d)
    cv.stamp(h, x, y)
    if not (bow_dy or bow_dx):
        return
    bname = {"SE": "bow_SE", "S": "bow_S", "E": "bow_E", "N": "bow_N", "SW": "bow_SE", "W": "bow_E"}[d]
    b = stamp(bname)
    mirror = d in ("SW", "W")
    if mirror:
        b = b[:, ::-1]
    # locate the cel inside the head stamp by exact match
    hr, br = rgba_to_chars(h), rgba_to_chars(b)
    bh, bw = len(br), len(br[0])
    best = None
    for oy in range(0, 4):
        for ox in range(0, len(hr[0]) - bw + 1):
            ok = sum(1 for yy in range(bh) for xx in range(bw)
                     if br[yy][xx] != "." and hr[oy + yy][ox + xx] == br[yy][xx])
            tot = sum(1 for yy in range(bh) for xx in range(bw) if br[yy][xx] != ".")
            if best is None or ok > best[0]:
                best = (ok, ox, oy, tot)
    _, ox, oy, _ = best
    # erase the cel footprint, restore hair underneath from the head, then paste the cel offset
    for yy in range(bh):
        for xx in range(bw):
            if br[yy][xx] != ".":
                c = hr[oy + yy][ox + xx]
                cv.put(x + ox + xx, y + oy + yy, c if (c in "hHJ" and br[yy][xx] in "hHJ") else ".")
    # under the moved bow: fill holes inside the dome with hair_0
    cv.stamp(b, x + ox + bow_dx, y + oy + bow_dy)
    for yy in range(bh + 1):
        for xx in range(bw):
            X, Y = x + ox + xx, y + oy + yy
            if cv.get(X, Y) == "." and cv.get(X - 1, Y) != "." and cv.get(X + 1, Y) != "." and cv.get(X, Y + 1) != ".":
                cv.put(X, Y, "h")


def shift_region(cv, x0, y0, x1, y1, dx, dy, fill="."):
    sub = cv.g[y0:y1 + 1, x0:x1 + 1].copy()
    cv.g[y0:y1 + 1, x0:x1 + 1] = fill
    for yy in range(sub.shape[0]):
        for xx in range(sub.shape[1]):
            if sub[yy, xx] != ".":
                cv.put(x0 + xx + dx, y0 + yy + dy, sub[yy, xx])


def erase(cv, x0, y0, x1, y1):
    cv.g[max(0, y0):y1 + 1, max(0, x0):x1 + 1] = "."


def close_outline(cv, x0=0, y0=0, x1=127, y1=127, skip="wtTPpE"):
    """add K wherever a filled pixel touches transparency on a 4-side and is not already dark/outline."""
    g = cv.g.copy()
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            if g[y, x] != ".":
                continue
            for dy, dx in ((0, 1), (0, -1), (1, 0), (-1, 0)):
                c = cv.get(x + dx, y + dy)
                if c not in ".K" and c not in skip:
                    g[y, x] = "K"
                    break
    cv.g = g
