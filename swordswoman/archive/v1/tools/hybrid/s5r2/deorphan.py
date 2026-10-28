"""orphan merge (gate: orphans 0). An orphan = opaque px with no same-colour 8-neighbour, not a legal accent
(hylib.ORPHAN_OK: glints, blush, mouth, buckles, smear pink_0) and not next to the sword. Each one takes the most
common colour among its 8-neighbours of the SAME material (else the most common opaque non-outline neighbour,
else outline). Head-stamp px (owner HEAD) are protected unless --head. deorphan.py IN.png [OUT.png]"""
import sys
import numpy as np
from PIL import Image
sys.path.insert(0, '/Users/waylonhuang/Documents/other/pixelart/swordswoman/tools/hybrid')
import hylib as H
N8 = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
def clean(a, protect=None, iters=4):
    pal = H.palette(); a = a.copy(); n_fix = 0
    ok = set(pal.names.index(n) for n in H.ORPHAN_OK if n in pal.names)
    for _ in range(iters):
        idx = H.index_of(a)
        steel = H.disk_op(H.base_mask(idx, 'steel'), 1)
        changed = 0
        for y in range(1, 127):
            for x in range(1, 127):
                v = idx[y, x]
                if v < 0 or v in ok or steel[y, x] or (protect is not None and protect[y, x]): continue
                nb = [idx[y + dy, x + dx] for dy, dx in N8]
                if v in nb: continue
                base = H.name_base(pal.names[v])
                same = [q for q in nb if q >= 0 and H.name_base(pal.names[q]) == base]
                opq = [q for q in nb if q >= 0 and pal.names[q] != 'outline']
                pick = same or opq or [q for q in nb if q >= 0]
                if not pick: continue
                q = max(set(pick), key=pick.count)
                a[y, x, :3] = pal.rgb[q][:3]
                changed += 1
        n_fix += changed
        if not changed: break
    return a, n_fix
if __name__ == '__main__':
    a = np.array(Image.open(sys.argv[1]).convert('RGBA'))
    b, n = clean(a)
    Image.fromarray(b).save(sys.argv[2] if len(sys.argv) > 2 else sys.argv[1]); print('fixed', n)
