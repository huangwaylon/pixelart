"""S4 textured-3D cel renderer.

The guide rig render passes (hybrid/guide/p2/<seq>/<DIR>/fNN_{id,clay,depth,mask,joints}) are
"textured" with the iso_v5 illustration's material colours (sampled per material from
concept/chibi_iso_v5.png and snapped to the locked palette) and shaded in flat painterly cel bands
from a heavily smoothed clay (lambert) pass, like iso_v5's 2-tone cel shading.  The head is NOT the
guide's head: the locked pixel head stamp (hybrid/lock/pixel) is pasted on the guide head joint.
The katana is redrawn from the guide's sword joints with the locked katana design.

Library used by tools/hybrid/s4/build_set.py.
"""
import json
import math
import os
import sys

import numpy as np
from PIL import Image, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import hylib as H  # noqa: E402
import pixgrid as PG  # noqa: E402

ROOT = H.ROOT
PAL = json.load(open(os.path.join(ROOT, "docs/palette.json")))
R = PAL["ramps"]


def hx(h):
    h = h.lstrip("#")
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)] + [255], np.uint8)


C = {"K": hx(PAL["outline"])}
for ramp, tones in R.items():
    for i, t in enumerate(tones):
        C[f"{ramp}_{i}"] = hx(t)
LEG = {k: v for k, v in PG.STD.items()}  # char -> palette name


def tone(name):
    if name in ("K", "outline"):
        return C["K"]
    if name in LEG:
        name = LEG[name]
    if name in ("outline",):
        return C["K"]
    return C[name]


# guide id -> material key
ID_MAT = {1: "hair", 2: "hair", 3: "red", 4: "skin", 5: "skin", 6: "collar", 7: "torso", 8: "leather",
          9: "red", 10: "under", 11: "dark", 12: "sleeve", 13: "sleeve", 14: "skin", 15: "skin",
          16: "skin", 17: "skin", 18: "skin", 19: "skin", 20: "shoe", 21: "shoe", 22: "pink", 23: "pink",
          24: "sword", 25: "smear"}
HEAD_IDS = (1, 2, 3, 4, 5)

# cel bands per material: list of (threshold on smoothed light 0..1, tone) from dark to light.
# (light >= thr -> that tone; first entry is the fallback).  Sampled from iso_v5: red dress = red_2 lit
# with red_1 cel shadow and red_0 only in deep folds; skin = skin_1 with skin_0 shade; corset leather_1
# with a leather_2 top edge; shorts dark.
BANDS = {
    "red":     [(0.0, "red_0"), (0.30, "red_1"), (0.56, "red_2")],
    "sleeve":  [(0.0, "red_0"), (0.30, "red_1"), (0.52, "red_2")],
    "collar":  [(0.0, "red_1"), (0.40, "red_2")],
    "torso":   [(0.0, "red_1"), (0.45, "red_2")],
    "under":   [(0.0, "red_0"), (0.62, "red_1")],
    "skin":    [(0.0, "skin_0"), (0.42, "skin_1")],
    "leather": [(0.0, "leather_1")],
    "dark":    [(0.0, "K"), (0.55, "dark_1")],
    "shoe":    [(0.0, "K"), (0.60, "leather_1")],
    "pink":    [(0.0, "pink_0"), (0.50, "pink_1")],
    "hair":    [(0.0, "hair_0"), (0.6, "hair_1")],
}
SELOUT = {"red": "red_1", "sleeve": "red_1", "collar": "red_1", "torso": "red_1", "under": "red_0",
          "skin": "skin_0", "pink": "pink_0"}


def load(p):
    return np.array(Image.open(p).convert("RGBA"))


def affine(img, sx, sy, pivot=(512, 832), nearest=False):
    """scale an image about the pivot (output = input scaled)."""
    im = Image.fromarray(img)
    px, py = pivot
    # PIL affine maps output -> input: x_in = (x_out - px)/sx + px
    coeffs = (1 / sx, 0, px - px / sx, 0, 1 / sy, py - py / sy)
    res = Image.NEAREST if nearest else Image.BILINEAR
    return np.array(im.transform(im.size, Image.AFFINE, coeffs, resample=res))


