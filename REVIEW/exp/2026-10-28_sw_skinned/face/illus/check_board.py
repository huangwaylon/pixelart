"""check_board.py (F round 7): per view, the illustration variants (head crop) + their 1x/4x proxy pixelization (pz.py EC0 at 96 px, the method of
the approved masters) next to the m96 master.  -> chk/board_<V>.png"""
import os, sys, json, subprocess
import numpy as np
from PIL import Image, ImageDraw
D = os.path.dirname(os.path.abspath(__file__)); SW = '/Users/waylonhuang/Documents/other/pixelart/swordswoman/'
PY = '/Users/waylonhuang/Documents/other/pixelart/.models/pixtools/venv/bin/python'
sys.path.insert(0, '/Users/waylonhuang/Documents/other/pixelart/REVIEW/exp/2026-10-28_sw_hires3d/scripts')
import hx
NAMES = ['neutral', 'neutral_half', 'neutral_blink', 'smile', 'joyful_open', 'determined', 'focused', 'effort_open', 'surprised_open', 'squint', 'hurt_open', 'wince']
BG = (110, 110, 110)
for V in sys.argv[1:] or ['S', 'SE', 'E']:
    box = json.load(open(f'{D}/out/index.json'))[V]['box']; od = f'{D}/chk/px_{V}'; os.makedirs(od, exist_ok=True)
    tiles = []
    m = hx.read_grid(f'{SW}v2/m96/masters/EC0_{V}_96.txt'); ys, xs = np.nonzero(m[:75] != '.'); y0 = ys.min() - 1; cx = int(np.median(xs[ys < y0 + 30]))
    def hc(g): return g[y0:y0 + 36, cx - 18:cx + 18]
    mt = hx.render(hc(m), 5, BG).convert('RGB'); ImageDraw.Draw(mt).text((3, 2), f'm96 master {V}', fill=(150, 220, 255))
    tiles.append((Image.new('RGB', (180, 180), 'white'), mt))
    for n in NAMES:
        p = f'{D}/out/{V}/{n}.png'
        subprocess.run([PY, '-I', f'{SW}v2/pixelize/tools/pz.py', 'EC0', V, '96', '--src', p, '--pal', f'{SW}v2/pixelize/palette.json', '--out', od, '--tag', '_' + n], capture_output=True)
        g = hx.read_grid(f'{od}/EC0_{n}_{V}_96.txt')
        t = hx.render(hc(g), 5, BG).convert('RGB'); t.paste(hx.render(hc(g), 1, BG), (t.width - 38, t.height - 38)); ImageDraw.Draw(t).text((3, 2), n, fill=(255, 255, 150))
        il = Image.open(p).convert('RGB').crop((box[0] + 60, box[1] + 120, box[2] - 60, box[3] - 40)).resize((180, 180), Image.LANCZOS)
        tiles.append((il, t))
    W = sum(max(a.width, b.width) + 4 for a, b in tiles); H = max(a.height for a, b in tiles) + max(b.height for a, b in tiles) + 6
    B = Image.new('RGB', (W, H), (36, 36, 40)); x = 0
    for a, b in tiles: B.paste(a, (x, 0)); B.paste(b, (x, a.height + 4)); x += max(a.width, b.width) + 4
    B.save(f'{D}/chk/board_{V}.png'); print('board', V)
