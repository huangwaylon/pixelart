"""vremap.py in out f0:f1:k ... : piecewise vertical rescale of the cropped figure; each band [f0,f1] (fractions of figure height) scaled by k, others 1."""
import sys, numpy as np
from PIL import Image
src, out = sys.argv[1], sys.argv[2]; bands = [tuple(map(float, s.split(':'))) for s in sys.argv[3:]]
im = Image.open(src).convert('RGB'); x = np.array(im).astype(int)
m = (x.min(-1) < 225) | (x.max(-1) - x.min(-1) > 25); ys, xs = np.where(m)
fig = im.crop((xs.min() - 20, ys.min(), xs.max() + 21, ys.max() + 1)); W, H = fig.size
cuts = sorted({0.0, 1.0} | {f for b in bands for f in b[:2]}); pieces = []
for a, b in zip(cuts[:-1], cuts[1:]):
    k = next((bb[2] for bb in bands if bb[0] <= a and b <= bb[1]), 1.0)
    p = fig.crop((0, round(a * H), W, round(b * H))); pieces.append(p.resize((W, max(1, round(p.height * k))), Image.LANCZOS))
c = Image.new('RGB', (W + 40, sum(p.height for p in pieces) + 40), 'white'); y = 20
for p in pieces: c.paste(p, (20, y)); y += p.height
c.save(out); print(out, c.size)
