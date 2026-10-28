"""overview.py DIR OUT.png [S=3]: per view: illustration over sprite (S x)"""
import sys, os, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import m96 as M, pzlib as Z
from PIL import Image
d, out = sys.argv[1], sys.argv[2]; s = int(sys.argv[3]) if len(sys.argv) > 3 else 3
keys, rgb, _ = Z.load_pal(M.PAL); cols = []
for v in ['S', 'SE', 'E', 'NE', 'N']:
    g, meta = Z.read(f'{d}/EC0_{v}_96'); im = Z.render(g, keys, rgb).crop((38, 26, 90, 127))
    bg = Image.new('RGB', im.size, (190, 190, 190)); bg.paste(im, (0, 0), im); bg = bg.resize((im.width * s, im.height * s), Image.NEAREST)
    x, b = M.illus_box(meta, 38, 26, 90, 127); il = Image.fromarray(x.astype(np.uint8)).crop(tuple(int(round(t)) for t in b)).resize(bg.size, Image.LANCZOS)
    cols.append((il, bg))
W = sum(c[1].width + 4 for c in cols); S = Image.new('RGB', (W, cols[0][1].height * 2 + 4), 'white'); x = 0
for il, bg in cols: S.paste(il, (x, 0)); S.paste(bg, (x, bg.height + 4)); x += bg.width + 4
S.save(out); print(out, S.size)
