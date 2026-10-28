import pk
def ne(a):
    # second loop peeking out LEFT of the bun (two-loop bow, as S/N/SE/E), lit upper-left
    pk.stamp(a, 49, 45, ['_KKKK_',
                         'KCCRRR',
                         'KCRRRr',
                         'KRRRrr',
                         '_KRrvv',
                         '__KKvK',
                         '____KK'], 'behind')
    return a
def nw(a):
    pk.stamp(a, 74, 45, ['_KKKK_',
                         'RCCRRK',
                         'RRRRrK',
                         'rRRrrK',
                         'vrrvK_',
                         'KvKK__',
                         'KK____'], 'behind')
    return a
def relight(a, box, cpts):
    """mirrored bow: move the lit red_3 from the loops' right edges to their upper-left (light is upper-left)"""
    x0, y0, x1, y1 = box
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            if pk.ch(a, x, y) == 'C': pk.put(a, x, y, 'R')
    for x, y in cpts:
        if pk.ch(a, x, y) in 'Rr': pk.put(a, x, y, 'C')
def sw(a): relight(a, (56, 43, 70, 50), [(61, 45), (62, 45), (59, 46), (59, 47), (65, 45), (65, 46)]); return a
def w(a): relight(a, (62, 43, 76, 50), [(65, 44), (64, 45), (64, 46), (64, 47), (71, 44), (70, 45), (70, 46)]); return a
