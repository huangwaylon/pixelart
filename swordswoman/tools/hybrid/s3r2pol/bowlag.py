import pk
def bow_mask(a, box):
    x0, y0, x1, y1 = box; red = set()
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            if pk.ch(a, x, y) in 'vrRC': red.add((x, y))
    m = set(red)
    for (x, y) in red:
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            q = (x + dx, y + dy)
            if pk.ch(a, *q) == 'K' and q not in m:
                nb = [pk.ch(a, q[0] + ex, q[1] + ey) for ex, ey in ((1, 0), (-1, 0), (0, 1), (0, -1))]
                if not any(c in 'hHJ' for c in nb) or dy == -1: m.add(q)
    return m
def shift_bow(a, box, dy, dx=0):
    m = bow_mask(a, box); src = {p: a[p[1], p[0]].copy() for p in m}
    for (x, y) in m:
        nb = [pk.ch(a, x + ex, y + ey) for ex, ey in ((1, 0), (-1, 0), (0, 1), (0, -1))]
        a[y, x] = 0
        if sum(c in 'hHJ' for c in nb) >= 2: pk.put(a, x, y, 'h')
    for (x, y), v in src.items(): a[y + dy, x + dx] = v
    # re-close the hair top where the bow lifted off (any hair pixel now touching empty above gets the outline)
    x0, y0, x1, y1 = box
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            if pk.ch(a, x, y) in 'hHJ' and pk.ch(a, x, y - 1) == '.': pk.put(a, x, y - 1, 'K')
    return len(m)

def fill_holes(a, box):
    x0, y0, x1, y1 = box; n = 0
    for _ in range(2):
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                if pk.ch(a, x, y) != '.': continue
                L = any(pk.ch(a, x - i, y) != '.' for i in (1, 2)); R = any(pk.ch(a, x + i, y) != '.' for i in (1, 2))
                D = pk.ch(a, x, y + 1) != '.'
                if L and R and D:
                    nb = [pk.ch(a, x + ex, y + ey) for ex, ey in ((1, 0), (-1, 0), (0, 1), (0, -1))]
                    pk.put(a, x, y, 'K' if any(c in 'vrRC' for c in nb) and pk.ch(a, x, y - 1) == '.' else 'h'); n += 1
    return n
