"""postfix.py : apply hx.main_comp to every out/<clip>/<method>/fNN grid (idempotent; rewrites txt/png/json)"""
import sys, os, glob
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hx
n = 0
for p in glob.glob(hx.EXP + 'out/*/*/f??.txt'):
    if '/master/' in p or ('poe' in p and os.environ.get('SKIPPOE')): continue
    g = hx.read_grid(p); g2 = hx.main_comp(hx.drop_bare_k(g))
    if (g2 != g).any(): hx.save(g2, p[:-4], p.split('/')[-3].split('_')[1]); n += 1
print('rewrote', n)
