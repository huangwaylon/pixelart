"""face_layer.py (F, round 3) -- the face as hand-designed pixel parts placed on the 3D head's projected anchors, per frame.

P's call (pixtools venv):
    from face_layer import face_layer                      # sys.path.insert(0, '<EXP>/face')
    g = face_layer({'action': 'walk', 'view': 'SE', 'i': 3}, g, {})     # g = 128x128 char grid (np array or list of rows)
  frame_info: action, view, i (motion frame index); optional 'face_json' (anchors file), 'expr' / 'blink' (override), 'loop'.
  passes:     optional 'ftex' = faceless head pass (path to the 8x <act>_<V>_fNN_tex.png from face/f_render.py, or the float RGBA
              array already cropped to the 128 cell like P's other passes).  Default paths: face/out/<act>/<act>_<V>_*.
  Needs face/f_run.sh "<acts>" "<views>" to have run for the same motion (anchors json + faceless head pass, ~1 s per clip).

What it does per frame:
  1. head cells of the face zone (bbox of the m96 face parts, moved with the head) are re-taken from the FACELESS head pass (the
     master hair/skin projected on the rig head, with the face features erased) -> no smeared baked eyes, no blush/hair crumbs on the face.
  2. parts (face_lib: eyes, brows, mouth, blush, nose) are drawn at the projected 3D anchors: one integer face offset with hysteresis
     (the whole face moves as a unit, never 1 px jitter between parts) + per-part integer residuals (dead band .7 px) for yaw spacing,
     roll (eye height difference) and pitch (eye-mouth spacing); far eye narrows (far -> far3 -> hidden) when the head turns away,
     S-view eyes swap to the 3/4 far eye when the head turns; brows/mouth/blush only on skin (bangs over brows are fine), eyes always
     win over hair, nothing drawn on the silhouette edge.
  3. expression per frame: the motion frame's "face"/"blink" keys, else the default map of the action (DEFAULT_MAP by key name).
CLI:
    python face_layer.py apply <frame_dir> <act> <view> <out_dir> [--json face/out/<act>/<act>_<V>_face.json]   (fNN.txt in -> out)
    python face_layer.py preview <preview_dir> <act> <view> <out_dir>    (composite the face on f_render --preview frames)
"""
import os, sys, json, math
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); EXP = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import face_lib as FL  # noqa: E402
sys.path.insert(0, '/Users/waylonhuang/Documents/other/pixelart/REVIEW/exp/2026-10-28_sw_hires3d/scripts')
import hx  # noqa: E402
P, N, OFF = 8, 128, 256
KEYS = hx.KEYS; PALRGB = np.array(hx.RGB, float)
HYS_G = float(os.environ.get('FHYS', '0.18'))     # global face offset hysteresis (px beyond .5)
HYS_R = float(os.environ.get('FHYSR', '0.22'))    # per-part residual dead band beyond .5
ROLL_SPLIT = float(os.environ.get('FROLL', '5'))  # deg: below this both eyes share one row

# ---------------------------------------------------------------- default expression maps (motion 'key' substrings, first match wins)
DEFAULT_MAP = {
    'walk': [('passing R', 'smile', 'closed'), ('', 'smile', None)],
    'run':  [('push-off', 'effort', None), ('flight', 'determined', None), ('', 'determined', None)],
    'idle': [('blink', 'neutral', 'closed'), ('look', 'smile', None), ('settle R', 'smile', 'half'), ('', 'neutral', None)],
    'dash': [('anticip', 'focused', None), ('crouch', 'focused', None), ('burst', 'effort', None), ('smear', 'effort', None),
             ('glide', 'focused', None), ('skid', 'surprised', None), ('brake', 'surprised', None), ('recover', 'smile', None),
             ('', 'focused', None)],
    'hurt': [('hit', 'hurt', None), ('snap', 'hurt', None), ('whip', 'wince', None), ('hold', 'wince', None), ('recover', 'determined', None),
             ('', 'hurt', None)],
    'jump': [('stand', 'neutral', None), ('anticipation', 'determined', None), ('crouch', 'determined', None), ('launch', 'effort', None),
             ('take-off', 'joyful', None), ('rise', 'joyful', None), ('apex', 'joyful', None), ('fall (reach)', 'smile_open', None),
             ('fall', 'surprised', None), ('land', 'squint', None), ('squash', 'squint', None), ('recover', 'smile_open', None),
             ('settle', 'smile', None), ('end', 'smile', None), ('', 'neutral', None)],
}


