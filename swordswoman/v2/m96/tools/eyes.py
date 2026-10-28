"""eyes.py: M96 eye/mouth/blush spec engine (eye_spec.json). Library + CLI.
  eyes.py detect STEM VIEW            -> print detected eyes/mouth (from the illustration + master)
  eyes.py apply STEM VIEW [EXPR] OUT  -> stamp spec eyes/mouth/blush (EXPR default neutral) into OUT stem
  eyes.py tmpl VIEWKIND EXPR          -> print a template (front_left, front_right, far, profile, profile_w)
"""
import sys, os, json, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import m96 as M, pzlib as Z
from scipy import ndimage as nd
from PIL import Image
SPEC = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'eye_spec.json')))
IRIS = set('hgL@')
SKIN = set('sSmk')


from eyetmpl import expr_key, canonical, mirror, kind_tmpl  # noqa: E402


def illus_lo(g, meta):
    x, m = Z.load(meta['view'], meta['src']); lo = Z.resize(x, meta['w'], meta['h'], Image.BOX)
    full = np.full((g.shape[0], g.shape[1], 3), 255.0); full[meta['oy']:meta['oy'] + meta['h'], meta['ox']:meta['ox'] + meta['w']] = lo
    return full


def face_mask(g, y0, y1):
    sk = np.isin(g, list(SKIN)); sk[:y0] = False; sk[y1:] = False
    return nd.binary_fill_holes(sk)


