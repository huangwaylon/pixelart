"""lock3 HEAD STAMP builder (S3 r3 owns it). Sources (hand-typed, source of truth): hybrid/lock3/src/head_{S,SE,E,NE,N}.pix
   o = bow LOOP mask, k = bow KNOT mask; they are shaded here by one rule (key light upper-left, red_0 underside), so every
   direction and the mirrors share the same bow lighting.
W / SW / NW = mirror of E / SE / NE: the hair shape and the strand groups are mirrored, the lit upper-left mass + the
hair_2 sheen are rebuilt on the upper-LEFT (same pixel count as the source), the bow mask is mirrored and re-shaded.
Acting stamps (head(d, e, t, act)):
   expr  e in calm glare wide kiai squint smile squeeze closed grit
   act   none | back (tilt-back: face up 1 / crown back 1) | down (forward-down: crown 1 px toward facing, face down 1)
         | squash (-2 dome rows) | lag (bow + bun cel 1 px against facing)
Python API: head(d, e='calm', t=0, act=None) -> char grid;  bow_cel(d) -> (grid, rows)"""
import json, os, sys
import numpy as np
from scipy import ndimage
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import read_grid, to_rgba, save, strip, write_grid

L3 = 'hybrid/lock3'
EXPRS = ['calm', 'glare', 'wide', 'kiai', 'squint', 'smile', 'squeeze', 'closed', 'grit']
FRONT = ['S', 'SE', 'E', 'SW', 'W']
MOUTH = {'S': (11, 26, 2), 'SE': (14, 25, 1), 'E': (21, 26, 1)}      # x, y, width (left px)
MIRROR = {'W': 'E', 'SW': 'SE', 'NW': 'NE'}
FACING = {'S': 0, 'SE': 1, 'E': 1, 'NE': 1, 'N': 0, 'NW': -1, 'W': -1, 'SW': -1}   # screen x sign of facing
H_LOCK2 = {'S': 30, 'SE': 29, 'E': 30, 'NE': 29, 'N': 27, 'NW': 29, 'W': 30, 'SW': 29}  # compositor anchor heights


def lightscore(g):
    hair = np.isin(g, list('hHJ'))
    ys, xs = np.nonzero(hair)
    cx, cy, sx, sy = xs.mean(), ys.mean(), xs.std() + 1e-6, ys.std() + 1e-6
    yy, xx = np.mgrid[0:g.shape[0], 0:g.shape[1]]
    return -(xx - cx) / sx * 0.85 - (yy - cy) / sy, hair


def shade_bow(g):
    """o/k masks -> red ramp. loops: upper-left rim C, underside v, right edge r, crease r next to the knot, body R.
    knot: C top-left, r bottom row, R."""
    g = g.copy()
    O = g == 'o'; Kn = g == 'k'
    lab, n = ndimage.label(O)
    H, W = g.shape
    def at(y, x): return g[y, x] if 0 <= y < H and 0 <= x < W else '.'
    src = g.copy()
    for i in range(1, n + 1):
        ys, xs = np.nonzero(lab == i)
        bx0, bx1, by0, by1 = xs.min(), xs.max(), ys.min(), ys.max()
        for y, x in zip(ys, xs):
            up, dn, lf, rt = at(y - 1, x), at(y + 1, x), at(y, x - 1), at(y, x + 1)
            u = (x - bx0) / max(1, bx1 - bx0); t = (y - by0) / max(1, by1 - by0)
            near_k = any(src[y + b, x + a] == 'k' for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1))
                         if 0 <= y + b < H and 0 <= x + a < W)
            c = 'R'
            if (rt not in 'ok' and u > 0.5) or (t > 0.6 and u > 0.55) or near_k: c = 'r'
            if (up not in 'ok' and u < 0.6) or (lf not in 'ok' and t < 0.45): c = 'C'
            if dn not in 'ok': c = 'v'
            g[y, x] = c
    ks = list(zip(*np.nonzero(Kn)))
    if ks:
        y0 = min(y for y, _ in ks); y1 = max(y for y, _ in ks)
        for y, x in ks:
            c = 'R'
            if y == y1 or at(y + 1, x) not in 'k': c = 'r'
            g[y, x] = c
        top = [p for p in ks if p[0] == y0]
        tl = min(top, key=lambda p: p[1]); g[tl] = 'C'
    return g


