# mkS.py NAME "CR=ch ..." : write /tmp/m96t/NAME/EC0_S_96.txt with joint5 edits on the S master
import sys, os, subprocess
src = open('eyes4/joint6.py').read().split('combos = []')[0]; ns = {}; exec(src, ns)
n, spec = sys.argv[1:3]; cells = {(int(t[0]), int(t[1])): t[3] for t in spec.split()}
g = [list(l.rstrip('\n')) for l in open(ns['M'] % 'S' + '.txt')]
for e in ns['edits']('S', cells):
    x, y, c = e.split(','); g[int(y)][int(x)] = c
os.makedirs('/tmp/m96t/' + n, exist_ok=True); open(f'/tmp/m96t/{n}/EC0_S_96.txt', 'w').write('\n'.join(''.join(r) for r in g) + '\n')
