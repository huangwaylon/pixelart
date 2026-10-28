#!/usr/bin/env python3
"""colorcheck.py: colour-consistency checks for the frame-by-frame pipeline (palette lock, material ramps, flicker, stamps).

Used by lint_style.py / ff_redraw.py (--palette, --master) and animate/tools/post.py (colors). Standalone CLI:
  colorcheck.py legend   PALETTE.json
  colorcheck.py material FRAME.txt [...] --master M.txt [--stamp S.txt] [--palette P.json]   (per-frame ramp-swap lint)
  colorcheck.py stamps   STAMP.txt [...] --master M.txt [--palette P.json]                    (stamp face colours vs master)

Palette JSON (any of these; v2/final/palette.json = char -> hex -> material):
  {"colors": {"K": ["#000000", "outline (all materials), pupils"], ...}}            (pk_palette.json style; materials parsed from text)
  {"colors"|"chars"|"palette": {"K": {"hex": "#000000", "material": "outline" | ["hair","boots"], "desc": ".."}}}
  top-level {"K": {...} | ["#hex", "material text"]}   or a list of {"char","hex","material"}
  optional "materials": {"hair": "LHh", "bow": ["e","E"], ...} replaces the ramps of the listed materials.
Material words recognised in text: hair, skin, dress (red/kimono/sleeve/skirt/shoulder), bow (ribbon; 'red' = dress+bow),
obi (sash/belt), boots (boot/shoe/sole), eyes (eye/iris/pupil/lash/glint), blade (katana/guard/sword); 'outline'/'all
materials' = universal char (allowed in every material, ignored by the ramp lint).
"""
import json, os, re, sys
from collections import Counter, deque

KEYWORDS = [  # regex on description text -> materials
    (r'\boutline|all materials', ('outline',)),
    (r'\bhair|\bbang|braid|ponytail', ('hair',)),
    (r'\bskin|\bmouth|\bblush|\bcheek', ('skin',)),
    (r'\bred\b', ('dress', 'bow')),
    (r'\bdress|kimono|sleeve|skirt|shoulder|\btop\b|haori', ('dress',)),
    (r'\bbow\b|ribbon', ('bow',)),
    (r'\bobi\b|\bsash|\bbelt', ('obi',)),
    (r'\bboot|\bshoe|\bsole', ('boots',)),
    (r'\beye|\biris|\bpupil|\blash|\bglint', ('eyes',)),
    (r'\bblade|katana|\bguard|\bsword|\bhilt', ('blade',)),
]
UNIVERSAL = {'outline', 'all'}


def parse_materials(text):
    t = str(text).lower(); out = []
    for rx, ms in KEYWORDS:
        if re.search(rx, t): out += [m for m in ms if m not in out]
    return out


