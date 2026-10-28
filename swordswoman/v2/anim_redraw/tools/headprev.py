"""headprev.py: preview m48/heads/*.txt next to the old master head (10x) -> m48/heads/preview.png"""
import sys, os, glob
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fin48 as F, numpy as np
from PIL import Image
D = F.A + '/m48/heads'
def load(p):
    L = [l for l in open(p).read().split('\n') if l and not l.startswith(';')]
    w = max(len(l) for l in L); return np.array([list(l.ljust(w, '.')) for l in L])
M = F.to_grid(F.A + '/m48/SE_box.png')[10:36, 14:46]
ims = [M] + [load(p) for p in sorted(glob.glob(D + '/*.txt')) if 'prompt' not in p]
S = 7; sh = Image.new('RGB', (len(ims) * (34 * S), 28 * S), (40, 40, 40))
for k, g in enumerate(ims):
    sh.paste(F.to_img(g, (110, 110, 110)).resize((g.shape[1] * S, g.shape[0] * S), Image.NEAREST), (k * 34 * S, 0))
sh.save(D + '/preview.png'); print('order: old,', [os.path.basename(p) for p in sorted(glob.glob(D + '/*.txt')) if 'prompt' not in p], sh.size)
