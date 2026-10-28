"""facemetrics.py DIR [DIR..]: face fidelity vs the illustration measurements (face_measure.json, sprite coords):
eye-line delta (lash top, iris centre), chin/jaw contour delta (S jaw edges rows 56-60, SE far cheek+jaw rows 54-60, E profile rows 49-61), + metrics.py face_ssim"""
import sys, json, os, subprocess
R = '/Users/waylonhuang/Documents/other/pixelart/swordswoman/'
FM = json.load(open(R + 'v2/m96/face_measure.json'))['views']
SK = set('sSmk')
def rd(p): return [l.rstrip('\n') for l in open(p) if l.strip() and not l.startswith(';')]
def lash(g, x0, x1):
    for y in range(44, 58):
        if sum(1 for x in range(x0, x1 + 1) if g[y][x] == 'K') >= 2: return y   # eye round: arched top = 2-3 K (far eye 2)
def eyeline(g, v):
    sp = FM[v]['spr']; out = []
    exs = sp['eye_x'] if isinstance(sp['eye_x'][0], list) else [sp['eye_x']]
    lts = sp['lash_top'] if isinstance(sp['lash_top'], list) else [sp['lash_top']] * len(exs)
    ics = sp['iris_c'] if isinstance(sp['iris_c'][0], list) else [sp['iris_c']]
    for (a, b), lt, ic in zip(exs, lts, ics):
        y = lash(g, int(a), int(b)); out.append((round(y - lt, 2), round(y + 2.5 - ic[1], 2)))   # lash top edge; iris centre = lash + 2.5
    return out
def contour(g, v):
    c = FM[v]['spr']['contour']; d = []
    for r, (L, Rr) in c.items():
        r = int(r); row = g[r]
        if v == 'SE' and r < 54: continue   # far eye interrupts the scan
        if v in ('S', 'SE'):
            cx = 63 if v == 'S' else 68
            ls = [x for x in range(52, cx + 1) if row[x] in 'sSk']; rs = [x for x in range(cx, 80) if row[x] in 'sSk']
            if L is not None and ls: d.append(abs(min(ls) - L))
            if Rr is not None and rs: d.append(abs(max(rs) + 1 - Rr))
        else:
            xs = [x for x in range(66, 83) if row[x] not in '.K']
            if xs and Rr is not None: d.append(abs(max(xs) + 1 - Rr))
    return round(sum(d) / len(d), 3), len(d)
def fssim(d):
    py = R + '.scratch/pixtools/venv/bin/python'; tmp = '/tmp/fm_%d.json' % os.getpid()
    subprocess.run([py, '-I', R + 'v2/pixelize/tools/metrics.py'] + [f'{d}/EC0_{v}_96' for v in ('S', 'SE', 'E')] + ['--json', tmp], capture_output=True, cwd=R)
    r = json.load(open(tmp)); os.remove(tmp)
    get = lambda k: r[k] if isinstance(r, dict) else next(x for x in r if x.get('name') == k)
    return {v: round(get(f'EC0_{v}_96')['face_ssim'], 3) for v in ('S', 'SE', 'E')}
if __name__ == '__main__':
    res = {}
    for d in sys.argv[1:]:
        fs = fssim(d); res[d] = {}
        for v in ('S', 'SE', 'E'):
            g = rd(f'{d}/EC0_{v}_96.txt'); el = eyeline(g, v); cd = contour(g, v)
            res[d][v] = dict(face_ssim=fs[v], eye_lash_delta=[e[0] for e in el], eye_iris_delta=[e[1] for e in el], contour_mae=cd[0])
            print(f'{os.path.basename(d.rstrip("/")):10s} {v:2s} face_ssim={fs[v]:.3f} lash_d={[e[0] for e in el]} iris_d={[e[1] for e in el]} contour_mae={cd[0]:.2f}px (n={cd[1]})')
    json.dump(res, open(R + 'v2/m96/face2/facemetrics.json', 'w'), indent=1)
