"""ruler.py out.png h img... : crop each figure, scale to height h, draw ruler lines every 5% of figure height (label = percent from top)."""
import sys, numpy as np
from PIL import Image, ImageDraw
out, h, fs = sys.argv[1], int(sys.argv[2]), sys.argv[3:]
tiles = []
for p in fs:
    im = Image.open(p).convert('RGB'); x = np.array(im).astype(int)
    m = (x.min(-1) < 215) | (x.max(-1) - x.min(-1) > 30); ys, xs = np.where(m)
    im = im.crop((xs.min() - 5, ys.min(), xs.max() + 5, ys.max() + 1)); im = im.resize((round(im.width * h / im.height), h), Image.LANCZOS)
    t = Image.new('RGB', (im.width + 30, h + 20), 'white'); t.paste(im, (30, 10)); d = ImageDraw.Draw(t)
    for k in range(0, 101, 5):
        y = 10 + round(k / 100 * (h - 1)); d.line([(22, y), (t.width, y)], fill=(255, 0, 0) if k % 10 == 0 else (255, 180, 180))
        if k % 10 == 0: d.text((0, y - 6), str(k), fill='red')
    d.text((32, 0), p.split('/')[-1][:-4], fill='blue'); tiles.append(t)
W = sum(t.width for t in tiles); o = Image.new('RGB', (W, h + 20), 'white'); x = 0
for t in tiles: o.paste(t, (x, 0)); x += t.width
o.save(out); print(o.size)
