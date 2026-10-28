"""hwarp.py in out halfw_frac f0:k0 f1:k1 ... : row-dependent horizontal warp. Within |x-cx| < halfw (fraction of figure height) pixels are
scaled by k(row) about the centre column; outside, they are translated by (k-1)*halfw (arms keep their width). k is linearly interpolated
between the (row fraction, k) keys (top=0 incl. bun) and is 1 outside the key range."""
import sys, numpy as np
from PIL import Image
src, out, hw = sys.argv[1], sys.argv[2], float(sys.argv[3]); keys = [tuple(map(float, s.split(':'))) for s in sys.argv[4:]]
im = Image.open(src).convert('RGB'); x = np.array(im); H0, W0 = x.shape[:2]
m = (x.min(-1) < 225) | (np.ptp(x, -1) > 25); ys, xs = np.where(m); t, b = ys.min(), ys.max(); Hf = b - t
cx = (xs[(ys > t + 0.4 * Hf) & (ys < t + 0.6 * Hf)].min() + xs[(ys > t + 0.4 * Hf) & (ys < t + 0.6 * Hf)].max()) / 2
kf, kk = np.array([k[0] for k in keys]), np.array([k[1] for k in keys]); hwp = hw * Hf
pad = int(0.15 * Hf); o = np.full((H0, W0 + 2 * pad, 3), 255, np.uint8); X = np.arange(W0 + 2 * pad) - pad
for y in range(H0):
    f = (y - t) / Hf; k = np.interp(f, kf, kk) if kf.min() <= f <= kf.max() else 1.0
    d = X - cx; ad = np.abs(d)
    src_d = np.where(ad < k * hwp, d / k, np.sign(d) * (ad - (k - 1) * hwp))   # inverse map
    sx = np.clip(np.round(cx + src_d).astype(int), 0, W0 - 1); inside = (cx + src_d >= 0) & (cx + src_d < W0)
    o[y] = np.where(inside[:, None], x[y, sx], 255)
Image.fromarray(o).save(out); print("wrote", out, o.shape)