class Palette:
    """chars -> (hex, desc, materials); ramps = material -> chars (palette order); univ = universal chars (outline)."""

    def __init__(self, path):
        self.path = os.path.abspath(path); d = json.load(open(path))
        ent = None
        if isinstance(d, list): ent = {e['char']: e for e in d}
        else:
            for k in ('colors', 'chars', 'palette'):
                if isinstance(d.get(k), (dict, list)): ent = d[k]; break
            if ent is None: ent = {k: v for k, v in d.items() if len(k) == 1}
            if isinstance(ent, list): ent = {e['char']: e for e in ent}
        self.colors = {}; self.mats = {}
        for c, v in ent.items():
            if isinstance(v, str): hx, desc, mat = v, '', None
            elif isinstance(v, (list, tuple)): hx, desc, mat = v[0], (v[1] if len(v) > 1 else ''), (v[2] if len(v) > 2 else None)
            else:
                hx = v.get('hex') or v.get('color') or v.get('rgb'); mat = v.get('material', v.get('materials'))
                desc = v.get('desc') or v.get('role') or v.get('note') or ''
            if isinstance(mat, str): ms = parse_materials(mat) or [re.sub(r'[^a-z_]+', '_', mat.lower()).strip('_')]
            elif isinstance(mat, (list, tuple)): ms = [m2 for m in mat for m2 in (parse_materials(m) or [str(m).lower()])]
            else: ms = parse_materials(desc)
            ms = list(dict.fromkeys(ms))
            self.colors[c] = [hx, desc or ', '.join(ms)]; self.mats[c] = set(ms)
        if isinstance(d, dict) and isinstance(d.get('materials'), dict):  # explicit ramp table overrides
            over = {m.lower() for m in d['materials']}
            for c in self.mats: self.mats[c] -= over  # listed materials are replaced, others kept
            for m, cs in d['materials'].items():
                cs = cs.get('chars', cs.get('ramp', '')) if isinstance(cs, dict) else cs
                for c in cs:
                    if c in self.mats: self.mats[c].add(m.lower())
        self.univ = {c for c, ms in self.mats.items() if ms & UNIVERSAL}
        self.ramps = {}
        for c, ms in self.mats.items():
            for m in ms:
                if m not in UNIVERSAL: self.ramps.setdefault(m, []).append(c)
        self.eyes = set(self.ramps.get('eyes', [])) - self.univ
        self.rgb = {k: tuple(int(v[0][j:j + 2], 16) for j in (1, 3, 5)) for k, v in self.colors.items()}

    def m(self, c):  # ramp materials of a char ({} for universal/unknown/transparent)
        return set() if c in self.univ else {x for x in self.mats.get(c, ()) if x not in UNIVERSAL}

    def legend(self):
        L = ['%s %s %s  [material: %s]' % (c, v[0], v[1], '/'.join(sorted(self.mats[c])) or '?') for c, v in self.colors.items()]
        L.append('MATERIAL RAMPS (a material may only use its own chars%s):' % (
            ('; ' + ' '.join(sorted(self.univ)) + ' = outline, allowed everywhere') if self.univ else ''))
        L += ['  %-7s %s' % (m, ' '.join(cs)) for m, cs in self.ramps.items()]
        return '\n'.join(L)

    def ramp_str(self, label):
        return ' '.join(c for c in self.colors if self.m(c) & set(label))


_PAL = {}
def load(path):
    p = os.path.abspath(path)
    if p not in _PAL: _PAL[p] = Palette(p)
    return _PAL[p]


def read(path):
    g, meta = [], {}
    for l in open(path):
        l = l.rstrip('\n')
        if l.startswith(';'):
            p = l[1:].split()
            if p: meta[p[0]] = [int(v) if v.lstrip('-').isdigit() else v for v in p[1:]]
        elif l.strip(): g.append(l)
    w = max(len(l) for l in g) if g else 0
    return [l.ljust(w, '.') for l in g], meta


# ---------------- palette lock ----------------
def off_palette(g, pal):
    bad = [(x, y, c) for y, r in enumerate(g) for x, c in enumerate(r) if c != '.' and c not in pal.colors]
    if not bad: return []
    return ['PAL %d off-palette pixels (locked palette %s): chars %s at %s; use only the legend chars' % (
        len(bad), os.path.basename(pal.path), sorted({b[2] for b in bad}), [b[:2] for b in bad[:10]])]


# ---------------- material components ----------------
N4 = ((1, 0), (-1, 0), (0, 1), (0, -1))


def components(g, pal):
    """4-connected regions of non-outline pixels whose neighbours share a ramp material. -> (lab grid, comps)."""
    H, W = len(g), len(g[0]); lab = [[-1] * W for _ in range(H)]; comps = []
    for y in range(H):
        for x in range(W):
            c = g[y][x]
            if c == '.' or lab[y][x] >= 0 or not pal.m(c): continue
            k = len(comps); lab[y][x] = k; q = deque([(x, y)]); px = []
            while q:
                a, b = q.popleft(); px.append((a, b)); ma = pal.m(g[b][a])
                for dx, dy in N4:
                    X, Y = a + dx, b + dy
                    if 0 <= X < W and 0 <= Y < H and lab[Y][X] < 0 and g[Y][X] != '.' and pal.m(g[Y][X]) & ma:
                        lab[Y][X] = k; q.append((X, Y))
            cnt = Counter(m for a, b in px for m in pal.m(g[b][a])); top = max(cnt.values())
            xs, ys = [p[0] for p in px], [p[1] for p in px]
            comps.append({'px': px, 'n': len(px), 'chars': Counter(g[b][a] for a, b in px),
                          'label': tuple(sorted(m for m, v in cnt.items() if v == top)),
                          'mats': set(cnt), 'bbox': (min(xs), min(ys), max(xs), max(ys)),
                          'cen': (sum(xs) / len(px), sum(ys) / len(px))})
    return lab, comps


