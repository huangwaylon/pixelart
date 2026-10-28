"""packet.py VIEW X0 Y0 X1 Y1 OUTDIR [STEM]: artist packet: crop.txt (coords), ref_hi.png (illustration crop ~400px), ref_box.png
(illustration box-averaged to sprite grid, 12x, grid), cur.png (current sprite crop 12x, grid)"""
import sys, os, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import m96 as M, pzlib as Z
from PIL import Image, ImageDraw
v, x0, y0, x1, y1, od = sys.argv[1], *map(int, sys.argv[2:6]), sys.argv[6]
stem = sys.argv[7] if len(sys.argv) > 7 else M.ROOT + f'v2/m96/work/EC0_{v}_96'
os.makedirs(od, exist_ok=True)
g, meta = Z.read(stem); keys, rgb, _ = Z.load_pal(M.PAL)
with open(od + '/crop.txt', 'w') as f:
    for y in range(y0, y1): f.write(''.join(g[y, x0:x1]) + '\n')
x, b = M.illus_box(meta, x0, y0, x1, y1)
il = Image.fromarray(x.astype(np.uint8)).crop(tuple(int(round(t)) for t in b))
s = 400 / max(il.size); il.resize((round(il.width * s), round(il.height * s)), Image.LANCZOS).save(od + '/ref_hi.png')
lo = Z.resize(x, meta['w'], meta['h'], Image.BOX)
full = np.full((128, 128, 3), 200.0); full[meta['oy']:meta['oy'] + meta['h'], meta['ox']:meta['ox'] + meta['w']] = lo
def grid(img, S=12):
    im = img.resize((img.width * S, img.height * S), Image.NEAREST); d = ImageDraw.Draw(im)
    for i in range(0, img.width + 1, 5): d.line([(i * S, 0), (i * S, im.height)], fill=(0, 120, 255))
    for j in range(0, img.height + 1, 5): d.line([(0, j * S), (im.width, j * S)], fill=(0, 120, 255))
    return im
grid(Image.fromarray(full[y0:y1, x0:x1].astype(np.uint8))).save(od + '/ref_box.png')
cur = Z.render(g, keys, rgb).crop((x0, y0, x1, y1)); bg = Image.new('RGB', cur.size, (200, 200, 200)); bg.paste(cur, (0, 0), cur)
grid(bg).save(od + '/cur.png'); print(od, x1 - x0, y1 - y0)
