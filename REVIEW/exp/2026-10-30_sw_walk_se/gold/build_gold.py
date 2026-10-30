"""Gold frames v2, walk SE (contact L, passing L), authored to DESIGN_LOCK.md + Amendment 1 (owner 2026-10-30).

v2 (after "approve style, revise pose"): head + side locks traced from the approved master EC0_SE_96 (same view angle and
proportions), master leg length / hem / boot size / obi band, re-posed by hand: dynamic contact (heel planted, back leg on its toe,
bent asymmetric arm swing) and a risen passing pose (knee forward, arms crossing the body line). v1 is in gold/v1/.

Method: part map (master-traced masks for hair/face/neck; hand-placed polygons for dress/obi/sleeves/hands; hand-placed pixel
spans for legs/boots) -> flat 2-tone fill -> closed 1-px K silhouette + interior K only on listed overlaps -> pixel-perfect
clean-up -> facesys eyes -> hand-drawn char blocks (bow_block.txt, REGION) and single-pixel PATCHes, each with a reason.
Usage: <pixtools venv python> build_gold.py   -> walk_SE_<key>.txt/.png
"""
import os, sys, json
import numpy as np, cv2

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = '/Users/waylonhuang/Documents/other/pixelart'
sys.path.insert(0, ROOT + '/docs/team_review/2026-10-30/face_palette/scripts')
import facesys as FS

PAL = {k: v['hex'] for k, v in json.load(open(ROOT + '/swordswoman/v2/pixelize/palette.json'))['colors'].items()}
LOCK = list('KhHgLsSeERQOoW')
RGB = {k: tuple(int(PAL[k][i:i + 2], 16) for i in (1, 3, 5)) for k in LOCK}
N, SS = 128, 8
EXPR = 'open'

# material -> (base, shadow)
MAT = {'hair': ('H', 'h'), 'hairback': ('H', 'h'), 'skin': ('s', 'S'), 'face': ('s', 's'), 'neck': ('S', 'S'),
       'red': ('E', 'R'), 'redfar': ('R', 'R'), 'obi': ('O', 'o'), 'sock': ('H', 'h'), 'boot': ('g', 'H')}
# shadow band width (px from the right edge) per part
SHW = {'hairback': 2, 'torso': 3, 'skirt': 3, 'sleeveN': 2, 'hair': 2,
       'legB': 1, 'legF': 1, 'bootB': 1, 'bootF': 1, 'obi': 2}


def ell(cx, cy, rx, ry, n=48):
    t = np.radians(np.linspace(0, 360, n, endpoint=False))
    return [(cx + rx * np.cos(a), cy + ry * np.sin(a)) for a in t]


def spans(*rows):
    """hand-placed pixel spans: rows of (y, x0, x1) inclusive -> a part mask (pixel-exact, outline ring included)."""
    return {'spans': rows}


def rast(poly):
    if isinstance(poly, np.ndarray):
        return poly.astype(bool)
    if isinstance(poly, dict):
        m = np.zeros((N, N), bool)
        for y, x0, x1 in poly['spans']: m[y, x0:x1 + 1] = True
        return m
    m = np.zeros((N * SS, N * SS), np.uint8)
    pts = np.round(np.array(poly, np.float64) * SS * 16).astype(np.int32)
    cv2.fillPoly(m, [pts], 1, lineType=cv2.LINE_8, shift=4)
    return m.reshape(N, SS, N, SS).mean((1, 3)) >= 0.5


def sh(m, dy, dx):
    return np.roll(np.roll(m, dy, 0), dx, 1)


def n4(m):
    p = np.pad(m, 1)
    return p[:-2, 1:-1], p[2:, 1:-1], p[1:-1, :-2], p[1:-1, 2:]



def compose(parts):
    lab = np.full((N, N), '', dtype=object)
    mat = np.full((N, N), '', dtype=object)
    for name, m, poly in parts:
        r = rast(poly)
        lab[r] = name; mat[r] = m
    return lab, mat


def elbows(K):
    N_, S_, W_, E_ = n4(K)
    p = np.pad(K, 1)
    NE, NW, SE, SW = p[:-2, 2:], p[:-2, :-2], p[2:, 2:], p[2:, :-2]
    return K & ((N_ & E_ & ~S_ & ~W_ & ~NE) | (E_ & S_ & ~N_ & ~W_ & ~SE) | (S_ & W_ & ~N_ & ~E_ & ~SW) | (W_ & N_ & ~S_ & ~E_ & ~NW))