def detect(g, meta, view):
    """eyes: list of dict(kind, x0, y0) (template top-left; lash row = y0+1); mouth: (cx, row); crown row; chin row"""
    oy, h = meta['oy'], meta['h']
    op = g != '.'; crown = int(np.where(op.any(1))[0][0])
    head1 = oy + int(0.42 * h)
    sk = np.isin(g, list(SKIN)); rows = [y for y in range(oy, head1) if sk[y].sum() >= 3]
    out = dict(view=view, crown=crown, eyes=[], mouth=None)
    if view == 'N' or not rows: return out
    fy0, fy1 = rows[0], rows[-1]
    out['face_rows'] = [fy0, fy1]
    span = np.zeros_like(sk)
    for y in range(fy0, fy1 + 1):
        win = sk[max(fy0, y - 3):y + 4].any(0); xs = np.where(win)[0]
        if len(xs): span[y, xs.min():xs.max() + 2] = True
    # 3x sub-grid of the illustration: eye = dark cluster touching white (sclera/glint); hair strands have no white
    lo = illus_lo(g, meta); L = Z.rgb2lab(lo)[..., 0]
    S3 = 3; x, m = Z.load(meta['view'], meta['src']); lo3 = Z.resize(x, meta['w'] * S3, meta['h'] * S3, Image.BOX)
    lab3 = Z.rgb2lab(lo3); L3 = lab3[..., 0]; C3 = np.hypot(lab3[..., 1], lab3[..., 2])
    sp3 = np.zeros(L3.shape, bool)
    sub = span[oy:oy + h, meta['ox']:meta['ox'] + meta['w']]
    sp3[:] = np.kron(sub, np.ones((S3, S3), bool))
    lim = fy0 + 0.65 * (fy1 - fy0)
    sp3[:(fy0 + 1 - oy) * S3] = False
    dark = (L3 < 40) & sp3
    white = (L3 > 84) & (C3 < 16) & sp3
    skin3 = (L3 > 58) & (L3 < 86) & (lab3[..., 1] > 10) & (lab3[..., 2] > 8)
    tr = np.kron(~nd.binary_fill_holes(op)[oy:oy + h, meta['ox']:meta['ox'] + meta['w']], np.ones((S3, S3), bool))
    wl, n = nd.label(white, np.ones((3, 3)))
    seeds = []
    for i in range(1, n + 1):
        cm = wl == i
        if cm.sum() > 60 or (nd.binary_dilation(cm, np.ones((3, 3)), 2) & tr).any(): continue
        if not (nd.binary_dilation(cm, np.ones((3, 3)), 2) & dark).any(): continue
        if (nd.binary_dilation(cm, np.ones((3, 3)), 5) & skin3).sum() < 6: continue
        seeds.append(cm)
    comps = []
    used = np.zeros_like(white)
    for cm in seeds:
        if (cm & used).any(): continue
        reg = nd.binary_dilation(cm, np.ones((3, 3)), 6)          # eye neighbourhood (~2 px)
        for c2 in seeds:
            if (c2 & reg).any(): cm = cm | c2
        used |= cm
        reg = nd.binary_dilation(cm, np.ones((3, 3)), 6)
        pts = (reg & dark) | cm
        ys, xs = np.where(pts); ys = ys / S3 + oy; xs = xs / S3 + meta['ox']
        if ys.min() > lim: continue
        comps.append(dict(n=int(len(ys)), y0=int(np.floor(np.percentile(ys, 5))), y1=int(np.floor(ys.max())), x0=int(np.floor(xs.min())), x1=int(np.floor(xs.max())), cx=float(xs.mean())))
    # eyes = upper-face comps; keep the two largest in the band of the largest
    comps.sort(key=lambda c: -c['n'])
    if view == 'NE':
        # cheek sliver: rightmost skin px per face row -> lash tip just outside it at the eye row
        out['ne_cheek'] = [[int(np.where(sk[y])[0].max()), y] for y in range(fy0, fy1 + 1) if sk[y].any()]
        return out
    if not comps: return out
    comps = [c for c in comps if c['n'] >= 20]
    if not comps: return out
    top = min(comps, key=lambda c: c['y0']); eyes = sorted([c for c in comps if abs(c['y0'] - top['y0']) <= 2], key=lambda c: -c['n'])[:2 if view in ('S', 'SE') else 1]
    eyes.sort(key=lambda c: c['cx'])
    lash = min(c['y0'] for c in eyes)
    for j, c in enumerate(eyes):
        cx = int(round((c['x0'] + c['x1']) / 2))
        if view == 'S': kind = 'front_left' if j == 0 else 'front_right'
        elif view == 'SE': kind = 'front_left' if j == 0 else 'far'
        else: kind = 'front_left'; x0_shift = -1   # E: same main-eye construction as S/SE (qc: identical main eye box)
        w = len(kind_tmpl(kind, 'neutral')[0])
        if kind == 'front_left': x0 = cx - 2 - 1 + (-1 if view == 'E' else 0)   # iris c1-c4 centred on cx (c2/c3 ~ centre)
        elif kind == 'front_right': x0 = cx - 2
        elif kind == 'far': x0 = cx - 1
        else: x0 = cx - 2
        # refine on the auto master: template ink (K/iris) over master non-skin, template skin over master skin
        t = kind_tmpl(kind, 'neutral'); best = None
        for dy in (-1, 0, 1):
            for dx in (-2, -1, 0, 1, 2):
                sc = 0
                for j, r in enumerate(t[1:], 1):
                    for i, ch in enumerate(r):
                        yy, xx = int(lash - 1 + dy + j), int(x0 + dx + i); b = g[yy, xx]
                        if ch == '_': continue
                        ink = ch not in '.S'; bink = b in 'KhgLWdD.'
                        if b == 'H': sc -= 1
                        sc += 1 if ink == bink else 0
                sc -= 0.3 * (abs(dx) + abs(dy))
                if best is None or sc > best[0]: best = (sc, dx, dy)
        x0 += best[1]; ly = lash + best[2]
        out['eyes'].append(dict(kind=kind, x0=int(x0), y0=int(ly - 1), w=w, src=c))
    # lash row = qc crown + EYE_DY for every face view (spec: consistent eye height); both eyes share it
    try:
        sys.path.insert(0, M.ROOT + 'v2/qc'); sys.path.insert(0, M.ROOT + 'v2/anim_cut/tools')
        import qc_gate as QC, colorcheck as CC
        P = QC.parts([''.join(r) for r in g], CC.load(M.PAL)); out['qc_crown'] = P['crown']
        ly = P['crown'] + SPEC.get('eye_dy', 20)
        if all(abs(ly - (e['y0'] + 1)) <= 3 for e in out['eyes']):
            for e in out['eyes']: e['y0'] = ly - 1
    except Exception as ex:
        out['crown_err'] = str(ex)
    if len(out['eyes']) == 2:
        out['eyes'][1]['y0'] = out['eyes'][0]['y0']
    # mouth: reddish darker-than-skin sub-pixels inside the skin, below the eyes (3x grid)
    ey = lash + 4
    core = nd.binary_erosion(skin3 | ((L3 < 70) & (lab3[..., 1] > 15)), np.ones((1, 7)))
    mo = (L3 > 30) & (L3 < 64) & (lab3[..., 1] > 12) & core
    wid = {y: int(span[y].sum()) for y in range(fy0, fy1 + 1)}; mx = max(wid.values())
    chin = max(y for y in wid if wid[y] >= 0.5 * mx and y > lash); out['chin'] = chin
    mo[:(ey - oy) * S3] = False; mo[(chin + 1 - oy) * S3:] = False
    if len(eyes) == 2:
        a0 = int((eyes[0]['cx'] + 1.5 - meta['ox']) * S3); a1 = int((eyes[1]['cx'] - meta['ox']) * S3)
        mo[:, :max(0, a0)] = False; mo[:, max(0, a1):] = False
    ys, xs = np.where(mo)
    if len(ys) >= 2:
        my = int(np.floor(np.median(ys) / S3 + oy)); cx = int(np.floor(np.median(xs) / S3 + meta['ox']))
        out['mouth'] = (cx, my)
    if view == 'E':   # profile: the mouth sits on the front contour, 1 row above the chin
        my = chin - 1; xs = np.where(sk[my])[0]
        if len(xs): out['mouth'] = (int(xs.max()), int(my))
    return out


