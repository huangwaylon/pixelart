"""2D illustration -> pixel art (for hand-designed anime portraits / full-body art; NOT derived from the 3D model).

Source: data/illustrations/<name>.json
{
  "canvas": [1000, 1250],              # design units (illustrators draw at this size)
  "size": [96, 120],                   # target pixel size
  "palette": "cw_oatmeal",             # palette file; colours referenced by name
  "outline": {"color": "outline", "selout": true, "line_colors": {...}},   # optional exterior line pass
  "layers": [                          # drawn in order (back to front)
    {"name": "hair_back", "fill": "hair_1", "d": "M 100 200 C ... Z", "line": "plum_0", "line_w": 6},
    {"name": "face", "fill": "skin_1", "d": "..."},
    {"name": "eyes", "group": "face_parts", "shapes": [{"fill": "ink", "d": "..."}, ...]}
  ],
  "variants": {                        # expression / pose swaps: replace or add layers by name
    "smile": {"replace": {"mouth": {"fill": "plum_0", "d": "..."}}, "hide": ["mouth_neutral"]}
  }
}
Path syntax: SVG path data, commands M L H V C S Q T Z (absolute and relative), arcs not supported.
Strokes ("line"/"line_w" in design units) are drawn as pixel lines without anti-aliasing.

    python -m pipeline.illustrate data/illustrations/s4_bust.json --out 00_REVIEW/r12_illustration
"""
import argparse
import copy
import json
import os
import re

import numpy as np
from PIL import Image, ImageDraw

from .palette import Palette
from .render import despeckle, pixel_perfect_outline

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_TOK = re.compile(r"[MmLlHhVvCcSsQqTtZz]|-?\d*\.?\d+(?:[eE][-+]?\d+)?")


def parse_path(d, steps=16):
    """SVG path data -> list of polylines (each a list of (x, y)); beziers flattened."""
    toks = _TOK.findall(d)
    i, cmd = 0, None
    x = y = sx = sy = 0.0
    last_c = None
    polys, cur = [], []

    def num():
        nonlocal i
        v = float(toks[i]); i += 1
        return v

    while i < len(toks):
        if re.match(r"[A-Za-z]", toks[i]):
            cmd = toks[i]; i += 1
            if cmd in "Zz":
                if cur:
                    cur.append(cur[0]); polys.append(cur); cur = []
                x, y = sx, sy
                continue
        rel = cmd.islower()
        c = cmd.upper()
        if c == "M":
            nx, ny = num(), num()
            if rel:
                nx, ny = x + nx, y + ny
            if cur:
                polys.append(cur)
            x, y, sx, sy = nx, ny, nx, ny
            cur = [(x, y)]
            cmd = "l" if rel else "L"
        elif c == "L":
            nx, ny = num(), num()
            x, y = (x + nx, y + ny) if rel else (nx, ny)
            cur.append((x, y))
        elif c == "H":
            nx = num(); x = x + nx if rel else nx; cur.append((x, y))
        elif c == "V":
            ny = num(); y = y + ny if rel else ny; cur.append((x, y))
        elif c in "CS":
            if c == "C":
                x1, y1 = num(), num()
                if rel:
                    x1, y1 = x + x1, y + y1
            else:
                x1, y1 = (2 * x - last_c[0], 2 * y - last_c[1]) if last_c else (x, y)
            x2, y2, ex, ey = num(), num(), num(), num()
            if rel:
                x2, y2, ex, ey = x + x2, y + y2, x + ex, y + ey
            for k in range(1, steps + 1):
                t = k / steps
                mt = 1 - t
                cur.append((mt ** 3 * x + 3 * mt * mt * t * x1 + 3 * mt * t * t * x2 + t ** 3 * ex,
                            mt ** 3 * y + 3 * mt * mt * t * y1 + 3 * mt * t * t * y2 + t ** 3 * ey))
            last_c = (x2, y2)
            x, y = ex, ey
            continue
        elif c in "QT":
            if c == "Q":
                x1, y1 = num(), num()
                if rel:
                    x1, y1 = x + x1, y + y1
            else:
                x1, y1 = (2 * x - last_c[0], 2 * y - last_c[1]) if last_c else (x, y)
            ex, ey = num(), num()
            if rel:
                ex, ey = x + ex, y + ey
            for k in range(1, steps + 1):
                t = k / steps
                mt = 1 - t
                cur.append((mt * mt * x + 2 * mt * t * x1 + t * t * ex, mt * mt * y + 2 * mt * t * y1 + t * t * ey))
            last_c = (x1, y1)
            x, y = ex, ey
            continue
        else:
            raise ValueError(f"unsupported path command {cmd}")
        last_c = None
    if cur:
        polys.append(cur)
    return polys


def _shapes(layer):
    if "shapes" in layer:
        for sh in layer["shapes"]:
            yield dict({k: v for k, v in layer.items() if k not in ("shapes", "name")}, **sh)
    else:
        yield layer


