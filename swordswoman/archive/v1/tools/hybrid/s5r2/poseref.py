"""Gemini hi-res pose -> cell-scale POSE REF (scale from the hair area vs the S3 cel head), flipped out of mirror
space, feet on y=104, feet centre on x=64. Writes ref png (palette-nearest, for onion-skin tracing only),
a 6x gridded view with coordinates, and the cropped hi-res (flipped) as <out>_hires.png.
poseref.py GEM.png SNAP.png OUT.png [--s 1.0] [--dx 0] [--dy 0]"""
import sys, json
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, 'tools/hybrid'); sys.path.insert(0, 'tools/hybrid/s5r2'); sys.path.insert(0, 'tools/hybrid/s5')
import hylib as H
from headw import hair_bbox
from snap import is_bg
from scipy import ndimage as ndi
def main(gem, snp, out, s=1.0, dx=0, dy=0):
    n = hair_bbox(snp)[4]
    meta = json.load(open(snp[:-4] + '_meta.json'))
    pitch = meta['pitch'][0]
    scale = s * (410.0 / n) ** 0.5 / pitch           # hi-res px -> cell px
    a = np.array(Image.open(gem).convert('RGB'))[:, ::-1]
    bg = is_bg(a)
    lab, k = ndi.label(~bg)
    sizes = ndi.sum(~bg, lab, range(1, k + 1)); big = lab == (np.argmax(sizes) + 1)
    near = ndi.binary_dilation(big, iterations=30); ids = set(np.unique(lab[near])) - {0}
    fg = np.isin(lab, list(ids))
    ys, xs = np.nonzero(fg); y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    rgba = np.dstack([a, (fg * 255).astype(np.uint8)])[y0:y1, x0:x1]
    hi = Image.fromarray(rgba, 'RGBA'); hi.save(out[:-4] + '_hires.png')
    W, Ht = max(1, round(hi.width * scale)), max(1, round(hi.height * scale))
    sm = np.array(hi.resize((W, Ht), Image.BOX))
    al = sm[..., 3] > 127
    cls, _ = H.classify(sm[..., :3].astype(np.uint8), allowed=None, penalty=6.0)
    q = H.quantize_tones(sm[..., :3].astype(np.uint8), cls); q[~al] = -1
    spr = H.rgba_of(q)
    bot = al[int(Ht * 0.75):]; cx = int(round(np.nonzero(bot)[1].mean())) if bot.any() else W // 2
    cell = np.zeros((128, 128, 4), np.uint8)
    oy, ox = 105 - Ht + dy, 64 - cx + dx
    for j in range(Ht):
        for i in range(W):
            if spr[j, i, 3] and 0 <= oy + j < 128 and 0 <= ox + i < 128: cell[oy + j, ox + i] = spr[j, i]
    Image.fromarray(cell).save(out)
    grid(cell, out[:-4] + '_grid.png')
    print(out, 'scale', round(scale * pitch, 3), 'size', W, Ht)
def grid(cell, path, z=6, box=(16, 16, 112, 112)):
    x0, y0, x1, y1 = box
    c = Image.fromarray(cell).crop(box)
    bgc = Image.new('RGBA', c.size, (90, 140, 70, 255)); bgc.alpha_composite(c)
    im = bgc.resize((c.width * z, c.height * z), Image.NEAREST)
    d = ImageDraw.Draw(im)
    for i in range(0, c.width + 1):
        col = (255, 255, 255, 140) if (x0 + i) % 8 == 0 else (0, 0, 0, 40)
        d.line([(i * z, 0), (i * z, im.height)], fill=col, width=1)
        if (x0 + i) % 8 == 0: d.text((i * z + 1, 1), str(x0 + i), fill='yellow')
    for j in range(0, c.height + 1):
        col = (255, 255, 255, 140) if (y0 + j) % 8 == 0 else (0, 0, 0, 40)
        d.line([(0, j * z), (im.width, j * z)], fill=col, width=1)
        if (y0 + j) % 8 == 0: d.text((1, j * z + 1), str(y0 + j), fill='yellow')
    im.save(path)
if __name__ == '__main__':
    a = sys.argv[1:]; kw = {}
    for k in ('--s', '--dx', '--dy'):
        if k in a: i = a.index(k); kw[k[2:]] = float(a[i + 1]) if k == '--s' else int(a[i + 1]); del a[i:i + 2]
    main(*a, **kw)
