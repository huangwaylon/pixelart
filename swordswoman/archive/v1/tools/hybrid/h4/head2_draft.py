"""Head stamp v2 DRAFT generator (lock2): decimate the v1 hand-typed heads (drop near-duplicate rows/cols, ~0.9x)
and re-tone the hair dark (hair_0 >= 60 %, hair_1 only as the lit upper-left band, hair_2 only as the top-left
sheen). The drafts are then hand-edited: the .pix files in hybrid/lock2/src/ are the source of truth.
  .venv/bin/python tools/hybrid/h3/head2_draft.py            -> hybrid/lock2/draft/head_<D>.pix + x8 previews
"""
import sys, os
import numpy as np
sys.path.insert(0, os.path.dirname(__file__))
from common import read_grid, write_grid, to_rgba, zoom, strip

SRC = 'hybrid/lock/pixel/src'
OUT = 'hybrid/lock2/draft'
# rows / cols of the v1 grid to drop (hand-picked duplicates), per direction
DROP = {
    'S':  dict(rows=[5, 15, 17, 19, 30], cols=[12, 13]),
    'SE': dict(rows=[4, 16, 18, 19, 29], cols=[3, 14]),
    'E':  dict(rows=[3, 14, 16, 18, 30], cols=[4, 8]),
    'NE': dict(rows=[5, 16, 18, 20, 26], cols=[10, 18]),
    'N':  dict(rows=[4, 15, 17], cols=[12, 13]),
}


def strand(g, y, x):
    W = g.shape[1]
    l = g[y, x - 1] if x > 0 else '.'; r = g[y, x + 1] if x + 1 < W else '.'
    return g[y, x] == 'h' and l in 'HJ' and r in 'HJ'


def retone(g):
    """dark dome: everything hair_0, then a lit crescent (hair_1) hugging the upper-left rim, a hair_2 sheen
    inside it, and the v1 strand lines that fall inside the lit zone kept as hair_0 separations."""
    from scipy import ndimage
    hair = np.isin(g, list('hHJ'))
    inside = g != '.'
    dist = ndimage.distance_transform_cdt(inside, metric='taxicab')
    ys, xs = np.nonzero(hair)
    cy, cx = ys.mean() + 2, xs.mean() + 1
    out = g.copy()
    for y, x in zip(ys, xs):
        ang = np.degrees(np.arctan2(-(y - cy), x - cx)) % 360      # 90 = up, 180 = left
        d = dist[y, x]
        out[y, x] = 'h'
        if 95 <= ang <= 215 and 2 <= d <= 4:
            out[y, x] = 'H'
            if 125 <= ang <= 165 and d == 3: out[y, x] = 'J'
        if strand(g, y, x) and out[y, x] == 'H': out[y, x] = 'h'
    return out


def main():
    os.makedirs(OUT, exist_ok=True)
    ims, labs = [], []
    for d, dr in DROP.items():
        g = read_grid(f'{SRC}/head_{d}.pix')
        keep_r = [i for i in range(g.shape[0]) if i not in dr['rows']]
        keep_c = [i for i in range(g.shape[1]) if i not in dr['cols']]
        g2 = retone(g[keep_r][:, keep_c])
        hair = np.isin(g2, list('hHJ')).sum()
        share = {c: round((g2 == c).sum() / hair, 2) for c in 'hHJ'}
        print(d, g2.shape, share)
        write_grid(g2, f'{OUT}/head_{d}.pix', f'DRAFT v2 head {d} (decimated from lock v1 + dark retone)')
        ims += [to_rgba(g[:, :]), to_rgba(g2)]; labs += [f'v1 {d}', f'v2 {d}']
    strip(ims, z=8, labels=labs).save(f'{OUT}/draft_x8.png')


if __name__ == '__main__':
    main()
