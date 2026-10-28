"""stamp.py (face round 2: cat-eye wing + oval blush patches): build expression faces from the eye_spec + heads/anchor.json (pure python).
  stamp.py face MASTER.txt VIEW EXPR OUT.txt          -> full master grid with that expression
  stamp.py heads MASTER_DIR OUT_DIR                   -> heads/<V>_<expr>.txt for S SE E NE (N: neutral only) + anchor stamp boxes
Clears the anchor's eye/mouth boxes to skin (eye/hair-ramp chars only, never outline/transparent), then draws the templates."""
import sys, os, json
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import eyetmpl as ET
SPEC = ET.SPEC; ANC = os.path.join(HERE, '..', 'heads', 'anchor.json')
SK = set('sSmk')
EXPRS = [e for e in SPEC['front_left'] if not e.startswith('_')]


def rd(p): return [list(l.rstrip('\n')) for l in open(p) if l.strip() and not l.startswith(';')]


def is_edge(g, x, y):
    return any(not (0 <= y + b < len(g) and 0 <= x + a < len(g[0])) or g[y + b][x + a] == '.' for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1)))


def put(g, t, x0, y0, clear_rows=()):
    for j, r in enumerate(t):
        for i, c in enumerate(r):
            y, x = y0 + j, x0 + i
            if c == '_' or not (0 <= y < len(g) and 0 <= x < len(g[0])): continue
            b = g[y][x]
            if b == '.' or is_edge(g, x, y): continue
            if c == ',':
                if b in 'sSmkKhgLWHDd': g[y][x] = 's'
                continue
            if c == '.':
                if j == 0 and b not in 'mk': continue   # brow row: only skin-ramp marks are cleared, never the fringe
                if b not in 'sS': g[y][x] = 's'
                continue
            if c == 'm' and j == 0 and b not in SK: continue   # brow only on skin
            g[y][x] = 'W' if c == '@' else c


HAIR = set('HhgL')


def brows(g, ey, e):
    """brow window (rows lash-4..lash-2 over the brow cols: hair -> skin; lash-4 -> S) then the 2-row h brow template"""
    t = ET.brow_tmpl(ey['kind'], e); w = len(t[0]); y0 = ey['y0'] - len(t); x0 = ey['x0']
    top = min(j for j, r in enumerate(t) if 'h' in r)
    sh = 's'   # face round r2: plain skin above the brow (an S row merged brow + bang edge at 1x)
    cols = range(-1, 4) if w == 4 else range(0, 6)
    for i in cols:
        x = x0 + i
        for y, fill in [(y0 + top - 1, sh)] + [(y0 + j, 's') for j in range(top, len(t))]:
            b = g[y][x]
            if b == '.' or is_edge(g, x, y): continue
            if b in HAIR or b in 'mkK': g[y][x] = fill
    for j, r in enumerate(t):
        for i, c in enumerate(r):
            x, y = x0 + i, y0 + j
            if c == '.' or is_edge(g, x, y) or g[y][x] in 'K.': continue
            g[y][x] = SPEC['brow'].get('char', 'h')   # templates write 'h' = the brow char