SMALL = 12  # regions below this size need an enclosure precedent in the master


def enclosed(g, pal, lab, comps, frac=0.6, rel=0.5, small=SMALL):
    """components mostly surrounded by ONE other component of a disjoint material -> [(C, D)]."""
    H, W = len(g), len(g[0]); out = []
    for k, C in enumerate(comps):
        nb = Counter()
        seen = set()
        for a, b in C['px']:
            for dx, dy in N4:
                X, Y = a + dx, b + dy
                if 0 <= X < W and 0 <= Y < H and (X, Y) not in seen and lab[Y][X] >= 0 and lab[Y][X] != k:
                    seen.add((X, Y)); nb[lab[Y][X]] += 1
        if not nb: continue
        d, v = nb.most_common(1)[0]; D = comps[d]
        if v < frac * sum(nb.values()) or C['n'] > max(small, rel * D['n']): continue
        if C['mats'] & set(D['label']): continue
        out.append((C, D))
    return out


def anchor(g, st):
    """best offset of a stamp in g -> (matched, total, ox, oy): by its face (eyes+lash, lint_style.find_stamp) when the
    stamp has eye pixels, else (closed-eye expressions) by all its opaque pixels (numpy)."""
    import lint_style as LS
    face, _ = LS.stamp_info(st)
    if face: return LS.find_stamp(g, st, face)
    import numpy as np
    H, W = len(g), len(g[0]); h, w = len(st), len(st[0])
    A = np.full((H + 2 * h, W + 2 * w), '.', dtype='<U1'); A[h:h + H, w:w + W] = np.array([list(r) for r in g])
    M = np.zeros((H + h + 1, W + w + 1), int); pts = [(x, y, c) for y, r in enumerate(st) for x, c in enumerate(r) if c != '.']
    for x, y, c in pts: M += A[y:y + H + h + 1, x:x + W + w + 1] == c
    oy, ox = np.unravel_index(M.argmax(), M.shape)
    return int(M.max()), len(pts), int(ox) - w, int(oy) - h


def head_box(g, stamp):
    """frame-coords bbox of the head stamp (matched by its face / whole stamp), or None."""
    if not stamp: return None
    m, n, ox, oy = anchor(g, stamp)
    if m < 0.5 * n: return None
    return (ox, oy, ox + len(stamp[0]) - 1, oy + len(stamp) - 1)


def zone(C, hb):
    x, y = C['cen']
    return 'head' if hb and hb[0] <= x <= hb[2] and hb[1] <= y <= hb[3] else 'body'


def allowed_from(g, pal, stamp=None):
    """{(char, neighbour-region label, zone): largest such neighbour region size} for adjacencies present in the master
    (or a stamp) = allowed; ('in', char, label, zone) = char used inside a region of that material."""
    lab, comps = components(g, pal); H, W = len(g), len(g[0])
    hb = head_box(g, stamp) if stamp is not None else (0, 0, W - 1, H - 1); out = {}
    inb = lambda a, b: 'head' if hb and hb[0] <= a <= hb[2] and hb[1] <= b <= hb[3] else 'body'
    for k, C in enumerate(comps):
        for a, b in C['px']:
            z = inb(a, b)
            for dx, dy in N4:
                X, Y = a + dx, b + dy
                if 0 <= X < W and 0 <= Y < H and lab[Y][X] >= 0 and lab[Y][X] != k:
                    D = comps[lab[Y][X]]; key = (g[b][a], D['label'], z if inb(X, Y) == z else 'body')  # head = both px in the box
                    out[key] = max(out.get(key, 0), D['n'])
            out[('in', g[b][a], C['label'], z)] = 1  # char used inside a region of that material
    for C, D in enclosed(g, pal, lab, comps, rel=1e9):  # enclosure precedents (any size)
        for c in C['chars']: out[('enc', c, D['label'], zone(C, hb))] = 1
    return out


