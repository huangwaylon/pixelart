import pk, sys
def line_v(a, x, y0, y1, gaps=()):
    for y in range(y0, y1 + 1):
        if y in gaps: continue
        t = (y - y0) / max(1, y1 - y0)
        pk.put(a, x, y, 'P' if t < 0.45 else 'p', 'behind')
def fix(a):
    for y in range(90, 104):
        for x in list(range(44, 52)) + list(range(71, 80)):
            if pk.ch(a, x, y) == 'p' and pk.ch(a, x - 1, y) == '.' : a[y, x] = 0
    # take-off speed lines: long, thick-near-body, broken at the trailing end (cloth + heels left them behind)
    line_v(a, 45, 80, 96, gaps=(93,))
    for y in (97, 98, 99, 100, 102, 103): pk.put(a, 47, y, 'p', 'behind')
    line_v(a, 74, 90, 103, gaps=(100,))
    line_v(a, 77, 84, 97, gaps=(94,))
    line_v(a, 80, 93, 100)
    return a
if __name__ == '__main__':
    a = pk.load('/Users/waylonhuang/Documents/other/pixelart/swordswoman/hybrid/S3_editchain/r2/std/jump_E_apex.png'); pk.save(fix(a), sys.argv[1])
