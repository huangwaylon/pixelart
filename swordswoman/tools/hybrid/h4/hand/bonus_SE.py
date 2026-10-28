"""run_SE_f1 + dash_SE_f1 (S3 r3). Base poses from the h4 kit (anims/bonus_SE.py, lock3 heads); FX are authored here.
run:  stretched leg smear + 2-copy leg echo (kept) + HEM DRAG: the back hem and tails pulled into a red_1 / red_0
      drag wedge trailing up-left, 2 motion lines.
dash: no soft pink blob. Two HARD multiples of the body silhouette along the SE travel vector (trail = up-left):
      a full silhouette 7 px back (pink_1 body, pink_0 1 px rim on its trailing edge) and a partial (upper body +
      sleeve only) 14 px back in pink_0; then 4 rimmed speed bands (steel_2 core with a steel_1 rim, or pink_1 / pink_0)
      off the trailing edge. Palette-locked, binary alpha, no dither."""
import copy, os, sys
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
import kit
import importlib.util
from common import to_rgba, save

sp = importlib.util.spec_from_file_location('bon', os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'anims', 'bonus_SE.py'))
BON = importlib.util.module_from_spec(sp); sp.loader.exec_module(BON)
N = 128
NB4 = ((1, 0), (-1, 0), (0, 1), (0, -1))


def run():
    fs = copy.deepcopy(BON.FRAMES['run_SE_f1'])
    fs['fx'] = list(fs['fx']) + [
        ('limb', dict(path=[(51, 93), (46, 92), (41, 91), (37, 90)], w0=4, w1=1, tones='rrv', mode='behind', ol_lead=False)),
        ('limb', dict(path=[(46, 96), (41, 95), (36, 94)], w0=3, w1=1, tones='rv', mode='behind', ol_lead=False)),
    ]
    a, info = kit.render(fs)
    return info['chars']


def dash():
    fs = copy.deepcopy(BON.FRAMES['dash_SE_f1'])
    fs['fx'] = []
    a, info = kit.render(fs)
    g = info['chars'].copy()
    body = (g != '.') & ~np.isin(g, list('tTw'))
    def shifted(m, dx, dy):
        o = np.zeros_like(m)
        ys, xs = np.nonzero(m)
        ok = (ys + dy >= 0) & (ys + dy < N) & (xs + dx >= 0) & (xs + dx < N)
        o[ys[ok] + dy, xs[ok] + dx] = True
        return o
    # far partial first (upper body + sleeve: rows above the hem), then the full near copy
    up = body.copy(); up[92:] = False
    c2 = shifted(up, -15, -7)
    c1 = shifted(body, -8, -4)
    near = np.zeros_like(body)
    for a_, b_ in NB4 + ((1, 1), (-1, -1), (1, -1), (-1, 1)): near |= shifted(body, a_, b_)
    out = g.copy()
    for m, mode in ((c2, 'hollow'), (c1, 'full')):
        n1 = np.zeros_like(near)
        for a_, b_ in NB4 + ((1, 1), (-1, -1), (1, -1), (-1, 1)): n1 |= shifted(c1, a_, b_)
        for y, x in zip(*np.nonzero(m)):
            if out[y, x] != '.' or near[y, x]: continue          # 1 px air gap to the real body
            if mode == 'hollow' and c1[y, x] | n1[y, x]: continue  # partial copy sits clear of the full copy
            edge = any(not (0 <= x + a_ < N and 0 <= y + b_ < N) or not m[y + b_, x + a_] for a_, b_ in NB4)
            if mode == 'full': out[y, x] = 'p' if edge else 'P'
            elif edge: out[y, x] = 'p'
    # speed bands: 4 bands from the trailing edge, along the travel vector (2:1 iso slope), 2 px: core + rim
    bands = [((33, 60), 13, 'w', 'T'), ((30, 75), 16, 'P', 'p'), ((32, 88), 12, 'w', 'T'), ((36, 98), 9, 'P', 'p')]
    for (x0, y0), L, core, rim in bands:
        for k in range(L):
            x = x0 - k; y = y0 - k // 2
            for (xx, yy, c) in ((x, y, core), (x, y + 1, rim)):
                if 0 <= xx < N and 0 <= yy < N and out[yy, xx] == '.': out[yy, xx] = c
    return kit.orphan_fix(out)


if __name__ == '__main__':
    o = sys.argv[1]; os.makedirs(o, exist_ok=True)
    save(to_rgba(run()), f'{o}/run_SE_f1.png'); save(to_rgba(dash()), f'{o}/dash_SE_f1.png')
