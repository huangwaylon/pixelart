"""Crop the head (top of the figure down to the neck = narrowest row between 22% and 50% of the height) from a
prepared RGBA input (prep.py output). Writes OUT.png (RGBA square, same margins as prep.py) and prints the head
fraction of the full height + bbox aspect.
Usage: venv/bin/python -I head_crop.py IN.png OUT.png [--pad 0.02]
"""
import sys, json
import numpy as np
from PIL import Image
src, out = sys.argv[1:3]
im = np.asarray(Image.open(src).convert('RGBA')); m = im[..., 3] > 127
ys, xs = np.nonzero(m); t, b = ys.min(), ys.max(); H = b - t
w = m.sum(1)
lo, hi = int(t + 0.22 * H), int(t + 0.5 * H)
neck = lo + int(np.argmin(w[lo:hi]))
cut = neck + int(0.02 * H)
sub = im[t:cut].copy()
# keep only the central component columns of the head (drop hands that might reach up: none in A-pose)
mm = sub[..., 3] > 127; cx = np.nonzero(mm.any(0))[0]
sub = sub[:, cx.min():cx.max() + 1]
h, ww = sub.shape[:2]; side = int(max(h, ww) / 0.9)
c = np.zeros((side, side, 4), np.uint8); c[(side - h) // 2:(side - h) // 2 + h, (side - ww) // 2:(side - ww) // 2 + ww] = sub
Image.fromarray(c).resize((1024, 1024), Image.LANCZOS).save(out)
print(json.dumps(dict(head_frac=round((cut - t) / H, 3), neck_frac=round((neck - t) / H, 3), aspect_w_h=round(ww / h, 3))))
