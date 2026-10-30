import sys, numpy as np
sys.path.insert(0, '.'); import build_gold as B
m = np.array([list(l.rstrip('\n')) for l in open(B.MASTER)]) != '.'
out = {}
for f in ('contact', 'passing'):
    g = np.array([list(l.rstrip('\n')) for l in open(f'walk_SE_{f}.txt')]) != '.'
    r = {}
    for nm, (y0, y1) in {'full': (0, 128), 'head': (26, 66), 'torso': (63, 92), 'head+torso': (26, 92)}.items():
        best = 0
        for dy in range(-2, 3):          # allow the walk bob
            gs = np.roll(g, -dy, 0)
            a, b = gs[y0:y1], m[y0:y1]
            best = max(best, (a & b).sum() / (a | b).sum())
        r[nm] = round(float(best), 3)
    out[f] = r
print(out)
import json; json.dump(out, open('iou_vs_master.json', 'w'), indent=1)
