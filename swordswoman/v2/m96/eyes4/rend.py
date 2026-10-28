# rend.py OUT name1 name2 ... : S eye band crops (cols 52-76, rows 45-56) of /tmp/m96t/<name>/EC0_S_96.txt at 8x + 2x, stacked
import sys, numpy as np
sys.path.insert(0, '/Users/waylonhuang/Documents/other/pixelart/swordswoman/v2/pixelize/tools')
import pzlib as Z
from PIL import Image, ImageDraw
keys, rgb, _ = Z.load_pal('/Users/waylonhuang/Documents/other/pixelart/swordswoman/v2/pixelize/palette.json')
ims = []
for n in sys.argv[2:]:
    p = n if '/' in n else f'/tmp/m96t/{n}/EC0_S_96.txt'
    g = np.array([list(l.rstrip('\n')) for l in open(p) if l.strip() and not l.startswith(';')])
    im = Z.render(g[45:57, 52:77], keys, rgb); bg = Image.new('RGB', im.size, (200, 200, 200)); bg.paste(im, (0, 0), im)
    big = bg.resize((bg.width * 14, bg.height * 14), Image.NEAREST); sm = bg.resize((bg.width * 3, bg.height * 3), Image.NEAREST)
    c = Image.new('RGB', (big.width + sm.width + 30, big.height + 14), 'white'); c.paste(big, (0, 14)); c.paste(sm, (big.width + 20, 14)); ImageDraw.Draw(c).text((2, 1), n.split('/')[-1], fill='black'); ims.append(c)
cols = 2; W = ims[0].width; H = ims[0].height; rows = (len(ims) + cols - 1) // cols
O = Image.new('RGB', (W * cols, H * rows), 'white')
for i, im in enumerate(ims): O.paste(im, ((i % cols) * W, (i // cols) * H))
O.thumbnail((800, 800)); O.save(sys.argv[1]); print(O.size)