def rasterize(ill, palette, variant=None):
    """-> palette index image (-1 transparent), plus a per-pixel layer-name map (for line colours)."""
    ill = copy.deepcopy(ill)
    layers = ill["layers"]
    if variant:
        v = ill.get("variants", {}).get(variant, {})
        hide = set(v.get("hide", []))
        rep = v.get("replace", {})
        layers = [dict(l, **rep[l["name"]]) if l.get("name") in rep else l for l in layers if l.get("name") not in hide]
        names = {l.get("name") for l in layers}
        layers += [dict(l, name=n) for n, l in rep.items() if n not in names]
        layers += v.get("add", [])
    cw, ch = ill["canvas"]
    W, H = ill["size"]
    sx, sy = W / cw, H / ch
    idx = np.full((H, W), -1, int)
    lname = np.full((H, W), None, dtype=object)
    for layer in layers:
        for sh in _shapes(layer):
            polys = parse_path(sh["d"])
            pts = [[(px * sx, py * sy) for px, py in p] for p in polys]
            if sh.get("fill"):
                m = Image.new("L", (W, H), 0)
                dr = ImageDraw.Draw(m)
                for p in pts:                       # even-odd via XOR of each sub-path
                    if len(p) >= 3:
                        sub = Image.new("L", (W, H), 0)
                        ImageDraw.Draw(sub).polygon(p, fill=255)
                        m = Image.fromarray(np.bitwise_xor(np.array(m), np.array(sub)))
                mask = np.array(m) > 127
                idx[mask] = palette.index[sh["fill"]]
                lname[mask] = layer.get("name")
            if sh.get("line"):
                lw = max(1, int(round(sh.get("line_w", 0) * sx)))
                m = Image.new("L", (W, H), 0)
                dr = ImageDraw.Draw(m)
                for p in pts:
                    if len(p) >= 2:
                        dr.line(p, fill=255, width=lw)
                mask = np.array(m) > 127
                idx[mask] = palette.index[sh["line"]]
                lname[mask] = layer.get("name") + "_line" if layer.get("name") else "line"
    return idx, lname


def pixel_pass(idx, lname, ill, palette):
    """Pixel-art finishing: speck cleanup, exterior outline (closed, pixel-perfect, sel-out per layer)."""
    out = despeckle(idx, max_island=1)
    o = ill.get("outline")
    if not o:
        return out
    ol = palette.index[o.get("color", "outline")]
    op = out >= 0
    grow = np.zeros_like(op)
    grow[1:, :] |= op[:-1, :]; grow[:-1, :] |= op[1:, :]; grow[:, 1:] |= op[:, :-1]; grow[:, :-1] |= op[:, 1:]
    ring = grow & ~op
    out[ring] = ol
    out = pixel_perfect_outline(out, {ol}, exterior=ring)
    if o.get("selout"):
        lc = o.get("line_colors", {})
        H, W = out.shape
        for y in range(H):
            for x in range(W):
                if out[y, x] != ol or not ring[y, x]:
                    continue
                # lit side = fill lies to the right/below of this outline pixel (light from upper-left)
                for dy, dx in ((1, 0), (0, 1)):
                    yy, xx = y + dy, x + dx
                    if 0 <= yy < H and 0 <= xx < W and op[yy, xx] and lname[yy, xx] in lc and y < H - 3:
                        out[y, x] = palette.index[lc[lname[yy, xx]]]
                        break
    return out


def render_illustration(path, variant=None):
    ill = json.load(open(path))
    pal = Palette(os.path.join(ROOT, "data", "palettes", f"{ill['palette']}.json"))
    idx, lname = rasterize(ill, pal, variant)
    return pal, pixel_pass(idx, lname, ill, pal), ill


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("source")
    ap.add_argument("--out", required=True)
    ap.add_argument("--scale", type=int, default=4, help="nearest-neighbour preview scale")
    a = ap.parse_args()
    ill = json.load(open(a.source))
    name = os.path.splitext(os.path.basename(a.source))[0]
    out = os.path.join(ROOT, a.out)
    os.makedirs(out, exist_ok=True)
    variants = [None] + list(ill.get("variants", {}).keys())
    cells = []
    for v in variants:
        pal, idx, _ = render_illustration(a.source, v)
        im = Image.fromarray(pal.to_rgba(idx))
        tag = v or "base"
        im.save(os.path.join(out, f"{name}_{tag}.png"))
        cells.append((tag, im))
    # labelled preview sheet
    W, H = ill["size"]
    s = a.scale
    cols = min(len(cells), 5)
    rows = (len(cells) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * (W * s + 8) + 8, rows * (H * s + 22) + 8), (36, 22, 40))
    dr = ImageDraw.Draw(sheet)
    dr.fontmode = "1"
    for k, (tag, im) in enumerate(cells):
        x, y = 8 + (k % cols) * (W * s + 8), 8 + (k // cols) * (H * s + 22)
        dr.text((x, y), tag, fill=(244, 234, 210))
        bg = Image.new("RGBA", im.size, (223, 234, 246, 255))
        bg.alpha_composite(im)
        sheet.paste(bg.convert("RGB").resize((W * s, H * s), Image.NEAREST), (x, y + 14))
    sheet.save(os.path.join(out, f"{name}_sheet_x{s}.png"))
    # engine sheet: all variants in a row, transparent
    eng = Image.new("RGBA", (W * len(cells), H), (0, 0, 0, 0))
    for k, (_, im) in enumerate(cells):
        eng.alpha_composite(im, (k * W, 0))
    eng.save(os.path.join(out, f"{name}_spritesheet.png"))
    json.dump({"image": f"{name}_spritesheet.png", "frameSize": [W, H], "frames": [t for t, _ in cells]},
              open(os.path.join(out, f"{name}_spritesheet.json"), "w"), indent=1)
    print("wrote", out)


if __name__ == "__main__":
    main()