def relight_mirror(src):
    """mirror a source head; rebuild the lit mass + sheen on the upper-left."""
    s0, hair0 = lightscore(src)
    lit0 = np.isin(src, list('HJ'))
    thr = np.quantile(s0[hair0], 0.62)
    mass0 = lit0 & (s0 >= thr)
    strands0 = lit0 & ~mass0
    nJ = int((src == 'J').sum())
    g = src[:, ::-1].copy()
    strands = strands0[:, ::-1]
    hair = np.isin(g, list('hHJ'))
    g[hair] = 'h'; g[strands & hair] = 'H'
    s1, _ = lightscore(g)
    cand = hair & ~strands
    order = np.argsort(-s1[cand]); ys, xs = np.nonzero(cand)
    for i in order[:int(mass0.sum())]: g[ys[i], xs[i]] = 'H'
    dist = ndimage.distance_transform_cdt(g != '.', metric='taxicab')
    cj = hair & (dist == 3) & (g == 'H')
    ys, xs = np.nonzero(cj); order = np.argsort(-s1[cj])
    for i in order[:nJ]: g[ys[i], xs[i]] = 'J'
    return g


def base_raw(d):
    if d in MIRROR: return relight_mirror(read_grid(f'{L3}/src/head_{MIRROR[d]}.pix'))
    return read_grid(f'{L3}/src/head_{d}.pix')


def base(d): return shade_bow(base_raw(d))


def bow_rows(d):
    g = base_raw(d)
    ys = np.nonzero(np.isin(g, list('ok')).any(1))[0]
    return int(ys.max()) + 1


def eyes(g):
    m = np.isin(g, list('eEw'))
    m &= ~(g == 'w') | ndimage.binary_dilation(np.isin(g, list('eE')), iterations=1)
    lab, n = ndimage.label(m, structure=np.ones((3, 3)))
    out = []
    for i in range(1, n + 1):
        ys, xs = np.nonzero(lab == i)
        if len(ys) < 3: continue
        out.append(dict(x0=int(xs.min()), x1=int(xs.max()), y0=int(ys.min()), y1=int(ys.max())))
    return sorted(out, key=lambda e: e['x0'])


def mouth_of(d, W):
    if d in MOUTH: return MOUTH[d]
    if MIRROR.get(d) in MOUTH:
        x, y, w = MOUTH[MIRROR[d]]; return (W - x - w, y, w)
    return None


