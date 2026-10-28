"""mkpal24.py: extend the locked 16-colour palette with 8 colours = k-means of high-error illustration pixels (all 9 views,
error-weighted), each tagged with the material of its nearest locked colour. -> v2/pixelize/palette24.json"""
import sys, os, json, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pzlib as Z
from scipy.cluster.vq import kmeans2
keys, rgb, mat = Z.load_pal(); plab = Z.rgb2lab(rgb)
X = []
for v in ['front', 'left', 'back', 'right', 'S', 'SE', 'E', 'NE', 'N']:
    x, m = Z.load(v); X.append(x[m][::7])
X = np.concatenate(X); L = Z.rgb2lab(X)
d = np.sqrt(((L[:, None] - plab[None]) ** 2).sum(-1)); e = d.min(1)
hi = L[e > 9]; print('pixels', len(X), 'high-error', len(hi))
np.random.seed(0)
c, lab = kmeans2(hi, 8, minit='++', seed=0)
cnt = np.bincount(lab, minlength=8)
def lab2rgb(l):
    fy = (l[0] + 16) / 116; fx = fy + l[1] / 500; fz = fy - l[2] / 200
    f = np.array([fx, fy, fz]); xyz = np.where(f > 0.2069, f ** 3, (f - 16 / 116) / 7.787) * np.array([0.95047, 1, 1.08883])
    M = np.linalg.inv(np.array([[0.4124, 0.3576, 0.1805], [0.2126, 0.7152, 0.0722], [0.0193, 0.1192, 0.9505]]))
    r = M @ xyz; r = np.where(r > 0.0031308, 1.055 * np.abs(r) ** (1 / 2.4) - 0.055, 12.92 * r)
    return np.clip(np.round(r * 255), 0, 255).astype(int)
P = json.load(open(Z.PALFILE)); new = dict(P['colors'])
names = '12345678'
for i in np.argsort(-cnt):
    rr = lab2rgb(c[i]); nn = keys[int(((plab - c[i]) ** 2).sum(1).argmin())]
    hx = '#%02x%02x%02x' % tuple(rr)
    new[names[len(new) - 16]] = {'hex': hx, 'material': mat[nn], 'desc': f'extra (near {nn}, {cnt[i]} px)'}
    print(names[len(new) - 17], hx, 'near', nn, cnt[i])
P['colors'] = new; P['name'] = 'pixelize_24'; P['note'] = 'locked 16 + 8 error-driven extras (mkpal24.py)'
json.dump(P, open(Z.ROOT + 'v2/pixelize/palette24.json', 'w'), indent=1)
