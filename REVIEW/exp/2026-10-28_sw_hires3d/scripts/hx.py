"""hx.py: shared lib for the HIRES3D experiment (render styles, downscalers, fix pass).  Run with the PixelOE venv
(.models/pixelize/pixeloe/venv/bin/python -I), which has numpy scipy opencv torch skimage pillow.
Hi-res frames: big/<clip>/<clip>_fNN_{guide,shade,lum,nrm,dep}.png, 192 cell at 8x (1536 px); the in-game 128 cell = crop 256..1280 (1024 px,
8 hi-res px per sprite px, pivot (64,120) in the cell)."""
import os, sys, json, subprocess, numpy as np, cv2
from PIL import Image
from scipy import ndimage as nd
EXP = '/Users/waylonhuang/Documents/other/pixelart/REVIEW/exp/2026-10-28_sw_hires3d/'
ROOT = '/Users/waylonhuang/Documents/other/pixelart/'
SW = ROOT + 'swordswoman/'
sys.path.insert(0, SW + 'v2/pixelize/tools')
import pzlib as Z  # noqa: E402
import pz as PZ  # noqa: E402  (kcentroid, pixeloe, cleanup)
P = 8; N = 128; OFF = 256
KEYS, RGB, _ = Z.load_pal(Z.PAL18)
CH = {k: i for i, k in enumerate(KEYS)}
def hexc(k): return RGB[CH[k]]
# rig matid colours (sRGB) -> material
MATS = {'hair': (61, 50, 53), 'dress': (192, 59, 61), 'skin': (248, 218, 194), 'sleeve': (142, 34, 44), 'socks': (38, 42, 71),
        'boots': (42, 34, 42), 'bow': (232, 96, 79), 'obi': (69, 56, 73), 'eyes': (85, 128, 162)}
MN = list(MATS); MC = np.array([MATS[k] for k in MN], float)
# cel ramps (dark, base, light) from the locked palette + lum bias per material
RAMP = {'hair': 'hHg', 'boots': 'hHg', 'dress': 'REe', 'sleeve': 'REe', 'bow': 'REe', 'skin': 'Sss', 'obi': 'oOQ', 'socks': 'DDd', 'eyes': 'hhg'}
BIAS = {'sleeve': 0.8, 'bow': 1.25, 'skin': 1.15, 'hair': 0.78, 'boots': 0.85}
T1, T2 = 0.22, 0.80  # linear-lum thresholds shadow | base | light (after smoothing)
ALLOW = {'hair': 'KhHgL', 'boots': 'KhHgL', 'dress': 'ReEK', 'sleeve': 'ReEK', 'bow': 'ReEK', 'skin': 'sSmK', 'obi': 'oOQK', 'socks': 'KDd', 'eyes': 'KhgLW'}
BG = (0x6e, 0x6e, 0x6e)


def rd16(p):
    a = cv2.imread(p, cv2.IMREAD_UNCHANGED)
    a = a[..., [2, 1, 0, 3]] if a.ndim == 3 and a.shape[2] == 4 else a
    return a.astype(np.float64) / (65535. if a.dtype == np.uint16 else 255.)


def shift(a, dx, dy):
    """integer shift by (dx,dy) sprite px = 8*dx hi-res px (keeps the 8-px grid)"""
    return np.roll(np.roll(a, dy * P, 0), dx * P, 1)


def load(clip, i, dx=0, dy=0):
    st = EXP + f'big/{clip}/{clip}_f{i:02d}_'
    out = {}
    for k in ('guide', 'shade', 'lum', 'nrm', 'dep'):
        a = rd16(st + k + '.png')[OFF:OFF + N * P, OFF:OFF + N * P]
        out[k] = shift(a, dx, dy)
    g = out['guide']; al = g[..., 3] > 0.5
    d = ((g[..., None, :3] * 255 - MC[None, None]) ** 2).sum(-1); mid = d.argmin(-1); mid[~al] = -1
    out['mid'] = mid; out['alpha'] = al
    out['meta'] = json.load(open(EXP + f'big/{clip}/{clip}.json'))['frames'][i]
    return out


