"""bighead2.py in out chin_frac crop_frac k : scale the head (rows above crop_frac, non-red pixels only) by k about the chin point and paste it over the full original body (shifted down). Avoids seams: body keeps its collar; head keeps hair tips."""
import sys, numpy as np
from PIL import Image
src, out, cf, sf, k = sys.argv[1], sys.argv[2], float(sys.argv[3]), float(sys.argv[4]), float(sys.argv[5])
im = Image.open(src).convert('RGB'); x = np.array(im).astype(int)
m = (x.min(-1) < 225) | (x.max(-1) - x.min(-1) > 25); ys, xs = np.where(m); t, b = ys.min(), ys.max(); l, r = xs.min(), xs.max()
x = x[t:b+1, l:r+1]; m = m[t:b+1, l:r+1]; H, W = m.shape; cy = round(cf * H); sy = round(sf * H)
red = (x[..., 0] > 110) & (x[..., 0] > x[..., 1] + 50) & (x[..., 0] > x[..., 2] + 30)
hm = m.copy(); hm[sy:] = False
# keep red only in the bow zone (top 25% of the head) so the collar stays from the body layer
hm[int(0.6 * cy):sy] &= ~red[int(0.6 * cy):sy]
from scipy.ndimage import binary_fill_holes
hm[:sy] = binary_fill_holes(hm[:sy])  # light face pixels are not 'figure'; fill so nothing shows through
cxs = np.where(m[cy])[0]; cx = cxs.mean()
fig = Image.fromarray(x.astype(np.uint8)); head = fig.crop((0, 0, W, sy)); hmask = Image.fromarray((hm[:sy] * 255).astype(np.uint8))
HW, HH = round(W * k), round(sy * k); head = head.resize((HW, HH), Image.LANCZOS); hmask = hmask.resize((HW, HH), Image.LANCZOS)
dy = round(cy * (k - 1)); pad = round(W * (k - 1) / 2) + 20
c = Image.new('RGB', (W + 2 * pad, H + dy + 40), 'white')
bm = m & ~hm if k < 1 else m  # shrinking: drop the old head from the body layer so its outline does not ghost
c.paste(fig, (pad, 20 + dy), Image.fromarray((bm * 255).astype(np.uint8)))
c.paste(head, (round(pad + cx - cx * k), 20), hmask)
c.save(out); print(out, c.size)