def material_lint(g, pal, master=None, stamp=None, allow=None):
    """ramp-swap fix lines: a small region whose material differs from the ONE material area surrounding it (>=60% of
    its non-outline border), unless the master has one of its chars touching that material in the same zone (head stamp
    box vs body) and all its chars belong to its own ramp. master/stamp = grids."""
    if allow is None:
        allow = {}
        for src in ([(master, stamp)] if master else []) + ([(stamp, None)] if stamp else []):
            for k, v in allowed_from(src[0], pal, src[1]).items(): allow[k] = max(allow.get(k, 0), v)  # whole stamp = head zone (e.g. mouth/blush in skin)
    lab, comps = components(g, pal); hb = head_box(g, stamp); fx = []
    for C in comps:  # foreign chars inside a region (joined through a shared char, e.g. hair H in a boot via h)
        z = zone(C, hb); lb = set(C['label'])
        bad = [c for c in C['chars'] if not (pal.m(c) & lb) and ('in', c, C['label'], z) not in allow]
        if bad:
            pts = [(x, y) for x, y in C['px'] if g[y][x] in bad]
            fx.append('MAT ramp swap [%s]: %d px of %s (%s colours) inside the %s area at %s, not seen in the master; %s may only use its own ramp: %s' % (
                z, len(pts), ''.join(sorted(bad)), '/'.join(sorted({m for c in bad for m in pal.m(c)})), '/'.join(C['label']), pts[:8], '/'.join(C['label']), pal.ramp_str(C['label'])))
    for C, D in enclosed(g, pal, lab, comps):
        z = zone(C, hb)
        # allowed if the master has the same enclosure (one of these chars inside D's material, same zone), or - for
        # regions >= SMALL px - one of these chars touching a comparable (>=1/4 size) region of D's material
        prec = any(('enc', c, D['label'], z) in allow for c in C['chars']) or (
            C['n'] >= SMALL and any(allow.get((c, D['label'], z), 0) >= 0.25 * D['n'] for c in C['chars']))
        if prec and all(pal.m(c) & set(C['label']) for c in C['chars']): continue
        cm = '/'.join(sorted(C['mats']))
        fx.append('MAT ramp swap [%s]: %d px of %s (%s colours) inside the %s area at (%d,%d)-(%d,%d), not seen in the master; %s may only use its own ramp: %s' % (
            z, C['n'], ''.join(sorted(C['chars'])), cm, '/'.join(D['label']), *C['bbox'], '/'.join(D['label']), pal.ramp_str(D['label'])))
    return fx


# ---------------- expression stamps ----------------
def face_rect(st, eyes):
    pts = [(x, y) for y, r in enumerate(st) for x, c in enumerate(r) if c in eyes]
    if not pts: return None
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    return (max(0, min(xs) - 2), max(0, min(ys) - 2), min(len(st[0]) - 1, max(xs) + 2), len(st) - 1)


def master_window(master, st, meta, ref=None):
    """master region under the stamp: via '; origin X Y' meta, else by matching ref (neutral stamp) / the stamp face."""
    import lint_style as LS
    h, w = len(st), len(st[0])
    if 'origin' in meta: ox, oy = meta['origin'][:2]
    else:
        r = ref or st; face, _ = LS.stamp_info(r); _, _, ox, oy = LS.find_stamp(master, r, face)
    return [''.join(master[y][x] if 0 <= y < len(master) and 0 <= x < len(master[0]) else '.' for x in range(ox, ox + w))
            for y in range(oy, oy + h)]


