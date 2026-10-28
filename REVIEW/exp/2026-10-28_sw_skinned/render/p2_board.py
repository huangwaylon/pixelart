"""p2_board.py (P) ACT VIEW [--crop x0,y0,x1,y1] [--scale s] [--out path]  (pixtools venv)
Board: rows = round-1 shipped (old rig/motion, head stamp: render/out/<act>/<act>_<view>_px_hs), round-1 chain on the\nCURRENT passes (render/out/p2/r1/), P2 pixel (render/out/p2/<act>/<act>_<view>_px), per frame at --scale,
plus a 1x strip of both rows under it and the m96 master at the left of each row.  Mid-grey background."""
import sys, os, glob, numpy as np
from PIL import Image, ImageDraw
EXP = '/Users/waylonhuang/Documents/other/pixelart/REVIEW/exp/2026-10-28_sw_skinned/'
MAST = '/Users/waylonhuang/Documents/other/pixelart/swordswoman/v2/m96/masters/EC0_{}_96.png'
BG = (128, 128, 128)
a = sys.argv[1:]; act, view = a[0], a[1]
cr = next((tuple(int(v) for v in a[i + 1].split(',')) for i, x in enumerate(a) if x == '--crop'), (24, 24, 104, 124))
S = int(next((a[i + 1] for i, x in enumerate(a) if x == '--scale'), 4))
out = next((a[i + 1] for i, x in enumerate(a) if x == '--out'), f'{EXP}render/out/p2/{act}/board_{act}_{view}.png')
rows = [('r1 shipped', f'{EXP}render/out/{act}/{act}_{view}_px_hs'), ('r1 chain', f'{EXP}render/out/p2/r1/{act}/{act}_{view}_px'),
        ('P2', f'{EXP}render/out/p2/{act}/{act}_{view}_px')]
rows += [(lbl, p) for lbl, p in [(x.split('=')[0], x.split('=')[1]) for x in a if '=' in x and not x.startswith('--')]]


def onbg(im):
    im = im.convert('RGBA'); b = Image.new('RGBA', im.size, BG + (255,)); b.alpha_composite(im); return b.convert('RGB')


def frames(d):
    fs = sorted(glob.glob(d + '/f??.png')); return [onbg(Image.open(f)) for f in fs]


R = [(l, frames(d)) for l, d in rows if os.path.isdir(d)]
m = onbg(Image.open(MAST.format(view)))
n = max(len(f) for _, f in R); cw, ch = (cr[2] - cr[0]) * S, (cr[3] - cr[1]) * S
W = (n + 1) * (cw + 4) + 70; Ht = len(R) * (ch + 16) + len(R) * 132 + 10
B = Image.new('RGB', (W, Ht), (40, 40, 44)); d = ImageDraw.Draw(B); y = 0
for l, fs in R:
    d.text((4, y + 2), l, fill=(230, 230, 120))
    B.paste(m.crop(cr).resize((cw, ch), Image.NEAREST), (70, y + 14))
    for i, f in enumerate(fs):
        B.paste(f.crop(cr).resize((cw, ch), Image.NEAREST), (70 + (i + 1) * (cw + 4), y + 14)); d.text((72 + (i + 1) * (cw + 4), y + 2), f'f{i:02d}', fill=(200, 200, 200))
    y += ch + 16
for l, fs in R:
    d.text((4, y + 2), l + ' 1x', fill=(230, 230, 120)); x = 70
    for f in [m] + fs:
        B.paste(f, (x, y + 2)); x += 130
    y += 132
B.save(out); print(out)
