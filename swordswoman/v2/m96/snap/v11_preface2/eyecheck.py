"""eyecheck.py: verify the M96 EYE SPEC (eye_spec.json) on a master, head stamp or animation frame.
  eyecheck.py FRAME.txt VIEW [EXPR|auto] [--anchor v2/m96/heads/anchor.json] [--json]
  exit 0 = eyes match the spec template exactly (lash, iris h/g/L, 1 catchlight top-left, sclera only per template), 1 = fixes printed.
Module: check(grid, view, expr='auto', anchor=None) -> (metrics, fixes);  qc_hook(grid, view, ref_grid, pal_path) -> (metrics, fixes)
Animator hooks (one line each, documented in EYE_SPEC.md):
  lint_style.py / ff_redraw.validate:  sys.path.insert(0, '/Users/waylonhuang/Documents/other/pixelart/swordswoman/v2/m96/tools'); import eyecheck; fx += eyecheck.check(grid, view)[1]
"""
import sys, os, json
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
SPEC = json.load(open(os.path.join(HERE, '..', 'eye_spec.json')))
SKIN = set('sSmk'); IRIS = set('hgL'); BC = SPEC.get('brow', {}).get('char', 'h')   # brow colour (templates write 'h')
EXPRS = [e for e in SPEC['front_left'] if not e.startswith('_')]


def _tmpl(kind, expr):
    import eyetmpl as E
    return E.kind_tmpl(kind, expr)


def _match(g, t, x0, y0):
    """exact template match; '.' = skin; '_' = don't care; '@' = W. returns (#mismatch, #checked)"""
    bad = n = 0
    for j, r in enumerate(t):
        for i, c in enumerate(r):
            if c == '_': continue
            y, x = y0 + j, x0 + i
            if not (0 <= y < len(g) and 0 <= x < len(g[0])): bad += 1; continue
            b = g[y][x]; n += 1
            if c == '.': bad += b not in SKIN
            elif c == '@': bad += b != 'W'
            elif c == 'm' and j == 0: bad += b not in 'mhHKsS'   # brow is optional (fringe may hide it; orphan guard may drop it)
            elif c == 'm': bad += b != 'm'
            else: bad += b != c
    return bad, n


def _brow(kind, expr):
    import eyetmpl as E
    return E.brow_tmpl(kind, expr)


def _match_brow(g, kind, e, x0, y0):
    """brow template (FACE_SPEC) rows lash-4..lash-2 = eye origin y0-3..y0-1: 'h' must be h, '.' must be skin (not h). -> (#bad, #h present)"""
    t = _brow(kind, e); bad = hp = 0; y0 -= len(t)
    for j, r in enumerate(t):
        for i, c in enumerate(r):
            y, x = y0 + j, x0 + i
            if not (0 <= y < len(g) and 0 <= x < len(g[0])): bad += 1; continue
            b = g[y][x]
            if c == 'h': bad += b != BC; hp += b == BC
            elif b == BC or b not in SKIN: bad += 1
    return bad, hp


def _search(g, kind, exprs, win):
    best = None
    x0r, y0r = win
    for e in exprs:
        t = _tmpl(kind, e)
        for y in y0r:
            for x in x0r:
                b, n = _match(g, t, x, y)
                if 'brow' in SPEC: b += _match_brow(g, kind, e, x, y)[0]
                if best is None or b < best[0] or (b == best[0] and n > best[3]): best = (b, x, y, n, e)
    return best


