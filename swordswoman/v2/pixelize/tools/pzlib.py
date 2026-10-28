"""pzlib: shared loading / palette lock / placement for the pixelize bake-off."""
import json, os, sys, numpy as np
from PIL import Image
from scipy import ndimage as nd

ROOT = '/Users/waylonhuang/Documents/other/pixelart/swordswoman/'
SRCDIR = ROOT + 'v2/hair/turnE_final/'
SRC = {'front': 'front.png', 'back': 'back.png', 'left': 'left.png', 'right': 'right.png',
       'S': 'iso_S.png', 'SE': 'iso_SE_fixed.png', 'E': 'iso_E.png', 'NE': 'iso_NE.png', 'N': 'iso_N.png'}
CELL = {48: 64, 64: 96, 80: 112, 96: 128}
sys.path.insert(0, ROOT + 'v2/final/tools')
from seg import seg  # noqa: E402

PALFILE = ROOT + 'v2/final/palette.json'
PAL18 = ROOT + 'v2/pixelize/palette.json'  # locked 16 + socks ramp D/d
ALLOW = {'K': 'K', 'hair': 'KhHgLW', 'boot': 'KhHgL', 'red': 'ReEK', 'skin': 'sSmk', 'obi': 'oOQ', 'socks': 'KDd', '?': None}
SOCKS = (0.60, 0.86)  # sock band (fraction of figure height); dark 'hair' pixels there are socks


def seg2(x, m):
    L = seg(x, m, 0, x.shape[0] - 1).astype('<U6')
    yy = np.arange(x.shape[0])[:, None] / max(1, x.shape[0] - 1) * np.ones(x.shape[:2])
    band = (yy > SOCKS[0]) & (yy <= SOCKS[1])
    L[(L == 'hair') & band] = 'socks'
    L[(L == 'K') & band & (x.max(-1) >= 30)] = 'socks'  # sock fill is near-black (max 31-43); true outline stays K
    return L


def srcpath(view, src=None):
    if src: return src
    if view in SRC and os.path.exists(SRCDIR + SRC[view]): return SRCDIR + SRC[view]
    return SRCDIR + f'iso_{view}.png'


def load_pal(path=None):
    d = json.load(open(path or PALFILE))['colors']
    keys = list(d)
    hx = [(v['hex'] if isinstance(v, dict) else v[0]) for v in d.values()]
    rgb = np.array([[int(h[i:i + 2], 16) for i in (1, 3, 5)] for h in hx], float)
    mat = {k: (v.get('material', []) if isinstance(v, dict) else []) for k, v in d.items()}
    import re
    for k, v in d.items():  # extras (palette24): join the material sets of their nearest locked colour
        mm = re.search(r'near (\w)', v.get('desc', '')) if isinstance(v, dict) else None
        if mm and k not in ''.join(a for a in ALLOW.values() if a):
            for mt, al in ALLOW.items():
                if al and mm.group(1) in al: ALLOW[mt] = al + k
    return keys, rgb, mat


def rgb2lab(x):
    x = np.asarray(x, float) / 255.
    x = np.where(x > 0.04045, ((x + 0.055) / 1.055) ** 2.4, x / 12.92)
    M = np.array([[0.4124, 0.3576, 0.1805], [0.2126, 0.7152, 0.0722], [0.0193, 0.1192, 0.9505]])
    xyz = x @ M.T / np.array([0.95047, 1.0, 1.08883])
    f = np.where(xyz > 0.008856, np.cbrt(xyz), 7.787 * xyz + 16 / 116)
    return np.stack([116 * f[..., 1] - 16, 500 * (f[..., 0] - f[..., 1]), 200 * (f[..., 1] - f[..., 2])], -1)


def fgmask(x):
    return (x.min(-1) < 215) | (x.max(-1) - x.min(-1) > 30)


def load(view, src=None):
    """illustration cropped to figure bbox (RGB float), mask with small holes (eye whites) filled"""
    x = np.array(Image.open(srcpath(view, src)).convert('RGB')).astype(float)
    m = fgmask(x)
    lab, n = nd.label(~m)
    if n:
        sizes = nd.sum(np.ones_like(lab), lab, range(1, n + 1))
        border = set(np.unique(np.r_[lab[0], lab[-1], lab[:, 0], lab[:, -1]]))
        for i, s in enumerate(sizes, 1):
            if i not in border and s < m.size * 0.0015: m[lab == i] = True
    ys, xs = np.where(m)
    y0, y1, x0, x1 = ys.min(), ys.max(), xs.min(), xs.max()
    x = x[y0:y1 + 1, x0:x1 + 1].copy(); m = m[y0:y1 + 1, x0:x1 + 1]
    x[~m] = 255
    return x, m


