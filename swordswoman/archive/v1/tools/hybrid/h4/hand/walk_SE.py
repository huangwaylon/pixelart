"""walk_SE hand cels (S3 r3). k0 CONTACT, k1 DOWN, k2 PASSING, k3 UP; k4..k7 = the second step (legs swapped) for
the 8-key bonus cycle. Everything below the collar is typed here per key; head / katana / ribbons are lock3 stamps.
  body bounce (crown):        k0 0, k1 +3 (down), k2 +1, k3 -2 (up)          -> crown range 5
  shoulders vs hips:          -1, 0, 0, +1 px (counter-rotation)
  bow + bun (lag 1 key, overshoot): rel dy -1, -2, +2, +1; dx 0, -1, -1, 0
  katana: 45 deg on every key (stable), fist swings with the far arm only
  tails / ribbons: swing opposite the lead leg with a 1-key lag
"""
import os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import se_body as B
from se_body import kit, RB

SHIFT = -2                          # whole walk -2 px: the contact foot centre sits on the pivot column
BY = [0, 3, 1, -2] * 2
SH = [-1, 0, 0, 1, 1, 0, 0, -1]
BOW = [(0, -1), (-1, -1), (-1, 2), (0, 1)] * 2
NEAR_SWING = [2, 1, 0, -2, -2, -1, 0, 2]          # near (right) arm forward when the right leg is back
FAR_SWING = [-1, 0, 0, 1, 1, 0, 0, -1]
FIST = [(78, 88), (79, 88), (79, 89), (80, 89), (80, 89), (79, 89), (79, 88), (78, 88)]
FIST_LAG = [-1, -1, 1, 1] * 2                       # sword hand lags the bounce 1 key (tip bobs, angle fixed)
COLLAR_LAG = [-1, -1, 1, 1] * 2                     # collar flare tips trail the bounce 1 px

# ---- legs (typed). Far leg = her LEFT (viewer-right). Near leg = her RIGHT (viewer-left).
LEGS = {
 0: [  # CONTACT: far leg forward, heel strike at x64..69 on 104; near leg back on the toe, sole 103
  (64, 94, ['KssmK', 'KssmK', 'KssmK', 'KssmK', 'KssmK', 'KdddK', 'KsmK.', 'KddKKK', 'KdddddK', 'KdKKKKK', 'KK.....']),
  (57, 94, ['.KssK', '.KsmK', 'KssmK', 'KsmK.', 'KdddK', 'KsmK.', 'KdddK', 'KddK.', '.KK..']),
 ],
 1: [  # DOWN: far foot flat at 64..69, knee bent forward (+1); near toe pushing off, heel high
  (65, 96, ['KssmK', 'KssmK', 'KssmK', 'KssmK', 'KdddK', '.KsmK', 'KddddK', 'KdKddK', 'KK.KKK']),
  (58, 95, ['KssK.', 'KsmK.', '.KsmK', '.KsmK', '.KddK', '..KdK', '..KdK', '..KK.']),
 ],
 2: [  # PASSING: far leg straight under the body, foot flat; near knee lifted forward, foot 3 px up (sole 100)
  (64, 95, ['KssmK', 'KssmK', 'KssmK', 'KssmK', 'KssmK', 'KdddK', 'KsmK.', 'KddddK', 'KdKddK', 'KK.KKK']),
  (56, 95, ['.KssK.', '.KssmK', '.KssmK', '..KdddK', '..KdsdKK', '..KddddK', '...KKKKK']),
 ],
 3: [  # UP: far leg on the ball of the foot (heel up), body high; near leg reaching forward, toe up, sole 102
  (63, 93, ['KssmK', 'KssmK', 'KssmK', 'KssmK', 'KssmK', 'KssmK', 'KdddK', '.KsmK', '.KdddK', '..KddK', '..KdK', '..KK.']),
  (66, 94, ['KssmK.', '.KssmK', '.KssmK', '..KssmK', '..KdddK', '..KsmK.', '..KdddKK', '..KdddddK', '..KKKKKK']),
 ],
 # ---- second step (bonus 8-key cycle): the NEAR leg leads; far leg drawn first (behind)
 4: [  # CONTACT: far leg back on the toe (sole 102), near heel strike 58..64
  (66, 94, ['.KssK', '.KsmK', 'KssmK', 'KsmK.', 'KdddK', 'KsmK.', 'KdddK', 'KddK.', '.KK..']),
  (58, 94, ['KssmK', 'KssmK', 'KssmK', 'KssmK', 'KssmK', 'KdddK', 'KsmK.', 'KddKKK', 'KdddddK', 'KdKKKKK', 'KK.....']),
 ],
 5: [  # DOWN: far toe pushing off; near flat, knee bent
  (66, 95, ['KssK.', 'KsmK.', '.KsmK', '.KsmK', '.KddK', '..KdK', '..KdK', '..KK.']),
  (59, 96, ['KssmK', 'KssmK', 'KssmK', 'KssmK', 'KdddK', '.KsmK', 'KddddK', 'KdKddK', 'KK.KKK']),
 ],
 6: [  # PASSING: far knee lifted forward, foot 3 px up (sole 101) right of the stance leg; near straight
  (67, 95, ['.KssK.', '.KssmK', '.KssmK', '..KdddK', '..KdsdKK', '..KddddK', '...KKKKK']),
  (58, 95, ['KssmK', 'KssmK', 'KssmK', 'KssmK', 'KssmK', 'KdddK', 'KsmK.', 'KddddK', 'KdKddK', 'KK.KKK']),
 ],
 7: [  # UP: far leg reaching forward toe up (sole 102); near on the ball of the foot
  (69, 94, ['KssmK.', '.KssmK', '.KssmK', '..KssmK', '..KdddK', '..KsmK.', '..KdddKK', '..KdddddK', '..KKKKKK']),
  (57, 93, ['KssmK', 'KssmK', 'KssmK', 'KssmK', 'KssmK', 'KssmK', 'KdddK', '.KsmK', '.KdddK', '..KddK', '..KdK', '..KK.']),
 ],
}

