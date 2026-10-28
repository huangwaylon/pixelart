# ksheet.py KEYS_ROOT ACTION [dirs] -> KEYS_ROOT/sheet_<action>.png : per dir rows = toon shade | flat matid | 1x box-downsample (x4 nearest); key names on top
import sys, json, os
from PIL import Image, ImageDraw
root, act = sys.argv[1:3]; dirs = (sys.argv[3] if len(sys.argv) > 3 else "SE,E").split(",")
G = (128, 128, 128); C = 384; rows = []
for dn in dirs:
    d = f"{root}/{act}_{dn}"; kj = json.load(open(f"{d}/keys.json")); n = len(kj["keys"])
    for mode in ("shade", "matid", "px"):
        r = Image.new("RGB", (C * n + 90, C), G); dr = ImageDraw.Draw(r); dr.text((6, C // 2), f"{dn}\n{mode}", fill=(255, 255, 255))
        for i, kn in enumerate(kj["keys"]):
            im = Image.open(f"{d}/f{i:02d}_{'matid' if mode == 'matid' else 'shade'}.png").convert("RGBA")
            if mode == "px": im = im.resize((96, 96), Image.BOX).resize((C, C), Image.NEAREST)
            r.paste(im, (90 + i * C, 0), im); dr.text((96 + i * C, 6), kn, fill=(255, 255, 255))
        rows.append(r)
W = max(r.width for r in rows); s = Image.new("RGB", (W, C * len(rows)), G)
for i, r in enumerate(rows): s.paste(r, (0, i * C))
s.save(f"{root}/sheet_{act}.png"); print(f"{root}/sheet_{act}.png", s.size)