def expr_for(act, fr):
    """per-frame expression: the motion file's 'face' / 'blink' keys win; else the action's default map on the frame 'key'"""
    if fr.get('face'): return fr['face'], fr.get('blink'), fr.get('mouth')
    key = (fr.get('key') or '')
    for sub, e, b in DEFAULT_MAP.get(act, [('', 'neutral', None)]):
        if sub in key: return e, (fr.get('blink') or b), fr.get('mouth')
    return 'neutral', fr.get('blink'), fr.get('mouth')


# ---------------------------------------------------------------- faceless head pass -> (mask, chars)
def nearest(rgb, pal):
    d = ((rgb[..., None, :] - pal[None, None]) ** 2).sum(-1); return d.argmin(-1)


CI = (np.arange(N * P)[:, None] // P) * N + (np.arange(N * P)[None, :] // P)


def tex_cells(tex):
    """same rule as P's pixel_chain.tex_cells: texel phase -> per-cell mode of exact palette colours (coverage >= .5)"""
    al = tex[..., 3] > 0.5; rgb = tex[..., :3] * 255
    pid = nearest(rgb, PALRGB); pid[~al] = -1
    ph = []
    for ax in (1, 0):
        a = np.moveaxis(pid, ax, 1); ch = (a[:, 1:] != a[:, :-1]) & (a[:, 1:] >= 0) & (a[:, :-1] >= 0)
        pos = (np.nonzero(ch)[1] + 1) % P; hst = np.bincount(pos, minlength=P); ph.append(int(hst.argmax()) if hst.sum() > 50 else 0)
    phx, phy = ph
    phx = phx - P if phx > P // 2 else phx; phy = phy - P if phy > P // 2 else phy
    pid = np.roll(np.roll(pid, -phy, 0), -phx, 1)
    m = pid >= 0; key = CI[m] * len(KEYS) + pid[m]
    cnt = np.bincount(key, minlength=N * N * len(KEYS)).reshape(N, N, len(KEYS))
    cov = cnt.sum(-1) / (P * P); T = cov >= 0.5
    g = np.array(KEYS)[cnt.argmax(-1)]; g[~T] = '.'
    return T, g


def load_ftex(path, dx, dy):
    a = hx.rd16(path)
    return hx.shift(a[OFF:OFF + N * P, OFF:OFF + N * P], dx, dy)


# ---------------------------------------------------------------- placement (whole clip, cached; loops run twice so f0 sees the end)
_CACHE = {}


def _hround(v, prev, band):
    if prev is None: return int(math.floor(v + 0.5))
    return prev if abs(v - prev) < 0.5 + band else int(math.floor(v + 0.5))


def plan_clip(fj, act, loop=True):
    """per frame: {'G': (gx, gy), 'R': {anchor: (rx, ry)}, 'kinds': {eye.i: kind or None}, 'expr', 'blink', 'g_cont'}"""
    if fj in _CACHE: return _CACHE[fj]
    d = json.load(open(fj)); V = d['view']; parts = json.load(open(os.path.join(HERE, 'parts.json'))).get(V, {})
    rest = d['anchors_rest']; frs = d['frames']; n = len(frs)
    order = (list(range(n)) if loop and n > 2 else []) + list(range(n))
    out = [None] * n; Gp = [None, None]; Rp = {}; kp = {}; RRp = {}
    for t in order:
        f = frs[t]; A = f['anchors']; hd = f['head']
        o = {k: (A[k]['xy'][0] - rest[k][0], A[k]['xy'][1] - rest[k][1]) for k in A}
        core = [k for k in o if k.startswith('eye.') or k == 'mouth'] or list(o)
        if not core:
            out[t] = {'G': (0, 0), 'R': {}, 'kinds': {}, 'expr': expr_for(act, f)[0], 'blink': None, 'mouth': None, 'g_cont': (0, 0), 'head': hd}; continue
        g = (sum(o[k][0] for k in core) / len(core), sum(o[k][1] for k in core) / len(core))
        G = (_hround(g[0], Gp[0], HYS_G), _hround(g[1], Gp[1], HYS_G)); Gp = list(G)
        R = {}; RR = {}
        # eye.0 against the face offset; every other part RELATIVE to eye.0 with a wider dead band, so the face's internal
        # spacing only changes when the 3D projection really moved it by ~1 px (yaw spacing, pitch eye-mouth, roll)
        k0 = 'eye.0' if 'eye.0' in o else core[0]
        px, py = Rp.get(k0, (None, None))
        R[k0] = (_hround(o[k0][0] - G[0], px, HYS_R), _hround(o[k0][1] - G[1], py, HYS_R))
        b0 = R[k0]
        for k in o:
            if k == k0: continue
            px, py = RRp.get(k, (None, None)); hb = HYS_R + (0.13 if k.startswith('eye.') else 0.25)
            rel = (_hround(o[k][0] - G[0] - b0[0], px, hb), _hround(o[k][1] - G[1] - b0[1], py, hb))
            RR[k] = rel; R[k] = (b0[0] + rel[0], b0[1] + rel[1])
        for k in R: R[k] = (max(-2, min(2, R[k][0])), max(-2, min(2, R[k][1])))
        # eyes share a row unless the head is visibly rolled; the row difference keeps the roll's sign
        if 'eye.1' in R:
            (x0, y0), (x1, y1) = R['eye.0'], R['eye.1']
            if abs(hd['roll']) < ROLL_SPLIT:
                ym = int(math.floor((o['eye.0'][1] + o['eye.1'][1]) / 2 - G[1] + 0.5)); y0 = y1 = ym
            else:
                ex_ = FL.resolve(*expr_for(act, f))
                lim = 2 if abs(hd['roll']) >= 10 and ex_['eye'] not in FL.CLOSED_EYES | {'blink_half', 'pain'} else 1
                if abs(y0 - y1) > lim: y1 = y0 + (lim if y1 > y0 else -lim)
            R['eye.0'], R['eye.1'] = (x0, y0), (x1, y1)
        # face proportions: mouth/nose stay within 1 px (y) of the eye-pair mean and 1 px (x) of the eye-pair centre
        ey = [R[k] for k in R if k.startswith('eye.')] or [b0]; emx = sum(e[0] for e in ey) / len(ey); emy = sum(e[1] for e in ey) / len(ey)
        for k in ('mouth', 'nose'):
            if k in R:
                R[k] = (int(max(math.floor(emx - 1), min(math.ceil(emx + 1), R[k][0]))), int(max(math.floor(emy - 1), min(math.ceil(emy + 1), R[k][1]))))
        # brows ride on their eye; cheeks within 1 px of their eye in x and of the mouth in y; nose between
        for k in list(R):
            if k.startswith('brow.'): R[k] = R['eye.' + k.split('.')[1]]
        for k in list(R):
            if k.startswith('cheek.'):
                e = R.get('eye.' + k.split('.')[1], R.get('eye.0', R[k])); m = R.get('mouth', e)
                R[k] = (max(e[0] - 1, min(e[0] + 1, R[k][0])), max(min(e[1], m[1]) - 1, min(max(e[1], m[1]) + 1, R[k][1])))
        if 'nose' in R and 'mouth' in R:
            m = R['mouth']; R['nose'] = (max(m[0] - 1, min(m[0] + 1, R['nose'][0])), max(m[1] - 1, min(m[1] + 1, R['nose'][1])))
        Rp = dict(R); RRp = dict(RR)
        # foreshortening: eye kinds from the head turn (dyaw + = toward the camera) with hysteresis
        kinds = {}
        for k, a in parts.items():
            if not k.startswith('eye.'): continue
            base = a['kind']; prev = kp.get(k, base); kind = base
            if V in ('SE', 'SW') and base in ('far', 'far_left'):
                dy_ = hd['dyaw']; f3 = 'far3' if base == 'far' else 'far3_left'; fo = 'front_right' if base == 'far' else 'front_left'
                kind = base
                if dy_ < (-11 if prev == base else -8): kind = f3
                if dy_ < (-24 if prev != 'hidden' else -20): kind = 'hidden'
                if dy_ > (13 if prev != fo else 9): kind = fo   # turned toward the camera: the far eye opens up
            elif V == 'S':
                tr = hd['turn']; thr = 8 if prev != base else 12
                far_right = tr < -thr; far_left = tr > thr     # sign: + turn = her left = screen right in S
                if base == 'front_right' and far_right: kind = 'far'
                if base == 'front_left' and far_left: kind = 'far_left'
            if A[k]['facing'] < 0.12: kind = 'hidden'
            kinds[k] = kind; kp[k] = kind
        e, b, mo = expr_for(act, f)
        off = d.get('tex_off', [0, 0]); Gd = (G[0] + int(off[0]), G[1] + int(off[1]))   # part origins are master coords
        out[t] = {'G': Gd, 'R': R, 'kinds': kinds, 'expr': e, 'blink': b, 'mouth': mo, 'g_cont': g, 'head': hd}
    res = {'view': V, 'json': d, 'parts': parts, 'plan': out}
    _CACHE[fj] = res
    return res


# ---------------------------------------------------------------- drawing
def _edge(g, x, y):
    if not (0 < x < N - 1 and 0 < y < N - 1): return True
    return g[y, x] == '.' or any(g[y + b, x + a] == '.' for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1)))


