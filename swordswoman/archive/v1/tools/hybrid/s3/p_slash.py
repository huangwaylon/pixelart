import sys; sys.path.insert(0, 'tools/hybrid/s3')
import numpy as np
from pol import *
R = 'hybrid/S3_editchain/r1'
BODY = set('rvRClLsmSdhH')
def erase_smear(a, cx, cy, rx, ry, r0=0.7, r1=1.35, ymin=0, keep=None):
    H, W = a.shape[:2]
    c = chars(a)
    for y in range(ymin, H):
        for x in range(W):
            r = np.hypot((x - cx) / rx, (y - cy) / ry)
            if not (r0 <= r <= r1) or (keep is not None and keep[y, x]): continue
            if c[y, x] in 'pP': a[y, x] = 0
    c = chars(a)
    for y in range(ymin, H):
        for x in range(W):
            r = np.hypot((x - cx) / rx, (y - cy) / ry)
            if not (r0 <= r <= r1) or c[y, x] not in 'KwS' or (keep is not None and keep[y, x]): continue
            nb = c[max(0, y-1):y+2, max(0, x-1):x+2]
            if not any(ch_ in BODY for ch_ in nb.ravel()): a[y, x] = 0
    return a
if __name__ == '__main__':
    k = sys.argv[1]
    a = load(f'{R}/sprite_px/slash_SE_{k}_rt.png')
    if k == 'k1':
        a = erase_smear(a, 75, 80, 41, 20.5, keep=stamp_mask(f'{R}/sprite_px/slash_SE_k1_meta.json', 'SE'))
    save(a, f'{R}/wip/pol/slash_SE_{k}_e.png')
