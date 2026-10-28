"""Shared helpers for tools/hybrid (pixelize / metrics / sheets / gifs).

Conventions (see tools/hybrid/README.md):
  * cell 128x128, feet pivot (64, 104)  (docs/anim_spec.json, tools/pixel/pxlib.py)
  * STANDARD TEST SET names: turn_<DIR>.png, walk_SE_k0..3.png, slash_SE_k0..2.png, jump_E_apex.png
  * a GUIDE is a file prefix P with (all optional except the mask):
        P_mask.png    silhouette (alpha, or luminance if no alpha). Any size; non-128 square sizes
                      are treated as k x the cell (512 = 4x, 1024 = 8x) and box-reduced.
        P_id.png      object-ID pass, R channel = id * 10 (same as pixel/base/<anim>/_id), alpha >= 128
        P_groups.json {"groups": {name: id}}  (falls back to <dir>/id_groups.json, then pixel/base/idle/_id)
        P_joints.json {"joints": {name: [x, y]}, "space": "cell" (default) | "px", "size": [W, H]}
                      names used by the tools: eye_L, eye_R (or eyes), bow, guard, root, foot_L, foot_R,
                      head_top, hand_L, hand_R, face.  Missing joints are derived from the id pass.
        P_sword.png   sword-only mask (optional; else ids 'sword'/'kagi')
"""
import json
import os
import re
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, "tools", "pixel"))
from pxlib import Palette, hx, to_hex  # noqa: E402,F401

DIRS = ["S", "SE", "E", "NE", "N", "NW", "W", "SW"]
CELL = 128
PIVOT = (64, 104)
STD_NAMES = [f"turn_{d}" for d in DIRS] + [f"walk_SE_k{i}" for i in range(4)] + \
            [f"slash_SE_k{i}" for i in range(3)] + ["jump_E_apex"]
SPRITE_RE = re.compile(r"^(?P<anim>[a-z]+)_(?P<dir>S|SE|E|NE|N|NW|W|SW)(?:_(?P<key>k\d+|f\d+|apex|[a-z]+\d*))?\.png$")
AUX_SUFFIX = ("_4x", "_hires", "_mat", "_src", "_dbg", "_guide", "_cmp")

# ---------------------------------------------------------------- materials
# material -> ramps (palette.json) whose tones it may use; 'outline' is always allowed
MATERIALS = {
    "hair":    ["hair"],
    "red":     ["red"],
    "skin":    ["skin"],
    "face":    ["skin", "eye", "pink"],          # + steel_2 glint (added below)
    "leather": ["leather"],
    "dark":    ["dark"],
    "steel":   ["steel"],
    "sword":   ["steel", "dark", "red"],
    "eye":     ["eye"],                          # + steel_2 glint
    "pink":    ["pink"],                         # + skin_2 lit edge
    "purple":  ["purple"],
}
EXTRA = {"face": ["steel_2"], "eye": ["steel_2"], "pink": ["skin_2"], "purple": ["red_1", "red_2"]}
# lit-side (top/left) selective outline per material (cleanup guide R9); None = leave untouched (R20)
SELOUT_LIT = {"red": "red_1", "skin": "skin_0", "face": "skin_0", "hair": "hair_0", "pink": "pink_0",
              "leather": "outline", "dark": "outline", "eye": "outline", "purple": "purple_0",
              "steel": None, "sword": None}
# id-pass group -> material
GROUP_MAT = {"hair": "hair", "sheen": "hair", "bun": "hair", "bow": "red", "face": "face", "ear": "skin",
             "corset": "leather", "buckles": "steel", "pouch": "leather", "skirt": "red", "skirt_under": "red",
             "sleeve": "red", "ornament": "purple", "scarf": "pink", "sword": "sword", "arm": "skin",
             "hand": "skin", "leg_L": "skin", "leg_R": "skin", "collar": "red", "torso": "red",
             "shorts": "dark", "thigh_strap": "leather", "kagi": "steel"}
