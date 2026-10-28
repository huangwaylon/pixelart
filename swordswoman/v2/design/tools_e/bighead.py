"""bighead.py in out split_frac k [wscale] : scale everything above split (fraction of figure height from top) by k, anchored at the split-row centre, over the body (optionally widen body by wscale)."""
import sys, numpy as np
from PIL import Image
src, out, sf, k = sys.argv[1], sys.argv[2], float(sys.argv[3]), float(sys.argv[4]); ws = float(sys.argv[5]) if len(sys.argv) > 5 else 1.0
im = Image.open(src).convert('RGB'); x = np.array(im).astype(int)
m = (x.min(-1) < 225) | (x.max(-1) - x.min(-1) > 25); ys, xs = np.where(m); t, b = ys.min(), ys.max(); l, r = xs.min(), xs.max()
fig = im.crop((l, t, r + 1, b + 1)); mk = Image.fromarray((m[t:b+1, l:r+1] * 255).astype(np.uint8))
H, W = b - t + 1, r - l + 1; sy = round(sf * H)
body = fig.crop((0, sy, W, H)); bm = mk.crop((0, sy, W, H))
if ws != 1: body = body.resize((round(W * ws), H - sy), Image.LANCZOS); bm = bm.resize(body.size, Image.LANCZOS)
cxs = np.where(m[t + sy - 1, l:r+1])[0]; cx = cxs.mean() if len(cxs) else W / 2
head = fig.crop((0, 0, W, sy)).resize((round(W * k), round(sy * k)), Image.LANCZOS); hm = mk.crop((0, 0, W, sy)).resize(head.size, Image.LANCZOS)
CW = max(head.width, body.width) + 40; CH = head.height + body.height + 40
c = Image.new('RGB', (CW, CH), 'white'); bx = (CW - body.width) // 2; c.paste(body, (bx, 20 + head.height), bm)
hx = round(bx + cx * ws - cx * k); c.paste(head, (hx, 20), hm)
c.save(out); print(out, c.size)