# ---- front skirt hem profiles (typed per key): lowest row per column; petals + notches
def hem_from(pts):
    """pts = [(x, y), ...] corner points of the petal hem; straight runs between them (authored corners)"""
    h = {}
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        for x in range(x0, x1 + 1):
            t = (x - x0) / max(1, x1 - x0)
            h[x] = int(round(y0 + (y1 - y0) * t))
    return h

HEM = {
 0: [(52, 95), (53, 96), (54, 96), (57, 94), (61, 98), (65, 94), (67, 93), (68, 93), (71, 93), (72, 95), (74, 96), (76, 95), (77, 96), (79, 95)],
 1: [(51, 96), (52, 97), (54, 97), (57, 95), (61, 99), (65, 95), (67, 94), (68, 94), (71, 94), (72, 96), (74, 97), (76, 96), (77, 97), (80, 96)],
 2: [(52, 95), (53, 96), (54, 96), (57, 94), (61, 97), (64, 93), (66, 92), (68, 92), (71, 92), (72, 94), (74, 95), (76, 94), (77, 95), (79, 94)],
 3: [(52, 94), (53, 95), (54, 95), (57, 93), (61, 97), (65, 94), (67, 93), (68, 93), (71, 93), (72, 95), (75, 97), (77, 95), (78, 96), (80, 95)],
}
XL = {84: 58, 85: 57, 86: 56, 88: 55, 89: 54, 91: 53, 93: 52}
SLIT = (69, 70, 88)
# typed fold clusters (2-3 per panel): lit wedge rising from the left petal tip, red_0 crease above the notch,
# red_1 shadow wedge on the right panel. Positions are relative to k0 and follow the key's hem shift.
def folds(k):
    d = {0: 0, 1: 1, 2: -1, 3: 0}[k]
    return [('C', [(55, 90 + d), (55, 91 + d), (56, 92 + d), (56, 93 + d), (55, 89 + d)]),
            ('C', [(60, 92 + d), (60, 93 + d), (61, 94 + d), (61, 95 + d), (61, 96 + d)]),
            ('v', [(57, 92 + d), (57, 93 + d)]),
            ('v', [(65, 92 + d)]),
            ('r', [(73, 91 + d), (73, 92 + d), (74, 93 + d), (74, 94 + d)])]

# ---- back tails (behind the legs): left tail point and right tail point per key (lag opposite the lead leg)
TAIL = {0: ((48, 100), (81, 99)), 1: ((47, 100), (82, 100)), 2: ((46, 99), (81, 98)), 3: ((47, 99), (80, 99)),
        4: ((47, 99), (80, 99)), 5: ((48, 100), (81, 100)), 6: ((49, 99), (82, 98)), 7: ((48, 100), (81, 99))}


