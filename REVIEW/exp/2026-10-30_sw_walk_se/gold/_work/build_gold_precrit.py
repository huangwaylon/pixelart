"""Gold frames, walk SE (contact L, passing L), authored to DESIGN_LOCK.md (owner-approved 2026-10-30).

Authoring method (all hand-placed, no rig/renderer input):
 1. SHAPES: every part is a polygon / ellipse with hand-picked vertices in 1x pixel units (head() and body() below), drawn
    back-to-front into a part map (8x supersampled, coverage >= 0.5).
 2. FILL: flat 2-tone per material (base + shadow band on the side away from an upper-left light; hair also gets the one
    L sheen band), plus explicit cast shadows (under obi, under hem, under chin) and fold lines.
 3. LINE (lock 3): closed 1-px K silhouette (inner ring), interior K only on the listed overlaps (LINES), then pixel-perfect
    clean-up (redundant elbows, 2x2 clumps).
 4. FACE (lock 1): facesys.py eye + brow templates at the SE layout (front eye 5 px, far eye 4 px); brows in K where on hair.
 5. PATCH: per-frame hand edits, char by char (PATCH dict: (x, y) -> char, each with a reason).
Writes walk_SE_<key>.txt (char map, '.' = transparent) + walk_SE_<key>.png (128x128 RGBA).

Usage: <pixtools venv python> build_gold.py
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
       'red': ('E', 'R'), 'redfar': ('R', 'R'), 'knot': ('R', 'R'), 'obi': ('O', 'o'), 'sock': ('H', 'h'), 'boot': ('g', 'H')}
# shadow band width (px from the right edge) per part
SHW = {'hairback': 2, 'torso': 3, 'skirt': 3, 'sleeveN': 2, 'hair': 2, 'rlock': 1, 'bun': 2, 'bow': 1, 'bowtail': 1,
       'legB': 1, 'legF': 1, 'bootB': 1, 'bootF': 1, 'obi': 2}


def ell(cx, cy, rx, ry, n=48):
    t = np.radians(np.linspace(0, 360, n, endpoint=False))
    return [(cx + rx * np.cos(a), cy + ry * np.sin(a)) for a in t]


def spans(*rows):
    """hand-placed pixel spans: rows of (y, x0, x1) inclusive -> a part mask (pixel-exact, outline ring included)."""
    return {'spans': rows}


def rast(poly):
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


# ------------------------------------------------------------------------------------------------------------------ shapes
def head(dy):
    P = lambda pts: [(x, y + dy) for x, y in pts]
    return [
        ('hairback', 'hairback', P([(52, 41), (57, 35.5), (60.5, 34.2), (64.5, 33.3), (68, 33.1), (71.5, 33.7), (74.6, 34.8), (77.4, 36.4), (79.6, 38.6), (80.8, 41.8), (81.2, 48), (80.8, 55),
                                    (80.4, 61), (79.6, 64.6), (77.4, 64.6), (76, 60), (61.4, 63.6), (57.6, 65), (53, 65.2),
                                    (49.8, 60), (48.6, 52), (49.2, 45)])),
        ('neck', 'neck', P([(63.6, 58), (70, 58), (70.4, 64), (67.4, 67.6), (63.6, 64)])),
        ('face', 'face', P([(58, 43), (77, 43), (78.5, 48), (78.5, 53), (77.6, 57), (75.4, 60.4), (72.4, 62.7), (69.4, 63.4),
                            (65.6, 62.4), (61.4, 59.6), (58.5, 55.5), (57.5, 49)])),
        ('hair', 'hair', P([(54, 44), (56.8, 39.5), (62, 36.5), (69, 35.8), (75, 37), (79, 40), (80.6, 44),
                            # bangs lower edge, right -> left; tips swept down-left, shorter on the far (right) side
                            (79.6, 46), (78.2, 45.2), (76.6, 47.6), (75.2, 45.2), (72.8, 47.6), (70.8, 45.4), (67.8, 47.8),
                            (65.8, 45.6), (62.8, 48.4), (61.2, 46.8),
                            # near side lock (screen-left) hanging in front of the cheek
                            (59.2, 50.6), (59.8, 56), (60.2, 62), (58, 64.8), (55.4, 59.5), (54, 52)])),
    ]


def body(f, dy):
    """Screen-left = her right side = NEAR side in SE (near arm armN, near leg legB). Legs are planted (no bob)."""
    P = lambda pts: [(x, y + dy) for x, y in pts]
    Q = lambda pts: pts
    if f == 'contact':
        # contact L: left leg (screen-right, legF) forward heel-strike, right leg (screen-left, legB) back on the toe
        legB = [('legB', 'sock', spans((98, 58, 65), (99, 58, 65), (100, 58, 64), (101, 57, 64), (102, 57, 63), (103, 57, 63),
                                       (104, 56, 62), (105, 56, 62), (106, 56, 61), (107, 55, 61), (108, 55, 60), (109, 55, 60))),
                ('bootB', 'boot', spans((110, 54, 60), (111, 54, 60), (112, 54, 60), (113, 54, 61), (114, 54, 62), (115, 55, 63),
                                        (116, 55, 63), (117, 56, 63), (118, 57, 62)))]
        legF = [('legF', 'sock', spans((98, 65, 72), (99, 65, 72), (100, 66, 73), (101, 66, 73), (102, 66, 73), (103, 67, 74),
                                       (104, 67, 74), (105, 67, 74), (106, 68, 74), (107, 68, 75), (108, 68, 75), (109, 69, 75),
                                       (110, 69, 75), (111, 69, 76), (112, 69, 76))),
                ('bootF', 'boot', spans((113, 69, 76), (114, 69, 77), (115, 69, 77), (116, 69, 78), (117, 69, 79), (118, 69, 80),
                                        (119, 69, 81), (120, 69, 81), (121, 69, 81), (122, 69, 80), (123, 69, 79), (124, 70, 77)))]
        legs = legB + legF
        # contact: near arm (her right) swings forward -> hand in front of the skirt; far arm back
        armFar = [('sleeveFar', 'redfar', P([(72, 66), (75.8, 66.6), (78.2, 72), (79.6, 79), (80.2, 85.6), (76, 87.4), (74.6, 81), (73.4, 76)]))]
        handFar = [('handFar', 'skin', P(ell(79.2, 89.8, 2.4, 2.7)))]
        armN = [('sleeveN', 'red', P([(58.6, 66.2), (55, 66.6), (52.6, 72), (52, 79), (53.6, 85.6), (59.6, 87.4), (60.2, 82), (58.4, 76), (58.8, 70)])),
                ('handN', 'skin', P(ell(58.6, 90.4, 3.2, 3.0)))]
    else:
        # passing L: left leg (screen-right) planted straight; right leg (screen-left, near) passes in front, foot lifted behind
        legF = [('legF', 'sock', spans(*[(y, 66, 73) for y in range(98, 105)], *[(y, 67, 73) for y in range(105, 113)])),
                ('bootF', 'boot', spans(*[(y, 66, 73) for y in range(113, 118)], (118, 66, 74), (119, 66, 75), (120, 66, 76),
                                        (121, 66, 77), (122, 66, 77), (123, 66, 77), (124, 67, 76)))]
        legB = [('legB', 'sock', spans((98, 58, 65), (99, 58, 65), (100, 58, 66), *[(y, 59, 66) for y in range(101, 107)],
                                       (107, 59, 65), (108, 58, 65), (109, 58, 64), (110, 57, 63), (111, 56, 62))),
                ('bootB', 'boot', spans((112, 55, 62), (113, 54, 61), (114, 54, 61), (115, 54, 61), (116, 54, 60), (117, 55, 60),
                                        (118, 55, 59), (119, 56, 58)))]
        legs = legF + legB
        armFar = [('sleeveFar', 'redfar', P([(72, 66), (75.8, 66.6), (78, 72), (79.2, 79), (79.8, 86.4), (75, 87.4), (74.2, 81), (73.4, 76)]))]
        handFar = [('handFar', 'skin', P(ell(78.6, 89.2, 2.4, 2.7)))]
        armN = [('sleeveN', 'red', P([(58.2, 66.2), (55, 66.6), (52.8, 72), (52, 79), (52.2, 85.8), (57, 86.8), (57.6, 81), (57.6, 74), (58.6, 70)])),
                ('handN', 'skin', P(ell(54.6, 89.4, 2.5, 2.8)))]
    dress = [('torso', 'red', P([(59.4, 63.4), (71, 63.4), (74.6, 65.8), (75.6, 70), (75, 75.5), (74, 77), (56.6, 77), (55.2, 73), (55, 68.5), (56.4, 65.4)])),
             ('skirt', 'red', P([(56.6, 81), (74.2, 81), (76.4, 86), (78.4, 92.5), (79, 100), (75, 101.2), (65, 101.2), (57, 100.4),
                                 (48.6, 99.2), (50.4, 92.5), (53.4, 86)])),
             ('obi', 'obi', P([(56, 76), (74.6, 76), (74.6, 82), (56, 82)]))]
    return armFar + legs + dress + handFar + armN


def lines_for(f):
    front_leg = ({'legF', 'bootF'}, {'legB', 'bootB'}) if f == 'contact' else ({'legB', 'bootB'}, {'legF', 'bootF'})
    return [front_leg,                                                            # leg/leg
            ({'sleeveN', 'handN', 'handFar'}, {'torso', 'obi', 'skirt'}),         # arm over body
            ({'torso', 'skirt', 'obi'}, {'sleeveFar'}),                           # body over the far arm (arm/body edge)
            ({'sleeveN'}, {'handN'}), ({'sleeveFar'}, {'handFar'}),               # hand/sleeve (cuff)
            ({'hair', 'rlock'}, {'face'}), ({'face'}, {'hairback'}),              # bangs/face
            ({'bow', 'bowtail', 'knot'}, {'hair', 'hairback', 'bun', 'rlock'}),           # bow/hair
            ({'face'}, {'neck'})]                                                 # chin/neck


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


def build(f):
    bob = 1 if f == 'contact' else 0
    lab, mat = compose(body(f, bob) + head(bob))
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
    # obi: lower edge in shadow; skirt under obi in shadow
    g[L('obi') & ~sh(L('obi'), -1, 0)] = 'o'
    g[L('skirt') & sh(L('obi'), 1, 0)] = 'R'
    # sleeve openings: bottom row of each sleeve = inside of the sleeve (R)
    for s_ in ('sleeveN',):
        m = L(s_); g[m & ~sh(m, -1, 0)] = 'R'
    # torso: kimono collar (R lapel lines) + skin V is the neck part
    for pts in ([(62, 64 + bob), (67, 69 + bob)], [(72, 64 + bob), (66, 76 + bob)]):
        for y, x in line_px(pts):
            if lab[y, x] == 'torso': g[y, x] = 'R'
    # skirt fold lines
    for pts in ([(61.5, 83 + bob), (59.5, 99 + bob)], [(70.5, 83 + bob), (71.5, 99 + bob)]):
        for y, x in line_px(pts):
            if lab[y, x] == 'skirt': g[y, x] = 'R'
    # legs: thigh skin (hem -> sock top), red sock band, sock
    sock_top = 104
    for nm in ('legB', 'legF'):
        lg = L(nm)
        thigh = lg & (yy < sock_top)
        g[thigh] = 's'
        g[thigh & ~sh(lg, 0, -1)] = 'S'
        g[lg & (sh(L('skirt'), 1, 0))] = 'S'
        g[lg & (yy == sock_top)] = 'E'
    # hands: lower-right shade
    for nm in ('handN', 'handFar'):
        hm = L(nm); g[hm & ~sh(hm, -1, -1)] = 'S'
    # hair: sheen band (L) on the crown, broken into strands; strand lines (h) up from the bang valleys; shadow under the bow
    hr = L('hair')
    d = np.hypot((xx - 67.5) / 12.0, (yy - (49.5 + bob)) / 11.0)
    ang = np.degrees(np.arctan2(yy - (49.5 + bob), xx - 67.5))
    band = hr & (d > 0.86) & (d < 0.97) & (ang > -132) & (ang < -48) & ~np.isin(xx, [62, 68, 73])
    g[band] = 'L'
    for x0, y0 in ((76, 49), (71.5, 47.8), (66, 47.6), (61, 48)):
        for k in range(1, 4):
            y, x = int(y0 + bob) - k, int(round(x0))
            if lab[y, x] == 'hair' and g[y, x] == 'H': g[y, x] = 'h'
    hb = L('hairback'); a_, b_, c_, d_ = n4(hr)
    g[hb & (a_ | b_ | c_ | d_)] = 'h'                     # strand split between the near lock and the side mass
    g[hb & ~sh(hb, -1, 0)] = 'h'                          # lock tips
    # hand-drawn stamps (bow + bun): '.' clears, ' ' keeps, anything else is placed as-is (own K lines included)
    for fn, x0, y0 in STAMPS:
        rows = [r.rstrip('\n') for r in open(f'{HERE}/{fn}') if not r.startswith('#')]
        for r, line in enumerate(rows):
            for c, ch in enumerate(line):
                y, x = y0 + bob + r, x0 + c
                if ch == ' ': continue
                if ch == '.':
                    if lab[y, x] in ('', 'bun'): g[y, x] = '.'; lab[y, x] = ''
                    continue
                g[y, x] = ch; lab[y, x] = 'stamp'
    op = lab != ''
    bw = lab == 'stamp'                                   # the bow shades the hair right under it
    g[np.isin(lab, ['hair', 'hairback']) & (sh(bw, 1, 0) | sh(bw, 1, 1)) & (g == 'H')] = 'h'
    fill = g.copy()
    # ---- line: silhouette + listed overlaps
    g[silmask(g)] = 'K'
    for F_, B_ in lines_for(f):
        fm = np.isin(lab, list(F_)); a, b, c, d_ = n4(np.isin(lab, list(B_)))
        g[fm & (a | b | c | d_)] = 'K'
    g = clean(g, fill)
    # ---- face
    for (ox, oy), side, kind in FS.LAYOUT['SE']:
        for r, line in enumerate(FS.eye(EXPR, side, kind)):
            for c, ch in enumerate(line):
                y, x = oy + bob + r, ox + c
                if ch in ' .': continue
                if ch == 'h':
                    if lab[y, x] == 'face' and g[y, x] == 's': g[y, x] = 'h'
                    elif lab[y, x] in ('hair', 'rlock'): g[y, x] = 'K'
                else:
                    g[y, x] = {'@': 'W', 'K': 'K', 'g': 'g', 'W': 'W'}[ch]
    for (x0, y0, why, rows) in REGION.get(f, []):      # hand-drawn region repaints (' ' keeps)
        for r, line in enumerate(rows):
            for c, ch in enumerate(line):
                if ch != ' ': g[y0 + r, x0 + c] = ch
    for (x, y), (ch, why) in PATCH.get(f, {}).items():
        g[y, x] = ch
    return lab, g


PATCH = {'contact': {(49, 97): ('.', 'skirt edge run 50x3'), (50, 97): ('K', 'skirt edge run 50x3')}, 'passing': {}}
REGION = {'contact': [
    (50, 86, 'near hand in front of the skirt: cuff line + 4-px mitten hand; skirt edge runs 7-3-3-3-2 (monotone)', [
        '...KEEEERKERE',
        '...KRRRRRKERE',
        '...KKKKKKKKKE',
        '..KEEEKssssKE',
        '..KEEEKsssSKE',
        '..KEEEKsssSKE',
        '.KEEEEEKssSKE',
        '.KEEEEEEKKKEE',
        '.KEEEEEEEEREE',
        '             ',
        '             ',
        'K            ']),
    (73, 85, 'far hand under its sleeve, flush with the sleeve edge (x79) so the right contour stays 2 clean runs', [
        'RRKRRRK...',
        'RRKRRRK...',
        'RRKRRRK...',
        'RRKKKKK...',
        'RRKsssK...',
        'RRKsssK...',
        'RRKssSK...',
        'RRRKSK....',
        'RRRRKK....',
        'RRRRRK....']),
  ], 'passing': [
    (49, 84, 'near hand: steps 1 px in from the sleeve (x52 -> x53) so sleeve and skirt contours are separate monotone stretches; '
             'hem bottom-left runs 1-4-5', [
        '   KEERKEE',
        '   KRRRKEE',
        '   .KKKKKE',
        '   .KsssKE',
        '   .KsssKE',
        '   .KssSKE',
        '   .KssSKE',
        '  ..KKKKEE',
        '...KEEEEEE',
        '...KEEEEEE',
        '...KEEEEEE',
        '..KEEEEEEE',
        '..KEEEEEEE',
        '.KEEEEEEEE',
        'KEEEEEEEEE',
        '.KKKKEEEEE',
        '.....KKKKK']),
    (73, 85, 'far hand under its sleeve (3-px, farther away), skirt edge x78 below', [
        'RRKRRRK...',
        'RRKRRRK...',
        'RRKKKKK...',
        'RRKsssK...',
        'RRKsssK...',
        'RRKssSK...',
        'RRRKKK....',
        'EERRRK....']),
]}
# hand-drawn repaints of small shapes, in final frame coords (x0, y0, reason, rows)
REGION_OFF = {'contact': [
    (50, 86, 'near hand in front of the skirt: clean cuff line + 4-px mitten hand; skirt edge runs 7-4-4-3', [
        '...KEEEERKERE',
        '...KRRRRRKERE',
        '...KKKKKKKKKE',
        '..KEEEKssssKE',
        '..KEEEKsssSKE',
        '..KEEEKsssSKE',
        '..KEEEEKssSKE',
        '.KEEEEEEKKKRE',
        '.KEEEEEEEEERE']),
    (74, 86, 'far hand under its sleeve at the skirt edge: cuff line + hand, right edge runs 8-6-1-1', [
        'RRKRRRK...',
        'RRKRRRRK..',
        'RRKKKKKK..',
        'RRKssssK..',
        'RRKsssSK..',
        'RRKsssSK..',
        'RRRKssSK..',
        'RRRRKKK...',
        'RRRRRK....']),
]}
STAMPS = [('bow_block.txt', 44, 27)]


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