def face_cells(V, parts, G, R, kinds, ex):
    """list of (x, y, char, layer) for one frame; layer: eye (wins over hair) | wing | skin (only on skin) | blush"""
    out = []; e_eye = ex['eye']
    eyes = sorted([k for k in parts if k.startswith('eye.')])
    for n_, k in enumerate(eyes):
        kind = kinds.get(k, parts[k]['kind'])
        if kind == 'hidden': continue
        x0, y0 = parts[k]['origin']; rx, ry = R[k]; x0 += G[0] + rx; y0 += G[1] + ry
        base = parts[k]['kind']
        if kind == 'far3': x0 += 1                     # narrowed far eye keeps its outer edge at the cheek
        if kind == 'far' and base == 'front_right': x0 += 1
        if kind == 'front_right' and base == 'far': x0 -= 1
        if kind == 'front_left' and base == 'far_left': x0 -= 1
        if kind == 'far_left' and base == 'front_left': x0 += 1
        ee = e_eye
        if ex.get('wink') and n_ == 0: ee = 'joy'       # wink: the screen-left eye closes in a happy arc
        if n_ == 1 and ex.get('eye1'): ee = ex['eye1']  # wince: the second eye only squints
        t = FL.eye_tmpl(kind, ee)
        for j, r in enumerate(t):
            ink = [i for i, c in enumerate(r) if c not in '._']
            for i, c in enumerate(r):
                if c == '_': continue
                if c == '.':
                    if 1 <= j <= 4 and ink and min(ink) < i < max(ink): out.append((x0 + i, y0 + j, 's', 'eyebg', n_))
                    continue
                out.append((x0 + i, y0 + j, 'W' if c == '@' else c, 'eye', n_))
        for dx, dy, c in FL.wing_tmpl(kind, ee):
            out.append((x0 + dx, y0 + dy, c, 'wing', n_))
        if ex.get('tear'):   # 2 px W tear under the outer corner (outer = screen side away from the nose)
            w = len(t[0]); outer = 0 if kind in ('front_left', 'profile', 'far_left', 'far3_left') else w - 2
            out += [(x0 + outer, y0 + 5, 'W', 'skin', -1), (x0 + outer, y0 + 6, 'W', 'skin', -1)]
        bt = FL.brow_tmpl(kind, ex['brow'])
        top = min([j for j, r in enumerate(bt) if 'h' in r] or [0])
        for j, r in enumerate(bt):
            for i, c in enumerate(r):
                if c != '.': out.append((x0 + i, y0 - 3 + j, FL.SPEC['brow'].get('char', 'g'), 'brow', n_))
        w = len(bt[0])
        for i in (range(-1, 4) if w <= 4 else range(0, 6)):
            for j in range(top - 1, 3):
                out.append((x0 + i, y0 - 3 + j, 's', 'window', n_))
    if 'mouth' in parts:
        mx, my = parts['mouth']['origin']; rx, ry = R['mouth']; mx += G[0] + rx; my += G[1] + ry
        mt = FL.mouth_tmpl(ex['mouth'])
        if parts['mouth'].get('mirror'): mt = [r[::-1] for r in mt]
        if V in ('E', 'W'):   # profile: 3 px mouth set 1 px back from the muzzle edge (a 4 px mouth touched the jaw outline)
            mt = [r[:3] if V == 'E' else r[1:] for r in mt]; mx += -1 if V == 'E' else 1
            mt = [r if any(c not in '._' for c in r) else r for r in mt]
        for j, r in enumerate(mt):
            for i, c in enumerate(r):
                if c == '_': continue
                out.append((mx + i, my + j, 's' if c == '.' else c, 'skin', -1))
    for k in sorted(parts):
        if not k.startswith('cheek.'): continue
        idx = k.split('.')[1]
        if kinds.get('eye.' + idx) == 'hidden': continue
        bx, by = parts[k]['origin']; rx, ry = R[k]; bx += G[0] + rx; by += G[1] + ry
        kind = parts[k]['kind']
        if ex['blush'] is None: continue
        bt = FL.blush_tmpl(kind, ex['blush'])
        if parts[k].get('mirror'): bt = [r[::-1] for r in bt]
        sh = 1 if kinds.get('eye.' + idx) == 'far3' else 0
        for j, r in enumerate(bt):
            for i, c in enumerate(r):
                if c == 'k': out.append((bx + i + sh, by + j, 'k', 'blush', -1))
    for k in sorted(parts):   # NE/NW: lash tip px poking past the cheek outline (count per expression, eye_spec ne_lash)
        if not k.startswith('lash.'): continue
        lx, ly = parts[k]['origin']; rx, ry = R[k]; lx += G[0] + rx; ly += G[1] + ry
        nl = FL.SPEC['ne_lash'].get(FL.ET.expr_key(e_eye), 1)
        for dx, dy in parts[k]['px'][:nl]: out.append((lx + dx, ly + dy, 'K', 'lash', -1))
    if 'nose' in parts and V != 'E':
        nx, ny = parts['nose']['origin']; rx, ry = R['nose']; nx += G[0] + rx; ny += G[1] + ry
        for dx, dy, c in parts['nose']['px']: out.append((nx + dx, ny + dy, c, 'skin', -1))
    return out


