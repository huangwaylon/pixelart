"""onion.py OUT a.png b.png ... : each frame at 6x with the PREVIOUS frame's silhouette edge in cyan (motion check)
+ prints per-frame crown row, bow top/centre, lowest row, feet centre, sword tip."""
import sys
import numpy as np
from PIL import Image
from scipy import ndimage
out, fs = sys.argv[1], sys.argv[2:]
A = [np.array(Image.open(f).convert('RGBA')) for f in fs]
z = 6; crop = (30, 34, 100, 108)
x0, y0, x1, y1 = crop
tiles = []
for i, a in enumerate(A):
    p = A[i - 1]
    m = p[..., 3] > 0
    edge = m & ~ndimage.binary_erosion(m)
    rgb = np.full(a.shape[:2] + (3,), 118, np.uint8)
    al = a[..., 3:4] / 255.0
    rgb = (rgb * (1 - al) + a[..., :3] * al).astype(np.uint8)
    rgb[edge & (a[..., 3] == 0)] = (0, 220, 255)
    rgb[edge & (a[..., 3] > 0)] = (rgb[edge & (a[..., 3] > 0)] * 0.5 + np.array([0, 110, 128])).astype(np.uint8)
    t = Image.fromarray(rgb[y0:y1, x0:x1]).resize(((x1 - x0) * z, (y1 - y0) * z), Image.NEAREST)
    tiles.append(t)
    red = np.isin(a[..., 0], [0]) & False
    ys, xs = np.nonzero(a[..., 3])
    R, G, B = a[..., 0].astype(int), a[..., 1].astype(int), a[..., 2].astype(int)
    redm = (a[..., 3] > 0) & (R > 150) & (G < 110) & (B < 110)
    redm[60:] = False
    by, bx = np.nonzero(redm)
    print(fs[i].split('/')[-1], 'crown', ys.min(), 'bow top', by.min() if len(by) else None, 'bow cx', round(bx.mean(), 1) if len(bx) else None, 'low', ys.max())
W = sum(t.width for t in tiles) + 6 * (len(tiles) + 1)
im = Image.new('RGB', (W, tiles[0].height + 12), (36, 32, 44)); x = 6
for t in tiles: im.paste(t, (x, 6)); x += t.width + 6
im.save(out)
