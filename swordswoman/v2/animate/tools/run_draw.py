#!/usr/bin/env python3
"""Drive ff_redraw.draw_one over many clips with one global worker pool.
run_draw.py JOBS CLIP[:frames] ...   CLIP = S/act  e.g. A/walk  A/slash:3,4   (dir SE, master SE_k)
Phase 1 draws frame 0 of every clip (continuity key), phase 2 the rest."""
import os, sys, json, itertools
from concurrent.futures import ThreadPoolExecutor
V2 = '/Users/waylonhuang/Documents/other/pixelart/swordswoman/v2'
sys.path.insert(0, V2 + '/anim_cut/tools'); import ff_redraw as FR
W = V2 + '/animate/work'
FR.wd = lambda act, d: os.path.join(W, act.split('@')[1], '%s_%s' % (act.split('@')[0], d))
_p = FR.prompt
FR.prompt = lambda act, d, *a, **k: _p(act, d, *a, **k).replace('ACTION ' + act, 'ACTION ' + act.split('@')[0])
MASTER = V2 + '/masters/SE_k.txt'; ACC = ['be_system', 'bni_requests', 'nsystem4']
jobs = int(sys.argv[1]); tasks0, tasks1 = [], []
for c in sys.argv[2:]:
    c, _, fr = c.partition(':'); S, act = c.split('/'); a = act + '@' + S
    fj = json.load(open(os.path.join(FR.wd(a, 'SE'), 'frames.json')))
    idx = [int(x) for x in fr.split(',')] if fr else range(len(fj['frames']))
    for i in idx: (tasks0 if (i == 0 and not fr) else tasks1).append((a, fj, i))
cnt = itertools.count()
def go(t):
    a, fj, i = t; acc = ACC[next(cnt) % 3]
    fx = FR.draw_one(a, 'SE', fj, i, MASTER, None, acc, 2); print(a, i, 'done', len(fx), flush=True)
with ThreadPoolExecutor(jobs) as ex: list(ex.map(go, tasks0))
with ThreadPoolExecutor(jobs) as ex: list(ex.map(go, tasks1))
print('ALL DONE', flush=True)
