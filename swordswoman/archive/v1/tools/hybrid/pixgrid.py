"""Hand-authored pixel art as text grids (.pix), palette-locked to docs/palette.json.

Ported from ~/Documents/other/pixelart/pipeline/pixgrid.py (read-only original).  Additions:
palette NAMES in legends, a built-in STANDARD legend (no legend block needed), palette-lock
validation, `extends:` from a PNG (paint over a pixelized sprite), `topng` with 128-cell output,
`fromimg` that writes standard chars, `diff`, and `legend` (prints the standard map).

File format (.pix, plain text):
    # comments
    size: 128 128                (optional, checked against the grid)
    extends: base.pix | base.png (optional: start from another grid / image, relative path)
    legend:                      (optional; the STANDARD legend below is always pre-loaded)
    . = transparent
    K = outline                  (palette name, alias like leather_0, or #hex IN the palette)
    grid:                        (full image; one char per pixel; rows must be equal length)
    ....KKKK....
    patch: 40 52                 (optional, repeatable: overlay at x y; '_' = keep pixel underneath)
    _KK_
    K__K

STANDARD legend (lower case = darker, upper = lighter):
    .  transparent     K outline
    m skin_0  s skin_1  S skin_2      h hair_0  H hair_1  J hair_2
    v red_0   r red_1   R red_2  C red_3     l leather_1  L leather_2   d dark_1
    t steel_0 T steel_1 w steel_2     e eye_0  E eye_1     p pink_0  P pink_1   u purple_0

    .venv/bin/python tools/hybrid/pixgrid.py render a.pix [b.pix ...] --out DIR [--zoom 4] [--bg #DFEAF6] [--grid]
    .venv/bin/python tools/hybrid/pixgrid.py topng a.pix --out a.png [--cell] [--at X Y]    (1x PNG; --cell pads into 128x128)
    .venv/bin/python tools/hybrid/pixgrid.py sheet a.pix b.png ... --out sheet.png [--zoom 3] [--cols 5]
    .venv/bin/python tools/hybrid/pixgrid.py stats a.pix|a.png ...       (colours, off-palette, orphans)
    .venv/bin/python tools/hybrid/pixgrid.py fromimg in.png --out x.pix [--crop x0,y0,x1,y1] [--snap]
    .venv/bin/python tools/hybrid/pixgrid.py diff a.pix b.pix|b.png       (changed pixels)
    .venv/bin/python tools/hybrid/pixgrid.py legend
"""
import argparse
import os
import string
import sys

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hylib as H  # noqa: E402

KEEP = "_"
STD = {".": "transparent", "K": "outline",
       "m": "skin_0", "s": "skin_1", "S": "skin_2",
       "h": "hair_0", "H": "hair_1", "J": "hair_2",
       "v": "red_0", "r": "red_1", "R": "red_2", "C": "red_3",
       "l": "leather_1", "L": "leather_2", "d": "dark_1",
       "t": "steel_0", "T": "steel_1", "w": "steel_2",
       "e": "eye_0", "E": "eye_1", "p": "pink_0", "P": "pink_1", "u": "purple_0"}


def _rgba_of(val, path, free=False):
    """legend value (palette name / alias / #hex / transparent) -> RGBA tuple"""
    v = val.strip()
    if v in ("transparent", ".", "clear"):
        return (0, 0, 0, 0)
    pal = H.palette()
    try:
        return pal.rgba(pal.resolve(v))
    except ValueError:
        if free and v.startswith("#"):
            h = v.lstrip("#")
            return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)) + (255,)
        raise ValueError(f"{path}: legend colour {v!r} is not in the locked palette (docs/palette.json)")


def std_legend():
    return {c: (n, n) for c, n in STD.items()}