def zone_box(parts, G, pad=2):
    xs, ys = [], []
    for k, a in parts.items():   # mirror-symmetric margins (W/SW/NW boxes = mirrored E/SE/NE boxes)
        x, y = a['origin']
        if k.startswith(('eye.', 'brow.')): w = FL.kind_w(a['kind'])
        elif k == 'mouth': w = 4
        elif k.startswith('cheek.'): w = len(FL.ET.blush_tmpl(a['kind'], 'neutral')[0])
        elif k == 'nose': w = max(p[0] for p in a['px']) + 1
        else: w = 1
        xs += [x - 1, x + w + 1]; ys += [y - 1, y + 6]
    return max(0, min(xs) + G[0] - pad), max(0, min(ys) + G[1] - pad), min(N, max(xs) + G[0] + pad), min(N, max(ys) + G[1] + pad)


def draw(g, gn, T, V, parts, pl):
    """g: frame chars (modified copy returned), gn/T: faceless head chars/mask for this frame"""
    g = np.array(g, dtype='<U1').copy()
    ex = FL.resolve(pl['expr'], pl['blink'], pl.get('mouth'))
    x0, y0, x1, y1 = zone_box(parts, pl['G'])
    # 1. face zone <- faceless head (drops the baked/smeared face + texture crumbs)
    Z = np.zeros((N, N), bool); Z[y0:y1, x0:x1] = True; Z &= T & (g != '.')
    g[Z] = gn[Z]
    # 1b. stray hair crumbs on the face skin (1 px hair char with >= 6 skin 8-neighbours) -> skin
    for y, x in zip(*np.nonzero(Z)):
        if g[y, x] in 'HhgLm' and not _edge(g, x, y):
            nb = g[y - 1:y + 2, x - 1:x + 2].ravel()
            if sum(c in 'sS' for c in nb) >= 6: g[y, x] = 's'
    cells = face_cells(V, parts, pl['G'], pl['R'], pl['kinds'], ex)
    # keep every eye inside the face: if eye ink lands on the silhouette edge / off the head, slide that eye (+ brow, wing) toward the
    # face centre by the smallest shift (<= 2 px) that fits (far eye at the cheek outline when the head turns)
    mcx = np.mean([x for x, y, c, l, e in cells if l == 'skin'] or [N / 2])
    for e in sorted({c[4] for c in cells if c[4] >= 0}):
        ink = [(x, y) for x, y, c, l, ee in cells if ee == e and l == 'eye']
        if not ink: continue
        ex_ = np.mean([x for x, y in ink]); step = 1 if mcx > ex_ else -1
        bad = lambda dx: sum(1 for x, y in ink if not (0 <= x + dx < N and 0 <= y < N) or _edge(g, x + dx, y) or not T[y, x + dx])
        b0 = bad(0)
        if b0:
            best = min((bad(k * step), k) for k in (0, 1, 2))[1] * step
            if best: cells = [(x + best, y, c, l, ee) if ee == e else (x, y, c, l, ee) for x, y, c, l, ee in cells]
    # round 4: far eye off the cheek outline -- if the outward neighbours of the far eye's outer ink column are dark (outline / side-lock
    # K/h) on >= 2 iris rows, slide that eye 1 px inward so a skin column separates lash and cheek outline (walk SE f03-f05)
    for e in sorted({c[4] for c in cells if c[4] >= 0}):
        kind = pl['kinds'].get(f'eye.{e}', '')
        if kind not in ('far', 'far3', 'far_left', 'far3_left'): continue
        d_ = 1 if kind in ('far', 'far3') else -1
        ink = [(x, y) for x, y, c, l, ee in cells if ee == e and l == 'eye']
        if not ink: continue
        ox = max(x for x, y in ink) if d_ > 0 else min(x for x, y in ink)
        ys_ = sorted({y for x, y in ink})[1:4]
        dark = sum(1 for y in ys_ if 0 <= ox + d_ < N and g[y, ox + d_] in 'KhHm')
        if dark >= 2: cells = [(x - d_, y, c, l, ee) if ee == e else (x, y, c, l, ee) for x, y, c, l, ee in cells]
    sk = lambda c: c in 'sSk'
    for x, y, c, layer, _e in cells:          # window first (hair over the brow cols -> skin, never on the edge)
        if layer == 'window' and 0 <= x < N and 0 <= y < N and g[y, x] in 'HhgLmK' and not _edge(g, x, y) and gn[y, x] != '.':
            # only cut where the cell is near skin (a bang tip), not deep inside the fringe
            if sum(ch in 'sS' for ch in g[y - 1:y + 2, x - 1:x + 2].ravel()) >= 3: g[y, x] = 's'
    for x, y, c, layer, _e in cells:
        if not (0 <= x < N and 0 <= y < N): continue
        b = g[y, x]
        if layer in ('eye', 'eyebg'):
            if _edge(g, x, y) or not T[y, x]: continue
            g[y, x] = c
        elif layer == 'wing':
            if b != '.' and T[y, x]: g[y, x] = c
        elif layer == 'brow':
            if sk(b) and not _edge(g, x, y):
                g[y, x] = c
                # round 4: angled brows clear of the fringe: the bang px right above a brow px becomes skin (1 px gap)
                if y > 0 and g[y - 1, x] in 'HhgLmK' and not _edge(g, x, y - 1) and T[y - 1, x]: g[y - 1, x] = 's'
        elif layer == 'skin':
            if (sk(b) or b == 'm') and not _edge(g, x, y): g[y, x] = c
        elif layer == 'blush':
            if b in 'sS' and not _edge(g, x, y): g[y, x] = c
        elif layer == 'lash':   # outside the silhouette, touching it
            if b == '.' and any(0 <= y + bb < N and 0 <= x + aa < N and g[y + bb, x + aa] != '.' for aa, bb in ((1, 0), (-1, 0), (0, 1), (0, -1))): g[y, x] = c
    # orphan guard: single brow/blush px -> skin
    for x, y, c, layer, _e in cells:
        if layer in ('brow', 'blush') and 0 < x < N - 1 and 0 < y < N - 1 and g[y, x] == c:
            nb = g[y - 1:y + 2, x - 1:x + 2].ravel()
            if (nb == c).sum() <= 1: g[y, x] = 's'
    return g


