# usage: board.py out.png maxw title -- label=path[@crop x,y,w,h][*scale] ...
import sys
from PIL import Image, ImageDraw, ImageFont
out, maxw, title = sys.argv[1], int(sys.argv[2]), sys.argv[3]
items = sys.argv[5:]
BG = (128,128,128)
font = ImageFont.load_default()
tiles = []
for it in items:
    lab, spec = it.split('=', 1)
    sc = 0
    if '*' in spec: spec, sc = spec.rsplit('*', 1); sc = int(sc)
    crop = None
    if '@' in spec: spec, c = spec.split('@'); crop = tuple(map(int, c.split(',')))
    src = Image.open(spec)
    im = src.convert('RGBA')
    if src.mode == 'P' and 'transparency' not in src.info:
        import numpy as np
        a = np.array(im); a[np.array(src) == 0, 3] = 0; im = Image.fromarray(a)
    if crop: x,y,w,h = crop; im = im.crop((x,y,x+w,y+h))
    if not sc: sc = max(1, min(4, 160 // max(im.size)))
    im = im.resize((im.width*sc, im.height*sc), Image.NEAREST)
    t = Image.new('RGB', (im.width+8, im.height+22), BG)
    t.paste(im, (4,4), im)
    d = ImageDraw.Draw(t); d.text((4, im.height+8), f"{lab} x{sc}", fill=(255,255,255), font=font)
    tiles.append(t)
rows, row, w = [], [], 0
for t in tiles:
    if row and w + t.width > maxw: rows.append(row); row, w = [], 0
    row.append(t); w += t.width
if row: rows.append(row)
H = 20 + sum(max(t.height for t in r) for r in rows)
W = min(maxw, max(sum(t.width for t in r) for r in rows))
B = Image.new('RGB', (W, H), BG); d = ImageDraw.Draw(B); d.text((4,4), title, fill=(255,255,0), font=font)
y = 20
for r in rows:
    x = 0
    for t in r: B.paste(t, (x, y)); x += t.width
    y += max(t.height for t in r)
B.save(out)
th = out.replace('.png', '_thumb.png')
if B.width > 1000 or B.height > 1000:
    s = min(1000/B.width, 1000/B.height); B.resize((int(B.width*s), int(B.height*s)), Image.LANCZOS).save(th)
print(out, B.size)
