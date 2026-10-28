"""S4 r1 polish helpers: exact-pixel edits on 128-cell palette sprites (numpy RGBA)."""
import os, sys
import numpy as np
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import hylib as H  # noqa
import pixgrid as PG  # noqa
PAL = H.palette()
LOG = []


def T(c):
    if c in PG.STD:
        c = PG.STD[c]
    if c in ("transparent", "clear", "."):
        return np.array([0, 0, 0, 0], np.uint8)
    return np.array(PAL.rgba(PAL.resolve(c)), np.uint8)


def load(p):
    return np.array(Image.open(p).convert("RGBA"))


def save(a, p):
    Image.fromarray(a).save(p)


def name_at(a, x, y):
    if a[y, x, 3] == 0:
        return "."
    k = tuple(int(v) for v in a[y, x, :3])
    for ch, n in PG.STD.items():
        if n == "transparent":
            continue
        if tuple(T(n)[:3]) == k:
            return ch
    return "?"


def group(a, chars):
    cols = np.array([T(c)[:3] for c in chars])
    m = (a[..., None, :3] == cols[None, None]).all(-1).any(-1) & (a[..., 3] > 0)
    return m


def put(a, x, y, c, behind=False):
    if 0 <= x < 128 and 0 <= y < 128:
        if behind and a[y, x, 3]:
            return
        a[y, x] = T(c)


def stamp(a, x0, y0, rows, behind=False):
    """rows: list of strings of legend chars; '_' keeps, '.' clears."""
    for j, r in enumerate(rows):
        for i, ch in enumerate(r):
            if ch == "_" or ch == " ":
                continue
            put(a, x0 + i, y0 + j, ch, behind=behind)


def top_row(a):
    return int(np.nonzero(a[..., 3].any(1))[0][0])


def label(m):
    lab, n = H.label_cc(m, 8) if hasattr(H, "label_cc") else (None, 0)
    return lab, n


def bow_mask(a, rows=13):
    """red-ramp pixels in the top `rows` of the figure that are 8-connected to the topmost red,
    plus their outline px (K touching the bow)."""
    t = top_row(a)
    red = group(a, "vrRC")
    red[t + rows:] = False
    lab = H.label_cc(red, 8)
    lab = lab[0] if isinstance(lab, tuple) else lab
    ys, xs = np.nonzero(red)
    if not len(ys):
        return red
    # components that reach within 4 rows of the top
    keep = {lab[y, x] for y, x in zip(ys, xs) if y <= t + 4}
    m = np.isin(lab, list(keep)) & red
    K = group(a, "K")
    mo = m.copy()
    for y, x in zip(*np.nonzero(K)):
        if y < t + rows and m[max(0, y - 1):y + 2, max(0, x - 1):x + 2].any():
            mo[y, x] = True
    return mo


def shift_bow(a, dx, dy, why=""):
    if not dx and not dy:
        return a
    m = bow_mask(a)
    hair = group(a, "hHJ")
    out = a.copy()
    src = a.copy()
    for y, x in zip(*np.nonzero(m)):
        nb = [(y + 1, x), (y, x - 1), (y, x + 1), (y - 1, x)]
        hn = [hair[p] and not m[p] for p in nb if 0 <= p[0] < 128 and 0 <= p[1] < 128]
        out[y, x] = T("h") if sum(hn) >= 2 else T(".")
    for y, x in zip(*np.nonzero(m)):
        Y, X = y + dy, x + dx
        if 0 <= Y < 128 and 0 <= X < 128:
            out[Y, X] = src[y, x]
    # re-close outline: transparent px 4-adjacent to moved red -> K ; dangling K next to transparent only
    red = group(out, "vrRC")
    for y, x in zip(*np.nonzero(red)):
        for ddy, ddx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            Y, X = y + ddy, x + ddx
            if out[Y, X, 3] == 0:
                out[Y, X] = T("K")
    # hair px exposed to transparency above (where bow left) -> outline
    hair = group(out, "hHJ")
    for y, x in zip(*np.nonzero(hair)):
        if out[y - 1, x, 3] == 0:
            out[y, x] = T("K")
    LOG.append(f"bow shift ({dx},{dy}) {why}")
    return out


def shift_box(a, x0, y0, x1, y1, dx, dy, fill="."):
    """move the box content (inclusive) by dx,dy; vacated px -> fill; moved px overwrite."""
    out = a.copy()
    sub = a[y0:y1 + 1, x0:x1 + 1].copy()
    out[y0:y1 + 1, x0:x1 + 1] = T(fill)
    for j in range(sub.shape[0]):
        for i in range(sub.shape[1]):
            if sub[j, i, 3]:
                Y, X = y0 + j + dy, x0 + i + dx
                if 0 <= Y < 128 and 0 <= X < 128:
                    out[Y, X] = sub[j, i]
    return out


def line(a, p0, p1, c, behind=False):
    sys.path.insert(0, os.path.dirname(HERE))
    import draw as D
    for x, y in D.pixel_perfect(D.bresenham(*p0, *p1)):
        put(a, x, y, c, behind)


def outline_new(a, before, max_y=127):
    """1px K outline around pixels that were added (opaque now, transparent before)."""
    new = (a[..., 3] > 0) & (before[..., 3] == 0)
    out = a.copy()
    for y, x in zip(*np.nonzero(new)):
        for ddy, ddx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            Y, X = y + ddy, x + ddx
            if 0 <= Y <= max_y and 0 <= X < 128 and out[Y, X, 3] == 0:
                out[Y, X] = T("K")
    return out