def check(g, view, expr='auto', anchor=None, ref_eye_dy=None):
    g = [''.join(r) for r in g]; H, W = len(g), len(g[0]); fixes = []; met = dict(view=view, eyes=[])
    kinds = SPEC['kinds_by_view'].get(view, [])
    if not kinds: return met, fixes
    exprs = EXPRS if expr in (None, 'auto') else [SPEC['aliases'].get(expr, expr)]
    pos = None
    if anchor:
        a = json.load(open(anchor)) if isinstance(anchor, str) else anchor
        pos = a.get('views', {}).get(view, {}).get('eyes')
    found = []
    for k, kind in enumerate(kinds):
        if pos and k < len(pos):
            win = (range(pos[k]['x0'] - 0, pos[k]['x0'] + 1), range(pos[k]['y0'], pos[k]['y0'] + 1))
        else:
            win = (range(0, W - 3), range(0, int(H * 0.6)))
        # choose expression jointly: first eye picks, others must use the same
        b = _search(g, kind, exprs if not found else [found[0][4]], win)
        found.append(b)
    ex = found[0][4]
    for kind, b in zip(kinds, found):
        bad, x, y, n, e = b
        bb, hp = _match_brow(g, kind, e, x, y) if 'brow' in SPEC else (0, 0)
        met['eyes'].append(dict(kind=kind, x0=x, y0=y, expr=e, mismatch=bad - bb, brow_px=hp, brow_bad=bb))
        if 'brow' in SPEC and (bb or hp < 3):
            fixes.append('FACESPEC %s brow (%s, expr %s) above eye origin (%d,%d): %d px differ / %d h px present; template rows lash-4..lash-2 = %s (h = dark hair ramp only, "." = skin; the row right above the lash stays skin)' % (kind, view, e, x, y, bb, hp, '/'.join(_brow(kind, e))))
        bad -= bb
        if bad > 0:
            t = _tmpl(kind, e)
            fixes.append('EYESPEC %s eye (%s, expr %s) at template origin (%d,%d): %d px differ from the spec template %s (rows from the brow row; "." = skin, "@" = W catchlight)' % (kind, view, e, x, y, bad, '/'.join(t)))
    met['expr'] = ex
    if pos is not None:   # nose (FACE_SPEC): anchor pixels must be exact
        nz = a.get('views', {}).get(view, {}).get('nose', [])
        nb = [(x, y, c) for x, y, c in nz if g[y][x] != c]
        met['nose_bad'] = len(nb)
        if nb: fixes.append('FACESPEC nose (%s): %d px differ from the anchor nose %s' % (view, len(nb), nz))
    # stray highlights: W inside the head region that is not in a template '@'/'W'
    allowed = set()
    for kind, b in zip(kinds, found):
        t = _tmpl(kind, b[4])
        for j, r in enumerate(t):
            for i, c in enumerate(r):
                if c in '@W': allowed.add((b[1] + i, b[2] + j))
    ys = [b[2] for b in found]; y_lo, y_hi = min(ys) - 3, max(ys) + 9
    xs = [b[1] for b in found]; x_lo, x_hi = min(xs) - 4, max(xs) + 10
    stray = [(x, y) for y in range(max(0, y_lo), min(H, y_hi)) for x in range(max(0, x_lo), min(W, x_hi)) if g[y][x] == 'W' and (x, y) not in allowed]
    if stray: fixes.append('EYESPEC stray highlight W px near the eyes (catchlight must be exactly 1 px, top-left of each iris): %s' % stray[:8])
    met['catchlights'] = len([p for p in allowed if g[p[1]][p[0]] == 'W'])
    if ref_eye_dy is not None and anchor is None:
        pass
    return met, fixes


def _crown(g, pal_path):
    sys.path.insert(0, '/Users/waylonhuang/Documents/other/pixelart/swordswoman/v2/qc'); sys.path.insert(0, '/Users/waylonhuang/Documents/other/pixelart/swordswoman/v2/anim_cut/tools')
    import qc_gate as QC, colorcheck as CC
    return QC.parts([''.join(r) for r in g], CC.load(pal_path))['crown']


def qc_hook(grid, view, ref_grid, pal_path):
    """called by v2/qc/qc_gate.py: spec template match (any expression) + eye height vs the reference grid (same view master)"""
    met, fixes = check(grid, view, 'auto')
    if met.get('eyes') and ref_grid is not None:
        try:
            rm, _ = check(ref_grid, view, 'auto')
            if rm.get('eyes'):
                d0 = met['eyes'][0]['y0'] - _crown(grid, pal_path); d1 = rm['eyes'][0]['y0'] - _crown(ref_grid, pal_path)
                met['eye_dy'] = d0
                if abs(d0 - d1) > 0: fixes.append('EYESPEC eye row %d below the crown vs %d in the reference (must be identical)' % (d0, d1))
        except Exception as ex:
            met['ref_err'] = str(ex)
    return met, fixes


if __name__ == '__main__':
    a = sys.argv[1:]; js = '--json' in a; a = [t for t in a if t != '--json']
    anc = None
    if '--anchor' in a: i = a.index('--anchor'); anc = a[i + 1]; del a[i:i + 2]
    g = [l.rstrip('\n') for l in open(a[0]) if l.strip() and not l.startswith(';')]
    org = [l.split()[2:4] for l in open(a[0]) if l.startswith('; origin')]
    if org:   # head stamp: paste into the 128 cell at its origin and check at the anchor positions
        ox, oy = map(int, org[0]); cell = [['.'] * 128 for _ in range(128)]
        for j, r in enumerate(g):
            for i, c in enumerate(r):
                if c != '.': cell[oy + j][ox + i] = c
        g = [''.join(r) for r in cell]; anc = anc or os.path.join(HERE, '..', 'heads', 'anchor.json')
    m, fx = check(g, a[1], a[2] if len(a) > 2 else 'auto', anc)
    if js: print(json.dumps(dict(metrics=m, fixes=fx)))
    else:
        print(('OK   ' if not fx else 'FAIL ') + a[0], m.get('expr'), [(e['kind'], e['x0'], e['y0'], e['mismatch']) for e in m.get('eyes', [])])
        for f in fx: print('   ', f)
    sys.exit(1 if fx else 0)
