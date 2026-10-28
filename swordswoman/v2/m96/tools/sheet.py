"""sheet.py DIR OUT.png: per view column: illustration (original turnE_final) | master 4x->2x | master 1x  (+ OUT_thumb.png <=800)"""
import sys, os, numpy as np
sys.path.insert(0, '/Users/waylonhuang/Documents/other/pixelart/swordswoman/v2/pixelize/tools'); sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pzlib as Z, m96 as M
from PIL import Image, ImageDraw
D, out = sys.argv[1], sys.argv[2]; keys, rgb, _ = Z.load_pal(M.PAL); cols = []
for v in ['S', 'SE', 'E', 'NE', 'N']:
    g, meta = Z.read(f'{D}/EC0_{v}_96'); im = Z.render(g, keys, rgb).crop((36, 24, 92, 127))
    s4 = im.resize((im.width * 4, im.height * 4), Image.NEAREST); s2 = s4.resize((im.width * 2, im.height * 2), Image.NEAREST)
    x, m = Z.load(v, None); il = Image.fromarray(x.astype(np.uint8)); il = il.resize((round(il.width * s2.height * 0.93 / il.height), round(s2.height * 0.93)), Image.LANCZOS)
    cols.append((v, il, s2, im))
cw = max(max(c[1].width, c[2].width) for c in cols) + 12
H = 18 + cols[0][2].height * 2 + 20 + cols[0][3].height + 10
S = Image.new('RGB', (cw * len(cols), H), 'white'); d = ImageDraw.Draw(S)
for k, (v, il, s2, im) in enumerate(cols):
    x = k * cw; d.text((x + 4, 3), v, fill='black'); S.paste(il, (x + (cw - il.width) // 2, 18))
    y = 18 + s2.height + 6; bg = Image.new('RGB', s2.size, (235, 235, 235)); bg.paste(s2, (0, 0), s2); S.paste(bg, (x + (cw - s2.width) // 2, y))
    y += s2.height + 10; bg = Image.new('RGB', im.size, (235, 235, 235)); bg.paste(im, (0, 0), im); S.paste(bg, (x + (cw - im.width) // 2, y))
S.save(out); t = S.copy(); t.thumbnail((800, 800)); t.save(out[:-4] + '_thumb.png'); print(out, S.size, t.size)
