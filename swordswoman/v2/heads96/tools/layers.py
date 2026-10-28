"""layers.py: build the layered-head library v2/heads96/layers/<V>/ from labels.txt + master + m96 stamps.
Files (all on the view BOX canvas, '; origin X0 Y0' = master coords of canvas (0,0), '.' = transparent):
  base_neutral.txt          b pixels + face mask filled with blank skin (features removed)
  face/<expr>.txt           the approved m96 stamp pixels on the face mask (identical copies; never edited)
  <P>_rest.txt              P in B l r w t (rest = the master pixels)
  draft/<P>_<state>.txt     procedural sway drafts; draft/base_tilt{L,R}.txt procedural tilt drafts
  approved/                 the accepted variant set (written by accept.py; manifest.json with sha1 per file)
Run: layers.py [VIEWS]"""
import sys, os, json, math, hashlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cm import *
import decompose as D
HAIR = set('KhHgL'); SKIN = set('sSmk'); PARTS = ['B', 'l', 'r', 'w', 't']
LD = f'{ROOT}/heads96/layers'
def grid_of(lab, G, X0, Y0, want):
    return [''.join(G[Y0 + y][X0 + x] if c in want else '.' for x, c in enumerate(r)) for y, r in enumerate(lab)]
def feature_boxes(v):
    a = json.load(open(f'{ROOT}/m96/heads/anchor.json'))['views'][v]; M = set()
    for e in a.get('eyes', []):
        w = 6 if e['kind'] != 'far' else 4
        M |= {(x, y) for x in range(e['x0'] - 1, e['x0'] + w + 1) for y in range(e['y0'] - 3, e['y0'] + 6)}
    if a.get('mouth'): mx, my = a['mouth']; M |= {(x, y) for x in range(mx, mx + 4) for y in range(my, my + 3)}
    for x, y, c in a.get('nose', []): M.add((x, y))
    for bx, by, k in a.get('blush', []): M |= {(x, y) for x in range(bx, bx + 4) for y in range(by, by + 2)}
    for x, y in a.get('ne_lash', []): M.add((x, y))
    return M
def blank_face(v, base, lab, X0, Y0):
    """replace face-mask pixels by skin from the nearest non-mask skin pixel of the base (keeps the S shading under the bangs)"""
    FB = feature_boxes(v); B = [list(r) for r in base]; H, W = len(B), len(B[0])
    fm = [(x, y) for y, r in enumerate(lab) for x, c in enumerate(r) if c == 'f']
    src = [(x, y) for y, r in enumerate(lab) for x, c in enumerate(r) if c == 'b' and base[y][x] in 'sS']
    for x, y in fm:
        c = base[y][x]
        if c in HAIR - {'K'} and (X0 + x, Y0 + y) not in FB: continue   # bangs strand inside the rect: keep
        if c == 'K' and (X0 + x, Y0 + y) not in FB: continue
        best = min(src, key=lambda p: (abs(p[0] - x) + 2 * abs(p[1] - y), p[1] != y)) if src else None
        B[y][x] = base[best[1]][best[0]] if best else 's'
        if B[y][x] not in 'sS': B[y][x] = 's'
    return [''.join(r) for r in B]
# ---------- procedural drafts ----------
def bbox(g):
    p = [(x, y) for y, r in enumerate(g) for x, c in enumerate(r) if c != '.']
    return (min(q[0] for q in p), min(q[1] for q in p), max(q[0] for q in p), max(q[1] for q in p)) if p else None
def shift_rows(g, fn):
    """row y moves by fn(y) px horizontally"""
    H, W = len(g), len(g[0]); out = [['.'] * W for _ in range(H)]
    for y, r in enumerate(g):
        s = fn(y)
        for x, c in enumerate(r):
            if c != '.' and 0 <= x + s < W: out[y][x + s] = c
    return [''.join(r) for r in out]
def shift_cols(g, fn):
    H, W = len(g), len(g[0]); out = [['.'] * W for _ in range(H)]
    for y, r in enumerate(g):
        for x, c in enumerate(r):
            s = fn(x, y)
            if c != '.' and 0 <= y + s < H: out[y + s][x] = c
    return [''.join(r) for r in out]
def translate(g, dx, dy):
    H, W = len(g), len(g[0]); out = [['.'] * W for _ in range(H)]
    for y, r in enumerate(g):
        for x, c in enumerate(r):
            if c != '.' and 0 <= x + dx < W and 0 <= y + dy < H: out[y + dy][x + dx] = c
    return [''.join(r) for r in out]