def expr(g, d, e):
    g = g.copy()
    if e == 'calm' or d not in FRONT: return g
    H, W = g.shape
    E = eyes(g)
    mo = mouth_of(d, W)
    for ey in E:
        x0, x1, y0, y1 = ey['x0'], ey['x1'], ey['y0'], ey['y1']
        yl = y0 - 1
        fx = np.mean([q['x0'] + q['x1'] for q in E]) / 2 if len(E) > 1 else (x1 + 2 if d in ('E', 'SE', 'S') else x0 - 2)
        inner = x1 if (x0 + x1) / 2 < fx else x0
        outer = x0 if inner == x1 else x1
        step = 1 if inner == x1 else -1
        def clear_eye():
            for y in range(y0, y1 + 1):
                for x in range(x0, x1 + 1):
                    if g[y, x] in 'eEw': g[y, x] = 's'
        if e in ('glare', 'grit'):
            for x in range(x0, x1 + 1):
                if x != outer and g[y0, x] in 'eEw': g[y0, x] = 'K'
            if y0 + 1 <= y1: g[y0 + 1, inner] = 'K'
            g[yl, outer] = 'K'
        elif e == 'wide':
            for x in range(x0, x1 + 1):
                if g[yl - 1, x] in 'hHJmsS': g[yl - 1, x] = 'K'
                if g[yl, x] == 'K': g[yl, x] = 'e'
            for x in range(x0, x1 + 1):
                if g[y0, x] == 'w': g[y0, x] = 'e'; g[yl, x] = 'w'
        elif e == 'kiai':
            g[y0, inner] = 'K'; g[y0, inner - step] = 'K'
            for x in range(x0, x1 + 1):
                if g[y1, x] in 'eE': g[y1, x] = 'K'
        elif e in ('squint', 'smile', 'squeeze', 'closed'):
            clear_eye()
            for x in range(x0, x1 + 1):
                if g[yl, x] == 'K': g[yl, x] = 's'
            w = x1 - x0 + 1
            if e == 'squint':
                for x in range(x0, x1 + 1): g[y0, x] = 'K'
                g[y0 + 1, outer] = 'K'
            elif e == 'closed':                                  # blink / closed: 1 px lash line, low, outer flick
                for x in range(x0, x1 + 1): g[y0 + 1, x] = 'K'
                g[y0, outer] = 'K'
            elif e == 'smile':
                for x in range(x0 + 1, x1): g[y0, x] = 'K'
                g[y0 + 1, x0] = 'K'; g[y0 + 1, x1] = 'K'
            else:
                mid = y0 + 1
                pts = [(outer, y0), (outer + step, y0), (inner, mid), (outer + step, mid + 1), (outer, mid + 1)] if w >= 3 else \
                      [(outer, y0), (inner, mid), (outer, mid + 1)]
                if w >= 4: pts += [(inner - step, mid)]
                for x, y in pts: g[y, x] = 'K'
    if mo:
        x, y, w = mo
        if e == 'glare':
            for k in range(-1, w + 1):
                if g[y, x + k] in 'sS': g[y, x + k] = 'm'
        elif e == 'grit':                       # 2 px dark-red gritted mouth right under the nose, no cheek line
            xs = [x, x + 1] if w >= 2 else ([x, x + 1] if FACING[d] >= 0 and d != 'E' else [x - 1, x])
            if d == 'E': xs = [x - 1, x]
            for xx in xs:
                if 0 <= xx < W and g[y, xx] in 'sSm': g[y, xx] = 'v'
        elif e == 'wide':
            g[y, x] = 'K'
            if w > 1: g[y, x + 1] = 'K'
            if g[y + 1, x] in 'sm': g[y + 1, x] = 'v'
        elif e == 'kiai':
            for k in range(0, max(2, w)): g[y, x + k] = 'K'
            g[y + 1, x] = 'v'
            if g[y + 1, x + 1] in 'sm': g[y + 1, x + 1] = 'K' if w < 2 else 'v'
        elif e == 'smile':
            g[y, x - 1] = 'm'; g[y, x + w] = 'm'
            for k in range(w): g[y + 1, x + k] = 'm' if g[y + 1, x + k] in 'sS' else g[y + 1, x + k]
            for k in range(w): g[y, x + k] = 's'
        elif e == 'squeeze':
            for k in range(-1, w + 1): g[y, x + k] = 'K'
        elif e == 'squint':
            for k in range(w): g[y, x + k] = 'm'
    return g


def tilt(g, t):
    if t == 0: return g
    H, W = g.shape
    out = np.full((H + 1, W), '.', dtype=g.dtype)
    c = W // 2
    for x in range(W):
        dy = (1 if t > 0 else 0) if x >= c else (0 if t > 0 else 1)
        out[dy:dy + H, x] = g[:, x]
    return out


def face_top(g):
    """first row of the face window (skin) -> rows above it are 'dome'"""
    ys = np.nonzero(np.isin(g, list('msS')).any(1))[0]
    return int(ys.min()) if len(ys) else g.shape[0] - 6


