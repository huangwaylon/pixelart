"""fixlib: pixel-art-fixer -> figure crop -> (optional rescale to the 96 px figure) -> E2 palette lock (pzlib).
Run with the fixer venv (has numpy/scipy/cv2/PIL):
  /Users/waylonhuang/Documents/other/pixelart/.models/pixel-art-fixer/venv/bin/python -I fixlib.py IN.png OUTSTEM [--view SE] [--h 96] [--src illus.png]
Writes OUTSTEM_fix.png (fixer native 1 cell = 1 px), OUTSTEM_nat.{txt,png,json} (palette-locked at native size),
OUTSTEM_r96.{txt,png,json} (rescaled to h px figure, palette-locked, 128 cell), OUTSTEM_info.json."""
import sys, os, json, argparse, numpy as np
from PIL import Image
from scipy import ndimage as nd

REPO = '/Users/waylonhuang/Documents/other/pixelart/'
SW = REPO + 'swordswoman/'
sys.path.insert(0, REPO + 'pipeline/tools')
sys.path.insert(0, SW + 'v2/pixelize/tools')
import pixelfix  # noqa: E402
import pzlib as Z  # noqa: E402
import pz  # noqa: E402

PAL = SW + 'v2/pixelize/palette.json'


def bgmask(rgb):
    """foreground mask. Background = pixels within 22 (RGB dist) of the border colour (median of the 2px frame) that are
    connected to the border; enclosed regions count as background only if they match the bg colour closely (mean dist <10),
    else they are figure (fix: the grey-lavender obi sat inside a mid-grey bg and was dropped as a 'hole').
    Small specks dropped; for sprite sheets the largest figure is kept."""
    x = rgb.astype(float)
    fr = np.concatenate([x[:2].reshape(-1, 3), x[-2:].reshape(-1, 3), x[:, :2].reshape(-1, 3), x[:, -2:].reshape(-1, 3)])
    bg = np.median(fr, 0)
    d = np.sqrt(((x - bg) ** 2).sum(-1))
    near = d <= 22
    lab, n = nd.label(near)
    border = set(np.unique(np.r_[lab[0], lab[-1], lab[:, 0], lab[:, -1]])) - {0}
    m = np.ones(d.shape, bool)
    for i in range(1, n + 1):
        sel = lab == i
        if i in border or d[sel].mean() < 10: m[sel] = False
    lab, n = nd.label(m)
    if n > 1:
        sz = nd.sum(m, lab, range(1, n + 1)); m = np.isin(lab, 1 + np.where(sz >= sz.max() * 0.03)[0])
    grp, ng = nd.label(nd.binary_dilation(m, iterations=max(2, int(0.03 * max(m.shape)))))
    if ng > 1:
        sz = nd.sum(m, grp, range(1, ng + 1)); m = m & (grp == 1 + int(np.argmax(sz)))
    return m, bg


def crop(rgb, m):
    ys, xs = np.where(m)
    y0, y1, x0, x1 = ys.min(), ys.max(), xs.min(), xs.max()
    c = rgb[y0:y1 + 1, x0:x1 + 1].astype(float).copy(); cm = m[y0:y1 + 1, x0:x1 + 1]
    c[~cm] = 255
    return c, cm


def to_h(nat, na, h):
    """rescale a native-grid figure to an h px tall figure. near (<12%) -> nearest; else k-centroid of the nearest x8 upscale"""
    hn, wn = na.shape
    w = max(1, round(wn * h / hn))
    if hn == h:
        return nat, na, w, 'identity'
    if abs(hn - h) / h < 0.12:
        lo = Z.resize(nat, w, h, Image.NEAREST); al = Z.resize(na * 255., w, h, Image.NEAREST) > 127
        return lo, al, w, 'nearest'
    P = pz.P
    hi = Z.resize(nat, w * P, h * P, Image.NEAREST); hm = Z.resize(na * 255., w * P, h * P, Image.NEAREST) > 127
    hi[~hm] = 255
    lo = pz.kcentroid(hi, 3, line=False, prefilter=False)
    al = hm.reshape(h, P, w, P).mean((1, 3)) > 0.5
    return lo, al, w, 'kcentroid'


