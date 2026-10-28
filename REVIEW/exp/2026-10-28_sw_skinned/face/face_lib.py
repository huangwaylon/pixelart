"""face_lib.py (F, round 3) -- the face part library at sprite scale (96 px figure, 128 cell) + faceless head textures.

Parts are the approved m96 face (swordswoman/v2/m96/FACE_SPEC.md, eye_spec.json, heads/anchor.json), read through the m96 template
code (v2/m96/tools/eyetmpl.py), so the eyes / brows / mouths / blush / nose are pixel-identical to the masters and the 45 head stamps.
New here: named expressions (EXPR) that combine eye/brow/mouth/blush parts, blink overlays, a closed-smile mouth, a wink, a landing
squint, and a narrowed far eye ('far3') for foreshortening.

  python face_lib.py build     -> face/tex/tex_<V>_nf.png (faceless projection textures) + face/tex/EC0_<V>_nf.txt + face/parts.json
"""
import os, sys, json
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); EXP = os.path.dirname(HERE)
SW = '/Users/waylonhuang/Documents/other/pixelart/swordswoman/'
M96 = SW + 'v2/m96/'
sys.path.insert(0, M96 + 'tools')
import eyetmpl as ET  # noqa: E402
SPEC = ET.SPEC
ANC = json.load(open(M96 + 'heads/anchor.json'))['views']
SKIN = set('sSk')
HAIR = set('HhgLm')
INK_EYE = set('KhgLW')

# ---------------------------------------------------------------- expressions (owner names) -> parts
SMILE_CLOSED = ['____', 'm..m', '.mm.']          # closed smile: corners on the mouth row, centre 1 row lower (never touches the nose)
MOUTH_FLAT = ['____', 'mmmm', '____']
MOUTH_SMALL_O = ['____', '.RR.', '.RR.']
MOUTH_GRIT = ['____', 'mWWm', '.mm.']           # round 4: effort = a flat dark slit with 2 px of teeth (the spec's m__m read as a pout)
MOUTH_GRIT_OPEN = ['____', 'mWWm', '.RR.']      # effort with the mouth open (M's mouth: open) -- 4x2 max, no red lips ring
MOUTH_HURT = ['____', '.mm.', 'm..m']           # downturned frown (round-4 crit: the spec grimace read close to joyful)
MOUTH_FOCUS = ['____', 'mmm.', '____']          # short set mouth, off-centre
EXPR = {
    #  name          eye (eye_spec expr)  brow          mouth (eye_spec expr or template)   blush
    'neutral':    dict(eye='neutral',    brow='neutral',    mouth='neutral',      blush='neutral'),
    'smile':      dict(eye='neutral',    brow='cheerful',   mouth=SMILE_CLOSED,   blush='cheerful'),
    'smile_open': dict(eye='cheerful',   brow='cheerful',   mouth='cheerful',     blush='cheerful'),
    'joyful':     dict(eye='joy',        brow='joy',        mouth='joy',          blush='joy'),
    'determined': dict(eye='determined', brow='determined', mouth=MOUTH_FLAT,     blush='neutral'),
    'effort':     dict(eye='blink_half', brow='effort',     mouth=MOUTH_GRIT,     blush='neutral'),   # narrowed, focused eyes (not shut while running)
    'strain':     dict(eye='effort',     brow='effort',     mouth=MOUTH_GRIT,     blush='neutral'),
    # round 4: dash + hurt
    'focused':    dict(eye='determined', brow='determined', mouth=MOUTH_FOCUS,    blush=None),   # dash: open eyes under steep V brows, set mouth, no blush
    'hurt':       dict(eye='pain',       brow='pain',       mouth=MOUTH_HURT,     blush='neutral'),   # pained > <, brows tilted up to the centre
    'wince':      dict(eye='pain',       brow='pain',       mouth=MOUTH_GRIT,     blush='neutral', eye1='blink_half'),   # one eye shut, one squinting
    'hurt_tear':  dict(eye='pain',       brow='pain',       mouth=MOUTH_HURT,     blush='neutral', tear=True),   # spec effort: eyes squeezed shut
    'shout':      dict(eye='shout',      brow='shout',      mouth='shout',        blush='neutral'),
    'surprised':  dict(eye='surprised',  brow='surprised',  mouth=MOUTH_SMALL_O,  blush='neutral'),
    'squint':     dict(eye='pain',       brow='effort',     mouth=MOUTH_FLAT,     blush='neutral'),   # landing: > < eyes
    'wink':       dict(eye='neutral',    brow='cheerful',   mouth='cheerful',     blush='cheerful', wink=True),
    'blink':      dict(eye='blink_closed', brow='neutral',  mouth='neutral',      blush='neutral'),
    'half_blink': dict(eye='blink_half', brow='neutral',    mouth='neutral',      blush='neutral'),
}
ALIASES = {'joy': 'joyful', 'cheerful': 'smile_open', 'blink_closed': 'blink', 'blink_half': 'half_blink', 'half-blink': 'half_blink',
           'land': 'squint', 'pain': 'hurt', 'dash': 'focused', 'tear': 'hurt_tear', 'tears': 'hurt_tear'}
