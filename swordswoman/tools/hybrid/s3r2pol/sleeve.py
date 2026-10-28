import pk
def comp(a, seed, box):
    x0, y0, x1, y1 = box; st = [seed]; seen = set()
    while st:
        x, y = st.pop()
        if (x, y) in seen or not (x0 <= x <= x1 and y0 <= y <= y1): continue
        if pk.ch(a, x, y) not in 'vrRC': continue
        seen.add((x, y)); st += [(x+1, y), (x-1, y), (x, y+1), (x, y-1)]
    return seen
if __name__ == '__main__':
    for n, seed in (('slash_SE_k2', (53, 91)), ('slash_SE_k3', (55, 90))):
        a = pk.load('/Users/waylonhuang/Documents/other/pixelart/swordswoman/hybrid/S3_editchain/r2/std/%s.png' % n)
        s = comp(a, seed, (44, 82, 64, 99))
        print(n, len(s))
        for y in range(82, 100): print(y, ''.join('#' if (x, y) in s else pk.ch(a, x, y) for x in range(44, 66)))

def separate(a, seed, box, log=None):
    s = comp(a, seed, box)
    rows = {}
    for x, y in s: rows.setdefault(y, []).append(x)
    n = 0
    for y, xs in rows.items():
        xr = max(xs)
        if pk.ch(a, xr + 1, y) == 'K' and pk.ch(a, xr + 2, y) in 'CR':
            pk.put(a, xr + 2, y, 'r'); n += 1
    ys = sorted(rows)
    for y in ys[-3:-1]:   # sleeve opening: dark lining inside the bottom rows
        xs = sorted(rows[y])
        for x in xs[1:]: pk.put(a, x, y, 'v'); n += 1
    return n
