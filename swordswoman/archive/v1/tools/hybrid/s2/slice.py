#!/usr/bin/env python3
"""Slice a Gemini multi-panel sheet back into per-panel hi-res images.

  slice.py GEN.png GUIDE_META.json --out-dir D [--pad-top F --pad-bot F] [--mirror|--mirror-cells] [--thr 28]

Non-white pixels are grouped into connected components (after a small dilation); each component is
assigned to the grid cell that holds its centroid (so a smear that crosses the cell border stays with
its figure). Each panel is written as <name>_hires.png: RGBA, white background removed by a soft
key against white, cropped to the panel's components + margin, un-mirrored.
"""
import argparse, json, os
import numpy as np
from PIL import Image
from scipy import ndimage as ndi

ap = argparse.ArgumentParser()
ap.add_argument("gen"); ap.add_argument("meta"); ap.add_argument("--out-dir", required=True)
ap.add_argument("--pad-top", type=float, default=0.0, help="fraction of the gen height that is padding on top")
ap.add_argument("--pad-bot", type=float, default=0.0)
ap.add_argument("--mirror", action="store_true", help="whole sheet was mirrored: flip gen back first")
ap.add_argument("--mirror-cells", action="store_true", help="each cell mirrored in place: flip each crop")
ap.add_argument("--thr", type=float, default=24)
ap.add_argument("--margin", type=int, default=24)
a = ap.parse_args()
os.makedirs(a.out_dir, exist_ok=True)
meta = json.load(open(a.meta))
im = Image.open(a.gen).convert("RGB")
if a.mirror:
    im = im.transpose(Image.FLIP_LEFT_RIGHT)
W, H = im.size
y0 = int(round(a.pad_top * H)); y1 = H - int(round(a.pad_bot * H))
arr = np.asarray(im).astype(float)
dist = np.sqrt(((255 - arr) ** 2).sum(-1))
fg = dist > a.thr
fgd = ndi.binary_dilation(fg, iterations=3)
lab, n = ndi.label(fgd)
sw, sh = meta["size"]
sx, sy = W / sw, (y1 - y0) / sh
cells = []
for p in meta["panels"]:
    x0b, y0b, x1b, y1b = p["box"]
    cells.append((p, (x0b * sx, y0 + y0b * sy, x1b * sx, y0 + y1b * sy)))
assign = {}
sizes = ndi.sum(np.ones_like(lab), lab, index=np.arange(1, n + 1))
coms = ndi.center_of_mass(fgd, lab, index=np.arange(1, n + 1))
for i, ((cy, cx), s) in enumerate(zip(coms, sizes), start=1):
    if s < 40:
        continue
    for k, (p, (bx0, by0, bx1, by1)) in enumerate(cells):
        if bx0 <= cx < bx1 and by0 <= cy < by1:
            assign.setdefault(k, []).append(i)
# alpha: soft key from white (premultiplied un-mix), so pale smears survive as partial alpha
alpha = np.clip((dist - 6) / 40.0, 0, 1)
for k, (p, box) in enumerate(cells):
    ids = assign.get(k, [])
    m = np.isin(lab, ids)
    if not m.any():
        print("EMPTY", p["name"]); continue
    ys, xs = np.nonzero(m)
    bx0, by0 = max(xs.min() - a.margin, 0), max(ys.min() - a.margin, 0)
    bx1, by1 = min(xs.max() + a.margin, W), min(ys.max() + a.margin, H)
    al = (alpha * m)[by0:by1, bx0:bx1]
    al[ndi.binary_fill_holes(fg[by0:by1, bx0:bx1] & m[by0:by1, bx0:bx1]) & (al < 1)] = 1  # solid interior
    rgb = arr[by0:by1, bx0:bx1]
    # un-premultiply against white
    safe = np.maximum(al, 1e-3)[..., None]
    col = np.clip((rgb - 255 * (1 - al[..., None])) / safe, 0, 255)
    out = np.dstack([col, al * 255]).astype(np.uint8)
    o = Image.fromarray(out, "RGBA")
    if a.mirror_cells:
        o = o.transpose(Image.FLIP_LEFT_RIGHT)
    path = os.path.join(a.out_dir, p["name"] + "_gen.png")
    o.save(path)
    # also flat-on-white for pixelize's flood path
    flat = Image.new("RGB", o.size, "white"); flat.paste(o, (0, 0), o)
    flat.save(path.replace("_gen.png", "_genflat.png"))
    json.dump({"guide": p["guide"], "src": a.gen, "crop": [int(bx0), int(by0), int(bx1), int(by1)]},
              open(path.replace("_gen.png", "_gen.json"), "w"))
    print(p["name"], o.size, "components", len(ids))