CLOSED_EYES = {'joy', 'effort', 'pain', 'blink_closed'}


MOUTH_OPEN = {'neutral': 'cheerful', 'smile': 'cheerful', 'smile_open': 'cheerful', 'joyful': 'joy', 'determined': ['____', 'mmmm', '.RR.'],
              'effort': MOUTH_GRIT_OPEN, 'strain': MOUTH_GRIT_OPEN, 'focused': ['____', 'mmmm', '.RR.'], 'hurt': MOUTH_HURT,
              'hurt_tear': MOUTH_HURT, 'wince': MOUTH_GRIT_OPEN, 'shout': 'shout', 'surprised': MOUTH_SMALL_O, 'squint': ['____', 'mmmm', '.RR.'], 'wink': 'cheerful',
              'blink': 'neutral', 'half_blink': 'neutral'}
MOUTH_CLOSED = {'hurt': MOUTH_GRIT, 'hurt_tear': MOUTH_GRIT, 'smile_open': SMILE_CLOSED, 'joyful': SMILE_CLOSED, 'shout': MOUTH_FLAT, 'surprised': ['____', '.mm.', '____'], 'wink': SMILE_CLOSED}


def resolve(expr, blink=None, mouth=None):
    """expression name (+ optional blink cue 'closed'|'half') -> part dict; a blink overrides only the eyes of an open-eye expression"""
    e = ALIASES.get(expr, expr); d = dict(EXPR.get(e, EXPR['neutral'])); d['name'] = e
    if isinstance(blink, (int, float)) and not isinstance(blink, bool):   # M's numeric lid cue: 0 open, .5 half, 1 closed
        blink = 'closed' if blink >= 0.75 else ('half' if blink >= 0.25 else None)
    if mouth == 'open': d['mouth'] = MOUTH_OPEN.get(e, d['mouth'])
    elif mouth == 'closed': d['mouth'] = MOUTH_CLOSED.get(e, d['mouth'])
    b = {'closed': 'blink_closed', 'blink': 'blink_closed', True: 'blink_closed', 'half': 'blink_half', 'half_blink': 'blink_half'}.get(blink)
    if b and d['eye'] not in CLOSED_EYES:
        if not (b == 'blink_half' and d['eye'] == 'blink_closed'): d['eye'] = b
        d['wink'] = False; d.pop('eye1', None)
    return d


# ---------------------------------------------------------------- part templates
def eye_tmpl(kind, e):
    """6-row eye block (gap row + lash + 3 iris + empty) for kind front_left|front_right|far|far3|profile|far_left"""
    if kind == 'far3':   # foreshortened far eye: the far block without its inner contour column (3 wide)
        return [r[1:] for r in ET.kind_tmpl('far', e)]
    if kind == 'far3_left':
        return [r[:-1] for r in ET.kind_tmpl('far_left', e)]
    return ET.kind_tmpl(kind, e)


