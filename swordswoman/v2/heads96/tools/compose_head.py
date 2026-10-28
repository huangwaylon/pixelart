"""compose_head.py: composite the LAYERED head (v2/heads96/layers/<V>/) from a per-frame head spec.
spec (dict; the motion strand's frames.json per-frame 'head' block, all keys optional):
  {"expr": "neutral", "tilt": -1|0|1, "nod": -1|0|1, "turn": -1|0|1, "dx": 0, "dy": 0,
   "sec": {"B": state, "l": state, "r": state, "w": state, "t": state}}      state in rest lagL lagR lift drop
  tilt +1 = crown leans to screen right (pre-drawn base_tiltR + part anchor offsets); nod +1 = look down (face layer 1 px down;
  NE/N: knot/bow/tails 1 px up), nod -1 = look up (jaw row below the mouth doubled = chin 1 px lower, face layer unmoved; NE/N bow 1 px down);
  turn +-1 = face layer 1 px toward screen right/left (allowed: S +-1, SE -1, E -1; others ignored). dx/dy = whole-head offset (bob) in px.
API:
  compose_stamp(view, spec) -> (rows, (X0, Y0), info)    head canvas in master coords at rest (dx/dy NOT applied)
  write_stamp(view, spec, path)                          '; origin X0+dx Y0+dy' file = drop-in for frames.json 'stamp'
  head_at(view, old_stamp_head_at, old_stamp_path, spec) -> paste position of the composed stamp for an m96-stamp head_at
  paste(grid, rows, at, prev=None)                       paste; prev=(rows, at) of the previous head clears its stale px
  verify(grid, view, spec, at) -> list of fix strings    face == approved stamp (minus hair occlusion), hair px == sprites
CLI: compose_head.py VIEW 'JSON_SPEC' OUT.txt        |  compose_head.py frames FRAMES.json OUTDIR  (writes cNN_head.txt per frame
     with a 'head' block, sets fr['stamp'] = composed file, fr['head_at'] adjusted; backup FRAMES.json.bak_h96)"""
import sys, os, json, math, hashlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cm import load, save, ROOT
LD = f'{ROOT}/heads96/layers'
SKIN = set('sSmk'); HAIRC = set('hHgL')
ORDER = {'S': 'Bwtbflr', 'SE': 'Bwtbflr', 'E': 'tBwbfl', 'NE': 'Btbfrw', 'N': 'lrBbtw'}
TILT_DEG = 8; STATES = ('rest', 'lagL', 'lagR', 'lift', 'drop')
_cache = {}
def _ld(p):
    if p not in _cache: _cache[p] = load(p)
    return _cache[p]
def lib(view, name):
    """approved/ wins over draft/ over the top level (base_neutral, <P>_rest, face/<e>)"""
    for d in (('artist',) if os.environ.get('H96_ARTIST') else ()) + ('approved', '', 'draft'):
        p = os.path.join(LD, view, d, name + '.txt')
        if os.path.exists(p): return _ld(p)[0], p
    raise FileNotFoundError(f'{view}/{name}')
def meta(view):
    lab, m = _ld(f'{LD}/{view}/labels.txt'); X0, Y0 = map(int, m['origin'])
    fm = [y for y, r in enumerate(lab) for c in r if c == 'f']
    yc = (min(fm) + max(fm)) // 2 if fm else len(lab) // 2
    tops = {}
    for p in 'Bwtlr':
        ys = [y for y, r in enumerate(lab) for c in r if c == p]
        tops[p] = min(ys) if ys else yc
    return lab, X0, Y0, yc, tops
def resolve_expr(view, e):
    for cand in (e, {'smile': 'cheerful', 'squash': 'blink_closed', 'hurt': 'pain'}.get(e, e), 'neutral'):
        if os.path.exists(f'{LD}/{view}/face/{cand}.txt'): return cand
    return 'neutral'
