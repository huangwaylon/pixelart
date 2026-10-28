#!/usr/bin/env python3
"""Score candidates vs guide silhouette. sel.py ACTION [--dir SE] -> prints per frame scores, writes work/<act>/sel.json
(best k per frame) + work/<act>/cands.png sheet (rows = frames)."""
import sys, os, json, glob, re
import numpy as np
from PIL import Image
ROOT = '/Users/waylonhuang/Documents/other/pixelart/swordswoman'
sys.path.insert(0, ROOT + '/v2/pixel/anim'); import fx2  # noqa
act = sys.argv[1]; d = sys.argv[sys.argv.index('--dir') + 1] if '--dir' in sys.argv else 'SE'
W = f'{ROOT}/v2/anim_redraw/work/{act}_{d}'
tag = sys.argv[sys.argv.index('--tag') + 1] if '--tag' in sys.argv else ''


def gmask(i):
    g = np.array(Image.open(f'{W}/_guide_f{i:02d}.png').convert('RGB')).astype(int)
    g = g.reshape(128, 8, 128, 8, 3)[:, 4, :, 4]
    bg = (np.abs(g - 192).sum(-1) < 12)
    white = (g.min(-1) > 215)                     # guide blade
    return ~bg & ~white


def comps(mask):
    from collections import deque
    seen = np.zeros_like(mask); n = 0
    for y, x in zip(*np.nonzero(mask)):
        if seen[y, x]: continue
        n += 1; q = deque([(y, x)]); seen[y, x] = 1
        while q:
            cy, cx = q.popleft()
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    yy, xx = cy + dy, cx + dx
                    if 0 <= yy < 128 and 0 <= xx < 128 and mask[yy, xx] and not seen[yy, xx]:
                        seen[yy, xx] = 1; q.append((yy, xx))
    return n


def score(p, i):
    a = np.array(Image.open(p).convert('RGBA'))
    op = (a[..., 3] >= 128) & ~fx2.m(a, 'mnw')
    gm = gmask(i)
    iou = (op & gm).sum() / max(1, (op | gm).sum())
    ys = np.nonzero(gm.any(1))[0]; cut = int(ys.max() - (ys.max() - ys.min()) * 0.33)
    lo, glo = op.copy(), gm.copy(); lo[:cut] = 0; glo[:cut] = 0
    liou = (lo & glo).sum() / max(1, (lo | glo).sum())
    iris = fx2.m(a, 'iI'); oys = np.nonzero(op.any(1))[0]
    iris[int(oys.min() + (oys.max() - oys.min()) * 0.6):] = 0
    ok = iris.sum() >= 4 and comps(iris) <= 3
    return round(0.5 * iou + 0.5 * liou, 3), round(iou, 3), round(liou, 3), ok


res = {}; rows = []
for p in sorted(glob.glob(f'{W}/cand/{tag}f??_k*.png')):
    i, k = map(int, re.findall(r'f(\d+)_k(\d+)', os.path.basename(p))[0])
    s = score(p, i); res.setdefault(i, []).append((s[0] if s[3] else s[0] - 1, k, s))
best = {}
for i in sorted(res):
    r = sorted(res[i], reverse=True); best[i] = r[0][1]
    print(f'f{i:02d}', ' '.join(f'k{k}:{s[0]}({s[1]}/{s[2]}){"" if s[3] else "X"}' for _, k, s in sorted(res[i], key=lambda t: t[1])), '-> k', best[i])
json.dump(best, open(f'{W}/sel{tag}.json', 'w'))
# sheet: rows = frames, cols = guide + candidates
n = max(len(v) for v in res.values()); S = 3
sh = Image.new('RGB', ((n + 1) * 128 * S, len(res) * 128 * S), (110, 110, 110))
for r_, i in enumerate(sorted(res)):
    g = Image.open(f'{W}/_guide_f{i:02d}.png').resize((128 * S, 128 * S)); sh.paste(g, (0, r_ * 128 * S))
    for c, (_, k, _) in enumerate(sorted(res[i], key=lambda t: t[1])):
        im = Image.open(f'{W}/cand/{tag}f{i:02d}_k{k}.png').convert('RGBA').resize((128 * S, 128 * S), Image.NEAREST)
        sh.paste(im, ((c + 1) * 128 * S, r_ * 128 * S), im)
sh.save(f'{W}/cands{tag}.png')
