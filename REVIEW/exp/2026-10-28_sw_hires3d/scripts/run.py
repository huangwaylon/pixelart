"""run.py CLIP[,CLIP] [METHODS] : every style x downscaler (+ fix, +/- head stamp) for all frames of the clips -> out/<clip>/<method>/fNN.{txt,png,json}
methods = <style>_<ds> (style shade|cel|celo|flat, ds kc|area|paf|poe) and matv (material vote + lum bands); each also as <m>_hs (m96 head stamp).
Alignment: one integer (dx,dy) per view from the rest frame (soles -> master bottom row, feet centre -> master feet centre), applied in hi-res."""
import sys, os, json, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hx
from multiprocessing import Pool
MAST = hx.SW + 'v2/m96/masters/EC0_{}_96.txt'
ALL = [f'{s}_{d}' for s in ('shade', 'cel', 'celo') for d in ('kc', 'area', 'paf', 'poe')] + ['flat_kc', 'matv']


def feet(a):
    ys = np.where(a.any(1))[0]; yb = ys.max(); xs = np.where(a[yb - 4:yb + 1].any(0))[0]; return yb, (xs.min() + xs.max()) / 2


def align(view):
    p = hx.EXP + f'out/align_{view}.json'
    if os.path.exists(p): return json.load(open(p))
    F = hx.load(f'rest_{view}', 0); a = hx.cells(F['alpha'].astype(float)).mean((2, 3)) > 0.5
    m = hx.read_grid(MAST.format(view)) != '.'
    yb, xc = feet(a); mb, mc = feet(m); r = {'dx': int(round(mc - xc)), 'dy': int(mb - yb)}
    os.makedirs(hx.EXP + 'out', exist_ok=True); json.dump(r, open(p, 'w')); return r


def head_clear(F, mg, al, sh):
    nk = F['meta']['pts']['neck'][1] - 32 + sh['dy']
    rows = np.arange(hx.N)[:, None] < nk + 1
    hm = np.isin(mg, [hx.MN.index(k) for k in ('hair', 'skin', 'eyes', 'bow')]) & rows
    return hm


def one(args):
    clip, i, methods = args; view = clip.split('_')[1]; sh = align(view)
    F = hx.load(clip, i, sh['dx'], sh['dy']); mg = hx.mat_grid(F)
    R = hx.load(f'rest_{view}', 0)['meta']['pts']['head']; H = F['meta']['pts']['head']
    t, x0, y0 = hx.stamp_of(view); x0 += int(round(H[0] - R[0])); y0 += int(round(H[1] - R[1]))
    cache = {}
    for m in methods:
        od = hx.EXP + f'out/{clip}/{m}'; os.makedirs(od, exist_ok=True); os.makedirs(od + '_hs', exist_ok=True)
        if m == 'matv':
            g, _ = hx.ds_matv(F, 'cel'); a = g != '.'
        else:
            st, ds = m.split('_')
            if st not in cache: cache[st] = hx.STYLES[st](F)
            img, al = cache[st]
            lo, a = hx.ds_paf(img, al, f'{clip}{i}{st}') if ds == 'paf' else hx.DS[ds](img, al)
            mgx = np.where(a & (mg < 0), hx.MN.index('dress'), mg)  # cells kept by the ds but not by the vote: default ramp
            g = hx.snap_mat(lo, a, mgx)
        lines = not m.startswith(('celo', 'shade'))  # those styles already carry lines
        g1 = hx.fix(g, F, mg, lines=lines)
        hx.save(g1, od + f'/f{i:02d}', view)
        g2 = g1.copy(); g2[head_clear(F, mg, g1 != '.', sh)] = '.'
        g2 = hx.paste(g2, t, x0, y0); g2 = hx.Z.clean_orphans(g2, keep='WK')
        hx.save(g2, od + f'_hs/f{i:02d}', view)
    return clip, i


if __name__ == '__main__':
    clips = sys.argv[1].split(','); methods = sys.argv[2].split(',') if len(sys.argv) > 2 else ALL
    for c in clips: align(c.split('_')[1])
    jobs = []
    for c in clips:
        n = len(json.load(open(hx.EXP + f'big/{c}/{c}.json'))['frames'])
        if c.startswith('rest'): n = 1
        jobs += [(c, i, methods) for i in range(n)]
    with Pool(int(os.environ.get('NP', '8'))) as p:
        for c, i in p.imap_unordered(one, jobs): print('ok', c, i, flush=True)
