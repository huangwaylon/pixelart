"""Locate the locked head stamp in each sprite and apply stamp-space edits (bun pinch crease)."""
import numpy as np
import pl

ST = "hybrid/S4_textured3d/r1/stamps/head_%s.png"
# stamp-space edits: (x, y, char)  -- bun/skull crease so the high bun reads as a ball, not a cone
EDITS = {
    "E": [(0, 9, "."), (1, 9, "K"), (2, 9, "K"), (3, 9, "K"), (4, 9, "h")],
    "W": [(25, 9, "."), (24, 9, "K"), (23, 9, "K"), (22, 9, "K")],
    "SE": [(1, 8, "K"), (2, 8, "K"), (3, 8, "K"), (4, 8, "K")],
    "SW": [(21, 8, "K"), (22, 8, "K"), (23, 8, "K"), (24, 8, "K")],
}


def locate(a, st):
    m = st[..., 3] > 0
    best = (-1, 0, 0)
    sh, sw = st.shape[:2]
    for oy in range(0, 128 - sh):
        for ox in range(0, 128 - sw):
            win = a[oy:oy + sh, ox:ox + sw]
            s = ((win[..., :4] == st[..., :4]).all(-1) & m).sum()
            if s > best[0]:
                best = (s, ox, oy)
    return best[1], best[2], best[0] / m.sum()


def apply(a, d):
    st = pl.load(ST % d)
    ox, oy, score = locate(a, st)
    n = 0
    for x, y, c in EDITS.get(d, []):
        X, Y = ox + x, oy + y
        if (a[Y, X] == st[y, x]).all():      # only where the stamp pixel is untouched
            a[Y, X] = pl.T(c)
            n += 1
    return a, (ox, oy, round(float(score), 3), n)