def load(path, _depth=0, free=False):
    """-> (rgba uint8 HxWx4, legend {char: (value, role)}).  PNG paths load as images."""
    if path.lower().endswith(".png"):
        return np.array(Image.open(path).convert("RGBA")), std_legend()
    lines = open(path).read().splitlines()
    legend, img, mode, patch_at, rows, size = std_legend(), None, None, None, [], None
    base_dir = os.path.dirname(os.path.abspath(path))

    def flush():
        nonlocal img, rows
        if mode == "grid" and rows:
            img = _paint(np.zeros((len(rows), len(rows[0]), 4), np.uint8), rows, legend, 0, 0, path, free)
        elif mode == "patch" and rows:
            if img is None:
                raise ValueError(f"{path}: patch before grid/extends")
            img = _paint(img, rows, legend, patch_at[0], patch_at[1], path, free)
        rows = []

    for raw in lines:
        line = raw.rstrip("\n")
        s = line.strip()
        if mode in ("grid", "patch") and s and not s.startswith("#") and ":" not in s.split()[0] and "=" not in s:
            rows.append(s)
            continue
        if not s or s.startswith("#"):
            continue
        key = s.split(":", 1)[0].strip().lower()
        if key == "size":
            size = tuple(int(v) for v in s.split(":", 1)[1].split())
        elif key == "extends":
            flush()
            img, base_legend = load(os.path.join(base_dir, s.split(":", 1)[1].strip()), _depth + 1, free)
            img = img.copy()
            legend = {**base_legend, **legend}
            mode = None
        elif key == "legend":
            flush()
            mode = "legend"
        elif key == "grid":
            flush()
            mode = "grid"
        elif key == "patch":
            flush()
            mode = "patch"
            patch_at = tuple(int(v) for v in s.split(":", 1)[1].split())
        elif mode == "legend" and "=" in s:
            ch, rest = line.split("=", 1)
            ch = ch.strip()
            parts = rest.split()
            legend[ch] = (parts[0] if parts else "transparent", " ".join(parts[1:]))
        else:
            raise ValueError(f"{path}: cannot parse line: {line!r}")
    flush()
    if img is None:
        raise ValueError(f"{path}: no grid")
    if size and (img.shape[1], img.shape[0]) != size:
        raise ValueError(f"{path}: size {size} but grid is {img.shape[1]}x{img.shape[0]}")
    return img, legend


def _paint(img, rows, legend, x0, y0, path, free=False):
    w = len(rows[0])
    cache = {}
    for j, r in enumerate(rows):
        if len(r) != w:
            raise ValueError(f"{path}: row {j} has {len(r)} chars, expected {w}")
        for i, ch in enumerate(r):
            if ch == KEEP:
                continue
            if ch not in legend:
                raise ValueError(f"{path}: row {j} col {i}: char {ch!r} not in legend")
            if ch not in cache:
                cache[ch] = _rgba_of(legend[ch][0], path, free)
            y, x = y0 + j, x0 + i
            if 0 <= y < img.shape[0] and 0 <= x < img.shape[1]:
                img[y, x] = cache[ch]
    return img


def stats(img):
    a = img[..., 3] > 0
    flat = img[..., :3].astype(np.int32)
    key = (flat[..., 0] << 16) | (flat[..., 1] << 8) | flat[..., 2]
    key = np.where(a, key, -1)
    Hh, W = key.shape
    pad = np.pad(key, 1, constant_values=-2)
    same = np.zeros((Hh, W), bool)
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            if dy or dx:
                same |= pad[1 + dy:1 + dy + Hh, 1 + dx:1 + dx + W] == key
    idx = H.index_of(img)
    pal = H.palette()
    orph = a & ~same
    orphans = [(int(x), int(y), pal.names[idx[y, x]] if idx[y, x] >= 0 else "off") for y, x in zip(*np.nonzero(orph))]
    semi = int(((img[..., 3] > 0) & (img[..., 3] < 255)).sum())
    bad_orph = [o for o in orphans if o[2] not in H.ORPHAN_OK]
    return {"size": [W, Hh], "opaque": int(a.sum()), "colours": int(len(np.unique(key[a]))),
            "off_palette": int((idx == -2).sum()), "semi_alpha": semi, "orphans": len(orphans),
            "orphans_not_whitelisted": len(bad_orph), "orphan_xy": orphans[:20]}