def offsets(view, spec):
    """per-layer (dx, dy) from tilt / nod / turn"""
    lab, X0, Y0, yc, tops = meta(view); t = math.tan(math.radians(TILT_DEG)); d = int(spec.get('tilt', 0))
    off = {p: (int(round((yc - tops[p]) * t)) * d, 0) for p in 'Bwtlr'}
    for p in 'lrB': off[p] = (int(round((yc - max(tops[p], yc)) * t)) * d + (0 if p == 'B' else 0), 0)   # hanging hair attaches at/below the face centre
    nod = int(spec.get('nod', 0)); turn = int(spec.get('turn', 0))
    turn = turn if turn in TURN_OK.get(view, ()) else 0
    fdy = 1 if (nod == 1 and view in ('S', 'SE', 'E')) else 0   # look down: face layer 1 px lower (more crown); look up = jaw stretch (base)
    off['f'] = (turn, fdy); off['b'] = (0, 0)
    if nod and view in ('NE', 'N'):   # back views: the knot/bow + tails tip 1 px up when looking down, down when looking up
        for p in 'wt': off[p] = (off[p][0], off[p][1] - nod)
    return off
TURN_OK = {'S': (-1, 1), 'SE': (-1,), 'E': (-1,)}   # face layer may slide 1 px only where the eyes stay off the cheek outline (eyecheck)
def jaw_row(view):
    a = json.load(open(f'{ROOT}/m96/heads/anchor.json'))['views'][view]; _, X0, Y0, yc, _ = meta(view)
    return a['mouth'][1] + 3 - Y0 if a.get('mouth') else None
def nod_up(base, view):
    """look up: the jaw drops 1 px (the row below the mouth is doubled) so the features sit higher in the face; face layer unchanged"""
    r = jaw_row(view)
    if r is None: return base
    return (base[:r + 1] + base[r:])[:len(base)]
def compose_stamp(view, spec=None):
    spec = spec or {}; lab, X0, Y0, yc, tops = meta(view); H, W = len(lab), len(lab[0])
    tilt = int(spec.get('tilt', 0)); sec = spec.get('sec', {}) or {}
    base, bp = lib(view, {0: 'base_neutral', -1: 'base_tiltL', 1: 'base_tiltR'}[tilt])
    if int(spec.get('nod', 0)) == -1: base = nod_up(base, view)
    e = resolve_expr(view, spec.get('expr', 'neutral')); face, fp = lib(view, 'face/' + e)
    off = offsets(view, spec); out = [['.'] * W for _ in range(H)]; src = {}; owner = {}
    def put(g, dx, dy, tag, cond=None):
        for y, r in enumerate(g):
            for x, c in enumerate(r):
                if c == '.': continue
                X, Y = x + dx, y + dy
                if 0 <= X < W and 0 <= Y < H and (cond is None or cond(X, Y, c)):
                    out[Y][X] = c; owner[(X, Y)] = tag
    used = {'base': bp, 'face': fp}
    for L in ORDER[view]:
        if L == 'b': put(base, 0, 0, 'b')
        elif L == 'f':
            fdx, fdy = off['f']
            # face px land only on skin / blank-face of the base; hair or outline of the base occludes them (bangs over brows)
            put(face, fdx, fdy, 'f', lambda X, Y, c: owner.get((X, Y)) in ('b', 'f') and (out[Y][X] in SKIN or lab[Y][X] == 'f' and out[Y][X] not in HAIRC | {'K'}) or (fdx, fdy) == (0, 0))
        else:
            st = sec.get(L, 'rest'); st = st if st in STATES else 'rest'
            try: g, p = lib(view, f'{L}_{st}') if st != 'rest' else lib(view, f'{L}_rest')
            except FileNotFoundError: g, p = lib(view, f'{L}_rest')
            if not any(c != '.' for r in g for c in r): continue
            used[L] = p; put(g, off[L][0], off[L][1], L)
    # seam re-outline: an exposed hole (px inside the rest silhouette, now empty) beside a non-K head px gets a K outline px
    rest = rest_union(view)
    for (X, Y) in rest:
        if out[Y][X] != '.': continue
        nb = [out[Y + j][X + i] for i, j in ((1, 0), (-1, 0), (0, 1), (0, -1)) if 0 <= X + i < W and 0 <= Y + j < H]
        if any(c not in '.K' for c in nb): out[Y][X] = 'K'; owner[(X, Y)] = 'seam'
    rows = [''.join(r) for r in out]
    return rows, (X0, Y0), dict(expr=e, used=used, off=off, owner=owner)