# ---------------------------------------------------------------- P's entry point
def _paths(fi):
    act, V = fi['action'], fi['view']; d = fi.get('face_dir') or os.path.join(HERE, 'out', act)
    return fi.get('face_json') or os.path.join(d, f'{act}_{V}_face.json'), os.path.join(d, f"{act}_{V}_f{int(fi['i']):02d}_tex.png")


def face_layer(frame_info, pixel_frame, passes=None):
    passes = passes or {}
    fj, tp = _paths(frame_info)
    loop = frame_info.get('loop', frame_info['action'] != 'jump')
    C = plan_clip(fj, frame_info['action'], loop)
    if not C['parts']: return pixel_frame   # N / NW without face parts
    d = C['json']; idx = [f['i'] for f in d['frames']].index(int(frame_info['i'])); pl = dict(C['plan'][idx])
    if frame_info.get('expr'): pl['expr'] = frame_info['expr']; pl['blink'] = frame_info.get('blink'); pl['mouth'] = frame_info.get('mouth')
    rf = passes.get('rface') or frame_info.get('rface')     # R's per-frame anchors (render info frames[i].face): body/arm/hand occlusion
    if rf:
        fa = d['frames'][idx]['anchors']; kinds = dict(pl['kinds'])
        for k in kinds:
            if k not in fa: continue
            x, y = fa[k]['xy']
            best = min(((n, (v['px'][0] - x) ** 2 + (v['px'][1] - y) ** 2) for n, v in rf.items() if n.startswith('eye') and 'px' in v), key=lambda t: t[1], default=None)
            if best and best[1] < 16 and rf[best[0]].get('occ_m') is not None and not rf[best[0]].get('visible', True): kinds[k] = 'hidden'
        pl['kinds'] = kinds
    if passes.get('ftex_cells') is not None:   # precomputed (T, chars) of the faceless head
        T, gn = passes['ftex_cells']
    else:
        ft = passes.get('ftex', tp)
        tex = load_ftex(ft, d['align']['dx'], d['align']['dy']) if isinstance(ft, str) else ft
        T, gn = tex_cells(tex)
    g = np.array([list(r) for r in pixel_frame]) if not isinstance(pixel_frame, np.ndarray) else pixel_frame
    out = draw(g, gn, T, C['view'], C['parts'], pl)
    return out if isinstance(pixel_frame, np.ndarray) else [''.join(r) for r in out]


def frame_meta(frame_info):
    """placement + expression of a frame (for boards / P's logs)"""
    fj, _ = _paths(frame_info); C = plan_clip(fj, frame_info['action'], frame_info.get('loop', frame_info['action'] != 'jump'))
    idx = [f['i'] for f in C['json']['frames']].index(int(frame_info['i'])); return C, C['plan'][idx], C['json']['frames'][idx]


# ---------------------------------------------------------------- CLI
def _apply(fd, act, V, od, fj=None):
    os.makedirs(od, exist_ok=True)
    fs = sorted(f for f in os.listdir(fd) if f.endswith('.txt') and f.startswith('f'))
    res = []
    for f in fs:
        i = int(f[1:3]); g = hx.read_grid(os.path.join(fd, f))
        fi = {'action': act, 'view': V, 'i': i}
        if fj: fi['face_json'] = fj
        g2 = face_layer(fi, g, {})
        hx.save(g2, os.path.join(od, f[:-4]), V); res.append(g2)
    return res


if __name__ == '__main__':
    a = sys.argv[1:]
    if a[0] == 'apply':
        fj = a[a.index('--json') + 1] if '--json' in a else None
        _apply(a[1], a[2], a[3], a[4], fj); print('face ->', a[4])
