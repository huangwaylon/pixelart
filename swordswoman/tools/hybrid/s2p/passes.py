"""Global polish passes for S2 (each returns a list of {x,y,from,to,reason} edits)."""
import numpy as np
from scipy import ndimage as ndi
N8 = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
N4 = [(-1, 0), (1, 0), (0, -1), (0, 1)]
STEEL = set('tTw'); REDS = set('vrRC'); HAIR = set('hHJ')
KEEP = set('eEwPpSuL')  # eye, glint, pink ribbons/smear, skin_2 highlight, purple, buckle-leather: never auto-merged


def nb(g, y, x, n=N8):
    H, W = g.shape
    return [g[y + dy, x + dx] if 0 <= y + dy < H and 0 <= x + dx < W else '.' for dy, dx in n]


def _set(g, y, x, c, log, why):
    if g[y, x] != c:
        log.append({'x': int(x), 'y': int(y), 'from': str(g[y, x]), 'to': c, 'reason': why})
        g[y, x] = c


def blade_clean(g, log):
    """skin/leather/red specks embedded in the 2 px blade (pixelize sel-out residue) -> steel_0 spine"""
    for y, x in zip(*np.nonzero(np.isin(g, list('mlsHhr')))):
        n = nb(g, y, x)
        st = sum(c in STEEL for c in n); body = sum(c not in STEEL and c != '.' for c in n)
        if st >= 2 and body <= 1:
            _set(g, y, x, 't', log, 'blade: foreign tone inside the katana line -> steel_0 spine')


def despeckle(g, log, tones=REDS | set('lh'), rounds=2):
    """1 px tone specks inside a flat cluster (blotchy dress shading) -> the surrounding tone"""
    for _ in range(rounds):
        out = g.copy()
        for y, x in zip(*np.nonzero(np.isin(g, list(tones)))):
            n = nb(g, y, x)
            if g[y, x] in n:
                same = sum(c == g[y, x] for c in n)
            else:
                same = 0
            if same > 1:
                continue
            cand = [c for c in n if c in tones and c != g[y, x]]
            if not cand:
                continue
            c, k = max(((c, cand.count(c)) for c in set(cand)), key=lambda t: t[1])
            if k >= 5:
                out[y, x] = c
                log.append({'x': int(x), 'y': int(y), 'from': str(g[y, x]), 'to': c,
                            'reason': 'despeckle: lone tone pixel inside a %s cluster' % c})
        g[:] = out


def red_mode(g, log, region=None):
    """3x3 mode filter on red-ramp pixels only (merge 1-2 px shading crumbs into the larger clusters);
    outline, skin, hair, steel untouched. region = (x0,y0,x1,y1) limits it to the body."""
    out = g.copy()
    H, W = g.shape
    ys, xs = np.nonzero(np.isin(g, list('rR')))
    for y, x in zip(ys, xs):
        if region and not (region[0] <= x < region[2] and region[1] <= y < region[3]):
            continue
        n = nb(g, y, x)
        cnt = {c: n.count(c) for c in 'rR'}
        me = cnt[g[y, x]]
        other = 'R' if g[y, x] == 'r' else 'r'
        if me <= 1 and cnt[other] >= 4:
            out[y, x] = other
            log.append({'x': int(x), 'y': int(y), 'from': str(g[y, x]), 'to': other,
                        'reason': 'dress cluster: %s crumb merged into %s mass' % (g[y, x], other)})
    g[:] = out