def lock(lo, al, h, w, keys, rgb):
    g, (ox, oy) = pz.finish(lo, h, w, 0, keys, rgb, al)
    return Z.clean_orphans(g), ox, oy


_ML = {}


def master_L():
    """median Lab-L per material of the m96 SE master (palette colours via its char grid)"""
    if _ML: return _ML
    keys, rgb, _ = Z.load_pal(PAL)
    g = np.array([list(l.rstrip('\n')) for l in open(SW + 'v2/m96/masters/EC0_SE_96.txt') if l.strip()])
    lab = Z.rgb2lab(rgb)[:, 0]
    for mt, al in Z.ALLOW.items():
        if not al or mt == 'K': continue
        v = [lab[keys.index(c)] for c in g.ravel() if c in al and c != 'K' and c in keys]
        if v: _ML[mt] = float(np.median(v))
    return _ML


def lock2(lo, al, h, w, keys, rgb, pad=0):
    """palette lock v2 (this experiment): pzlib material segmentation + (1) low-saturation lavender/grey '?' cells -> obi,
    (2) per-material lightness match: shift each material's Lab L so its median equals the master's (clamped +-18),
    then nearest palette colour inside the material's allowed set; outline + orphan clean as E2."""
    from scipy import ndimage as nd
    a = al.copy(); lab_, n = nd.label(a)
    if n > 1:
        sz = nd.sum(a, lab_, range(1, n + 1)); a = np.isin(lab_, 1 + np.where(sz >= max(3, sz.max() * 0.01))[0])
    L = Z.seg2(lo, a)
    mx, mn = lo.max(-1), lo.min(-1); sat = (mx - mn) / np.maximum(mx, 1)
    L[(L == '?') & a & (sat < 0.3) & (lo[..., 2] >= 0.85 * lo[..., 0]) & (mx > 90) & (mx < 245)] = 'obi'
    lab = Z.rgb2lab(lo); plab = Z.rgb2lab(rgb); ML = master_L()
    shift = {}
    for mt, v in ML.items():
        sel = (L == mt) & a
        if sel.sum() >= 4:
            d = float(np.clip(v - np.median(lab[sel][:, 0]), -18, 18)); lab[sel, 0] += d; shift[mt] = round(d, 1)
    d = ((lab[:, :, None, :] - plab[None, None]) ** 2).sum(-1); idx = d.argmin(-1)
    for mt, alw in Z.ALLOW.items():
        if alw is None: continue
        cols = [keys.index(c) for c in alw if c in keys]
        sel = (L == mt) & a
        if sel.any() and cols: idx[sel] = np.array(cols)[d[sel][:, cols].argmin(1)]
    g = np.array(keys, dtype='<U1')[idx]; g[~a] = '.'
    g = Z.outline_sil(g)
    g, (ox, oy) = Z.place(g, h, pad)
    return Z.clean_orphans(g), ox, oy, shift


def roundtrip(rgba, fixed):
    """mean abs RGB error over the foreground: fixer output nearest-upscaled back to the input size vs the input"""
    h, w = rgba.shape[:2]
    up = np.array(Image.fromarray(fixed).resize((w, h), Image.NEAREST)).astype(float)
    m, _ = bgmask(rgba[..., :3])
    return float(np.abs(up[..., :3] - rgba[..., :3].astype(float))[m].mean())


