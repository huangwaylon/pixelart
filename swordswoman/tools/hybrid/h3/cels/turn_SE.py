# turn_SE rig (3/4 front, facing viewer-right-down). Hand-typed torso / collar grids ride integer offsets; skirt,
# tail, cuffs, legs, katana and ribbons are parametric so the anim keys can pose them. Near side = her RIGHT
# (viewer left); the katana (her LEFT hand) is on the far side (viewer right). Body centre +1 px right of the head,
# buckles 2 px right of the body centre.
HEAD = ('SE', 52, 43)
SHIFT = (-1, 0)

DEF = dict(
    body=(0, 0),            # whole-body offset (torso, collar, arms roots, skirt, tail)
    torso=(0, 0),           # extra torso offset (twist / lean)
    collar=None,            # collar offset (default = body + torso)
    skirt=dict(top=82, cx=64.5, tw=14, tips=[(51, 95), (57, 98), (68, 98), (77, 95)], slit=(66, 88, 2, 2),
               shorts=93, slope=0.9, wedge=5, sway=0),
    tail=dict(top=86, cx=63, tw=20, tips=[(46, 101), (79, 99)], slope=0.45),
    legs=[((61, 93), (60, 97), (60, 101), 'se', 0), ((69, 93), (69, 97), (69, 100), 'sef', 0)],
    armN=dict(cuff=((55.5, 76), (53.5, 90), 5, 10), hand=(52, 90), upper=None),
    armF=dict(cuff=((73, 78), (75, 89), 4, 8), upper=((72, 75), (73, 79))),
    katana=(76, 90, 63.4, 21, 1),
    kat_layer='back',        # back: behind legs/skirt (far hand) | front: over everything but the head
    ribbonN=[(58, 75), (55, 77), (52, 79), (50, 82), (50, 85), (48, 88), (48, 91)],
    ribbonF=[(71, 74), (75, 76), (78, 79), (79, 83), (78, 86), (80, 89)],
    extra={},               # name -> (position, text)
)

TORSO = """
69 61 KmssmK
70 61 KmssmK
71 57 KrRRRRRRRRRRrK
72 57 KrRRRRRRRRRRrK
73 57 KrRRRRRRRRRRrK
74 57 KrRRRRRRRRRRrK
75 58 KRRRRRRRRRrK
74 54 KSss
75 53 KSsss
76 53 KSssKrRRRRRRRRRRRrK
77 53 KSssKCRRRRRRRRRRrrK
78 57 KCRRRRRRRRRRrrK
78 58 KKLLLLLLLLLLKK
79 59 KllllllllllK
80 59 KlllllllKTTK
81 59 KllllllllddK
82 59 KlllllllKTTK
"""
COLLAR = """
71 56 KCRRRRRRRRRRRrK
72 56 KCRRRRRvvvvRRrK
73 57 KCRRRRRRRRRRrK
74 57 KrRRRRRRRRRrK
75 58 KvrrrrrrrrvK
"""
COLLAR_OVER = """
66 54 K
67 54 KCK
68 54 KCRK
69 55 KCRK
70 55 KCRRK
67 72 K
68 71 KrK
69 70 KRrK
70 69 KRrK
"""


def _off(text, dx, dy):
    """shift a row-format text block"""
    out = []
    for ln in text.strip('\n').splitlines():
        y, x, s = ln.split(None, 2)
        out.append(f'{int(y) + dy} {int(x) + dx} {s}')
    return '\n'.join(out)


def _pts(pts, dx=0, dy=0):
    return ' '.join(f'{x + dx},{y + dy}' for x, y in pts)