def stretch(g, y0, y1, n):
    """hang/drop: duplicate n rows evenly between y0..y1 (rows below move down); n<0 removes rows (lift)"""
    rows = list(g); H = len(rows)
    if n == 0 or y1 <= y0: return rows
    seg = list(range(y0 + 1, y1 + 1)); k = abs(n); picks = [seg[int((i + 1) * len(seg) / (k + 1))] for i in range(k)] if seg else []
    if n > 0:
        for p in sorted(picks, reverse=True): rows.insert(p, rows[p])
        rows = rows[:H]
    else:
        for p in sorted(set(picks), reverse=True): del rows[p]
        rows = rows + ['.' * len(g[0])] * (H - len(rows))
    return rows
def sway(g, part, state, view):
    """procedural sway draft: hair hangs from its top (attach) row; lag = tip trails 1-2 px; lift = 1 px shorter/up; drop = 1 px longer"""
    bb = bbox(g)
    if not bb: return g
    x0, y0, x1, y1 = bb; h = max(1, y1 - y0)
    amp = {'B': 1, 'l': 2, 'r': 2, 't': 2, 'w': 1}[part]
    if part == 'w':   # bow: loops flutter -> lag = whole bow 1 px; lift = up 1; drop = down 1
        return {'rest': g, 'lagL': translate(g, -1, 0), 'lagR': translate(g, 1, 0), 'lift': translate(g, 0, -1), 'drop': translate(g, 0, 1)}[state]
    if state == 'rest': return g
    if state in ('lagL', 'lagR'):
        d = -1 if state == 'lagL' else 1
        return shift_rows(g, lambda y: 0 if y < y0 else d * int(math.floor(amp * ((y - y0) / h) ** 1.3 + 0.5)))
    if state == 'lift': return stretch(g, y0, y1, -1 if part != 'B' else -1)
    if state == 'drop': return stretch(g, y0, y1, 1)
STATES = ['rest', 'lagL', 'lagR', 'lift', 'drop']
TILT_DEG = 8
def tilt_base(base, lab, d, yc):
    """procedural tilt draft: rows above the face centre slide toward d, rows below slide opposite (shear ~8 deg).
    face-mask (f) rows near yc stay (the face layer is never moved by tilt beyond the anchor offset)"""
    t = math.tan(math.radians(TILT_DEG))
    return shift_rows(base, lambda y: int(round((yc - y) * t)) * d)
def build(v):
    G, _ = load(f'{ROOT}/m96/masters/EC0_{v}_96.txt'); lab, m = load(f'{LD}/{v}/labels.txt'); X0, Y0 = map(int, m['origin'])
    od = f'{LD}/{v}'; os.makedirs(od + '/face', exist_ok=True); os.makedirs(od + '/draft', exist_ok=True)
    meta = {'origin': [X0, Y0], 'view': [v]}
    base = grid_of(lab, G, X0, Y0, 'bf')
    save(f'{od}/base_master.txt', base, meta)
    bn = blank_face(v, base, lab, X0, Y0); save(f'{od}/base_neutral.txt', bn, meta)
    hd = f'{ROOT}/m96/heads'; nst = 0
    for fn in sorted(os.listdir(hd)):
        if not (fn.startswith(v + '_') and fn.endswith('.txt')): continue
        st, sm = load(f'{hd}/{fn}'); sx, sy = map(int, sm['origin']); e = fn[len(v) + 1:-4]
        Gx = [list(r) for r in G]
        for y, r in enumerate(st):
            for x, c in enumerate(r):
                if c != '.': Gx[sy + y][sx + x] = c
        fl = [''.join(Gx[Y0 + y][X0 + x] if c == 'f' else '.' for x, c in enumerate(r)) for y, r in enumerate(lab)]
        save(f'{od}/face/{e}.txt', fl, dict(meta, expr=[e], src=[fn])); nst += 1
    for p in PARTS:
        g = grid_of(lab, G, X0, Y0, p)
        save(f'{od}/{p}_rest.txt', g, meta)
        for s in STATES: save(f'{od}/draft/{p}_{s}.txt', sway(g, p, s, v), dict(meta, part=[p], state=[s]))
    fm = [y for y, r in enumerate(lab) for c in r if c == 'f']
    yc = (min(fm) + max(fm)) // 2 if fm else len(lab) // 2
    for d, nm in ((-1, 'L'), (1, 'R')): save(f'{od}/draft/base_tilt{nm}.txt', tilt_base(bn, lab, d, yc), dict(meta, tilt=[d], yc=[yc]))
    print(v, 'faces', nst, 'yc', yc)
if __name__ == '__main__':
    for v in (sys.argv[1:] or ['S', 'SE', 'E', 'NE', 'N']): build(v)
