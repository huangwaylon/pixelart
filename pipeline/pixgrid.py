"""Hand-authored pixel art: every pixel is typed by an artist in a text grid (no 3D, no vectors).

File format (.pix, plain text):
    # comments
    size: 96 128                 (optional, checked against the grid)
    extends: bust_base.pix       (optional: start from another .pix, relative path)
    legend:
    . = transparent
    K = #241628   outline        (char = hex, optional role name)
    grid:                        (full image; one char per pixel; rows must be equal length)
    ....KKKK....
    patch: 40 52                 (optional, repeatable: overlay at x y; '_' = keep pixel underneath)
    _KK_
    K__K

    python -m pipeline.pixgrid render a.pix [b.pix ...] --out DIR [--zoom 4] [--bg #DFEAF6] [--grid]
    python -m pipeline.pixgrid sheet a.pix b.pix ... --out sheet.png [--zoom 3] [--cols 5] [--labels]
    python -m pipeline.pixgrid stats a.pix          (colours, orphans = pixels with no same-colour 8-neighbour)
    python -m pipeline.pixgrid fromimg in.png --out x.pix   (convert a PNG back to a grid, auto legend)
"""
import argparse
import os
import string

import numpy as np
from PIL import Image, ImageDraw

KEEP = "_"


def _hex(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)) + (255,)


def load(path, _depth=0):
    """-> (rgba uint8 HxWx4, legend {char: (hex, role)})"""
    lines = open(path).read().splitlines()
    legend, img, mode, patch_at, rows, size = {}, None, None, None, [], None
    base_dir = os.path.dirname(os.path.abspath(path))

    def flush():
        nonlocal img, rows
        if mode == "grid" and rows:
            img = _paint(np.zeros((len(rows), len(rows[0]), 4), np.uint8), rows, legend, 0, 0, path)
        elif mode == "patch" and rows:
            if img is None:
                raise ValueError(f"{path}: patch before grid/extends")
            img = _paint(img, rows, legend, patch_at[0], patch_at[1], path)
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
            img, base_legend = load(os.path.join(base_dir, s.split(":", 1)[1].strip()), _depth + 1)
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


def _paint(img, rows, legend, x0, y0, path):
    w = len(rows[0])
    for j, r in enumerate(rows):
        if len(r) != w:
            raise ValueError(f"{path}: row {j} has {len(r)} chars, expected {w}")
        for i, ch in enumerate(r):
            if ch == KEEP:
                continue
            if ch not in legend:
                raise ValueError(f"{path}: row {j} col {i}: char {ch!r} not in legend")
            hx = legend[ch][0]
            y, x = y0 + j, x0 + i
            if 0 <= y < img.shape[0] and 0 <= x < img.shape[1]:
                img[y, x] = (0, 0, 0, 0) if hx in ("transparent", ".") else _hex(hx)
    return img


def stats(img):
    a = img[..., 3] > 0
    flat = img[..., :3].astype(np.int32)
    key = (flat[..., 0] << 16) | (flat[..., 1] << 8) | flat[..., 2]
    key = np.where(a, key, -1)
    H, W = key.shape
    pad = np.pad(key, 1, constant_values=-2)
    same = np.zeros((H, W), bool)
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            if dy or dx:
                same |= pad[1 + dy:1 + dy + H, 1 + dx:1 + dx + W] == key
    orphans = [(int(x), int(y)) for y, x in zip(*np.nonzero(a & ~same))]
    return {"size": [W, H], "colours": int(len(np.unique(key[a]))), "orphans": len(orphans), "orphan_xy": orphans[:20]}


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
    return im


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


def from_image(path):
    im = np.array(Image.open(path).convert("RGBA"))
    chars = iter(c for c in string.ascii_letters + string.digits + "!$%&*+-/<>?@^~|;" if c not in ("_", "."))
    legend, rows = {}, []
    for y in range(im.shape[0]):
        r = ""
        for x in range(im.shape[1]):
            p = im[y, x]
            if p[3] < 128:
                r += "."
                continue
            hx = "#%02X%02X%02X" % tuple(p[:3])
            if hx not in legend:
                legend[hx] = next(chars)
            r += legend[hx]
        rows.append(r)
    txt = [f"size: {im.shape[1]} {im.shape[0]}", "legend:", ". = transparent"]
    txt += [f"{c} = {hx}" for hx, c in legend.items()] + ["grid:"] + rows
    return "\n".join(txt) + "\n"


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("render")
    r.add_argument("files", nargs="+")
    r.add_argument("--out", required=True)
    r.add_argument("--zoom", type=int, default=4)
    r.add_argument("--bg", default="#DFEAF6")
    r.add_argument("--grid", action="store_true")
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
    a = ap.parse_args()
    if a.cmd == "render":
        os.makedirs(a.out, exist_ok=True)
        for p in a.files:
            img, _ = load(p)
            n = os.path.splitext(os.path.basename(p))[0]
            to_image(img).save(os.path.join(a.out, f"{n}.png"))
            to_image(img, a.zoom, a.bg, a.grid).save(os.path.join(a.out, f"{n}_x{a.zoom}.png"))
            print(n, stats(img))
    elif a.cmd == "sheet":
        sheet(a.files, a.zoom, a.cols, a.bg).save(a.out)
        print("wrote", a.out)
    elif a.cmd == "stats":
        for p in a.files:
            print(p, stats(load(p)[0]))
    elif a.cmd == "fromimg":
        open(a.out, "w").write(from_image(a.file))
        print("wrote", a.out)


if __name__ == "__main__":
    main()
