"""shade_lines.py -- round 3 (Amendment 2: lines + shading) for lock_chain.py. All shapes come from the 3D passes (camera normal,
depth, rest position 'rpos'); nothing is painted per frame.
 tones()       N.L per cell from the camera normals and one KEY light from the screen's upper left (smoothed inside each material),
               3 bands: shadow / base / highlight (highlight only where the material has one: red cloth e, obi Q).
 clean_bands() deliberate cel shapes: per material, 1-px shadow spurs/notches removed (opening/closing, the material edge counts as
               shadow so shadows may touch it), islands < MINB cells merged, band hysteresis against the previous frame moved by the
               surface-point flow (shapes do not pop).
 cast()        occlusion shadows from the labels + depth: under the bangs on the forehead (1 px), the neck (chin), the thighs under the
               skirt hem (2 px), the dress under the obi (1 px), the far leg where the legs overlap.
 marks()       surface-attached marks from the rest position (stable on the model): the hair highlight ring (one band, broken into
               clumps), hair clump separations (every CLUMP_DEG of azimuth around the head, below the ring), skirt fold lines at the
               8 skirt-panel seams (the rig's skirt bones). Drawn 1 px, pixel-perfect, >= MINLEN.
 form_pairs    extra interior form lines: collar V (neck skin | dress), obi edges (obi | dress).
 selout()      line colour by context: an interior line on a lit cell takes the darker tone of the material it sits in; on a shadow cell
               it is K. The outer silhouette stays K everywhere."""
import os
import numpy as np
from scipy import ndimage as nd
CROSS = nd.generate_binary_structure(2, 1)
KEY = np.array([-0.55, 0.62, -0.56]); KEY /= np.linalg.norm(KEY)  # camera space: x right, y up, z into the screen -> upper-left, toward camera
# material: (shadow, base, highlight or None, shadow below N.L, highlight above N.L)
TONES = {'hair': ('h', 'H', None, 0.10, 9), 'dress': ('R', 'E', 'e', -0.04, 0.50), 'sleeve': ('R', 'E', 'e', 0.10, 0.75),
         'bow': ('E', 'e', None, 0.18, 9), 'obi': ('o', 'O', 'Q', -0.20, 0.12), 'skin': ('S', 's', None, -0.12, 9),
         'socks': ('h', 'H', None, 0.15, 9), 'boots': ('H', 'g', None, 0.22, 9)}
NSIG = {'dress': 4.0, 'sleeve': 2.0, 'skin': 2.0, 'socks': 1.5, 'boots': 1.5, 'hair': 2.0, 'bow': 1.0, 'obi': 1.5}
HYS = 0.06
MINB = {'dress': 6, 'sleeve': 5, 'hair': 4, 'skin': 3, 'socks': 3, 'boots': 3, 'bow': 3, 'obi': 3}  # smallest band shape (cells)
RING_Z, RING_W, RING_LIT, RING_ROWS = 1.445, 0.0110, 0.05, 2   # hair highlight ring: rest height (m), half width, min N.L, rows
HEAD_C = (0.0, -0.02); CLUMP_DEG, CLUMP_W, CLUMP_ZMAX = 30.0, 0.0028, 1.43   # clump seams every 20 deg (half width in m of arc)
PELV_C = (0.0, 0.003); PANEL_DEG0, PANEL_W, SKIRT_Z = 22.5, 0.0035, (0.60, 0.765)  # skirt panel seams at 22.5 + 45 k deg
MINLEN = 4


def tones(F, mat1, MN, blocks, P):
    v = (F['nrm'] * KEY).sum(-1); N = mat1.shape[0]; out = np.full((N, N), 0.3)
    for k, m_ in enumerate(MN):
        m = F['mid'] == k
        if not m.any(): continue
        sg = NSIG[m_] * P; num = nd.gaussian_filter(np.where(m, v, 0), sg); den = nd.gaussian_filter(m.astype(float), sg)
        vs = np.where(m, num / np.maximum(den, 1e-6), 0); bm = blocks(m); c = bm.sum(-1); s = (blocks(vs) * bm).sum(-1); sel = (mat1 == k) & (c > 0)
        out[sel] = s[sel] / c[sel]
    return out


