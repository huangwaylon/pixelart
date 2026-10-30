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


HAIR, FACE, NECK = master_masks()


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
        legF = [('legF', 'sock', spans(*[(y, 65 + (y - 89) // 4, 65 + (y - 89) // 4 + (7 if y < 101 else 6)) for y in range(89, 114)])),
                ('bootF', 'boot', spans(*[(y, 71, 77) for y in range(114, 119)], (119, 71, 78), (120, 71, 79), (121, 71, 80),
                                        (122, 71, 80), (123, 71, 79), (124, 72, 77)))]
        legB = [('legB', 'sock', spans(*[(y, 58 - (y - 89) // 4, 58 - (y - 89) // 4 + (7 if y < 101 else 6)) for y in range(89, 112)])),
                ('bootB', 'boot', spans((112, 52, 58), (113, 52, 59), (114, 52, 60), (115, 53, 60), (116, 53, 61), (117, 54, 61),
                                        (118, 55, 61), (119, 56, 60)))]
        legs = legB + legF
        # near arm swings forward (bent, hand in front of the obi/skirt); far arm swings back (bent, hand behind the hip)
        armFar = [('sleeveFar', 'redfar', P([(73, 65.6), (76.8, 66.2), (79.8, 71), (81.6, 76.2), (81.2, 80.6), (77.2, 81), (76.2, 76), (74.4, 71)]))]
        handFar = [('handFar', 'skin', P(ell(80.4, 83.2, 2.3, 2.5)))]
        armN = [('sleeveN', 'red', P([(58.6, 65.6), (54.6, 66.2), (52.2, 71), (52.2, 76.4), (54.8, 79.8), (59.6, 82.4), (61.4, 79.2), (58.4, 75.6), (58.6, 70)])),
                ('handN', 'skin', P(ell(62.2, 82.8, 2.6, 2.5)))]
    else:
        # passing L: left leg (screen-right) planted straight; right (near) leg passes in front, knee forward, foot lifted behind
        legF = [('legF', 'sock', spans(*[(y, 66, 72 if y < 101 else 71) for y in range(89, 114)])),
                ('bootF', 'boot', spans(*[(y, 66, 72) for y in range(114, 118)], (118, 66, 73), (119, 66, 74), (120, 66, 75),
                                        (121, 66, 75), (122, 66, 75), (123, 66, 75), (124, 67, 74)))]
        legB = [('legB', 'sock', spans(*[(y, 58 + (y - 89) * 4 // 14, 58 + (y - 89) * 4 // 14 + 7) for y in range(89, 104)],
                                       *[(y, 62 - (y - 104) * 5 // 8, 62 - (y - 104) * 5 // 8 + 6) for y in range(104, 113)])),
                ('bootB', 'boot', spans((113, 56, 62), (114, 55, 62), (115, 55, 62), (116, 55, 61), (117, 55, 61), (118, 56, 61),
                                        (119, 56, 60), (120, 57, 59)))]
        legs = legF + legB
        armFar = [('sleeveFar', 'redfar', P([(73, 65.6), (76.8, 66.2), (79.4, 71), (80.4, 76.6), (79.6, 81.4), (75.4, 82), (75, 77), (74.4, 71)]))]
        handFar = [('handFar', 'skin', P(ell(77, 84.4, 2.4, 2.5)))]
        armN = [('sleeveN', 'red', P([(58.4, 65.6), (54.6, 66.2), (52.4, 71), (52, 76.6), (53, 81), (58.2, 82), (58.6, 77), (58, 72)])),
                ('handN', 'skin', P(ell(56.4, 84.6, 2.6, 2.5)))]
    dress = [('torso', 'red', P([(59, 63.4), (70.6, 63.4), (75, 65.4), (76.6, 69.5), (76.4, 76), (56, 77.6), (55.4, 72), (55.8, 67.4), (57, 65)])),
             ('skirt', 'red', P([(56.4, 81), (75.6, 78), (77.8, 83), (79.8, 88.4), (80.2, 90.2), (73, 91.2), (65, 91.4), (57, 90.8),
                                 (51.8, 90.2), (49.8, 89.2), (49.6, 87.6), (51.6, 84.4), (54.4, 81.6)])),
             ('obi', 'obi', P([(56.2, 76.6), (75.8, 73.4), (76, 79.8), (56.4, 83)]))]
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
    for pts in ([(61, 63 + bob), (66, 69 + bob)], [(71, 63 + bob), (64, 77 + bob)]):
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
                y, x = oy + bob + r, ox + HEADX[f] + c
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
STRANDS = [[(54, 47), (53, 52), (54, 57), (55, 62)], [(58, 50), (57, 55), (58, 60), (59, 65)], [(78, 50), (78, 56), (77, 61)]]
STAMPS = [('bow_block.txt', 44, 27)]
PATCH = {'contact': {}, 'passing': {}}
REGION = {}
