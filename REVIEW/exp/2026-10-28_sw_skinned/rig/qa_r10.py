"""qa_r10.py : round-7 QA -> rig/qa/r10_QA.png : per view (S SE E NE N): illustration head | m96 master 4x | rig preview (illustration-textured
head, unlit) | rig pixel 4x (R QA chain = round-1 chain + tex pass snapped to the palette) ; walk SE f0/2/4/6 pixel 4x ; 1x strip."""
import sys, json, numpy as np
sys.path.insert(0, '/Users/waylonhuang/Documents/other/pixelart/REVIEW/exp/2026-10-28_sw_hires3d/scripts'); import hx
from PIL import Image, ImageDraw
SRC = {'S': 'iso_S.png', 'SE': 'iso_SE_fixed.png', 'E': 'iso_E.png', 'NE': 'iso_NE.png', 'N': 'iso_N.png'}
IM = json.load(open('rig/illus_map.json')); AL = json.load(open('rig/align.json')); D = 'rig/qa/r10'; T = 256
tiles = []
for v in SRC:
    ill = Image.open('/Users/waylonhuang/Documents/other/pixelart/swordswoman/v2/hair/turnE_final/' + SRC[v]).convert('RGB'); mp = IM[v]
    # head box in master coords (rows 24..72, cols 36..92) -> illustration px
    X0, X1 = [(c - mp['bx']) / mp['ax'] for c in (36, 92)]; Y0, Y1 = [(r - mp['by']) / mp['ay'] for r in (22, 74)]
    tiles.append((ill.crop((int(X0), int(Y0), int(X1), int(Y1))).resize((T, int(T * (Y1 - Y0) / (X1 - X0)))), f'{v} illustration'))
    m = hx.read_grid(hx.SW + f'v2/m96/masters/EC0_{v}_96.txt'); L = AL[v]['lift_px']; mm = np.full_like(m, '.'); mm[:128 - L] = m[L:]
    tiles.append((hx.render(mm, 4).crop((36 * 4, (22 - L) * 4, 92 * 4, (74 - L) * 4)), f'{v} master'))
    pv = Image.open(f'{D}/rest_{v}_f00_pv.png').convert('RGBA'); k = pv.size[0] // 192; dy = AL[v]['dy']; dx = AL[v]['dx']
    c = pv.crop(((36 + 32 - dx) * k, (22 - L + 32 - dy) * k, (92 + 32 - dx) * k, (74 - L + 32 - dy) * k)); bg = Image.new('RGBA', c.size, (110, 110, 110, 255)); bg.alpha_composite(c)
    tiles.append((bg.convert('RGB'), f'{v} rig preview'))
    g = hx.read_grid(f'{D}/rest_{v}_rq/f00.txt'); tiles.append((hx.render(g, 4).crop((36 * 4, (22 - L) * 4, 92 * 4, (74 - L) * 4)), f'{v} rig pixel'))
for i in (0, 2, 4, 6):
    g = hx.read_grid(f'{D}/walk_SE_rq/f{i:02d}.txt'); tiles.append((hx.render(g, 4).crop((30 * 4, 14 * 4, 98 * 4, 110 * 4)), f'walk SE f{i}'))
cols = 4; rows = (len(tiles) + cols - 1) // cols; W = Image.new('RGB', (T * cols + 40, 300 * rows + 140), (40, 40, 44)); d = ImageDraw.Draw(W)
for k_, (im, lab) in enumerate(tiles):
    im = im.copy(); im.thumbnail((T, 280)); x, y = (k_ % cols) * (T + 10), (k_ // cols) * 300; W.paste(im, (x, y + 14)); d.text((x + 3, y + 1), lab, fill=(240, 230, 120))
x = 0
for v in SRC:
    W.paste(hx.render(hx.read_grid(f'{D}/rest_{v}_rq/f00.txt'), 1).crop((14, 10, 114, 124)), (x, 300 * rows + 10)); x += 104
W.save('rig/qa/r10_QA.png'); print(W.size)
