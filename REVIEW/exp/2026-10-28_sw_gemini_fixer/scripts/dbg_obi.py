"""debug obi: rescaled lo of a1 -> seg labels and colours at obi rows. Fixer venv."""
import sys, os, numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fixlib as F, pzlib as Z
E = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/'
fx = np.array(Image.open(E + 'work/proc/a1_fix.png').convert('RGB'))
m, bg = F.bgmask(fx); nat, na = F.crop(fx, m)
lo, al, w, how = F.to_h(nat, na, 96)
L = Z.seg2(lo, al)
g = np.array([list(l.rstrip('\n')) for l in open(E + 'work/proc/a1_r96L2.txt')])
ys, xs = np.where(g != '.')
sub = g[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
for r in range(40, 52):
    print(r, ''.join(sub[r]), ' '.join(L[r, c][:2] for c in range(0, w, 3)))
r = 45
print([tuple(lo[r, c].astype(int)) for c in range(8, w - 8, 3)])
