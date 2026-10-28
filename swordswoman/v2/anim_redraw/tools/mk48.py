#!/usr/bin/env python3
"""mk48.py ACT VER [--k n0,n0,...] [--over over.json] -> work48/<act>/plan_<ver>.json (mannequin-key mode).
--k: per-frame candidate '<tag><k>' (n0 = cand/nf00_k0.png). ms/head/bow/blade/fx come from guide/frames.json unless overridden."""
import json, sys
ROOT = '/Users/waylonhuang/Documents/other/pixelart/swordswoman'; A = ROOT + '/v2/anim_redraw'
act, v = sys.argv[1], sys.argv[2]
W = f'{A}/work48/{act}'
mf = json.load(open(f'{W}/guide/frames.json'))['frames']
ks = sys.argv[sys.argv.index('--k') + 1].split(',') if '--k' in sys.argv else ['n0'] * len(mf)
frames = [dict(src=f'cand/{ks[i][:-1]}f{i:02d}_k{ks[i][-1]}.png') for i in range(len(mf))]
plan = dict(action=act, ver=v, name=f'{act}_SE_{v}', mine=1, frames=frames)
if '--over' in sys.argv:
    o = json.load(open(sys.argv[sys.argv.index('--over') + 1]))
    for k, val in o.items():
        if k != 'frames': plan[k] = val
    for i, fo in o.get('frames', {}).items():
        plan['frames'][int(i)].update(fo)
json.dump(plan, open(f'{W}/plan_{v}.json', 'w'), indent=1)
print(f'{W}/plan_{v}.json')
