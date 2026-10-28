"""one-off fixes on work (v4): SE crown px restored from master0 (SE_hair job had recoloured the hair crown red), E legs back to
v3 (job moved the boot top) + E boot cuff interior K -> h/H, NE back-hair trim 1px at x80 (head width SE/NE within 1)."""
import sys
D = '/Users/waylonhuang/Documents/other/pixelart/swordswoman/v2/m96/'
rd = lambda p: [list(l.rstrip('\n')) for l in open(p)]
def wr(p, w): open(p, 'w').write('\n'.join(''.join(r) for r in w) + '\n')
a, w = rd(D + 'master0/EC0_SE_96.txt'), rd(D + 'work/EC0_SE_96.txt')
for y in range(29, 34):
    for x in range(58, 65): w[y][x] = a[y][x]
wr(D + 'work/EC0_SE_96.txt', w)
a, w = rd(D + 'snap/v3_regions1/EC0_E_96.txt'), rd(D + 'work/EC0_E_96.txt')
for y in range(100, 127):
    for x in range(50, 80): w[y][x] = a[y][x]
for y in (114, 115, 116):
    xs = [x for x in range(128) if w[y][x] != '.']
    for x in xs[1:-1]: w[y][x] = 'h' if y < 116 else 'H'
wr(D + 'work/EC0_E_96.txt', w)
w = rd(D + 'work/EC0_NE_96.txt')
for y in range(30, 64):
    if w[y][80] != '.' and w[y][81] == '.':
        w[y][80] = '.'
        if w[y][79] != '.': w[y][79] = 'K'
wr(D + 'work/EC0_NE_96.txt', w)
print('ok')
