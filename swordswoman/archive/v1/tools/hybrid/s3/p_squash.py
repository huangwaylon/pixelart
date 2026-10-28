"""squash the body (non-stamp) of a sprite around its bottom-centre: sy<1 shorter, sx>1 wider; head stamp re-pasted lower by the height loss * k."""
import sys, json; sys.path.insert(0, 'tools/hybrid/s3')
import numpy as np
from pol import *
def squash(src, meta, headdir, sx, sy, out, head_drop=None):
    a = load(src); M = stamp_mask(meta, headdir)
    m = json.load(open(meta))['s3']
    st = a.copy(); st[~M] = 0
    body = a.copy(); body[M] = 0
    ys, xs = np.nonzero(body[..., 3] > 0)
    bot = ys.max(); cx = (xs.min() + xs.max()) / 2
    chin = m['stamp_top'] + 33
    res = np.zeros_like(a)
    for y in range(128):
        for x in range(128):
            srcy = bot - (bot - y) / sy
            srcx = cx + (x - cx) / sx
            iy, ix = int(round(srcy)), int(round(srcx))
            if 0 <= iy < 128 and 0 <= ix < 128 and body[iy, ix, 3] > 0:
                res[y, x] = body[iy, ix]
    drop = int(round((bot - chin) * (1 - sy))) if head_drop is None else head_drop
    st2 = np.zeros_like(st); st2[drop:] = st[:128 - drop] if drop > 0 else st
    Ms = st2[..., 3] > 0
    res[Ms] = st2[Ms]
    save(res, out); return drop
if __name__ == '__main__':
    src, meta, hd, sx, sy, out = sys.argv[1:7]
    print('drop', squash(src, meta, hd, float(sx), float(sy), out))
