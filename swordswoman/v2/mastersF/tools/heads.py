#!/usr/bin/env python3
"""heads.py V [V...]: from mastersF/<V>.txt + FACE2 kit (face2/out/sprite/<V>_<expr>.txt, tile->cell offset +24,+9):
  mastersF/<V>_face.txt        face layer (master pixels where the kit neutral tile has face pixels; '.' elsewhere)
  mastersF/heads/<V>_neutral.txt  head stamp (rows from the top of the figure to the row above the collar, bbox; '; origin X Y')
  mastersF/heads/<V>_<expr>.txt   expression stamps = neutral stamp + (kit_expr - kit_neutral) delta
Prints face-match (master vs kit neutral on the face mask) and delta pixels per expr."""
import sys, glob, os, numpy as np
sys.path.insert(0, '/Users/waylonhuang/Documents/other/pixelart/swordswoman/v2/mastersF/tools'); import mf
R = mf.R; DX, DY = 24, 9; FACE = set('sSWiInkr')
def tile(p):
    rows = [l.rstrip('\n') for l in open(p) if l.strip() and not l.startswith(';')]; w = max(map(len, rows))
    t = np.full((64, 64), '.', dtype='<U1')
    for y, r in enumerate(rows):
        for x, c in enumerate(r.ljust(w, '.')): t[y + DY, x + DX] = c
    return t
def facemask(t):
    m = np.isin(t, list(FACE))
    k = np.zeros_like(m)
    for y, x in zip(*np.where(t == 'K')):
        nb = t[max(0, y-1):y+2, max(0, x-1):x+2]
        if np.isin(nb, list(FACE)).any() and not np.isin(nb, list('HhL')).sum() > 2: k[y, x] = True
    return m | k
def run(v):
    g, meta = mf.load(R + f'mastersF/{v}.txt'); os.makedirs(R + 'mastersF/heads', exist_ok=True)
    kn = R + f'face2/out/sprite/{v}_neutral.txt'
    crown = next(y for y in range(64) if (g[y] != '.').any())
    collar = next(y for y in range(crown + 10, 64) if sum(c in 'eERr' for c in g[y]) >= 4)
    def stamp(G, name):
        rows = G[crown:collar]; xs = np.where((rows != '.').any(0))[0]; x0, x1 = xs.min(), xs.max()
        open(R + f'mastersF/heads/{v}_{name}.txt', 'w').write(f'; origin {x0} {crown}\n; view {v}\n' + '\n'.join(''.join(r[x0:x1+1]) for r in rows) + '\n')
    stamp(g, 'neutral')
    if not os.path.exists(kn): print(v, 'no kit; neutral stamp only'); return
    tn = tile(kn); fm = facemask(tn)
    fm[:17] = False; fm[29:] = False  # face rows only (kit bow/neck excluded)
    if v == 'N': fm[:] = False
    face = np.where(fm, g, '.'); np.savetxt(R + f'mastersF/{v}_face.txt', face, fmt='%s', delimiter='')
    mism = [(y, x, g[y, x], tn[y, x]) for y, x in zip(*np.where(fm)) if g[y, x] != tn[y, x]]
    print(v, f'face mask {fm.sum()} px, master!=kit on {len(mism)}', mism[:8])
    for p in sorted(glob.glob(R + f'face2/out/sprite/{v}_*.txt')):
        e = os.path.basename(p)[len(v) + 1:-4]
        if e == 'neutral': continue
        te = tile(p); d = np.where(te != tn); G = g.copy(); G[d] = te[d]
        out = [(y, x) for y, x in zip(*d) if not fm[y, x]]
        stamp(G, e); print(f'  {e}: delta {len(d[0])} px' + (f', {len(out)} outside face mask {out[:4]}' if out else ''))
if __name__ == '__main__':
    for v in sys.argv[1:]: run(v)