MAT_NAMES = list(MATERIALS)
MAT_COLOR = {"hair": (116, 72, 58), "red": (216, 52, 62), "skin": (240, 180, 156), "face": (253, 227, 210),
             "leather": (168, 116, 74), "dark": (80, 68, 98), "steel": (168, 176, 192), "sword": (95, 102, 120),
             "eye": (95, 142, 232), "pink": (248, 181, 200), "purple": (155, 69, 201)}

_PAL = None


def palette():
    global _PAL
    if _PAL is None:
        _PAL = Palette()
    return _PAL


def mat_allowed(mat):
    """canonical palette names a material may use (always includes 'outline')."""
    pal = palette()
    out = ["outline"]
    for rn in MATERIALS[mat]:
        for i in range(len(pal.raw["ramps"][rn])):
            n = pal.alias.get(f"{rn}_{i}", f"{rn}_{i}")
            if n not in out:
                out.append(n)
    for n in EXTRA.get(mat, []):
        n = pal.alias.get(n, n)
        if n not in out:
            out.append(n)
    return out


# ---------------------------------------------------------------- colour
def srgb_to_lab(rgb):
    """(..., 3) uint8/float 0-255 sRGB -> CIELAB (D65)."""
    c = np.asarray(rgb, float) / 255.0
    c = np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
    M = np.array([[0.4124564, 0.3575761, 0.1804375],
                  [0.2126729, 0.7151522, 0.0721750],
                  [0.0193339, 0.1191920, 0.9503041]])
    xyz = c @ M.T / np.array([0.95047, 1.0, 1.08883])
    f = np.where(xyz > 0.008856, np.cbrt(xyz), 7.787 * xyz + 16 / 116)
    L = 116 * f[..., 1] - 16
    a = 500 * (f[..., 0] - f[..., 1])
    b = 200 * (f[..., 1] - f[..., 2])
    return np.stack([L, a, b], -1)


def pal_lab(names):
    pal = palette()
    return srgb_to_lab(np.array([pal.rgb[pal.index[n]] for n in names], float))


def ramp_poly_dist(lab, mat):
    """distance (Lab) from each pixel to the polyline through the material's ramp tones (sorted by L).
    Shading in-between two tones of one ramp is close to the polyline, so this classifies
    'which material is this' far better than nearest-tone (e.g. dark hair vs dark[1])."""
    pal = palette()
    names = [n for n in mat_allowed(mat) if n != "outline"]
    if mat in ("pink",):
        names = [n for n in names if n != "skin_2"]
    if mat in ("face", "eye"):
        names = [n for n in names if n != "steel_2"]
    if mat == "purple":
        names = ["purple_0"]
    P = pal_lab(names)
    P = P[np.argsort(P[:, 0])]
    flat = lab.reshape(-1, 3)
    best = np.full(len(flat), np.inf)
    if len(P) == 1:
        best = np.linalg.norm(flat - P[0], axis=1)
    else:
        for a, b in zip(P[:-1], P[1:]):
            ab = b - a
            t = np.clip(((flat - a) @ ab) / max(ab @ ab, 1e-9), 0, 1)
            d = np.linalg.norm(flat - (a + t[:, None] * ab), axis=1)
            best = np.minimum(best, d)
    return best.reshape(lab.shape[:-1])


# ---------------------------------------------------------------- io
def load_rgba(p):
    return np.array(Image.open(p).convert("RGBA"))


def save_rgba(a, p):
    os.makedirs(os.path.dirname(os.path.abspath(p)), exist_ok=True)
    Image.fromarray(np.asarray(a, np.uint8), "RGBA").save(p)


def up(a, s):
    return np.repeat(np.repeat(a, s, axis=0), s, axis=1)


def is_sprite_name(fn):
    st = os.path.splitext(fn)[0]
    return fn.endswith(".png") and not st.endswith(AUX_SUFFIX) and SPRITE_RE.match(fn) is not None


def list_sprites(d):
    return sorted(f for f in os.listdir(d) if is_sprite_name(f)) if os.path.isdir(d) else []