def act(g, d, a):
    """acting variants; all keep the stamp width; height may change (-2 squash). Anchor = last row."""
    if not a: return g
    H, W = g.shape
    f = FACING[d]
    if a == 'squash':                                  # drop 2 rows from the dome (between bow and face)
        br = bow_rows(d); ft = face_top(g)
        rows = list(range(br + 1, ft - 1))
        kill = {rows[len(rows) // 3], rows[2 * len(rows) // 3]}
        return np.array([g[y] for y in range(H) if y not in kill])
    if a == 'back':                                    # tilt-back: crown 1 px against facing, face rows up 1
        out = g.copy()
        if f:
            ft = face_top(g)
            for y in range(0, ft - 3):
                out[y] = np.roll(g[y], -f); out[y][(0 if -f < 0 else W - 1)] = '.' if True else out[y]
            return out
        ft = face_top(g)                               # S / N: face window rises 1 px (look up)
        out = g.copy()
        for y in range(ft - 1, H - 2): out[y] = g[y + 1]
        return out
    if a == 'down':                                    # forward-down: crown 1 px toward facing, face 1 px down
        out = g.copy()
        ft = face_top(g)
        if f:
            for y in range(0, ft - 3):
                out[y] = np.roll(g[y], f)
                out[y][W - 1 if f > 0 else 0] = '.'
            return out
        out = np.vstack([g[:ft], g[ft - 1:ft], g[ft:]])   # S/N: one more hair row over the face (looking down)
        return out
    if a == 'lag':                                     # bow + bun cel 1 px against facing (or up for S/N)
        br = bow_rows(d)
        out = g.copy()
        dx = -f if f else 0
        dy = 0 if f else -1
        cel = g[:br].copy()
        out[:br][np.isin(out[:br], list('vrRCok'))] = '.'
        if dy: out = np.vstack([np.full((1, W), '.', dtype=g.dtype), out]); cel_y = 0
        else: cel_y = 0
        for y in range(cel.shape[0]):
            for x in range(W):
                c = cel[y, x]
                if c == '.': continue
                xx = x + dx
                if 0 <= xx < W: out[cel_y + y + (0 if dy else 0), xx] = c
        # re-close hair under the old bow position
        return out
    raise SystemExit('unknown act ' + a)


def head(d, e='calm', t=0, a=None):
    return act(tilt(expr(base(d), d, e), t), d, a)


ACTS = [None, 'back', 'down', 'squash', 'lag']


def stats(g):
    hair = np.isin(g, list('hHJ')).sum()
    W = (g != '.').any(0).sum()
    return dict(red=int(np.isin(g, list('vrRC')).sum()), lit=round(float(np.isin(g, list('HJ')).sum()) / hair, 3),
                J=int((g == 'J').sum()), width=int(W))


def main():
    os.makedirs(L3, exist_ok=True)
    info = {}
    sheet = []
    for d in ['S', 'SE', 'E', 'NE', 'N', 'NW', 'W', 'SW']:
        g = base(d)
        save(to_rgba(g), f'{L3}/head_{d}.png')
        write_grid(g, f'{L3}/head_{d}.pix', f'lock3 head {d} (built by tools/hybrid/h4/heads.py from src/)')
        br = bow_rows(d)
        bow = g.copy(); bow[br:] = '.'
        save(to_rgba(bow[:br]), f'{L3}/bow_{d}.png')
        for t in (1, -1):
            save(to_rgba(tilt(g, t)), f'{L3}/head_{d}_tilt{t:+d}.png')
        row = [to_rgba(g)]
        for a_ in ACTS[1:]:
            ga = act(g, d, a_); save(to_rgba(ga), f'{L3}/head_{d}_act-{a_}.png'); row.append(to_rgba(ga))
        if d in FRONT:
            for e in EXPRS[1:]:
                ge = expr(g, d, e)
                save(to_rgba(ge), f'{L3}/head_{d}_{e}.png'); row.append(to_rgba(ge))
        info[d] = dict(size=[int(g.shape[1]), int(g.shape[0])], chin_row=int(g.shape[0] - 1), cx=(g.shape[1] - 1) / 2,
                       bow_rows=br, eyes=eyes(g) if d in FRONT else [], mouth=mouth_of(d, g.shape[1]),
                       mirrored_from=MIRROR.get(d), **stats(g))
        sheet.append((d, row))
    json.dump(dict(
        how_to_use='Paste whole stamps at integer offsets, never scale. All heads 24 wide, centre col 11.5. Align by the LAST '
                   'row (chin / nape) on the body neck row (lock2 anchor heights kept: S30 SE29 E30 NE29 N27). '
                   'Acting: head_<D>_act-{back,down,squash,lag}.png; expressions incl. closed + grit on S SE E SW W. '
                   'Bow cels bow_<D>.png = rows 0..bow_rows-1 for lag offsets.',
        exprs=EXPRS, acts=ACTS[1:], dirs=info), open(f'{L3}/heads.json', 'w'), indent=1)
    from PIL import Image, ImageDraw
    z = 6; cw, chh = 26 * z, 33 * z
    im = Image.new('RGB', (cw * 13 + 60, chh * 8), (36, 32, 44)); dr = ImageDraw.Draw(im)
    for r, (d, row) in enumerate(sheet):
        dr.text((4, r * chh + 4), d, fill=(230, 230, 230))
        for k, a in enumerate(row):
            im.paste(strip([a], z=z), (60 + k * cw, r * chh))
    im.save(f'{L3}/lock3_heads_x6.png')
    for d in info: print(d, {k: info[d][k] for k in ('size', 'red', 'lit', 'J', 'width', 'bow_rows')})


if __name__ == '__main__':
    main()


BOW_ROWS = {d: bow_rows(d) for d in ['S', 'SE', 'E', 'NE', 'N', 'NW', 'W', 'SW']}
