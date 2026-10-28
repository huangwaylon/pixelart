# qa_col.py PREFIX VIEW SHIFT COL[,COL] : run-lengths of materials down columns, rig (shifted down by SHIFT) vs master codes
import sys, numpy as np
from PIL import Image
pre, v, sh, cols = sys.argv[1], sys.argv[2], int(sys.argv[3]), [int(c) for c in sys.argv[4].split(',')]
MT = '/Users/waylonhuang/Documents/other/pixelart/swordswoman/v2/m96/masters/EC0_{}_96.txt'
MATS = {'hair': (61, 50, 53), 'dress': (192, 59, 61), 'skin': (248, 218, 194), 'sleeve': (142, 34, 44), 'socks': (38, 42, 71),
        'boots': (42, 34, 42), 'bow': (232, 96, 79), 'obi': (69, 56, 73), 'eyes': (85, 128, 162)}
MN = list(MATS); MC = np.array([MATS[k] for k in MN], float); AB = {'hair': 'H', 'dress': 'E', 'skin': 's', 'sleeve': 'e', 'socks': 'D', 'boots': 'b', 'bow': 'w', 'obi': 'O', 'eyes': 'y'}
a = np.asarray(Image.open(f'{pre}_{v}.png').convert('RGBA')).astype(float); k = a.shape[0] // 192
a = a[32 * k:160 * k, 32 * k:160 * k].reshape(128, k, 128, k, 4)[:, k // 2, :, k // 2]
al = a[..., 3] > 127; mid = ((a[..., None, :3] - MC) ** 2).sum(-1).argmin(-1)
g = np.array([list(l.rstrip('\n')) for l in open(MT.format(v)) if l.strip() and not l.startswith(';')])
CL = {**{c: 'H' for c in 'hHgL'}, **{c: 's' for c in 'sSmk'}, **{c: 'E' for c in 'ReE'}, **{c: 'O' for c in 'oOQ'}, 'D': 'D', 'd': 'D', 'W': 'y', 'K': 'K', '.': '.'}
def rle(s):
    out = []; i = 0
    while i < len(s):
        j = i
        while j < len(s) and s[j] == s[i]: j += 1
        out.append(f'{s[i]}{i}-{j-1}'); i = j
    return ' '.join(x for x in out if not x.startswith('.'))
for c in cols:
    r = ['.'] * 128
    for y in range(128):
        yy = y - sh
        if 0 <= yy < 128 and al[yy, c]: r[y] = AB[MN[mid[yy, c]]]
    m = [CL.get(ch, '?') for ch in g[:, c]]
    print('col', c, '\n rig', rle(r), '\n mst', rle(m))
