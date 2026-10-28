"""S6 body painter: guide id trace (128 cell) -> designed 2-tone cel paint, contact lines, sel-out.
The result is the UNDERLAY that Claude then edits by hand (frames.py ops + .pix patches)."""
import numpy as np
from common import *

# part -> (light, base, shadow, deep)
TONES = {
    "collar": ("C", "R", "r", "v"), "torso": ("R", "R", "r", "v"), "corset": ("L", "l", "l", "K"),
    "skirt": ("C", "R", "r", "v"), "skirt_under": ("r", "v", "v", "K"), "shorts": ("d", "K", "K", "K"),
    "sleeve_L": ("C", "R", "r", "v"), "sleeve_R": ("C", "R", "r", "v"),
    "arm_L": ("S", "s", "m", "m"), "arm_R": ("S", "s", "m", "m"), "hand_L": ("S", "s", "m", "m"),
    "hand_R": ("S", "s", "m", "m"), "leg_L": ("S", "s", "m", "m"), "leg_R": ("S", "s", "m", "m"),
    "shoe_L": ("d", "K", "K", "K"), "shoe_R": ("d", "K", "K", "K"),
    "scarf_L": ("P", "P", "p", "p"), "scarf_R": ("P", "P", "p", "p"),
}
DARKER = {"C": "R", "R": "r", "r": "v", "v": "K", "S": "s", "s": "m", "m": "K", "P": "p", "p": "m",
          "L": "l", "l": "K", "d": "K", "K": "K", "H": "h", "h": "K", "J": "H"}
SELOUT_LIT = {"red": "r", "skin": "m", "pink": "p", "dark": "K", "leather": "K"}
MAT = {"collar": "red", "torso": "red", "corset": "leather", "skirt": "red", "skirt_under": "red",
       "shorts": "dark", "sleeve_L": "red", "sleeve_R": "red", "arm_L": "skin", "arm_R": "skin",
       "hand_L": "skin", "hand_R": "skin", "leg_L": "skin", "leg_R": "skin", "shoe_L": "dark",
       "shoe_R": "dark", "scarf_L": "pink", "scarf_R": "pink"}
N4 = [(-1, 0), (1, 0), (0, -1), (0, 1)]
N8 = N4 + [(-1, -1), (-1, 1), (1, -1), (1, 1)]


def depth_cell(prefix):
    a = load_rgba(prefix + "_depth.png").astype(float)
    d = a[..., 0]
    d[a[..., 3] < 128] = np.nan
    b = d.reshape(128, 8, 128, 8).transpose(0, 2, 1, 3).reshape(128, 128, 64)
    with np.errstate(all="ignore"):
        return np.nanmax(b, -1)


def mode_filter(lab, mask, it=1):
    """3x3 majority on a label map inside mask (kills render-noise speckle)."""
    h, w = lab.shape
    for _ in range(it):
        out = lab.copy()
        for y in range(h):
            for x in range(w):
                if not mask[y, x]:
                    continue
                win = []
                for dy in (-1, 0, 1):
                    for dx in (-1, 0, 1):
                        yy, xx = y + dy, x + dx
                        if 0 <= yy < h and 0 <= xx < w and mask[yy, xx]:
                            win.append(lab[yy, xx])
                v, c = np.unique(win, return_counts=True)
                if c.max() >= 5:
                    out[y, x] = v[c.argmax()]
        lab = out
    return lab


def paint_body(name, drop=(1, 2, 3, 4, 5, 24, 25), relight=0.0):
    """returns (rgba 128x128 body without head/sword, ids, depth)."""
    ids, clay = trace(GUIDES[name])
    dep = depth_cell(GUIDES[name])
    ids = ids.copy()
    body = ~np.isin(ids, drop) & (ids > 0)
    grid = np.full((128, 128), ".", "<U1")
    # tone level per pixel: 0 light, 1 base, 2 shadow, 3 deep; from clay vs the part's own stats
    lvl = np.ones((128, 128), int)
    ys, xs = np.nonzero(body)
    for pid in np.unique(ids[body]):
        pn = IDN[pid]
        m = (ids == pid) & body
        cv = clay[m]
        cv = cv[~np.isnan(cv)]
        if len(cv) < 3:
            continue
        q_lo, q_hi = np.percentile(cv, [28, 88])
        L = np.ones_like(ids)
        cl = np.nan_to_num(clay, nan=np.median(cv))
        # key light top-left: bias by position inside the part's bbox
        my, mx = np.nonzero(m)
        y0, y1, x0, x1 = my.min(), my.max() + 1, mx.min(), mx.max() + 1
        bias = ((np.arange(128)[None, :] - (x0 + x1) / 2) / max(4, x1 - x0) * 10 +
                (np.arange(128)[:, None] - (y0 + y1) / 2) / max(4, y1 - y0) * 6) * relight
        v = cl - bias
        L = np.where(v < q_lo, 2, 1)
        L = np.where(v > q_hi, 0, L)
        lvl[m] = L[m]
    lvl = mode_filter(lvl, body, 2)
    for y, x in zip(ys, xs):
        pn = IDN[ids[y, x]]
        t = TONES.get(pn)
        if t:
            grid[y, x] = t[lvl[y, x]]
    # contact lines: a pixel touching a nearer, different part of the same material darkens one step
    d = np.nan_to_num(dep, nan=-1)
    g2 = grid.copy()
    for y, x in zip(ys, xs):
        p = ids[y, x]
        for dy, dx in N4:
            yy, xx = y + dy, x + dx
            q = ids[yy, xx]
            if q != p and body[yy, xx] and d[yy, xx] > d[y, x] + 6:
                g2[y, x] = DARKER[grid[y, x]] if MAT.get(IDN[p]) != "dark" else "K"
                if MAT.get(IDN[p]) != MAT.get(IDN[q]) and MAT.get(IDN[p]) in ("red", "skin") and grid[y, x] in "rm":
                    g2[y, x] = "K" if MAT.get(IDN[p]) == "skin" else "v"
                break
    grid = g2
    return grid, ids, dep, body


def outline(grid, protect=None):
    """1 px exterior outline outside the silhouette: K on bottom/right, material-dark sel-out on top/left."""
    h, w = grid.shape
    filled = grid != "."
    out = grid.copy()
    for y in range(h):
        for x in range(w):
            if filled[y, x]:
                continue
            nb = [(dy, dx) for dy, dx in N4 if 0 <= y + dy < h and 0 <= x + dx < w and filled[y + dy, x + dx]]
            if not nb:
                continue
            out[y, x] = "K"
    return out


def selout_inner(grid):
    """turn the outermost ring of lit-side pixels into the material dark tone instead of K (top/left)."""
    h, w = grid.shape
    out = grid.copy()
    for y in range(1, h - 1):
        for x in range(1, w - 1):
            c = grid[y, x]
            if c != "K":
                continue
            # K pixel outside the silhouette on the top/left: find the body pixel below/right
            for dy, dx in ((1, 0), (0, 1)):
                b = grid[y + dy, x + dx]
                if b in "RCrSsPp" and grid[y - dy, x - dx] == ".":
                    out[y, x] = {"R": "r", "C": "r", "r": "v", "S": "m", "s": "m", "P": "p", "p": "m"}[b]
                    break
    return out


def to_rgba(grid):
    return chars_to_rgba(["".join(r) for r in grid])


def from_rgba(a):
    return np.array([list(r) for r in rgba_to_chars(a)])