class Frame:
    def __init__(self, prefix, sx=1.0, sy=1.0):
        self.prefix = prefix
        self.sx, self.sy = sx, sy
        idp = load(prefix + "_id.png")
        cl = load(prefix + "_clay.png")
        dp = load(prefix + "_depth.png")
        self.id = affine(idp, sx, sy, nearest=True)
        self.clay = affine(cl, sx, sy)
        self.depth = affine(dp, sx, sy, nearest=True)
        j = json.load(open(prefix + "_joints.json"))
        self.joints = {}
        self.raw = {}
        self.ids_raw = np.where(idp[..., 3] >= 128, idp[..., 0].astype(int) // 10, 0)
        for k, v in j["joints"].items():
            self.raw[k] = (v["px"][0] / 8.0, v["px"][1] / 8.0)
            x, y = v["px"]
            x = (x - 512) * sx + 512
            y = (y - 832) * sy + 832
            self.joints[k] = (x / 8.0, y / 8.0, v.get("depth", 0), v.get("visible", True))
        self.ids = np.where(self.id[..., 3] >= 128, self.id[..., 0].astype(int) // 10, 0)

    def light(self, sigma=10):
        """smoothed clay luminance, normalised 0..1 over the figure (per-material smoothing)."""
        lum = self.clay[..., 0].astype(float)
        a = self.ids > 0
        lo, hi = np.percentile(lum[a], 3), np.percentile(lum[a], 97)
        n = np.clip((lum - lo) / max(1, hi - lo), 0, 1)
        out = np.zeros_like(n)
        # smooth inside each material only (avoid bleeding across parts)
        for mid in np.unique(self.ids[a]):
            m = self.ids == mid
            img = Image.fromarray((n * m * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(sigma))
            w = Image.fromarray((m * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(sigma))
            num = np.array(img).astype(float)
            den = np.array(w).astype(float) + 1e-6
            out[m] = (num / den)[m]
        return out


def band_tone(mat, v):
    t = BANDS[mat][0][1]
    for thr, nm in BANDS[mat]:
        if v >= thr:
            t = nm
    return t


def cel_hires(fr, drop_head=True):
    """1024 cel-shaded colour image (the textured 3D render)."""
    L = fr.light()
    out = np.zeros(fr.id.shape, np.uint8)
    for mid, mat in ID_MAT.items():
        m = fr.ids == mid
        if not m.any():
            continue
        if mat == "sword":
            out[m] = C["steel_1"]
            continue
        if mat == "smear":
            continue
        if drop_head and mid in HEAD_IDS:
            continue
        b = BANDS[mat]
        for thr, nm in b:
            sel = m & (L >= thr)
            out[sel] = tone(nm)
    return out, L


def reduce_cell(fr, L, drop_head=True, cover=0.5):
    """8x8 block reduce to a 128 cell: material = majority id, tone = band(mean light)."""
    ids = fr.ids.copy()
    if drop_head:
        for h in HEAD_IDS:
            ids[ids == h] = 0
    ids[ids == 25] = 0
    ids[ids == 24] = 0  # sword is redrawn
    b = ids.reshape(128, 8, 128, 8).transpose(0, 2, 1, 3).reshape(128, 128, 64)
    Lb = L.reshape(128, 8, 128, 8).transpose(0, 2, 1, 3).reshape(128, 128, 64)
    cell_id = np.zeros((128, 128), int)
    cell_L = np.zeros((128, 128))
    for y in range(128):
        for x in range(128):
            v = b[y, x]
            nz = v[v > 0]
            # thin parts (scarf, arms, legs) survive at a lower coverage
            if len(nz) == 0:
                continue
            cnt = np.bincount(nz, minlength=26)
            top = cnt.argmax()
            thin = top in (22, 23, 14, 15, 16, 17)
            need = 64 * (0.3 if thin else cover)
            if len(nz) < need:
                continue
            cell_id[y, x] = top
            cell_L[y, x] = Lb[y, x][v == top].mean()
    return cell_id, cell_L


def majority_clean(img, ids, it=2):
    """remove 1 px tone orphans inside a material (same id, different tone, no same-tone 4-neighbour)."""
    H_, W_ = ids.shape
    for _ in range(it):
        changed = 0
        for y in range(1, H_ - 1):
            for x in range(1, W_ - 1):
                i = ids[y, x]
                if i == 0:
                    continue
                c = tuple(img[y, x])
                same = 0
                nb = []
                for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    if ids[y + dy, x + dx] == i:
                        nb.append(tuple(img[y + dy, x + dx]))
                        if tuple(img[y + dy, x + dx]) == c:
                            same += 1
                if same == 0 and len(nb) >= 3:
                    vals, cnts = np.unique(np.array(nb), axis=0, return_counts=True)
                    img[y, x] = vals[cnts.argmax()]
                    changed += 1
        if not changed:
            break
    return img


def paint_cells(cell_id, cell_L):
    img = np.zeros((128, 128, 4), np.uint8)
    for y in range(128):
        for x in range(128):
            i = cell_id[y, x]
            if i == 0:
                continue
            mat = ID_MAT[i]
            img[y, x] = tone(band_tone(mat, cell_L[y, x]))
    return img


def outline(img, ids, interior=True):
    """selective outline: exterior 1 px outline (dark everywhere = K; lit top-left uses the material's
    dark tone), plus interior part-boundary lines where a nearer part overlaps a different material."""
    a = img[..., 3] > 0
    out = img.copy()
    Hh, Ww = a.shape
    ext = np.zeros_like(a)
    for y in range(1, Hh - 1):
        for x in range(1, Ww - 1):
            if a[y, x]:
                continue
            if a[y - 1, x] or a[y + 1, x] or a[y, x - 1] or a[y, x + 1]:
                ext[y, x] = True
    # exterior outline painted outside the figure (keeps the silhouette, adds 1 px)
    for y, x in zip(*np.nonzero(ext)):
        out[y, x] = C["K"]
    return out


def paste_stamp(img, stamp, x0, y0, mask_keep=None):
    h, w = stamp.shape[:2]
    for yy in range(h):
        for xx in range(w):
            if stamp[yy, xx, 3] == 0:
                continue
            X, Y = x0 + xx, y0 + yy
            if 0 <= X < 128 and 0 <= Y < 128:
                if mask_keep is not None and mask_keep[Y, X]:
                    continue
                img[Y, X] = stamp[yy, xx]
    return img


def line_pts(x0, y0, x1, y1):
    x0, y0, x1, y1 = int(round(x0)), int(round(y0)), int(round(x1)), int(round(y1))
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
    # pixel-perfect: drop L corners
    pp = []
    i = 0
    while i < len(pts):
        if 0 < i < len(pts) - 1:
            a, b, c = pts[i - 1], pts[i], pts[i + 1]
            if (a[0] == b[0] or a[1] == b[1]) and (b[0] == c[0] or b[1] == c[1]) and a[0] != c[0] and a[1] != c[1]:
                i += 1
                continue
        pp.append(pts[i])
        i += 1
    return pp


# ---------------------------------------------------------------- katana (locked design, any angle)
def _perp(dx, dy):
    n = (dx * dx + dy * dy) ** 0.5 or 1
    return -dy / n, dx / n


def draw_katana(fr, img, guide_vis, pommel=None, guard=None, tip=None, hook_side=1):
    """Draw the locked katana from guide joints. guide_vis: 128x128 bool, guide sword visible there
    (drawn over the body); elsewhere only on transparent pixels (behind).  Returns the katana layer
    mask (pixels drawn)."""
    J = fr.joints
    off = np.array(J["hand_L"][:2]) - np.array(fr.raw["hand_L"])
    P = np.array(pommel) if pommel is not None else np.array(fr.raw["sword_pommel"]) + off
    G = np.array(guard) if guard is not None else np.array(fr.raw["sword_guard"]) + off
    T = np.array(tip) if tip is not None else np.array(fr.raw["sword_tip"]) + off
    layer = {}

    def put(x, y, c, prio):
        x, y = int(round(x)), int(round(y))
        if not (0 <= x < 128 and 0 <= y < 128):
            return
        if (x, y) in layer and layer[(x, y)][1] > prio:
            return
        layer[(x, y)] = (c, prio)

    d = T - G
    L = np.hypot(*d)
    # snap the blade to a clean pixel ratio (0, 1:3, 1:2, 1:1, 2:1, 3:1, vertical): even steps, no
    # 1-2-1-2 staircase wobble on a straight blade (rotation <= ~9 deg)
    ang = math.atan2(d[1], d[0])
    cands = []
    for rx_, ry_ in ((1, 0), (3, 1), (2, 1), (1, 1), (1, 2), (1, 3), (0, 1)):
        for sx_ in (1, -1):
            for sy_ in (1, -1):
                cands.append(math.atan2(ry_ * sy_, rx_ * sx_))
    a2 = min(cands, key=lambda c: abs(math.atan2(math.sin(c - ang), math.cos(c - ang))))
    T = G + L * np.array([math.cos(a2), math.sin(a2)])
    d = T - G
    u = d / L
    px_, py_ = _perp(*u)
    # offset axis for 2 px parts (blade spine/edge)
    off = np.array([0, 1]) if abs(u[0]) > abs(u[1]) else np.array([1, 0])
    # blade: steel_2 edge on the light (upper/left) side, steel_0 spine
    bl = line_pts(G[0] + u[0] * 1.5, G[1] + u[1] * 1.5, T[0], T[1])
    for i, (x, y) in enumerate(bl):
        put(x, y, "steel_2", 3)
        if i < len(bl) - 1:
            put(x + off[0], y + off[1], "steel_0", 2)
    # habaki
    put(G[0] + u[0] * 1, G[1] + u[1] * 1, "steel_1", 4)
    # hilt: 2 px wrap with red diamonds, outlined
    hd = P - G
    hl = line_pts(G[0] - u[0] * 0.0 + hd[0] * 0.15, G[1] + hd[1] * 0.15, P[0], P[1])
    for i, (x, y) in enumerate(hl):
        put(x, y, "red_2" if i % 2 else "dark_1", 5)
        put(x + off[0], y + off[1], "dark_1" if i % 2 else "red_2", 5)
    if hl:
        x, y = hl[-1]
        put(x, y, "steel_1", 6)
        put(x + off[0], y + off[1], "steel_1", 6)
    # guard bar (perpendicular, 2 px each side) + crescent kagi on one end
    for s in (-2, -1, 0, 1, 2):
        put(G[0] + px_ * s, G[1] + py_ * s, "steel_1", 7)
    hx_, hy_ = G[0] + px_ * 2.6 * hook_side, G[1] + py_ * 2.6 * hook_side
    put(hx_ + u[0] * 1.2, hy_ + u[1] * 1.2, "steel_1", 7)   # hook horn toward the blade
    put(hx_ - u[0] * 1.0, hy_ - u[1] * 1.0, "steel_1", 7)   # horn toward the hilt (notch between)
    # outline around hilt + guard only (blade has no outline: R20)
    keys = [k for k, v in layer.items() if v[0] not in ("steel_2", "steel_0")]
    for (x, y) in keys:
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            k = (x + dx, y + dy)
            if k not in layer:
                layer[k] = ("K", 1)
    drawn = np.zeros((128, 128), bool)
    for (x, y), (c, pr) in layer.items():
        if not (0 <= x < 128 and 0 <= y < 128):
            continue
        front = guide_vis[max(0, y - 1):y + 2, max(0, x - 1):x + 2].any()
        if front or img[y, x, 3] == 0:
            img[y, x] = tone(c)
            drawn[y, x] = True
    return drawn


def guide_sword_visible(fr):
    """sword-visible map from the UNSCALED guide (the katana is rigid), moved with the scaled hand."""
    s = (fr.ids_raw == 24).reshape(128, 8, 128, 8).sum(axis=(1, 3)) >= 3
    off = np.array(fr.joints["hand_L"][:2]) - np.array(fr.raw["hand_L"])
    dx, dy = int(round(off[0])), int(round(off[1]))
    return np.roll(np.roll(s, dy, 0), dx, 1)


def draw_fist(img, x, y, side=1):
    x, y = int(round(x)), int(round(y))
    pat = [".KKK.", "KssmK", "KsmmK", ".KKK."]
    for j, row in enumerate(pat):
        for i, ch in enumerate(row):
            if ch == ".":
                continue
            X, Y = x - 2 + i, y - 2 + j
            if 0 <= X < 128 and 0 <= Y < 128:
                img[Y, X] = tone(ch)


def load_stamp(name, src_dir=None):
    p = os.path.join(src_dir or os.path.join(ROOT, "hybrid/lock/pixel"), name + ".png")
    return np.array(Image.open(p).convert("RGBA"))


# ---------------------------------------------------------------- pass B helpers
def reveal_legs(fr, ns_prefix, hem_y_cell):
    """skirt_outer pixels below the front-hem line show what is behind the skirt (legs, shorts,
    shoes) from the skirt-hidden guide render: iso_v5's short front panel with pale legs."""
    idn = affine(load(ns_prefix + "_id.png"), fr.sx, fr.sy, nearest=True)
    cln = affine(load(ns_prefix + "_clay.png"), fr.sx, fr.sy)
    idsn = np.where(idn[..., 3] >= 128, idn[..., 0].astype(int) // 10, 0)
    yy = np.arange(1024)[:, None] * np.ones((1, 1024))
    m = (fr.ids == 9) & (yy >= hem_y_cell * 8) & np.isin(idsn, [11, 18, 19, 20, 21, 10])
    fr.ids[m] = idsn[m]
    fr.clay[m] = cln[m]
    return m.sum()


def cluster_clean(img, ids, min_px=4):
    """recolour tone clusters smaller than min_px (4-conn, same id) to the dominant neighbouring tone
    of the same part: deliberate big cel clusters instead of render noise."""
    Hh, Ww = ids.shape
    key = np.zeros((Hh, Ww), np.int64)
    a = img[..., 3] > 0
    col = (img[..., 0].astype(np.int64) << 16) | (img[..., 1].astype(np.int64) << 8) | img[..., 2]
    seen = np.zeros((Hh, Ww), bool)
    for y in range(Hh):
        for x in range(Ww):
            if seen[y, x] or ids[y, x] == 0:
                continue
            stack = [(y, x)]
            comp = []
            seen[y, x] = True
            while stack:
                cy, cx = stack.pop()
                comp.append((cy, cx))
                for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    ny, nx = cy + dy, cx + dx
                    if 0 <= ny < Hh and 0 <= nx < Ww and not seen[ny, nx] and ids[ny, nx] == ids[y, x] \
                            and col[ny, nx] == col[y, x]:
                        seen[ny, nx] = True
                        stack.append((ny, nx))
            if len(comp) >= min_px:
                continue
            nb = {}
            cs = set(comp)
            for cy, cx in comp:
                for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    ny, nx = cy + dy, cx + dx
                    if 0 <= ny < Hh and 0 <= nx < Ww and (ny, nx) not in cs and ids[ny, nx] == ids[y, x]:
                        nb[col[ny, nx]] = nb.get(col[ny, nx], 0) + 1
            if nb:
                c = max(nb, key=nb.get)
                for cy, cx in comp:
                    img[cy, cx, :3] = [(c >> 16) & 255, (c >> 8) & 255, c & 255]
    return img


def ribbon_paths(fr, sid):
    """centre line of a scarf ribbon (guide id sid) in cell coords, root (near the collar) first."""
    ys, xs = np.nonzero(fr.ids == sid)
    if len(xs) < 40:
        return []
    P = np.stack([xs, ys], 1).astype(float)
    mu = P.mean(0)
    U, S, Vt = np.linalg.svd(P - mu, full_matrices=False)
    ax = Vt[0]
    t = (P - mu) @ ax
    bins = np.arange(t.min(), t.max() + 8, 8)
    pts = []
    for b0, b1 in zip(bins[:-1], bins[1:]):
        s = (t >= b0) & (t < b1)
        if s.sum() < 6:
            continue
        pts.append(P[s].mean(0) / 8.0)
    if not pts:
        return []
    # root = end nearest the neck
    nx, ny = fr.joints["neck"][:2]
    if np.hypot(pts[0][0] - nx, pts[0][1] - ny) > np.hypot(pts[-1][0] - nx, pts[-1][1] - ny):
        pts = pts[::-1]
    return pts


def draw_ribbon(img, pts, front=True, wave=None, body=None, keep_root=3):
    """1-2 px tapering pink ribbon along pts: pink_1 lit core, pink_0 shade on the lower side for the
    root half; the tail is 1 px pink_0."""
    if len(pts) < 2:
        return
    n = len(pts)
    path = []
    for i in range(n - 1):
        seg = line_pts(pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1])
        path += seg if not path else seg[1:]
    L = len(path)
    for k, (x, y) in enumerate(path):
        if not (0 <= x < 128 and 0 <= y < 128):
            continue
        f = k / max(1, L - 1)
        if not front and img[y, x, 3] > 0:
            continue
        if body is not None and k >= keep_root and body[y, x]:
            continue
        img[y, x] = tone("pink_1" if f < 0.7 else "pink_0")
        if f < 0.45 and y + 1 < 128 and (front or img[y + 1, x, 3] == 0) and \
                (body is None or k < keep_root or not body[y + 1, x]):
            img[y + 1, x] = tone("pink_0")


def absorb_small_parts(ci, cl, ids=(8, 10, 11, 7, 6), min_px=6):
    """small disconnected islands of minor parts (pouch, under-skirt, shorts, torso bits) inside
    another part take that part's id + light: no 3-4 px noise islands at sprite scale."""
    Hh, Ww = ci.shape
    seen = np.zeros_like(ci, bool)
    for y in range(Hh):
        for x in range(Ww):
            i = ci[y, x]
            if seen[y, x] or i not in ids:
                continue
            comp, st = [], [(y, x)]
            seen[y, x] = True
            while st:
                cy, cx = st.pop()
                comp.append((cy, cx))
                for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    ny, nx = cy + dy, cx + dx
                    if 0 <= ny < Hh and 0 <= nx < Ww and not seen[ny, nx] and ci[ny, nx] == i:
                        seen[ny, nx] = True
                        st.append((ny, nx))
            if len(comp) >= min_px:
                continue
            nb = {}
            cs = set(comp)
            for cy, cx in comp:
                for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    ny, nx = cy + dy, cx + dx
                    if 0 <= ny < Hh and 0 <= nx < Ww and (ny, nx) not in cs and ci[ny, nx] > 0:
                        nb[ci[ny, nx]] = nb.get(ci[ny, nx], 0) + 1
            if nb:
                t = max(nb, key=nb.get)
                for cy, cx in comp:
                    ci[cy, cx] = t
    return ci, cl


def despike(ci, it=2, y_from=0):
    """shorten 1 px icicles on hems: an opaque px with both side neighbours empty and nothing below."""
    for _ in range(it):
        rm = []
        Hh, Ww = ci.shape
        for y in range(y_from, Hh - 1):
            for x in range(1, Ww - 1):
                if ci[y, x] and not ci[y, x - 1] and not ci[y, x + 1] and not ci[y + 1, x] \
                        and ci[y, x] in (9, 10, 12, 13):
                    rm.append((y, x))
        for y, x in rm:
            ci[y, x] = 0
    return ci


def katana_pts(fr):
    """drawn (rigid) katana pommel, guard, tip in cell coords."""
    off = np.array(fr.joints["hand_L"][:2]) - np.array(fr.raw["hand_L"])
    return [np.array(fr.raw[k]) + off for k in ("sword_pommel", "sword_guard", "sword_tip")]


def polish_parts(img, ci):
    """rule-based paint-over on the reduced cell (pass 2):
    - corset: clean band = leather_2 top lip, leather_1 body, 1 steel_1 buckle px per 3 columns on the
      middle row (iso_v5 double buckles), outline row under it where it meets the skirt;
    - collar: top-row lit lip red_2, flare tips (1 px up-out) on both ends of the collar's top row;
    - legs: skin_1 body with skin_0 only on the right-most column (shadow side)."""
    Hh, Ww = ci.shape
    cor = ci == 8
    if cor.any():
        cols = np.nonzero(cor.any(0))[0]
        for x in cols:
            ys = np.nonzero(cor[:, x])[0]
            for y in ys:
                img[y, x] = tone("leather_1")
            img[ys.min(), x] = tone("leather_2")
            if len(ys) >= 3:
                mid = ys[len(ys) // 2]
                if (x - cols.min()) % 3 == 1:
                    img[mid, x] = tone("steel_1")
            yb = ys.max() + 1
            if yb < Hh and ci[yb, x] in (9, 10):
                img[yb, x] = tone("K")
    col = ci == 6
    if col.any():
        ys, xs = np.nonzero(col)
        top = ys.min()
        for y in range(top, top + 1):
            for x in np.nonzero(col[y])[0]:
                img[y, x] = tone("red_2")
        # flare tips: the outer ends of the collar's top two rows get a 1 px point up-out
        row = np.nonzero(col[top] | (col[top + 1] if top + 1 < Hh else col[top]))[0]
        if len(row):
            for x, s in ((row.min(), -1), (row.max(), 1)):
                X, Y = x + s, top - 1
                if 0 <= X < Ww and 0 <= Y and img[Y, X, 3] == 0:
                    img[Y, X] = tone("red_2")
                    # keep the outline closed around the tip
                    for dx, dy in ((s, 0), (0, -1)):
                        if img[Y + dy, X + dx, 3] == 0:
                            img[Y + dy, X + dx] = tone("K")
    for lid in (18, 19):
        m = ci == lid
        for y in np.unique(np.nonzero(m)[0]):
            xs = np.nonzero(m[y])[0]
            for x in xs:
                img[y, x] = tone("skin_1")
            if len(xs) >= 3:
                img[y, xs.max()] = tone("skin_0")
    return img


def clip_ribbon(pts_path_img, body_alpha, keep_root=3):
    return None


def collar_band(img, st, x0, y0, d):
    """tall flared funnel collar round the jaw (front-ish views): a red wedge hugging the lowest 5
    rows of the jaw on each side, widest at the top (tucks under the side locks), lit red_2 on the
    key-light (left) side and red_1 on the right, outlined outside.  Never paints over the stamp."""
    if d in ("N", "NE", "NW"):
        return img
    sh, sw = st.shape[:2]
    a = st[..., 3] > 0
    widths = [3, 3, 2, 2, 1]
    rows = list(range(sh - 5, sh))
    sides = {"E": (-1,), "W": (1,)}.get(d, (-1, 1))
    for s_ in sides:
        lit = "red_2" if s_ < 0 else "red_1"
        for r, w in zip(rows, widths):
            xs = np.nonzero(a[r])[0]
            if not len(xs):
                continue
            edge = xs.min() if s_ < 0 else xs.max()
            for k in range(1, w + 1):
                X, Y = x0 + edge + s_ * k, y0 + r
                if 0 <= X < 128 and 0 <= Y < 128:
                    img[Y, X] = tone(lit if k < w or w == 1 else "red_1" if s_ < 0 else "red_0")
            X = x0 + edge + s_ * (w + 1)
            if 0 <= X < 128:
                img[y0 + r, X] = tone("K")
        # flare tip: one px up-out above the widest row, outlined
        r = rows[0]
        xs = np.nonzero(a[r])[0]
        if len(xs):
            edge = xs.min() if s_ < 0 else xs.max()
            X, Y = x0 + edge + s_ * 3, y0 + r - 1
            if 0 <= X < 128 and Y > 0 and not (0 <= Y - y0 < sh and 0 <= X - x0 < sw and a[Y - y0, X - x0]):
                img[Y, X] = tone("red_2")
                img[Y - 1, X] = tone("K")
                if 0 <= X + s_ < 128:
                    img[Y, X + s_] = tone("K")
    return img


def smooth_hem(ci, it=4):
    """remove 1-2 px wide spikes (icicles) hanging from skirt/sleeve hems: a column run at the very
    bottom whose width <= 2 and with empty sides gets trimmed one row per iteration."""
    Hh, Ww = ci.shape
    for _ in range(it):
        rm = []
        for y in range(1, Hh - 1):
            for x in range(1, Ww - 2):
                if ci[y, x] in (9, 10, 12, 13) and not ci[y + 1, x]:
                    # width of this bottom run
                    x1 = x
                    while x1 + 1 < Ww and ci[y, x1 + 1] and not ci[y + 1, x1 + 1]:
                        x1 += 1
                    if x1 - x + 1 <= 2 and not ci[y, x - 1] and not ci[y, x1 + 1]:
                        # protruding: the row above is wider
                        if ci[y - 1, max(0, x - 1)] or ci[y - 1, min(Ww - 1, x1 + 1)]:
                            continue
                        rm += [(y, xx) for xx in range(x, x1 + 1)]
        for y, x in rm:
            ci[y, x] = 0
    return ci


def strappy_heels(img, ci):
    """shoes: sole + heel outline, crossed straps over skin on the upper rows (iso_v5 strappy heels)."""
    for sid in (20, 21):
        m = ci == sid
        if not m.any():
            continue
        ys, xs = np.nonzero(m)
        top, bot = ys.min(), ys.max()
        for y, x in zip(ys, xs):
            if y < bot and y <= top + 1:
                img[y, x] = tone("skin_1" if (x + y) % 2 == 0 else "K")
            else:
                img[y, x] = tone("K") if y == bot else tone("leather_1")
    return img
