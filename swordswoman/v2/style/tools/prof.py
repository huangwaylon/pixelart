# prof.py path[@x,y,w,h][/2] : per-row profile: silhouette span/width, skin runs, dark runs ("#")
import sys, numpy as np
from PIL import Image
spec = sys.argv[1]; half = spec.endswith('/2'); spec = spec[:-2] if half else spec
crop = None
if '@' in spec: spec, c = spec.split('@'); crop = tuple(map(int, c.split(',')))
src = Image.open(spec); im = src.convert('RGBA')
if src.mode == 'P' and 'transparency' not in src.info:
    a = np.array(im); a[np.array(src) == 0, 3] = 0; im = Image.fromarray(a)
if crop: x, y, w, h = crop; im = im.crop((x, y, x + w, y + h))
if half: im = im.resize((im.width // 2, im.height // 2), Image.NEAREST)
a = np.array(im).astype(int); op = a[..., 3] > 0; ys, xs = np.where(op); a = a[ys.min():ys.max()+1, xs.min():xs.max()+1]; op = op[ys.min():ys.max()+1, xs.min():xs.max()+1]
r, g, b = a[..., 0], a[..., 1], a[..., 2]
skin = op & (r > 190) & (r > g + 15) & (g > b) & (g > 130) & (b > 90) & (r - b < 120)
for y in range(a.shape[0]):
    row = ''.join('s' if skin[y, x] else ('#' if op[y, x] and a[y, x, :3].sum() < 90 else ('o' if op[y, x] else '.')) for x in range(a.shape[1]))
    xx = np.where(op[y])[0]
    print(f"{y:3d} w={len(xx):2d} {row}")
