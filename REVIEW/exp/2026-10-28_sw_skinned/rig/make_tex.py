"""make_tex.py (R, round 2): per-view head projection textures rig/tex/tex_<V>.png = the m96 master EC0_<V>_96 (128x128, exact palette
pixels) with every transparent pixel filled by its nearest opaque master pixel (tolerates the hull overshooting the master silhouette by
1-2 px). Sampled with 'Closest' through the per-view projection UVs pj_<V> (build_rig.py)."""
import os, numpy as np
from PIL import Image
from scipy import ndimage as nd
H = os.path.dirname(os.path.abspath(__file__)); M = '/Users/waylonhuang/Documents/other/pixelart/swordswoman/v2/m96/masters/EC0_{}_96.png'
for v in ('S', 'SE', 'E', 'NE', 'N'):
    a = np.asarray(Image.open(M.format(v)).convert('RGBA')).copy(); op = a[..., 3] > 127
    _, (iy, ix) = nd.distance_transform_edt(~op, return_indices=True)
    b = a[iy, ix]; b[..., 3] = 255; Image.fromarray(b, 'RGBA').save(os.path.join(H, 'tex', f'tex_{v}.png')); print(v)
