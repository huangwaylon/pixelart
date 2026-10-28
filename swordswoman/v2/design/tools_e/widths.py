"""widths.py img frac... : for each fraction of figure height (top=0, incl. bun), print the runs (start,len) of figure pixels, in units of figure height."""
import sys, numpy as np
from PIL import Image
x = np.array(Image.open(sys.argv[1]).convert('RGB')).astype(int)
m = (x.min(-1) < 225) | (x.max(-1) - x.min(-1) > 25); ys, xs = np.where(m); t, b = ys.min(), ys.max(); H = b - t
for f in map(float, sys.argv[2:]):
    y = t + round(f / 100 * H); row = m[y]; runs = []; i = 0
    while i < len(row):
        if row[i]:
            j = i
            while j < len(row) and row[j]: j += 1
            if j - i > 2: runs.append((round((i - xs.min()) / H * 100, 1), round((j - i) / H * 100, 1)))
            i = j
        else: i += 1
    print(f, runs)
