"""metrics.py STEM [STEM ...] [--json out.json]: fidelity metrics of sprite STEM(.txt/.json) vs its illustration.
ssim/ssim_b: SSIM (Lab L) vs illustration area-downsampled to sprite size (ssim_b: both gaussian-blurred 1px, shift-tolerant)
dE: mean CIEDE2000 over figure; iou_*: per-material IoU (cell majority); sil: silhouette IoU; bloat: sprite/illus area
line_f: outline F1@1px (illustration dark-line cells vs sprite K); kcomp: K components; orph: orphan pixels
face_*: face measurements error (eye spacing/size/aspect/height, mouth, contour IoU); depth_*: E-view body width ratios"""
import sys, os, json, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pzlib as Z
from PIL import Image
from scipy import ndimage as nd
from skimage.metrics import structural_similarity as ssim
from skimage.color import deltaE_ciede2000

C2M = {**{c: 'K' for c in 'K'}, **{c: 'hair' for c in 'hHgL'}, **{c: 'skin' for c in 'sSmk'}, **{c: 'red' for c in 'ReE'},
       **{c: 'obi' for c in 'oOQ'}, 'D': 'socks', 'd': 'socks', 'W': 'W', '.': ''}
_cache = {}


def ref(view, src, h, w):
    key = (src, h, w)
    if key in _cache: return _cache[key]
    x, m = Z.load(view, src)
    L = Z.materials(x, m)
    Hh, Ww = m.shape
    ry = (np.arange(Hh) * h // Hh)[:, None] * np.ones((1, Ww), int)
    rx = (np.arange(Ww) * w // Ww)[None, :] * np.ones((Hh, 1), int)
    mats = ['K', 'hair', 'boot', 'socks', 'skin', 'red', 'obi', 'W', '?']
    cnt = np.zeros((len(mats), h, w))
    for i, mt in enumerate(mats):
        s = L == mt; np.add.at(cnt[i], (ry[s], rx[s]), 1)
    tot = np.zeros((h, w)); np.add.at(tot, (ry.ravel(), rx.ravel()), 1)
    alpha = cnt.sum(0) > 0.5 * tot
    nk = cnt.copy(); nk[0] *= 0.35  # outline lines are thin: majority after down-weighting K
    mat = np.array(mats)[nk.argmax(0)]; mat[~alpha] = ''
    line = cnt[0] >= 0.18 * tot
    lo = Z.resize(x, w, h, Image.BOX)
    r = dict(x=x, m=m, L=L, lo=lo, alpha=alpha, mat=mat, line=line)
    _cache[key] = r
    return r


def face_measure(skin, feat, dark):
    """skin/feat masks of head region -> dict of normalised face measurements"""
    hull = nd.binary_fill_holes(nd.binary_closing(skin, iterations=max(1, int(skin.shape[1] / 40))))
    lab, n = nd.label(hull)
    if n == 0: return None
    sz = nd.sum(hull, lab, range(1, n + 1)); hull = lab == (1 + sz.argmax())
    ys, xs = np.where(hull); fy0, fy1, fx0, fx1 = ys.min(), ys.max(), xs.min(), xs.max()
    fw, fh = fx1 - fx0 + 1, fy1 - fy0 + 1
    inner = nd.binary_erosion(hull, iterations=1) if fw > 20 else hull
    eyes = inner & dark & (np.arange(hull.shape[0])[:, None] < fy0 + 0.75 * fh)
    lab, n = nd.label(eyes, np.ones((3, 3)))
    out = {'fw_fh': fw / fh}
    if n:
        sz = nd.sum(eyes, lab, range(1, n + 1)); top = np.argsort(sz)[::-1][:2]
        top = [t for t in top if sz[t] >= sz.max() * 0.15]
        E = []
        for t in top:
            yy, xx = np.where(lab == t + 1)
            E.append(((xx.mean() - fx0) / fw, (yy.mean() - fy0) / fh, (xx.max() - xx.min() + 1) / fw, (yy.max() - yy.min() + 1) / fh))
        E.sort()
        out['n_eyes'] = len(E)
        out['eye_y'] = float(np.mean([e[1] for e in E])); out['eye_w'] = float(np.mean([e[2] for e in E])); out['eye_h'] = float(np.mean([e[3] for e in E]))
        out['eye_dx'] = float(E[-1][0] - E[0][0]) if len(E) > 1 else 0.0
    else:
        out['n_eyes'] = 0
    mouth = inner & feat & ~dark | (inner & dark & (np.arange(hull.shape[0])[:, None] >= fy0 + 0.75 * fh))
    mouth &= (np.arange(hull.shape[0])[:, None] >= fy0 + 0.6 * fh)
    out['mouth'] = bool(mouth.sum() > 0)
    if mouth.any(): out['mouth_y'] = float((np.where(mouth)[0].mean() - fy0) / fh)
    out['_hull'] = hull
    return out


def face_err(fi, fs):
    if fi is None or fs is None: return 1.0, {}
    terms = {}
    for k, wgt in [('eye_y', 1), ('eye_w', 1), ('eye_h', 1), ('eye_dx', 1), ('mouth_y', 1), ('fw_fh', 0.5)]:
        if k in fi:
            terms[k] = abs(fi[k] - fs.get(k, 0 if k != 'mouth_y' else 1)) * wgt
    terms['n_eyes'] = 0.15 * abs(fi['n_eyes'] - fs['n_eyes'])
    terms['mouth'] = 0 if fi['mouth'] == fs['mouth'] else 0.15
    return float(sum(terms.values()) / len(terms)), terms


def depth_rows(mat, h):
    """rows (fraction of h) chest / waist / hip / thigh from obi + hem landmarks of a material grid"""
    obi = np.where((mat == 'obi').any(1))[0]; red = np.where((mat == 'red').sum(1) >= 2)[0]
    if len(obi) == 0 or len(red) == 0: return None
    o0, o1 = obi.min(), obi.max(); oh = max(1, o1 - o0 + 1); hem = red.max()
    return {'chest': o0 - oh, 'waist': (o0 + o1) // 2, 'hip': o1 + oh, 'thigh': hem + max(1, round(0.06 * h))}


def rowwidth(a, matrow, r):
    s = a[r] & ~np.isin(matrow[r], ['hair', 'boot', 'W'])
    xs = np.where(s)[0]
    return 0 if len(xs) == 0 else xs.max() - xs.min() + 1


def metrics(stem):
    g, meta = Z.read(stem)
    keys, rgb, _ = Z.load_pal(meta['pal'])
    h, w, ox, oy = meta['h'], meta['w'], meta['ox'], meta['oy']
    R = ref(meta['view'], meta['src'], h, w)
    pad = 2
    N = g.shape[0]
    gp = np.full((h + 2 * pad, w + 2 * pad), '.', dtype='<U1')
    y0, x0 = oy - pad, ox - pad
    for r in range(h + 2 * pad):
        for c in range(w + 2 * pad):
            if 0 <= y0 + r < N and 0 <= x0 + c < g.shape[1]: gp[r, c] = g[y0 + r, x0 + c]
    P = np.full(gp.shape + (3,), 255.)
    for i, k in enumerate(keys): P[gp == k] = rgb[i]
    sa = gp != '.'
    smat = np.vectorize(lambda c: C2M.get(c, '?'))(gp)
    rr = np.arange(gp.shape[0])[:, None] - pad
    smat[(smat == 'hair') & (rr > 0.86 * h)] = 'boot'
    smat[(smat == 'hair') & (rr > Z.SOCKS[0] * h) & (rr <= Z.SOCKS[1] * h)] = 'socks'
    Rlo = np.full(gp.shape + (3,), 255.); Rlo[pad:pad + h, pad:pad + w] = R['lo']
    ra = np.zeros(gp.shape, bool); ra[pad:pad + h, pad:pad + w] = R['alpha']
    rmat = np.full(gp.shape, '', dtype='<U6'); rmat[pad:pad + h, pad:pad + w] = R['mat']
    rline = np.zeros(gp.shape, bool); rline[pad:pad + h, pad:pad + w] = R['line']
    la, lb = Z.rgb2lab(P), Z.rgb2lab(Rlo)
    out = {'name': os.path.basename(stem)}
    out['ssim'] = float(ssim(la[..., 0], lb[..., 0], data_range=100, win_size=7))
    out['ssim_b'] = float(ssim(nd.gaussian_filter(la[..., 0], 1), nd.gaussian_filter(lb[..., 0], 1), data_range=100, win_size=7))
    u = sa | ra
    out['dE'] = float(deltaE_ciede2000(la[u], lb[u]).mean())
    out['sil'] = float((sa & ra).sum() / u.sum()); out['bloat'] = float(sa.sum() / ra.sum())
    for mt in ['hair', 'red', 'skin', 'obi', 'boot', 'socks']:
        a, b = smat == mt, rmat == mt
        out['iou_' + mt] = float((a & b).sum() / max(1, (a | b).sum()))
    sk = gp == 'K'; d1 = nd.binary_dilation
    rec = (rline & d1(sk, np.ones((3, 3)))).sum() / max(1, rline.sum()); pre = (sk & d1(rline, np.ones((3, 3)))).sum() / max(1, sk.sum())
    out['line_f'] = float(2 * rec * pre / max(1e-6, rec + pre))
    out['kcomp'] = int(nd.label(sk, np.ones((3, 3)))[1])
    orph = 0
    for r in range(1, gp.shape[0] - 1):
        for c in range(1, gp.shape[1] - 1):
            v = gp[r, c]
            if v != '.' and (gp[r - 1:r + 2, c - 1:c + 2] == v).sum() == 1: orph += 1
    out['orph'] = orph
    try:
        # face (sprite grid): illustration face hull + feature cells (eyes = upper 70% of hull, mouth = lower 30%)
        x, m, L = R['x'], R['m'], R['L']; Hh, Ww = m.shape
        sk = L == 'skin'; sk[int(Hh * 0.42):] = False
        hull = nd.binary_fill_holes(nd.binary_closing(sk, iterations=max(3, Ww // 60)))
        lab_, n_ = nd.label(hull)
        if n_: sz = nd.sum(hull, lab_, range(1, n_ + 1)); hull = lab_ == 1 + sz.argmax()
        ys_ = np.where(hull.any(1))[0]; hy0, hy1 = ys_.min(), ys_.max(); split = hy0 + 0.70 * (hy1 - hy0)
        feat = hull & m & (L != 'skin')
        yy = np.arange(Hh)[:, None]
        dn = lambda b: Z.resize(b * 255., w, h, Image.BOX) / 255.
        hullg = dn(hull) > 0.5; eyeg = dn(feat & (yy < split)) >= 0.25; mouthg = dn(feat & (yy >= split)) >= 0.10
        eyeg &= hullg; mouthg &= hullg
        sub = gp[pad:pad + h, pad:pad + w]; ns = ~np.isin(sub, list('sSk.')) & hullg
        gy = np.arange(h)[:, None] * np.ones((1, w)); splitg = split * h / Hh
        se = ns & (gy < splitg); smo = ns & (gy >= splitg)
        dl = lambda b: nd.binary_dilation(b, np.ones((3, 3)))
        rec = (eyeg & dl(se)).sum() / max(1, eyeg.sum()); pre = (se & dl(eyeg)).sum() / max(1, se.sum())
        out['eye_f1'] = float(2 * rec * pre / max(1e-6, rec + pre))
        out['mouth'] = int(bool((dl(mouthg) & smo).any())) if mouthg.any() else -1
        hx = np.where(hullg.any(0))[0]; mid = (hx.min() + hx.max()) / 2; fw = hx.max() - hx.min() + 1
        def eyes(b):
            r = []
            for side in (np.arange(w) < mid, np.arange(w) >= mid):
                yy2, xx2 = np.where(b & side[None, :])
                if len(xx2) == 0: return None
                r.append((xx2.mean(), (yy2.max() - yy2.min() + 1) / (xx2.max() - xx2.min() + 1)))
            return r
        ei, es = eyes(eyeg), eyes(se)
        if ei and es:
            out['eye_dx_err'] = float(abs((ei[1][0] - ei[0][0]) - (es[1][0] - es[0][0])) / fw)
            out['eye_ar_err'] = float(np.mean([abs(np.log(max(.1, es[i][1]) / max(.1, ei[i][1]))) for i in (0, 1)]))
        else:
            out['eye_dx_err'] = 1.0; out['eye_ar_err'] = 1.0
        fy, fx = np.where(hullg); bb = (slice(fy.min(), fy.max() + 1), slice(fx.min(), fx.max() + 1))
        fl, fr = la[pad:pad + h, pad:pad + w, 0][bb], lb[pad:pad + h, pad:pad + w, 0][bb]
        ws = min(7, min(fl.shape)); ws -= (ws % 2 == 0)
        out['face_ssim'] = float(ssim(fl, fr, data_range=100, win_size=ws)) if ws >= 3 else float('nan')
        if ws < 3 or hullg.sum() < (0.12 * h) ** 2: out['face_score'] = float('nan')
        else: out['face_score'] = float(0.3 * out['face_ssim'] + 0.3 * out['eye_f1'] + 0.15 * max(0, out['mouth']) +
                                  0.125 * (1 - min(1, 4 * out['eye_dx_err'])) + 0.125 * (1 - min(1, out['eye_ar_err'])))
    except ValueError:  # no usable face (back views)
        out['face_score'] = float('nan')
    # body depth (side views): torso/leg width (red/obi/skin extent + outline) at chest/waist/hip/thigh rows of the illustration
    oc = (L == 'obi').sum(1); orow = np.where(oc > 0.3 * oc.max())[0]
    rc = (L == 'red').sum(1); rrow = np.where(rc > 0.05 * rc.max())[0]
    if len(orow) and len(rrow):
        o0, o1 = orow.min(), orow.max(); oh = o1 - o0 + 1; hem = rrow.max()
        rows = {'chest': o0 - oh, 'waist': (o0 + o1) // 2, 'hip': o1 + oh // 2, 'thigh': hem + int(0.05 * Hh)}
        body = np.isin(L, ['red', 'obi', 'skin', 'socks'])
        sb = np.isin(sub, list('ReEoOQsSmkDd'))
        for k, r in rows.items():
            if not (0 <= r < body.shape[0]) or not (0 <= int(r * h / Hh) < sb.shape[0]): continue  # m96 guard (warped sources)
            xs_ = np.where(body[r])[0]; rs = int(r * h / Hh); xg = np.where(sb[rs])[0]
            if len(xs_) and len(xg):
                wi = (xs_.max() - xs_.min() + 1) * w / Ww + 2; ws = xg.max() - xg.min() + 1 + 2
                out['depth_' + k] = round(ws / wi, 3); out['depthpx_' + k] = [int(ws), round(float(wi), 1)]
    return out


if __name__ == '__main__':
    args = sys.argv[1:]; js = None
    if '--json' in args: i = args.index('--json'); js = args[i + 1]; args = args[:i] + args[i + 2:]
    res = [metrics(s[:-4] if s.endswith(('.txt', '.png')) else s) for s in args]
    keys = ['ssim', 'ssim_b', 'dE', 'sil', 'bloat', 'iou_hair', 'iou_red', 'iou_skin', 'iou_obi', 'iou_boot', 'iou_socks', 'line_f', 'kcomp', 'orph', 'face_score', 'face_ssim', 'eye_f1', 'mouth', 'eye_dx_err', 'eye_ar_err']
    print('name'.ljust(16) + ''.join(k[:8].rjust(9) for k in keys))
    for r in res:
        print(r['name'][:16].ljust(16) + ''.join((f'{r[k]:9.3f}' if isinstance(r.get(k), float) else str(r.get(k, '-')).rjust(9)) for k in keys))
    if js: json.dump(res, open(js, 'w'), indent=0)