# ---------------------------------------------------------------- guides
def _to_cell(a, mode):
    """resize a guide image (H, W[, C]) to the 128 cell. mode 'mask' = box + 0.5 threshold, 'id' = majority."""
    H, W = a.shape[:2]
    if (H, W) == (CELL, CELL):
        return a
    if H % CELL or W % CELL or H != W:
        raise ValueError(f"guide image {W}x{H} is not k x {CELL} square")
    k = H // CELL
    if mode == "mask":
        return a.reshape(CELL, k, CELL, k).mean((1, 3)) >= 0.5
    blk = a.reshape(CELL, k, CELL, k).transpose(0, 2, 1, 3).reshape(CELL, CELL, k * k)
    out = np.zeros((CELL, CELL), a.dtype)
    for y in range(CELL):
        for x in range(CELL):
            v, c = np.unique(blk[y, x], return_counts=True)
            if (v > 0).any():
                c = np.where(v > 0, c, 0)
                if c.max() * 4 >= k * k:      # needs >= 25 % coverage of a non-background id
                    out[y, x] = v[c.argmax()]
    return out


class Guide:
    """Loaded guide in CELL space: .mask (bool 128x128), .ids (int, 0 = none), .gnames {id: group},
    .mat (material index map, -1 = none), .joints {name: (x, y)}, .body (mask minus sword/kagi)."""

    def __init__(self, prefix):
        self.prefix = prefix
        mp = prefix + "_mask.png"
        idp = prefix + "_id.png"
        if not os.path.exists(mp) and not os.path.exists(idp):
            raise FileNotFoundError(f"guide {prefix}: no {mp} or {idp}")
        self.ids = None
        self.gnames = {}
        if os.path.exists(idp):
            a = np.array(Image.open(idp).convert("RGBA"))
            ids = np.rint(a[..., 0] / 10.0).astype(int)
            ids[a[..., 3] < 128] = 0
            self.ids = _to_cell(ids, "id")
            for gp in (prefix + "_groups.json", os.path.join(os.path.dirname(prefix), "id_groups.json"),
                       os.path.join(ROOT, "pixel", "base", "idle", "_id", "id_groups.json")):
                if os.path.exists(gp):
                    self.gnames = {v: g for g, v in json.load(open(gp))["groups"].items()}
                    break
        if os.path.exists(mp):
            a = np.array(Image.open(mp).convert("RGBA")).astype(float)
            m = a[..., 3] / 255.0 if (a[..., 3] < 255).any() else a[..., :3].mean(-1) / 255.0
            self.mask = _to_cell(m >= 0.5, "mask") if m.shape[0] != CELL else (m >= 0.5)
            self.mask = np.asarray(self.mask, bool)
        else:
            self.mask = self.ids > 0
        thin = np.zeros_like(self.mask)
        sp = prefix + "_sword.png"
        if os.path.exists(sp):
            a = np.array(Image.open(sp).convert("RGBA")).astype(float)
            m = a[..., 3] / 255.0 if (a[..., 3] < 255).any() else a[..., :3].mean(-1) / 255.0
            thin |= np.asarray(_to_cell(m >= 0.5, "mask") if m.shape[0] != CELL else m >= 0.5, bool)
        if self.ids is not None:
            for v, g in self.gnames.items():
                if g in ("sword", "kagi"):
                    thin |= self.ids == v
        self.sword = thin & self.mask
        self.body = self.mask & ~thin
        self.mat = np.full((CELL, CELL), -1, int)
        if self.ids is not None:
            for v, g in self.gnames.items():
                mt = GROUP_MAT.get(g)
                if mt:
                    self.mat[self.ids == v] = MAT_NAMES.index(mt)
        self.joints = self._derive_joints()
        jp = prefix + "_joints.json"
        if os.path.exists(jp):
            j = json.load(open(jp))
            jj = j.get("joints", j)
            sx = sy = 1.0
            if j.get("space") == "px" and "size" in j:
                sx, sy = CELL / j["size"][0], CELL / j["size"][1]
            for k, v in jj.items():
                if isinstance(v, (list, tuple)) and len(v) >= 2 and all(isinstance(t, (int, float)) for t in v[:2]):
                    self.joints[k] = (float(v[0]) * sx, float(v[1]) * sy)
            if "eyes" not in self.joints and "eye_L" in self.joints and "eye_R" in self.joints:
                self.joints["eyes"] = tuple((np.array(self.joints["eye_L"]) + self.joints["eye_R"]) / 2)

    def group_mask(self, *names):
        m = np.zeros((CELL, CELL), bool)
        if self.ids is None:
            return m
        for v, g in self.gnames.items():
            if g in names:
                m |= self.ids == v
        return m

    def _derive_joints(self):
        J = {}
        b = self.body if self.body.any() else self.mask
        if b.any():
            ys, xs = np.nonzero(b)
            by = ys.max()
            fx = np.nonzero(b[max(by - 1, 0):by + 1].any(0))[0]
            J["root"] = (float(fx.mean()), float(by))
            J["head_top"] = (float(xs[ys == ys.min()].mean()), float(ys.min()))
        for nm, groups in (("bow", ("bow",)), ("face", ("face",)), ("guard", ("kagi",)),
                           ("hair", ("hair", "bun", "sheen"))):
            m = self.group_mask(*groups)
            if m.any():
                ys, xs = np.nonzero(m)
                J[nm] = (float(xs.mean()), float(ys.mean()))
        for nm in ("leg_L", "leg_R"):
            m = self.group_mask(nm)
            if m.any():
                ys, xs = np.nonzero(m)
                J["foot_" + nm[-1]] = (float(xs[ys == ys.max()].mean()), float(ys.max()))
        return J


