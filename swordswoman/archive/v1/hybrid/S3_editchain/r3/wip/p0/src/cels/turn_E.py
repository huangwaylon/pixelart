# turn_E rig (profile, facing viewer right). Near side = her RIGHT; the katana (her LEFT hand) is the FAR hand:
# the hilt peeks under the near cuff, blade down-forward in front of the skirt. Back tail long on the left.
# Parametric like turn_SE so jump_E keys pose it (body offset, skirt/tail tips, legs, near arm, katana, ribbon).
HEAD = ('E', 48, 43)

DEF = dict(
    body=(0, 0), torso=(0, 0), collar=None, lean=0,
    skirt=dict(top=82, cx=62.5, tw=11, tips=[(51, 96), (57, 98), (65, 98), (71, 95)], slit=(69, 88, 1, 3), shorts=93,
               slope=0.9, wedge=5, sway=0),
    tail=dict(top=84, cx=61, tw=12, tips=[(48, 101), (62, 97)], slope=0.5),
    legs=[((60, 93), (60, 97), (60, 101), 'e', 0)],
    legF=[((64, 93), (65, 97), (65, 100), 'e', 0)],
    armN=dict(upper=((61, 75), (62, 80)), cuff=((62, 78), (61, 90), 4, 11), hand=(63, 90)),
    armF=None,
    katana=(69, 90, 45, 18, 1), kat_layer='back',
    ribbon=[(59, 74), (56, 76), (53, 79), (51, 82), (50, 85), (48, 88), (47, 90)],
    extra={},
)
TORSO = """
69 59 KmssK
70 59 KmssK
71 57 KrRRRRRRRK
72 57 KrRRRRRRRK
73 57 KrRRRRRRRK
74 57 KrRRRRRRRK
75 58 KsssK
76 57 KrRRRRRRRK
77 57 KCRRRRRRRrK
78 57 KCRRRRRRRrK
78 57 KKLLLLLLLKK
79 58 KlllllllK
80 58 KllllllTTK
81 58 KlllllllldK
82 58 KllllllTTK
"""
COLLAR = """
70 55 K
71 55 KCK.......K
72 55 KCRRRRRRRRK
73 55 KCRRRRRRRrK
74 56 KRRRRRRRrK
75 57 KvrrrrrvK
"""
COLLAR_OVER = """
66 54 K
67 54 KK
68 54 KCK
69 54 KCRK
70 55 KCRK
"""


def _off(text, dx, dy):
    out = []
    for ln in text.strip('\n').splitlines():
        y, x, s = ln.split(None, 2)
        out.append(f'{int(y) + dy} {int(x) + dx} {s}')
    return '\n'.join(out)


def _pts(pts): return ' '.join(f'{x},{y}' for x, y in pts)


def _legs(lst):
    return '\n'.join(f"@leg {h[0]},{h[1]} {k[0]},{k[1]} {a[0]},{a[1]} foot={f} fx={fx} shade=r" for h, k, a, f, fx in lst)


def _arm(a):
    if not a: return ''
    t = ''
    if a.get('upper'): t += f"@limb {a['upper'][0][0]},{a['upper'][0][1]},1.6 {a['upper'][1][0]},{a['upper'][1][1]},1.4\n"
    if a.get('sleeve'):
        e_, w_, d_, sw = a['sleeve']; t += f"@sleeve {e_[0]},{e_[1]} {w_[0]},{w_[1]} {d_[0]},{d_[1]} w0={sw}\n"
    else:
        c0, c1, w0, w1 = a['cuff']
        t += f"@cuff {c0[0]},{c0[1]} {c1[0]},{c1[1]} {w0} {w1}\n"
    if a.get('hand'):
        hx, hy = a['hand']; t += f"= {hx} {hy}\n|KssK\n|.KK.\n"
    return t


def make(P):
    p = {k: (v.copy() if isinstance(v, dict) else v) for k, v in DEF.items()}
    for k, v in P.items():
        if isinstance(v, dict) and isinstance(p.get(k), dict) and k != 'extra': p[k].update(v)
        else: p[k] = v
    bx, by = p['body']; tx, ty = p['torso']
    cx_, cy_ = p['collar'] if p['collar'] else (bx + tx, by + ty)
    sk, tl = p['skirt'], p['tail']
    L = {}
    L['tail'] = (f"@skirt top={tl['top'] + by} cx={tl['cx'] + bx} tw={tl['tw']} "
                 f"tips={','.join(f'{x}:{y}' for x, y in tl['tips'])} slope={tl['slope']} wedge=0")
    L['legF'] = _legs(p['legF'])
    L['legs'] = _legs(p['legs'])
    fx_, fy_, ang, ln, hook = p['katana']
    L['katana'] = f"@katana {fx_} {fy_} {ang} {ln} hook={hook}"
    sl = sk.get('slit')
    L['skirt'] = (f"@skirt top={sk['top'] + by} cx={sk['cx'] + bx} tw={sk['tw']} "
                  f"tips={','.join(f'{x}:{y}' for x, y in sk['tips'])} "
                  + (f"slit={sl[0] + bx}:{sl[1] + by}:{sl[2]}:{sl[3]} shorts={sk['shorts'] + by} " if sl else '')
                  + f"slope={sk['slope']} wedge={sk['wedge']} sway={sk.get('sway', 0)}")
    L['torso'] = _off(TORSO, bx + tx, by + ty)
    L['collar'] = _off(COLLAR, cx_, cy_)
    L['collar_over'] = _off(COLLAR_OVER, cx_, cy_)
    L['armN'] = _arm(p['armN'])
    L['armF'] = _arm(p['armF'])
    L['ribbon'] = f"@ribbon {_pts(p['ribbon'])} side=-1 over=0"
    kl = p['kat_layer']
    order = ['tail', 'armF', 'legF'] + (['katana'] if kl == 'back' else []) + ['legs', 'skirt', 'torso', 'collar', 'armN'] \
        + (['katana'] if kl == 'mid' else []) + ['HEAD', 'collar_over', 'ribbon'] + (['katana'] if kl == 'front' else [])
    for nm, (pos, text) in p['extra'].items():
        L[nm] = text
        if pos == 'back': order.insert(0, nm)
        elif pos == 'front': order.append(nm)
        elif pos.startswith('before:'): order.insert(order.index(pos[7:]), nm)
        elif pos.startswith('after:'): order.insert(order.index(pos[6:]) + 1, nm)
    if p.get('lean'):
        pass
    return order, L
SHIFT = (1, 0)
