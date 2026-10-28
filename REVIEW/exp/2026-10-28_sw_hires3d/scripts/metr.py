"""metr.py : metrics.py (vs illustration) for every rest candidate + the m96 master (re-scored against the same illustration), plus
direct agreement with the m96 master (sil IoU, same-char %, mean Lab dE on the union).  -> out/metrics_<V>.json"""
import sys, os, json, subprocess, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hx, run
sys.path.insert(0, hx.SW + 'v2/pixelize/tools'); import metrics as MT
from skimage.color import deltaE_ciede2000


def vs_master(g, gm):
    a, b = g != '.', gm != '.'; u = a | b
    la = hx.Z.rgb2lab(np.array(hx.render(g, bg=(255, 255, 255))).astype(float)); lb = hx.Z.rgb2lab(np.array(hx.render(gm, bg=(255, 255, 255))).astype(float))
    return {'m_sil': round(float((a & b).sum() / u.sum()), 3), 'm_same': round(float(((g == gm) & u).sum() / u.sum()), 3), 'm_dE': round(float(deltaE_ciede2000(la[u], lb[u]).mean()), 2)}


if __name__ == '__main__':
    K = ['ssim_b', 'dE', 'sil', 'face_ssim', 'orph', 'line_f', 'm_sil', 'm_same', 'm_dE']
    for v in sys.argv[1].split(','):
        gm = hx.read_grid(hx.SW + f'v2/m96/masters/EC0_{v}_96.txt'); d = hx.EXP + f'out/rest_{v}/'
        os.makedirs(d + 'master', exist_ok=True); hx.save(gm, d + 'master/f00', v)
        rows = {}
        for m in ['master'] + [m + s for m in run.ALL for s in ('', '_hs')]:
            r = MT.metrics(d + f'{m}/f00'); r.update(vs_master(hx.read_grid(d + f'{m}/f00.txt'), gm)); rows[m] = {k: r.get(k) for k in K}
        json.dump(rows, open(hx.EXP + f'out/metrics_{v}.json', 'w'), indent=0)
        print(v, ''.join(k[:8].rjust(9) for k in K))
        for m, r in rows.items(): print(m[:16].ljust(16) + ''.join((f'{r[k]:9.3f}' if isinstance(r[k], float) else str(r[k]).rjust(9)) for k in K))
