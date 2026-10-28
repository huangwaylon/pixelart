"""eyes3/crops.py OUT.png DIR [DIR..]: 8x eye-region crops of DIR/EC0_{S,SE,E}_96 masters side by side (rows = dirs)"""
import sys, os, numpy as np
sys.path.insert(0, '/Users/waylonhuang/Documents/other/pixelart/swordswoman/v2/pixelize/tools')
import pzlib as Z
from PIL import Image
keys, rgb, _ = Z.load_pal('/Users/waylonhuang/Documents/other/pixelart/swordswoman/v2/pixelize/palette.json')

BOX = {'S': (53, 45, 75, 57), 'SE': (59, 46, 80, 58), 'E': (67, 45, 82, 58)}; K = int(os.environ.get('K', 8))
if os.environ.get('V'): BOX = {k: BOX[k] for k in os.environ['V'].split(',')}
rows = []
for d in sys.argv[2:]:
    ims = []
    for v, (x0, y0, x1, y1) in BOX.items():
        g = np.array([list(l.rstrip('\n')) for l in open(f'{d}/EC0_{v}_96.txt') if l.strip() and not l.startswith(';')])
        im = Z.render(g[y0:y1, x0:x1], keys, rgb); bg = Image.new('RGB', im.size, (200, 200, 200)); bg.paste(im, (0, 0), im)
        ims.append(bg.resize((bg.width * K, bg.height * K), Image.NEAREST))
    rows.append(ims)
W = sum(i.width + 8 for i in rows[0]); H = sum(r[0].height + 8 for r in rows)
O = Image.new('RGB', (W, H), 'white'); y = 0
for r in rows:
    x = 0
    for i in r: O.paste(i, (x, y)); x += i.width + 8
    y += r[0].height + 8
O.thumbnail((800, 800)); O.save(sys.argv[1]); print(O.size)
