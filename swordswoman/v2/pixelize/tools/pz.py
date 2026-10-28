"""pz.py METHOD VIEW H [--src illus.png] [--out DIR] [--pal palette.json] [--tag T]
Methods: A (palette-locked majority, v2/final ds.py), B (PixelOE contrast + outline expansion), C0 (k-centroid),
C (k-centroid, bilateral prefilter, line-aware), D (Gemini grid-snap; needs --gem image), EB/EC (B/C + cleanup).
Writes OUT/<M>_<VIEW>_<H>.{txt,png,json}.  Run with .scratch/pixtools/venv/bin/python -I."""
import sys, os, argparse, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pzlib as Z
from PIL import Image

PIXELOE = Z.ROOT + '.scratch/pixelize/pixeloe/src/src'
P = 8  # hi-res pixels per sprite pixel


def hires(x, m, h, pad):
    w, _ = Z.figsize(m, h)
    hi = Z.resize(x, w * P, h * P)
    hm = Z.resize(m.astype(float) * 255, w * P, h * P, Image.BOX) > 127
    hi[~hm] = 255
    hp = np.full(((h + 2 * pad) * P, (w + 2 * pad) * P, 3), 255.)
    hp[pad * P:(pad + h) * P, pad * P:(pad + w) * P] = hi
    mp = np.zeros(hp.shape[:2], bool); mp[pad * P:(pad + h) * P, pad * P:(pad + w) * P] = hm
    return hp, mp, w


def low_alpha(lo):
    return Z.fgmask(lo)


