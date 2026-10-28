"""eyesheet.py BEFORE_HEADS AFTER_HEADS OUT.png [expr,..]: eye close-up sheet (eye round): rows = views S SE E x (before | after),
cols = key expressions; each cell = the eye band of the head stamp (lash-3 .. lash+6 rows) at 8x. Writes OUT and OUT_thumb (<=800)."""
import sys, os, json, numpy as np
sys.path.insert(0, '/Users/waylonhuang/Documents/other/pixelart/swordswoman/v2/pixelize/tools')
import pzlib as Z
from PIL import Image, ImageDraw
B, A, out = sys.argv[1:4]; EX = (sys.argv[4] if len(sys.argv) > 4 else 'neutral,cheerful,determined,surprised,blink_half,joy').split(',')
keys, rgb, _ = Z.load_pal('/Users/waylonhuang/Documents/other/pixelart/swordswoman/v2/pixelize/palette.json'); K = 8
BOX = {'S': (53, 46, 75, 56), 'SE': (59, 47, 80, 57), 'E': (67, 46, 82, 56)}   # 128-cell coords
def cell(d, v, e):
    L = [l.rstrip('\n') for l in open(f'{d}/{v}_{e}.txt') if l.strip()]; ox, oy = map(int, L[0].split()[2:4])
    g = np.full((128, 128), '.', dtype='<U1')
    for j, r in enumerate([r for r in L if not r.startswith(';')]):
        for i, c in enumerate(r): g[oy + j, ox + i] = c
    x0, y0, x1, y1 = BOX[v]; im = Z.render(g[y0:y1, x0:x1], keys, rgb)
    bg = Image.new('RGB', im.size, (200, 200, 200)); bg.paste(im, (0, 0), im); return bg.resize((bg.width * K, bg.height * K), Image.NEAREST)
rows = [(f'{v} {t}', [cell(d, v, e) for e in EX]) for v in BOX for t, d in (('before', B), ('after', A))]
cw = max(i.width for _, r in rows for i in r) + 6; ch = max(r[0].height for _, r in rows) + 6
O = Image.new('RGB', (70 + cw * len(EX), 16 + ch * len(rows)), 'white'); d = ImageDraw.Draw(O)
for i, e in enumerate(EX): d.text((70 + i * cw, 2), e, fill='black')
for j, (lab, r) in enumerate(rows):
    y = 16 + j * ch + (6 if j % 2 == 0 and j else 0) * 0; d.text((4, y + ch // 2 - 6), lab, fill='black' if 'after' in lab else (110, 110, 110))
    for i, im in enumerate(r): O.paste(im, (70 + i * cw, y))
O.save(out); t = O.copy(); t.thumbnail((800, 800)); t.save(out.replace('.png', '_thumb.png')); print(out, O.size, t.size)
