"""ascii dump with STD pixgrid chars: asc.py IMG x0 y0 x1 y1 (inclusive)"""
import sys, os
sys.path.insert(0, '/Users/waylonhuang/Documents/other/pixelart/swordswoman/tools/hybrid')
import numpy as np
from PIL import Image
import pixgrid as PG, hylib as H
pal = H.palette()
rev = {}
for ch, n in PG.STD.items():
    if n == 'transparent': continue
    rgb = tuple(pal.rgba(pal.resolve(n))[:3]); rev.setdefault(rgb, ch)
a = np.array(Image.open(sys.argv[1]).convert('RGBA'))
x0, y0, x1, y1 = map(int, sys.argv[2:6])
print('    ' + ''.join(str((x // 10) % 10) for x in range(x0, x1 + 1)))
print('    ' + ''.join(str(x % 10) for x in range(x0, x1 + 1)))
for y in range(y0, y1 + 1):
    print('%3d ' % y + ''.join('.' if a[y, x, 3] == 0 else rev.get(tuple(a[y, x, :3]), '?') for x in range(x0, x1 + 1)))
