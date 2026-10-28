"""hair-tone bbox of a sprite (scale calibration of Gemini poses against the S3 cel head)."""
import sys, json
import numpy as np
from PIL import Image
P = json.load(open('docs/palette.json'))['ramps']['hair']
def hx(h): return tuple(int(h[i:i+2], 16) for i in (1, 3, 5))
def hair_bbox(p):
    a = np.array(Image.open(p).convert('RGBA'))
    m = np.zeros(a.shape[:2], bool)
    for h in P: m |= np.all(a[..., :3] == hx(h), -1) & (a[..., 3] > 0)
    ys, xs = np.nonzero(m)
    # drop isolated hair-tone px far below the main mass (e.g. corset confusions)
    y_med = np.median(ys); keep = ys < y_med + 20
    ys, xs = ys[keep], xs[keep]
    return xs.min(), ys.min(), xs.max(), ys.max(), int(m.sum())
if __name__ == '__main__':
    for p in sys.argv[1:]:
        x0, y0, x1, y1, n = hair_bbox(p); print(f'{p.split("/")[-1]:40s} w {x1-x0+1:3d} h {y1-y0+1:3d} n {n}')
