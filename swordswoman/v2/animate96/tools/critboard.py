#!/usr/bin/env python3
"""critboard.py CLIPDIR OUT.png : master | frames (3x, cropped, grey) + the same row at 1x below (critique board, <=1536 px)."""
import sys, os, json, numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import post96 as P
cd, outp = sys.argv[1], sys.argv[2]
fj, fr = P.load(cd, 'c'); _, RGB = P.rgbmap(fj); V = fj['dir']
M = P.LS.read('%s/m96/masters/EC0_%s_96.txt' % (P.V2, V))[0]
ims = [P.rgba(M, RGB)] + [P.rgba(g, RGB) for g, _ in fr]
al = np.any([np.array(i)[..., 3] > 0 for i in ims], 0); ys, xs = np.nonzero(al)
box = (xs.min() - 2, ys.min() - 2, xs.max() + 3, ys.max() + 3); w, h = box[2] - box[0], box[3] - box[1]
s = max(1, min(4, 1500 // (len(ims) * w))); W = len(ims) * w * s
B = Image.new('RGB', (W, h * s + h + 30), P.BG); d = ImageDraw.Draw(B)
for k, im in enumerate(ims):
    c = im.crop(box); B.paste(c.resize((w * s, h * s), Image.NEAREST), (k * w * s, 14), c.resize((w * s, h * s), Image.NEAREST))
    B.paste(c, (k * w * s + w * s // 2 - w // 2, h * s + 24), c)
    d.text((k * w * s + 2, 1), 'MASTER' if k == 0 else 'f%02d %s %s' % (k - 1, fj['frames'][k - 1]['key'], fj['frames'][k - 1]['ms']), fill=(255, 255, 255))
B.save(outp); print(outp, B.size)