_ru = {}
def rest_union(view):
    if view not in _ru:
        lab = meta(view)[0]; _ru[view] = {(x, y) for y, r in enumerate(lab) for x, c in enumerate(r) if c != '.'}
    return _ru[view]
def write_stamp(view, spec, path):
    rows, (X0, Y0), info = compose_stamp(view, spec)
    m = {'origin': [X0 + int(spec.get('dx', 0)), Y0 + int(spec.get('dy', 0))], 'view': [view], 'expr': [info['expr']],
         'head_spec': [json.dumps(spec, separators=(',', ':'))], 'layered': ['heads96']}
    save(path, rows, m); return path
def head_at(view, old_at, old_stamp_path, spec=None):
    """frames.json head_at is the paste pos of the m96 stamp (origin O); the composed canvas origin is (X0,Y0): shift by (X0-Ox, Y0-Oy)"""
    o = list(map(int, load(old_stamp_path)[1]['origin'])); _, X0, Y0, _, _ = meta(view); spec = spec or {}
    return [old_at[0] + X0 - o[0] + int(spec.get('dx', 0)), old_at[1] + Y0 - o[1] + int(spec.get('dy', 0))]
def paste(grid, rows, at, prev=None):
    G = [list(r) for r in grid]; H, W = len(G), len(G[0])
    if prev:   # clear the previous head's px that the new head does not cover (fill from the nearest non-head px in the row)
        pr, pa = prev; newc = {(at[0] + x, at[1] + y) for y, r in enumerate(rows) for x, c in enumerate(r) if c != '.'}
        oldc = {(pa[0] + x, pa[1] + y) for y, r in enumerate(pr) for x, c in enumerate(r) if c != '.'}
        for X, Y in sorted(oldc - newc):
            if not (0 <= X < W and 0 <= Y < H): continue
            fill = '.'
            for k in range(1, 4):
                for X2 in (X - k, X + k):
                    if 0 <= X2 < W and (X2, Y) not in oldc and G[Y][X2] != '.': fill = G[Y][X2]; break
                if fill != '.': break
            G[Y][X] = fill
    for y, r in enumerate(rows):
        for x, c in enumerate(r):
            if c != '.' and 0 <= at[1] + y < H and 0 <= at[0] + x < W: G[at[1] + y][at[0] + x] = c
    return [''.join(r) for r in G]
def verify(grid, view, spec, at, occl_ok=True):
    """layered-head QC: (1) every face-layer px of the approved stamp face/<expr> appears unchanged at its offset unless the base/hair
    occludes it in the composite (identical eyes/highlights/colours); (2) every head px in the frame equals the composite from the
    approved sprites (hair from approved sway states only), body/arm occlusion allowed when occl_ok."""
    rows, _, info = compose_stamp(view, spec); fx = []; H, W = len(grid), len(grid[0])
    face = lib(view, 'face/' + info['expr'])[0]; fdx, fdy = info['off']['f']; bad = []
    for y, r in enumerate(face):
        for x, c in enumerate(r):
            if c == '.': continue
            X, Y = x + fdx, y + fdy
            if info['owner'].get((X, Y)) != 'f': continue      # occluded by hair/outline in the composite (by design)
            gx, gy = at[0] + X, at[1] + Y
            if 0 <= gx < W and 0 <= gy < H and grid[gy][gx] != c: bad.append((gx, gy, c, grid[gy][gx]))
    if bad: fx.append('LAYERFACE %d face-layer px differ from the approved stamp %s_%s (offset %+d,%+d): %s; restore them' % (len(bad), view, info['expr'], fdx, fdy, bad[:8]))
    hb = []
    for y, r in enumerate(rows):
        for x, c in enumerate(r):
            if c == '.' or info['owner'].get((x, y)) == 'f': continue
            gx, gy = at[0] + x, at[1] + y
            if not (0 <= gx < W and 0 <= gy < H): continue
            g = grid[gy][gx]
            if g == c: continue
            if occl_ok and g not in HAIRC | SKIN | {'K', '.'} and c in HAIRC | {'K'}: continue   # arm/blade/dress in front
            hb.append((gx, gy, c, g))
    if len(hb) > 2: fx.append('LAYERHAIR %d head px differ from the approved layer sprites (%s): %s; repaste the composed head' % (len(hb), ','.join('%s:%s' % (k, os.path.basename(v)[:-4]) for k, v in info['used'].items()), hb[:8]))
    return fx
