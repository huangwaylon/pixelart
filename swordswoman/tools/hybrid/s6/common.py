"""S6 Claude-pixel helpers: guide tracing at sprite resolution, palette, stamps, io."""
import json, os, sys
import numpy as np
from PIL import Image

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "tools", "hybrid"))
import pixgrid  # noqa: E402

PAL = json.load(open(os.path.join(ROOT, "docs", "palette.json")))
# legend char -> hex
LEG = {
    "K": "#1a1220", "m": "#c48089", "s": "#f0b49c", "S": "#fde3d2",
    "h": "#42282a", "H": "#74483a", "J": "#b07a62",
    "v": "#4a1640", "r": "#92203f", "R": "#d8343e", "C": "#f5705a",
    "l": "#4a2e20", "L": "#a8744a", "d": "#504462",
    "t": "#5f6678", "T": "#a8b0c0", "w": "#eef0f5",
    "e": "#2c3f9e", "E": "#5f8ee8", "p": "#f49ab0", "P": "#f8b5c8", "u": "#9b45c9",
}
RGB = {k: tuple(int(v[i:i + 2], 16) for i in (1, 3, 5)) for k, v in LEG.items()}
INV = {v: k for k, v in RGB.items()}

IDN = {1: "hair", 2: "bun", 3: "bow", 4: "face", 5: "ear", 6: "collar", 7: "torso", 8: "corset",
       9: "skirt", 10: "skirt_under", 11: "shorts", 12: "sleeve_L", 13: "sleeve_R", 14: "arm_L",
       15: "arm_R", 16: "hand_L", 17: "hand_R", 18: "leg_L", 19: "leg_R", 20: "shoe_L", 21: "shoe_R",
       22: "scarf_L", 23: "scarf_R", 24: "sword", 25: "smear"}
NID = {v: k for k, v in IDN.items()}

G = os.path.join(ROOT, "hybrid", "guide")
GUIDES = {}
for d in ["S", "SE", "E", "NE", "N", "NW", "W", "SW"]:
    GUIDES[f"turn_{d}"] = f"{G}/turn/{d}/f00"
for i in range(4):
    GUIDES[f"walk_SE_k{i}"] = f"{G}/p2/walk_SE_keys/SE/f0{i}"
    GUIDES[f"slash_SE_k{i}"] = f"{G}/p2/slash_SE_keys/SE/f0{i}"
for i, k in enumerate(["crouch", "apex", "land"]):
    GUIDES[f"jump_E_{k}"] = f"{G}/p2/jump_E_keys/E/f0{i}"
NAMES = list(GUIDES)


def trace(prefix, cell=128, thr=0.5):
    """mode-downsample the 1024 id pass to the 128 cell. returns ids (int), clay lum (float), depth."""
    a = np.array(Image.open(prefix + "_id.png").convert("RGBA"))
    ids = np.rint(a[..., 0] / 10.0).astype(int)
    ids[a[..., 3] < 128] = 0
    k = a.shape[0] // cell
    b = ids.reshape(cell, k, cell, k).transpose(0, 2, 1, 3).reshape(cell, cell, k * k)
    out = np.zeros((cell, cell), int)
    cov = (b > 0).mean(-1)
    for y in range(cell):
        for x in range(cell):
            if cov[y, x] >= thr:
                c = np.bincount(b[y, x], minlength=26)
                c[0] = 0
                # thin parts (sword, scarf) win at lower coverage
                out[y, x] = c.argmax()
    # thin parts: keep sword / scarf pixels with >= 20 % coverage even if bg wins
    for tid in (24, 22, 23):
        frac = (b == tid).mean(-1)
        m = (frac >= 0.2) & (out == 0)
        out[m] = tid
    clay = None
    if os.path.exists(prefix + "_clay.png"):
        c = np.array(Image.open(prefix + "_clay.png").convert("RGBA")).astype(float)
        lum = c[..., :3].mean(-1)
        lum[c[..., 3] < 128] = np.nan
        lb = lum.reshape(cell, k, cell, k).transpose(0, 2, 1, 3).reshape(cell, cell, k * k)
        clay = np.nanmean(lb, -1)
    return out, clay


def load_rgba(p):
    return np.array(Image.open(p).convert("RGBA"))


def save_rgba(a, p):
    os.makedirs(os.path.dirname(p) or ".", exist_ok=True)
    Image.fromarray(a.astype(np.uint8), "RGBA").save(p)


def chars_to_rgba(g):
    h, w = len(g), max(len(r) for r in g)
    a = np.zeros((h, w, 4), np.uint8)
    for y, row in enumerate(g):
        for x, ch in enumerate(row):
            if ch in RGB:
                a[y, x, :3] = RGB[ch]
                a[y, x, 3] = 255
    return a


def rgba_to_chars(a):
    rows = []
    for y in range(a.shape[0]):
        r = ""
        for x in range(a.shape[1]):
            if a[y, x, 3] < 128:
                r += "."
            else:
                r += INV.get(tuple(int(v) for v in a[y, x, :3]), "?")
        rows.append(r)
    return rows


def load_pix(path):
    """minimal .pix reader for the lock stamps (legend chars only)."""
    rows, on = [], False
    for ln in open(path):
        ln = ln.rstrip("\n")
        if ln.startswith("grid:"):
            on = True
            continue
        if on:
            if not ln.strip() or ln.startswith("#"):
                if rows:
                    break
                continue
            rows.append(ln)
    return rows


def stamp(name):
    return chars_to_rgba(load_pix(os.path.join(ROOT, "hybrid", "lock", "pixel", "src", name + ".pix")))


def paste(cv, st, x0, y0, behind=False):
    h, w = st.shape[:2]
    for y in range(h):
        for x in range(w):
            if st[y, x, 3] and 0 <= y0 + y < cv.shape[0] and 0 <= x0 + x < cv.shape[1]:
                if behind and cv[y0 + y, x0 + x, 3]:
                    continue
                cv[y0 + y, x0 + x] = st[y, x]


def zoom(a, z, bg=(36, 32, 44), grid=False):
    h, w = a.shape[:2]
    out = np.zeros((h * z, w * z, 3), np.uint8)
    out[:] = bg
    al = a[..., 3:4] / 255.0
    big = np.repeat(np.repeat(a, z, 0), z, 1).astype(float)
    out = (big[..., :3] * np.repeat(np.repeat(al, z, 0), z, 1) + out * (1 - np.repeat(np.repeat(al, z, 0), z, 1))).astype(np.uint8)
    if grid:
        out[::z, :] = (out[::z, :] * 0.8).astype(np.uint8)
        out[:, ::z] = (out[:, ::z] * 0.8).astype(np.uint8)
    return out
