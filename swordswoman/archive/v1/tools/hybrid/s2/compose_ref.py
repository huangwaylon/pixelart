#!/usr/bin/env python3
"""S2 gridsheet v2: guide sheets with FINISHED REFERENCE PANELS inside the same image.

Layout 3 x 2 (aspect 3:2). Ref panels hold already-approved Gemini art (sliced from the turn sheet),
fitted to the guide's rest-pose silhouette box, so Gemini sees the finished character, its facing,
handedness and scale INSIDE the image it edits. Guide panels are colour clay as in compose.py.
Everything is built in mirror space per cell (--mirror-cells) for the handedness trick.

  compose_ref.py LAYOUT --out out.png
LAYOUTS: walk (ref SE, k0, k1 / k2, k3, ref S), slash (ref SE, k0, k1 / k2, k3, ref S),
         jump (ref E, crouch, apex / land, ref SE, ref S)
"""
import argparse, json, os, sys
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import compose as C

SL = "hybrid/S2_gridsheet/r1/slice"
L = {
    "walk": [[("ref", "turn_SE"), ("g", "walk_SE_keys/SE/f00", "walk_SE_k0"), ("g", "walk_SE_keys/SE/f01", "walk_SE_k1")],
             [("g", "walk_SE_keys/SE/f02", "walk_SE_k2"), ("g", "walk_SE_keys/SE/f03", "walk_SE_k3"), ("ref", "turn_S")]],
    "slash": [[("ref", "turn_SE"), ("g", "slash_SE_keys/SE/f00", "slash_SE_k0"), ("g", "slash_SE_keys/SE/f01", "slash_SE_k1")],
              [("g", "slash_SE_keys/SE/f02", "slash_SE_k2"), ("g", "slash_SE_keys/SE/f03", "slash_SE_k3"), ("ref", "turn_S")]],
    "jump": [[("ref", "turn_E"), ("g", "jump_E_keys/E/f00", "jump_E_crouch"), ("g", "jump_E_keys/E/f01", "jump_E_apex")],
             [("g", "jump_E_keys/E/f02", "jump_E_land"), ("ref", "turn_SE"), ("ref", "turn_S")]],
}


def ref_panel(name, cell):
    d = name.split("_")[1]
    gm = np.asarray(Image.open(f"{C.G}/turn/{d}/f00_mask.png").convert("L").crop(C.WIN)) > 127
    ys, xs = np.nonzero(gm)
    k = cell / (C.WIN[2] - C.WIN[0])
    gy0, gy1, gcx = ys.min() * k, ys.max() * k, xs.mean() * k
    im = Image.open(f"{SL}/{name}_gen.png").convert("RGBA")
    a = np.asarray(im)[..., 3] > 128
    ys2, xs2 = np.nonzero(a)
    # fit height to the guide figure height (bow to sole; both include the bow)
    s = (gy1 - gy0) / (ys2.max() - ys2.min() + 1)
    im = im.resize((max(1, int(im.width * s)), max(1, int(im.height * s))), Image.LANCZOS)
    out = Image.new("RGB", (cell, cell), "white")
    x = int(gcx - xs2.mean() * s); y = int(gy1 - ys2.max() * s)
    out.paste(im, (x, y), im)
    return out


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("layout"); ap.add_argument("--out", required=True)
    ap.add_argument("--cell", type=int, default=640)
    a = ap.parse_args(); c = a.cell
    rows = L[a.layout]
    W, H = 3 * c, 2 * c
    sheet = Image.new("RGB", (W, H), "white")
    meta = {"sheet": a.layout, "cell": c, "size": [W, H], "mirror_cells": True, "panels": []}
    for r, row in enumerate(rows):
        for k, p in enumerate(row):
            if p[0] == "ref":
                im = ref_panel(p[1], c); nm = "ref_" + p[1]; gd = None
            else:
                im = C.panel(p[1], "colour", True).resize((c, c), Image.LANCZOS); nm = p[2]; gd = f"{C.G}/{p[1]}"
            im = im.transpose(Image.FLIP_LEFT_RIGHT)
            sheet.paste(im, (k * c, r * c))
            meta["panels"].append({"name": nm, "guide": gd, "box": [k * c, r * c, (k + 1) * c, (r + 1) * c]})
    sheet.save(a.out)
    json.dump(meta, open(a.out.replace(".png", ".json"), "w"), indent=1)
    print(a.out, sheet.size)


if __name__ == "__main__":
    main()
