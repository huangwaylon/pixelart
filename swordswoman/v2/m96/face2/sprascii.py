import sys, json, numpy as np
sys.path.insert(0, '/Users/waylonhuang/Documents/other/pixelart/swordswoman/v2/pixelize/tools'); import pzlib as Z
v, x0, x1, y0, y1 = sys.argv[1], *map(int, sys.argv[2:6]); sub = 4
meta = json.load(open(f'/Users/waylonhuang/Documents/other/pixelart/swordswoman/v2/m96/masters/EC0_{v}_96.json'))
x, m = Z.load(v, meta['src']); Hh, Ww = m.shape
fx = lambda X: (X - meta['ox']) * Ww / meta['w']; fy = lambda Y: (Y - meta['oy']) * Hh / meta['h']
print('     ' + ''.join(f'{c%100:<4d}' if c % 2 == 0 else '    ' for c in range(x0, x1)))
for ys in np.arange(y0, y1, 1 / sub):
    Y = int(fy(ys + 0.125)); row = ''
    for xs in np.arange(x0, x1, 0.5):
        X = int(fx(xs + 0.25)); p = x[min(Y, Hh - 1), min(X, Ww - 1)]
        mx = p.max(); r, g, b = p
        ch = ' ' if p.min() > 235 else '#' if mx < 85 else 'o' if mx < 150 else 'b' if (r - g) > 75 else ':' if (r - g) > 62 else '.'
        row += ch
    print(f'{ys:5.2f} ' + row)