def silmask(g):
    op = g != '.'
    bN, bS, bW, bE = n4(~op)
    return op & (bN | bS | bW | bE)


def clean(g, fill):
    """Pixel-perfect line clean-up: redundant elbows (silhouette -> bg if it touches no fill, interior -> fill) and 2x2 clumps."""
    for _ in range(8):
        K = g == 'K'; op = g != '.'; fl = op & ~K
        fN, fS, fW, fE = n4(fl)
        sil = silmask(g)
        el = elbows(K)
        g[el & ~(fN | fS | fW | fE) & sil] = '.'
        K = g == 'K'; sil = silmask(g)
        ie = elbows(K) & ~sil
        g[ie] = fill[ie]
        K = g == 'K'; sil = silmask(g)
        c = K[:-1, :-1] & K[1:, :-1] & K[:-1, 1:] & K[1:, 1:]
        for y, x in zip(*np.nonzero(c)):
            for yy, xx in ((y, x), (y, x + 1), (y + 1, x), (y + 1, x + 1)):
                if not sil[yy, xx] and g[yy, xx] == 'K' and fill[yy, xx] not in ('.', 'K'):
                    g[yy, xx] = fill[yy, xx]; break
    return g


def line_px(pts):
    """pixels of a polyline (Bresenham, pixel centres)."""
    out = []
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        n = int(max(abs(x1 - x0), abs(y1 - y0))) + 1
        for t in np.linspace(0, 1, n):
            out.append((int(np.floor(y0 + (y1 - y0) * t + 0.5)), int(np.floor(x0 + (x1 - x0) * t + 0.5))))
    return out



# ------------------------------------------------------------------------------------------------------------------ master
MASTER = ROOT + '/swordswoman/v2/m96/masters/EC0_SE_96.txt'


def master_masks():
    """Head parts traced from the approved master EC0_SE_96 (Amendment 1: same view angle + proportions, longer wavy side locks).
    Every master px (outline included) gets the material of its nearest non-outline px; face = skin above the chin (holes filled),
    neck = skin below it, hair = hair px of the head (master bun/bow dropped: the bow block replaces them)."""
    from scipy import ndimage as nd
    g = np.array([list(l.rstrip('\n')) for l in open(MASTER)])
    op = g != '.'
    cls = np.zeros(g.shape, int)
    for chs, c in (('hHgL', 1), ('sSmk', 2), ('eER', 3), ('QOo', 4), ('Dd', 5), ('W', 2)):
        cls[np.isin(g, list(chs))] = c
    idx = nd.distance_transform_edt(cls == 0, return_distances=False, return_indices=True)
    lab = cls[idx[0], idx[1]] * op
    yy = np.arange(N)[:, None] * np.ones((1, N), int)
    xx = np.ones((N, 1), int) * np.arange(N)[None, :]
    skin = (lab == 2) & (yy >= 44) & (yy <= 66) & (xx >= 57)
    face = nd.binary_fill_holes(nd.binary_closing(skin & (yy <= 61), np.ones((3, 3))) | (skin & (yy <= 61)))
    face &= op
    face = nd.binary_opening(face, np.ones((2, 2))) | (face & nd.binary_erosion(face))
    hair = (lab == 1) & (yy <= 69) & ~face
    hair |= (lab == 2) & (yy <= 61) & ~face & (xx < 62)      # the master's ear/cheek px inside the side hair -> hair
    hair &= ~((yy < 36) & (xx < 58))                          # master bun: replaced by the bow block
    hair &= ~((lab == 3) & (yy <= 54))
    hair = nd.binary_opening(hair, np.ones((2, 2))) | (hair & nd.binary_erosion(hair, np.ones((3, 3))))
    neck = (lab == 2) & (yy > 59) & (yy <= 66) & (xx >= 61) & (xx <= 70) & ~face
    return hair, face, neck


