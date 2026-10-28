"""sprgrid.py VIEW X0 Y0 X1 Y1 S OUT [MASTERDIR]: warped illustration crop in sprite coords with a sprite-pixel grid (S screen px per sprite px)"""
import sys, json, numpy as np
sys.path.insert(0, '/Users/waylonhuang/Documents/other/pixelart/swordswoman/v2/pixelize/tools'); import pzlib as Z
from PIL import Image, ImageDraw
v, x0, y0, x1, y1, s, out = sys.argv[1], *map(int, sys.argv[2:7]), sys.argv[7]
meta = json.load(open(f'/Users/waylonhuang/Documents/other/pixelart/swordswoman/v2/m96/masters/EC0_{v}_96.json'))
x, m = Z.load(v, meta['src']); Hh, Ww = m.shape
fx = lambda X: (X - meta['ox']) * Ww / meta['w']; fy = lambda Y: (Y - meta['oy']) * Hh / meta['h']
im = Image.fromarray(x.astype(np.uint8)).crop(tuple(int(round(t)) for t in (fx(x0), fy(y0), fx(x1), fy(y1)))).resize(((x1 - x0) * s, (y1 - y0) * s), Image.LANCZOS)
d = ImageDraw.Draw(im)
for X in range(x0, x1 + 1):
    d.line([((X - x0) * s, 0), ((X - x0) * s, im.height)], fill=(0, 140, 255) if X % 5 else (255, 0, 255), width=1)
    if X % 2 == 0: d.text(((X - x0) * s + 2, 1), str(X % 100), fill=(0, 0, 255))
for Y in range(y0, y1 + 1):
    d.line([(0, (Y - y0) * s), (im.width, (Y - y0) * s)], fill=(0, 140, 255) if Y % 5 else (255, 0, 255), width=1)
    d.text((1, (Y - y0) * s + 2), str(Y), fill=(0, 0, 255))
im.save(out); print(im.size)
