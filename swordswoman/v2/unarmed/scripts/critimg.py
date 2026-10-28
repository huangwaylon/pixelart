# critimg.py ROOT ACT OUT : rows S/SE/E (figure crop, 160 px cells) + a true-1x row (SE, 96 cell -> shown x2 nearest)
import sys, glob
from PIL import Image
root, act, out = sys.argv[1:4]; V = ["S", "SE", "E"]
rows = {v: sorted(glob.glob(f"{root}/{act}_{v}/s48/f*_shade.png")) for v in V}; n = len(rows["SE"])
CW, CH = 160, 180; M = Image.new("RGB", (CW * n, CH * 3 + 192), (110, 110, 110))
for i, v in enumerate(V):
    for j, p in enumerate(rows[v]):
        im = Image.open(p).convert("RGBA").crop((64, 64, 320, 352)).resize((CW, CH), Image.LANCZOS); M.paste(im, (j * CW, i * CH), im)
for j, p in enumerate(rows["SE"]):
    im = Image.open(p).convert("RGBA").resize((96, 96), Image.NEAREST).resize((192, 192), Image.NEAREST); M.paste(im, (j * CW - 16, CH * 3), im)
M.save(out); print(out, M.size)
