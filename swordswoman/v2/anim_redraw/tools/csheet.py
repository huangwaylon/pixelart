#!/usr/bin/env python3
"""csheet.py OUT S img1 img2 ... [--cols N] : grey-bg nearest-upscaled contact sheet (crop to 128 cell's middle)"""
import sys
from PIL import Image
args = sys.argv[1:]; cols = 8
if '--cols' in args:
    i = args.index('--cols'); cols = int(args[i + 1]); del args[i:i + 2]
out, s, ims = args[0], int(args[1]), args[2:]
cr = (24, 24, 104, 128)
w, h = (cr[2] - cr[0]) * s, (cr[3] - cr[1]) * s
rows = (len(ims) + cols - 1) // cols
sh = Image.new('RGB', (cols * (w + 2), rows * (h + 2)), (40, 40, 40))
for k, p in enumerate(ims):
    im = Image.open(p).convert('RGBA').crop(cr)
    bg = Image.new('RGBA', im.size, (110, 110, 110, 255)); bg.alpha_composite(im)
    sh.paste(bg.convert('RGB').resize((w, h), Image.NEAREST), ((k % cols) * (w + 2), (k // cols) * (h + 2)))
sh.save(out); print(out, sh.size)
