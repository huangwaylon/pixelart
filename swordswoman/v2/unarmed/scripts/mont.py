# mont.py ROOT VIEW OUT [acts] : montage rows of f*_shade.png (one row per action), cell 96 px (downscaled from 384)
import sys, os, glob
from PIL import Image
root, view, out = sys.argv[1:4]; acts = (sys.argv[4] if len(sys.argv) > 4 else "idle,walk,run,jump,dash,hurt").split(",")
rows = [sorted(glob.glob(f"{root}/{a}_{view}/s48/f*_shade.png")) for a in acts]
C = 96; W = C * max(len(r) for r in rows); M = Image.new("RGB", (W, C * len(rows)), (110, 110, 110))
for i, r in enumerate(rows):
    for j, p in enumerate(r):
        im = Image.open(p).convert("RGBA"); s = im.size[0]; im = im.resize((C, C), Image.NEAREST); M.paste(im, (j * C, i * C), im)
M.save(out); print(out, M.size)
