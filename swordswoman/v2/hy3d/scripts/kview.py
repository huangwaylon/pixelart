# kview.py OUT.png DIR... : row per dir: shade frames then matid frames, mid-grey bg
import sys, glob, os
from PIL import Image
out = sys.argv[1]; rows = []
for d in sys.argv[2:]:
    fs = sorted(glob.glob(f'{d}/f*_shade.png')); ims = [Image.open(f) for f in fs] + [Image.open(f.replace('shade', 'matid')) for f in fs]
    rows.append(ims)
W = max(len(r) for r in rows) * 384; s = Image.new('RGB', (W, 384 * len(rows)), (128, 128, 128))
for y, r in enumerate(rows):
    for x, i in enumerate(r): s.paste(i, (x * 384, y * 384), i)
s.thumbnail((2400, 2400)); s.save(out)
