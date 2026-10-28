"""Shared helpers for tools/hybrid (pixelize / metrics / sheets / gifs).

Conventions (see tools/hybrid/README.md):
  * cell 128x128, feet pivot (64, 104)  (docs/anim_spec.json, tools/pixel/pxlib.py)
  * STANDARD TEST SET names: turn_<DIR>.png, walk_SE_k0..3.png, slash_SE_k0..3.png,
    jump_E_{crouch,apex,land}.png
  * a GUIDE is a file prefix P with (all optional except the mask):
        P_mask.png    silhouette (alpha, or luminance if no alpha). Any size; non-128 square sizes
                      are treated as k x the cell (512 = 4x, 1024 = 8x) and box-reduced.
                      Fallback: P_body.png (+ P_sword.png) alpha union, i.e. the round-9 layout
                      renders/model_round_9/_masks/anim_<anim>_<DIR>_f<N>_64_{body,id,sword}.png
        P_body.png    colour body pass (optional): used by metrics for guide feature positions
        P.png         colour sprite (optional, e.g. renders/model_round_9/anim_walk_SE_f0_64.png)
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
            [f"slash_SE_k{i}" for i in range(4)] + [f"jump_E_{k}" for k in ("crouch", "apex", "land")]
KEY_ORDER = {"crouch": 0, "anticipation": 0, "takeoff": 1, "rise": 1, "apex": 2, "fall": 3, "land": 4, "recover": 5}
SPRITE_RE = re.compile(r"^(?P<anim>[a-z][a-z0-9]*(?:_[a-z][a-z0-9]*)*?)_(?P<dir>S|SE|E|NE|N|NW|W|SW)"
                       r"(?:_(?P<key>k\d+|f\d+|[a-z]+\d*))?\.png$")
AUX_SUFFIX = ("_4x", "_hires", "_mat", "_src", "_dbg", "_guide", "_cmp", "_fxmask")

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
        bp = prefix + "_body.png"
        self.color = None
        for cp in (prefix + ".png", bp):
            if os.path.exists(cp):
                c = np.array(Image.open(cp).convert("RGBA"))
                if c.shape[:2] == (CELL, CELL):
                    self.color = c
                    if cp == prefix + ".png":
                        break
        if not os.path.exists(mp) and os.path.exists(bp):
            mp = bp                                   # round-9 _masks layout: body (+ sword below)
        if not os.path.exists(mp) and not os.path.exists(idp) and os.path.exists(prefix + ".png"):
            mp = prefix + ".png"                      # colour sprite only: its alpha is the mask
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
        if not thin.any() and self.color is not None:
            # no sword pass: steel-coloured components >= 4 px of the colour sprite (+ outline ring)
            st = base_mask(index_of(self.color), "steel")
            if st.any():
                lab_, sz_ = label_cc(st, 8)
                st = np.isin(lab_, np.nonzero(sz_ >= 4)[0]) & st
                thin |= disk_op(st, 1) & self.mask
        if mp == bp or self.ids is not None:
            self.mask = self.mask | thin | (self.ids > 0 if self.ids is not None else False)
        if self.ids is not None:
            # the outline ring is added after the ID pass: give ring pixels an adjacent body id
            for _ in range(2):
                z = (self.ids == 0) & self.mask
                if not z.any():
                    break
                for dy, dx in N4:
                    sh = shift(self.ids, dy, dx)
                    self.ids = np.where(z & (sh > 0), sh, self.ids)
                    z = (self.ids == 0) & self.mask
        if self.color is not None:
            self.mask = self.mask | (self.color[..., 3] > 0)   # include the outline ring of the sprite
        self.sword = thin & self.mask
        self.body = self.mask & ~thin
        self.mat = np.full((CELL, CELL), -1, int)
        if self.ids is not None:
            for v, g in self.gnames.items():
                mt = GROUP_MAT.get(g)
                if mt:
                    self.mat[self.ids == v] = MAT_NAMES.index(mt)
        if self.ids is None and self.color is not None:
            # no id pass: material prior from the palette tones of the guide's colour sprite
            ci = index_of(self.color)
            pal = palette()
            for i, n in enumerate(pal.names):
                b = name_base(n)
                if b in MAT_NAMES:
                    self.mat[ci == i] = MAT_NAMES.index(b)
            self.mat[~self.mask] = -1
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


# ================================================================ v2 additions (pipeline engineer)
# Base colour classes used for classification / quantization.  Composite guide materials
# (face, sword) expand to sets of base classes.
BASE = ["hair", "red", "skin", "leather", "dark", "steel", "eye", "pink", "purple"]
MAT_BASES = {"face": ["skin", "eye", "pink"], "sword": ["steel", "dark", "red"]}
for _m in MATERIALS:
    MAT_BASES.setdefault(_m, [_m])
# orphans that are legal by colour (cleanup guide R13): glint, mouth, blush, buckle, lace, eyes
ORPHAN_OK = {"steel_2", "skin_0", "pink_0", "steel_1", "purple_0", "eye_0", "eye_1"}
SMEAR_TONES = ["steel_2", "pink_1", "pink_0"]          # palette.json roles.smear_arc


def base_tones(b, with_outline=True):
    """canonical palette names of a base class ramp, dark -> light (outline first if asked)."""
    pal = palette()
    out = ["outline"] if with_outline else []
    for i in range(len(pal.raw["ramps"][b])):
        n = pal.alias.get(f"{b}_{i}", f"{b}_{i}")
        if n not in out:
            out.append(n)
    return out


def name_base(n):
    """palette name -> base class ('outline' -> 'outline')."""
    if n == "outline":
        return "outline"
    return n.rsplit("_", 1)[0]


def lab_of_names(names):
    return pal_lab(names)


def poly_dist(lab, names):
    """Lab distance of every pixel to the polyline through the given tones (sorted by L)."""
    P = pal_lab(names)
    P = P[np.argsort(P[:, 0])]
    flat = lab.reshape(-1, 3)
    if len(P) == 1:
        return np.linalg.norm(flat - P[0], axis=1).reshape(lab.shape[:-1])
    best = np.full(len(flat), np.inf)
    for a, b in zip(P[:-1], P[1:]):
        ab = b - a
        t = np.clip(((flat - a) @ ab) / max(ab @ ab, 1e-9), 0, 1)
        best = np.minimum(best, np.linalg.norm(flat - (a + t[:, None] * ab), axis=1))
    return best.reshape(lab.shape[:-1])


def classify(rgb, allowed=None, penalty=14.0, outline_node=False, smooth_margin=5.0, cw=0.8):
    """Per-pixel base-class classification by distance to each ramp polyline (dark -> light; the
    outline node is left out by default because outline->light segments cut through unrelated
    hues).  Chroma is weighted by cw (illustrations are often less saturated than the palette).
    rgb: (H, W, 3).  allowed: optional (H, W) int array of guide material indices into MAT_NAMES
    (-1 = no guide); classes outside the guide material's bases pay `penalty` (Lab units).
    Ambiguous pixels (best two classes within smooth_margin) take the 3x3-averaged costs.
    -> (cls (H, W) int index into BASE, cost (H, W, len(BASE)))."""
    lab = srgb_to_lab(rgb) * np.array([1.0, cw, cw])
    def tones(b):
        if b == "purple":
            return ["purple_0"]
        if b == "pink":                       # scarf lit edge is skin_2 (palette roles.scarf)
            return ["pink_0", "pink_1", "skin_2"]
        return base_tones(b, outline_node or b in ("leather", "dark"))
    C = np.stack([poly_dist_w(lab, tones(b), cw) for b in BASE], -1)
    if allowed is not None:
        for mi, mn in enumerate(MAT_NAMES):
            sel = allowed == mi
            if not sel.any():
                continue
            ok = np.array([b in MAT_BASES[mn] for b in BASE])
            C[sel] += np.where(ok, 0.0, penalty)[None, :]
    if smooth_margin and C.shape[0] > 2 and C.shape[1] > 2:
        srt = np.sort(C, -1)
        amb = (srt[..., 1] - srt[..., 0]) < smooth_margin
        if amb.any():
            from scipy import ndimage
            Cs = np.stack([ndimage.uniform_filter(C[..., i], 3, mode="nearest") for i in range(C.shape[-1])], -1)
            C = np.where(amb[..., None], 0.5 * C + 0.5 * Cs, C)
    return C.argmin(-1), C


def poly_dist_w(lab_w, names, cw):
    """poly_dist on pre-weighted Lab (L, cw*a, cw*b)."""
    P = pal_lab(names) * np.array([1.0, cw, cw])
    P = P[np.argsort(P[:, 0])]
    flat = lab_w.reshape(-1, 3)
    if len(P) == 1:
        return np.linalg.norm(flat - P[0], axis=1).reshape(lab_w.shape[:-1])
    best = np.full(len(flat), np.inf)
    for a, b in zip(P[:-1], P[1:]):
        ab = b - a
        t = np.clip(((flat - a) @ ab) / max(ab @ ab, 1e-9), 0, 1)
        best = np.minimum(best, np.linalg.norm(flat - (a + t[:, None] * ab), axis=1))
    return best.reshape(lab_w.shape[:-1])


def quantize_tones(rgb, cls, lw=1.0, cw=0.6, outline_bias=6.0):
    """nearest tone (incl. outline) inside each pixel's base class.  Distance weights L by lw and
    chroma (a, b) by cw, so shading value wins over hue noise.  -> (H, W) palette index image."""
    pal = palette()
    lab = srgb_to_lab(rgb)
    out = np.full(cls.shape, -1, int)
    for bi, b in enumerate(BASE):
        sel = cls == bi
        if not sel.any():
            continue
        names = base_tones(b) if b != "purple" else ["outline", "purple_0"]
        if b == "eye":
            names = names + ["steel_2"]
        if b == "pink":
            names = names + ["skin_2"]
        P = pal_lab(names)
        d = ((lab[sel][:, None, 0] - P[None, :, 0]) * lw) ** 2 + \
            (((lab[sel][:, None, 1:] - P[None, :, 1:]) * cw) ** 2).sum(-1)
        if b not in ("leather", "dark"):
            d[:, names.index("outline")] += outline_bias ** 2   # ramp's own dark tone wins ties
        out[sel] = np.array([pal.index[n] for n in names])[d.argmin(1)]
    return out


def index_of(a):
    """RGBA -> palette index image (-1 transparent, -2 off-palette)."""
    pal = palette()
    H, W = a.shape[:2]
    key = (a[..., 0].astype(np.int64) << 16) | (a[..., 1].astype(np.int64) << 8) | a[..., 2]
    lut = {(r << 16) | (g << 8) | b: i for i, (r, g, b) in enumerate(pal.rgb)}
    idx = np.full((H, W), -2, int)
    for k, i in lut.items():
        idx[key == k] = i
    idx[a[..., 3] == 0] = -1
    return idx


def rgba_of(idx):
    pal = palette()
    out = np.zeros(idx.shape + (4,), np.uint8)
    for i, c in enumerate(pal.rgb):
        out[idx == i] = tuple(c) + (255,)
    return out


def names_to_idx(names):
    pal = palette()
    return [pal.index[pal.resolve(n)] for n in names]


def base_mask(idx, *bases):
    """mask of pixels whose palette tone belongs to one of the base classes."""
    pal = palette()
    ids = [i for i, n in enumerate(pal.names) if name_base(n) in bases or
           any(pal.alias.get(f"{b}_0") == n and b in bases for b in pal.raw["ramps"])]
    return np.isin(idx, ids)


# ---------------------------------------------------------------- feature detection (sprites)
def _centroid(m):
    if not m.any():
        return None
    ys, xs = np.nonzero(m)
    return (float(xs.mean()), float(ys.mean()))


def features(a, guide=None):
    """Feature points of a palette sprite (128 cell RGBA) from its colours (no guide needed).
    -> dict name -> (x, y) | value.  bbox, height, baseline, feet_cx, eyes (centroid of eye-ramp
    pixels), eye_row, bow (red pixels in the head zone, above the eyes / top 30 %), hair, head
    (hair + bow + face skin above the collar), body (corset leather, else red mid-band), steel,
    sword_tip (steel pixel farthest from the body), guard (steel px nearest the body)."""
    idx = index_of(a) if a.ndim == 3 else a
    op = idx != -1
    F = {}
    if not op.any():
        return F
    ys, xs = np.nonzero(op)
    y0, y1, x0, x1 = int(ys.min()), int(ys.max()), int(xs.min()), int(xs.max())
    steel = base_mask(idx, "steel")
    eye = base_mask(idx, "eye")
    hair = base_mask(idx, "hair")
    red = base_mask(idx, "red")
    leather = base_mask(idx, "leather") & ~(idx == palette().index["outline"])
    big_steel = steel.copy()
    if steel.any():                      # sword = steel components of >= 4 px (+ their outline ring)
        lab_, sz_ = label_cc(steel, 8)
        big_steel = np.isin(lab_, np.nonzero(sz_ >= 4)[0]) & steel
    body_op = op & ~disk_op(big_steel, 1)
    if guide is not None and guide.sword.any():
        body_op &= ~disk_op(guide.sword, 1)
    bys = np.nonzero(body_op.any(1))[0]
    by0, by1 = (int(bys.min()), int(bys.max())) if len(bys) else (y0, y1)
    H = by1 - by0 + 1
    fx = np.nonzero(body_op[max(by1 - 1, 0):by1 + 1].any(0))[0]
    bxs = np.nonzero(body_op.any(0))[0]
    F.update(bbox=[x0, y0, x1, y1], width=x1 - x0 + 1, height=y1 - y0 + 1, body_top=by0, baseline=by1,
             body_height=H, body_width=int(bxs.max() - bxs.min() + 1) if len(bxs) else 0,
             feet_cx=float(fx.mean()) if len(fx) else None)
    head_zone = np.zeros_like(op)
    head_zone[by0:by0 + int(round(0.45 * H))] = True
    e = eye & head_zone
    if e.sum() >= 1:
        F["eyes"] = _centroid(e)
        F["eye_row"] = float(np.nonzero(e)[0].mean())
    bz = np.zeros_like(op)
    lim = int(F["eye_row"]) - 1 if "eye_row" in F else by0 + int(round(0.3 * H))
    bz[by0:max(lim, by0 + 1)] = True
    b = red & bz
    if b.sum() >= 3:
        F["bow"] = _centroid(b)
    h = hair & head_zone
    if h.any():
        F["hair"] = _centroid(h)
    hd = (hair | (red & bz) | eye) & head_zone
    if hd.any():
        F["head"] = _centroid(hd)
    l = leather & ~head_zone
    if l.sum() >= 4:
        F["body"] = _centroid(l)
    else:
        mid = np.zeros_like(op)
        mid[by0 + int(0.45 * H):by0 + int(0.75 * H)] = True
        if (red & mid).any():
            F["body"] = _centroid(red & mid)
    if steel.sum() >= 3:
        lab, sz = label_cc(steel, 8)
        k = int(np.argmax(sz))
        sm = lab == k
        F["steel"] = _centroid(sm)
        ref = F.get("body") or ((x0 + x1) / 2, (by0 + by1) / 2)
        sy, sx = np.nonzero(sm)
        d = (sx - ref[0]) ** 2 + (sy - ref[1]) ** 2
        F["sword_tip"] = (float(sx[d.argmax()]), float(sy[d.argmax()]))
        F["guard"] = (float(sx[d.argmin()]), float(sy[d.argmin()]))
        F["sword_px"] = int(sm.sum())
    return F


# ---------------------------------------------------------------- naming / sequences
def parse_name(fn):
    """'slash_SE_k2.png' -> ('slash', 'SE', 'k2', order)  ; None if not a sprite name."""
    m = SPRITE_RE.match(os.path.basename(fn))
    if not m:
        return None
    key = m.group("key") or ""
    if key[:1] in "kf" and key[1:].isdigit():
        order = int(key[1:])
    else:
        order = KEY_ORDER.get(key, 50)
    return m.group("anim"), m.group("dir"), key, order


def group_sequences(paths):
    """-> {(anim, dir): [paths ordered by key]}"""
    seq = {}
    for p in paths:
        r = parse_name(p) if is_sprite_name(os.path.basename(p)) else None
        if r:
            seq.setdefault((r[0], r[1]), []).append((r[3], r[2], p))
    return {k: [p for _, _, p in sorted(v)] for k, v in seq.items()}


def collect(inputs):
    """files and/or directories -> sorted sprite paths (aux files like *_4x.png skipped)."""
    out = []
    for p in inputs:
        if os.path.isdir(p):
            out += [os.path.join(p, f) for f in list_sprites(p)]
        elif os.path.exists(p):
            out.append(p)
    return out


def find_guide(sprite_path, guide_dir=None, guide_map=None):
    """guide prefix for a sprite: explicit map {stem: prefix}, else <guide_dir>/<stem>, else
    <sprite_dir>/guide/<stem>; prefix valid if any of _mask/_id/_body exists."""
    st = os.path.splitext(os.path.basename(sprite_path))[0]
    cands = []
    if guide_map and st in guide_map:
        cands.append(guide_map[st])
    if guide_dir:
        cands.append(os.path.join(guide_dir, st))
    cands.append(os.path.join(os.path.dirname(sprite_path), "guide", st))
    for c in cands:
        if any(os.path.exists(c + s) for s in ("_mask.png", "_id.png", "_body.png", ".png")):
            return c
    return None


def hires_of(sprite_path):
    """hi-res source next to a sprite: <stem>_hires.png or <stem>_src.png"""
    st = os.path.splitext(sprite_path)[0]
    for s in ("_hires.png", "_src.png"):
        if os.path.exists(st + s):
            return st + s
    return None


def timing_for(anim, d, n, keys=None):
    """per-frame ms for a sequence.  Priority: hybrid/ANIM_DIRECTION.md (json block with
    {"timing": {"<anim>_<dir>" | "<anim>": [ms...]}}, or lines 'timing <anim>[_<dir>]: a,b,c'),
    then docs/anim_spec.json when the frame count matches, then TEST_TIMING for the standard
    test set, then the spec mean.  -> (ms list, source string)"""
    md = os.path.join(ROOT, "hybrid", "ANIM_DIRECTION.md")
    if os.path.exists(md):
        txt = open(md).read()
        tab = {}
        for blk in re.findall(r"```json\s*(\{.*?\})\s*```", txt, re.S):
            try:
                j = json.loads(blk)
            except ValueError:
                continue
            tab.update(j.get("timing", {}))
        for m in re.finditer(r"^\s*[-*]?\s*`?timing\s+([A-Za-z0-9_]+)`?\s*[:=]\s*`?([0-9 ,]+)`?", txt, re.M):
            tab[m.group(1)] = [int(v) for v in m.group(2).replace(",", " ").split()]
        for k in (f"{anim}_{d}", anim):
            v = tab.get(k)
            if isinstance(v, dict) and keys:
                v = [v.get(kk, v.get("default", 120)) for kk in keys]
            if isinstance(v, list) and len(v) == n:
                return [int(x) for x in v], f"ANIM_DIRECTION.md:{k}"
    spec = json.load(open(os.path.join(ROOT, "docs", "anim_spec.json")))["anims"]
    alias = {"slash": "attack1", "attack": "attack1"}
    a = spec.get(anim) or spec.get(alias.get(anim, ""))
    if a and len(a["ms"]) == n:
        return list(a["ms"]), "anim_spec.json"
    if anim in TEST_TIMING and len(TEST_TIMING[anim]) == n:
        return list(TEST_TIMING[anim]), "TEST_TIMING (key poses)"
    if a:
        m = int(round(sum(a["ms"]) / len(a["ms"]) * (len(a["ms"]) / max(n, 1)) ** 0.5))
        return [m] * n, f"anim_spec.json mean (spec {len(a['ms'])} frames, have {n})"
    return [120] * n, "default 120"


# key-pose test set: holds on the poses that sell weight (contact/down), hit-stop on impact
TEST_TIMING = {"walk": [140, 110, 140, 110], "slash": [220, 50, 160, 240], "jump": [160, 220, 200],
               "turn": [250] * 8, "run": [90, 70, 90, 70]}


def resolve_steel(cls, C, rgb, op, guide_sword=None, min_px=6, min_elong=2.5):
    """Steel is legal on the sword (and buckles).  Illustrations have desaturated greys in eyes,
    ribbons and highlights that sit closest to the steel ramp; keep steel only on elongated
    components (blade), components touching the guide sword mask, or tiny ones inside leather
    (buckles).  Everything else takes its next-best class; blue-ish pixels (b* < -5) prefer eye."""
    sb = BASE.index("steel")
    st = (cls == sb) & op
    if not st.any():
        return cls
    cls = cls.copy()
    lab = srgb_to_lab(rgb)
    lab_s, sz = label_cc(st, 8)
    leather = (cls == BASE.index("leather")) & op
    near_leather = disk_op(leather, 1)
    for k in range(1, len(sz)):
        m = lab_s == k
        ys, xs = np.nonzero(m)
        keep = False
        if guide_sword is not None and (m & disk_op(guide_sword, 1)).any():
            keep = True
        elif sz[k] >= min_px:
            cov = np.cov(np.stack([xs, ys]).astype(float)) if len(xs) > 2 else np.eye(2)
            ev = np.sort(np.linalg.eigvalsh(cov + 1e-6 * np.eye(2)))
            keep = np.sqrt(ev[1] / max(ev[0], 1e-6)) >= min_elong and np.median(lab[m][:, 1]) < 5
        elif sz[k] <= 2 and near_leather[m].all():
            keep = True
        if keep:
            continue
        cc = C[m].copy()
        cc[:, sb] = np.inf
        blue = lab[m][:, 2] < -5
        cc[blue, BASE.index("eye")] -= 25
        warm = lab[m][:, 1] > 4
        cc[warm, BASE.index("pink")] -= 8
        cls[m] = cc.argmin(1)
    return cls
