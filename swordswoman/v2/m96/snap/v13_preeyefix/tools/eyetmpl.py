"""eyetmpl.py: pure-python M96 eye templates (eye_spec.json). No deps.
kind_tmpl(kind, expr): front_left | profile (E; kind_override.profile else front_left) | front_right (mirror, catchlight keeps its column) | far (SE far eye) | far_left (SW) """
import os, json
SPEC = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'eye_spec.json')))


def expr_key(e): return SPEC['aliases'].get(e, e)


def mirror(t):
    """mirror the lash/wing geometry only: rows that contain iris chars keep their iris span (cols 1..4 for the 6-wide block)
    unmirrored, so the pupil + catchlight sit at the same screen-space spot in both eyes"""
    out = []
    for r in t:
        m = list(r[::-1])
        if any(c in 'hgL@' for c in r) and len(r) == 6:
            m[1:5] = list(r[1:5])
            if r[0] == 'K' and m[5] == '.': pass
        out.append(''.join(m))
    return out


def canonical(t): return list(t)


def kind_tmpl(kind, expr):
    ko = SPEC.get('kind_override', {}).get(kind, {}).get(expr_key(expr))
    if ko: return list(ko)
    t = SPEC['front_left'][expr_key(expr)]
    if kind in ('front_left', 'profile'): return list(t)
    if kind == 'front_right': return list(SPEC.get('front_right_override', {}).get(expr_key(expr)) or mirror(t))
    if kind == 'far':
        t = [''.join(r[i] for i in (1, 2, 3, 5)) for r in kind_tmpl('front_right', expr)]
        if not SPEC.get('far_lower_lash', True) and t[4][3] in 'Kh' and t[3][3] == '.': t[4] = t[4][:3] + '.'   # SE far eye: no lower lash (cheek edge)
        return t
    if kind == 'far_left': return mirror(kind_tmpl('far', expr))
    raise KeyError(kind)


def brow_tmpl(kind, expr):
    """2-row brow template (rows lash-3, lash-2) for an eye kind; front_right / far_left are plain mirrors"""
    b = SPEC['brow']; e = expr_key(expr)
    if kind in ('front_left', 'profile'): return list(b['front_left'][e])
    if kind == 'front_right': return [r[::-1] for r in b['front_left'][e]]
    if kind == 'far': return list(b['far'][e])
    if kind == 'far_left': return [r[::-1] for r in b['far'][e]]
    raise KeyError(kind)


FAR_COL = {1: 0, 2: 1, 3: 2, 5: 3, 6: 4, -1: -1, 0: -1}


def wing_px(kind, expr):
    """outer lash flick px [(dx, dy, char)] relative to the kind's eye origin (eye_spec 'wing' entries [dx, dy] or [dx, dy, char], default K;
    per-kind lists in 'wing_override'[kind]; the SE far eye keeps only K flicks (they land on the cheek outline))"""
    e = expr_key(expr); wo = SPEC.get('wing_override', {})
    if kind in wo and e in wo[kind]: return [(p[0], p[1], p[2] if len(p) > 2 else 'K') for p in wo[kind][e]]
    w = [(p[0], p[1], p[2] if len(p) > 2 else 'K') for p in SPEC.get('wing', {}).get(e, [])]
    if kind in ('front_left', 'profile'): return w
    fr = [(5 - dx, dy, c) for dx, dy, c in w]
    if kind == 'front_right': return fr
    if kind == 'far':
        # eye round: the far block (fr cols 1,2,3,5) drops fr col 0 = an arched lid's inner-corner drop (if any) -> outside px at far col -1
        inner = [(-1, j, 'K') for j, r in enumerate(kind_tmpl('front_right', expr)) if r[0] == 'K'] if SPEC.get('far_inner_drop', True) else []
        return [(FAR_COL.get(dx, dx - 2), dy, c) for dx, dy, c in fr if c == 'K'] + inner
    if kind == 'far_left': return [(3 - dx, dy, c) for dx, dy, c in wing_px('far', expr)]
    raise KeyError(kind)


def wing(kind, expr):
    """flick positions [(dx, dy)] (see wing_px for the chars)"""
    return [(dx, dy) for dx, dy, c in wing_px(kind, expr)]


def all_wings(kind):
    return sorted({p for e in SPEC['front_left'] if not e.startswith('_') for p in wing(kind, e)})


def blush_tmpl(kind, expr):
    b = SPEC['blush'][kind]; return list(b.get(expr_key(expr)) or b['_default'])