def bands(ndl, mat1, inside, MN, prev=None):
    b = np.full(mat1.shape, -1, np.int8)
    for k, m_ in enumerate(MN):
        sh, ba, hi, t0, t1 = TONES[m_]; sel = inside & (mat1 == k)
        x = np.where(ndl < t0, 0, np.where(ndl > t1, 2, 1)).astype(np.int8)
        if hi is None: x = np.minimum(x, 1)
        if prev is not None:  # hysteresis near either threshold: keep last frame's band (moved by the flow)
            near = (np.abs(ndl - t0) < HYS) | (np.abs(ndl - t1) < HYS)
            x = np.where(near & (prev >= 0) & (prev <= (2 if hi else 1)), prev, x)
        b[sel] = x[sel]
    return b


def clean_bands(b, mat1, inside, MN):
    for k, m_ in enumerate(MN):
        M = inside & (mat1 == k)
        if not M.any(): continue
        for lvl in (0, 2):
            S = M & (b == lvl)
            if not S.any(): continue
            S = nd.binary_opening(S | ~M, CROSS) & M      # 1-px spurs/lines of this band go (the material edge counts as band)
            S = nd.binary_closing(S, CROSS) & M           # 1-px notches fill
            lab, n = nd.label(S)
            for i in range(1, n + 1):
                if (lab == i).sum() < MINB[m_]: S[lab == i] = False
            b[M & (b == lvl) & ~S] = 1; b[S] = lvl
        if TONES[m_][2]:  # highlight = a rim on the lit (upper/left) side of the shape, never a floating blob
            if m_ == 'obi':  # obi: Q only on its top edge row (a 1-px sheen along the band)
                near = M & ~np.roll(M, 1, 0)
            else:
                lit_edge = M & (~np.roll(M, 1, 0) | ~np.roll(M, 1, 1))
                near = nd.binary_dilation(lit_edge, CROSS, iterations=2) & M
            b[M & (b == 2) & ~near] = 1
            H2 = M & (b == 2); lab, n = nd.label(H2)
            for i in range(1, n + 1):
                if (lab == i).sum() < MINB[m_]: b[lab == i] = 1
        base = M & (b == 1); lab, n = nd.label(base)
        for i in range(1, n + 1):  # tiny base islands inside a shadow / highlight join their surroundings
            c = lab == i
            if c.sum() < MINB[m_]:
                ring = nd.binary_dilation(c, CROSS) & M & ~c
                if ring.any(): b[c] = np.bincount(b[ring].astype(int) + 1).argmax() - 1
    return b


