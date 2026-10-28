#!/usr/bin/env python3
"""r4: png/zoom.png = given composed views side by side at 12x + 2x. usage: zoom.py se_neutral e_neutral ..."""
import sys, os
from PIL import Image
H = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
ims = [Image.open(f'{H}/png/{n}_1x.png') for n in sys.argv[1:]]
S = int(os.environ.get('S', 12)); W = sum(i.width * S + 10 for i in ims); Hh = max(i.height for i in ims) * S
sh = Image.new('RGB', (W, Hh + 80), (40, 40, 40)); x = 0
for k, i in enumerate(ims):
    sh.paste(i.resize((i.width * S, i.height * S), Image.NEAREST), (x, 0))
    sh.paste(i.resize((i.width * 2, i.height * 2), Image.NEAREST), (x, Hh + 10)); sh.paste(i, (x + i.width * 2 + 10, Hh + 10))
    x += i.width * S + 10
sh.save(f'{H}/png/zoom.png'); print(sh.size)
