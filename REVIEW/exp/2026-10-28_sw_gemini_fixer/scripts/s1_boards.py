"""Boards for step 1 (baseline). Fixer venv. -> boards/b1_baseline_key.png, boards/b1_baseline_all.png"""
import sys, os, json
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from boardlib import *

E = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/'
SW = '/Users/waylonhuang/Documents/other/pixelart/swordswoman/'
B = {b['name']: b for b in json.load(open(E + 'work/base/baseline.json'))}
MT = {m['name']: m for m in json.load(open(E + 'work/base/metrics_r96.json'))}
os.makedirs(E + 'boards', exist_ok=True)
H = 400


def item_row(name, title=None):
    b = B[name]; w = E + 'work/base/' + name
    raw = Image.open(b['in']); fx = Image.open(w + '_fix.png'); nat = Image.open(w + '_nat.png'); r = Image.open(w + '_r96.png')
    m = MT.get(name + '_r96', {})
    tiles = [fit(raw, H, False), fit(trim(fx), H), fit(trim(nat), H), r.resize((r.width * 3, r.height * 3), Image.NEAREST).convert('RGBA'), r]
    tiles = [on_grey(t) for t in tiles]
    labs = [f'raw {b["in_size"][0]}x{b["in_size"][1]}', f'fixer grid {b["step_x"]:.2f}x{b["step_y"]:.2f} ({b["grid_pick"]})\nfig {b["fig_native_h"]} px  rt-err {b["err_best"]}',
            f'lock native h{b["fig_native_h"]}', f'r96 lock 3x ({b["rescale"]})\nssim_b {m.get("ssim_b", 0):.2f} dE {m.get("dE", 0):.1f}', '1x']
    return row(tiles, labs, H, title=title or name)


def ref_row():
    il = Image.open(SW + 'v2/hair/turnE_final/iso_SE_fixed.png'); ms = Image.open(SW + 'v2/m96/masters/EC0_SE_96.png')
    return row([fit(il, H, False), on_grey(ms.resize((384, 384), Image.NEAREST)), on_grey(ms)],
               ['illustration iso_SE_fixed', 'm96 master SE 3x\nssim_b vs illus .81 (vs warped geo src .92)', '1x'], H, title='REFERENCE')


key = ['pzD_SE_96', 'pzD_SE_80', 'pzD_S_96', 'pixel_g48s_a', 'pixE_mk_v1', 'redraw_walk_raw_d2f00_k0']
stack([ref_row()] + [item_row(n) for n in key]).save(E + 'boards/b1_baseline_key.png')
H = 220
rows = [item_row(n) for n in B if 'error' not in B[n]]
# two columns of rows
half = (len(rows) + 1) // 2
L, R = stack(rows[:half]), stack(rows[half:])
out = Image.new('RGB', (L.width + R.width + 12, max(L.height, R.height)), GREY); out.paste(L, (0, 0)); out.paste(R, (L.width + 12, 0))
out.save(E + 'boards/b1_baseline_all.png')
print('ok')