def stamp_check(path, master, pal=None, eyes=None):
    """issues for one expression stamp: off-palette chars, face colours not used in the master's face, head colours
    not in the master head."""
    import lint_style as LS
    st, meta = read(path); eyes = eyes or (pal.eyes if pal and pal.eyes else LS.EYE); iss = []
    if pal: iss += off_palette(st, pal)
    d = os.path.dirname(path); b = os.path.basename(path); ref = None
    v = re.match(r'(?:stamp_)?([A-Z]+)_', b)
    if v and os.path.exists(os.path.join(d, v.group(1) + '_neutral.txt')): ref = read(os.path.join(d, v.group(1) + '_neutral.txt'))[0]
    mw = master_window(master, st, meta, ref)
    fr = face_rect(ref or mw, eyes) or face_rect(st, eyes)
    if not fr: return iss + ['STAMP no eye pixels (%s) found' % ''.join(sorted(eyes))]
    x0, y0, x1, y1 = fr
    mface = {mw[y][x] for y in range(y0, y1 + 1) for x in range(x0, x1 + 1)} - {'.'}
    mhead = {c for r in mw for c in r} - {'.'}
    bad = [(x, y, st[y][x]) for y in range(y0, min(y1 + 1, len(st))) for x in range(x0, min(x1 + 1, len(st[0]))) if st[y][x] not in mface | {'.'}]
    if bad:
        nm = lambda c: (pal.colors[c][1] if pal and c in pal.colors else c)
        iss.append('FACE %d px use colours not in the master face %s: %s at %s' % (
            len(bad), ''.join(sorted(mface)), ', '.join("%s (%s)" % (c, nm(c)) for c in sorted({q[2] for q in bad})), [q[:2] for q in bad[:10]]))
    extra = ({c for r in st for c in r} - {'.'}) - mhead
    if extra: iss.append('HEADCOL stamp uses colours absent from the master head: %s' % ''.join(sorted(extra)))
    return iss


# ---------------- clip flicker ----------------
def regions(g, pal, low=None):
    """stable regions of a frame: obi (obi-labelled comps above the boots zone), boots (obi/boots comps in the bottom 10
    rows above the lowest opaque row; left/right by x). -> {'obi': [px..], 'bootL': .., 'bootR': ..}"""
    lab, comps = components(g, pal)
    if low is None: low = max((y for y, r in enumerate(g) if r.strip('.')), default=len(g) - 1)
    has = lambda C, m: m in C['label'] or (m in C['mats'] and C['n'] >= 3)
    boots = [C for C in comps if 'boots' in pal.ramps and has(C, 'boots') and C['bbox'][1] >= low - 10 and 'hair' not in C['label']]
    obi = [C for C in comps if 'obi' in pal.ramps and has(C, 'obi') and C not in boots and C['n'] >= 4 and 'hair' not in C['label']]
    out = {}
    if obi: out['obi'] = [p for C in obi for p in C['px']]
    boots.sort(key=lambda C: C['cen'][0])
    if boots:
        # merge comps into two boots by x gap
        xs = sorted(boots, key=lambda C: C['cen'][0]); gaps = [xs[i + 1]['bbox'][0] - xs[i]['bbox'][2] for i in range(len(xs) - 1)]
        cut = gaps.index(max(gaps)) + 1 if gaps and max(gaps) > 1 else len(xs)
        out['bootL'] = [p for C in xs[:cut] for p in C['px']]
        if cut < len(xs): out['bootR'] = [p for C in xs[cut:] for p in C['px']]
    return out


def hist(g, px): return Counter(g[y][x] for x, y in px)


def l1(a, b):
    na, nb = sum(a.values()) or 1, sum(b.values()) or 1
    return sum(abs(a[k] / na - b[k] / nb) for k in set(a) | set(b))


def rel_grid(g, px):
    if not px: return {}
    x0, y0 = min(p[0] for p in px), min(p[1] for p in px)
    return {(x - x0, y - y0): g[y][x] for x, y in px}


