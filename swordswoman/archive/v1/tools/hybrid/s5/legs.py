"""Claude hand pass: repaint the walk legs per key (Gemini kept them parallel in every key).
Clears the old legs below the hem and draws two strappy-heel legs as exact pixels, back leg first."""
import numpy as np
from common import *
SK = {"front": ("skin_2", "skin_2", "skin_1"), "back": ("skin_1", "skin_1", "skin_0")}

def put(a, x, y, t, behind=True):
    if 0 <= x < 128 and 0 <= y < 128 and (not behind or a[y, x, 3] == 0):
        a[y, x, :3] = TRGB[t]; a[y, x, 3] = 255

def clear_legs(a, x0, x1, y0, y1=110):
    tones = {TRGB[k] for k in ("skin_0", "skin_1", "skin_2", "leather_1", "leather_2", "dark_1", "hair_0")}
    reds = {TRGB[k] for k in ("red_0", "red_1", "red_2", "red_3")}
    for y in range(y0, y1):
        for x in range(x0, x1):
            if not a[y, x, 3]: continue
            c = tuple(a[y, x, :3])
            if c in tones: a[y, x] = 0
            elif c == TRGB["outline"]:
                nb = [tuple(a[y+dy, x+dx, :3]) for dy, dx in ((0, 1), (0, -1), (1, 0), (-1, 0)) if a[y+dy, x+dx, 3]]
                if not any(n in reds for n in nb): a[y, x] = 0

def xs_at(pts, y):
    for (xa, ya), (xb, yb) in zip(pts[:-1], pts[1:]):
        if ya <= y <= yb:
            return xa + (xb - xa) * (y - ya) / max(yb - ya, 1)
    return pts[-1][0]

def leg(a, pts, kind="front", foot="flat", fwd=1):
    s = SK[kind]
    y0, y1 = pts[0][1], pts[-1][1]
    for y in range(y0, y1 + 1):
        c = int(round(xs_at(pts, y)))
        put(a, c - 2, y, "outline"); put(a, c + 2, y, "outline")
        for i, t in zip((-1, 0, 1), s): put(a, c + i, y, t)
    ax, ay = int(round(pts[-1][0])), y1
    if foot == "flat":       # strap row + sole, toe forward, heel spike back
        for i in range(-2, 4): put(a, ax + i * fwd, ay + 1, "outline" if i in (-2, 3) else "leather_1")
        for i in range(-2, 4): put(a, ax + i * fwd, ay + 2, "outline")
        put(a, ax, ay, "leather_1", behind=False)            # ankle strap
    elif foot == "toe":      # heel raised: shoe tilted, only the toe touches
        for i in range(-2, 3): put(a, ax + i * fwd, ay + 1, "outline" if i in (-2, 2) else "leather_1")
        for i in range(0, 4): put(a, ax + i * fwd, ay + 2, "outline")
        put(a, ax - 2 * fwd, ay + 2, "outline")            # heel spike
        put(a, ax, ay, "leather_1", behind=False)
    for y in range(y0, y1 + 1):   # close the bottom of the shin
        pass

WALK = {  # (clear box), back leg, front leg  (pts hip->knee->ankle), foot types
 "walk_SE_k0": ((57, 93, 79), [(62, 94), (61, 99), (59, 101)], "toe", [(69, 94), (70, 99), (72, 102)], "flat"),
 "walk_SE_k1": ((57, 94, 79), [(62, 95), (60, 99), (60, 102)], "toe", [(69, 95), (71, 99), (71, 102)], "flat"),
 "walk_SE_k2": ((57, 93, 79), [(63, 94), (66, 98), (64, 100)], "toe", [(68, 94), (68, 98), (68, 102)], "flat"),
 "walk_SE_k3": ((56, 92, 79), [(63, 92), (61, 97), (58, 99)], "toe", [(67, 92), (67, 97), (68, 101)], "toe"),
}
def paint(a, name):
    (x0, yc, x1), bp, bf, fp, ff = WALK[name]
    clear_legs(a, x0, x1, yc)
    leg(a, fp, "front", ff)      # behind-painting: front first so it wins, then back fills behind it
    leg(a, bp, "back", bf)
    return a
