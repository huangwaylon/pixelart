"""p2_eval.py (P): pxeval seq for every render/out/p2/<act>/<act>_<view>_px (P2) and render/out/p2/r1/... (round-1 chain, same passes)
-> render/out/p2/pxeval/<tag>_<act>_<view>.json + render/out/p2/pxeval/table.md"""
import os, json, subprocess, glob
EXP = '/Users/waylonhuang/Documents/other/pixelart/REVIEW/exp/2026-10-28_sw_skinned/'
R = '/Users/waylonhuang/Documents/other/pixelart/'; PY = R + '.models/pixtools/venv/bin/python'
OUT = os.environ.get('POUT', 'p2'); od = EXP + f'render/out/{OUT}/pxeval/'; os.makedirs(od, exist_ok=True)
K = ['boil', 'shade_swap', 'flicker', 'articulation_per_s', 'rigid_share', 'motion_px', 'feet_range', 'pose_range']
rows = []
for act in os.environ.get('ACTS', 'walk run idle jump').split():
    for v in os.environ.get('VIEWS', 'SE E S').split():
        js = EXP + f'render/out/{OUT}/{act}/{act}_{v}.json'
        if not os.path.exists(js): continue
        ms = [str(f['ms']) for f in json.load(open(js))['frames']]
        for tag, d in (('r1', EXP + f'render/out/p2/r1/{act}/{act}_{v}_px'), (OUT.upper(), EXP + f'render/out/{OUT}/{act}/{act}_{v}_px')):
            if not glob.glob(d + '/f*.png'): continue
            cmd = [PY, '-I', R + 'pipeline/tools/pxeval.py', 'seq', d + '/f*.png', '--ms', *ms, '--loop', 'no' if act.startswith(('jump', 'dash', 'hurt')) else 'yes']
            o = json.loads(subprocess.run(cmd, capture_output=True, text=True, cwd=R).stdout)
            json.dump(o, open(od + f'{tag}_{act}_{v}.json', 'w'), indent=0)
            rows.append((act, v, tag, o))
with open(od + 'table.md', 'w') as f:
    f.write('| act | view | chain | ' + ' | '.join(K) + ' | flags |\n|' + '---|' * (len(K) + 4) + '\n')
    for act, v, tag, o in rows:
        f.write(f'| {act} | {v} | {tag} | ' + ' | '.join(f"{o.get(k):.3f}" if isinstance(o.get(k), float) else str(o.get(k)) for k in K) + f" | {' '.join(o['flags'])} |\n")
print(open(od + 'table.md').read())
