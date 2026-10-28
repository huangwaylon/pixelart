"""S3 r3 HAND CELS for the SE body (Claude-authored). Upper body = typed rows (Y X0 STRING, standard legend);
front skirt = an authored HEM PROFILE (one sole row per column, typed per key) + typed fold clusters; legs/feet =
typed grids per key. Head / katana / ribbons are lock3 stamps. No parametric capsules."""
import os, sys
import numpy as np
H4 = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
sys.path.insert(0, H4)
import kit, heads as HEADS, ribbons as RB
from common import to_rgba

N = 128

COLLAR = """
67 56 K
67 76 K
68 56 KCK
68 75 KrK
69 56 KCRK
69 74 KRrK
70 56 KCRRK
70 73 KRRrK
71 56 KCRRRRRRRRRRRRRRRRRRrK
72 56 KCRRRRRRRvvvvRRRRRRrrK
73 57 KCRRRRRRRvvRRRRRRrrK
74 58 KCRRRRRRRRRRRRRrrK
75 59 KvrrrrrrrrrrrrrvK
"""
SHOULDERS = """
75 53 KSssss
75 76 smK
76 52 KSssss
76 74 ssmK
77 52 KSsssm
77 74 smmK
"""
BODICE = """
76 58 KCRRRRRRRRRRRRrK
77 58 KCRRRRRRRRRRRrrK
78 58 KCRRRRRRRRRRRrrK
"""
CORSET = """
79 58 KKLLLLLLLLLLLLKK
80 59 KLllllllKTTKlK
81 59 KLlllllllddllK
82 59 KLllllllKTTKlK
83 59 KLlllllllllllK
84 59 KKKKKKKKKKKKKK
"""


