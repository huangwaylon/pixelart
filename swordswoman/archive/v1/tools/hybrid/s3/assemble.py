import os, shutil, json, glob
R = 'hybrid/S3_editchain/r1'
SRC = {'slash_SE_k0': 'wip/pol/slash_SE_k0_s.png', 'slash_SE_k1': 'wip/pol/slash_SE_k1_s2.png',
       'slash_SE_k2': 'wip/pol/slash_SE_k2_s.png', 'slash_SE_k3': 'wip/pol/slash_SE_k3_s.png',
       'jump_E_land': 'wip/pol/jump_E_land_s.png', **{f'walk_SE_k{k}': f'wip/pol/walk_SE_k{k}_s.png' for k in range(4)}}
SRC.update({n: f'wip/pol/{n}_bow.png' for n in ['walk_SE_k1', 'walk_SE_k3', 'slash_SE_k1', 'slash_SE_k2', 'slash_SE_k3', 'jump_E_crouch', 'jump_E_land']})
SRC.update({f'slash_SE_k{k}': f'wip/pol/slash_SE_k{k}_face.png' for k in range(4)})
SRC.update(json.load(open(f'{R}/src_override.json')) if os.path.exists(f'{R}/src_override.json') else {})
os.makedirs(f'{R}/sprite', exist_ok=True)
names = [os.path.basename(p)[:-10] for p in glob.glob(f'{R}/sprite_px/*_meta.json')]
gm = {}
import sys; sys.path.insert(0, 'tools/hybrid/s3'); from s3guides import GUIDE
for n in sorted(names):
    shutil.copy(f"{R}/{SRC.get(n, 'wip/auto/' + n + '.png')}", f'{R}/sprite/{n}.png')
    shutil.copy(f'{R}/sprite_px/{n}_hires.png', f'{R}/sprite/{n}_hires.png')   # aligned 4x hi-res source (original: hires/<n>.png)
    os.makedirs(f'{R}/sprite/guide', exist_ok=True)
    shutil.copy(f'hybrid/guide/p2/cells/{n}.png', f'{R}/sprite/guide/{n}.png')
    gm[n] = GUIDE[n]
json.dump(gm, open(f'{R}/guide_map.json', 'w'), indent=1)
print(len(names))
