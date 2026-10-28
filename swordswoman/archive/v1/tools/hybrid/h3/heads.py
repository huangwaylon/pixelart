"""lock2 HEAD STAMP v2 builder (shared foundation; S3 owns it, S5 consumes it).

Sources (hand-typed, source of truth): hybrid/lock2/src/head_{S,SE,E,NE,N}.pix  (24 wide, ~0.9x of lock v1, dark dome).
W / SW / NW = mirror of E / SE / NE, re-lit (the lit hair_1 rim crescent + hair_2 sheen are rebuilt on the upper-LEFT;
strand strokes are kept, mirrored). Bodies are never mirrored; heads are symmetric by LOCK decision.

Outputs in hybrid/lock2/:
  head_<D>.png                  calm, the canonical stamp
  head_<D>_<expr>.png           expr in calm glare wide kiai squint smile squeeze (front-ish dirs S SE E SW W)
  head_<D>_tilt{+1,-1}.png      1 px tilt (column shear about the head centre; + = viewer-right side down)
  bow_<D>.png                   bun + bow cel (rows 0..bow_rows) for lag offsets
  heads.json                    per-dir size, chin row, centre, eye boxes, mouth, bow rows; how to use
  lock2_sheet_x6.png            review sheet
Python API (used by the h3 compositor): head(d, expr='calm', tilt=0) -> char grid
"""
import json, os, sys
import numpy as np
from scipy import ndimage
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import read_grid, to_rgba, save, strip, write_grid

L2 = 'hybrid/lock2'
EXPRS = ['calm', 'glare', 'wide', 'kiai', 'squint', 'smile', 'squeeze']
FRONT = ['S', 'SE', 'E', 'SW', 'W']
MOUTH = {'S': (11, 26, 2), 'SE': (14, 25, 1), 'E': (21, 26, 1)}      # x, y, width (left px)
BOW_ROWS = {'S': 7, 'SE': 7, 'E': 7, 'NE': 8, 'N': 6}
MIRROR = {'W': 'E', 'SW': 'SE', 'NW': 'NE'}


def crescent(g):
    """the lit rim crescent mask (upper-left), same rule as the drafts"""
    hair = np.isin(g, list('hHJ'))
    dist = ndimage.distance_transform_cdt(g != '.', metric='taxicab')
    ys, xs = np.nonzero(hair)
    cy, cx = ys.mean() + 2, xs.mean() + 1
    M = np.zeros(g.shape, bool); J = np.zeros(g.shape, bool)
    for y, x in zip(ys, xs):
        ang = np.degrees(np.arctan2(-(y - cy), x - cx)) % 360
        d = dist[y, x]
        if 95 <= ang <= 215 and 2 <= d <= 4:
            M[y, x] = True
            if 125 <= ang <= 165 and d == 3: J[y, x] = True
    return M, J


def base(d):
    if d in MIRROR:
        src = read_grid(f'{L2}/src/head_{MIRROR[d]}.pix')
        M, J = crescent(src)
        strokes = (src == 'H') & ~M                    # strand strokes (geometry) survive the mirror
        g = src[:, ::-1].copy(); strokes = strokes[:, ::-1]
        hair = np.isin(g, list('hHJ'))
        g[hair] = 'h'; g[strokes] = 'H'
        M2, J2 = crescent(g)
        g[M2 & hair] = 'H'; g[J2 & hair] = 'J'
        return g
    return read_grid(f'{L2}/src/head_{d}.pix')


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


def skin_of(g, x, y):
    """the skin tone that belongs at (x,y) when an eye is erased: blush/shade neighbours -> s"""
    return 's'


