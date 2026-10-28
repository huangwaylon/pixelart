"""Claude pass: vertical body normalization. Gemini lengthens bodies/legs; iso_v5 wants chunky legs.
Band-resize (nearest, rows only) chin->hem and hem->sole so the sole lands on BASE and legs are LEG rows.
Also removes tiny orphan components (< 4 px) not attached to the figure."""
import sys
import numpy as np
from common import *
BASE_Y = 105

def bands(a, name):
    al = a[..., 3] > 0
    reds = np.zeros_like(al)
    for k in ("red_0", "red_1", "red_2", "red_3"): reds |= np.all(a[..., :3] == TRGB[k], -1)
    st = np.zeros_like(al)
    for k in ("steel_0", "steel_1", "steel_2"): st |= np.all(a[..., :3] == TRGB[k], -1)
    x, y = head_xy(name); h = load(f"{ROOT}/hybrid/lock/pixel/head_{dir_of(name)}.png").shape[0]
    chin = y + h
    body = al & ~st
    rows = np.nonzero(body.any(1))[0]
    sole = rows.max()
    redc = reds.sum(1)
    hem = max(r for r in range(chin, sole + 1) if redc[r] >= 4)
    return chin, hem, sole

def resize_rows(band, n):
    H = band.shape[0]
    idx = np.clip(np.round((np.arange(n) + 0.5) * H / n - 0.5).astype(int), 0, H - 1)
    return band[idx]

def remove_orphans(a, minpx=4):
    from scipy import ndimage
    al = a[..., 3] > 0
    lab, n = ndimage.label(al, np.ones((3, 3)))
    sz = ndimage.sum(al, lab, range(1, n + 1))
    big = np.argmax(sz) + 1
    for i, s in enumerate(sz, 1):
        if i != big and s < minpx: a[lab == i] = 0
    return a

def steel_layer(a):
    """blade = steel components >= 6 px (plus their adjacent handle/guard px within 1 px that are outline/red)."""
    from scipy import ndimage
    st = np.zeros(a.shape[:2], bool)
    for k in ("steel_0", "steel_1", "steel_2"): st |= np.all(a[..., :3] == TRGB[k], -1)
    lab, n = ndimage.label(st, np.ones((3, 3)))
    keep = np.zeros_like(st)
    for i in range(1, n + 1):
        if (lab == i).sum() >= 6: keep |= lab == i
    return keep

def rowmap(r, chin, hem, sole, body_t, leg_t):
    if r < chin: return r
    if r <= hem: return chin + round((r - chin) * body_t / max(hem - chin, 1))
    if r <= sole: return chin + body_t + 1 + round((r - hem - 1) * (leg_t - 1) / max(sole - hem - 1, 1))
    return r - (sole - (chin + body_t + leg_t))

def normalize(a, name, leg_rows=None, base=BASE_Y, ratio=None, hem=None):
    chin, hem0, sole = bands(a, name)
    hem = hem if hem is not None else hem0
    if sole - hem < 3: hem = sole - 6
    legs = sole - hem
    if ratio is None:
        tgt_total = base - chin
        leg_t = leg_rows if leg_rows is not None else min(legs, 9)
        body_t = tgt_total - leg_t
    else:   # anim frames: same squeeze as the direction's turn sprite, keep squash/stretch
        body_t = int(round((hem - chin) * ratio[0])); leg_t = max(3, int(round(legs * ratio[1])))
    blade = steel_layer(a)
    bl = a.copy(); bl[~blade] = 0
    a = a.copy(); a[blade] = 0
    # close a chin->collar gap: the upper band starts at the first body row under the head
    hx, hy = head_xy(name)
    bt = chin
    while bt < hem and not a[bt, hx + 6:hx + 20, 3].any(): bt += 1
    upper = a[bt:hem + 1]; lower = a[hem + 1:sole + 1]
    out = np.zeros_like(a)
    out[:chin] = a[:chin]
    nb = resize_rows(upper, body_t + 1) if body_t + 1 != upper.shape[0] else upper
    nl = resize_rows(lower, leg_t) if leg_t != lower.shape[0] else lower
    out[chin:chin + len(nb)] = nb
    out[chin + len(nb):chin + len(nb) + len(nl)] = nl
    # below-sole pixels (sword tip etc): shift with the sole
    rest = a[sole + 1:]
    s0 = chin + len(nb) + len(nl)
    k = min(len(rest), 128 - s0)
    out[s0:s0 + k] = rest[:k]
    # re-place the rigid blade: translate it with its root (the end nearest the body centre)
    from scipy import ndimage
    lab, n = ndimage.label(blade, np.ones((3, 3)))
    cx = 64
    for i in range(1, n + 1):
        ys, xs = np.nonzero(lab == i)
        d = (xs - cx) ** 2 + (ys - 88) ** 2
        r = ys[np.argmin(d)]
        dy = rowmap(r, chin, hem, sole, body_t, leg_t) - r
        for y0, x0 in zip(ys, xs):
            if 0 <= y0 + dy < 128: out[y0 + dy, x0] = bl[y0, x0]
    info = dict(chin=int(chin), hem=int(hem), sole=int(sole), body_t=int(body_t), leg_t=int(leg_t),
                ratio=[body_t / max(hem - chin, 1), leg_t / max(legs, 1)])
    return remove_orphans(out, 8), info

HEM = {}
if __name__ == "__main__":
    for name in sys.argv[1:]:
        a = load(f"{OUT}/work/base_{name}.png")
        if name in BODY:
            body, sole = BODY[name]
            legs = {"jump_E_crouch": 5, "jump_E_land": 5, "jump_E_apex": 8, "walk_SE_k1": 7, "slash_SE_k2": 6, "slash_SE_k0": 7}.get(name)
            o, info = normalize(a, name, leg_rows=legs, base=sole, hem=HEM.get(name))
        else:
            o, info = normalize(a, name, hem=HEM.get(name))
        save(o, f"{OUT}/work/norm_{name}.png"); print(name, info)
