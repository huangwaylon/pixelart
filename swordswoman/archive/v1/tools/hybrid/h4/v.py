"""quick zoom view: v.py OUT.png a.png b.png ... [--z 6] [--crop x0,y0,x1,y1] : row of zoomed crops + 1x/2x on grass/dirt"""
import sys
import numpy as np
from PIL import Image, ImageDraw
args = sys.argv[1:]
z = int(args[args.index('--z') + 1]) if '--z' in args else 6
crop = tuple(int(v) for v in args[args.index('--crop') + 1].split(',')) if '--crop' in args else (28, 34, 102, 108)
fs = [a for i, a in enumerate(args[1:]) if a.endswith('.png') and (i == 0 or args[i] not in ('--z', '--crop'))]
out = args[0]
x0, y0, x1, y1 = crop; W, H = x1 - x0, y1 - y0
ims = [Image.open(f).convert('RGBA').crop(crop) for f in fs]
tile = Image.new('RGB', (len(ims) * (W * z + 8) + 8, H * z + 16 + H * 2 + 8), (36, 32, 44))
d = ImageDraw.Draw(tile)
for i, im in enumerate(ims):
    bg = Image.new('RGBA', (W * z, H * z), (118, 118, 126, 255))
    big = im.resize((W * z, H * z), Image.NEAREST)
    bg.alpha_composite(big)
    X = 8 + i * (W * z + 8)
    tile.paste(bg.convert('RGB'), (X, 16))
    d.text((X, 2), fs[i].split('/')[-1][:-4], fill=(230, 230, 230))
    for k, col in enumerate([(72, 128, 60), (120, 92, 62)]):
        g = Image.new('RGBA', (W * 2 // 2, H), col + (255,)); g.alpha_composite(im)
        g2 = Image.new('RGBA', (W * 2, H * 2), col + (255,)); g2.alpha_composite(im.resize((W * 2, H * 2), Image.NEAREST))
        tile.paste(g.convert('RGB'), (X + k * (W + 4), 16 + H * z + 4))
        if k == 0: tile.paste(g2.convert('RGB'), (X + 2 * (W + 4), 16 + H * z + 4)) if X + 2 * (W + 4) + 2 * W < tile.width else None
tile.save(out)