def wing_tmpl(kind, e):
    if kind == 'far3': return [(dx - 1, dy, c) for dx, dy, c in ET.wing_px('far', e) if dx >= 1]
    if kind == 'far3_left': return [(dx, dy, c) for dx, dy, c in ET.wing_px('far_left', e) if dx <= 2]
    return ET.wing_px(kind, e)


def brow_tmpl(kind, e):
    if kind == 'far3': return [r[1:] for r in ET.brow_tmpl('far', e)]
    if kind == 'far3_left': return [r[:-1] for r in ET.brow_tmpl('far_left', e)]
    return ET.brow_tmpl(kind, e)


def mouth_tmpl(m):
    return list(m) if isinstance(m, list) else list(SPEC['mouth'][ET.expr_key(m)])


def blush_tmpl(kind, e):
    return ET.blush_tmpl(kind, e)


# ---------------------------------------------------------------- per-view anchors (master cell coords) for the 3D anchor fit
def view_anchors(v):
    """named anchor points (pixel centres in the 128 master cell) + the part placement they carry.
    eye.<i>: iris centre (block x0 + w/2, y0 + 3); mouth: block centre; cheek.<i>: blush patch centre; nose: nose px centre."""
    a = ANC[v]; out = {}
    for i, ey in enumerate(a['eyes']):
        w = len(ET.kind_tmpl(ey['kind'], 'neutral')[0])
        out[f'eye.{i}'] = {'xy': [ey['x0'] + w / 2.0, ey['y0'] + 3.0], 'kind': ey['kind'], 'origin': [ey['x0'], ey['y0']]}
        out[f'brow.{i}'] = {'xy': [ey['x0'] + w / 2.0, ey['y0'] - 1.5], 'kind': ey['kind'], 'origin': [ey['x0'], ey['y0'] - 3]}
    if a.get('mouth'):
        mx, my = a['mouth']; out['mouth'] = {'xy': [mx + 2.0, my + 1.5], 'origin': [mx, my]}
    for i, (bx, by, kind) in enumerate(a.get('blush', [])):
        w = len(ET.blush_tmpl(kind, 'neutral')[0]); out[f'cheek.{i}'] = {'xy': [bx + w / 2.0, by + 1.0], 'kind': kind, 'origin': [bx, by]}
    if a.get('ne_lash'):
        xs = [p[0] for p in a['ne_lash']]; ys = [p[1] for p in a['ne_lash']]
        out['lash.0'] = {'xy': [xs[0] + .5, ys[0] + .5], 'origin': [xs[0], ys[0]], 'px': [[x - xs[0], y - ys[0]] for x, y in zip(xs, ys)]}
    if a.get('nose'):
        xs = [p[0] for p in a['nose']]; ys = [p[1] for p in a['nose']]
        out['nose'] = {'xy': [sum(xs) / len(xs) + .5, sum(ys) / len(ys) + .5], 'origin': [min(xs), min(ys)],
                       'px': [[p[0] - min(xs), p[1] - min(ys), p[2]] for p in a['nose']]}
    return out


MIRROR = {'W': 'E', 'SW': 'SE', 'NW': 'NE'}
MKIND = {'front_left': 'front_right', 'front_right': 'front_left', 'far': 'far_left', 'far_left': 'far', 'profile': 'front_right',
         'far3': 'far3_left', 'far3_left': 'far3', 'front': 'front', 'ne': 'ne'}


def kind_w(kind):
    return len(eye_tmpl(kind, 'neutral')[0])


def mirror_anchors(src):
    """W/SW/NW parts = the E/SE/NE parts mirrored in the 128 cell (x -> 128 - x; blocks: x0 -> 128 - x0 - w); mirrored kinds, templates
    mirrored at draw time ('mirror': True); the catchlight stays top-left (eyetmpl mirror keeps the iris span)."""
    out = {}
    for k, a in view_anchors(src).items():
        b = dict(a); b['xy'] = [128 - a['xy'][0], a['xy'][1]]
        if k.startswith(('eye.', 'brow.')):
            b['kind'] = MKIND[a['kind']]; w = kind_w(a['kind']); b['origin'] = [128 - a['origin'][0] - w, a['origin'][1]]
        elif k == 'mouth': b['origin'] = [128 - a['origin'][0] - 4, a['origin'][1]]
        elif k.startswith('cheek.'):
            w = len(ET.blush_tmpl(a['kind'], 'neutral')[0]); b['origin'] = [128 - a['origin'][0] - w, a['origin'][1]]
        elif k == 'nose':
            w = max(p[0] for p in a['px']) + 1; b['origin'] = [128 - a['origin'][0] - w, a['origin'][1]]
            b['px'] = [[w - 1 - p[0], p[1], p[2]] for p in a['px']]
        elif k.startswith('lash.'):
            b['origin'] = [127 - a['origin'][0], a['origin'][1]]; b['px'] = [[-p[0], p[1]] for p in a['px']]
        b['mirror'] = True; out[k] = b
    return out