def cast(b, mat1, sub1, inside, outline, F, MI, SI, blocks):
    """occlusion shadows (band 0) where a nearer part overhangs; returns the cast mask (for the record)"""
    N = b.shape[0]; up = lambda m, k: np.roll(m, k, 0)
    fill = inside & ~outline; c = np.zeros_like(fill)
    face = fill & (sub1 == SI['face']) & (mat1 == MI['skin']); hair = (mat1 == MI['hair']) & inside
    c |= face & up(hair, 1)                                                   # under the bangs (1 px)
    c |= fill & (sub1 == SI['neck'])                                          # neck under the chin
    ys = np.nonzero(face.any(1))[0]
    if len(ys):                                                               # shadow-side jaw rim: 1 px on the face's right edge, lower half
        low = np.zeros_like(face); low[(ys.min() + ys.max()) // 2 + 1:] = True
        c |= face & low & ~np.roll(face, -1, 1) & np.roll(face, 1, 1)
    dress = inside & (mat1 == MI['dress']) & (sub1 == SI['torso'])
    thigh = fill & (mat1 == MI['skin']) & np.isin(sub1, [SI['leg.L'], SI['leg.R']])
    c |= thigh & (up(dress, 1) | up(dress, 2))                                # thighs under the skirt hem (2 px)
    c |= fill & (mat1 == MI['dress']) & up(inside & (mat1 == MI['obi']), 1)   # dress under the obi (1 px)
    dep = blocks(np.where(np.isfinite(F['dep']), F['dep'], 99)).min(-1)
    for a, o in (('leg.L', 'leg.R'), ('leg.R', 'leg.L')):                     # between the legs: the farther leg next to the nearer one
        A = fill & (sub1 == SI[a]); B = inside & (sub1 == SI[o])
        nb = A & (np.roll(B, 1, 1) | np.roll(B, -1, 1))
        db = nd.grey_erosion(np.where(B, dep, 99), size=(1, 3))
        c |= nb & (dep > db + 0.01)
    b[c] = 0
    return c


def marks(F, mat1, sub1, inside, outline, ndl, b, MI, SI, blocks, thin_pp):
    """surface-attached 1-px marks from the rest position: ring (hair highlight), clump seams (hair), panel seams (skirt)"""
    out = {}
    if 'rp8' not in F or os.environ.get('SL_NOMARKS'): return {k: np.zeros(mat1.shape, bool) for k in ('ring', 'clump', 'fold')}
    rp = F['rp8']; mid = F['mid']; fill = inside & ~outline
    hair8 = mid == MI['hair']; dress8 = mid == MI['dress']
    phi_h = np.arctan2(rp[..., 0] - HEAD_C[0], rp[..., 1] - HEAD_C[1]); r_h = np.hypot(rp[..., 0] - HEAD_C[0], rp[..., 1] - HEAD_C[1])
    st = np.radians(CLUMP_DEG); dh = np.abs((phi_h + st / 2) % st - st / 2) * r_h
    phi_s = np.arctan2(rp[..., 0] - PELV_C[0], rp[..., 1] - PELV_C[1]); r_s = np.hypot(rp[..., 0] - PELV_C[0], rp[..., 1] - PELV_C[1])
    sp = np.radians(45.0); ds = np.abs((phi_s - np.radians(PANEL_DEG0) + sp / 2) % sp - sp / 2) * r_s
    cov = lambda m8, base8: blocks(m8).sum(-1) / np.maximum(blocks(base8).sum(-1), 1)
    hairc = fill & (mat1 == MI['hair']) & (sub1 == SI['hair'])
    ring = hairc & (cov(hair8 & (np.abs(rp[..., 2] - RING_Z) < RING_W), hair8) >= 0.3) & (ndl > RING_LIT)
    top = ring & ~np.roll(ring, 1, 0); ring = top | (np.roll(top, 1, 0) & ring) if RING_ROWS > 1 else top  # a 1-2 row band
    clump = hairc & (cov(hair8 & (dh < CLUMP_W) & (rp[..., 2] < CLUMP_ZMAX), hair8) >= 0.25) & (b >= 1)
    skirt = fill & (mat1 == MI['dress']) & (sub1 == SI['torso'])
    fold = skirt & (cov(dress8 & (ds < PANEL_W) & (rp[..., 2] > SKIRT_Z[0]) & (rp[..., 2] < SKIRT_Z[1]), dress8) >= 0.25) & (b >= 1)
    for k, m in (('clump', clump), ('fold', fold)):
        m = thin_pp(m); lab, n = nd.label(m, np.ones((3, 3)))
        for i in range(1, n + 1):
            if (lab == i).sum() < MINLEN + (1 if k == 'fold' else 0): m[lab == i] = False
        out[k] = m
    lab, n = nd.label(ring, np.ones((3, 3)))
    for i in range(1, n + 1):
        if (lab == i).sum() < 2: ring[lab == i] = False
    out['ring'] = ring & ~out['clump']                                          # the ring breaks where a clump seam crosses it
    return out


def selout(g, iline, b, mat1, MN, keepK=None):
    """colour of interior line px: K on shadow cells (and where keepK), else the darker tone of the material the line sits in"""
    for k, m_ in enumerate(MN):
        sel = iline & (mat1 == k) & (b >= 1)
        if keepK is not None: sel &= ~keepK
        g[sel] = TONES[m_][0]
    g[iline & ((b <= 0) | (keepK if keepK is not None else False))] = 'K'
    return g


def paint(b, mat1, sub1, inside, MN, MI, SI):
    g = np.full(b.shape, '.', dtype='<U1')
    for k, m_ in enumerate(MN):
        sh, ba, hi, _, _ = TONES[m_]; sel = inside & (mat1 == k)
        g[sel & (b == 0)] = sh; g[sel & (b == 1)] = ba
        if hi: g[sel & (b == 2)] = hi
    face = inside & (sub1 == SI['face']) & (mat1 == MI['skin']) & (b != 0); g[face] = 's'  # face skin flat s (only cast shadow on it)
    return g
