"""share of frames whose sprite splits into >1 8-connected piece (detached limbs/feet/ties), by body x size and per character."""
import glob, os, sys, collections, json
import numpy as np
from PIL import Image
from scipy import ndimage as nd
OUT = os.path.join(os.path.dirname(__file__), '..', '..', 'lab', 'out')
bs = collections.defaultdict(list); ch = collections.defaultdict(list); ts = collections.defaultdict(list)
for f in glob.glob(os.path.join(OUT, '*', '*_*', '*', '[SE]*_f*.png')):
    p = f.split(os.sep); cid, tb, s = p[-4], p[-3], p[-2]; t, b = tb.split('_')
    a = np.array(Image.open(f).convert('RGBA'))[..., 3] > 0
    n = nd.label(a, structure=np.ones((3, 3)))[1]
    bad = n > 1
    bs[(b, int(s))].append(bad); ch[cid].append(bad); ts[(t, int(s))].append(bad)
pr = lambda d: {f'{k[0]}/{k[1]}' if isinstance(k, tuple) else k: round(100 * np.mean(v), 1) for k, v in sorted(d.items())}
print(json.dumps({'body_size_pct': pr(bs), 'tier_size_pct': pr(ts), 'char_pct': pr(ch)}, indent=1))
