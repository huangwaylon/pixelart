import pk, sys
def fix(a):
    # thin the near half of the blade arc over the hips: rows 91-93 back to skirt so the hem reads; the arc keeps
    # its 3-row leading band (94-96) across the thighs and its full width out front (x>=75)
    for y in range(91, 94):
        for x in range(53, 75):
            if pk.ch(a, x, y) in 'pPd':
                c = 'R'
                if y == 93: c = 'v'
                elif x in (60, 61, 68): c = 'r'
                pk.put(a, x, y, c)
    for x in range(54, 75):
        if pk.ch(a, x, 94) in 'pP' and x % 3 == 0: pk.put(a, x, 94, 'p')
    return a
if __name__ == '__main__':
    a = pk.load('/Users/waylonhuang/Documents/other/pixelart/swordswoman/archive/v1/hybrid/S3_editchain/r2/std/slash_SE_k1.png'); pk.save(fix(a), sys.argv[1])
