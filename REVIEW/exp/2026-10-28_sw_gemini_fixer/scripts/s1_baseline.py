"""Step 1 baseline: pixel-art-fixer on existing Gemini 'pixel art' outputs. Fixer venv.
Writes work/base/<name>_{fix,nat,r96,info}.* and work/base/baseline.json"""
import sys, os, glob, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fixlib as F

SW = F.SW
E = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/'
OUT = E + 'work/base/'
os.makedirs(OUT, exist_ok=True)
items = []
for n in ['g48s_a', 'g48n_a', 'g48s_b', 'g48n_b', 'g40s_a', 'g40n_a', 'c48s_se', 'c48n_se', 'c56s_se', 'c48s_e', 'c48n_e']:
    items.append(('pixel_' + n, SW + f'v2/pixel/gem/{n}.png', 'E' if n.endswith('_e') else 'SE'))
for v in range(4):
    items.append((f'pixE_mk_v{v}', SW + f'archive/v2/pixel_E/work/master_k/raw_mk_f00_v{v}.png', 'E'))
for n in ['SE_64', 'SE_80', 'SE_96', 'S_48', 'S_64', 'S_80', 'S_96']:
    items.append(('pzD_' + n, SW + f'v2/pixelize/D/gem_{n}.png', n.split('_')[0]))
for n in ['raw_nc_f00', 'raw_nc_f01']:
    items.append(('anim_walk_' + n, SW + f'v2/pixel/anim/walk_SE/{n}.png', 'SE'))
for n in ['raw_d2f00_k0', 'raw_d2f02_k1']:
    items.append(('redraw_walk_' + n, SW + f'v2/anim_redraw/work/walk_SE/cand/{n}.png', 'SE'))
res = []
for name, p, view in items:
    if not os.path.exists(p): print('missing', p); continue
    try:
        r = F.run(p, OUT + name, view)
        r.update(name=name, view=view); res.append(r)
    except Exception as e:
        print('FAIL', name, e); res.append({'name': name, 'in': p, 'error': str(e)})
json.dump(res, open(OUT + 'baseline.json', 'w'), indent=1)