def polygonize(m, eps=0.9, sig=0.7):
    """smooth a 1x mask: trace its contour, Gaussian-smooth along the curve, simplify, refill at 8x (vector-line method)."""
    cs, _ = cv2.findContours(m.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    out = np.zeros((N, N), bool)
    for c in cs:
        if len(c) < 6: continue
        pts = c[:, 0, :].astype(np.float64) + 0.5
        k = max(1, int(3 * sig)); w = np.exp(-np.arange(-k, k + 1) ** 2 / (2 * sig * sig)); w /= w.sum()
        sm = np.stack([np.convolve(np.r_[pts[-k:, i], pts[:, i], pts[:k, i]], w, 'valid') for i in (0, 1)], 1)
        ap = cv2.approxPolyDP(sm.astype(np.float32), eps, True)[:, 0, :]
        out |= rast([(x, y) for x, y in ap])
    return out


def bang_tips(face):
    """full bangs: strand tips cut into the top of the face, pointing down-left, kept off the eyes (eyes clear)."""
    tips = [[(57.5, 46), (61.4, 46), (59.4, 51)], [(61.2, 46), (65, 46), (63, 49.4)], [(64.6, 46), (68.8, 46), (66.8, 50.2)],
            [(67.2, 46), (71.8, 46), (69.6, 51.2)], [(71.2, 46), (74.6, 46), (72.6, 49.4)], [(74, 46), (78.8, 46), (76.6, 51.4)]]
    m = face.copy()
    for t in tips: m &= ~rast(t)
    return m


_H, _F, _N = master_masks()
FACE = bang_tips(rast([(58, 46), (76.6, 46), (77, 50), (76.2, 54.6), (74.2, 58.4), (71.4, 61.4), (69.6, 62.6), (66.4, 61.8), (62, 59.4), (59.4, 56.2), (58.2, 51)]))
_yy = np.arange(N)[:, None] * np.ones((1, N), int); _xx = np.ones((N, 1), int) * np.arange(N)[None, :]
# hair silhouette: hand-placed vertices measured on the master (crown, far lock, near front lock, wavy near-side mass + lock)
HAIRPOLY = [(57, 38), (60.4, 35.6), (64.4, 34.5), (68.4, 34.5), (72.2, 35.4), (75.2, 37.2), (77.6, 39.6), (79.2, 44), (79.8, 48), (79.6, 53), (78.8, 57),
            (80.6, 61.4), (80.2, 64.6), (79.2, 67.2), (77.6, 68.2), (76.4, 64.6), (75.6, 61), (75.4, 57.6), (76.6, 52), (75, 60.5), (62.4, 62.6),
            (61, 65.2), (60.4, 67.6), (61.4, 69.8), (59.4, 70.6), (57.6, 68), (57.4, 65.4), (56.6, 62),
            (55.6, 62.6), (55.8, 64.6), (54.8, 67.8), (52.6, 68.4), (51.8, 65.6), (50.4, 62.8), (49.2, 59.6), (48.8, 56), (49, 53),
            (48.4, 50), (48.4, 47), (49.8, 42.4), (53, 39.4)]
HAIR = rast(HAIRPOLY) & ~FACE
NECK = rast([(63, 58), (70.4, 58), (71, 64.4), (68, 68.4), (63, 64.4)]) & ~FACE & ~HAIR


def shift(m, dx, dy):
    return np.roll(np.roll(m, dy, 0), dx, 1)


def head(dx, dy):
    return [('hair', 'hair', shift(HAIR, dx, dy)), ('neck', 'neck', shift(NECK, dx, dy) & ~shift(FACE, dx, dy)),
            ('face', 'face', shift(FACE, dx, dy))]


def leg_spans(rows):
    return spans(*[(y, l, r) for y, l, r in rows])


def body(f, dy):
    """Screen-left = her right = NEAR side in SE (armN, legB). Legs are planted (no bob)."""
    P = lambda pts: [(x, y + dy) for x, y in pts]
    if f == 'contact':
        # contact L: left leg (screen-right) forward, heel planted, toe up; right leg (screen-left) back on its toe
        legF = [('legF', 'sock', spans(*[(y, 65 + (y - 89) // 4, 65 + (y - 89) // 4 + 7) for y in range(89, 114)])),
                ('bootF', 'boot', spans(*[(y, 71, 77) for y in range(114, 118)], (118, 71, 78), (119, 71, 79), (120, 71, 80),
                                        (121, 71, 80), (122, 71, 79), (123, 71, 77), (124, 72, 75)))]
        legB = [('legB', 'sock', spans(*[(y, 58 - (y - 88) // 5, 58 - (y - 88) // 5 + 7) for y in range(89, 103)],
                                       *[(y, 55 - (y - 103) // 3, 55 - (y - 103) // 3 + 7) for y in range(103, 114)])),
                ('bootB', 'boot', spans((114, 51, 58), (115, 50, 58), (116, 51, 58), (117, 52, 59), (118, 53, 59), (119, 54, 59),
                                        (120, 54, 59), (121, 55, 58)))]
        legs = legB + legF
        # near arm swings forward (bent, hand in front of the obi/skirt); far arm swings back (bent, hand behind the hip)
        armFar = [('sleeveFar', 'redfar', P([(73, 65.6), (76.8, 66.2), (79.4, 69.6), (81.8, 73.4), (83.4, 78.4), (79.8, 79.8), (78.2, 75.6), (75.6, 72), (74.4, 70)])),
                  ('handFar', 'skin', P(ell(82.2, 81.4, 2.2, 2.3)))]           # swung back: elbow bent at ~(80,73), hand behind
        handFar = []
        armN = [('sleeveN', 'red', P([(58.6, 65.6), (54.6, 66.2), (52.2, 71), (52.4, 76.6), (55.4, 79.6), (61.6, 83.2), (63.2, 80.4), (58.6, 75.6), (58.6, 70)])),
                ('handN', 'skin', P(ell(64.6, 84.4, 2.6, 2.5)))]
    else:
        # passing L: left leg (screen-right) planted straight; right (near) leg passes in front, knee forward, foot lifted behind
        legF = [('legF', 'sock', spans(*[(y, 66, 72 if y < 101 else 71) for y in range(89, 114)])),
                ('bootF', 'boot', spans(*[(y, 66, 72) for y in range(114, 118)], (118, 66, 73), (119, 66, 74), (120, 66, 75),
                                        (121, 66, 75), (122, 66, 75), (123, 66, 75), (124, 67, 74)))]
        legB = [('legB', 'sock', spans(*[(y, 58 + (y - 89) * 3 // 7, 58 + (y - 89) * 3 // 7 + 7) for y in range(89, 104)],
                                       *[(y, 64 - (y - 104) * 6 // 8, 64 - (y - 104) * 6 // 8 + 6) for y in range(104, 113)])),
                ('bootB', 'boot', spans((113, 57, 63), (114, 57, 63), (115, 57, 62), (116, 57, 62), (117, 58, 62), (118, 58, 61),
                                        (119, 59, 61)))]
        legs = legF + legB
        armFar = [('sleeveFar', 'redfar', P([(73, 65.6), (76.8, 66.2), (79.4, 71), (80.2, 76), (79.4, 79.6), (76, 80), (75.4, 76), (74.4, 71)])),
                  ('handFar', 'skin', P(ell(77.4, 81.4, 2.2, 2.3)))]          # slightly back: hand half behind the hip
        handFar = []
        armN = [('sleeveN', 'red', P([(58.4, 65.6), (54.6, 66.2), (52.4, 71), (52.2, 76.6), (54.2, 80.6), (59.8, 82.4), (60.6, 78.6), (58.2, 74), (58.4, 70)])),
                ('handN', 'skin', P(ell(61.8, 83.8, 2.6, 2.5)))]
    dress = [('torso', 'red', P([(59, 63.4), (70.6, 63.4), (75, 65.4), (76.6, 69.5), (76.4, 76), (56, 77.6), (55.4, 72), (55.8, 67.4), (57, 65)])),
             ('skirt', 'red', P([(56.4, 81), (75.6, 78), (77.8, 83), (79.8, 88.4), (80.2, 90.2 if f == 'contact' else 89.4), (73, 91.2 if f == 'contact' else 90.6), (65, 91.4), (57, 90.8),
                                 (51.8, 90.2), (49.8, 89.2), (49.6, 87.6), (51.6, 84.4), (54.4, 81.6)])),
             ('obi', 'obi', P([(56.2, 76.6), (75.8, 73.4), (76, 79.8), (56.4, 83)] if f == 'contact' else
                              [(56.2, 76.8), (75.8, 72.6), (76, 79), (56.4, 83.2)]))]
    return armFar + legs + dress + handFar + armN


def lines_for(f):
    front_leg = ({'legF', 'bootF'}, {'legB', 'bootB'}) if f == 'contact' else ({'legB', 'bootB'}, {'legF', 'bootF'})
    return [front_leg,                                                            # leg/leg
            ({'sleeveN', 'handN', 'handFar'}, {'torso', 'obi', 'skirt'}),         # arm over body
            ({'torso', 'skirt', 'obi'}, {'sleeveFar'}),                           # body over the far arm (arm/body edge)
            ({'sleeveN'}, {'handN'}), ({'sleeveFar'}, {'handFar'}),               # hand/sleeve (cuff)
            ({'hair'}, {'face'}),                                                 # bangs/face + side locks over the cheek
            ({'face'}, {'neck'})]                                                 # chin/neck (bow/hair lines live in bow_block.txt)


BOB = {'contact': 1, 'passing': -1}
EYEDX = 1   # eyes 1 px toward the far side vs the facesys master layout (stronger 3/4 read; Amendment 1)
HEADX = {'contact': 0, 'passing': 0}
SOCK_TOP = 95


def build(f):
    bob = BOB[f]
    lab, mat = compose(body(f, bob) + head(HEADX[f], bob))
    op = lab != ''
    yy = np.arange(N)[:, None] * np.ones((1, N), int)
    xx = np.ones((N, 1), int) * np.arange(N)[None, :]
    g = np.full((N, N), '.', dtype='<U1')
    for name in sorted(set(lab[op])):
        m = lab == name
        base, shd = MAT[mat[m][0]]
        g[m] = base
        w = SHW.get(name, 0)
        if w and base != shd:
            lit = m.copy()
            for k in range(1, w + 1): lit &= sh(m, 0, -k)
            g[m & ~lit] = shd
    L = lambda n: lab == n
    g[L('obi') & ~sh(L('obi'), -1, 0)] = 'o'
    g[L('obi') & ~sh(L('obi'), 1, 0) & (xx < 70)] = 'O'
    g[L('skirt') & sh(L('obi'), 1, 0)] = 'R'
    m = L('sleeveN'); g[m & ~sh(m, -1, 0)] = 'R'
    # collar: lapels (R) meeting in a V at the obi, neck skin above
    for pts in ([(62, 63 + bob), (68, 69 + bob)], [(72, 63 + bob), (67, 76 + bob)]):
        for y, x in line_px(pts):
            if lab[y, x] == 'torso': g[y, x] = 'R'
    for pts in ([(61, 83 + bob), (59.5, 90 + bob)], [(70, 81 + bob), (71, 90 + bob)]):
        for y, x in line_px(pts):
            if lab[y, x] == 'skirt': g[y, x] = 'R'
    for nm in ('legB', 'legF'):
        lg = L(nm)
        thigh = lg & (yy < SOCK_TOP)
        g[thigh] = 's'
        g[thigh & ~sh(lg, 0, -1)] = 'S'
        g[lg & sh(L('skirt'), 1, 0)] = 'S'
        g[lg & (yy == SOCK_TOP)] = 'E'
    for nm in ('handN', 'handFar'):
        hm = L(nm); g[hm & ~sh(hm, -1, -1)] = 'S'
    # hair: sheen arc (L) on the lit crown; wave/strand splits (h) on the side locks; lock tips in shadow
    hr = L('hair')
    cx, cy = 66.5 + HEADX[f], 49.0 + bob
    d = np.hypot((xx - cx) / 12.5, (yy - cy) / 11.5)
    ang = np.degrees(np.arctan2(yy - cy, xx - cx))
    g[hr & (d > 0.84) & (d < 0.95) & (ang > -140) & (ang < -80) & (g == 'H')] = 'L'
    for pts in STRANDS:
        for y, x in line_px([(px + HEADX[f], py + bob) for px, py in pts]):
            if lab[y, x] == 'hair': g[y, x] = 'h'
    g[hr & ~sh(hr, -1, 0)] = 'h'
    # bow + bun block
    for fn, x0, y0 in STAMPS:
        rows = [r.rstrip('\n') for r in open(f'{HERE}/{fn}') if not r.startswith('#')]
        for r, line in enumerate(rows):
            for c, ch in enumerate(line):
                y, x = y0 + bob + r, x0 + HEADX[f] + c
                if ch == ' ': continue
                if ch == '.':
                    if lab[y, x] == '': g[y, x] = '.'
                    continue
                g[y, x] = ch; lab[y, x] = 'stamp'
    op = lab != ''
    bw = lab == 'stamp'
    g[(lab == 'hair') & (sh(bw, 1, 0) | sh(bw, 1, 1)) & (g == 'H')] = 'h'
    fill = g.copy()
    g[silmask(g)] = 'K'
    for F_, B_ in lines_for(f):
        fm = np.isin(lab, list(F_)); a, b, c, d_ = n4(np.isin(lab, list(B_)))
        g[fm & (a | b | c | d_)] = 'K'
    g = clean(g, fill)
    for (ox, oy), side, kind in FS.LAYOUT['SE']:
        for r, line in enumerate(FS.eye(EXPR, side, kind)):
            for c, ch in enumerate(line):
                y, x = oy + bob + r, ox + HEADX[f] + EYEDX + c
                if ch in ' .': continue
                if ch == 'h':
                    if lab[y, x] == 'face' and g[y, x] == 's': g[y, x] = 'h'
                    elif lab[y, x] == 'hair': g[y, x] = 'K'
                else:
                    g[y, x] = {'@': 'W', 'K': 'K', 'g': 'g', 'W': 'W'}[ch]
    for (x0, y0, why, rows) in REGION.get(f, []):
        for r, line in enumerate(rows):
            for c, ch in enumerate(line):
                if ch != ' ': g[y0 + r, x0 + c] = ch
    for (x, y), (ch, why) in PATCH.get(f, {}).items():
        g[y, x] = ch
    return lab, g


# wave / strand splits on the side locks, in master coords (polyline vertices)
STRANDS = [[(53.4, 47), (52.6, 50), (52.8, 52)], [(53.6, 56), (54.4, 59), (54, 62)], [(57.4, 51), (56.8, 54)], [(57.4, 58), (58.2, 61), (58, 64)], [(78.6, 51), (78.4, 54)], [(78.6, 58), (79.2, 61)]]
STAMPS = [('bow_block.txt', 44, 27)]
PATCH = {'contact': {(80, 83): ('.', 'far hand: drop leftover outline elbow'), (81, 84): ('.', 'idem')}, 'passing': {}}
# contact arms, hand-drawn rows (x0, y, row; ' ' keeps): near forearm swung forward (sleeve underside, cuff, 4-px mitten in front of the
# skirt; skirt edge runs 1-1-1-1-1-1-3; hem 4-3); far arm swung back, elbow bent, hand behind (right contour 2-3-2-2)
REGION = {'contact': [(x0, y, 'contact arm/hand repaint', [r]) for x0, y, r in [
        (46, 80, '.........KEEEERK'),
        (46, 81, '..........KEEEERKOOO'),
        (46, 82, '.........KEKEEERRKKKKK'),
        (46, 83, '........KEEEKEERRKsssK'),
        (46, 84, '.......KEEEEEKRRRKsssK'),
        (46, 85, '......KEEEEEEEKKKKssSK'),
        (46, 86, '.....KEEEEEEEEEEEKssSK'),
        (46, 87, '....KEEEEEEEEEEEEEKKKE'),
        (46, 90, '.....KKKK'),
        (46, 91, '.........KKK'),
        (76, 75, ' KRRRK....'),
        (76, 76, ' .KRRK....'),
        (76, 77, ' ..KRRK...'),
        (76, 78, ' ..KRRK...'),
        (76, 79, ' ..KRRK...'),
        (76, 80, ' ...KRRK..'),
        (76, 81, ' ...KKKK..'),
        (76, 82, ' ...KsssK.'),
        (76, 83, '     KsSK.'),
        (76, 84, '      KK..'),
    ]]}
def render(g, s=1, bg=None):
    a = np.zeros((N, N, 4), np.uint8)
    if bg is not None: a[:] = (*bg, 255)
    for k, c in RGB.items(): a[g == k] = (*c, 255)
    return cv2.resize(a, (N * s, N * s), interpolation=cv2.INTER_NEAREST)


def save(g, path_noext):
    open(path_noext + '.txt', 'w').write('\n'.join(''.join(r) for r in g) + '\n')
    cv2.imwrite(path_noext + '.png', cv2.cvtColor(render(g), cv2.COLOR_RGBA2BGRA))



if __name__ == '__main__':
    os.makedirs(HERE + '/_work', exist_ok=True)
    for f in ('contact', 'passing'):
        lab, g = build(f)
        save(g, f'{HERE}/walk_SE_{f}')
        cv2.imwrite(f'{HERE}/_work/prev_{f}.png', cv2.cvtColor(render(g, 6, (110, 110, 110)), cv2.COLOR_RGBA2BGRA))
