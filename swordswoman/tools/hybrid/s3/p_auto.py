import sys, glob, os, shutil; sys.path.insert(0, 'tools/hybrid/s3')
from pol import *
R = 'hybrid/S3_editchain/r1'
HD = lambda n: n.split('_')[1] if n.startswith('turn_') else ('E' if n.startswith('jump_E') else 'SE')
os.makedirs(f'{R}/wip/auto', exist_ok=True)
for p in sorted(glob.glob(f'{R}/sprite_px/*_meta.json')):
    n = os.path.basename(p)[:-10]
    src = f'{R}/wip/pol/{n}_e.png' if os.path.exists(f'{R}/wip/pol/{n}_e.png') else f'{R}/sprite_px/{n}_rt.png'
    a = load(src)
    M = stamp_mask(p, HD(n))
    a = collar_bridge(a, M)
    a = ribbon_bridge(a, M)
    save(body_pass(a, M), f'{R}/wip/auto/{n}.png')
print('ok')
