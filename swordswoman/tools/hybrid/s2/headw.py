"""skull width per slice: widest row of dark-brunette hair pixels (+ skin face row band), robust to sleeves/ribbons."""
import sys, numpy as np
from PIL import Image
from scipy import ndimage as ndi
for p in sys.argv[1:]:
    a = np.asarray(Image.open(p).convert('RGB')).astype(float)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    mx = a.max(-1); mn = a.min(-1)
    hair = (mx < 120) & (r >= b - 5) & (r - b < 45) & (mx - mn < 50)
    hair = ndi.binary_opening(hair, iterations=2)
    lab, n = ndi.label(hair)
    if n == 0: print(p, 0); continue
    sz = ndi.sum(hair, lab, range(1, n + 1)); k = int(np.argmax(sz)) + 1
    m = lab == k
    m = ndi.binary_closing(m, iterations=6)
    ys, xs = np.nonzero(m)
    w = max((np.ptp(np.nonzero(row)[0]) + 1) if row.any() else 0 for row in m)
    print(p.split('/')[-1], 'skull_w', w, 'hair_h', np.ptp(ys) + 1)
