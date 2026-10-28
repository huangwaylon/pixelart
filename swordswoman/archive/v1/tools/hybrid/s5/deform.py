"""Claude pose-seed pass for jump keys: squash/stretch the finished E sprite body (head rigid),
volume-paired (saint11: mass never changes), sole on a chosen row.  -> seed/<name>.png"""
import sys
import numpy as np
from PIL import Image
from common import *

def deform(a, chin, sy, sx, sole_to, cx=64, flare=0):
    rows = np.nonzero(a[..., 3].any(1))[0]; sole = rows.max()
    head = a[:chin]; body = a[chin:sole + 1]
    bh = body.shape[0]; nh = int(round(bh * sy))
    im = Image.fromarray(body)
    nw = int(round(128 * sx))
    b2 = np.array(im.resize((nw, nh), Image.NEAREST))
    # re-centre horizontally on cx
    out = np.zeros_like(a)
    x0 = int(round(cx - cx * sx))
    top = sole_to - nh + 1
    for y in range(nh):
        for x in range(nw):
            X = x + x0
            if 0 <= X < 128 and b2[y, x, 3]: out[top + y, X] = b2[y, x]
    if flare:   # widen the lowest skirt rows outward (bell flare)
        reds = [TRGB[k] for k in ("red_0", "red_1", "red_2", "red_3")]
        for y in range(top + nh - 12, top + nh - 4):
            xs = [x for x in range(128) if out[y, x, 3]]
            if not xs: continue
            l, r = min(xs), max(xs)
            for k in range(1, flare + 1):
                if l - k >= 0: out[y, l - k] = out[y, l]
                if r + k < 128: out[y, r + k] = out[y, r]
    dy = top - chin
    for y in range(chin):
        if 0 <= y + dy < 128:
            m = head[y, :, 3] > 0
            out[y + dy, m] = head[y, m]
    return out, dy

if __name__ == "__main__":
    a = load(f"{OUT}/work/norm_turn_E.png")
    chin = 74
    specs = {"jump_E_crouch": (0.72, 1.10, 105, 1), "jump_E_apex": (1.12, 0.94, 102, 0), "jump_E_land": (0.68, 1.14, 105, 3)}
    for n, (sy, sx, so, fl) in specs.items():
        if sys.argv[1:] and n not in sys.argv[1:]: continue
        o, dy = deform(a, chin, sy, sx, so, flare=fl)
        save(o, f"{OUT}/seed/{n}.png"); print(n, "head dy", dy)
