"""faces.py out.png H stem1 stem2 ... : illustration head crop + sprite head crops (top 34% of figure), same display height"""
import sys, os, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pzlib as Z
from PIL import Image, ImageDraw
out, DH = sys.argv[1], int(sys.argv[2]); stems = [s[:-4] if s.endswith(('.png', '.txt')) else s for s in sys.argv[3:]]
FR = 0.40
def head_ill(meta):
    x, m = Z.load(meta['view'], meta['src']); hc = int(x.shape[0] * FR)
    return Image.fromarray(x[:hc].astype(np.uint8))
def head_spr(stem):
    g, meta = Z.read(stem); keys, rgb, _ = Z.load_pal(meta['pal'])
    im = Z.render(g, keys, rgb).convert('RGBA'); hc = int(round(meta['h'] * FR))
    pad = 3; box = (max(0, meta['ox'] - pad), meta['oy'], meta['ox'] + meta['w'] + pad, meta['oy'] + hc)
    c = im.crop(box); bg = Image.new('RGB', c.size, 'white'); bg.paste(c, (0, 0), c)
    s = max(1, DH // c.height); return bg.resize((c.width * s, c.height * s), Image.NEAREST), meta
tiles = []; metas = []
for s in stems:
    t, meta = head_spr(s); tiles.append((os.path.basename(s), t)); metas.append(meta)
il = head_ill(metas[0]); il = il.resize((int(il.width * DH / il.height), DH), Image.LANCZOS)
tiles = [('illustration', il)] + tiles
W = sum(t.width + 8 for _, t in tiles); c = Image.new('RGB', (W, DH + 14), 'white'); d = ImageDraw.Draw(c); x = 0
for n, t in tiles:
    c.paste(t, (x, 14)); d.text((x + 2, 1), n, fill='black'); x += t.width + 8
c.save(out); print(out, c.size)
