"""Key boards (8-dir native vs methods, 4x + 1x), walk strip, hi-res buffer board, 8-dir GIFs (native vs best).
  .venv/bin/python -B REVIEW/exp/2026-10-28_snowpeak_hires/scripts/keyboards.py [BEST]"""
import glob
import json
import os
import pickle
import sys

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hrlib as H  # noqa: E402
from analyze import palette_for, rgb, label_img, grid, title, crop_box  # noqa: E402

KEY = ["N", "VM", "KC", "PF", "KCE"]
BEST = sys.argv[1] if len(sys.argv) > 1 else "KC"


def main():
    B = os.path.join(H.EXP, "boards")
    runs = {}
    for p in sorted(glob.glob(os.path.join(H.EXP, "frames", "*.pkl"))):
        with open(p, "rb") as f:
            o = pickle.load(f)
        runs[(o["variant"], o["clip"], o["k"])] = o
    for v in ("S4_hd2", "S4_hd"):
        o = runs.get((v, "idle", 8))
        if not o:
            continue
        pal = palette_for(v)
        y0, y1, x0, x1 = crop_box(o, o["dirs"], o["frames"])
        for sc_ in (4, 1):
            cells = [label_img(rgb(pal, o["final"][m][d][0])[y0:y1, x0:x1], f"{m} {d}" if sc_ > 1 else m, sc_)
                     for m in KEY for d in o["dirs"]]
            t = (f"{v} idle f1, 8 dirs. rows: N native shipped | hi-res 8x -> VM vote mode-band | KC k-centroid | "
                 f"PF RD pixel-fixer | KCE k-centroid + normal/depth edge lines (all through the shipped FIX chain)"
                 if sc_ > 1 else f"{v} 1x  rows N VM KC PF KCE")
            title(grid(cells, len(o["dirs"])), t).save(f"{B}/00_key_{v}_idle_8dir_{sc_}x.png")
    for v in ("S4_hd2", "S4_hd"):
        o = runs.get((v, "walk", 8))
        if not o:
            continue
        pal = palette_for(v)
        y0, y1, x0, x1 = crop_box(o, ["SE"], o["frames"])
        cells = [label_img(rgb(pal, o["final"][m]["SE"][j])[y0:y1, x0:x1], f"{m} f{j + 1}", 4)
                 for m in ["N", "KC", "PF", "KCE"] for j in range(len(o["frames"]))]
        title(grid(cells, len(o["frames"])), f"{v} walk SE, 8 frames. rows: N native | KC | PF | KCE (hi-res 8x)").save(
            f"{B}/01_{v}_walk_SE_strip_4x.png")
    for v in ("S4_hd2", "S4_hd"):
        ims = []
        for d in ("S", "SE", "E"):
            for suf in ("a_smooth", "b_bands", "b_matid", "b_normal", "b_depth", "c_edges"):
                p = os.path.join(H.EXP, "big", f"{v}__idle__k8__{d}_f1_{suf}.png")
                if os.path.exists(p):
                    im = Image.open(p).convert("RGB").crop((96, 150, 288, 480))
                    can = Image.new("RGB", (im.width, im.height + 14), (40, 40, 44))
                    can.paste(im, (0, 14))
                    ImageDraw.Draw(can).text((2, 1), f"{d} {suf}", fill=(240, 240, 220))
                    ims.append(can)
        if ims:
            title(grid(ims, 6), f"{v} idle f1 at 8x sprite PPU: (a) smooth, (b) bands / material id / normal / depth, "
                                f"(c) edges: black depth break, red crease, blue material").save(f"{B}/02_{v}_hires_buffers.png")
    for v, clip in (("S4_hd2", "idle"), ("S4_hd2", "walk"), ("S4_hd2", "run"), ("S4_hd", "walk")):
        o = runs.get((v, clip, 8))
        if not o or len(o["dirs"]) < 8:
            continue
        pal = palette_for(v)
        with open(os.path.join(H.ROOT, "data", "animations", f"{clip}.json")) as f:
            ms_ = [fr["ms"] for fr in json.load(f)["frames"]]
        y0, y1, x0, x1 = crop_box(o, o["dirs"], o["frames"])
        fr = []
        for j in range(len(o["frames"])):
            rows = [np.concatenate([np.pad(rgb(pal, o["final"][m][d][j])[y0:y1, x0:x1], ((1, 1), (1, 1), (0, 0)),
                                           constant_values=60) for d in o["dirs"]], 1) for m in ("N", BEST)]
            a = np.concatenate(rows, 0)
            fr.append(Image.fromarray(a).resize((a.shape[1] * 3, a.shape[0] * 3), Image.NEAREST))
        fr[0].save(f"{B}/03_{v}_{clip}_8dir_top_native_bottom_{BEST}.gif", save_all=True, append_images=fr[1:],
                   duration=ms_[:len(fr)], loop=0)
    print("key boards written")


if __name__ == "__main__":
    main()
