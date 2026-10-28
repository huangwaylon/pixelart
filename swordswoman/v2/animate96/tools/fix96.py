#!/usr/bin/env python3
"""fix96.py ROOT JOBS FIXES.json  -- one critique-driven fix round: FIXES = {"<act>_<DIR>": {"<frame>": ["fix line", ...]}, ...}
Frames listed under "_first" (e.g. {"_first": ["idle_SE:0"]}) run before the rest (key frame others derive from).
Each frame: ff_redraw fix prompt (edit in place) with the critique lines, head re-pasted, then validate + <=2 lint/gate retries."""
import os, sys, json, itertools, time
from concurrent.futures import ThreadPoolExecutor
V2 = '/Users/waylonhuang/Documents/other/pixelart/swordswoman/v2'
sys.path.insert(0, V2 + '/anim_cut/tools'); import ff_redraw as FR
FR.FFROOT = os.path.abspath(sys.argv[1]); jobs = int(sys.argv[2]); FX = json.load(open(sys.argv[3]))
ACC = os.environ.get('A96_ACC', 'bni_requests,nsystem4,be_system').split(','); cnt = itertools.count()
first = FX.pop('_first', []); FJ = {}
def fj_of(c):
    if c not in FJ:
        act, d = c.rsplit('_', 1); FJ[c] = json.load(open(os.path.join(FR.wd(act, d), 'frames.json')))
        if FR.PALOBJ is None and FJ[c].get('palette'): FR.use_palette(FJ[c]['palette'])
        FR.load_opts(FJ[c])
    return FJ[c]
def go(t):
    c, i, lines = t; act, d = c.rsplit('_', 1); fj = fj_of(c); fr = fj['frames'][i]; out = FR.wd(act, d)
    m = '%s/m96/masters/EC0_%s_96.txt' % (V2, d); st = fr['stamp']; fp = os.path.join(out, 'f%02d.txt' % i); log = os.path.join(out, 'log%02d.txt' % i)
    acc = ACC[next(cnt) % len(ACC)]; t0 = time.time(); k = 0
    ctx = ['CONTEXT: guide for this frame %s/g%02d.txt + g%02d_4x.png; master %s; previous frame %s/f%02d.txt; next frame %s/f%02d.txt' % (
        out, i, i, m, out, (i - 1) % len(fj['frames']), out, (i + 1) % len(fj['frames']))]
    FR.enforce_head(fp, fr)
    pf = os.path.join(out, 'p%02d_crit.txt' % i); open(pf, 'w').write(FR.prompt(act, d, fj, i, m, st, lines + ctx)); FR.call_artist(acc, pf, log)
    FR.enforce_head(fp, fr); fx = FR.validate(fp, fj, st, m)
    while fx and k < 2 and not fx[0].startswith('MISSING'):
        k += 1; pf = os.path.join(out, 'p%02d_crit_fix%d.txt' % (i, k)); open(pf, 'w').write(FR.prompt(act, d, fj, i, m, st, fx)); FR.call_artist(acc, pf, log)
        FR.enforce_head(fp, fr); fx = FR.validate(fp, fj, st, m)
    open(os.path.join(out, 'lint%02d.txt' % i), 'w').write('\n'.join(fx) or 'OK')
    print('%s f%02d %s (%d lint rounds, %ds, %s)' % (c, i, 'OK' if not fx else 'FAIL %s' % [x[:80] for x in fx], k, time.time() - t0, acc), flush=True)
T0 = [(c.split(':')[0], int(c.split(':')[1]), FX[c.split(':')[0]][c.split(':')[1]]) for c in first]
T1 = [(c, int(i), l) for c, fr in FX.items() for i, l in fr.items() if '%s:%s' % (c, i) not in first]
with ThreadPoolExecutor(jobs) as ex: list(ex.map(go, T0))
with ThreadPoolExecutor(jobs) as ex: list(ex.map(go, T1))
print('FIX ROUND DONE', flush=True)
