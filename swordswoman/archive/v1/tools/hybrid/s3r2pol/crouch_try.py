import pk, sys
def fix(a):
    for y in range(88, 100):
        for x in range(58, 80): a[y, x] = 0
    # knees (2 overlapping, far one 1px right/up) poking past the hem
    K = ['__KKKK__', '_KssssK_', 'KsssssmK', 'KssssmmK', '_KsmmmK_']
    pk.stamp(a, 68, 94, K)
    # shins down to the existing feet (y100+)
    pk.stamp(a, 63, 98, ['KKsssKK_mK', 'KssssKmmmK'])
    bell = {88: (57, 72), 89: (56, 72), 90: (55, 72), 91: (54, 71), 92: (53, 71), 93: (52, 70), 94: (51, 70), 95: (50, 69), 96: (50, 68)}
    for y, (l, r) in bell.items():
        for x in range(l, r + 1):
            if x in (l, r): c = 'K'
            elif x <= l + 2 and y <= 93: c = 'C'
            elif x >= r - 3: c = 'r'
            else: c = 'R'
            pk.put(a, x, y, c, 'over' if x >= 58 else 'behind')
    for y, x in ((89, 65), (90, 64), (91, 64), (92, 63), (93, 63), (94, 62), (95, 62)): pk.put(a, x, y, 'r')
    for x in range(51, 68): pk.put(a, x, 96, 'r' if x % 4 == 1 else 'v', 'over' if x >= 58 else 'behind')
    for x in range(50, 69):
        pk.put(a, x, 97, 'v' if x % 4 == 1 else 'K', 'over' if x >= 58 else 'behind')
        if x % 4 == 1: pk.put(a, x, 98, 'K', 'over' if x >= 58 else 'behind')
    return a
if __name__ == '__main__':
    a = pk.load('/Users/waylonhuang/Documents/other/pixelart/swordswoman/archive/v1/hybrid/S3_editchain/r2/std/jump_E_crouch.png'); pk.save(fix(a), sys.argv[1])
