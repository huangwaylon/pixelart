#!/usr/bin/env python3
"""run96.py ROOT JOBS CLIP[:frames] ...  -- one shared artist pool over many prepped ff_redraw clips (96 px pipeline).
CLIP = <act>_<DIR> dir under ROOT (prepped by ff_redraw.py prep ... --root ROOT, opts stored in frames.json).
Phase 1 = frame 0 of every clip (continuity key), phase 2 = the rest. Master = v2/m96/masters/EC0_<V>_96.txt (W/SW/NW: mirror
not supported here - prep the mirrored view from E/SE/NE). Accounts round-robin: env A96_ACC (default bni_requests,nsystem4,be_system).
Skips frames whose lintNN.txt says OK unless --redo. Log line per frame; summary at the end."""
import os, sys, json, itertools, time
from concurrent.futures import ThreadPoolExecutor
V2 = '/Users/waylonhuang/Documents/other/pixelart/swordswoman/v2'
sys.path.insert(0, V2 + '/anim_cut/tools'); import ff_redraw as FR
a = sys.argv[1:]; redo = '--redo' in a; a = [x for x in a if x != '--redo']
FR.FFROOT = os.path.abspath(a[0]); jobs = int(a[1])
ACC = os.environ.get('A96_ACC', 'bni_requests,nsystem4,be_system').split(',')
t0s, t1s, FJ = [], [], {}
for c in a[2:]:
    c, _, fr = c.partition(':'); act, d = c.rsplit('_', 1)
    fj = json.load(open(os.path.join(FR.wd(act, d), 'frames.json'))); FJ[c] = fj
    if FR.PALOBJ is None and fj.get('palette'): FR.use_palette(fj['palette'])
    FR.load_opts(fj)
    idx = [int(x) for x in fr.split(',')] if fr else range(len(fj['frames']))
    for i in idx:
        lp = os.path.join(FR.wd(act, d), 'lint%02d.txt' % i)
        if not redo and os.path.exists(lp) and open(lp).read().strip() == 'OK': continue
        (t0s if (i == 0 and not fr) else t1s).append((act, d, i))
cnt = itertools.count(); res = []
def go(t):
    act, d, i = t; acc = ACC[next(cnt) % len(ACC)]; m = '%s/m96/masters/EC0_%s_96.txt' % (V2, d); t1 = time.time()
    try: fx = FR.draw_one(act, d, FJ['%s_%s' % (act, d)], i, m, None, acc, 2)
    except Exception as e: fx = ['ERROR %s' % e]
    res.append((act, d, i, len(fx), round(time.time() - t1))); print('%s_%s f%02d %s %ds %s' % (act, d, i, 'OK' if not fx else 'FAIL%d' % len(fx), time.time() - t1, acc), flush=True)
T = time.time()
with ThreadPoolExecutor(jobs) as ex: list(ex.map(go, t0s))
with ThreadPoolExecutor(jobs) as ex: list(ex.map(go, t1s))
print('ALL DONE %d frames, %d OK, %ds wall' % (len(res), sum(r[3] == 0 for r in res), time.time() - T), flush=True)