def parts_for(v):
    return mirror_anchors(MIRROR[v]) if v in MIRROR else (view_anchors(v) if v in ANC else {})


# ---------------------------------------------------------------- faceless master (face features erased at the master positions)
def rd(p): return [list(l.rstrip('\n')) for l in open(p) if l.strip() and not l.startswith(';')]


def is_edge(g, x, y):
    return any(not (0 <= y + b < len(g) and 0 <= x + a_ < len(g[0])) or g[y + b][x + a_] == '.' for a_, b in ((1, 0), (-1, 0), (0, 1), (0, -1)))


EXPRS = [e for e in SPEC['front_left'] if not e.startswith('_')]


def faceless(g, v):
    """erase eyes / brows / mouth / blush / nose of the master grid (skin s; the side hair, outlines and the E profile nose stay)"""
    a = ANC[v]; g = [r[:] for r in g]
    for ey in a['eyes']:
        k = ey['kind']; x0, y0 = ey['x0'], ey['y0']
        t = ET.kind_tmpl(k, 'neutral'); w = len(t[0])
        # brow rows y0-3..y0-1 over the brow cols: brow ink (hair-ramp chars on the cut window) -> skin
        bt = ET.brow_tmpl(k, 'neutral')
        for j, r in enumerate(bt):
            for i, c in enumerate(r):
                x, y = x0 + i, y0 - 3 + j
                if c != '.' and g[y][x] in HAIR and not is_edge(g, x, y): g[y][x] = 's'
        # eye block rows 1..5 (all expressions' ink cells) and row-0 cap px -> skin
        cells = {(i, j) for e in EXPRS for j, r in enumerate(ET.kind_tmpl(k, e)) for i, c in enumerate(r) if c not in '._'}
        for j in range(1, 6):
            for i in range(w):
                if t[j][i] != '_': cells.add((i, j))
        for i, j in cells:
            x, y = x0 + i, y0 + j
            if g[y][x] != '.' and not is_edge(g, x, y) and (j > 0 or g[y][x] in 'hKgS'): g[y][x] = 's'
        for kk, c in ey.get('wing_bg', {}).items():
            dx, dy = map(int, kk.split(',')); g[y0 + dy][x0 + dx] = c
    if a.get('mouth'):
        mx, my = a['mouth']
        for j in range(3):
            for i in range(4):
                x, y = mx + i, my + j
                if g[y][x] != '.' and not is_edge(g, x, y) and g[y][x] in 'smRkKS': g[y][x] = 's'
    for bx, by, kind in a.get('blush', []):
        for j in range(3):
            for i in range(-1, 5):
                x, y = bx + i, by + j
                if g[y][x] == 'k': g[y][x] = 's'
    if v != 'E':
        for x, y, c in a.get('nose', []): g[y][x] = 's'
    return g


