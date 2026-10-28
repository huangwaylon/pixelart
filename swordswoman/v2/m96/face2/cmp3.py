import sys, json, numpy as np
sys.path.insert(0, '/Users/waylonhuang/Documents/other/pixelart/swordswoman/v2/pixelize/tools'); sys.path.insert(0, '/Users/waylonhuang/Documents/other/pixelart/swordswoman/v2/m96/tools')
import pzlib as Z, m96 as MM
from PIL import Image
old, new, out = sys.argv[1:4]; s = int(sys.argv[4]) if len(sys.argv) > 4 else 7
keys, rgb, _ = Z.load_pal(MM.PAL); rows = []
for v, b in [('S', (52, 44, 76, 62)), ('SE', (56, 44, 80, 62)), ('E', (62, 43, 84, 63))]:
    ims = []
    gn, meta = Z.read(f'{new}/EC0_{v}_96'); x, bb = MM.illus_box(meta, *b)
    W, H = (b[2] - b[0]) * s, (b[3] - b[1]) * s
    ims.append(Image.fromarray(x.astype(np.uint8)).crop(tuple(int(round(t)) for t in bb)).resize((W, H), Image.LANCZOS))
    for d in (old, new):
        g, _ = Z.read(f'{d}/EC0_{v}_96'); im = Z.render(g, keys, rgb).crop(b).resize((W, H), Image.NEAREST)
        bg = Image.new('RGB', (W, H), (200, 200, 200)); bg.paste(im, (0, 0), im); ims.append(bg)
    row = Image.new('RGB', (sum(i.width for i in ims) + 8 * len(ims), H), 'white'); xx = 0
    for i in ims: row.paste(i, (xx, 0)); xx += i.width + 8
    rows.append(row)
o = Image.new('RGB', (max(r.width for r in rows), sum(r.height + 6 for r in rows)), 'white'); y = 0
for r in rows: o.paste(r, (0, y)); y += r.height + 6
if o.width > 800: o = o.resize((800, int(o.height * 800 / o.width)), Image.LANCZOS)
o.save(out); print(o.size)