def expr(g, d, e):
    g = g.copy()
    if e == 'calm' or d not in FRONT: return g
    H, W = g.shape
    E = eyes(g)
    mo = mouth_of(d, W)
    cx = (W - 1) / 2
    for ey in E:
        x0, x1, y0, y1 = ey['x0'], ey['x1'], ey['y0'], ey['y1']
        yl = y0 - 1                                         # lash row
        inner_left = (x0 + x1) / 2 > cx if d in ('S',) else None
        # which side is the inner (nose-side) corner: toward the face centre
        fx = np.mean([q['x0'] + q['x1'] for q in E]) / 2 if len(E) > 1 else (x1 + 2 if d in ('E', 'SE', 'S') else x0 - 2)
        inner = x1 if (x0 + x1) / 2 < fx else x0
        outer = x0 if inner == x1 else x1
        step = 1 if inner == x1 else -1
        def clear_eye():
            for y in range(y0, y1 + 1):
                for x in range(x0, x1 + 1):
                    if g[y, x] in 'eEw': g[y, x] = 's'
        if e == 'glare':
            for x in range(x0, x1 + 1):                             # heavy lid over the top iris row ...
                if x != outer and g[y0, x] in 'eEw': g[y0, x] = 'K'
            if y0 + 1 <= y1: g[y0 + 1, inner] = 'K'                 # ... slanting down to the nose
            if yl - 1 >= 0 and g[yl - 1, outer] in 'hHmsS': pass
            g[yl, outer] = 'K'
        elif e == 'wide':
            for x in range(x0, x1 + 1):
                if g[yl - 1, x] in 'hHJmsS': g[yl - 1, x] = 'K'
                if g[yl, x] == 'K': g[yl, x] = 'e'
            # keep the glint in the top iris row
            for x in range(x0, x1 + 1):
                if g[y0, x] == 'w': g[y0, x] = 'e'; g[yl, x] = 'w'
        elif e == 'kiai':
            g[y0, inner] = 'K'; g[y0, inner - step] = 'K'
            for x in range(x0, x1 + 1):
                if g[y1, x] in 'eE': g[y1, x] = 'K'
        elif e in ('squint', 'smile', 'squeeze'):
            clear_eye()
            for x in range(x0, x1 + 1):
                if g[yl, x] == 'K': g[yl, x] = 's'
            w = x1 - x0 + 1
            if e == 'squint':                                   # heavy flat lid line, slight droop outward
                for x in range(x0, x1 + 1): g[y0, x] = 'K'
                g[y0 + 1, outer] = 'K'
            elif e == 'smile':                                  # ^ ^ closed happy arcs
                for x in range(x0 + 1, x1): g[y0, x] = 'K'
                g[y0 + 1, x0] = 'K'; g[y0 + 1, x1] = 'K'
            else:                                               # > <  squeezed shut
                mid = y0 + 1
                pts = [(outer, y0), (outer + step, y0), (inner, mid), (outer + step, mid + 1), (outer, mid + 1)] if w >= 3 else \
                      [(outer, y0), (inner, mid), (outer, mid + 1)]
                if w >= 4: pts += [(inner - step, mid)]
                for x, y in pts: g[y, x] = 'K'
    if mo:
        x, y, w = mo
        if e in ('glare',):
            for k in range(-1, w + 1):
                if g[y, x + k] in 'sS': g[y, x + k] = 'm'
        elif e == 'wide':
            g[y, x] = 'K'
            if w > 1: g[y, x + 1] = 'K'
            if g[y + 1, x] in 'sm': g[y + 1, x] = 'v'
        elif e in ('kiai',):                                     # small open shout: K lip + red_0 mouth
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
    """1 px tilt: the half right of the centre moves down t px (t=-1: up). Rows stay whole-pixel."""
    if t == 0: return g
    H, W = g.shape
    out = np.full((H + 1, W), '.', dtype=g.dtype)
    c = W // 2
    for x in range(W):
        dy = (1 if t > 0 else 0) if x >= c else (0 if t > 0 else 1)
        out[dy:dy + H, x] = g[:, x]
    # close the seam: where the shifted column leaves an outline step, copy the neighbour outline
    return out


def head(d, e='calm', t=0):
    return tilt(expr(base(d), d, e), t)


def main():
    os.makedirs(L2, exist_ok=True)
    info = {}
    sheet = []
    for d in ['S', 'SE', 'E', 'NE', 'N', 'NW', 'W', 'SW']:
        g = base(d)
        save(to_rgba(g), f'{L2}/head_{d}.png')
        write_grid(g, f'{L2}/head_{d}.pix', f'lock2 head v2 {d} (built by tools/hybrid/h3/heads.py)')
        br = BOW_ROWS.get(d, BOW_ROWS.get(MIRROR.get(d, ''), 7))
        bow = g.copy(); bow[br + 1:] = '.'
        save(to_rgba(bow[:br + 1]), f'{L2}/bow_{d}.png')
        for t in (1, -1):
            save(to_rgba(tilt(g, t)), f'{L2}/head_{d}_tilt{t:+d}.png')
        row = [to_rgba(g)]
        if d in FRONT:
            for e in EXPRS[1:]:
                ge = expr(g, d, e)
                save(to_rgba(ge), f'{L2}/head_{d}_{e}.png'); row.append(to_rgba(ge))
        hair = np.isin(g, list('hHJ')).sum()
        info[d] = dict(size=[int(g.shape[1]), int(g.shape[0])], chin_row=int(g.shape[0] - 1), cx=(g.shape[1] - 1) / 2,
                       bow_rows=br, eyes=eyes(g) if d in FRONT else [], mouth=mouth_of(d, g.shape[1]),
                       hair_share={c: round(float((g == c).sum()) / hair, 3) for c in 'hHJ'},
                       mirrored_from=MIRROR.get(d))
        sheet.append((d, row))
    json.dump(dict(
        how_to_use='Paste whole stamps at integer offsets, never scale. Row 0 = bow top; all heads 24 wide, centre col 11.5. '
                   'Align heads by their LAST row (chin / nape) on the body neck row. SINK (squash) = place the head 1-2 rows '
                   'lower and let the collar layer paint OVER the jaw (h3 compositor collar_over). TILT = head_<D>_tilt+1/-1 '
                   '(1 row taller). Bow lag = bow_<D>.png pasted 1-2 px off after the head. Expressions only on S SE E SW W.',
        exprs=EXPRS, dirs=info), open(f'{L2}/heads.json', 'w'), indent=1)
    # review sheet: one row per direction
    from PIL import Image, ImageDraw
    z = 6; cw, chh = 26 * z, 32 * z
    im = Image.new('RGB', (cw * 8 + 60, chh * 8), (36, 32, 44)); dr = ImageDraw.Draw(im)
    for r, (d, row) in enumerate(sheet):
        dr.text((4, r * chh + 4), d, fill=(230, 230, 230))
        for k, a in enumerate(row):
            sub = strip([a], z=z)
            im.paste(sub, (60 + k * cw, r * chh))
    im.save(f'{L2}/lock2_sheet_x6.png')
    print('wrote', L2, {d: info[d]['size'] for d in info})


if __name__ == '__main__':
    main()
