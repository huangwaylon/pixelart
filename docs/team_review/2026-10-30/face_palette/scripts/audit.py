"""Palette consistency audit of build 20261030_66119a7 (final 1x frames, all 6 actions x 8 dirs).
Per frame: #colours, off-palette px; per material (guide matid of the 8x pass, block majority) the palette keys actually used;
shade_swap / boil from the build's own pxeval gate jsons (work/gates/pxeval_<act>_<dir>.json)."""
import sys, os, glob, collections
sys.path.insert(0, os.path.dirname(__file__))
from common import *
OUT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/'
ACTS = ['idle', 'walk', 'run', 'jump', 'dash', 'hurt']; DIRS = ['S', 'SE', 'E', 'NE', 'N', 'NW', 'W', 'SW']
MN = list(hx.MATS); MCx = np.array([hx.MATS[k] for k in MN], float)
def matmap(act, v, i):
    try: g = pass_img(act, v, i, 'guide')
    except Exception: return None
    al = g[..., 3] > 128; d = ((g[..., None, :3] - MCx[None, None]) ** 2).sum(-1); mid = d.argmin(-1); mid[~al] = len(MN)
    b = blocks(mid[..., None])[..., 0]  # 128,128,64
    cnt = np.stack([(b == k).sum(-1) for k in range(len(MN) + 1)], -1)
    return cnt.argmax(-1)
if __name__ == '__main__':
    rows = []; per_mat = collections.defaultdict(collections.Counter); per_view_mat = collections.defaultdict(collections.Counter)
    nframes = 0; offpal = 0; ncol = []
    for act in ACTS:
        for v in DIRS:
            fs = sorted(glob.glob(f'{B}{act}/{v}/final/f??.png'))
            for i, p in enumerate(fs):
                a = np.asarray(Image.open(p).convert('RGBA')); m = a[..., 3] > 0
                keys = [INV.get(tuple(c)) for c in a[m][:, :3]]
                cc = collections.Counter(keys); offpal += cc.pop(None, 0); ncol.append((act, v, i, len(cc))); nframes += 1
                if i % 2 == 0:  # material attribution on every 2nd frame (cost)
                    mm = matmap(act, v, i)
                    if mm is None: continue
                    ys, xs = np.where(m)
                    for y, x, k in zip(ys, xs, keys):
                        if mm[y, x] < len(MN): per_mat[MN[mm[y, x]]][k] += 1; per_view_mat[(v, MN[mm[y, x]])][k] += 1
    gates = {}
    for f in glob.glob(B + 'gates/pxeval_*.json'):
        j = json.load(open(f)); n = os.path.basename(f)[7:-5]
        gates[n] = {k: j.get(k) for k in ('shade_swap', 'boil', 'flicker', 'flags')}
    res = {'frames': nframes, 'offpal_px': offpal,
           'colours_per_frame': {'min': min(c[3] for c in ncol), 'max': max(c[3] for c in ncol), 'mean': float(np.mean([c[3] for c in ncol]))},
           'colours_by_dir': {v: float(np.mean([c[3] for c in ncol if c[1] == v])) for v in DIRS},
           'union_keys': sorted(set(k for c in per_mat.values() for k in c if k)),
           'per_material': {k: dict(c.most_common()) for k, c in per_mat.items()},
           'per_view_material': {f'{v}:{m}': dict(c.most_common()) for (v, m), c in per_view_mat.items() if m in ('skin', 'hair')},
           'gates': gates}
    json.dump(res, open(OUT + 'palette_audit.json', 'w'), indent=1)
    print(json.dumps({k: res[k] for k in ('frames', 'offpal_px', 'colours_per_frame', 'colours_by_dir', 'union_keys')}))
    for k, c in res['per_material'].items():
        tot = sum(c.values()); print(k, tot, ' '.join(f'{a}:{100*b/tot:.1f}' for a, b in c.items() if 100 * b / tot >= 0.3))
    for k, c in sorted(res['per_view_material'].items()):
        tot = sum(c.values()); print(k, ' '.join(f'{a}:{100*b/tot:.1f}' for a, b in c.items() if 100 * b / tot >= 1))
    ss = sorted(gates.items(), key=lambda t: -(t[1]['shade_swap'] or 0))
    print('shade_swap top', [(n, g['shade_swap'], g['boil']) for n, g in ss[:10]])
    print('shade_swap mean', np.mean([g['shade_swap'] for g in gates.values() if g['shade_swap'] is not None]))