def load_guide(prefix):
    if prefix in (None, "", "none"):
        return None
    return Guide(prefix)


# ---------------------------------------------------------------- morphology (no scipy needed)
def shift(m, dy, dx, fill=0):
    """out[y, x] = m[y + dy, x + dx]"""
    H, W = m.shape[:2]
    out = np.full_like(m, fill)
    ys0, ys1 = max(0, -dy), min(H, H - dy)
    xs0, xs1 = max(0, -dx), min(W, W - dx)
    out[ys0:ys1, xs0:xs1] = m[ys0 + dy:ys1 + dy, xs0 + dx:xs1 + dx]
    return out


N4 = [(-1, 0), (1, 0), (0, -1), (0, 1)]
N8 = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]


def label_cc(mask, conn=8):
    """connected components -> (labels, sizes) ; sizes[0] = 0. Uses scipy if present."""
    try:
        from scipy import ndimage
        st = np.ones((3, 3)) if conn == 8 else None
        lab, n = ndimage.label(mask, structure=st)
        sizes = np.bincount(lab.ravel(), minlength=n + 1)
        sizes[0] = 0
        return lab, sizes
    except ImportError:
        pass
    H, W = mask.shape
    lab = np.zeros((H, W), int)
    sizes = [0]
    nb = N8 if conn == 8 else N4
    n = 0
    for y, x in zip(*np.nonzero(mask)):
        if lab[y, x]:
            continue
        n += 1
        st = [(y, x)]
        lab[y, x] = n
        c = 0
        while st:
            cy, cx = st.pop()
            c += 1
            for dy, dx in nb:
                yy, xx = cy + dy, cx + dx
                if 0 <= yy < H and 0 <= xx < W and mask[yy, xx] and not lab[yy, xx]:
                    lab[yy, xx] = n
                    st.append((yy, xx))
        sizes.append(c)
    return lab, np.array(sizes)


def disk_op(mask, r, op="dilate"):
    """binary dilate/erode with a disk of radius r (separable approx via repeated 3x3 + cross)."""
    from PIL import ImageFilter
    im = Image.fromarray((mask * 255).astype(np.uint8), "L")
    size = 2 * int(r) + 1
    f = ImageFilter.MaxFilter(size) if op == "dilate" else ImageFilter.MinFilter(size)
    return np.array(im.filter(f)) > 127
