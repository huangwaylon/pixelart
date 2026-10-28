"""Re-tone the red dress by hi-res luminance rank so every sprite shares one tone mix
(C 3 %, R 50 %, r 37 %, v 10 %) -> fixes per-image Gemini exposure drift. Writes sprite_px/<n>_rt.png"""
import sys, glob, os; sys.path.insert(0, 'tools/hybrid/s3')
import numpy as np
from PIL import Image
from pol import *
R = 'hybrid/S3_editchain/r1'
HD = lambda n: n.split('_')[1] if n.startswith('turn_') else ('E' if n.startswith('jump_E') else 'SE')
MIX = [('C', 0.03), ('R', 0.50), ('r', 0.37), ('v', 0.10)]
for p in sorted(glob.glob(f'{R}/sprite_px/*_meta.json')):
    n = os.path.basename(p)[:-10]
    a = load(f'{R}/sprite_px/{n}.png'); M = stamp_mask(p, HD(n))
    hi = np.array(Image.open(f'{R}/sprite_px/{n}_hires.png').convert('RGB')).astype(float)
    lum = (0.2126 * hi[..., 0] + 0.7152 * hi[..., 1] + 0.0722 * hi[..., 2]).reshape(128, 4, 128, 4).mean((1, 3))
    c = chars(a)
    red = np.isin(c, list('vrRC')) & ~M
    ys, xs = np.nonzero(red)
    order = np.argsort(-lum[ys, xs])
    k = 0
    for ch_, f in MIX:
        m = int(round(f * len(order))) if ch_ != 'v' else len(order) - k
        for i in order[k:k + m]: put(a, xs[i], ys[i], ch_)
        k += m
    save(a, f'{R}/sprite_px/{n}_rt.png')
print('ok')
