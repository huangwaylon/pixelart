"""Surface eye anchors: rest-space point of each drawn eye (centroid of the illustration eye pixels on the head surface, idle <V> f0),
found again in every frame through the rpos pass -> exact screen position of that surface point (+ hidden if not visible).
Replaces the interior face.* empties (3.8 cm inside the head; in E/W their projection drifts 1.3-3.8 px vs the painted eye)."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from common import *
from facesys import LAYOUT
AJ = json.load(open(ROOT + 'swordswoman/v2/m96/heads/anchor.json'))['views']
KEYS = {'S': ['eye.R', 'eye.L'], 'SE': ['eye.R', 'eye.L'], 'E': ['eye.R']}
_cache = {}
def master_centroids(v):
    M = np.asarray(Image.open(ROOT + f'swordswoman/v2/m96/masters/EC0_{v}_96.png').convert('RGBA')).astype(int)
    out = []
    for e in AJ[v]['eyes']:
        x0, y0 = e['x0'], e['y0']; pts = []
        for y in range(y0 + 1, y0 + 6):
            for x in range(x0 - 1, x0 + 7):
                c = INV.get(tuple(M[y, x, :3]))
                if c in ('K', 'h', 'g', 'L', 'W') and M[y, x, 3]: pts.append((x + .5, y + .5))
        out.append(np.mean(pts, 0))
    return out

def calib(v):
    if v in _cache: return _cache[v]
    d, _ = info('idle', v); f = d['frames'][0]['face']
    rp, ok = rpos('idle', v, 0); t = pass_img('idle', v, 0, 'tex') / 255.; lum = t[..., :3].mean(-1)
    eyeish = ok & (t[..., 3] > .5) & ((lum < .3) | (lum > .85)) & (rp[..., 1] > 0.03)
    yy, xx = np.mgrid[0:1024, 0:1024]
    res = []
    for k, mc, ((ox, oy), side, kind) in zip(KEYS[v], master_centroids(v), LAYOUT[v]):
        A = f[k]['px']; win = eyeish & (np.abs(xx / 8 - A[0]) < 3.5) & (yy / 8 - A[1] < 2.5) & (yy / 8 - A[1] > -3.5)
        P = rp[win].mean(0); cand = rp[ok]; P = cand[((cand - P) ** 2).sum(-1).argmin()]  # snap onto the surface
        res.append(dict(key=k, P=P, off=(ox - mc[0], oy - mc[1])))
    if v == 'SE':  # far eye: the master draws it ~3 px off the 3D head; use the mirror of the near-eye surface point (the head is symmetric)
        Pm = res[0]['P'] * np.array([-1, 1, 1]); cand = rp[ok]; res[1]['P'] = cand[((cand - Pm) ** 2).sum(-1).argmin()]
    _cache[v] = res; return res

def locate(act, v, i, P, r=0.009):
    rp, ok = rpos(act, v, i); dd = np.sqrt(((rp - P) ** 2).sum(-1)); s = ok & (dd < r)
    if s.sum() < 6: return None
    ys, xs = np.where(s); w = 1 / (dd[s] + 1e-3)
    return (float((xs + .5) @ w / w.sum() / 8), float((ys + .5) @ w / w.sum() / 8), int(s.sum()))