def make(P):
    p = {k: (v.copy() if isinstance(v, dict) else v) for k, v in DEF.items()}
    for k, v in P.items():
        if isinstance(v, dict) and isinstance(p.get(k), dict) and k != 'extra': p[k].update(v)
        else: p[k] = v
    bx, by = p['body']; tx, ty = p['torso']
    cx_, cy_ = p['collar'] if p['collar'] else (bx + tx, by + ty)
    sk = p['skirt']; tl = p['tail']
    L = {}
    L['tail'] = (f"@skirt top={tl['top'] + by} cx={tl['cx'] + bx} tw={tl['tw']} "
                 f"tips={','.join(f'{x + bx}:{y}' for x, y in tl['tips'])} slope={tl['slope']} wedge=0")
    L['legs'] = '\n'.join(f"@leg {h[0]},{h[1]} {k[0]},{k[1]} {a[0]},{a[1]} foot={f} fx={fx} shade=r"
                          for h, k, a, f, fx in p['legs'])
    sl = sk.get('slit')
    L['skirt'] = (f"@skirt top={sk['top'] + by} cx={sk['cx'] + bx} tw={sk['tw']} "
                  f"tips={','.join(f'{x + bx}:{y}' for x, y in sk['tips'])} "
                  + (f"slit={sl[0] + bx}:{sl[1] + by}:{sl[2]}:{sl[3]} shorts={sk['shorts'] + by} " if sl else '')
                  + f"slope={sk['slope']} wedge={sk['wedge']} sway={sk.get('sway', 0)}")
    L['torso'] = _off(TORSO, bx + tx, by + ty)
    a = p['armN']; (c0, c1, w0, w1) = a['cuff'] or ((0, 0), (0, 0), 0, 0)
    t = ''
    if a.get('upper'): t += f"@limb {a['upper'][0][0]},{a['upper'][0][1]},1.5 {a['upper'][1][0]},{a['upper'][1][1]},1.3\n"
    if a.get('sleeve'):
        e_, w_, d_, sw = a['sleeve']; t += f"@sleeve {e_[0]},{e_[1]} {w_[0]},{w_[1]} {d_[0]},{d_[1]} w0={sw}\n"
    else:
        t += f"@cuff {c0[0]},{c0[1]} {c1[0]},{c1[1]} {w0} {w1}\n"
    if a.get('hand'):
        hx, hy = a['hand']; t += f"= {hx} {hy}\n|KssK\n|.KK.\n"
    L['armN'] = t
    a = p['armF']; (c0, c1, w0, w1) = a['cuff'] or ((0, 0), (0, 0), 0, 0)
    t = ''
    if a.get('upper'): t += f"@limb {a['upper'][0][0]},{a['upper'][0][1]},1.5 {a['upper'][1][0]},{a['upper'][1][1]},1.3\n"
    if a.get('sleeve'):
        e_, w_, d_, sw = a['sleeve']; t += f"@sleeve {e_[0]},{e_[1]} {w_[0]},{w_[1]} {d_[0]},{d_[1]} w0={sw}\n"
    else:
        t += f"@cuff {c0[0]},{c0[1]} {c1[0]},{c1[1]} {w0} {w1}\n"
    L['armR'] = t
    fx_, fy_, ang, ln, hook = p['katana']
    L['katana'] = f"@katana {fx_} {fy_} {ang} {ln} hook={hook}"
    L['collar'] = _off(COLLAR, cx_, cy_)
    L['collar_over'] = _off(COLLAR_OVER, cx_, cy_)
    L['ribbonF'] = f"@ribbon {_pts(p['ribbonF'])} side=1 over=0"
    rn = p['ribbonN']
    L['ribbonN'] = f"@ribbon {_pts(rn)} side=-1 over=0\n{rn[0][1] - 1} {rn[0][0]} PK\n{rn[0][1]} {rn[0][0] - 1} pP"
    order = ['tail', 'ribbonF', 'armR'] + (['katana'] if p['kat_layer'] == 'back' else []) + \
            ['legs', 'skirt', 'torso', 'armL'] + (['katana'] if p['kat_layer'] == 'mid' else []) + \
            ['collar', 'HEAD', 'collar_over', 'ribbonN'] + (['katana'] if p['kat_layer'] == 'front' else [])
    L['armL'] = L.pop('armN')
    for nm, (pos, text) in p['extra'].items():
        L[nm] = text
        if pos == 'back': order.insert(0, nm)
        elif pos == 'front': order.append(nm)
        elif pos.startswith('before:'): order.insert(order.index(pos[7:]), nm)
        elif pos.startswith('after:'): order.insert(order.index(pos[6:]) + 1, nm)
    return order, L