# ------------------------------------------------------------------ render styles (hi-res RGB on white + alpha)
def lum_s(F, sig=5.0):
    """lum smoothed inside each material (normalised convolution) -> no bleed across material boundaries"""
    L = F['lum'][..., 0]; out = np.zeros_like(L)
    for j in range(len(MN)):
        m = (F['mid'] == j).astype(float)
        if m.sum() == 0: continue
        num = nd.gaussian_filter(L * m, sig); den = nd.gaussian_filter(m, sig)
        out[m > 0] = (num / np.maximum(den, 1e-6))[m > 0]
    return out


def bands(F, sig=5.0):
    L = lum_s(F, sig); b = np.ones(L.shape, int)
    for j, n in enumerate(MN):
        m = F['mid'] == j; l = L[m] * BIAS.get(n, 1.0)
        b[m] = np.where(l < T1, 0, np.where(l > T2, 2, 1))
    return b


def style_cel(F):
    b = bands(F); img = np.full(F['mid'].shape + (3,), 255.)
    for j, n in enumerate(MN):
        for k in range(3):
            img[(F['mid'] == j) & (b == k)] = hexc(RAMP[n][k])
    return img, F['alpha']


def edges_hi(F, w=6, dthr=0.035):
    """hi-res line mask: silhouette (inner band) + depth discontinuities (far side) + material-group boundaries"""
    al = F['alpha']; dep = F['dep'][..., 0]
    sil = al & ~nd.binary_erosion(al, iterations=w)
    dl = nd.grey_dilation(np.where(al, -dep, -9), size=(3, 3))  # nearest neighbour depth (as -dep max)
    near = -dl
    dd = al & (dep - near > dthr)  # this px is farther than a neighbour by > dthr -> occluded side of an edge
    grp = {'hair': 0, 'boots': 5, 'dress': 1, 'sleeve': 1, 'bow': 2, 'skin': 3, 'obi': 4, 'socks': 5, 'eyes': 6}
    G = np.array([grp[n] for n in MN] + [-1])[F['mid']]  # mid -1 -> last entry
    mb = al & ((G != np.roll(G, 1, 0)) | (G != np.roll(G, 1, 1))) & (G != 6) & (np.roll(G, 1, 0) != 6) & (np.roll(G, 1, 1) != 6)
    inner = nd.binary_dilation(dd | mb, iterations=max(1, w // 2 - 1)) & al
    return sil | inner


def style_celo(F):
    img, al = style_cel(F); img = img.copy(); img[edges_hi(F)] = hexc('K'); return img, al


def style_shade(F):
    s = F['shade']; al = s[..., 3] > 0.5; img = s[..., :3] * 255; img[~al] = 255; return img, al


def style_matid(F):
    g = F['guide']; img = g[..., :3] * 255; img[~F['alpha']] = 255; return img, F['alpha']


STYLES = {'shade': style_shade, 'cel': style_cel, 'celo': style_celo, 'flat': style_matid}


# ------------------------------------------------------------------ downscalers -> (lo RGB float NxN, alpha NxN)
def cells(a):
    return a.reshape(N, P, N, P, *a.shape[2:]).swapaxes(1, 2)


def mat_grid(F):
    """per-cell majority material (cov > 0.5), -1 transparent"""
    c = cells(F['mid']).reshape(N, N, P * P); out = np.full((N, N), -1)
    cov = (c >= 0).mean(-1) > 0.5
    for y, x in zip(*np.nonzero(cov)):
        v = c[y, x][c[y, x] >= 0]; out[y, x] = np.bincount(v).argmax()
    return out


def ds_area(img, al):
    lo = cells(img).mean((2, 3)); a = cells(al.astype(float)).mean((2, 3)) > 0.5; lo[~a] = 255; return lo, a


def ds_kc(img, al):
    hp = img.copy(); hp[~al] = 255
    lo = PZ.kcentroid(hp, 3, line=True, prefilter=True); a = cells(al.astype(float)).mean((2, 3)) > 0.5; lo[~a] = 255; return lo, a


def ds_poe(img, al):
    hp = img.copy(); hp[~al] = 255
    lo = PZ.pixeloe(hp, 2); a = cells(al.astype(float)).mean((2, 3)) > 0.5; lo[~a] = 255; return lo, a


PAF_PY = ROOT + '.models/pixel-art-fixer/venv/bin/python'


def ds_paf(img, al, tag='x'):
    tmp = EXP + f'tmp/paf_{os.getpid()}_{tag}'
    rgba = np.dstack([np.clip(img, 0, 255), al * 255]).astype(np.uint8)
    Image.fromarray(rgba, 'RGBA').save(tmp + '_in.png')
    r = subprocess.run([PAF_PY, '-I', ROOT + 'pipeline/tools/pixelfix.py', tmp + '_in.png', tmp + '_out.png', '--step', '8', '8'], capture_output=True, text=True, cwd=ROOT)
    if r.returncode: raise SystemExit(r.stderr[-800:])
    o = np.array(Image.open(tmp + '_out.png').convert('RGBA')).astype(float)
    os.remove(tmp + '_in.png'); os.remove(tmp + '_out.png')
    o = o[:N, :N]; a = o[..., 3] > 127; lo = o[..., :3]; lo[~a] = 255; return lo, a


def ds_matv(F, style):
    """material majority vote + per-cell mean smoothed lum -> ramp band (palette chars directly); style celo adds no hi-res lines (lines = fix)"""
    mg = mat_grid(F); L = lum_s(F); lc = np.zeros((N, N))
    Lc = cells(L); Mc = cells(F['mid'])
    g = np.full((N, N), '.', dtype='<U1')
    for y, x in zip(*np.nonzero(mg >= 0)):
        j = mg[y, x]; sel = Mc[y, x] == j; l = Lc[y, x][sel].mean() * BIAS.get(MN[j], 1.0)
        g[y, x] = RAMP[MN[j]][0 if l < T1 else 2 if l > T2 else 1]
    return g, mg


DS = {'kc': ds_kc, 'area': ds_area, 'paf': ds_paf, 'poe': ds_poe}


# ------------------------------------------------------------------ fix pass
def snap_mat(lo, a, mg):
    """palette lock, constrained to the cell's rig material ramp (K allowed everywhere it is allowed)"""
    lab = Z.rgb2lab(lo); plab = Z.rgb2lab(RGB)
    d = ((lab[:, :, None, :] - plab[None, None]) ** 2).sum(-1)
    g = np.array(KEYS, dtype='<U1')[d.argmin(-1)]
    for j, n in enumerate(MN):
        cols = [CH[c] for c in ALLOW[n]]; sel = (mg == j) & a
        if sel.any(): g[sel] = np.array(KEYS)[np.array(cols)[d[sel][:, cols].argmin(1)]]
    g[~a] = '.'
    return g


def depth_lines(F, g, mg, thr=0.035):
    """1-px interior lines at sprite level: a cell farther (cell-median depth) than a 4-neighbour by > thr gets K"""
    dep = F['dep'][..., 0]; Dc = cells(np.where(F['alpha'], dep, np.nan)).reshape(N, N, P * P)
    with np.errstate(all='ignore'): dm = np.nanmedian(Dc, -1)
    out = g.copy()
    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        nb = np.roll(np.roll(dm, dy, 0), dx, 1); nbg = np.roll(np.roll(g, dy, 0), dx, 1)
        e = (g != '.') & (nbg != '.') & (dm - nb > thr)
        out[e] = 'K'
    return out


def fix(g, F=None, mg=None, lines=True, stamp=None):
    g = Z.outline_sil(g)
    if lines and F is not None: g = depth_lines(F, g, mg)
    g = Z.clean_orphans(g, keep='WK')
    g = Z.outline_sil(g)
    if stamp is not None: g = paste(g, *stamp)
    return g


def read_grid(p): return np.array([list(l.rstrip('\n')) for l in open(p) if l.strip() and not l.startswith(';')])


def stamp_of(view, expr='neutral'):
    p = SW + f'v2/m96/heads/{view}_{expr}.txt'; ls = open(p).read().splitlines()
    o = [l for l in ls if l.startswith('; origin')][0].split()[2:4]
    return read_grid(p), int(o[0]), int(o[1])


def paste(g, t, x0, y0, clear=None):
    g = g.copy()
    if clear is not None: g[clear] = '.'
    for r in range(t.shape[0]):
        for c in range(t.shape[1]):
            y, x = y0 + r, x0 + c
            if t[r, c] != '.' and 0 <= y < N and 0 <= x < N: g[y, x] = t[r, c]
    return g


def render(g, s=1, bg=BG):
    a = np.zeros(g.shape + (3,), np.uint8); a[:] = bg
    for i, k in enumerate(KEYS): a[g == k] = RGB[i]
    im = Image.fromarray(a); return im.resize((g.shape[1] * s, g.shape[0] * s), Image.NEAREST) if s > 1 else im


def save(g, stem, view, src=None):
    """writes stem.txt/.png/.json in pzlib format (json h/w/ox/oy = sprite bbox, src = illustration) so metrics.py can score it"""
    ys, xs = np.where(g != '.')
    meta = {'method': 'hires3d', 'view': view, 'h': int(ys.max() - ys.min() + 1), 'w': int(xs.max() - xs.min() + 1), 'ox': int(xs.min()), 'oy': int(ys.min()),
            'src': src or Z.srcpath(view), 'pal': Z.PAL18}
    Z.save(g, stem, KEYS, RGB, meta)


def main_comp(g):
    """keep only the largest 8-connected opaque component (drops detached rig-outline crumbs, e.g. the rig bun outline left after the head stamp)"""
    a = g != '.'; lab, n = nd.label(a, np.ones((3, 3)))
    if n <= 1: return g
    sz = nd.sum(a, lab, range(1, n + 1)); g = g.copy(); g[a & (lab != 1 + int(np.argmax(sz)))] = '.'; return g


CLS = {**{c: 'hair' for c in 'hHgL'}, **{c: 'skin' for c in 'sSmk'}, **{c: 'red' for c in 'ReE'}, **{c: 'obi' for c in 'oOQ'}, 'D': 'sock', 'd': 'sock', 'W': 'W', 'K': 'K', '.': '.'}


def band_churn(G, loop=True):
    """sprite-only boiling measure (works on any frame list, e.g. the animate96 pilot): among cells with the same non-K colour class in
    consecutive frames, fraction whose char (shade band) changed"""
    ch = tot = 0
    for i in range(len(G) - (0 if loop else 1)):
        a, b = G[i], G[(i + 1) % len(G)]
        ca = np.vectorize(CLS.get)(a); cb = np.vectorize(CLS.get)(b)
        s = (ca == cb) & ~np.isin(ca, ['.', 'K', 'W']); ch += int((s & (a != b)).sum()); tot += int(s.sum())
    return round(ch / max(1, tot), 4)


def drop_bare_k(g):
    """remove outline crumbs: K pixels with no non-K opaque 8-neighbour (iterated); real outlines always touch fill"""
    g = g.copy()
    while True:
        k = g == 'K'; f = (g != '.') & ~k
        nb = nd.binary_dilation(f, np.ones((3, 3)))
        bad = k & ~nb
        if not bad.any(): return g
        g[bad] = '.'