def hair_shade(g, log, light=(0.45, 0.55), tJ=0.50, tH=0.60, ymax=None):
    """darken the hair dome toward iso_v5 (near-black brown): shadow side (lower/right, light from
    top-left) hair_1 -> hair_0, hair_2 strands -> hair_1 except on the lit top-left."""
    m = np.isin(g, list(HAIR))
    if ymax is not None:
        m[ymax:] = False
    lab, n = ndi.label(m, structure=np.ones((3, 3)))
    if n == 0:
        return
    sizes = ndi.sum(m, lab, range(1, n + 1))
    keep = np.zeros_like(m)
    for k, s in enumerate(sizes, 1):
        if s >= 12:
            keep |= lab == k
    ys, xs = np.nonzero(keep)
    y0, y1, x0, x1 = ys.min(), ys.max(), xs.min(), xs.max()
    skin = ndi.binary_dilation(np.isin(g, list('msSeE')), iterations=2)
    for y, x in zip(ys, xs):
        if skin[y, x]:
            continue                      # bangs / side locks framing the face keep their value
        u = (x - x0) / max(1, x1 - x0); v = (y - y0) / max(1, y1 - y0)
        s = light[0] * u + light[1] * v
        if g[y, x] == 'J' and s > tJ:
            _set(g, y, x, 'H', log, 'hair value: sheen only on the lit top-left (iso_v5 dark dome)')
        elif g[y, x] == 'H' and s > tH:
            _set(g, y, x, 'h', log, 'hair value: shadow side to hair_0 (iso_v5 dark dome)')


def lint_clean(g, log, protect=None):
    """orphans (no same-tone 8-neighbour) merged into the majority neighbour tone, 1 px spurs removed,
    1 px silhouette notches filled with outline. Protected: eye, glint, pink, smear, steel."""
    H, W = g.shape
    prot = np.zeros(g.shape, bool) if protect is None else protect
    # orphans
    out = g.copy()
    for y, x in zip(*np.nonzero(g != '.')):
        c = g[y, x]
        if c in KEEP or c in STEEL or c == 'K' or prot[y, x]:
            continue
        n = nb(g, y, x)
        if c in 'mh' and sum(k in 'sS' for k in n) >= 4:
            continue                      # nose / mouth / brow pixels in the face are deliberate
        if c in n:
            continue
        op = [k for k in n if k != '.' and k not in STEEL and k not in KEEP]
        if len(op) < 5:
            continue
        # prefer a neighbour of the same ramp
        same_ramp = [k for k in op if k != 'K' and _ramp(k) == _ramp(c)]
        pool = same_ramp if same_ramp else [k for k in op if k != 'K'] or op
        to = max(set(pool), key=pool.count)
        out[y, x] = to
        log.append({'x': int(x), 'y': int(y), 'from': c, 'to': to, 'reason': 'orphan merged into neighbour cluster'})
    g[:] = out
    # spurs: opaque px with >=3 transparent 4-nbrs (not steel / smear / ground row)
    for y, x in zip(*np.nonzero(g != '.')):
        c = g[y, x]
        if c in STEEL or c in 'pP' or prot[y, x]:
            continue
        n4 = nb(g, y, x, N4)
        if sum(k == '.' for k in n4) >= 3 and y < 103:
            _set(g, y, x, '.', log, 'spur: 1 px hanging pixel removed')
    # notches: transparent with >=3 opaque 4-nbrs -> outline
    for y, x in zip(*np.nonzero(g == '.')):
        if not (0 < x < W - 1 and 0 < y < H - 1) or prot[y, x]:
            continue
        n4 = nb(g, y, x, N4)
        if sum(k != '.' and k not in STEEL and k not in 'pP' for k in n4) >= 3:
            _set(g, y, x, 'K', log, 'notch: 1 px bite in the silhouette filled with outline')


def _ramp(c):
    for r in ('vrRC', 'mSs', 'hHJ', 'lL', 'Kd', 'tTw', 'eE', 'pP'):
        if c in r:
            return r
    return c


