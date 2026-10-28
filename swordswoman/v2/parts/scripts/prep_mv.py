# prep_mv.py OUTDIR front=SRC[:flip][:neck] left=... back=...
# Multi-view prep for Hunyuan 2mv parts: rembg (isnet-anime), optional horizontal flip, optional crop above the neck
# (for head from the full turnD views), then put every view at the SAME pixel scale (equal part height) and add
# alpha=1 sentinel pixels at the corners of one shared square box, so Hunyuan's per-image recenter() keeps the
# relative extents between views (otherwise a wide-short part gets a different scale in front vs side).
import sys, os, numpy as np
from PIL import Image
from rembg import remove, new_session
od = sys.argv[1]; os.makedirs(od, exist_ok=True)
sess = new_session("isnet-anime")
views = {}
for a in sys.argv[2:]:
    k, spec = a.split('=', 1); src, *opts = spec.split(':')
    im = Image.open(src).convert('RGB')
    rgba = remove(im, session=sess); al = np.asarray(rgba)[..., 3]
    if 'neck' in opts:  # cut at the narrowest row between 30% and 60% of the figure height (the neck)
        ys = np.nonzero(al.max(1) > 20)[0]; t, b = ys.min(), ys.max()
        w = np.array([np.count_nonzero(al[r] > 20) for r in range(al.shape[0])])
        lo, hi = int(t + 0.33 * (b - t)), int(t + 0.6 * (b - t)); r = lo + int(np.argmin(w[lo:hi]))
        A = np.asarray(rgba).copy(); A[r:, :, 3] = 0; rgba = Image.fromarray(A); print(k, 'neck cut row', r)
    a2 = rgba.split()[3].point(lambda v: 0 if v < 30 else v); rgba.putalpha(a2)
    rgba = rgba.crop(rgba.getbbox())
    if 'flip' in opts: rgba = rgba.transpose(Image.FLIP_LEFT_RIGHT)
    views[k] = rgba
H = 560  # common part height in px (shrunk if the widest view would exceed 600 px)
mw = max(v.width * H / v.height for v in views.values())
if mw > 600: H = int(H * 600 / mw)
for k in views:
    v = views[k]; views[k] = v.resize((max(1, round(v.width * H / v.height)), H), Image.LANCZOS)
S = 768; side = max(max(v.width for v in views.values()), H)
for k, v in views.items():
    c = Image.new('RGBA', (S, S), (255, 255, 255, 0)); c.paste(v, ((S - v.width) // 2, (S - v.height) // 2), v)
    A = np.asarray(c).copy(); x0 = y0 = (S - side) // 2; x1 = y1 = x0 + side - 1
    for (yy, xx) in ((y0, x0), (y1, x1), (y0, x1), (y1, x0)):
        if A[yy, xx, 3] == 0: A[yy, xx] = (255, 255, 255, 1)
    Image.fromarray(A).save(f'{od}/{k}.png'); print('prep', k, v.size, 'box', side)
