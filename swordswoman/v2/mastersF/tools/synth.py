# blockout material map -> crude palette master with K outline (tool test / artist base)
import sys, numpy as np
sys.path.insert(0, '/Users/waylonhuang/Documents/other/pixelart/swordswoman/v2/mastersF/tools'); import mf
MAP = dict(H='H', B='H', W='E', F='s', N='S', e='i', D='E', O='d', A='R', h='s', L='s', T='d')
B, _ = mf.load(sys.argv[1]); g = np.vectorize(lambda c: MAP.get(c, '.'))(B)
o = g.copy()
for r in range(64):
    for x in range(64):
        if g[r, x] != '.' and any(not (0 <= rr < 64 and 0 <= xx < 64) or g[rr, xx] == '.' for rr, xx in ((r-1,x),(r+1,x),(r,x-1),(r,x+1))): o[r, x] = 'K'
open(sys.argv[2], 'w').write('\n'.join(''.join(l) for l in o) + '\n')
