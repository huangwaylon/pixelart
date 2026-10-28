#!/usr/bin/env python3
"""mkplan.py ACT VERSION [--over over.json]: plan from sel.json + r6 meta + per-action defaults (+ overrides).
Writes work/<act>_SE/plan_<v>.json"""
import json, sys, os
ROOT = '/Users/waylonhuang/Documents/other/pixelart/swordswoman'
act, v = sys.argv[1], sys.argv[2]
W = f'{ROOT}/v2/anim_redraw/work/{act}_SE'
meta = json.load(open(f'{ROOT}/v2/anim/guides/{act}_SE/frames.json'))['frames']
tag = sys.argv[sys.argv.index('--tag') + 1] if '--tag' in sys.argv else ''
sel = json.load(open(f'{W}/sel{tag}.json')) if os.path.exists(f'{W}/sel{tag}.json') else {}
TILT = {'squash': 'squash', 'forward': 'lean', 'back': 'neutral', 'neutral': 'neutral'}
frames = []
for i, md in enumerate(meta):
    frames.append(dict(src=f'cand/{tag}f{i:02d}_k{sel.get(str(i), 0)}.png', head=TILT[md.get('head_tilt', 'neutral')],
                       ms=md['ms'], fx=[], motion=[1, 0.5]))
plan = dict(master=ROOT + '/v2/anim_redraw/master/SE_nokatana_D2.png', action=act, out=f'{W}/{v}', name=f'{act}_SE_{v}', frames=frames)
if '--over' in sys.argv:
    o = json.load(open(sys.argv[sys.argv.index('--over') + 1]))
    for k, val in o.items():
        if k != 'frames': plan[k] = val
    for i, fo in o.get('frames', {}).items():
        plan['frames'][int(i)].update(fo)
json.dump(plan, open(f'{W}/plan_{v}.json', 'w'), indent=1)
print(f'{W}/plan_{v}.json')