def sleeve_near(dx=0, dy=0, swing=0):
    """her RIGHT sleeve (viewer-left, near): dark arm band + purple ornament, bell flaring to the lower-left, red_0
    lining at the mouth, hand peeking out. swing = cuff end x shift (arm swing, + = forward / down-right)."""
    s = swing
    rows = []
    # band (upper arm) rows 78-79
    rows += [(78, 53, 'Kdddd'), (79, 53, 'Kuddd')]
    # bell: left edge moves out as it falls; the bottom follows the swing
    L = [53, 52, 52, 51, 51 + s // 2, 50 + s // 2, 49 + s, 49 + s, 48 + s, 47 + s]
    RR = [56, 56, 57, 57, 57, 58, 58, 58, 58, 58]
    for k, y in enumerate(range(80, 90)):
        xl = L[k]; xr = RR[k] + (s if y > 87 else 0)
        w = xr - xl + 1
        body = ['R'] * w
        body[0] = 'K'; body[1] = 'C'
        if y < 84: body[2] = 'C'
        for j in range(w - 3, w): body[j] = 'r'
        fold = 54 + (s if y > 85 else 0) - (y - 80) // 3                  # one fold crease running down-left
        if 0 < fold - xl < w - 1 and y > 81: body[fold - xl] = 'r'
        rows.append((y, xl, ''.join(body)))
    # mouth / lining rows 90-91, bottom outline 92
    xl = 47 + s; xr = 58 + s
    rows.append((90, xl, 'KC' + 'v' * (xr - xl - 2) + 'K'))
    rows.append((91, xl, 'Kv' + 'v' * (xr - xl - 3) + 'rK'))
    rows.append((92, xl + 1, 'K' * (xr - xl - 1)))
    # hand out of the cuff
    hx = 51 + s
    rows += [(92, hx, 'KssK'), (93, hx, 'KsmK'), (94, hx + 1, 'KK')]
    # ornament cord hanging from the band
    rows += [(80, 52, 'u'), (81, 51, 'u')]
    return '\n'.join(f'{y + dy} {x + dx} {t}' for y, x, t in rows)


def sleeve_far(dx=0, dy=0, swing=0):
    """her LEFT sleeve (viewer-right, far, behind the torso): band + bell to the lower-right; the katana fist sits in
    the mouth."""
    s = swing
    rows = [(78, 72, 'Kdddd'), (79, 72, 'KddddK')]
    L = [77, 77, 78, 78, 79, 79, 80 + s, 80 + s]
    for k, y in enumerate(range(80, 88)):
        xr = L[k]; xl = 71
        w = xr - xl + 1
        body = ['r'] * w; body[-1] = 'K'
        body[-2] = 'r'
        for j in range(0, min(3, w)): body[j] = 'R'
        rows.append((y, xl, ''.join(body)))
    rows.append((88, 74 + s, 'Kvvvv' + 'vK'))
    rows.append((89, 75 + s, 'KKKKK'))
    return '\n'.join(f'{y + dy} {x + dx} {t}' for y, x, t in rows)


def front_skirt(g, hem, xl_rows, slit, top=84, dx=0, dy=0, folds=(), shorts_to=93):
    """authored front wrap skirt.
    hem: {x: lowest row} (typed per key, petal hem); xl_rows: {y: left x} outline of the left edge; the right edge is
    the last hem column. slit = (x0, x1, y_top): columns x0..x1 open below y_top (shorts dark_1 down to shorts_to,
    then transparent: the legs show). folds: list of (char, [(x, y), ...]) typed clusters."""
    xs = sorted(hem)
    xr_ = xs[-1]
    for x in xs:
        yb = hem[x]
        for y in range(top, yb + 1):
            if x < xl_for(xl_rows, y): continue
            c = 'R'
            if x <= xl_for(xl_rows, y) + 1: c = 'C'
            if x >= xr_ - 2: c = 'r'
            if y >= yb - 1: c = 'r' if x > xs[0] + 1 else c
            if y == yb: c = 'K'
            if x == xl_for(xl_rows, y): c = 'K'
            if x == xr_: c = 'K'
            if slit and slit[0] <= x <= slit[1] and y >= slit[2] + (x - slit[0]) * 0:
                c = 'd' if y <= shorts_to else '.'
            kit.put(g, x + dx, y + dy, c)
    if slit:                                                   # panel edges along the slit: K left, red_0 right
        x0, x1, yt = slit
        for y in range(yt, max(hem[x0 - 1], hem.get(x1 + 1, 0)) + 1):
            if y <= hem.get(x0 - 1, 0): kit.put(g, x0 - 1 + dx, y + dy, 'K')
            if y <= hem.get(x1 + 1, 0) - 1 and y > yt: kit.put(g, x1 + 1 + dx, y + dy, 'v')
    for c, pts in folds:
        for x, y in pts: kit.put(g, x + dx, y + dy, c)


def xl_for(xl_rows, y):
    ks = sorted(xl_rows)
    best = xl_rows[ks[0]]
    for k in ks:
        if k <= y: best = xl_rows[k]
    return best


def stamp(g, x0, y0, rows, only_empty=False):
    for j, r in enumerate(rows):
        for i, ch in enumerate(r):
            if ch in '._ ': continue
            x, y = x0 + i, y0 + j
            if 0 <= x < N and 0 <= y < N and (not only_empty or g[y, x] == '.'):
                g[y, x] = '.' if ch == 'X' else ch


def text(g, t, dx=0, dy=0):
    kit.render_layer(kit.parse_layer('\n'.join(
        f'{int(a) + dy} {int(b) + dx} {c}' for a, b, c in (ln.split(None, 2) for ln in t.strip().splitlines()))), g)


def head_with_bow(d, expr, X, Y, bow=(0, 0), act=None):
    """paste the lock3 head; bow = lag offset of the BOW cel only (red loops/knot + their outline). Vacated pixels
    become hair if they are inside the dome, else transparent; the dome outline is re-closed."""
    hg = HEADS.head(d, expr, 0, act)
    Y += HEADS.H_LOCK2[d] - hg.shape[0]
    br = HEADS.BOW_ROWS[d]
    H, W = hg.shape
    red = np.isin(hg, list('vrRC')); red[br:] = False
    nb = np.zeros_like(red)
    nb[1:] |= red[:-1]; nb[:-1] |= red[1:]; nb[:, 1:] |= red[:, :-1]; nb[:, :-1] |= red[:, 1:]
    hairn = np.zeros_like(red); hm = np.isin(hg, list('hHJ'))
    hairn[1:] |= hm[:-1]; hairn[:-1] |= hm[1:]; hairn[:, 1:] |= hm[:, :-1]; hairn[:, :-1] |= hm[:, 1:]
    bowm = red | (nb & (hg == 'K') & ~(hairn & ~nb))
    bowm[br:] = False
    bx, by = bow
    base = hg.copy()
    if (bx, by) != (0, 0):
        base[bowm] = '.'
        # re-close: empty px next to hair -> outline
        for y in range(min(br + 1, H)):
            for x in range(W):
                if base[y, x] == '.' and any(0 <= y + b < H and 0 <= x + a < W and base[y + b, x + a] in 'hHJ'
                                             for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                    base[y, x] = 'K'
    out = kit.blank()
    for j in range(H):
        for i in range(W):
            if base[j, i] != '.': kit.put(out, X + i, Y + j, base[j, i])
    if (bx, by) != (0, 0):
        for j, i in zip(*np.nonzero(bowm)):
            kit.put(out, X + i + bx, Y + j + by, hg[j, i])
    return out
