#!/usr/bin/env python3
"""print composed full char-maps with row/col rulers. usage: show.py se_neutral ..."""
import sys, os
H = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
for n in sys.argv[1:]:
    L = [l for l in open(f'{H}/png/{n}_full.txt').read().split('\n') if l and not l.startswith(';')]
    w = max(map(len, L)); print('==', n, w, 'x', len(L)); print('    ' + ''.join(str(i % 10) for i in range(w)))
    for i, l in enumerate(L): print(f'{i:3d} {l}')
