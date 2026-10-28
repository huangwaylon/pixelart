"""f3d_exprboard.py (F round 5): expression board per view from a multi-frame f3d render dir: per frame the pixelized head (standard chain) 6x + 1x inset,
and the hi-res guide (matid) crop; leftmost = m96 master.   python f3d_exprboard.py <dir> <view> [<view> ...]"""
import os, sys, json
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, '/Users/waylonhuang/Documents/other/pixelart/REVIEW/exp/2026-10-28_sw_hires3d/scripts')
import hx
EXP = '/Users/waylonhuang/Documents/other/pixelart/REVIEW/exp/2026-10-28_sw_skinned'
M96 = '/Users/waylonhuang/Documents/other/pixelart/swordswoman/v2/m96/'; BG = (110, 110, 110); MIR = {'W': 'E', 'SW': 'SE', 'NW': 'NE'}
d = sys.argv[1]; act = os.path.basename(d.rstrip('/')).replace('_nocut', '')
rows = []
for V in sys.argv[2:]:
    st = f'{d}/{act}_{V}'; info = json.load(open(st + '.json')); al = json.load(open(f'{EXP}/rig/align.json'))[V]
    src = MIR.get(V); m = hx.read_grid(f'{M96}masters/EC0_{src or V}_96.txt')
    if src: m = m[:, ::-1]
    lift = al['dy'] - al.get('reg_dy', al['dy'])
    ys, xs = np.nonzero(m[:75] != '.'); my0 = ys.min() - 1; mcx = int(np.median(xs[ys < my0 + 30]))
    y0, x0 = my0 + 8 + lift, mcx - 15
    mt = hx.render(m[my0 + 8:my0 + 34, mcx - 15:mcx + 15], 6, BG).convert('RGB'); ImageDraw.Draw(mt).text((3, 2), f'm96 {V}', fill=(150, 220, 255))
    tl = [mt]; gl = [Image.new('RGB', mt.size, (36, 36, 40))]
    M = json.load(open(f'{EXP}/face/f3d/fexpr.json'))['frames'] if act == 'fexpr' else None
    for f in info['frames']:
        i = f['i']; g = hx.read_grid(f'{st}_px/f{i:02d}.txt'); c = g[y0:y0 + 26, x0:x0 + 30]
        t = hx.render(c, 6, BG).convert('RGB'); t.paste(hx.render(c, 1, BG), (t.width - 32, t.height - 28))
        lab = os.path.basename(f.get('face_tex') or '?').replace('.png', '')
        ImageDraw.Draw(t).text((3, 2), lab, fill=(255, 255, 150)); tl.append(t)
        gd = Image.open(f'{st}_f{i:02d}_guide.png').convert('RGBA'); X = (x0 + 32 - al['dx']) * 8; Y = (y0 + 32 - al['dy']) * 8
        gc = gd.crop((X, Y, X + 30 * 8, Y + 26 * 8)).resize(t.size); bg = Image.new('RGBA', t.size, BG + (255,)); bg.alpha_composite(gc); gl.append(bg.convert('RGB'))
    rows += [tl, gl]
W = max(sum(t.width + 4 for t in r) for r in rows); H = sum(r[0].height + 4 for r in rows)
B = Image.new('RGB', (W, H), (36, 36, 40)); y = 0
for r in rows:
    x = 0
    for t in r: B.paste(t, (x, y)); x += t.width + 4
    y += r[0].height + 4
p = f'{d}/board_expr_{act}.png'; B.save(p); print(p)
