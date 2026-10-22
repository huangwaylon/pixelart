"""2D illustration -> pixel art (for hand-designed anime portraits / full-body art; NOT derived from the 3D model).

Source: data/illustrations/<name>.json
{
  "canvas": [768, 768],                # design units (illustrators draw at this size; 8x = design_scale)
  "size": [96, 96],                    # target pixel size
  "palette": "cw_oatmeal",             # palette file; colours referenced by name
  "outline": {"color": "outline", "selout": true, "line_colors": {"hair": "plum_0", ...}},  # exterior line pass
  "layers": [                          # drawn in order (back to front; optional "z" re-sorts, stable)
    {"name": "hair_back", "fill": "hair_1", "d": "M 100 200 C ... Z", "line": "plum_0", "line_w": 6},
    {"name": "face", "fill": "skin_2", "paths": ["M ...Z", "M ...Z"], "line": "auto", "line_color": "line_skin"},
    {"name": "face_shade", "fill": "skin_1", "d": "..."},          # *_shade/*_hi: clipped to part "face"
    {"name": "eyes", "group": "face_parts", "shapes": [{"fill": "ink", "d": "..."}, ...]}
  ],
  "panels": [{"name": "front", "layers": [...]}, ...],   # optional: several canvases side by side (model sheet)
  "anchors": {"eye_L": [40, 50]},      # pixel coords of face-cel anchors (per panel when panels are used)
  "cels": {"eye_L": "eye_L_neutral"},  # slot -> cel file data/illustrations/<dir>/face/<cel>.json (or inline dict)
  "variants": {                        # expression / pose swaps: replace or add layers by name, swap cels
    "smile": {"replace": {"mouth": {"fill": "plum_0", "d": "..."}}, "hide": ["mouth_neutral"],
              "cels": {"mouth": "mouth_smile"}}
  }
}
Path syntax: SVG path data, commands M L H V C S Q T Z (absolute and relative), arcs not supported.
"d" sub-paths combine even-odd (holes); entries of "paths" are unioned.
Layer keys:
  fill            palette colour of the shape; rasterized by pixel-centre sampling (no AA)
  line            "auto" -> 1 px pixel-perfect line on the part's own edge where it borders a part BEHIND it
                  (lower z); the silhouette against the background is drawn by the exterior outline pass.
                  Colour = "line_color" or outline.line_colors[part]. "line_bg": true also lines background edges.
                  Any other value -> a stroke of that colour, width "line_w" (design units), L-doubles removed.
  part            part name (default: layer name minus _shade/_shade2/_hi/_hi2/_dark/_line suffix)
  clip            list of part names (or true = own part); shape only paints over those parts. Layers with a
                  shading suffix clip to their own part by default and never change part ownership; other clipped
                  layers (e.g. a hem band clipped to the coat) become their own part (own sel-out / auto line).
  mirror          x (design units): also draw the shape mirrored about this vertical axis
  translate       [dx, dy] design units
  z               sort key (layers without z inherit the previous layer's z)
Face cel file: {"anchor": [ax, ay], "legend": {"#": "ink", "o": "iris_1", "x": null}, "grid": ["..#..", ...]}
  A cel ref "name:flip" mirrors the grid horizontally (anchor mirrored too).
  '.' and ' ' are transparent, null in the legend = clear to the base face colour under the anchor ("base" key).
Overrides: overrides/illustrations/<name>[_<variant>].png (opaque pixels replace; #FF00FF = transparent).

    python -m pipeline.illustrate data/illustrations/S4/bust.json --out 00_REVIEW/r12_illustration
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
from .qa import orphan_count

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_TOK = re.compile(r"[MmLlHhVvCcSsQqTtZz]|-?\d*\.?\d+(?:[eE][-+]?\d+)?")
SUFFIXES = ("_shade2", "_shade", "_hi2", "_hi", "_dark", "_line")
DIRS4 = ((1, 0), (-1, 0), (0, 1), (0, -1))


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
            yield dict({k: v for k, v in layer.items() if k not in ("shapes",)}, **sh)
    else:
        yield layer


def part_of(layer):
    if layer.get("part"):
        return layer["part"]
    n = layer.get("name") or "anon"
    for s in SUFFIXES:
        if n.endswith(s):
            return n[: -len(s)]
    return n


def _is_shading(layer):
    n = layer.get("name") or ""
    return any(n.endswith(s) for s in SUFFIXES[:-1])


def _groups(sh):
    """-> list of polygon groups (each group combines even-odd; groups union), in design units."""
    ds = sh.get("paths") or ([sh["d"]] if sh.get("d") else [])
    tx, ty = sh.get("translate", (0, 0))
    out = []
    for d in ds:
        g = [[(px + tx, py + ty) for px, py in p] for p in parse_path(d)]
        out.append(g)
        if sh.get("mirror") is not None:
            m = sh["mirror"] + tx
            out.append([[(2 * m - px, py) for px, py in p] for p in g])
    return out


def _evenodd(polys, W, H, sx, sy):
    """Pixel-centre sampling of closed polygons (even-odd), no anti-aliasing."""
    ys = (np.arange(H) + 0.5) / sy
    xs = (np.arange(W) + 0.5) / sx
    inside = np.zeros((H, W), bool)
    for p in polys:
        if len(p) < 3:
            continue
        a = np.array(p, float)
        if not np.allclose(a[0], a[-1]):
            a = np.vstack([a, a[:1]])
        for (x0, y0), (x1, y1) in zip(a[:-1], a[1:]):
            if y0 == y1:
                continue
            rows = (y0 <= ys) != (y1 <= ys)
            if not rows.any():
                continue
            xi = x0 + (ys[rows] - y0) * (x1 - x0) / (y1 - y0)
            inside[rows] ^= xs[None, :] < xi[:, None]
    return inside


def thin_l(mask):
    """Remove L-shaped doubles from a 1px line mask (corner pixel of an L whose diagonal keeps the line
    8-connected). Returns (thinned mask, removed mask)."""
    m = mask.copy()
    H, W = m.shape
    removed = np.zeros_like(m)
    get = lambda y, x: 0 <= y < H and 0 <= x < W and m[y, x]
    for _ in range(2):
        changed = False
        for y, x in zip(*np.nonzero(m)):
            for (ay, ax), (by, bx) in (((0, -1), (1, 0)), ((0, 1), (1, 0)), ((0, -1), (-1, 0)), ((0, 1), (-1, 0))):
                if (get(y + ay, x + ax) and get(y + by, x + bx) and not get(y + ay + by, x + ax + bx)
                        and not get(y - ay, x - ax) and not get(y - by, x - bx)):
                    m[y, x] = False
                    removed[y, x] = True
                    changed = True
                    break
        if not changed:
            break
    return m, removed


def _resolve_layers(layers, variant_def):
    layers = copy.deepcopy(layers)
    if variant_def:
        hide = set(variant_def.get("hide", []))
        rep = variant_def.get("replace", {})
        layers = [dict(l, **rep[l["name"]]) if l.get("name") in rep else l for l in layers
                  if l.get("name") not in hide]
        names = {l.get("name") for l in layers}
        layers += [dict(l, name=n) for n, l in rep.items() if n not in names]
        layers += copy.deepcopy(variant_def.get("add", []))
    z, keyed = 0, []
    for k, l in enumerate(layers):
        z = l.get("z", z)
        keyed.append((z, k, l))
    return [l for _, _, l in sorted(keyed, key=lambda t: (t[0], t[1]))]


def rasterize(ill, palette, variant=None, layers=None):
    """-> palette index image (-1 transparent), per-pixel part-name map, part info {name: {z, line...}}."""
    vdef = ill.get("variants", {}).get(variant, {}) if variant else {}
    layers = _resolve_layers(layers if layers is not None else ill["layers"], vdef)
    cw, ch = ill["canvas"]
    W, H = ill["size"]
    sx, sy = W / cw, H / ch
    idx = np.full((H, W), -1, int)
    part = np.full((H, W), None, dtype=object)
    info = {}
    for k, layer in enumerate(layers):
        p = part_of(layer)
        shading = _is_shading(layer)
        if not shading and p not in info:
            info[p] = {"z": k}
        if layer.get("line") == "auto":
            info.setdefault(p, {"z": k}).update(auto=True, line_color=layer.get("line_color"),
                                                 line_bg=layer.get("line_bg", False),
                                                 line_mode=layer.get("line_mode", "front"))
        clip = layer.get("clip", True if shading else None)
        if clip is True:
            clip = [p]
        for sh in _shapes(layer):
            cmask = np.isin(part, clip) if clip else None
            if sh.get("fill"):
                mask = np.zeros((H, W), bool)
                for g in _groups(sh):
                    mask |= _evenodd(g, W, H, sx, sy)
                if cmask is not None:
                    mask &= cmask
                idx[mask] = palette.index[sh["fill"]]
                if not shading:
                    part[mask] = p
            if sh.get("line") and sh["line"] != "auto":
                lw = max(1, int(round(sh.get("line_w", 0) * sx)))
                m = Image.new("L", (W, H), 0)
                dr = ImageDraw.Draw(m)
                for g in _groups(sh):
                    for poly in g:
                        if len(poly) >= 2:
                            dr.line([(px * sx - 0.5, py * sy - 0.5) for px, py in poly], fill=255, width=lw)
                mask = np.array(m) > 127
                if lw == 1:
                    mask, _ = thin_l(mask)
                if cmask is not None:
                    mask &= cmask
                idx[mask] = palette.index[sh["line"]]
                part[mask & (part == None)] = p  # noqa: E711
    return idx, part, info


def auto_lines(idx, part, info, ill, palette):
    """1px pixel-perfect inner lines: each part with line:auto gets a line on its own edge pixels where it
    touches a part behind it (or, with line_mode 'back', on the behind part's pixels)."""
    H, W = idx.shape
    lc_map = ill.get("outline", {}).get("line_colors", {})
    out = idx.copy()
    for p, inf in sorted(info.items(), key=lambda t: t[1]["z"]):
        if not inf.get("auto"):
            continue
        col = inf.get("line_color") or lc_map.get(p) or ill.get("outline", {}).get("color", "outline")
        me = part == p
        line = np.zeros((H, W), bool)
        donor = np.full((H, W), -1, int)
        for dy, dx in DIRS4:
            nb = np.full((H, W), None, dtype=object)
            ys = slice(max(dy, 0), H + min(dy, 0)); yd = slice(max(-dy, 0), H + min(-dy, 0))
            xs = slice(max(dx, 0), W + min(dx, 0)); xd = slice(max(-dx, 0), W + min(-dx, 0))
            nb[yd, xd] = part[ys, xs]
            nbi = np.full((H, W), -1, int)
            nbi[yd, xd] = out[ys, xs]
            behind = np.vectorize(lambda q: q is not None and q != p and q in info and info[q]["z"] < inf["z"],
                                  otypes=[bool])(nb)
            if inf.get("line_bg"):
                behind |= (nb == None) & (nbi < 0)  # noqa: E711
            if inf.get("line_mode") == "back":
                # mark the behind pixel instead of our own
                tgt = np.zeros((H, W), bool)
                tgt[ys, xs] = (me & behind)[yd, xd]
                tgt &= part != None  # noqa: E711
                line |= tgt
            else:
                hit = me & behind
                donor[hit & (donor < 0)] = nbi[hit & (donor < 0)]
                line |= hit
        line, removed = thin_l(line)
        if inf.get("line_mode") != "back":
            fix = removed & (donor >= 0)
            out[fix] = donor[fix]
        out[line] = palette.index[col]
    return out


def pixel_pass(idx, part, info, ill, palette):
    """Pixel-art finishing: speck cleanup, inner auto lines, exterior outline (closed, pixel-perfect, sel-out)."""
    names = sorted({p for p in part.ravel() if p is not None})
    mat = np.full(idx.shape, -1, int)
    for k, n in enumerate(names):
        mat[part == n] = k
    keep = [palette.index[c] for c in ill.get("keep_colors", [])]
    out = despeckle(idx, keep=keep, max_island=1, material=mat)
    out = auto_lines(out, part, info, ill, palette)
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
                    if 0 <= yy < H and 0 <= xx < W and op[yy, xx] and part[yy, xx] in lc and y < H - 3:
                        out[y, x] = palette.index[lc[part[yy, xx]]]
                        break
    return out


def _load_cel(ref, base_dir):
    if isinstance(ref, dict):
        return ref
    return json.load(open(os.path.join(base_dir, "face", f"{ref}.json")))


def composite_cels(out, src, palette, base_dir, variant=None):
    """Stamp pixel-grid face cels at their named anchors (after all line passes; never despeckled)."""
    cels = dict(src.get("cels", {}))
    if variant:
        cels.update(src.get("variants", {}).get(variant, {}).get("cels", {}))
    anchors = src.get("anchors", {})
    H, W = out.shape
    for slot, ref in cels.items():
        if not ref or slot not in anchors:
            continue
        flip = isinstance(ref, str) and ref.endswith(":flip")
        cel = copy.deepcopy(_load_cel(ref[:-5] if flip else ref, base_dir))
        ax, ay = cel.get("anchor", (0, 0))
        if flip:
            wmax = max(len(r) for r in cel["grid"])
            cel["grid"] = [r.ljust(wmax, ".")[::-1] for r in cel["grid"]]
            ax = wmax - 1 - ax
        X, Y = anchors[slot]
        legend = cel.get("legend", {})
        base = cel.get("base")
        for r, row in enumerate(cel["grid"]):
            for c, ch in enumerate(row):
                if ch in ". " or ch not in legend:
                    continue
                y, x = Y - ay + r, X - ax + c
                if not (0 <= y < H and 0 <= x < W):
                    continue
                v = legend[ch]
                if v is None:
                    if base:
                        out[y, x] = palette.index[base]
                else:
                    out[y, x] = palette.index[v]
    return out


def _render_stack(src, ill, pal, base_dir, variant):
    idx, part, info = rasterize(ill, pal, variant, src["layers"])
    out = pixel_pass(idx, part, info, ill, pal)
    return composite_cels(out, src, pal, base_dir, variant)


def render_illustration(path, variant=None):
    ill = json.load(open(path))
    base_dir = os.path.dirname(os.path.abspath(path))
    pal = Palette(os.path.join(ROOT, "data", "palettes", f"{ill['palette']}.json"))
    if ill.get("panels"):
        tiles = []
        for pn in ill["panels"]:
            src = dict(pn)
            src.setdefault("variants", ill.get("variants", {}))
            tiles.append(_render_stack(src, ill, pal, base_dir, variant))
        out = np.concatenate(tiles, axis=1)
    else:
        out = _render_stack(ill, ill, pal, base_dir, variant)
    name = os.path.splitext(os.path.basename(path))[0]
    stats = {"override_px": 0}
    for cand in ([f"{name}_{variant}.png"] if variant else []) + [f"{name}.png"]:
        op = os.path.join(ROOT, "overrides", "illustrations", cand)
        if os.path.exists(op):
            rgba = np.array(Image.open(op).convert("RGBA"))
            for y, x in zip(*np.nonzero(rgba[..., 3] > 0)):
                r, g, b = (int(v) for v in rgba[y, x, :3])
                out[y, x] = -1 if (r, g, b) == (255, 0, 255) else pal.rgb.index((r, g, b))
                stats["override_px"] += 1
            break
    return pal, out, ill, stats


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
        pal, idx, _, stats = render_illustration(a.source, v)
        im = Image.fromarray(pal.to_rgba(idx))
        tag = v or "base"
        im.save(os.path.join(out, f"{name}_{tag}.png"))
        for k in (2, 4):
            im.resize((im.width * k, im.height * k), Image.NEAREST).save(os.path.join(out, f"{name}_{tag}_x{k}.png"))
        used = len(set(idx[idx >= 0].ravel().tolist()))
        print(f"{tag}: {used} colours, {orphan_count(idx)} orphans, overrides {stats['override_px']} px "
              f"({100 * stats['override_px'] / max(1, (idx >= 0).sum()):.1f}%)")
        cells.append((tag, im))
    # labelled preview sheet on three backgrounds (snow, navy, dialogue box)
    W, H = cells[0][1].size
    s = a.scale
    bgs = [(223, 234, 246, 255), (47, 58, 108, 255), (244, 234, 210, 255)]
    cols = min(len(cells), max(1, 5 if W < 200 else 1))
    rows = (len(cells) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * (W * s + 8) + 8, rows * (H * s + 22) + 8), (36, 22, 40))
    dr = ImageDraw.Draw(sheet)
    dr.fontmode = "1"
    for k, (tag, im) in enumerate(cells):
        x, y = 8 + (k % cols) * (W * s + 8), 8 + (k // cols) * (H * s + 22)
        dr.text((x, y), tag, fill=(244, 234, 210))
        bg = Image.new("RGBA", im.size, bgs[0])
        bg.alpha_composite(im)
        sheet.paste(bg.convert("RGB").resize((W * s, H * s), Image.NEAREST), (x, y + 14))
    sheet.save(os.path.join(out, f"{name}_sheet_x{s}.png"))
    # 1x readability strip: base on each background
    strip = Image.new("RGB", (len(bgs) * (W + 4) + 4, H + 8), (36, 22, 40))
    for k, c in enumerate(bgs):
        bg = Image.new("RGBA", (W, H), c)
        bg.alpha_composite(cells[0][1])
        strip.paste(bg.convert("RGB"), (4 + k * (W + 4), 4))
    strip.resize((strip.width * 2, strip.height * 2), Image.NEAREST).save(os.path.join(out, f"{name}_bgs_x2.png"))
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