def fix_sq(im, step=None, square=True):
    """pixelfix detect; if the detected grid is anisotropic (>0.2%) also try square grids (step_y,step_y)/(step_x,step_x)
    and keep the lowest round-trip error. Exp finding: arbitration often mis-detects step_x on narrow figures."""
    fixed, info = pixelfix.fix(im, step)
    info['err_det'] = roundtrip(im, fixed); info['grid_pick'] = 'detected'
    sx, sy = info['step_x'], info['step_y']; info['det_sx'], info['det_sy'] = sx, sy
    if square and not step and abs(sx - sy) / sy > 0.002:
        for tag, s in (('square_y', sy), ('square_x', sx)):
            f2, i2 = pixelfix.fix(im, (s, s))
            e = roundtrip(im, f2)
            info['err_' + tag] = e
            if e < info.get('err_best', info['err_det']) - 0.3:
                fixed, info['err_best'], info['grid_pick'] = f2, e, tag
                info['step_x'] = info['step_y'] = s; info['cols'], info['rows'] = i2['cols'], i2['rows']
    info.setdefault('err_best', info['err_det'])
    return fixed, info


def run(inp, stem, view='SE', h=96, src=None, step=None, square=True):
    keys, rgb, _ = Z.load_pal(PAL)
    im = np.array(Image.open(inp).convert('RGBA'))
    fixed, info = fix_sq(im, step, square)
    Image.fromarray(fixed).save(stem + '_fix.png')
    m, bg = bgmask(fixed[..., :3])
    nat, na = crop(fixed[..., :3], m)
    hn, wn = na.shape
    src = src or Z.srcpath(view)
    meta = {'view': view, 'src': src, 'pal': PAL}
    # native size, palette locked (no rescale)
    gN, ox, oy = lock(nat, na, hn, wn, keys, rgb)
    Z.save(gN, stem + '_nat', keys, rgb, {**meta, 'method': 'GFXnat', 'h': hn, 'w': wn, 'ox': int(ox), 'oy': int(oy)})
    lo, al, w, how = to_h(nat, na, h)
    g, ox, oy = lock(lo, al, h, w, keys, rgb)
    Z.save(g, stem + f'_r{h}', keys, rgb, {**meta, 'method': 'GFX', 'h': h, 'w': w, 'ox': int(ox), 'oy': int(oy)})
    g2, ox2, oy2, shift = lock2(lo, al, h, w, keys, rgb)
    Z.save(g2, stem + f'_r{h}L2', keys, rgb, {**meta, 'method': 'GFX_L2', 'h': h, 'w': w, 'ox': int(ox2), 'oy': int(oy2), 'shift': shift})
    out = {'in': inp, 'in_size': [im.shape[1], im.shape[0]], 'step_x': info.get('step_x'), 'step_y': info.get('step_y'),
           'cols': info.get('cols'), 'rows': info.get('rows'), 'consensus': info.get('consensus'),
           'grid_pick': info['grid_pick'], 'det_step': [round(info['det_sx'], 3), round(info['det_sy'], 3)], 'err_det': round(info['err_det'], 2), 'err_best': round(info['err_best'], 2),
           'bg': [int(v) for v in bg], 'fig_native_h': int(hn), 'fig_native_w': int(wn),
           'fig_in_px_h': round(hn * info['step_y'], 1), 'rescale': how, 'scale_to_96': round(h / hn, 3),
           'n_colors_fix': int(len(np.unique(fixed[..., :3][m].reshape(-1, 3), axis=0)))}
    json.dump(out, open(stem + '_info.json', 'w'), indent=1)
    print(json.dumps(out))
    return out


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('inp'); ap.add_argument('stem')
    ap.add_argument('--view', default='SE'); ap.add_argument('--h', type=int, default=96); ap.add_argument('--src')
    ap.add_argument('--step', nargs=2, type=float); ap.add_argument('--nosquare', action='store_true')
    a = ap.parse_args()
    os.makedirs(os.path.dirname(os.path.abspath(a.stem)), exist_ok=True)
    run(a.inp, a.stem, a.view, a.h, a.src, a.step, not a.nosquare)
