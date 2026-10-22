"""Pixel-level review sheets: every frame at high zoom with coordinate grid, rulers and colour legend.

    python -m pipeline.pixelreview --build out/variants/A_chibi --dirs S SE --frames 1-12
Writes <build>/pixelreview/<DIR>_<NN>.png plus census.json (colour counts, islands, colours per frame).
Reviewers cite pixels as (x,y) and record fixes as override JSON (overrides/...), each with a reason.
"""
import argparse
import json
import os

import numpy as np
from PIL import Image, ImageDraw

from .palette import Palette

INK = (36, 22, 40)
GRID = (205, 214, 228)
TXT = (244, 234, 210)


def load(build):
    sj = [f for f in os.listdir(build) if f.endswith("_sheet.json")][0]
    meta = json.load(open(os.path.join(build, sj)))
    pdir = os.path.join(build, "inputs", "data")
    if os.path.isdir(os.path.join(pdir, "palettes")):
        pf = os.path.join(pdir, "palettes", os.listdir(os.path.join(pdir, "palettes"))[0])
    else:
        pf = os.path.join(pdir, "palette.json")
    pal = Palette(pf)
    idx = pal.from_rgba(np.array(Image.open(os.path.join(build, meta["image"])).convert("RGBA")))
    return meta, pal, idx


def islands(f, max_size=2):
    H, W = f.shape
    seen = np.zeros_like(f, bool)
    small = []
    for y in range(H):
        for x in range(W):
            if seen[y, x] or f[y, x] < 0:
                continue
            v, comp, st = f[y, x], [], [(y, x)]
            seen[y, x] = True
            while st:
                cy, cx = st.pop()
                comp.append((cx, cy))
                for yy, xx in ((cy - 1, cx), (cy + 1, cx), (cy, cx - 1), (cy, cx + 1)):
                    if 0 <= yy < H and 0 <= xx < W and not seen[yy, xx] and f[yy, xx] == v:
                        seen[yy, xx] = True
                        st.append((yy, xx))
            if len(comp) <= max_size:
                small.append({"color": int(v), "px": comp})
    return small


def sheet_for(f, pal, title, z=12, prev=None):
    H, W = f.shape
    ys, xs = np.nonzero(f >= 0)
    x0, x1 = max(xs.min() - 2, 0), min(xs.max() + 3, W)
    y0, y1 = max(ys.min() - 2, 0), min(ys.max() + 3, H)
    cw, ch = (x1 - x0) * z, (y1 - y0) * z
    used = sorted(set(int(v) for v in np.unique(f) if v >= 0))
    leg_w = 190
    img = Image.new("RGB", (cw + 40 + leg_w, ch + 60), INK)
    d = ImageDraw.Draw(img)
    d.fontmode = "1"
    d.text((8, 6), title, fill=TXT)
    ox, oy = 32, 40
    for y in range(y0, y1):
        for x in range(x0, x1):
            v = f[y, x]
            px, py = ox + (x - x0) * z, oy + (y - y0) * z
            if v >= 0:
                col = pal.rgb[v]
            elif prev is not None and prev[y, x] >= 0:
                col = tuple(int(c * 0.25 + 235 * 0.75) for c in pal.rgb[prev[y, x]])  # onion of previous frame
            else:
                col = (240, 244, 250) if (x + y) % 2 else (230, 236, 244)
            d.rectangle([px, py, px + z - 1, py + z - 1], fill=col)
    for x in range(x0, x1 + 1):
        c = (150, 160, 180) if x % 4 == 0 else GRID
        d.line([(ox + (x - x0) * z, oy), (ox + (x - x0) * z, oy + ch)], fill=c)
        if x % 4 == 0 and x < x1:
            d.text((ox + (x - x0) * z + 1, oy - 12), str(x), fill=TXT)
    for y in range(y0, y1 + 1):
        c = (150, 160, 180) if y % 4 == 0 else GRID
        d.line([(ox, oy + (y - y0) * z), (ox + cw, oy + (y - y0) * z)], fill=c)
        if y % 4 == 0 and y < y1:
            d.text((4, oy + (y - y0) * z + 1), str(y), fill=TXT)
    lx = ox + cw + 12
    for k, v in enumerate(used):
        cnt = int((f == v).sum())
        d.rectangle([lx, oy + k * 16, lx + 12, oy + k * 16 + 12], fill=pal.rgb[v])
        d.text((lx + 18, oy + k * 16 + 1), f"{v:2d} {pal.names[v][:12]} {cnt}", fill=TXT)
    return img


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--build", required=True)
    ap.add_argument("--dirs", nargs="+", default=None)
    ap.add_argument("--frames", default=None, help="e.g. 1-12 or 3,6,9 (1-based)")
    ap.add_argument("--zoom", type=int, default=12)
    a = ap.parse_args()
    meta, pal, idx = load(a.build)
    W, H = meta["frameSize"]
    dirs = a.dirs or meta["directions"]
    n = len(meta["frames"])
    if a.frames:
        if "-" in a.frames:
            s, e = a.frames.split("-")
            frames = list(range(int(s) - 1, int(e)))
        else:
            frames = [int(v) - 1 for v in a.frames.split(",")]
    else:
        frames = list(range(n))
    out = os.path.join(a.build, "pixelreview")
    os.makedirs(out, exist_ok=True)
    census = {}
    for d in dirs:
        r = meta["directions"].index(d)
        for i in frames:
            f = idx[r * H:(r + 1) * H, i * W:(i + 1) * W]
            prev = idx[r * H:(r + 1) * H, (i - 1) * W:i * W] if i > 0 else None
            inf = meta["frames"][i]
            title = f"{d} f{i + 1} {inf['name']} {inf['duration_ms']}ms z{inf['z_px']}  (x,y = column,row in {W}x{H} cell; faint = previous frame)"
            sheet_for(f, pal, title, a.zoom, prev).save(os.path.join(out, f"{d}_{i + 1:02d}.png"))
            isl = [s_ for s_ in islands(f) if s_["color"] != pal.special["outline"]]  # outline stair-steps are diagonal by design
            census[f"{d}_{i + 1:02d}"] = {
                "colours": len(set(np.unique(f[f >= 0]).tolist())),
                "opaque_px": int((f >= 0).sum()),
                "small_islands": [{"color": pal.names[s["color"]], "px": s["px"]} for s in isl],
            }
    with open(os.path.join(out, "census.json"), "w") as fh:
        json.dump(census, fh, indent=1)
    print(f"wrote {len(census)} review sheets to {out}")


if __name__ == "__main__":
    main()
