"""Contact sheet of guide renders.
  .venv/bin/python tools/hybrid/guide_sheet.py hybrid/guide/turn [--frame f00] [--passes clay,id,line,depth,mask,joints]
      [--dirs S,SE,..] [--crop 1.0] [--tile 256] [--out hybrid/guide/turn_sheet.png] [--cell]
Rows = passes, columns = directions.  'joints' draws the joint dots over the clay pass.  --cell adds a
row with the mask box-reduced to the 128 cell (true sprite scale, x2)."""
import json
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

ROOT = "/Users/waylonhuang/Documents/other/pixelart/swordswoman"
a = sys.argv[1:]


def opt(n, d=None):
    return a[a.index(n) + 1] if n in a else d


src = a[0] if os.path.isabs(a[0]) else os.path.join(ROOT, a[0])
frame = opt("--frame", "f00")
passes = opt("--passes", "clay,id,line,depth,mask,joints").split(",")
dirs = opt("--dirs", "S,SE,E,NE,N,NW,W,SW").split(",")
tile = int(opt("--tile", "256"))
crop = float(opt("--crop", "0.6"))           # fraction of the frame kept (centred on x, pivot-anchored y)
out = opt("--out", os.path.join(os.path.dirname(src), os.path.basename(src) + "_sheet.png"))
out = out if os.path.isabs(out) else os.path.join(ROOT, out)
BG = (118, 118, 118)
JCOL = {"eye": (40, 120, 255), "hand": (255, 200, 0), "foot": (0, 220, 120), "toe": (0, 220, 120), "sword": (255, 60, 60),
        "bow": (255, 0, 200), "bun": (160, 90, 40), "head": (255, 255, 255), "chin": (255, 255, 255), "root": (0, 0, 0),
        "elbow": (255, 140, 0), "knee": (0, 160, 90), "hips": (0, 0, 0), "chest": (0, 0, 0), "neck": (0, 0, 0)}


def jcol(n):
    for k, c in JCOL.items():
        if n.startswith(k):
            return c
    return (200, 200, 200)


def load(d, p):
    f = os.path.join(src, d, f"{frame}_{p}.png")
    if not os.path.exists(f):
        return None
    im = Image.open(f)
    if p == "depth":
        arr = np.array(im).astype(np.float32)
        if arr.ndim == 3:
            g = arr[..., 0]
            al = arr[..., 3] if arr.shape[2] == 4 else np.full(g.shape, g.max())
        else:
            g, al = arr, np.ones_like(arr)
        mx = 65535.0 if g.max() > 255 else 255.0
        al = (al / (65535.0 if al.max() > 255 else 255.0) * 255).astype(np.uint8)
        g8 = (g / mx * 255).astype(np.uint8)
        im = Image.fromarray(np.dstack([g8, g8, g8, al]), "RGBA")
    return im.convert("RGBA")


def comp(im):
    bg = Image.new("RGBA", im.size, BG + (255,))
    bg.alpha_composite(im)
    return bg


def cropbox(W):
    c = int(W * crop)
    x0 = (W - c) // 2
    y0 = int(W * 104 / 128) - int(c * 0.86)
    y0 = max(0, min(W - c, y0))
    return (x0, y0, x0 + c, y0 + c)


rows = []
for p in passes + (["cell"] if "--cell" in a else []):
    row = []
    for d in dirs:
        if p == "joints":
            im = load(d, "clay")
            jf = os.path.join(src, d, f"{frame}_joints.json")
            if im is None or not os.path.exists(jf):
                row.append(None)
                continue
            im = comp(im)
            J = json.load(open(jf))["joints"]
            dr = ImageDraw.Draw(im)
            r = max(3, im.size[0] // 160)
            for n, j in J.items():
                if n in ("guard", "tip"):
                    continue
                x, y = j["px"]
                c = jcol(n)
                if j["visible"]:
                    dr.ellipse([x - r, y - r, x + r, y + r], fill=c, outline=(0, 0, 0))
                else:
                    dr.ellipse([x - r, y - r, x + r, y + r], outline=c, width=2)
        elif p == "cell":
            m = load(d, "mask")
            if m is None:
                row.append(None)
                continue
            W = m.size[0]
            k = W // 128
            al = np.array(m)[..., 3].astype(np.float32).reshape(128, k, 128, k).mean((1, 3))
            cl = load(d, "clay")
            rgb = np.array(cl.convert("RGB").resize((128, 128), Image.BOX)) if cl else np.full((128, 128, 3), 200, np.uint8)
            cellim = np.dstack([rgb, np.where(al > 127, 255, 0).astype(np.uint8)])
            im = comp(Image.fromarray(cellim, "RGBA")).resize((W, W), Image.NEAREST)
        else:
            im = load(d, p)
            if im is None:
                row.append(None)
                continue
            if p == "line":
                wb = Image.new("RGBA", im.size, (255, 255, 255, 255))
                wb.alpha_composite(im)
                im = wb
            else:
                im = comp(im)
        im = im.crop(cropbox(im.size[0])).resize((tile, tile), Image.LANCZOS if p != "id" else Image.NEAREST)
        row.append(im)
    rows.append((p, row))
H = 18
sheet = Image.new("RGB", (60 + tile * len(dirs), H + tile * len(rows)), (40, 40, 40))
dr = ImageDraw.Draw(sheet)
for i, d in enumerate(dirs):
    dr.text((60 + i * tile + tile // 2 - 6, 3), d, fill=(255, 255, 255))
for r, (p, row) in enumerate(rows):
    dr.text((4, H + r * tile + tile // 2), p, fill=(255, 255, 255))
    for i, im in enumerate(row):
        if im is not None:
            sheet.paste(im.convert("RGB"), (60 + i * tile, H + r * tile))
sheet.save(out)
print(out, sheet.size)