def materials(x, m):
    L = seg2(x, m)
    L[m & (x.min(-1) > 200) & (x.max(-1) - x.min(-1) < 40) & (L != 'obi')] = 'W'
    return L


def resize(x, w, h, how=Image.LANCZOS):
    return np.array(Image.fromarray(np.clip(x, 0, 255).astype(np.uint8)).resize((w, h), how)).astype(float)


def figsize(m, h):
    H, W = m.shape
    return max(1, round(W * h / H)), h


def snap(img, alpha, keys, rgb, use_mat=True):
    """palette-lock a low-res RGB image (material-constrained nearest in Lab). returns char grid ('.' = transparent)"""
    lab = rgb2lab(img); plab = rgb2lab(rgb)
    d = ((lab[:, :, None, :] - plab[None, None]) ** 2).sum(-1)
    idx = d.argmin(-1)
    if use_mat:
        L = seg2(img, alpha)
        for mt, al in ALLOW.items():
            if al is None: continue
            cols = [keys.index(c) for c in al if c in keys]
            if mt == 'socks' and not any(c in keys for c in 'Dd'): cols = [keys.index(c) for c in ALLOW['hair'] if c in keys]
            sel = (L == mt) & alpha
            if sel.any() and cols: idx[sel] = np.array(cols)[d[sel][:, cols].argmin(1)]
    g = np.array(keys, dtype='<U1')[idx]
    g[~alpha] = '.'
    return g


def outline_sil(g):
    a = g != '.'
    p = np.pad(a, 1)
    e = a & ~(p[:-2, 1:-1] & p[2:, 1:-1] & p[1:-1, :-2] & p[1:-1, 2:])
    g = g.copy(); g[e] = 'K'
    return g


def place(sub, h, pad=0):
    """put grid (figure bbox h x w at offset pad,pad inside sub) into cell N x N, soles on row N-4, centred.
    returns grid, (ox,oy) = figure bbox origin in the cell"""
    N = CELL.get(h, int(h * 1.35))
    hh, ww = sub.shape; w = ww - 2 * pad
    g = np.full((N, N), '.', dtype='<U1')
    oy = N - 3 - h; ox = (N - w) // 2
    ys, xs = oy - pad, ox - pad
    y0, x0 = max(0, ys), max(0, xs)
    y1, x1 = min(N, ys + hh), min(N, xs + ww)
    g[y0:y1, x0:x1] = sub[y0 - ys:y1 - ys, x0 - xs:x1 - xs]
    return g, (ox, oy)


def render(g, keys, rgb, s=1):
    a = np.zeros(g.shape + (4,), np.uint8)
    for i, k in enumerate(keys):
        a[g == k, :3] = rgb[i]; a[g == k, 3] = 255
    im = Image.fromarray(a, 'RGBA')
    return im.resize((g.shape[1] * s, g.shape[0] * s), Image.NEAREST) if s != 1 else im


def save(g, path, keys, rgb, meta):
    open(path + '.txt', 'w').write('\n'.join(''.join(r) for r in g) + '\n')
    render(g, keys, rgb).save(path + '.png')
    json.dump(meta, open(path + '.json', 'w'))


def read(path):
    g = np.array([list(l.rstrip('\n')) for l in open(path + '.txt') if l.strip() and not l.startswith(';')])
    return g, json.load(open(path + '.json'))


def clean_orphans(g, keep='W'):
    """isolated pixels (no same-colour 8-neighbour, fully inside) -> majority of 4-neighbours"""
    g = g.copy(); H, W = g.shape
    for _ in range(2):
        out = g.copy()
        for r in range(1, H - 1):
            for c in range(1, W - 1):
                v = g[r, c]
                if v == '.' or v in keep: continue
                nb8 = g[r - 1:r + 2, c - 1:c + 2].ravel()
                if '.' in nb8: continue
                if (nb8 == v).sum() == 1:
                    nb = [g[r - 1, c], g[r + 1, c], g[r, c - 1], g[r, c + 1]]
                    nb = [n for n in nb if n not in keep]
                    if nb: out[r, c] = max(set(nb), key=nb.count)
        g = out
    return g
