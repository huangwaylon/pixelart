"""Make the bow loops (and bun) 2 px taller: duplicate the widest bow-fill row twice (a deliberate
structural edit; the bow is the #1 silhouette ID and read small at 1x)."""
import sys; sys.path.insert(0,'/tmp'); from stamplib import *
def load(p): return open(p).read().split('grid:\n')[1].strip('\n').split('\n')
for d in ['S','SE','E','NE','N']:
    p=f'head_{d}.pix'; rows=load(p)
    m=max(range(0,7),key=lambda y: rows[y].count('R'))
    rows=rows[:m]+[rows[m],rows[m]]+rows[m:]
    hdr=open(p).read().split('\n')[0]
    save(p,rows,f'facing {d} (bow grown +2 rows)')
