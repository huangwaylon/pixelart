"""Compose the lineup (x3, labelled) and the transparent sprite sheet from the rendered poses.
    python data/illustrations/S4/poses/_compose.py [--out 00_REVIEW/r12_illustration/poses] [--tmp]"""
import json, os, sys
from PIL import Image, ImageDraw
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
sys.path.insert(0, HERE)
from poses_def import POSES  # noqa
out = sys.argv[sys.argv.index("--out") + 1] if "--out" in sys.argv else "00_REVIEW/r12_illustration/poses"
out = os.path.join(ROOT, out)
names = [n for n in POSES]
ims = [Image.open(os.path.join(out, f"{n}_base.png")).convert("RGBA") for n in names]
W, H = ims[0].size
s = 3
bg = (223, 234, 246, 255)
sheet = Image.new("RGB", (len(ims) * (W * s + 6) + 6, H * s + 26), (36, 22, 40))
dr = ImageDraw.Draw(sheet)
for k, (n, im) in enumerate(zip(names, ims)):
    x = 6 + k * (W * s + 6)
    dr.text((x + 2, 6), n, fill=(244, 234, 210))
    b = Image.new("RGBA", im.size, bg); b.alpha_composite(im)
    g = b.convert("RGB").resize((W * s, H * s), Image.NEAREST)
    gd = ImageDraw.Draw(g)
    gd.line([(0, 153 * s + s), (W * s, 153 * s + s)], fill=(168, 192, 224))  # ground line
    sheet.paste(g, (x, 20))
sheet.save(os.path.join(out, "poses_lineup_x3.png"))
if "--tmp" not in sys.argv:
    eng = Image.new("RGBA", (W * len(ims), H), (0, 0, 0, 0))
    for k, im in enumerate(ims):
        eng.alpha_composite(im, (k * W, 0))
    eng.save(os.path.join(out, "poses_spritesheet.png"))
    json.dump({"image": "poses_spritesheet.png", "frameSize": [W, H], "frames": names,
               "rects": {n: [k * W, 0, W, H] for k, n in enumerate(names)}, "ground_y": 153,
               "palette": "cw_oatmeal_portrait", "source": "data/illustrations/S4/poses/<pose>.json"},
              open(os.path.join(out, "poses_spritesheet.json"), "w"), indent=1)
print("wrote", out)
