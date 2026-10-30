"""Temporal stability of the face ink: per frame, count of eye/brow pixels by colour drawn by (a) vs (b') over whole clips."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from proto import *
res = {}
for act, v, n in [('idle', 'SE', 12), ('run', 'E', 8), ('walk', 'SE', 8), ('jump', 'S', 16), ('idle', 'S', 12)]:
    rows = []
    for i in range(n):
        a, base, at, b, ex, c, b2 = proto(act, v, i)
        def ink(im):
            d = (im[..., :3] != base[..., :3]).any(-1); ch = [INV.get(tuple(p)) for p in im[d][:, :3]]
            return {k: ch.count(k) for k in 'KgWh'}
        rows.append((i, ex, ink(at), ink(b2)))
    res[f'{act}_{v}'] = rows
    for r in rows: print(act, v, r)
json.dump(res, open(os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/stability.json', 'w'), indent=0)
