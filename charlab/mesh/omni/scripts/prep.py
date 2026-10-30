"""Prepare Omni input images from a concept sheet or a reference image.

Usage: venv/bin/python -I prep.py SRC.png OUT.png [--view left|right|full] [--size 1024]
Crops one view, mattes the white background to alpha by flood fill from the border (outlines are dark, so
white garments enclosed by an outline survive), crops to the subject and pads to a square RGBA image.
Also writes OUT_mask.png (binary silhouette, same framing) for IoU metrics.
"""
import argparse
import numpy as np
from PIL import Image
from scipy import ndimage

ap = argparse.ArgumentParser()
ap.add_argument('src'); ap.add_argument('out')
ap.add_argument('--view', default='left'); ap.add_argument('--size', type=int, default=1024)
ap.add_argument('--thr', type=int, default=22, help='max distance from white for background')
a = ap.parse_args()

im = Image.open(a.src)
if im.mode == 'RGBA' and np.asarray(im)[..., 3].min() < 250:
    rgba = np.asarray(im).copy()
    fg = rgba[..., 3] > 127
else:
    rgb = np.asarray(im.convert('RGB')).astype(int)
    W = rgb.shape[1]
    if a.view == 'left':
        rgb = rgb[:, :W // 2]
    elif a.view == 'right':
        rgb = rgb[:, W // 2:]
    near_white = (255 - rgb).max(2) <= a.thr
    lab, _ = ndimage.label(near_white)
    border = np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]]))
    bg = np.isin(lab, border[border > 0])
    fg = ~bg
    # keep the largest component(s): drop specks
    lab2, n = ndimage.label(fg)
    if n > 1:
        sizes = ndimage.sum(fg, lab2, range(1, n + 1))
        keep = np.nonzero(sizes > 0.002 * sizes.max())[0] + 1
        fg = np.isin(lab2, keep)
    fg = ndimage.binary_fill_holes(fg)
    alpha = ndimage.gaussian_filter(fg.astype(float), 0.6)
    rgba = np.dstack([rgb, np.clip(alpha * 255, 0, 255)]).astype(np.uint8)
ys, xs = np.nonzero(fg)
t, b, l, r = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
crop = rgba[t:b, l:r]
h, w = crop.shape[:2]
side = int(max(h, w) / 0.9)  # 5% margin each side
canvas = np.zeros((side, side, 4), np.uint8)
y0, x0 = (side - h) // 2, (side - w) // 2
canvas[y0:y0 + h, x0:x0 + w] = crop
out = Image.fromarray(canvas).resize((a.size, a.size), Image.LANCZOS)
out.save(a.out)
m = (np.asarray(out)[..., 3] > 127).astype(np.uint8) * 255
Image.fromarray(m).save(a.out.replace('.png', '_mask.png'))
print('prep', a.out, 'subject h/w', h, w, 'aspect w/h %.3f' % (w / h))
