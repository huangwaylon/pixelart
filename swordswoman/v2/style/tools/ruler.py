# ruler.py out.png scale label=path[@x,y,w,h][/2] ...  : sprites cropped to bbox, enlarged, with row numbers (from figure top) every 5 rows and faint grid
import sys
from PIL import Image, ImageDraw, ImageFont
import numpy as np
out, s = sys.argv[1], int(sys.argv[2]); F = ImageFont.load_default()
tiles = []
for it in sys.argv[3:]:
    lab, spec = it.split('=', 1); half = spec.endswith('/2')
    if half: spec = spec[:-2]
    crop = None
    if '@' in spec: spec, c = spec.split('@'); crop = tuple(map(int, c.split(',')))
    src = Image.open(spec); im = src.convert('RGBA')
    if src.mode == 'P' and 'transparency' not in src.info:
        a = np.array(im); a[np.array(src) == 0, 3] = 0; im = Image.fromarray(a)
    if crop: x, y, w, h = crop; im = im.crop((x, y, x + w, y + h))
    if half: im = im.resize((im.width // 2, im.height // 2), Image.NEAREST)
    a = np.array(im)[..., 3] > 0; ys, xs = np.where(a); im = im.crop((xs.min(), ys.min(), xs.max() + 1, ys.max() + 1))
    W, H = im.size; t = Image.new('RGB', (W * s + 40, H * s + 30), (128, 128, 128)); big = im.resize((W * s, H * s), Image.NEAREST)
    t.paste(big, (30, 20), big); d = ImageDraw.Draw(t)
    for r in range(0, H + 1):
        y = 20 + r * s
        if r % 5 == 0:
            d.line([(24, y), (30 + W * s, y)], fill=(255, 255, 0) if r % 10 == 0 else (200, 200, 120)); d.text((2, y - 5), str(r), fill=(255, 255, 0), font=F)
    for c in range(0, W + 1, 5):
        d.line([(30 + c * s, 14), (30 + c * s, 20)], fill=(0, 255, 255)); d.text((30 + c * s - 3, 2), str(c) if c % 10 == 0 else '', fill=(0, 255, 255), font=F)
    d.text((30, H * s + 20), f"{lab} {W}x{H}", fill=(255, 255, 255), font=F); tiles.append(t)
Wt = sum(t.width for t in tiles); Ht = max(t.height for t in tiles)
B = Image.new('RGB', (Wt, Ht), (128, 128, 128)); x = 0
for t in tiles: B.paste(t, (x, 0)); x += t.width
B.save(out); print(out, B.size)