def outline_close(g, log):
    """exterior pixel of body (non steel/pink) touching transparency that is a mid tone on the
    bottom/right -> outline (closes gaps left by edits); conservative: only where the outward 4-nbr is
    transparent AND both side nbrs along the edge are outline."""
    H, W = g.shape
    for y, x in zip(*np.nonzero(np.isin(g, list('vrRCmsShHJlLd')))):
        for dy, dx in ((1, 0), (0, 1)):
            yy, xx = y + dy, x + dx
            if not (0 <= yy < H and 0 <= xx < W) or g[yy, xx] != '.':
                continue
            a = (y + dx, x + dy); b = (y - dx, x - dy)
            if all(0 <= p[0] < H and 0 <= p[1] < W and g[p] == 'K' for p in (a, b)):
                _set(g, y, x, 'K', log, 'outline gap closed (bottom/right edge)')
                break


def corset_dress(g, log, ymin=74, ymax=100, straps=(0.55,), buckle_u=0.4, top_edge=True, lit=0.55):
    """repaint the muddy leather_1 band as the buckled corset: leather_2 top edge on the lit 2/3,
    two leather_2 belt straps with a steel_1 buckle, outline seam under it."""
    m = g == 'l'
    m[:ymin] = False; m[ymax:] = False
    lab, n = ndi.label(m, structure=np.ones((3, 3)))
    if n == 0:
        return None
    sizes = ndi.sum(m, lab, range(1, n + 1))
    k = int(np.argmax(sizes)) + 1
    if sizes[k - 1] < 20:
        return None
    reg = lab == k
    ys, xs = np.nonzero(reg)
    y0, y1, x0, x1 = ys.min(), ys.max(), xs.min(), xs.max()
    # trim to the dense band (rows with >= 4 px)
    rows = [y for y in range(y0, y1 + 1) if reg[y].sum() >= 4]
    if len(rows) < 4:
        return None
    y0, y1 = rows[0], rows[-1]
    hgt = y1 - y0 + 1
    if top_edge:
        for x in range(x0, x1 + 1):
            col = np.nonzero(reg[:, x])[0]
            col = col[(col >= y0) & (col <= y1)]
            if len(col) and (x - x0) <= lit * (x1 - x0):
                _set(g, col[0], x, 'L', log, 'corset: leather_2 top edge on the lit side')
    for f in straps:
        y = y0 + int(round(f * (hgt - 1)))
        xs_r = np.nonzero(reg[y])[0]
        if len(xs_r) < 4:
            continue
        a, b = xs_r.min(), xs_r.max()
        for x in xs_r:
            if g[y, x] == 'l' and (x - a) <= lit * (b - a):
                _set(g, y, x, 'L', log, 'corset: belt strap, leather_2 on the lit side only')
        bx = a + int(round(buckle_u * (b - a)))
        _set(g, y, bx, 'T', log, 'corset: buckle (steel_1)')
        if g[y - 1, bx] in 'lL':
            _set(g, y - 1, bx, 'K', log, 'corset: buckle frame')
        if g[y + 1, bx] in 'lL':
            _set(g, y + 1, bx, 'K', log, 'corset: buckle frame')
    return (int(x0), int(y0), int(x1), int(y1))


def blade_find(g, min_px=8):
    """largest elongated t/w component -> (guard_end, tip_end) along its PCA axis; guard = end nearer
    the body centroid."""
    m = np.isin(g, ['t', 'w'])
    lab, n = ndi.label(m, structure=np.ones((3, 3)))
    best = None
    for k in range(1, n + 1):
        ys, xs = np.nonzero(lab == k)
        if len(ys) < min_px:
            continue
        P_ = np.stack([xs, ys], 1).astype(float); c = P_.mean(0)
        w, V = np.linalg.eigh(np.cov((P_ - c).T))
        if w[1] < 4 * max(w[0], 0.05):
            continue
        if best is None or len(ys) > best[0]:
            best = (len(ys), P_, c, V[:, 1])
    if best is None:
        return None
    _, P_, c, u = best
    s = (P_ - c) @ u
    a, b = c + u * s.min(), c + u * s.max()
    body = np.isin(g, list('vrRCmsShHJlLKd')) & ~m
    by, bx = np.nonzero(body); bc = np.array([bx.mean(), by.mean()])
    if np.linalg.norm(a - bc) > np.linalg.norm(b - bc):
        a, b = b, a
    return a, b