def build():
    from PIL import Image
    sys.path.insert(0, '/Users/waylonhuang/Documents/other/pixelart/REVIEW/exp/2026-10-28_sw_hires3d/scripts')
    import hx
    od = os.path.join(HERE, 'tex'); os.makedirs(od, exist_ok=True)
    rgb = {k: tuple(int(c) for c in hx.RGB[i]) for i, k in enumerate(hx.KEYS)}
    rep = {}
    for v in ('S', 'SE', 'E', 'NE', 'N'):
        m = rd(f'{M96}masters/EC0_{v}_96.txt'); f = faceless(m, v) if v in ('S', 'SE', 'E') else [r[:] for r in m]
        if v == 'NE':   # NE: drop the blush + lash tip (re-drawn as parts when the head turns toward the camera)
            for bx, by, kind in ANC['NE'].get('blush', []):
                for j in range(3):
                    for i in range(-1, 3):
                        if f[by + j][bx + i] == 'k': f[by + j][bx + i] = 's'
        open(f'{od}/EC0_{v}_nf.txt', 'w').write('\n'.join(''.join(r) for r in f) + '\n')
        im = Image.open(f'{EXP}/rig/tex/tex_{v}.png').convert('RGBA'); a = np.array(im)
        n = 0
        for y in range(len(m)):
            for x in range(len(m[0])):
                if f[y][x] != m[y][x]:
                    a[y, x, :3] = rgb[f[y][x]]; n += 1
        Image.fromarray(a).save(f'{od}/tex_{v}_nf.png'); rep[v] = n
    # mirrored views: R projects the mirrored masters; the faceless texture = R's tex_<W> with the mirrored source erase applied
    for v, src in MIRROR.items():
        f = [r[::-1] for r in rd(f'{od}/EC0_{src}_nf.txt')]; m = [r[::-1] for r in rd(f'{M96}masters/EC0_{src}_96.txt')]
        open(f'{od}/EC0_{v}_nf.txt', 'w').write('\n'.join(''.join(r) for r in f) + '\n')
        tp = f'{EXP}/rig/tex/tex_{v}.png'
        if not os.path.exists(tp): rep[v] = 'no rig tex yet'; continue
        a = np.array(Image.open(tp).convert('RGBA')); n = 0
        for y in range(len(m)):
            for x in range(len(m[0])):
                if f[y][x] != m[y][x]: a[y, x, :3] = rgb[f[y][x]]; n += 1
        Image.fromarray(a).save(f'{od}/tex_{v}_nf.png'); rep[v] = n
    parts = {v: parts_for(v) for v in ('S', 'SE', 'E', 'NE', 'N', 'W', 'SW', 'NW')}
    json.dump(parts, open(os.path.join(HERE, 'parts.json'), 'w'), indent=1)
    print('faceless textures', rep, '->', od)


def calib():
    """integer offset of the rendered rest head (faceless tex pass, face/out/rest) vs the m96 master per view -> face/calib.json.
    The rig head renders a few px above the master (the rig body is taller; align.json fits the feet), so the anchors are ray-cast at
    master_xy - off, i.e. where the master's eye really shows on the rig head."""
    import face_layer as F
    out = {}
    for V in ('S', 'SE', 'E', 'NE', 'N', 'W', 'SW', 'NW'):
        if not os.path.exists(f'{HERE}/out/rest/rest_{V}_f00_tex.png'):
            src = MIRROR.get(V)
            if src in out: out[V] = {'dx': -out[src]['dx'], 'dy': out[src]['dy'], 'match': None, 'from': src}
            continue
        d = json.load(open(f'{HERE}/out/rest/rest_{V}_face.json'))
        T, gn = F.tex_cells(F.load_ftex(f'{HERE}/out/rest/rest_{V}_f00_tex.png', d['align']['dx'], d['align']['dy']))
        m = np.array(rd(f'{HERE}/tex/EC0_{V}_nf.txt')); best = None
        for dy in range(-6, 7):
            for dx in range(-6, 7):
                r = np.roll(np.roll(gn, dy, 0), dx, 1); Tm = np.roll(np.roll(T, dy, 0), dx, 1)
                eq = ((r == m) & Tm).sum() / Tm.sum()
                if best is None or eq > best[0]: best = (float(eq), -dx, -dy)
        out[V] = {'dx': best[1], 'dy': best[2], 'match': round(best[0], 3)}
    json.dump(out, open(f'{HERE}/calib.json', 'w'), indent=1); print('calib', out)


if __name__ == '__main__':
    if sys.argv[1:] and sys.argv[1] == 'build': build()
    if sys.argv[1:] and sys.argv[1] == 'calib': calib()
