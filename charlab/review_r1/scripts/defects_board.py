"""charlab review r1: defects.png - one 4x frame per top defect."""
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFont
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')); OUT = os.path.join(ROOT, 'lab', 'out')
BG = (122, 128, 140); FONT = ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc', 14)
D = [('ranger/simple_slim/64/S_f06', 'D1 detached shins/boots (slim 64)'),
     ('runner/medium_slim/96/SE_f04', 'D1 1-px limbs break (slim 96)'),
     ('schoolgirl/medium_compact/64/E_f00', 'D2 E: face hidden, tie floats'),
     ('astronaut/medium_chibi/48/E_f02', 'D2 E: faceless helmet'),
     ('mechanic/medium_compact/64/S_f00', 'D3 barrel torso, A-pose arms'),
     ('runner/medium_compact/64/S_f00', 'D4 ponytail reads as a head spike'),
     ('diver/detailed_compact/48/SE_f02', 'D5 decals/fins < 64 px = specks'),
     ('ranger/medium_chibi/48/SE_f02', 'D6 chibi hat = mushroom over face')]
tiles = []
for p, cap in D:
    im = Image.open(os.path.join(OUT, p + '.png')).convert('RGBA')
    a = np.array(im)[..., 3] > 0; ys, xs = np.nonzero(a)
    im = im.crop((xs.min() - 2, ys.min() - 2, xs.max() + 3, ys.max() + 3))
    k = max(2, min(6, 300 // im.height)); im = im.resize((im.width * k, im.height * k), Image.NEAREST)
    t = Image.new('RGBA', (max(im.width, 290), im.height + 40), BG + (255,)); t.alpha_composite(im, ((t.width - im.width) // 2, 36))
    d = ImageDraw.Draw(t); d.text((4, 2), cap, fill=(255, 255, 255), font=FONT); d.text((4, 18), p.replace('/', ' / ') + f'  x{k}', fill=(225, 230, 240), font=FONT)
    tiles.append(t.convert('RGB'))
H = max(t.height for t in tiles); rows = [tiles[:4], tiles[4:]]
W = max(sum(t.width for t in r) + 6 * 5 for r in rows)
o = Image.new('RGB', (W, 2 * H + 18), (30, 31, 36)); y = 6
for r in rows:
    x = 6
    for t in r: o.paste(t, (x, y)); x += t.width + 6
    y += H + 6
o.save(os.path.join(ROOT, 'review_r1', 'defects.png'))