def frames_cmd(fj, outdir):
    import shutil
    d = json.load(open(fj)); shutil.copy(fj, fj + '.bak_h96'); os.makedirs(outdir, exist_ok=True); view = d.get('dir')
    for fr in d['frames']:
        spec = dict(fr.get('head') or {}); spec.setdefault('expr', fr.get('expression', 'neutral'))
        old = fr.get('stamp_m96') or fr.get('stamp')
        p = write_stamp(view, dict(spec, dx=0, dy=0), os.path.join(outdir, 'c%02d_head.txt' % fr['i']))
        if fr.get('head_at') and old: fr['head_at'] = head_at(view, fr.get('head_at_m96') or fr['head_at'], old, spec); fr['head_at_m96'] = fr.get('head_at_m96') or fr['head_at']
        fr['stamp_m96'] = old; fr['stamp'] = p; fr['head'] = spec
    json.dump(d, open(fj, 'w'), indent=1); print('composed', len(d['frames']), 'heads ->', outdir)
if __name__ == '__main__':
    a = sys.argv[1:]
    if a and a[0] == 'frames': frames_cmd(a[1], a[2])
    else:
        print(write_stamp(a[0], json.loads(a[1]), a[2]))


# ---------------------------------------------------------------- QC helpers (used by v2/qc/qc_gate.py and m96/tools/eyecheck.py)
def is_layered(meta): return isinstance(meta, dict) and 'layered' in meta
def spec_of(meta):
    try: return json.loads(' '.join(meta['head_spec']))
    except Exception: return {}
def master_ref(M, view, stamp_rows, origin):
    """reference grid for a layered frame: the view master with its rest head layers replaced by the composed head at origin
    (rest-head px not covered by the composite are filled from the nearest non-head px in the row)"""
    _, X0, Y0, _, _ = meta(view); rest = compose_stamp(view, {})[0]
    return paste(M, stamp_rows, origin, prev=(rest, (X0, Y0)))
def face_offset(view, spec): return offsets(view, spec)['f']
def library_check(view):
    """every face/<expr>.txt layer == the approved m96 stamp on the face mask (identity of the face layer)"""
    lab, X0, Y0, _, _ = meta(view); G = load(f'{ROOT}/m96/masters/EC0_{view}_96.txt')[0]; bad = []
    for fn in sorted(os.listdir(f'{LD}/{view}/face')):
        e = fn[:-4]; face = load(f'{LD}/{view}/face/{fn}')[0]; st, sm = load(f'{ROOT}/m96/heads/{view}_{e}.txt'); sx, sy = map(int, sm['origin'])
        Gx = [list(r) for r in G]
        for y, r in enumerate(st):
            for x, c in enumerate(r):
                if c != '.': Gx[sy + y][sx + x] = c
        d = [(x, y) for y, r in enumerate(lab) for x, c in enumerate(r) if c == 'f' and face[y][x] != Gx[Y0 + y][X0 + x]]
        if d: bad.append('LAYERLIB face layer %s/%s differs from m96 stamp at %d px %s' % (view, e, len(d), d[:5]))
    return bad
