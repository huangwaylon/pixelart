#!/usr/bin/env python3
"""cuthead.py VIEW -> heads/VIEW_neutral.txt (head stamp cut from masters/VIEW.txt: all rows above the collar, bbox), with '; origin X Y' meta."""
import sys
v = sys.argv[1]
g = [l.rstrip('\n') for l in open(f'/Users/waylonhuang/Documents/other/pixelart/swordswoman/v2/masters/{v}.txt') if l.strip() and not l.startswith(';')]
crown = next(y for y, r in enumerate(g) if sum(c in 'HLh' for c in r) >= 8)
collar = next(y for y in range(crown + 8, 64) if sum(c in 'eERr' for c in g[y]) >= 4)
top = next(y for y, r in enumerate(g) if r.strip('.'))
rows = g[top:collar]
xs = [x for r in rows for x, c in enumerate(r) if c != '.']
x0, x1 = min(xs), max(xs)
out = [f'; origin {x0} {top}', f'; view {v}'] + [r[x0:x1+1] for r in rows]
open(f'/Users/waylonhuang/Documents/other/pixelart/swordswoman/v2/masters/heads/{v}_neutral.txt', 'w').write('\n'.join(out) + '\n')
print(v, 'origin', x0, top, 'size', x1 - x0 + 1, len(rows))
