# cmp2d.py KEYS_ROOT ANIM_SHEETS OUT.png : per action two rows -> anim_redraw 2D frame (cell from sheets/<act>_SE.png) | 3D key SE shade | 3D key SE matid
import sys, json
from PIL import Image, ImageDraw
root, sh, out = sys.argv[1:4]
MAP = {"run": [0, 2, 3], "jump": [0, 1, 2, 4, 6], "dash": [0, 1, 3], "slash": [1, 3, 4]}
G = (128, 128, 128); C = 220; H = 250; CH = {"jump": 241}; rows = []
for a, idx in MAP.items():
    src = Image.open(f"{sh}/{a}_SE.png").convert("RGB"); cw = 194; ch = CH.get(a, 194)
    ks = json.load(open(f"{root}/{a}_SE/keys.json"))["keys"]
    for mode in ("2d", "shade", "matid"):
        r = Image.new("RGB", (100 + C * 5, H), G); d = ImageDraw.Draw(r); d.text((4, C // 2), f"{a}\n{'anim_redraw' if mode == '2d' else '3D ' + mode}", fill="white")
        for i, (k, fi) in enumerate(zip(ks, idx)):
            if mode == "2d":
                im = src.crop(((fi % 4) * cw, (fi // 4) * ch, (fi % 4 + 1) * cw - 2, (fi // 4 + 1) * ch - 2)); im = im.resize((C, round(C * im.height / im.width)), Image.NEAREST); im = im.crop((0, im.height - H, C, im.height)) if im.height > H else im; r.paste(im, (100 + i * C, 0)); d.text((104 + i * C, 4), f"2D f{fi}", fill="white")
            else:
                im = Image.open(f"{root}/{a}_SE/f{i:02d}_{mode}.png").convert("RGBA").crop((32, 40, 352, 384)).resize((C, H), Image.LANCZOS); r.paste(im, (100 + i * C, 0), im); d.text((104 + i * C, 4), k, fill="white")
        rows.append(r)
s = Image.new("RGB", (100 + C * 5, H * len(rows)), G)
for i, r in enumerate(rows): s.paste(r, (0, i * H))
s.save(out); print(out, s.size)
