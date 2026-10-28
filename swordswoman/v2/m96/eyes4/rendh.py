# rendh.py OUT HEADS_DIR VIEW expr1,expr2,.. [scale] : eye band crops of head stamps (14x + 3x)
import sys, numpy as np
sys.path.insert(0, '/Users/waylonhuang/Documents/other/pixelart/swordswoman/v2/pixelize/tools')
import pzlib as Z
from PIL import Image, ImageDraw
keys, rgb, _ = Z.load_pal('/Users/waylonhuang/Documents/other/pixelart/swordswoman/v2/pixelize/palette.json')
out, hd, v, ex = sys.argv[1:5]; K = int(sys.argv[5]) if len(sys.argv) > 5 else 12
BOX = {'S': (52, 45, 77, 56), 'SE': (58, 46, 80, 57), 'E': (66, 45, 82, 56)}[v]
ims = []
for e in ex.split(','):
    L = [l.rstrip('\n') for l in open(f'{hd}/{v}_{e}.txt') if l.strip()]; ox, oy = map(int, L[0].split()[2:4])
    g = np.full((128, 128), '.', dtype='<U1')
    for j, r in enumerate([r for r in L if not r.startswith(';')]):
        for i, c in enumerate(r): g[oy + j, ox + i] = c
    x0, y0, x1, y1 = BOX; im = Z.render(g[y0:y1, x0:x1], keys, rgb); bg = Image.new('RGB', im.size, (200, 200, 200)); bg.paste(im, (0, 0), im)
    big = bg.resize((bg.width * K, bg.height * K), Image.NEAREST); sm = bg.resize((bg.width * 3, bg.height * 3), Image.NEAREST)
    c = Image.new('RGB', (big.width + sm.width + 16, big.height + 14), 'white'); c.paste(big, (0, 14)); c.paste(sm, (big.width + 8, 14)); ImageDraw.Draw(c).text((2, 1), e, fill='black'); ims.append(c)
cols = 2; W = ims[0].width; H = ims[0].height; rows = (len(ims) + cols - 1) // cols
O = Image.new('RGB', (W * cols, H * rows), 'white')
for i, im in enumerate(ims): O.paste(im, ((i % cols) * W, (i // cols) * H))
O.thumbnail((800, 800)); O.save(out); print(O.size)
