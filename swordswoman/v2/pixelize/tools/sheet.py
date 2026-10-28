"""sheet.py DIR [views...]: per view column: illustration | pixel 4x | pixel 1x  -> DIR/sheet.png (+ sheet_thumb.png)"""
import sys, os, glob, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pzlib as Z
from PIL import Image, ImageDraw
D = sys.argv[1]; views = sys.argv[2:] or ['S', 'SE', 'E', 'NE', 'N']
cols = []
for v in views:
    st = glob.glob(os.path.join(D, f'*_{v}_*.txt')); st = [s for s in st if os.path.basename(s).split('_')[1] == v][0][:-4]
    g, meta = Z.read(st); keys, rgb, _ = Z.load_pal(meta['pal']); im = Z.render(g, keys, rgb)
    bb = im.getbbox(); spr = im.crop((bb[0] - 2, bb[1] - 2, bb[2] + 2, bb[3] + 2))
    s4 = spr.resize((spr.width * 4, spr.height * 4), Image.NEAREST)
    x, m = Z.load(v, meta['src']); il = Image.fromarray(x.astype(np.uint8)); il = il.resize((round(il.width * s4.height / il.height), s4.height), Image.LANCZOS)
    cols.append((v, il, s4, spr))
W = sum(max(c[1].width, c[2].width) + 16 for c in cols); H = 16 + cols[0][2].height * 2 + max(c[3].height for c in cols) + 30
S = Image.new('RGB', (W, H), 'white'); d = ImageDraw.Draw(S); x = 0
for v, il, s4, spr in cols:
    cw = max(il.width, s4.width); d.text((x + 2, 2), v, fill='black')
    S.paste(il, (x, 16)); y = 16 + il.height + 6
    bg = Image.new('RGB', s4.size, 'white'); bg.paste(s4, (0, 0), s4); S.paste(bg, (x, y)); y += s4.height + 10
    bg = Image.new('RGB', spr.size, 'white'); bg.paste(spr, (0, 0), spr); S.paste(bg, (x, y)); x += cw + 16
S.save(os.path.join(D, 'sheet.png')); t = S.copy(); t.thumbnail((800, 800)); t.save(os.path.join(D, 'sheet_thumb.png')); print(D, S.size, t.size)
