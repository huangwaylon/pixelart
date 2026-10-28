"""eyetmpl.py: pure-python M96 eye templates (eye_spec.json). No deps.
kind_tmpl(kind, expr): front_left | front_right (mirror, catchlight keeps its column) | far (SE far eye) | far_left (SW) """
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
    t = SPEC['front_left'][expr_key(expr)]
    if kind == 'front_left': return list(t)
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
    if kind == 'front_left': return list(b['front_left'][e])
    if kind == 'front_right': return [r[::-1] for r in b['front_left'][e]]
    if kind == 'far': return list(b['far'][e])
    if kind == 'far_left': return [r[::-1] for r in b['far'][e]]
    raise KeyError(kind)


FAR_COL = {1: 0, 2: 1, 3: 2, 5: 3, 6: 4, -1: -1, 0: -1}


def wing(kind, expr):
    """cat-eye wing flick px [(dx, dy)] relative to the kind's eye origin (face round 2; eye_spec 'wing')"""
    w = [tuple(p) for p in SPEC.get('wing', {}).get(expr_key(expr), [])]
    if kind == 'front_left': return w
    fr = [(5 - dx, dy) for dx, dy in w]
    if kind == 'front_right': return fr
    if kind == 'far': return [(FAR_COL.get(dx, dx - 2), dy) for dx, dy in fr]
    if kind == 'far_left': return [(3 - dx, dy) for dx, dy in wing('far', expr)]
    raise KeyError(kind)


def all_wings(kind):
    return sorted({p for e in SPEC['front_left'] if not e.startswith('_') for p in wing(kind, e)})


def blush_tmpl(kind, expr):
    b = SPEC['blush'][kind]; return list(b.get(expr_key(expr)) or b['_default'])
