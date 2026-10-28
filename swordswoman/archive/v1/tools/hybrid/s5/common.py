"""S5 pixel-native: shared helpers (guide lookup, palette, head placement)."""
import json, os, sys
import numpy as np
from PIL import Image
ROOT = "/Users/waylonhuang/Documents/other/pixelart/swordswoman"
sys.path.insert(0, os.path.join(ROOT, "tools", "hybrid"))
G = os.path.join(ROOT, "hybrid/guide/p2")
OUT = os.path.join(ROOT, "hybrid/S5_pixelnative/r1")
DIRS = ["S", "SE", "E", "NE", "N", "NW", "W", "SW"]
NAMES = [f"turn_{d}" for d in DIRS] + [f"walk_SE_k{i}" for i in range(4)] + \
        [f"slash_SE_k{i}" for i in range(4)] + [f"jump_E_{k}" for k in ("crouch", "apex", "land")]
PAL = json.load(open(os.path.join(ROOT, "docs/palette.json")))
TONES = {}
for r, l in PAL["ramps"].items():
    for i, h in enumerate(l):
        TONES[f"{r}_{i}"] = h
TONES["outline"] = PAL["outline"]
def rgb(h): return tuple(int(h[i:i+2], 16) for i in (1, 3, 5))
TRGB = {k: rgb(v) for k, v in TONES.items()}
UNIQ = sorted(set(TRGB.values()))

def guide_prefix(name):
    if name.startswith("turn_"):
        return f"{G}/turn/{name[5:]}/f00"
    if name.startswith("walk_SE_k"):
        return f"{G}/walk_SE_keys/SE/f0{name[-1]}"
    if name.startswith("slash_SE_k"):
        return f"{G}/slash_SE_keys/SE/f0{name[-1]}"
    k = {"crouch": 0, "apex": 1, "land": 2}[name.split("_")[-1]]
    return f"{G}/jump_E_keys/E/f0{k}"

def dir_of(name):
    return name.split("_")[1] if not name.startswith("turn_") else name[5:]

# head stamp placement relative to the guide head joint (measured from lock/pixel/fit_<DIR>)
FIT = {"S": (51, 39), "SE": (54, 40), "E": (50, 39), "NE": (48, 40), "N": (51, 39), "NW": (54, 40), "W": (50, 39), "SW": (50, 39)}
def joints(prefix):
    return {k: v["cell"] for k, v in json.load(open(prefix + "_joints.json"))["joints"].items()}
def head_xy(name):
    d = dir_of(name)
    j0 = joints(guide_prefix(f"turn_{d}"))["head"]
    j = joints(guide_prefix(name))["head"]
    fx, fy = FIT[d]
    dy = HEAD_DY.get(name, 0)
    return int(round(fx + j[0] - j0[0])), int(round(fy + j[1] - j0[1])) + dy
# close the chin-collar gap on lunging/landing keys (measured: body top - head bottom)
HEAD_DY = {"slash_SE_k1": 3, "slash_SE_k2": 4, "slash_SE_k3": 3, "jump_E_crouch": 2, "jump_E_land": 2, "jump_E_apex": 2}

def load(p): return np.array(Image.open(p).convert("RGBA"))
def save(a, p): Image.fromarray(a.astype(np.uint8), "RGBA").save(p)
def paste(dst, src, x, y):
    h, w = src.shape[:2]
    m = src[..., 3] > 0
    reg = dst[y:y+h, x:x+w]
    reg[m] = src[m]

# ---- squash/stretch layout for anim keys (Claude timing/spacing decision, ANIM_DIRECTION 2.2):
# body rows below the chin and sole row; the head stamp is rigid and rides on top.
TURN_BODY = 31
BODY = {"walk_SE_k0": (30, 105), "walk_SE_k1": (28, 105), "walk_SE_k2": (31, 105), "walk_SE_k3": (32, 104),
        "slash_SE_k0": (27, 105), "slash_SE_k1": (29, 105), "slash_SE_k2": (26, 105), "slash_SE_k3": (28, 105),
        "jump_E_crouch": (23, 105), "jump_E_apex": (35, 102), "jump_E_land": (22, 105)}
_head_xy_guide = head_xy
def head_xy(name):
    x, y = _head_xy_guide(name)
    if name in BODY:
        body, sole = BODY[name]
        h = load(f"{ROOT}/hybrid/lock/pixel/head_{dir_of(name)}.png").shape[0]
        y = sole - body - h + 1
    return x, y
_hx2 = head_xy
def head_xy(name):
    x, y = _hx2(name)
    if name == "jump_E_apex": x = 50
    return x, y
