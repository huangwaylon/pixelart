"""polished_sheet.png: pre-polish vs polished, all 19 sprites at 3x (cropped cells) + 1x strips + refs"""
import os, sys
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
import hylib as H
R = 'hybrid/S2_gridsheet/r1'
names = H.STD_NAMES
Z, C = 3, (16, 24, 120, 116)                 # crop of the 128 cell
cw, ch = (C[2] - C[0]) * Z, (C[3] - C[1]) * Z
rows = [('pre-polish (sprite/)', f'{R}/sprite'), ('POLISHED (polished/)', f'{R}/polished')]
W = 10 * (cw + 4) + 8
Ht = 2 * (2 * (ch + 18)) + 2 * 140 + 560
im = Image.new('RGB', (W, Ht), (28, 26, 34)); d = ImageDraw.Draw(im)
y = 4
for label, src in rows:
    d.text((6, y), label, fill=(240, 220, 120)); y += 14
    for i, n in enumerate(names):
        r, c = divmod(i, 10)
        cell = Image.open(f'{src}/{n}.png').convert('RGBA').crop(C).resize((cw, ch), Image.NEAREST)
        bg = Image.new('RGBA', cell.size, (128, 128, 132, 255)); bg.alpha_composite(cell)
        x0, y0 = 6 + c * (cw + 4), y + r * (ch + 18)
        im.paste(bg.convert('RGB'), (x0, y0 + 12)); d.text((x0 + 2, y0), n, fill=(200, 200, 200))
    y += 2 * (ch + 18) + 6
for label, src in rows:
    d.text((6, y), label + ' 1x on grass', fill=(240, 220, 120)); y += 14
    for i, n in enumerate(names):
        cell = Image.open(f'{src}/{n}.png').convert('RGBA').crop(C)
        bg = Image.new('RGBA', cell.size, (72, 120, 56, 255)); bg.alpha_composite(cell)
        im.paste(bg.convert('RGB'), (6 + i * (C[2] - C[0] + 2), y))
    y += 120
for k, p in enumerate(['concept/chibi_iso_v5.png', 'docs/palette_v1_vs_v2_terrain.png']):
    ref = Image.open(p).convert('RGB'); s = 540 / ref.height
    ref = ref.resize((int(ref.width * s), 540))
    im.paste(ref, (6 + k * 560, y)); d.text((8 + k * 560, y + 2), p, fill=(255, 80, 80))
im.save(f'{R}/polished_sheet.png'); print(im.size)