def face(g, view, expr, anc=None):
    a = (anc or json.load(open(ANC)))['views'][view]; e = ET.expr_key(expr); g = [r[:] for r in g]
    for ey in a['eyes']:
        brows(g, ey, e)
    for ey in a['eyes']:
        t = ET.kind_tmpl(ey['kind'], e); w = len(t[0])
        put(g, ['_' * w] + [''.join('_' if c == '_' else ',' for c in r) for r in t[1:]], ey['x0'], ey['y0'])     # clear lash..iris rows to plain skin ('_' = keep)
        put(g, t, ey['x0'], ey['y0'])
        # cat-eye wing (face round 2): restore the master pixel under every wing position, then draw this expression's flick
        bg = ey.get('wing_bg', {})
        for dx, dy in ET.all_wings(ey['kind']):
            k = '%d,%d' % (dx, dy)
            if k in bg: g[ey['y0'] + dy][ey['x0'] + dx] = bg[k]
        for dx, dy, wc in ET.wing_px(ey['kind'], e):
            x, y = ey['x0'] + dx, ey['y0'] + dy
            if g[y][x] != '.': g[y][x] = wc
    if a.get('mouth'):
        mx, my = a['mouth']; put(g, ['....'] * 3, mx, my); put(g, SPEC['mouth'][e], mx, my)
    for bx, by, kind in a.get('blush', []):   # face round 2: oval k patches (eye_spec blush[kind] templates)
        for j, r in enumerate(ET.blush_tmpl(kind, e)):
            for i, c in enumerate(r):
                if c == 'k' and g[by + j][bx + i] in 'sSk': g[by + j][bx + i] = 'k'
    # orphan guard (qc S4): brow m / blush k marks that ended up as single pixels are dropped back to skin
    marks = [(ey['x0'] + i, ey['y0'] + j) for ey in a['eyes'] for i in range(-2, 8) for j in range(-5, 1)] + [(bx + i, by + j) for bx, by, n_ in a.get('blush', []) for i in range(-1, 5) for j in (0, 1, 2)]
    for (x, y) in marks:
        if 0 <= y < len(g) and 0 <= x < len(g[0]) and g[y][x] in 'mkS':
            if not any(g[y + b][x + a_] == g[y][x] for a_ in (-1, 0, 1) for b in (-1, 0, 1) if (a_ or b) and 0 <= y + b < len(g) and 0 <= x + a_ < len(g[0])):
                g[y][x] = 's'
    from collections import Counter
    marks += [(ey['x0'] + i, ey['y0'] + j) for ey in a['eyes'] for i in (-2, -1) for j in range(0, 6)]   # eye round: skin px boxed in by the outer lash flicks + side hair
    for (x, y) in marks:   # skin px left alone inside the hair by the window/guard -> the surrounding hair char
        if 0 < y < len(g) - 1 and 0 < x < len(g[0]) - 1 and g[y][x] in 'sS':
            nb = [g[y + b][x + a_] for a_ in (-1, 0, 1) for b in (-1, 0, 1) if a_ or b]
            if g[y][x] in nb: continue
            sk = [c for c in nb if c in 'sS']; hr = [c for c in nb if c in HAIR]
            if sk: g[y][x] = Counter(sk).most_common(1)[0][0]
            elif hr: g[y][x] = Counter(hr).most_common(1)[0][0]
    for x, y, c in a.get('nose', []): g[y][x] = c
    for k, (x, y) in enumerate(a.get('ne_lash', [])):
        if k < SPEC['ne_lash'][e] and g[y][x] == '.': g[y][x] = 'K'
    return g


def head_box(g, view):
    """full-head stamp box: rows from the top of the figure to the chin+1, cols spanning opaque px in those rows (+1)"""
    a = json.load(open(ANC))['views'][view]; y1 = a['chin'] + 2
    ys = [y for y in range(len(g)) if any(c != '.' for c in g[y])]; y0 = ys[0]
    xs = [x for y in range(y0, y1) for x, c in enumerate(g[y]) if c != '.']
    return [min(xs), y0, max(xs) + 1, y1]


if __name__ == '__main__':
    a = sys.argv[1:]
    if a[0] == 'face':
        g = face(rd(a[1]), a[2], a[3]); open(a[4], 'w').write('\n'.join(''.join(r) for r in g) + '\n')
    elif a[0] == 'heads':
        md, od = a[1], a[2]; os.makedirs(od, exist_ok=True); anc = json.load(open(ANC))
        for v in ['S', 'SE', 'E', 'NE', 'N']:
            m = rd(f'{md}/EC0_{v}_96.txt'); box = head_box(m, v); anc['views'][v]['stamp'] = box
            for e in (EXPRS if v != 'N' else ['neutral']):
                g = face(m, v, e, anc); x0, y0, x1, y1 = box
                rows = [''.join(r[x0:x1]) for r in g[y0:y1]]
                open(f'{od}/{v}_{e}.txt', 'w').write('; origin %d %d\n; view %s\n; expr %s\n' % (x0, y0, v, e) + '\n'.join(rows) + '\n')
        json.dump(anc, open(ANC, 'w'), indent=1)
        print('heads ->', od)
