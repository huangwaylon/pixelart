"""f3d_board.py (F, round 5): iteration board for the 3D face: m96 master head | pixelized head (standard chain) 8x | 1x | hi-res guide crop.
  python f3d_board.py <outdir> <stem> [<stem> ...]  -> <outdir>/board_<tag>.png  (stem = <dir>/<act>_<V>, frame f00 or --f=i)"""
import os, sys, json
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, '/Users/waylonhuang/Documents/other/pixelart/REVIEW/exp/2026-10-28_sw_hires3d/scripts')
import hx
M96 = '/Users/waylonhuang/Documents/other/pixelart/swordswoman/v2/m96/'
BG = (110, 110, 110)
MIR = {'W': 'E', 'SW': 'SE', 'NW': 'NE'}


def tile(stem, i, lab):
    V = os.path.basename(stem).split('_')[-1]; g = hx.read_grid(f'{stem}_px/f{i:02d}.txt')
    ys, xs = np.nonzero(g[:75] != '.'); y0 = max(0, ys.min() - 1); cx = int(np.median(xs[ys < y0 + 30]))
    x0 = cx - 18; c = g[y0:y0 + 38, x0:x0 + 36]
    t8 = hx.render(c, 8, BG).convert('RGB'); ImageDraw.Draw(t8).text((4, 3), lab, fill=(255, 255, 150))
    t8.paste(hx.render(c, 1, BG), (t8.width - 40, t8.height - 42))
    src = MIR.get(V); m = hx.read_grid(f'{M96}masters/EC0_{src or V}_96.txt')
    if src: m = m[:, ::-1]
    ys, xs = np.nonzero(m[:75] != '.'); my0 = ys.min() - 1; mcx = int(np.median(xs[ys < my0 + 30]))
    mt = hx.render(m[my0:my0 + 38, mcx - 18:mcx + 18], 8, BG).convert('RGB'); ImageDraw.Draw(mt).text((4, 3), f'm96 master {V}', fill=(150, 220, 255))
    gd = Image.open(f'{stem}_f{i:02d}_guide.png').convert('RGBA'); info = json.load(open(stem + '.json')); al = json.load(open('/Users/waylonhuang/Documents/other/pixelart/REVIEW/exp/2026-10-28_sw_skinned/rig/align.json'))[V]
    X = (x0 + 32 - al['dx']) * 8; Y = (y0 + 32 - al['dy']) * 8
    gc = gd.crop((X, Y, X + 36 * 8, Y + 38 * 8)); bg = Image.new('RGBA', gc.size, BG + (255,)); bg.alpha_composite(gc)
    return [mt, t8, bg.convert('RGB')]


if __name__ == '__main__':
    od = sys.argv[1]; fi = next((int(a.split('=')[1]) for a in sys.argv if a.startswith('--f=')), 0)
    stems = [a for a in sys.argv[2:] if not a.startswith('--')]
    tag = os.environ.get('TAG', 'f3d')
    rows = [tile(s, fi, f'{os.path.basename(s)} f{fi:02d} (standard chain)') for s in stems]
    W = sum(t.width + 6 for t in rows[0]); H = sum(r[0].height + 6 for r in rows)
    B = Image.new('RGB', (W, H), (36, 36, 40)); y = 0
    for r in rows:
        x = 0
        for t in r: B.paste(t, (x, y)); x += t.width + 6
        y += r[0].height + 6
    p = f'{od}/board_{tag}.png'; B.save(p); print(p)