def blade_redraw(g, log, guard, tip, clear=2.4, start=1.0):
    """clean contiguous 2 px katana: steel_2 edge line + steel_0 spine offset axis-aligned (up for a
    shallow blade, left for a steep one), so steep diagonals never break into 't.w' gaps."""
    import draw as D
    gv = np.array(guard, float); tv = np.array(tip, float)
    v = tv - gv; L = np.linalg.norm(v); u = v / max(L, 1e-6)
    nrm = np.array([-u[1], u[0]])
    yy, xx = np.mgrid[0:g.shape[0], 0:g.shape[1]]
    P_ = np.stack([xx - gv[0], yy - gv[1]], -1)
    sp = P_ @ u; dist = np.abs(P_ @ nrm)
    near = (sp > start) & (sp < L + 2) & (dist < clear) & np.isin(g, ['t', 'w'])
    for y, x in zip(*np.nonzero(near)):
        _set(g, y, x, '.', log, 'blade: old broken katana pixels cleared before redraw')
    a = np.round(gv + u * (start + 0.5)).astype(int); b = np.round(tv).astype(int)
    pts = D.pixel_perfect(D.bresenham(int(a[0]), int(a[1]), int(b[0]), int(b[1])))
    steep = abs(u[1]) > abs(u[0])
    off = (-1, 0) if steep else (0, -1)
    for i, (x, y) in enumerate(pts):
        if not (0 <= x < 128 and 0 <= y < 128):
            continue
        if g[y, x] in '.tw' or i > 1:
            if g[y, x] not in 'msS' or i > 3:
                _set(g, y, x, 'w', log, 'blade: steel_2 cutting edge')
        if i < len(pts) - 1:
            sx, sy = x + off[0], y + off[1]
            if 0 <= sx < 128 and 0 <= sy < 128 and g[sy, sx] in '.tw':
                _set(g, sy, sx, 't', log, 'blade: steel_0 spine (axis-aligned, contiguous)')


def crescent(g, log, cx, cy, rx, ry, a0, a1, W, tones=('w', 'P', 'p'), core=1.3, tmin=1.2, over=False,
             reason='blade-arc smear'):
    """Claude crescent smear: outer edge = the tip path ellipse (steel_2 core, always >= 1 px so it
    never breaks), thickness grows linearly tail -> lead (W px), pink_1 then pink_0 toward the inside.
    Painted behind the character unless over."""
    import math
    lo, hi = min(a0, a1), max(a0, a1)
    R = int(max(rx, ry) + 2)
    for y in range(int(cy - R), int(cy + R) + 1):
        for x in range(int(cx - R), int(cx + R) + 1):
            if not (0 <= x < g.shape[1] and 0 <= y < g.shape[0]):
                continue
            ex, ey = (x - cx) / rx, (y - cy) / ry
            ang = math.degrees(math.atan2(ey, ex))
            while ang < lo:
                ang += 360
            while ang > lo + 360:
                ang -= 360
            if ang > hi:
                continue
            t = (ang - a0) / (a1 - a0)
            rr = math.hypot(ex, ey)
            rloc = math.hypot(rx * math.cos(math.radians(ang)), ry * math.sin(math.radians(ang)))
            d = (1.0 - rr) * rloc + 0.5          # px inward from the outer edge
            th = tmin + (W - tmin) * t
            if d < 0 or d >= th:
                continue
            c0 = tones[0] if t > 0.22 else tones[1]      # the tail fades: no steel core
            c = c0 if d < core else (tones[1] if d < core + (th - core) * 0.55 else tones[2])
            if g[y, x] == '.' or over:
                _set(g, y, x, c, log, reason)
