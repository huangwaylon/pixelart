"""view.py OUT.png img1.png img2.png ... [--z 5] [--crop x0,y0,x1,y1] [--bg grass|grey]  side-by-side zoomed view with
coordinate ticks every 8 px (for Claude's per-pixel review)."""
import sys
from PIL import Image, ImageDraw
a = sys.argv[1:]; z = 5; crop = (16, 24, 112, 112); bg = (84, 132, 66)
if '--z' in a: i = a.index('--z'); z = int(a[i + 1]); del a[i:i + 2]
if '--crop' in a: i = a.index('--crop'); crop = tuple(int(v) for v in a[i + 1].split(',')); del a[i:i + 2]
if '--bg' in a: i = a.index('--bg'); bg = (84, 132, 66) if a[i + 1] == 'grass' else (128, 128, 128); del a[i:i + 2]
out, ims = a[0], a[1:]
w, h = (crop[2] - crop[0]) * z, (crop[3] - crop[1]) * z
S = Image.new('RGB', (w * len(ims) + 4 * len(ims), h + 14), (20, 20, 28))
d = ImageDraw.Draw(S)
for k, p in enumerate(ims):
    im = Image.open(p).convert('RGBA').crop(crop)
    b = Image.new('RGBA', im.size, bg + (255,)); b.alpha_composite(im)
    X = k * (w + 4)
    S.paste(b.resize((w, h), Image.NEAREST), (X, 14))
    d.text((X + 2, 1), p.split('/')[-1][:40], fill=(255, 255, 0))
    for x in range(crop[0], crop[2], 8):
        d.line([(X + (x - crop[0]) * z, 14), (X + (x - crop[0]) * z, 18)], fill=(255, 255, 0))
        d.text((X + (x - crop[0]) * z + 1, 16), str(x), fill=(255, 255, 0))
    for y in range(crop[1], crop[3], 8):
        d.line([(X, 14 + (y - crop[1]) * z), (X + 4, 14 + (y - crop[1]) * z)], fill=(255, 255, 0))
        d.text((X + 5, 14 + (y - crop[1]) * z), str(y), fill=(255, 255, 0))
S.save(out)
