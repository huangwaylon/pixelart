"""Identity / pixel-quality metrics on palette-locked char grids (pose-independent), vs the m96 SE master. Any venv w/ numpy+scipy.
  python s3_identity.py OUT.json STEM [STEM ...]
Per sprite: fig_h/w, n_colors, orph (pixels with no same-colour 8-neighbour), orph_pct, kedge (fraction of silhouette
boundary pixels that are outline K), mat_* (material area fractions), matL1 (L1 vs master fractions), palL1 (L1 of the
18-colour histogram vs master), hair_bbox (h,w px), hair_area, bow_px (red pixels at/above the hair top third), eyeW (W
pixels inside the head box), head_dh/dw (hair bbox minus master, px; 0 = same head size at the same scale)."""
import sys, json, numpy as np
from scipy import ndimage as nd

MAT = {'K': 'K', 'hair': 'hHgL', 'skin': 'sSmk', 'red': 'eER', 'obi': 'QOo', 'socks': 'Dd', 'W': 'W'}
PALK = 'KhHgLsSmkeERQOoWDd'
MASTER = '/Users/waylonhuang/Documents/other/pixelart/swordswoman/v2/m96/masters/EC0_SE_96'


def read(stem):
    return np.array([list(l.rstrip('\n')) for l in open(stem + '.txt') if l.strip() and not l.startswith(';')])


def measure(stem):
    g = read(stem); a = g != '.'
    ys, xs = np.where(a); g = g[ys.min():ys.max() + 1, xs.min():xs.max() + 1]; a = g != '.'
    H, W = g.shape; n = a.sum()
    o = {'name': stem.split('/')[-1], 'fig_h': int(H), 'fig_w': int(W), 'px': int(n)}
    o['n_colors'] = int(len(set(g[a].tolist())))
    orph = 0
    p = np.pad(g, 1, constant_values='.')
    for r, c in zip(*np.where(a)):
        if (p[r:r + 3, c:c + 3] == g[r, c]).sum() == 1: orph += 1
    o['orph'] = orph; o['orph_pct'] = round(100 * orph / n, 2)
    er = nd.binary_erosion(a); edge = a & ~er
    o['kedge'] = round(float((g[edge] == 'K').mean()), 3)
    for k, cs in MAT.items(): o['mat_' + k] = round(float(np.isin(g[a], list(cs)).mean()), 4)
    o['hist'] = {c: round(float((g[a] == c).mean()), 4) for c in PALK}
    hair = np.isin(g, list(MAT['hair']))
    lab, nn = nd.label(hair, np.ones((3, 3)))
    if nn:
        sz = nd.sum(hair, lab, range(1, nn + 1)); top = lab == 1 + int(np.argmax(sz))  # largest hair blob = head hair
        hy, hx = np.where(top); o['hair_bbox'] = [int(hy.max() - hy.min() + 1), int(hx.max() - hx.min() + 1)]
        o['hair_area'] = int(top.sum())
        y0, y1, x0, x1 = hy.min(), hy.max(), hx.min(), hx.max()
        red = np.isin(g, list(MAT['red']))
        lim = y0 + (y1 - y0) // 3
        o['bow_px'] = int(red[:lim + 1, max(0, x0 - 4):x1 + 5].sum())
        o['eyeW'] = int((g[y0:y1 + 1, x0:x1 + 1] == 'W').sum())
        o['face_skin'] = int(np.isin(g[y0:y1 + 1, x0:x1 + 1], list('sSmk')).sum())
    return o


def compare(o, m):
    o['matL1'] = round(sum(abs(o['mat_' + k] - m['mat_' + k]) for k in MAT), 3)
    o['palL1'] = round(sum(abs(o['hist'][c] - m['hist'][c]) for c in PALK), 3)
    if 'hair_bbox' in o:
        o['head_dh'] = o['hair_bbox'][0] - m['hair_bbox'][0]; o['head_dw'] = o['hair_bbox'][1] - m['hair_bbox'][1]
    return o


if __name__ == '__main__':
    out = sys.argv[1]; stems = [s[:-4] if s.endswith('.txt') else s for s in sys.argv[2:]]
    m = measure(MASTER); m['name'] = 'MASTER_SE'; compare(m, m)
    res = [m] + [compare(measure(s), m) for s in stems]
    keys = ['fig_h', 'fig_w', 'n_colors', 'orph', 'orph_pct', 'kedge', 'matL1', 'palL1', 'hair_bbox', 'head_dh', 'head_dw', 'bow_px', 'eyeW', 'face_skin']
    print('name'.ljust(22) + ''.join(k[:9].rjust(10) for k in keys))
    for r in res:
        print(r['name'][:22].ljust(22) + ''.join(str(r.get(k, '-')).rjust(10) for k in keys))
    json.dump(res, open(out, 'w'), indent=0)