def meth_A(x, m, h, keys, rgb, args):
    import importlib
    sys.path.insert(0, Z.ROOT + 'v2/final/tools')
    ds = importlib.import_module('ds')
    if args.pal: raise SystemExit('A uses the locked palette only')
    ds.illus = lambda v: (x, m)
    N = Z.CELL[h]
    g, _ = ds.down('X', h=h, F4=4, top=0, foot=N - 4, N=N)
    g = np.array(g)
    w, _ = Z.figsize(m, h)
    return g, ((N - w) // 2, N - 3 - h)


def pixeloe(hp, thickness=2):
    sys.path.insert(0, PIXELOE)
    import torch
    from pixeloe.torch.pixelize import pixelize
    t = torch.from_numpy(hp / 255.).permute(2, 0, 1)[None].float()
    with torch.no_grad():
        o = pixelize(t, pixel_size=P, thickness=thickness, mode='contrast', do_color_match=True,
                     no_post_upscale=True, backend='torch')
    if isinstance(o, (tuple, list)): o = o[0]
    o = o[0].permute(1, 2, 0).clamp(0, 1).numpy() * 255
    return o


def kcentroid(hp, k=3, line=False, prefilter=True):
    import cv2
    img = hp.astype(np.uint8)
    if prefilter:
        img = cv2.bilateralFilter(img, 7, 40, 5)
    img = img.astype(float)
    H, W = img.shape[0] // P, img.shape[1] // P
    b = img[:H * P, :W * P].reshape(H, P, W, P, 3).transpose(0, 2, 1, 3, 4).reshape(H * W, P * P, 3)
    lum = b @ np.array([.299, .587, .114])
    o = np.argsort(lum, 1)
    c = np.stack([np.take_along_axis(b, o[:, [int(q * (P * P - 1))]][..., None].repeat(3, -1), 1)[:, 0] for q in np.linspace(0, 1, k)], 1)
    for _ in range(8):
        d = ((b[:, :, None] - c[:, None]) ** 2).sum(-1); a = d.argmin(-1)
        for j in range(k):
            s = (a == j)[..., None]; n = s.sum(1)
            c[:, j] = np.where(n > 0, (b * s).sum(1) / np.maximum(n, 1), c[:, j])
    cnt = np.stack([(a == j).sum(1) for j in range(k)], 1)
    pick = cnt.argmax(1)
    if line:  # keep thin dark lines: darkest cluster wins if it is a real line (>=22% of cell, very dark)
        cl = c @ np.array([.299, .587, .114]); dk = cl.argmin(1)
        win = (cnt[np.arange(len(dk)), dk] >= 0.22 * P * P) & (cl[np.arange(len(dk)), dk] < 60)
        pick = np.where(win, dk, pick)
    return c[np.arange(len(pick)), pick].reshape(H, W, 3)


def finish(lo, h, w, pad, keys, rgb, alpha=None, use_mat=True):
    a = low_alpha(lo) if alpha is None else alpha
    # drop specks outside the main body
    from scipy import ndimage as nd
    lab, n = nd.label(a)
    if n > 1:
        sz = nd.sum(a, lab, range(1, n + 1)); a = np.isin(lab, 1 + np.where(sz >= max(3, sz.max() * 0.01))[0])
    g = Z.snap(lo, a, keys, rgb, use_mat)
    g = Z.outline_sil(g)
    return Z.place(g, h, pad)


def face_hull(x, m, h, w):
    """face (skin hull of the head) in sprite figure coords, from the illustration"""
    from scipy import ndimage as nd
    L = Z.materials(x, m); Hh = m.shape[0]
    sk = L == 'skin'; sk[int(Hh * 0.42):] = False
    hull = nd.binary_fill_holes(nd.binary_closing(sk, iterations=max(3, m.shape[1] // 60)))
    lab, n = nd.label(hull)
    if n: sz = nd.sum(hull, lab, range(1, n + 1)); hull = lab == 1 + sz.argmax()
    g = Z.resize(hull * 255., w, h, Image.BOX) > 140
    wd = g.sum(1); rmax = int(wd.argmax())
    for r in range(rmax, h):  # cut the neck: first row (below the widest) narrower than 62% of the face
        if wd[r] < 0.62 * wd[rmax]: g[r:] = False; break
    return g


def cleanup(g, x, m, h, ox, oy, keys, rgb):
    """E pass: (1) face region re-done by area-average + unconstrained palette snap (keeps iris/eye-white/mouth),
    (2) orphan removal outside the face, (3) isolated non-skin specks in skin -> skin shadow, (4) 1px outer-outline gaps"""
    w, _ = Z.figsize(m, h)
    fh = face_hull(x, m, h, w)
    lo = Z.resize(x, w, h, Image.BOX)
    fs = Z.snap(lo, np.ones((h, w), bool), keys, rgb, use_mat=False)
    G = np.full(g.shape, False); G[oy:oy + h, ox:ox + w] = fh
    sub = g[oy:oy + h, ox:ox + w]
    face_ok = fh.sum() >= (0.12 * h) ** 2  # back views (N) have no face -> skip feature pass
    GF = G.copy()
    if face_ok:
        # face features, data-driven per cell (upper face = eyes, lower = mouth)
        lum = x @ np.array([.299, .587, .114])
        L = Z.materials(x, m); Hh = m.shape[0]
        hullF = Z.resize(fh * 255., m.shape[1], Hh, Image.NEAREST) > 127
        dn = lambda b: Z.resize(b * 255., w, h, Image.BOX) / 255.
        dk = dn(lum < 55)
        wh = dn(m & (x.min(-1) > 195) & (x.max(-1) - x.min(-1) < 45))
        iris = dn(m & (L != 'skin') & (lum >= 55) & (lum < 165) & ~((x.min(-1) > 195)))
        rows = np.where(fh.any(1))[0]; fy0, fy1 = rows.min(), rows.max(); fhh = fy1 - fy0 + 1
        ylim = oy + fy0 + int(0.72 * fhh)
        upper = fh.copy(); upper[fy0 + int(0.72 * fhh):] = False
        sub[fh] = fs[fh]
        ki = [keys.index(c) for c in 'hgL']; plab = Z.rgb2lab(rgb)
        for r, c in zip(*np.where(upper)):
            if dk[r, c] >= 0.30: sub[r, c] = 'K'
            elif iris[r, c] >= 0.32 and r > fy0 + 0.25 * fhh:
                lab = Z.rgb2lab(lo[r, c][None])[0]; sub[r, c] = keys[ki[int(((plab[ki] - lab) ** 2).sum(1).argmin())]]
            elif wh[r, c] >= 0.45: sub[r, c] = 'W'
            elif sub[r, c] == 'W': sub[r, c] = 's'
        # lash = top dark row only: a K directly under a K (inside the face) becomes iris-dark h (pupil/iris), keeps eyes open
        for r, c in sorted(zip(*np.where(upper)), reverse=True):
            if sub[r, c] == 'K' and r > 0 and sub[r - 1, c] == 'K' and upper[r - 1, c]: sub[r, c] = 'h'
        # one catchlight per eye: in each iris blob (h/g/L/K cells below a lash), the cell with most white
        from scipy import ndimage as nd
        eye = upper & np.isin(sub, list('hgLK')); lab_, n_ = nd.label(eye)
        for i in range(1, n_ + 1):
            cells = np.argwhere((lab_ == i) & np.isin(sub, list('hgL')))
            if len(cells) >= 3:
                best = max(cells, key=lambda rc: wh[rc[0], rc[1]])
                if wh[best[0], best[1]] >= 0.12: sub[best[0], best[1]] = 'W'
        # mouth: the lower-face row with the strongest mouth line; its cells >= 12% -> m (never on the face border)
        mo = dn(m & (L != 'skin') & (lum < 150) & (lum >= 40) & hullF)
        inner = nd.binary_erosion(fh, iterations=1)
        cand = [(mo[r][inner[r]].sum(), r) for r in range(fy0 + int(0.70 * fhh), fy1) if inner[r].any()]
        if cand:
            sc, rbest = max(cand)
            if sc >= 0.3:
                for c in np.where(inner[rbest] & (mo[rbest] >= 0.12))[0]:
                    sub[rbest, c] = 'm'
        lowface = np.zeros(g.shape, bool); lowface[ylim:oy + h] = G[ylim:oy + h]
        g[lowface & (g == 'W')] = 's'
        GF = G.copy()
        G[ylim:] = False
    # W only where it is an eye highlight/sclera: needs a dark (K/h) pixel within 1px
    if not face_ok: G[:] = False; GF[:] = False
    for r, c in zip(*np.where(G & (g == 'W'))):
        if not np.isin(g[r - 1:r + 2, c - 1:c + 2], list('KhH')).any(): g[r, c] = 's'
    keep = g.copy()
    g = Z.clean_orphans(g)
    g[GF] = keep[GF]
    # skin specks: a non-skin pixel with >=6 skin 8-neighbours outside the face -> S
    H, W = g.shape; out = g.copy()
    for r in range(1, H - 1):
        for c in range(1, W - 1):
            if GF[r, c] or g[r, c] in 'sSk.': continue
            nb = g[r - 1:r + 2, c - 1:c + 2]
            if np.isin(nb, list('sSk')).sum() >= 6: out[r, c] = 'S'
    g = out; out = g.copy()
    for r in range(1, H - 1):
        for c in range(1, W - 1):
            if g[r, c] in 'K.W': continue
            if ((g[r - 1, c] == 'K' and g[r + 1, c] == 'K') or (g[r, c - 1] == 'K' and g[r, c + 1] == 'K')) and \
               (g[r - 1:r + 2, c - 1:c + 2] == '.').any(): out[r, c] = 'K'
    return out


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('method'); ap.add_argument('view'); ap.add_argument('h', type=int)
    ap.add_argument('--src'); ap.add_argument('--out', default=Z.ROOT + 'v2/pixelize/out'); ap.add_argument('--pal')
    ap.add_argument('--tag', default=''); ap.add_argument('--thick', type=int, default=2); ap.add_argument('--gem'); ap.add_argument('--nomat', action='store_true')
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    keys, rgb, _ = Z.load_pal(a.pal)
    Z_RGB = rgb
    x, m = Z.load(a.view, a.src)
    h = a.h; pad = 2
    M = a.method
    base = M[1:] if M.startswith('E') else M
    if base == 'A':
        g, (ox, oy) = meth_A(x, m, h, keys, rgb, a)
    elif base == 'D':
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from gemsnap import gemlow
        lo, al, w = gemlow(a.gem, h)
        g, (ox, oy) = finish(lo, h, w, 0, keys, rgb, al)
    else:
        hp, mp, w = hires(x, m, h, pad)
        if base == 'B': lo = pixeloe(hp, a.thick)
        elif base == 'C0': lo = kcentroid(hp, 3, line=False, prefilter=False)
        elif base == 'C': lo = kcentroid(hp, 3, line=True, prefilter=True)
        elif base == 'F':  # plain area (box) average
            H2, W2 = hp.shape[0] // P, hp.shape[1] // P
            lo = hp[:H2 * P, :W2 * P].reshape(H2, P, W2, P, 3).mean((1, 3))
            a2 = mp[:H2 * P, :W2 * P].reshape(H2, P, W2, P).mean((1, 3)) > 0.5
            lo[~a2] = 255
        else: raise SystemExit('unknown method')
        g, (ox, oy) = finish(lo, h, w, pad, keys, rgb, use_mat=not a.nomat)
    if M.startswith('E'):
        g = cleanup(g, x, m, h, ox, oy, keys, rgb)
    w, _ = Z.figsize(m, h)
    name = f'{M}{a.tag}_{a.view}_{h}'
    Z.save(g, os.path.join(a.out, name), keys, rgb, {'method': M, 'view': a.view, 'h': h, 'w': w, 'ox': int(ox), 'oy': int(oy),
                                                      'src': Z.srcpath(a.view, a.src), 'pal': a.pal or Z.PALFILE})
    print(name, 'ok', g.shape)
