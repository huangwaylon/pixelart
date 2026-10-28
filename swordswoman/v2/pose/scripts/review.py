# review.py OUTROOT ACT_VIEW[,..] OUT.png [scale=2]: rows of matid frames at `scale` (for my own quick look, <=1000 px)
import sys, os, json, numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import metrics as MX
root, ids, outp = sys.argv[1], sys.argv[2].split(","), sys.argv[3]; s = int(sys.argv[4]) if len(sys.argv) > 4 else 2
rows = []
for jid in ids:
    d = os.path.join(root, jid); fs = sorted(f for f in os.listdir(d) if f.endswith("_matid4x.png"))
    ims = []
    for f in fs:
        a = np.asarray(Image.open(os.path.join(d, f)).convert("RGBA"))[16*4:80*4, 16*4:80*4]
        k = 4; im = Image.fromarray(a).resize((64 * s, 64 * s), Image.NEAREST)
        bg = Image.new("RGBA", im.size, MX.BG + (255,)); bg.alpha_composite(im); ims.append(bg.convert("RGB"))
    rows.append((jid, ims))
W = max(len(r[1]) for r in rows) * 64 * s + 10; H = len(rows) * (64 * s + 2)
O = Image.new("RGB", (W, H), (50, 50, 50)); dr = ImageDraw.Draw(O)
for r, (jid, ims) in enumerate(rows):
    for i, im in enumerate(ims): O.paste(im, (i * 64 * s, r * (64 * s + 2)))
    dr.text((2, r * (64 * s + 2) + 2), jid, fill=(255, 255, 0))
O.save(outp); print(O.size)
