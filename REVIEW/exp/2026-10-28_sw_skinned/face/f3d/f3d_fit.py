"""f3d_fit.py (F, round 5): calibrate the face texture layout on the real head.  A UV-coded texture (R = u, G = v) is rendered at rest in the S
view (f3d_render.py --expr=uvcode); every hi-res sample gives sprite (x, y) -> texture (u, v).  A cubic fit maps the m96 S design coordinates
(col, row, shifted by face/calib.json's head offset) to texture pixels, so the drawn features land on the master's rows/cols in S, while SE/E/...
come out of the 3D head as they are.  -> face/f3d/uvfit.json (used by f3d_lib.to_px)"""
import os, sys, json
import numpy as np
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__)); EXP = os.path.dirname(os.path.dirname(HERE))
V = sys.argv[1] if len(sys.argv) > 1 else 'S'
al = json.load(open(f'{EXP}/rig/align.json'))[V]
cal = {'dx': al['dx'] - al.get('reg_dx', al['dx']), 'dy': al['dy'] - al.get('reg_dy', al['dy'])}   # sprite = master + (output placement - registration) = (0, -lift)
a = np.array(Image.open(f'{HERE}/out/calR/rest_{V}_f00_guide.png').convert('RGBA')).astype(float)
m = (a[..., 3] > 250) & (np.abs(a[..., 2] - 77) <= 2)
ys, xs = np.nonzero(m)
sx = (xs + .5) / 8 - 32 + al['dx']; sy = (ys + .5) / 8 - 32 + al['dy']
tu = a[ys, xs, 0] / 255 * 1024; tv = a[ys, xs, 1] / 255 * 1024
# design coords: m96 col/row (S master) -> sprite = (col + cal.dx, row + cal.dy)
cx = sx - cal['dx']; cy = sy - cal['dy']
def feats(x, y): return np.stack([np.ones_like(x), x, y, x * x, x * y, y * y, x ** 3, x * x * y, x * y * y, y ** 3], -1)
sel = (cx > 48) & (cx < 82) & (cy > 42) & (cy < 62)
A = feats(cx[sel] - 64, cy[sel] - 52)
cu = np.linalg.lstsq(A, tu[sel], rcond=None)[0]; cv = np.linalg.lstsq(A, tv[sel], rcond=None)[0]
ru = A @ cu - tu[sel]; rv = A @ cv - tv[sel]
json.dump({'view': V, 'cu': cu.tolist(), 'cv': cv.tolist(), 'n': int(sel.sum()), 'rms_texels': [float(np.sqrt((ru ** 2).mean())), float(np.sqrt((rv ** 2).mean()))],
           'range': [float(cx[sel].min()), float(cx[sel].max()), float(cy[sel].min()), float(cy[sel].max())]}, open(f'{HERE}/uvfit.json' if V == 'S' else f'{HERE}/uvfit_{V}.json', 'w'), indent=1)
print('uvfit', V, 'samples', int(sel.sum()), 'rms texels', np.sqrt((ru ** 2).mean()), np.sqrt((rv ** 2).mean()), 'cover', cx[sel].min(), cx[sel].max(), cy[sel].min(), cy[sel].max())
