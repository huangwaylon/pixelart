"""Pixel readability probe: crop subject, box-downsample to N px tall, quantize, show at 6x on mid-grey.
Usage: probe.py out.png img1 [img2 ...] [--h 40,48,56] [--colors 16]"""
import sys, numpy as np
from PIL import Image, ImageDraw
args = sys.argv[1:]; hs = [40, 48, 56]; nc = 16
if '--h' in args: i = args.index('--h'); hs = [int(v) for v in args[i+1].split(',')]; del args[i:i+2]
if '--colors' in args: i = args.index('--colors'); nc = int(args[i+1]); del args[i:i+2]
out, imgs = args[0], args[1:]
def subject(path):
    im = Image.open(path).convert('RGBA'); a = np.array(im).astype(float)
    if a[..., 3].min() < 250: m = a[..., 3] > 128
    else: m = (a[..., :3].min(-1) < 200) | (a[..., :3].max(-1) - a[..., :3].min(-1) > 40)  # non-white
    ys, xs = np.where(m); box = (xs.min(), ys.min(), xs.max()+1, ys.max()+1)
    rgb = im.convert('RGB'); arr = np.array(rgb); arr[~m] = 255
    return Image.fromarray(arr).crop(box), Image.fromarray((m*255).astype(np.uint8)).crop(box)
S = 6; tiles = []
for p in imgs:
    im, m = subject(p); row = []
    for h in hs:
        w = max(1, round(im.width * h / im.height))
        mf = np.array(m).astype(float) / 255; rgbf = np.array(im).astype(float) * mf[..., None]
        num = np.stack([np.array(Image.fromarray(rgbf[..., c].astype(np.float32), 'F').resize((w, h), Image.BOX)) for c in range(3)], -1)
        den = np.array(Image.fromarray(mf.astype(np.float32), 'F').resize((w, h), Image.BOX))
        sm = Image.fromarray(np.clip(num / np.maximum(den, 1e-6)[..., None], 0, 255).astype(np.uint8)); mm = den > 0.45
        q = sm.quantize(nc, method=Image.Quantize.MAXCOVERAGE, dither=Image.Dither.NONE).convert('RGB')
        a = np.array(q); a[~mm] = (110, 110, 118)
        row.append(Image.fromarray(a).resize((w*S, h*S), Image.NEAREST))
    W = sum(r.width for r in row) + 20*len(row) + 20; H = max(r.height for r in row) + 40
    t = Image.new('RGB', (W, H), (110, 110, 118)); x = 10
    for r, h in zip(row, hs): t.paste(r, (x, H - 10 - r.height)); x += r.width + 20
    ImageDraw.Draw(t).text((10, 5), p.split('/')[-1] + '  ' + '/'.join(map(str, hs)) + 'px', fill='white')
    tiles.append(t)
W = max(t.width for t in tiles); H = sum(t.height for t in tiles)
sheet = Image.new('RGB', (W, H), (110, 110, 118)); y = 0
for t in tiles: sheet.paste(t, (0, y)); y += t.height
sheet.save(out); print(out, sheet.size)
