"""board.py OUT.png --views SE front --methods A B C0 D EB --sizes 64 80 96 [--dir out] [--labels A=...]
rows = methods, columns = source + sizes; each cell: full figures (same display height) + head close-ups. Also OUT_thumb.png (<=800w)"""
import sys, os, argparse, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pzlib as Z
from PIL import Image, ImageDraw

FH, FR, GAP = 200, 0.40, 6
HH = (FH - GAP) // 2
ap = argparse.ArgumentParser(); ap.add_argument('out'); ap.add_argument('--views', nargs='+'); ap.add_argument('--methods', nargs='+')
ap.add_argument('--sizes', nargs='+', type=int); ap.add_argument('--dir', default=Z.ROOT + 'v2/pixelize/out'); ap.add_argument('--labels', nargs='*', default=[])
a = ap.parse_args(); LAB = dict(l.split('=', 1) for l in a.labels)


def fit(im, H, how):
    return im.resize((max(1, round(im.width * H / im.height)), H), how)


def on_white(im):
    bg = Image.new('RGB', im.size, 'white'); bg.paste(im, (0, 0), im if im.mode == 'RGBA' else None); return bg


def ill(view):
    x, m = Z.load(view); im = Image.fromarray(x.astype(np.uint8))
    return fit(im, FH, Image.LANCZOS), fit(im.crop((0, 0, im.width, int(im.height * FR))), HH, Image.LANCZOS)


def spr(stem):
    if not os.path.exists(stem + '.txt'): return None, None
    g, meta = Z.read(stem); keys, rgb, _ = Z.load_pal(meta['pal'])
    im = Z.render(g, keys, rgb); ox, oy, w, h = meta['ox'], meta['oy'], meta['w'], meta['h']
    bb = im.getbbox(); full = on_white(im.crop((min(bb[0], ox), oy, max(bb[2], ox + w), oy + h)))
    head = on_white(im.crop((max(0, ox - 2), oy, ox + w + 2, oy + int(round(h * FR)))))
    return fit(full, FH, Image.NEAREST), fit(head, HH, Image.NEAREST)


def cell(pairs):
    figs = [p[0] for p in pairs if p[0]]; heads = [p[1] for p in pairs if p[1]]
    if not figs: return Image.new('RGB', (120, FH), (235, 235, 235))
    fw = sum(f.width for f in figs) + GAP * (len(figs) - 1); hw = max(f.width for f in heads)
    c = Image.new('RGB', (fw + GAP + hw, FH), 'white'); x = 0
    for f in figs: c.paste(f, (x, 0)); x += f.width + GAP
    for i, f in enumerate(heads): c.paste(f, (fw + GAP, i * (HH + GAP)))
    return c


src = cell([ill(v) for v in a.views]); rows = []
for M in a.methods:
    rows.append((LAB.get(M, M), [src] + [cell([spr(os.path.join(a.dir, f'{M}_{v}_{s}')) for v in a.views]) for s in a.sizes]))
LW, TH = 70, 16
colw = [max((r[1][j].width if r[1][j] else 0) for r in rows) for j in range(len(a.sizes) + 1)]
RH = FH
B = Image.new('RGB', (LW + sum(colw) + GAP * len(colw), TH + len(rows) * (RH + GAP)), 'white'); d = ImageDraw.Draw(B)
x = LW
for j, t in enumerate(['illustration'] + [f'{s}px figure' for s in a.sizes]):
    d.text((x + 2, 2), t, fill='black'); x += colw[j] + GAP
for i, (name, cells) in enumerate(rows):
    y = TH + i * (RH + GAP); d.text((2, y + 4), name, fill='black'); x = LW
    if i: d.line([(0, y - 3), (B.width, y - 3)], fill=(200, 200, 200))
    for j, c in enumerate(cells):
        if c: B.paste(c, (x, y))
        x += colw[j] + GAP
if B.width > 1600: B = B.resize((1600, round(B.height * 1600 / B.width)), Image.LANCZOS)
B.save(a.out); t = B.copy(); t.thumbnail((800, 800)); t.save(a.out.replace('.png', '_thumb.png'))
print(a.out, B.size, t.size)
