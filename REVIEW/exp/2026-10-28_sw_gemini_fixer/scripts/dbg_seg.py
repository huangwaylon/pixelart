"""debug: material segmentation + colours of a fixer native crop. Fixer venv. usage: dbg_seg.py work/proc/a1_fix.png"""
import sys, os, numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fixlib as F, pzlib as Z
fx = np.array(Image.open(sys.argv[1]).convert('RGB'))
m, bg = F.bgmask(fx); nat, na = F.crop(fx, m)
L = Z.seg2(nat, na)
for mt in np.unique(L):
    s = (L == mt) & na
    if s.sum(): print(mt, int(s.sum()), nat[s].mean(0).round(), np.percentile(nat[s] @ [.299, .587, .114], [10, 50, 90]).round())
h, w = na.shape
rows = slice(int(h * .33), int(h * .42))
print('obi rows sample', [tuple(nat[int(h * .37), c].astype(int)) for c in range(w // 3, 2 * w // 3, 3)])
print('labels there', L[int(h * .37), w // 3:2 * w // 3:3])
