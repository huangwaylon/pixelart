"""paste.py BASESTEM CROP.txt X0 Y0 OUTSTEM [--keepsil]: paste char crop into sprite at (X0,Y0) -> OUTSTEM.{txt,json,png}
--keepsil: positions that are '.' in the base and not in crop (or vice versa) keep the base value, except interior holes"""
import sys, os, json, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import m96 as M, pzlib as Z
a = sys.argv[1:]; keep = '--keepsil' in a; a = [t for t in a if t != '--keepsil']
PR = [int(t) for t in os.environ.get('PROTECT', '').split()]; PR = [PR[i:i + 4] for i in range(0, len(PR), 4)]
g, meta = Z.read(a[0]); keys, rgb, _ = Z.load_pal(M.PAL)
rows = [l.rstrip('\n') for l in open(a[1]) if l.strip() and not l.startswith(';')]
x0, y0 = int(a[2]), int(a[3]); n = 0; bad = 0
for j, r in enumerate(rows):
    for i, c in enumerate(r):
        y, x = y0 + j, x0 + i
        if c not in keys and c != '.': bad += 1; continue
        if keep and (c == '.') != (g[y, x] == '.'):
            continue
        if any(p[0] <= x < p[2] and p[1] <= y < p[3] for p in PR): continue
        if g[y, x] != c: n += 1; g[y, x] = c
os.makedirs(os.path.dirname(a[4]), exist_ok=True); Z.save(g, a[4], keys, rgb, meta); print(f'{a[4]}: {n} px changed, {bad} bad chars')
