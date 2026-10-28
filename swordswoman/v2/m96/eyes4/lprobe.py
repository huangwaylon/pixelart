# lprobe.py STEM VIEW: print illustration L (ref, as 0-9 dark->light) vs sprite chars over the eye band (128-cell coords)
import sys, numpy as np
sys.path.insert(0, '/Users/waylonhuang/Documents/other/pixelart/swordswoman/v2/pixelize/tools')
import metrics as MX, pzlib as Z
stem, v = sys.argv[1:3]; g, meta = Z.read(stem); keys, rgb, _ = Z.load_pal(meta['pal'])
h, w, ox, oy = meta['h'], meta['w'], meta['ox'], meta['oy']; R = MX.ref(meta['view'], meta['src'], h, w)
lb = Z.rgb2lab(R['lo'].astype(float))[..., 0]
P = np.full((h, w, 3), 255.)
for i, k in enumerate(keys): P[g[oy:oy + h, ox:ox + w] == k] = rgb[i]
la = Z.rgb2lab(P)[..., 0]
X = {'S': (52, 76), 'SE': (58, 80), 'E': (66, 82)}[v]
for y in range(46, 56):
    r = y - oy
    print(y, ''.join(str(min(9, int(lb[r, x - ox] / 10))) for x in range(*X)), ''.join(str(min(9, int(la[r, x - ox] / 10))) for x in range(*X)), ''.join(g[y, X[0]:X[1]]))
