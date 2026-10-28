"""S1 contact sheet: whole set at 3x (slate) + 1x strips on slate/dirt/grass + look target / lock refs."""
import json, sys
from PIL import Image, ImageDraw
R = '/Users/waylonhuang/Documents/other/pixelart/swordswoman'
B = sys.argv[1] if len(sys.argv) > 1 else R + '/hybrid/S1_redraw/r1'
OUT = sys.argv[2] if len(sys.argv) > 2 else B + '/sheet.png'
TER = {'slate': (36, 32, 44), 'dirt': (110, 84, 60), 'grass': (74, 120, 58)}
ROWS = [[f'turn_{d}' for d in ['S', 'SE', 'E', 'NE', 'N', 'NW', 'W', 'SW']],
        [f'walk_SE_k{i}' for i in range(4)], [f'slash_SE_k{i}' for i in range(4)],
        [f'jump_E_{k}' for k in ['crouch', 'apex', 'land']]]
C = (8, 24, 128, 120); Z = 3; cw, ch = (C[2] - C[0]) * Z, (C[3] - C[1]) * Z
W = 8 * cw + 40; Hh = 4 * (ch + 18) + 3 * 110 + 330
s = Image.new('RGB', (W, Hh), (24, 22, 30)); d = ImageDraw.Draw(s)
y = 6
d.text((8, y), 'S1_redraw r1 POLISHED: Claude hand-pixel body cels (one torso cel per direction, autoshade light rule) under the locked head stamps, katana stamps, hand-animated slash smears + secondary motion', fill='white'); y += 16
for row in ROWS:
    for i, n in enumerate(row):
        im = Image.open(f'{B}/sprite/{n}.png').convert('RGBA').crop(C).resize((cw, ch), Image.NEAREST)
        bg = Image.new('RGBA', (cw, ch), TER['slate'] + (255,)); bg.alpha_composite(im)
        dd = ImageDraw.Draw(bg); dd.line([(0, (104 - C[1]) * Z), (cw, (104 - C[1]) * Z)], fill=(70, 70, 90))
        s.paste(bg.convert('RGB'), (20 + i * cw, y)); d.text((22 + i * cw, y + 2), n, fill=(255, 230, 120))
    y += ch + 18
for t, col in TER.items():
    x = 20
    for row in ROWS:
        for n in row:
            im = Image.open(f'{B}/sprite/{n}.png').convert('RGBA').crop((24, 30, 112, 118))
            bg = Image.new('RGBA', im.size, col + (255,)); bg.alpha_composite(im); s.paste(bg.convert('RGB'), (x, y)); x += im.size[0]
        x += 10
    d.text((W - 60, y + 2), t, fill='white'); y += 100
refs = [R + '/concept/chibi_iso_v5.png', R + '/docs/palette_v1_vs_v2_terrain.png', R + '/hybrid/lock/turn8_iso.png', R + '/hybrid/lock/pixel/pixel_lock_sheet.png']
x = 20
for r in refs:
    im = Image.open(r).convert('RGB'); im.thumbnail((W // 4 - 20, 320)); s.paste(im, (x, y)); x += im.size[0] + 10
s.save(OUT); print('sheet', OUT, s.size)
