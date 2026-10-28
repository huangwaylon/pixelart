"""r19: S4_hd vs Blender model B bake comparison boards -> 00_REVIEW/r19_blender_sprites/."""
import json
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, ROOT)
from pipeline.render import jaggy_count  # noqa: E402

OUT = os.path.join(ROOT, "00_REVIEW", "r19_blender_sprites")
DIRS = ["S", "SE", "E", "NE", "N", "NW", "W", "SW"]
BG = (196, 200, 206, 255)
SRC = [("S4_hd (current)", "out/variants/S4_hd__{clip}/{clip}_sheet.png"),
       ("Blender B, true proportions", "out/r19_blender/true_{clip}/true_{clip}_sheet.png"),
       ("Blender B, chibi retarget", "out/r19_blender/chibi_{clip}/chibi_{clip}_sheet.png")]


def frame(sheet, d, i):
    r = DIRS.index(d)
    return sheet.crop((i * 48, r * 64, i * 48 + 48, r * 64 + 64))


def sheets(clip):
    return [(n, Image.open(os.path.join(ROOT, p.format(clip=clip))).convert("RGBA")) for n, p in SRC
            if os.path.exists(os.path.join(ROOT, p.format(clip=clip)))]


def row(sheet, i=0, crop=None):
    im = Image.new("RGBA", (48 * 8 if crop is None else crop[2] * 8, 64 if crop is None else crop[3]), BG)
    for k, d in enumerate(DIRS):
        f = frame(sheet, d, i)
        if crop:
            f = f.crop((crop[0], crop[1], crop[0] + crop[2], crop[1] + crop[3]))
        im.alpha_composite(f, (k * f.width, 0))
    return im


def labelled(blocks, title):
    pad, lh = 8, 14
    w = max(b.width for _, b in blocks) + 2 * pad
    h = sum(b.height + lh + pad for _, b in blocks) + lh + pad
    im = Image.new("RGBA", (w, h), (236, 236, 236, 255))
    dr = ImageDraw.Draw(im)
    dr.text((pad, 2), title, fill=(20, 20, 20, 255))
    y = lh + pad
    for name, b in blocks:
        dr.text((pad, y), name, fill=(20, 20, 20, 255))
        im.paste(b, (pad, y + lh))
        y += b.height + lh + pad
    return im


def compare_idle():
    sh = sheets("idle")
    blocks = []
    for s in (1, 2, 8):
        for n, sht in sh:
            r = row(sht)
            blocks.append((f"{n}  {s}x   ({' '.join(DIRS)})", r.resize((r.width * s, r.height * s), Image.NEAREST)))
    labelled(blocks, "r19 idle frame 0: S4_hd vs Blender model B bake (48x64, same camera, palette and pixel pass)").save(
        os.path.join(OUT, "compare_idle_8dir.png"))


def faces():
    sh = sheets("idle")
    blocks = []
    for n, sht in sh:
        im = Image.new("RGBA", (4 * 32, 30), BG)
        for k, d in enumerate(["S", "SE", "E", "SW"]):
            im.alpha_composite(frame(sht, d, 0).crop((8, 16, 40, 46)), (k * 32, 0))
        blocks.append((f"{n}: S, SE, E, SW", im.resize((im.width * 8, im.height * 8), Image.NEAREST)))
    labelled(blocks, "r19 heads at 8x").save(os.path.join(OUT, "faces_8x.png"))


def walk_gif():
    sh = sheets("walk")
    if len(sh) < 2:
        return False
    imgs = []
    for i in range(8):
        blocks = [(n, row(s, i).resize((48 * 8 * 2, 128), Image.NEAREST)) for n, s in sh]
        imgs.append(labelled(blocks, f"r19 walk f{i}: S4_hd (8 frames, 100 ms) vs Blender B rig walk").convert("P",
                    palette=Image.ADAPTIVE, colors=64))
    imgs[0].save(os.path.join(OUT, "walk_8dir.gif"), save_all=True, append_images=imgs[1:], duration=100, loop=0,
                 disposal=2)
    return True


def metrics():
    out = {}
    for clip in ("idle", "walk"):
        for n, sht in sheets(clip):
            a = np.array(sht)
            js, cols, area = [], set(), []
            nf = sht.width // 48
            for d in DIRS:
                for i in range(nf):
                    f = np.array(frame(sht, d, i))
                    op = f[..., 3] > 0
                    js.append(jaggy_count(np.where(op, 0, -1)))
                    cols |= {tuple(c) for c in f[op][:, :3]}
                    area.append(int(op.sum()))
            out[f"{clip}: {n}"] = {"jaggies_per_frame": round(float(np.mean(js)), 1), "colours": len(cols),
                                   "opaque_px_per_frame": round(float(np.mean(area)), 1)}
    for m in ("true", "chibi"):
        p = os.path.join(ROOT, f"out/r19_blender/{m}_idle/{m}_idle_sheet.json")
        if os.path.exists(p):
            fs = json.load(open(p))["face_scale"]
            out[f"eye spacing px, {m} (S4_hd 5.3)"] = round(fs["S_0"] * 7.1 * 0.75, 2)
    with open(os.path.join(OUT, "metrics.json"), "w") as f:
        json.dump(out, f, indent=1)
    return out


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    compare_idle()
    faces()
    print("walk gif:", walk_gif())
    print(json.dumps(metrics(), indent=1))