def stamp(g, t, x0, y0, fm):
    for j, r in enumerate(t):
        for i, c in enumerate(r):
            y, x = y0 + j, x0 + i
            if c == '_' or not (0 <= y < g.shape[0] and 0 <= x < g.shape[1]): continue
            b = g[y, x]
            if c == '.':
                if fm[y, x] and b in 'KhHgLWDdQOoeER.': g[y, x] = 's'
                continue
            if b == '.' and not fm[y, x]: continue
            if c == 'm' and j == 0 and b not in SKIN: continue   # brows only on skin
            g[y, x] = 'W' if c == '@' else c


def apply(g, meta, view, expr='neutral', det=None, dy=0):
    g = g.copy(); e = expr_key(expr); det = det or detect(g, meta, view)
    if dy:
        det = json.loads(json.dumps(det, default=str)); [ey.update(y0=ey['y0'] + dy) for ey in det['eyes']]
    fr = det.get('face_rows')
    if not fr: return g, det
    fm = face_mask(g, fr[0] - 1, fr[1] + 2)
    # clear old eye pixels inside each template box (only enclosed/face px), then stamp
    for ey in det['eyes']:
        t = kind_tmpl(ey['kind'], e)
        clear = ['.' * len(r) for r in t] + ['.' * len(t[0])]
        stamp(g, clear, ey['x0'], ey['y0'], fm); stamp(g, t, ey['x0'], ey['y0'], fm)
    if det.get('mouth'):
        cx, my = det['mouth']; mt = SPEC['mouth'][e]
        x0 = cx - 2 if view != 'E' else cx - 3
        clear = ['....'] * 3
        stamp(g, clear, x0, my - 1, fm); stamp(g, mt, x0, my - 1, fm)
    n = SPEC['blush'][e]
    if view == 'NE' and det.get('ne_cheek'):
        ch = det['ne_cheek']; mid = ch[len(ch) // 2]
        if n: g[mid[1], mid[0]] = 'k'
        nl = SPEC['ne_lash'][e]; ly = ch[max(0, len(ch) // 2 - 3)][1]
        for k in range(nl):
            x, y = mid[0] + 1, ly - k
            if g[y, x] in '.K' and g[y, x - 1] in SKIN | {'K'}: g[y, x] = 'K'
    elif n:
        for ey in det['eyes']:
            by = ey['y0'] + 5; w = min(n, 2 if ey['kind'] in ('far', 'profile') else n)
            cx = ey['x0'] + (2 if ey['kind'] in ('front_left', 'profile') else 1)
            xs = range(cx - (w - 1) // 2, cx - (w - 1) // 2 + w)
            for x in xs:
                if g[by, x] in 'sS': g[by, x] = 'k'
    return g, det


if __name__ == '__main__':
    a = sys.argv[1:]
    if a[0] == 'tmpl':
        print('\n'.join(kind_tmpl(a[1], a[2])))
    elif a[0] == 'detect':
        g, meta = Z.read(a[1]); d = detect(g, meta, a[2]); print(json.dumps({k: v for k, v in d.items() if k != 'ne_cheek'}, default=str))
    elif a[0] == 'apply':
        dy = int(os.environ.get('EYE_DY', '0'))
        g, meta = Z.read(a[1]); expr = a[3] if len(a) > 4 else 'neutral'
        g2, d = apply(g, meta, a[2], expr, dy=dy); keys, rgb, _ = Z.load_pal(M.PAL); Z.save(g2, a[-1], keys, rgb, meta)
        print(a[-1], int((g2 != g).sum()), 'px')
