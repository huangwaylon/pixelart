#!/usr/bin/env python3
"""sheet.py OUT.png [suffix]  : 5 views (S SE E NE N) at 1x + 4x with height lines + refs (hilda-bw, PMD 0475 SE idle) at same scale.
Prints per-view metrics: top row, crown row (first H row), chin (lowest s row above neck), feet row, head width."""
import sys
sys.path.insert(0, '/Users/waylonhuang/Documents/other/pixelart/swordswoman/v2/masters/tools')
from mm import read, render, V2
from PIL import Image, ImageDraw
VIEWS = ['S', 'SE', 'E', 'NE', 'N']
suf = sys.argv[2] if len(sys.argv) > 2 else ''
def metrics(g):
    rows = [y for y, r in enumerate(g) if r.strip('.')]
    top, feet = rows[0], rows[-1]
    crown = next(y for y, r in enumerate(g) if sum(c in 'HLh' for c in r) >= 8)
    chin = next(y for y in range(crown + 8, 64) if sum(c in 'eERr' for c in g[y]) >= 4) - 1  # row above the collar
    hw = max((len(r.rstrip('.').replace('K', '.').strip('.')) for r in g[crown:crown+14] if ('H' in r)), default=0)
    return top, crown, chin, feet, hw
S = int(sys.argv[3]) if len(sys.argv) > 3 else 4
gs = {v: read(f'{V2}/masters/{v}{suf}.txt') for v in VIEWS}
refs = []
h = Image.open(f'{V2}/style/refs/battle/hilda-bw.png').convert('RGBA'); refs.append(h)
p = Image.open(f'{V2}/style/refs/pmd/0475_Idle.png').convert('RGBA'); refs.append(p.crop((0, 64, 24, 128)))
W = 64 * S * 5 + sum(r.width * S for r in refs) + 20 * 7
Hh = 64 * S + 64 + 40
im = Image.new('RGBA', (W, Hh), (110, 110, 110, 255)); d = ImageDraw.Draw(im)
x = 10; ms = {}
for v in VIEWS:
    g = gs[v]; ms[v] = metrics(g)
    im.alpha_composite(render(g, S), (x, 30)); im.alpha_composite(render(g, 1), (x, 64 * S + 34))
    d.text((x, 8), v + suf, fill='white'); x += 64 * S + 20
for r in refs:
    big = r.resize((r.width * S, r.height * S), Image.NEAREST)
    im.alpha_composite(big, (x, 30 + 64 * S - big.height)); im.alpha_composite(r, (x, 64 * S + 34 + 64 - r.height)); x += big.width + 20
top, crown, chin, feet, hw = ms['SE']
for yy, col in ((crown, (0, 255, 255, 255)), (crown + 14, (255, 255, 0, 255)), (feet + 1, (255, 0, 255, 255))):
    d.line([(0, 30 + yy * S), (W, 30 + yy * S)], fill=col, width=1)
im.save(sys.argv[1])
for v in VIEWS: print(v, 'top crown chin feet headw =', ms[v])