def tails(g, k, dy):
    (lx, ly), (rx, ry) = TAIL[k]
    # left tail: from the skirt side (55, 86) to the point; typed fill row by row (outline K, C lit edge, r body, v inner)
    for y in range(86, ly + 1):
        t = (y - 86) / (ly - 86)
        xa = round(55 + (lx - 55) * t)
        xb = 58 if y < 95 else round(58 - (58 - lx) * ((y - 95) / max(1, ly - 95)) ** 0.8)
        for x in range(xa, xb + 1):
            c = 'r'
            if x == xa: c = 'K'
            elif x == xa + 1: c = 'C' if y < ly - 2 else 'r'
            elif x >= xb - 1 and y > 92: c = 'v'
            if y == ly: c = 'K'
            kit.put(g, x, y + (dy if y < 95 else 0), c)
        if y >= 95: kit.put(g, xb + 1, y, 'K')
    for y in range(88, ry + 1):
        t = (y - 88) / (ry - 88)
        xb = round(77 + (rx - 77) * t)
        xa = 74 if y < 96 else round(74 + (rx - 1 - 74) * ((y - 96) / max(1, ry - 96)))
        for x in range(xa, xb + 1):
            c = 'r' if x < xb - 1 else 'v'
            if x == xb: c = 'K'
            if y == ry: c = 'K'
            kit.put(g, x, y + (dy if y < 96 else 0), c)
        if y >= 96: kit.put(g, xa - 1, y, 'K')


RIB = {   # (near preset, blend), (far preset, blend): ribbons trail up-left against the travel, wave root -> tip
 0: (('neutral', ('trail_out', 0.35)), ('neutral', ('trail_in', 0.3))),
 1: (('neutral', ('float', 0.45)), ('neutral', ('float', 0.25))),
 2: (('neutral', ('trail_out', 0.6)), ('neutral', ('trail_out', 0.25))),
 3: (('neutral', ('trail_in', 0.3)), ('neutral', ('trail_out', 0.3))),
 4: (('neutral', ('trail_in', 0.3)), ('neutral', ('trail_out', 0.35))),
 5: (('neutral', ('float', 0.3)), ('neutral', ('float', 0.4))),
 6: (('neutral', ('trail_out', 0.3)), ('neutral', ('trail_out', 0.5))),
 7: (('neutral', ('trail_out', 0.35)), ('neutral', ('trail_in', 0.3))),
}


def frame(k, expr='calm'):
    by = BY[k]; sh = SH[k]
    g = kit.blank()
    # back -> front
    fx, fy = FIST[k]
    (pn, bn), (pf, bf) = RIB[k]
    kit.ribbon(g, RB.spec((71 + sh, 74 + by), pf, 1, blend=bf).split()[1:])
    tails(g, k, by // 2)
    lay = kit.blank(); B.text(lay, B.sleeve_far(sh, by, FAR_SWING[k])); kit.over(g, lay)
    kat = kit.blank(); kit.katana(kat, [str(fx + sh), str(fy + by + FIST_LAG[k]), '45', '19', 'hook=1'])
    kit.over(g, kat)
    for (x0, y0, rows) in LEGS[k]:
        B.stamp(g, x0, y0 + 0, rows)
    sk = kit.blank()
    B.front_skirt(sk, B_hem(k % 4), XL, SLIT, dy=by // 2 if k % 4 != 1 else 2, folds=folds(k % 4))
    kit.over(g, sk)
    up = kit.blank()
    B.text(up, B.CORSET, 0, by)
    B.text(up, B.BODICE, sh, by)
    B.text(up, B.SHOULDERS, sh, by)
    kit.over(g, up)
    lay = kit.blank(); B.text(lay, B.sleeve_near(sh, by, NEAR_SWING[k])); kit.over(g, lay)
    tips = '\n'.join(l for l in B.COLLAR.strip().splitlines() if int(l.split()[0]) <= 70)
    body_ = '\n'.join(l for l in B.COLLAR.strip().splitlines() if int(l.split()[0]) > 70)
    lay = kit.blank(); B.text(lay, tips, sh, by + COLLAR_LAG[k]); B.text(lay, body_, sh, by); kit.over(g, lay)
    hd = B.head_with_bow('SE', expr, 54 + sh, 43 + by, BOW[k])
    m = hd != '.'; g[m] = hd[m]
    global OWNER
    OWNER = np.full(g.shape, '', dtype=object); OWNER[m] = 'HEAD'
    kit.ribbon(g, RB.spec((58 + sh, 75 + by), pn, -1, blend=bn).split()[1:])
    return g


def B_hem(k): return hem_from(HEM[k])


if __name__ == '__main__':
    out = sys.argv[1]
    os.makedirs(out, exist_ok=True)
    from common import save
    for k in range(8):
        g = frame(k)
        g = kit.shift(g, SHIFT, 0); own = np.roll(OWNER, SHIFT, axis=1)
        g = kit.lint_fix(g, own); g = kit.orphan_fix(g)
        if k < 4: save(B.to_rgba(g), f'{out}/walk_SE_k{k}.png')
        os.makedirs(f'{out}/../walk8', exist_ok=True)
        save(B.to_rgba(g), f'{out}/../walk8/walk8_SE_f{k}.png')