def to_image(img, zoom=1, bg=None, grid=False):
    im = Image.fromarray(img, "RGBA")
    if bg:
        b = Image.new("RGBA", im.size, _hex(bg))
        b.alpha_composite(im)
        im = b
    if zoom > 1:
        im = im.resize((im.width * zoom, im.height * zoom), Image.NEAREST)
        if grid and zoom >= 6:
            d = ImageDraw.Draw(im)
            for x in range(0, im.width, zoom):
                d.line([(x, 0), (x, im.height)], fill=(0, 0, 0, 40))
            for y in range(0, im.height, zoom):
                d.line([(0, y), (im.width, y)], fill=(0, 0, 0, 40))
            for x in range(0, im.width, zoom * 8):
                d.line([(x, 0), (x, im.height)], fill=(0, 0, 160, 90))
            for y in range(0, im.height, zoom * 8):
                d.line([(0, y), (im.width, y)], fill=(0, 0, 160, 90))
    return im


def _hex(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)) + (255,)


def sheet(paths, zoom=3, cols=5, bg="#DFEAF6", labels=True):
    imgs = [load(p)[0] for p in paths]
    w = max(i.shape[1] for i in imgs) * zoom
    h = max(i.shape[0] for i in imgs) * zoom
    top = 14 if labels else 0
    pad = 6
    rows = (len(imgs) + cols - 1) // cols
    out = Image.new("RGBA", (cols * (w + pad) + pad, rows * (h + pad + top) + pad), _hex("#241628"))
    d = ImageDraw.Draw(out)
    for k, (p, img) in enumerate(zip(paths, imgs)):
        x, y = pad + (k % cols) * (w + pad), pad + (k // cols) * (h + pad + top)
        if labels:
            d.text((x + 2, y + 1), os.path.splitext(os.path.basename(p))[0], fill=(244, 234, 210, 255))
        cell = to_image(img, zoom, bg)
        out.alpha_composite(cell, (x + (w - cell.width) // 2, y + top + (h - cell.height) // 2))
    return out


def from_image(path, crop=None, snap=False):
    """PNG -> .pix text.  Palette pixels use the STANDARD chars (no legend block needed); any other
    colour gets an auto char + #hex legend entry (or is snapped to the nearest palette tone with
    --snap).  Semi-alpha: alpha < 128 -> transparent."""
    im = np.array(Image.open(path).convert("RGBA"))
    if crop:
        x0, y0, x1, y1 = crop
        im = im[y0:y1, x0:x1]
    pal = H.palette()
    rev = {}
    for c, n in STD.items():
        if n != "transparent":
            rev[tuple(pal.rgb[pal.index[n]])] = c
    spare = iter(c for c in string.ascii_letters + string.digits + "!$%&*+-/<>?@^~|;"
                 if c not in STD and c not in ("_", "."))
    extra, rows = {}, []
    P = np.array(pal.rgb, float)
    for y in range(im.shape[0]):
        r = ""
        for x in range(im.shape[1]):
            p = im[y, x]
            if p[3] < 128:
                r += "."
                continue
            t = tuple(int(v) for v in p[:3])
            if t in rev:
                r += rev[t]
                continue
            if snap:
                k = int(((P - np.array(t)) ** 2).sum(1).argmin())
                r += rev[tuple(pal.rgb[k])]
                continue
            hx = "#%02X%02X%02X" % t
            if hx not in extra:
                extra[hx] = next(spare)
            r += extra[hx]
        rows.append(r)
    txt = [f"# from {os.path.basename(path)}" + (f" crop {crop}" if crop else ""),
           f"size: {im.shape[1]} {im.shape[0]}"]
    if extra:
        txt += ["legend:", "# OFF-PALETTE colours (fix before use; render/stats will reject them)"]
        txt += [f"{c} = {hx}" for hx, c in extra.items()]
    txt += ["grid:"] + rows
    return "\n".join(txt) + "\n"


def to_cell(img, at=None):
    """pad / place an image into the 128 cell.  at=(x, y) top-left; default: centred, bottom on 104."""
    Hc = H.CELL
    if img.shape[:2] == (Hc, Hc) and at is None:
        return img
    out = np.zeros((Hc, Hc, 4), np.uint8)
    if at is None:
        at = ((Hc - img.shape[1]) // 2, H.PIVOT[1] + 1 - img.shape[0])
    x0, y0 = at
    for y in range(img.shape[0]):
        for x in range(img.shape[1]):
            if 0 <= y + y0 < Hc and 0 <= x + x0 < Hc:
                out[y + y0, x + x0] = img[y, x]
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--free", action="store_true", help="allow off-palette #hex (exploration only)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("render")
    r.add_argument("files", nargs="+")
    r.add_argument("--out", required=True)
    r.add_argument("--zoom", type=int, default=4)
    r.add_argument("--bg", default="#DFEAF6")
    r.add_argument("--grid", action="store_true")
    tp = sub.add_parser("topng")
    tp.add_argument("file")
    tp.add_argument("--out", required=True)
    tp.add_argument("--cell", action="store_true", help="place into a 128x128 cell")
    tp.add_argument("--at", nargs=2, type=int, help="top-left in the cell (with --cell)")
    s = sub.add_parser("sheet")
    s.add_argument("files", nargs="+")
    s.add_argument("--out", required=True)
    s.add_argument("--zoom", type=int, default=3)
    s.add_argument("--cols", type=int, default=5)
    s.add_argument("--bg", default="#DFEAF6")
    t = sub.add_parser("stats")
    t.add_argument("files", nargs="+")
    f = sub.add_parser("fromimg")
    f.add_argument("file")
    f.add_argument("--out", required=True)
    f.add_argument("--crop")
    f.add_argument("--snap", action="store_true")
    d = sub.add_parser("diff")
    d.add_argument("a")
    d.add_argument("b")
    sub.add_parser("legend")
    a = ap.parse_args()
    if a.cmd == "render":
        os.makedirs(a.out, exist_ok=True)
        for p in a.files:
            img, _ = load(p, free=a.free)
            n = os.path.splitext(os.path.basename(p))[0]
            to_image(img).save(os.path.join(a.out, f"{n}.png"))
            to_image(img, a.zoom, a.bg, a.grid).save(os.path.join(a.out, f"{n}_x{a.zoom}.png"))
            print(n, stats(img))
    elif a.cmd == "topng":
        img, _ = load(a.file, free=a.free)
        if a.cell:
            img = to_cell(img, tuple(a.at) if a.at else None)
        os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
        Image.fromarray(img, "RGBA").save(a.out)
        print("wrote", a.out, stats(img))
    elif a.cmd == "sheet":
        sheet(a.files, a.zoom, a.cols, a.bg).save(a.out)
        print("wrote", a.out)
    elif a.cmd == "stats":
        for p in a.files:
            print(p, stats(load(p, free=a.free)[0]))
    elif a.cmd == "fromimg":
        crop = tuple(int(v) for v in a.crop.split(",")) if a.crop else None
        open(a.out, "w").write(from_image(a.file, crop, a.snap))
        print("wrote", a.out)
    elif a.cmd == "diff":
        A, B = load(a.a, free=a.free)[0], load(a.b, free=a.free)[0]
        if A.shape != B.shape:
            sys.exit(f"size differs {A.shape} vs {B.shape}")
        dm = np.any(A != B, -1)
        print(f"{int(dm.sum())} px differ")
        pal = H.palette()
        nm = lambda p: "clear" if p[3] == 0 else (pal.name_of(tuple(int(v) for v in p)) or "#%02x%02x%02x" % tuple(p[:3]))
        for y, x in list(zip(*np.nonzero(dm)))[:60]:
            print(f"  ({x},{y}) {nm(A[y, x])} -> {nm(B[y, x])}")
    elif a.cmd == "legend":
        for c, n in STD.items():
            print(f"{c} = {n}")


if __name__ == "__main__":
    main()
