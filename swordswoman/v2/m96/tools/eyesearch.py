"""eyesearch.py DIR [views]: coordinate-descent search of the neutral eye template rows (one construction for all views) +
per-view eye offsets, maximising fidelity (face_ssim, -dE) vs the auto masters in DIR. Writes best rows into eye_spec.json
(front_left.neutral, other expressions keep their lash/lid rows but take the iris rows) and offsets into eye_offsets.json."""
import sys, os, json, itertools, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, '/Users/waylonhuang/Documents/other/pixelart/swordswoman/v2/pixelize/tools')
import eyes as E, pzlib as Z, m96 as M, metrics as MT
D = sys.argv[1]; views = sys.argv[2:] or ['S', 'SE', 'E']
keys, rgb, _ = Z.load_pal(M.PAL); T = '/tmp/m96es'; os.makedirs(T, exist_ok=True)
base = {}; det = {}; G = {}
for v in views:
    G[v] = Z.read(f'{D}/EC0_{v}_96'); det[v] = E.detect(*G[v], v)
    base[v] = MT.metrics(f'{D}/EC0_{v}_96')
POPT = [["KKKK", ".KKK", "KKK.", "KKKKK"[:4]],
        ["K@hh", ".@hh", "K@hK", ".K@h", "..@h", ".@hW"],
        [".hgg", ".hhh", "..hg", ".hKh", "..hh", ".Lhg"],
        ["..LL", "..gg", "....", "..L.", ".LL."]]
OPT = [["KKKKK.", ".KKKK.", "KKKKKK", "KKKK.."],
       ["K@hhh.", ".@hhh.", "K@hhW.", ".@hKh.", "K@hKh.", "KK@hh."],
       [".hggh.", ".hhhh.", ".hKKh.", ".ghhg.", ".LhhL.", ".hgKh."],
       ["..LL..", "..gg..", "......", ".LggL.", "..hh.."]]
MOUTH = [["____", ".mm.", "____"], ["____", "____", "____"], ["____", ".m..", "____"], ["____", "mmm.", "____"]]
prow = [o[0] for o in POPT]
def score(rows, mouth, offs, pr=None):
    E.SPEC['front_left']['neutral'] = ['______'] + rows; E.SPEC['mouth']['neutral'] = mouth
    tot = 0; per = {}
    for v in views:
        g, meta = G[v]; d = json.loads(json.dumps(det[v], default=str))
        dx, dy = offs[v]
        for e in d['eyes']: e['x0'] += dx; e['y0'] += dy
        g2, _ = E.apply(g, meta, v, 'neutral', det=d); Z.save(g2, f'{T}/EC0_{v}_96', keys, rgb, meta)
        r = MT.metrics(f'{T}/EC0_{v}_96'); b = base[v]
        s = (r['face_ssim'] - b['face_ssim']) - 0.05 * (r['dE'] - b['dE']) + 0.5 * (r['ssim_b'] - b['ssim_b'])
        per[v] = s; tot += s
    return tot, per
rows = [o[0] for o in OPT]; mouth = MOUTH[0]; offs = {v: (0, 0) for v in views}
best = score(rows, mouth, offs)
for sweep in range(3):
    for i, opts in enumerate(OPT):
        for o in opts:
            r2 = rows[:]; r2[i] = o; s = score(r2, mouth, offs)
            if s[0] > best[0] + 1e-4: best, rows = s, r2
    for m in MOUTH:
        s = score(rows, m, offs)
        if s[0] > best[0] + 1e-4: best, mouth = s, m
    for v in views:
        for dx in (-2, -1, 0, 1, 2):
            for dy in (0,):
                o2 = dict(offs); o2[v] = (dx, dy); s = score(rows, mouth, o2)
                if s[0] > best[0] + 1e-4: best, offs = s, o2
    print('sweep', sweep, round(best[0], 4), {k: round(x, 4) for k, x in best[1].items()}, rows, prow, mouth, offs, flush=True)
json.dump(dict(rows=rows, prow=prow, mouth=mouth, offs=offs, score=best), open(f'{D}/../eyesearch_result.json', 'w'), indent=1)
