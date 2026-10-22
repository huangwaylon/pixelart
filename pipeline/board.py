"""Comparison boards: several variants side by side, synced, as an animated GIF + a static PNG.

    python -m pipeline.board --title "Proportions" --out out/boards/proportions \
        --variants A_chibi B_pokemon C_semichibi --dirs S SE E N
Each cell is upscaled by an integer factor so different resolutions display at a similar size.
"""
import argparse
import json
import os

import numpy as np
from PIL import Image, ImageDraw

from .palette import Palette
from . import export as ex

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BG = (36, 22, 40)
TXT = (244, 234, 210)
SUB = (168, 192, 224)


def load_variant_build(name):
    d = os.path.join(ROOT, "out", "variants", name)
    sheet_json = [f for f in os.listdir(d) if f.endswith("_sheet.json")][0]
    meta = json.load(open(os.path.join(d, sheet_json)))
    inputs = os.path.join(d, "inputs", "data", "palettes")
    pal_file = [f for f in os.listdir(inputs) if f.endswith(".json")][0]
    pal = Palette(os.path.join(inputs, pal_file))
    char = json.load(open(os.path.join(d, "inputs", "character_generated.json")))

    def cells(png, rows):
        idx = pal.from_rgba(np.array(Image.open(os.path.join(d, png)).convert("RGBA")))
        W, H = meta["frameSize"]
        return [[idx[r * H:(r + 1) * H, c * W:(c + 1) * W] for c in range(idx.shape[1] // W)] for r in range(rows)]

    sheet = cells(meta["image"], len(meta["directions"]))
    shadow = cells(meta["layers"]["shadow"], 1)[0]
    fxb = cells(meta["layers"]["fxBack"], 1)[0]
    fxf = cells(meta["layers"]["fxFront"], 1)[0]
    return {"name": name, "label": char.get("label", name), "meta": meta, "pal": pal, "sheet": sheet,
            "shadow": shadow, "fxb": fxb, "fxf": fxf, "ppu": char.get("render", {}).get("ppu", 1.0)}


def baked(v, d, i):
    W, H = v["meta"]["frameSize"]
    head = int(round(24 * v["ppu"]))
    r = v["meta"]["directions"].index(d)
    z = v["meta"]["frames"][i]["z_px"]
    idx = ex.baked_frame(v["sheet"][r][i], v["shadow"][i], v["fxb"][i], v["fxf"][i], z, v["pal"],
                         (W, H), tuple(v["meta"]["pivot"]), H + head)
    return Image.fromarray(v["pal"].to_rgba(idx)).convert("RGB")


def make_board(title, names, dirs, out, cell_h=300, notes=None):
    vs = [load_variant_build(n) for n in names]
    n = len(vs[0]["meta"]["frames"])
    durations = [f["duration_ms"] for f in vs[0]["meta"]["frames"]]
    # integer upscale per variant so displayed heights are close to cell_h
    # uniform integer scale (same px size for every variant) unless resolutions differ a lot
    hhs = [v["meta"]["frameSize"][1] + int(round(24 * v["ppu"])) for v in vs]
    uniform = max(1, cell_h // max(hhs))
    mixed = max(v["ppu"] for v in vs) / min(v["ppu"] for v in vs) > 1.2
    scales, sizes = [], []
    for v, hh in zip(vs, hhs):
        W, H = v["meta"]["frameSize"]
        s = max(1, cell_h // hh) if mixed else uniform
        scales.append(s)
        sizes.append((W * s, hh * s))
    col_w = max(w for w, _ in sizes) + 16
    row_h = max(h for _, h in sizes) + 8
    top, left = 62, 34
    Wb, Hb = left + col_w * len(vs), top + row_h * len(dirs) + (18 if notes else 0)
    frames = []
    for i in range(n):
        img = Image.new("RGB", (Wb, Hb), BG)
        dr = ImageDraw.Draw(img)
        dr.fontmode = "1"   # no antialiasing -> exact palette GIF
        dr.text((10, 8), title.replace("·", "-").replace("é", "e").replace("—", "-"), fill=TXT)
        dr.text((10, 22), f"frame {i + 1}/{n}  {vs[0]['meta']['frames'][i]['name']}", fill=SUB)
        for c, v in enumerate(vs):
            W, H = v["meta"]["frameSize"]
            label = v["label"].replace("·", "-").replace("é", "e").replace("—", "-")
            maxc = max(8, (col_w - 8) // 6)
            dr.text((left + c * col_w + 6, 30), label[:maxc], fill=TXT)
            if len(label) > maxc:
                dr.text((left + c * col_w + 6, 40), label[maxc:2 * maxc], fill=SUB)
            dr.text((left + c * col_w + 6, 51), f"{W}x{H} cell - x{scales[c]}", fill=SUB)
            for r, d in enumerate(dirs):
                cell = baked(v, d, i)
                cell = cell.resize((cell.width * scales[c], cell.height * scales[c]), Image.NEAREST)
                x = left + c * col_w + (col_w - cell.width) // 2
                y = top + r * row_h + (row_h - cell.height) // 2
                img.paste(cell, (x, y))
        for r, d in enumerate(dirs):
            dr.text((8, top + r * row_h + row_h // 2 - 6), d, fill=TXT)
        if notes:
            dr.text((10, Hb - 16), notes, fill=SUB)
        frames.append(img)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    # exact colours: global palette = union of all frame colours (well under 256)
    colors = set()
    for f in frames:
        colors |= {c for _, c in f.getcolors(1 << 20)}
    colors = sorted(colors)
    if len(colors) > 256:
        raise ValueError(f"board uses {len(colors)} colours")
    flat = [v for c in colors for v in c] + [0] * (3 * (256 - len(colors)))
    pimg = Image.new("P", (1, 1))
    pimg.putpalette(flat)
    ps = [f.quantize(palette=pimg, dither=Image.Dither.NONE) for f in frames]
    ps[0].save(out + ".gif", save_all=True, append_images=ps[1:], duration=durations, loop=0, disposal=1)
    slow = [t * 3 for t in durations]
    ps[0].save(out + "_slow.gif", save_all=True, append_images=ps[1:], duration=slow, loop=0, disposal=1)
    # static: ready + apex + land frames stacked
    # key frames chosen from metadata (works for any animation): last ground frame before takeoff,
    # apex (max z), landing contact, final frame
    fr = vs[0]["meta"]["frames"]
    zs = [f["z_px"] for f in fr]
    first_air = next((i for i, z in enumerate(zs) if z > 0), 0)
    land = next((i for i, f in enumerate(fr) if "land" in f.get("events", [])), len(fr) - 1)
    keep_idx = sorted({max(first_air - 1, 0), int(np.argmax(zs)), land, len(fr) - 1})
    st = Image.new("RGB", (Wb, Hb * len(keep_idx)), BG)
    for k, i in enumerate(keep_idx):
        st.paste(frames[i], (0, k * Hb))
    st.save(out + "_keys.png")
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--title", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--variants", nargs="+", required=True)
    ap.add_argument("--dirs", nargs="+", default=["S", "SE", "E", "NE", "N"])
    ap.add_argument("--cell-h", type=int, default=300)
    ap.add_argument("--notes")
    a = ap.parse_args()
    out = make_board(a.title, a.variants, a.dirs, os.path.join(ROOT, a.out), a.cell_h, a.notes)
    print("board:", out + ".gif")


if __name__ == "__main__":
    main()
