"""Holistic review sheet for a round: R/sheet.png
rows: turn x8 | walk_SE k0-k3 | slash_SE k0-k3 | jump_E crouch/apex/land | bonus run/dash, each frame at 4x on slate
(#24202c) with its name, plus a 1x strip of the same row on slate / dirt / grass; header: look target (iso_v5 +
its pixelization) and the lock2 heads."""
import os, sys
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, '/Users/waylonhuang/Documents/other/pixelart/swordswoman/tools/pixel')
from gif import grass_tile
R = sys.argv[1]
SP = f'{R}/sprite'
ROWS = [('turn', [f'turn_{d}' for d in ['S', 'SE', 'E', 'NE', 'N', 'NW', 'W', 'SW']]),
        ('walk_SE', [f'walk_SE_k{i}' for i in range(4)]),
        ('slash_SE', [f'slash_SE_k{i}' for i in range(4)]),
        ('jump_E', ['jump_E_crouch', 'jump_E_apex', 'jump_E_land']),
        ('bonus smears', ['run_SE_f1', 'dash_SE_f1'])]
SLATE, DIRT = (36, 32, 44), (112, 86, 62)
Z = 4; CW, CH = 96, 92            # crop of the 128 cell: x 16..112, y 20..112
def crop(a): return a[20:20 + CH, 16:16 + CW]
def on(a, bg):
    h, w = a.shape[:2]
    base = np.zeros((h, w, 3), np.uint8)
    if isinstance(bg, tuple): base[:] = bg
    else: base[:] = bg[:h, :w]
    m = a[..., 3] > 0
    base[m] = a[..., :3][m]
    return base
grass = grass_tile(CW, CH)
W = 8 * CW * Z + 40
rows_img = []
for title, names in ROWS:
    names = [n for n in names if os.path.exists(f'{SP}/{n}.png')]
    if not names: continue
    im = Image.new('RGB', (W, CH * Z + 22 + CH + 8), (24, 22, 30)); d = ImageDraw.Draw(im)
    d.text((6, 4), title, fill=(235, 235, 235))
    for i, n in enumerate(names):
        a = crop(np.array(Image.open(f'{SP}/{n}.png').convert('RGBA')))
        big = Image.fromarray(on(a, SLATE)).resize((CW * Z, CH * Z), Image.NEAREST)
        im.paste(big, (20 + i * CW * Z, 18)); d.text((24 + i * CW * Z, 20), n, fill=(200, 200, 210))
        for j, bg in enumerate((SLATE, DIRT, grass)):
            im.paste(Image.fromarray(on(a, bg)), (20 + i * CW * Z + j * (CW + 4), 18 + CH * Z + 4))
    rows_img.append(im)
# header
hdr = Image.new('RGB', (W, 300), (24, 22, 30)); d = ImageDraw.Draw(hdr)
iso = Image.open('concept/chibi_iso_v5.png').convert('RGB'); iso.thumbnail((260, 290)); hdr.paste(iso, (10, 5))
pz = Image.open('docs/palette_v1_vs_v2_terrain.png').convert('RGB'); pz.thumbnail((700, 290)); hdr.paste(pz, (280, 5))
lk = Image.open('hybrid/lock2/lock2_sheet_x6.png').convert('RGB'); lk.thumbnail((900, 290)); hdr.paste(lk, (1000, 5))
d.text((10, 285), 'look target iso_v5 | its pixelization | lock2 head stamps v2 (all expressions)', fill=(220, 220, 220))
H = hdr.height + sum(r.height for r in rows_img)
out = Image.new('RGB', (W, H), (24, 22, 30)); y = 0
out.paste(hdr, (0, 0)); y = hdr.height
for r in rows_img: out.paste(r, (0, y)); y += r.height
out.save(f'{R}/sheet.png'); print('sheet', out.size)
