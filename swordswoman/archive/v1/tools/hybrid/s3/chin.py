"""Auto chin (collar-top) + sole detection on hires images; writes hires/<name>_chin.json and a check sheet."""
import sys, json
import numpy as np
sys.path.insert(0, 'tools/hybrid')
import pixelize as PX, hylib as H
from PIL import Image, ImageDraw
R = 'hybrid/S3_editchain/r1/hires'
def detect(name):
    img = Image.open(f'{R}/{name}.png'); rgb, mask, _ = PX.remove_bg(img, 'auto', 11.0)
    k = 2; sm = rgb[::k, ::k].astype(float); m = mask[::k, ::k]
    cls, _ = H.classify(sm)
    ys, xs = np.nonzero(m); y0, y1 = ys.min(), ys.max()
    hair = (cls == H.BASE.index('hair')) & m
    hz = hair.copy(); hz[int(y0 + 0.6 * (y1 - y0)):] = False
    lab, sz = PX.label_cc(hz, 8); i = int(np.argmax(sz[1:]) + 1)
    hy, hx = np.nonzero(lab == i)
    cy, cx = hy.mean(), np.median(hx); half = max(4, int(0.12 * (hx.max() - hx.min())))
    red = (cls == H.BASE.index('red')) & m
    chin = None
    for y in range(int(cy), int(y1)):
        band = red[y, int(cx - half):int(cx + half)]
        if band.mean() > 0.5:
            chin = y; break
    geo = PX.body_rows(rgb, mask)
    d = dict(chin=int(chin * k), head_cx=float(cx * k), hair_top=int(hy.min() * k), sole=int(geo['bottom']),
             head_w=float((np.percentile(hx, 99.5) - np.percentile(hx, .5)) * k))
    json.dump(d, open(f'{R}/{name}_chin.json', 'w')); return d, img.convert('RGB')
tiles = []
for n in sys.argv[1:]:
    d, im = detect(n); print(n, d)
    dr = ImageDraw.Draw(im)
    for key, c in (('chin', (0, 160, 255)), ('hair_top', (0, 200, 0)), ('sole', (255, 0, 255))):
        dr.line([(0, d[key]), (im.width, d[key])], fill=c, width=5)
    s = 420 / im.height; tiles.append(im.resize((int(im.width * s), 420)))
W = Image.new('RGB', (sum(t.width for t in tiles), 420), 'white'); x = 0
for t in tiles: W.paste(t, (x, 0)); x += t.width
W.save('/tmp/chin.png')
