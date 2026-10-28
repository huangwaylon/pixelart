#!/usr/bin/env python3
"""S2 gridsheet: compose multi-panel GUIDE sheets from hybrid/guide/p2 renders (guide only, never art).

Each panel = colour-coded clay (id pass -> flat costume colour x clay shading) + line pass, cropped
from the 1024 px (8x cell) render with ONE fixed window, so every panel shares scale and pivot.

  compose.py SHEET --out out.png [--mirror] [--cell 512] [--style colour|clay] [--smear]
SHEETS: turn (4x2: S SE E NE / N NW W SW), actions (4x3: walk k0-3 / slash k0-3 / E idle, crouch, apex, land)
Writes out.png and out.json (panel boxes in sheet px + source prefixes) for slicing.
"""
import argparse, json, sys
import numpy as np
from PIL import Image

G = "hybrid/guide/p2"
WIN = (256, 336, 896, 976)          # x0,y0,x1,y1 in the 1024 render (pivot 512,832)
COL = {  # id -> rgb (costume truth, a little lighter than palette so the shading reads)
    1: (84, 52, 48), 2: (84, 52, 48), 3: (216, 52, 62), 4: (253, 220, 200), 5: (253, 220, 200),
    6: (200, 40, 56), 7: (210, 48, 60), 8: (90, 58, 40), 9: (216, 52, 62), 10: (150, 30, 60),
    11: (40, 34, 48), 12: (216, 52, 62), 13: (216, 52, 62), 14: (250, 214, 196), 15: (250, 214, 196),
    16: (250, 214, 196), 17: (250, 214, 196), 18: (250, 214, 196), 19: (250, 214, 196),
    20: (30, 26, 36), 21: (30, 26, 36), 22: (248, 181, 200), 23: (248, 181, 200), 24: (200, 206, 220),
    25: (238, 240, 245),
}
SHEETS = {
    "turn": [[f"turn/{d}/f00" for d in ("S", "SE", "E", "NE")],
             [f"turn/{d}/f00" for d in ("N", "NW", "W", "SW")]],
    "actions": [[f"walk_SE_keys/SE/f0{i}" for i in range(4)],
                [f"slash_SE_keys/SE/f0{i}" for i in range(4)],
                ["turn/E/f00"] + [f"jump_E_keys/E/f0{i}" for i in range(3)]],
    "walk": [[f"walk_SE_keys/SE/f0{i}" for i in range(4)]],
    "slash": [[f"slash_SE_keys/SE/f0{i}" for i in range(4)]],
    "jump": [["turn/E/f00"] + [f"jump_E_keys/E/f0{i}" for i in range(3)]],
    "walk22": [["walk_SE_keys/SE/f00", "walk_SE_keys/SE/f01"], ["walk_SE_keys/SE/f02", "walk_SE_keys/SE/f03"]],
    "slash22": [["slash_SE_keys/SE/f00", "slash_SE_keys/SE/f01"], ["slash_SE_keys/SE/f02", "slash_SE_keys/SE/f03"]],
    "jump22": [["turn/E/f00", "jump_E_keys/E/f00"], ["jump_E_keys/E/f01", "jump_E_keys/E/f02"]],
}
NAMES = {
    "turn": [["turn_S", "turn_SE", "turn_E", "turn_NE"], ["turn_N", "turn_NW", "turn_W", "turn_SW"]],
    "actions": [[f"walk_SE_k{i}" for i in range(4)], [f"slash_SE_k{i}" for i in range(4)],
                ["ref_turn_E", "jump_E_crouch", "jump_E_apex", "jump_E_land"]],
    "walk": [[f"walk_SE_k{i}" for i in range(4)]],
    "slash": [[f"slash_SE_k{i}" for i in range(4)]],
    "jump": [["ref_turn_E", "jump_E_crouch", "jump_E_apex", "jump_E_land"]],
    "walk22": [["walk_SE_k0", "walk_SE_k1"], ["walk_SE_k2", "walk_SE_k3"]],
    "slash22": [["slash_SE_k0", "slash_SE_k1"], ["slash_SE_k2", "slash_SE_k3"]],
    "jump22": [["ref_turn_E", "jump_E_crouch"], ["jump_E_apex", "jump_E_land"]],
}


def panel(prefix, style, smear):
    p = f"{G}/{prefix}"
    clay = np.asarray(Image.open(p + "_clay.png").convert("RGBA")).astype(float)
    a = clay[..., 3:4] / 255
    if style == "colour":
        ids = np.asarray(Image.open(p + "_id.png").convert("RGBA"))[..., 0] // 10
        lum = clay[..., :3].mean(-1, keepdims=True) / 255
        shade = np.clip(0.45 + 0.85 * lum, 0, 1.15)
        base = np.zeros(clay.shape[:2] + (3,))
        for k, c in COL.items():
            base[ids == k] = c
        rgb = np.clip(base * shade, 0, 255)
    else:
        rgb = clay[..., :3]
    out = rgb * a + 255 * (1 - a)
    try:
        ln = np.asarray(Image.open(p + "_line.png").convert("RGBA")).astype(float)[..., 3:4] / 255
        out = out * (1 - ln) + np.array([40, 26, 30]) * ln
    except FileNotFoundError:
        pass
    if smear:
        try:
            sm = np.asarray(Image.open(p + "_mask_smear.png").convert("L")).astype(float)[..., None] / 255
            sm = sm * (1 - a)
            out = out * (1 - sm) + np.array([248, 190, 210]) * sm
        except FileNotFoundError:
            pass
    im = Image.fromarray(out.astype(np.uint8))
    return im.crop(WIN)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("sheet"); ap.add_argument("--out", required=True)
    ap.add_argument("--mirror", action="store_true"); ap.add_argument("--cell", type=int, default=512)
    ap.add_argument("--style", default="colour"); ap.add_argument("--smear", action="store_true")
    ap.add_argument("--gap", type=int, default=0)
    ap.add_argument("--mirror-cells", action="store_true", help="flip each panel in place (keeps reading order)")
    a = ap.parse_args()
    rows = SHEETS[a.sheet]; c = a.cell; gap = a.gap
    ncol = max(len(r) for r in rows)
    W, H = ncol * c + (ncol - 1) * gap, len(rows) * c + (len(rows) - 1) * gap
    sheet = Image.new("RGB", (W, H), "white")
    meta = {"sheet": a.sheet, "cell": c, "gap": gap, "size": [W, H], "win": WIN, "mirror": a.mirror, "mirror_cells": a.mirror_cells, "panels": []}
    for r, row in enumerate(rows):
        for k, pre in enumerate(row):
            im = panel(pre, a.style, a.smear).resize((c, c), Image.LANCZOS)
            if a.mirror_cells:
                im = im.transpose(Image.FLIP_LEFT_RIGHT)
            x, y = k * (c + gap), r * (c + gap)
            sheet.paste(im, (x, y))
            meta["panels"].append({"name": NAMES[a.sheet][r][k], "guide": f"{G}/{pre}", "box": [x, y, x + c, y + c]})
    if a.mirror:
        sheet = sheet.transpose(Image.FLIP_LEFT_RIGHT)
    sheet.save(a.out)
    json.dump(meta, open(a.out.replace(".png", ".json"), "w"), indent=1)
    print(a.out, sheet.size)


if __name__ == "__main__":
    main()
