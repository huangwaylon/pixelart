"""Which palette pairs make up shade_swap (pxeval definition: changed px not explained by local motion, both opaque, CIEDE2000 < 12),
over all 48 clips of 20261030_66119a7; also optionally for a recoloured frame set (lock.py)."""
import sys, os, glob, collections
sys.path.insert(0, os.path.dirname(__file__)); sys.path.insert(0, '/Users/waylonhuang/Documents/other/pixelart/pipeline/tools')
from common import *
import pxeval as PX
KEYS = list(HEX); KI = {k: i for i, k in enumerate(KEYS)}; LAB = PX.rgb2lab(np.array([HEX[k] for k in KEYS], float))
def index(a):
    idx = np.full(a.shape[:2], -1)
    m = a[..., 3] > 0
    for k, c in HEX.items(): idx[m & (a[..., :3] == c).all(-1)] = KI[k]
    return idx
def swaps(frames, loop=True):
    idx = [index(f) for f in frames]; n = len(idx); C = collections.Counter(); tot = 0; U_ = 0
    for t in range(n if loop else n - 1):
        a, b = idx[t], idx[(t + 1) % n]; U = (a >= 0) | (b >= 0); ch = (a != b) & U
        mis, *_ = PX.motion_comp(a, b); sw = (a >= 0) & (b >= 0) & ch & mis
        if sw.any():
            de = PX.ciede2000(LAB[a[sw]], LAB[b[sw]]); ya, yb = a[sw][de < 12], b[sw][de < 12]
            for p, q in zip(ya, yb): C[''.join(sorted((KEYS[p], KEYS[q])))] += 1
        U_ += U.sum()
    return C, U_
if __name__ == '__main__':
    ALL = collections.Counter(); UU = 0; per = {}
    for act in ['idle', 'walk', 'run', 'jump', 'dash', 'hurt']:
        for v in ['S', 'SE', 'E', 'NE', 'N', 'NW', 'W', 'SW']:
            fs = [np.asarray(Image.open(p).convert('RGBA')) for p in sorted(glob.glob(f'{B}{act}/{v}/final/f??.png'))]
            C, U = swaps(fs); ALL += C; UU += U; per[f'{act}_{v}'] = sum(C.values()) / U
    tot = sum(ALL.values())
    print('near-swap px total', tot, 'rate', tot / UU)
    print(' '.join(f'{k}:{100*c/tot:.1f}%' for k, c in ALL.most_common(16)))
    json.dump({'pairs': dict(ALL.most_common()), 'rate': tot / UU, 'per_clip': per}, open(os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/swap_pairs.json', 'w'), indent=1)