def clip_report(G, pal, stamps=None, keys=None, loop=True, head_px=3, hist_t=0.2, region_px=4, shape_t=0.25, name='clip'):
    """G: list of frame grids; stamps: per-frame stamp grids (expression) or None. Returns (text, data dict)."""
    import lint_style as LS
    n = len(G); keys = keys or ['f%02d' % i for i in range(n)]; flags = []; F = []
    for i, g in enumerate(G):
        st = stamps[i] if stamps else None; f = {'i': i, 'key': keys[i], 'hist': Counter(c for r in g for c in r if c != '.')}
        if pal: f['offpal'] = off_palette(g, pal)
        if st:
            m, nn, ox, oy = anchor(g, st); f['anchor'] = (ox, oy); f['face_match'] = (m, nn)
            win = [''.join(g[y][x] if 0 <= y < len(g) and 0 <= x < len(g[0]) else '.' for x in range(ox, ox + len(st[0])))
                   for y in range(oy, oy + len(st))]
            f['head'] = win
            smats = set().union(*[pal.m(c) for r in st for c in r]) if pal else set()
            occ = lambda c: pal is not None and c != '.' and pal.m(c) and not (pal.m(c) & smats)
            dr = [(x, y, st[y][x], win[y][x]) for y in range(len(st)) for x in range(len(st[0]))
                  if st[y][x] != '.' and win[y][x] != '.' and win[y][x] != st[y][x] and not occ(win[y][x])]
            f['drift'] = dr
            if len(dr) > head_px: flags.append('%s HEAD %d px recoloured vs its stamp (anchor %s): %s' % (keys[i], len(dr), (ox, oy), ', '.join('(%d,%d) %s->%s' % q for q in dr[:8])))
        f['reg'] = {k: (hist(g, px), rel_grid(g, px), len(px)) for k, px in (regions(g, pal).items() if pal else [])}
        if f.get('offpal'): flags += ['%s %s' % (keys[i], x) for x in f['offpal']]
        F.append(f)
    pairs = [(i, i + 1) for i in range(n - 1)] + ([(n - 1, 0)] if loop and n > 2 else [])
    D = []
    for i, j in pairs:
        a, b = F[i], F[j]; d = {'pair': '%02d-%02d' % (i, j)}
        if 'head' in a and 'head' in b and len(a['head']) == len(b['head']) and len(a['head'][0]) == len(b['head'][0]):
            si, sj = stamps[i], stamps[j]
            same_shape = len(si) == len(sj) and len(si[0]) == len(sj[0])
            exp = {(x, y) for y in range(len(si)) for x in range(len(si[0])) if same_shape and si[y][x] != sj[y][x]}
            ch = [(x, y, a['head'][y][x], b['head'][y][x]) for y in range(len(si)) for x in range(len(si[0]))
                  if a['head'][y][x] != '.' and b['head'][y][x] != '.' and a['head'][y][x] != b['head'][y][x] and (x, y) not in exp
                  and si[y][x] != '.']
            d.update(head_change=len(ch), expr_delta=len(exp), head_hist_l1=round(l1(hist(a['head'], [(x, y) for y in range(len(si)) for x in range(len(si[0])) if si[y][x] != '.']),
                                                                                       hist(b['head'], [(x, y) for y in range(len(si)) for x in range(len(si[0])) if si[y][x] != '.'])), 3))
            if len(ch) > head_px:
                flags.append('%s->%s HEAD %d px change colour beyond the expression delta (%d px) after aligning on the head anchor %s->%s: %s' % (
                    keys[i], keys[j], len(ch), len(exp), a['anchor'], b['anchor'], ', '.join('(%d,%d) %s->%s' % q for q in ch[:8])))
        for k in sorted(set(a['reg']) & set(b['reg'])):
            (ha, ga, na), (hb, gb, nb) = a['reg'][k], b['reg'][k]
            shape = abs(na - nb) / max(na, nb, 1); h1 = l1(ha, hb)
            newc = {c for c in hb if hb[c] >= 2 and c not in ha} | {c for c in ha if ha[c] >= 2 and c not in hb}
            pp = sum(1 for p in set(ga) & set(gb) if ga[p] != gb[p]) if shape <= shape_t else None
            d[k] = {'px': [na, nb], 'hist_l1': round(h1, 3), 'pix_change': pp, 'new_colours': ''.join(sorted(newc))}
            pose = shape > shape_t
            if newc: flags.append('%s->%s %s colour set changes (%s) %s->%s' % (keys[i], keys[j], k, ''.join(sorted(newc)), dict(ha), dict(hb)))
            elif not pose and (h1 > hist_t or (pp or 0) > region_px):
                flags.append('%s->%s %s colours change without a shape change (size %d->%d): hist L1 %.2f, %s px recoloured; %s -> %s' % (
                    keys[i], keys[j], k, na, nb, h1, pp, dict(ha), dict(hb)))
        # transient colours: a char only in this frame (>=2 px) and in neither neighbour
        D.append(d)
    for i in range(n):
        nbs = [F[(i - 1) % n]['hist'], F[(i + 1) % n]['hist']] if (loop or 0 < i < n - 1) else [F[i - 1]['hist'] if i else F[1]['hist'] if n > 1 else Counter()]
        tr = [c for c, v in F[i]['hist'].items() if v >= 2 and all(c not in h for h in nbs)]
        if tr and n > 1: flags.append('%s transient colour(s) %s (only in this frame, %s px)' % (keys[i], ''.join(tr), [F[i]['hist'][c] for c in tr]))
    L = ['COLOR REPORT %s: %d frames%s; thresholds head_px %d, hist_l1 %.2f, region_px %d, shape %.2f; palette %s' % (
        name, n, ' (loop)' if loop else '', head_px, hist_t, region_px, shape_t, pal.path if pal else '-')]
    for f in F:
        s = '%02d %-14s %2d colours' % (f['i'], f['key'], len(f['hist']))
        if 'anchor' in f: s += ' | head anchor %s face %d/%d drift %d' % (f['anchor'], f['face_match'][0], f['face_match'][1], len(f['drift']))
        for k, (h, _, npx) in sorted(f['reg'].items()): s += ' | %s %dpx %s' % (k, npx, ''.join('%s%d' % kv for kv in sorted(h.items())))
        L.append(s)
    for d in D:
        s = 'd' + d['pair']
        if 'head_change' in d: s += ' head %d px (expr delta %d, hist L1 %.2f)' % (d['head_change'], d['expr_delta'], d['head_hist_l1'])
        for k in ('obi', 'bootL', 'bootR'):
            if k in d: s += ' | %s L1 %.2f px %s%s' % (k, d[k]['hist_l1'], d[k]['pix_change'] if d[k]['pix_change'] is not None else 'shape', (' new ' + d[k]['new_colours']) if d[k]['new_colours'] else '')
        L.append(s)
    L.append('FLAGS (%d):' % len(flags)); L += ['- ' + x for x in flags] or ['- none']
    data = {'name': name, 'frames': [{'i': f['i'], 'key': f['key'], 'hist': dict(f['hist']), 'anchor': f.get('anchor'),
                                      'drift': len(f.get('drift', [])), 'regions': {k: dict(v[0]) for k, v in f['reg'].items()}} for f in F],
            'pairs': D, 'flags': flags}
    return '\n'.join(L) + '\n', data


if __name__ == '__main__':
    a = sys.argv[1:]; cmd = a.pop(0)
    def opt(k):
        if k not in a: return None
        i = a.index(k); v = a[i + 1]; del a[i:i + 2]; return v
    P = opt('--palette'); M = opt('--master'); S = opt('--stamp')
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import lint_style as LS
    pal = load(P or LS.PAL_PATH); bad = 0
    if cmd == 'legend': print(load(a[0]).legend()); sys.exit()
    master = read(M)[0] if M else None
    for f in a:
        if cmd == 'material': iss = material_lint(read(f)[0], pal, master, read(S)[0] if S else None)
        elif cmd == 'stamps': iss = stamp_check(f, master, pal)
        print(('OK   ' if not iss else 'FAIL ') + f); [print('   ', x) for x in iss]; bad += bool(iss)
    sys.exit(1 if bad else 0)
