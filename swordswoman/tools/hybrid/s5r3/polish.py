"""S5 r3 POLISH + ASSEMBLY (Claude hand pixels). fx/<name>.png -> sprite/<name>.png for the S5-owned keys
(slash_SE, jump_E, run_SE_f1, dash_SE_f1); turn_* and walk_SE_* are COPIED as-is from S3's r3 output.
Per-sprite hand edits (FIX) run first, then the orphan merge (no protected regions: lock3 head orphans would show
up here and are reported, not excluded). Writes <name>_4x.png, <name>_fxmask.png (pixels the FX stage painted, for
metrics), <name>_hires.png (the Gemini hi-res acting ref for the key, when one exists), <name>_meta.json, and logs
every edit to work/edits.json (with the fx-stage edits)."""
import sys, os, json, shutil, hashlib
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, '/Users/waylonhuang/Documents/other/pixelart/swordswoman/tools/hybrid/s5r2')
import patch as P, deorphan
ROOT = '/Users/waylonhuang/Documents/other/pixelart/swordswoman'
R3 = f'{ROOT}/hybrid/S5_pixelnative/r3'
S3 = os.environ.get('S3_SRC', f'{ROOT}/hybrid/S3_editchain/r3/sprite')
OUT = f'{R3}/sprite'
LOG = []
def note(n, what, why): LOG.append(dict(sprite=n, stage='polish', edit=what, reason=why))
HIRES = {'slash_SE_k0': 'pose/slash_SE_k0_hires.png', 'slash_SE_k1': 'pose/slash_SE_k1_r2_hires.png',
         'slash_SE_k2': 'pose/slash_SE_k2_hires.png', 'slash_SE_k3': 'pose/slash_SE_k3_hires.png',
         'jump_E_crouch': 'pose/jump_E_crouch_r2_hires.png', 'jump_E_apex': 'pose/jump_E_apex_hires.png',
         'jump_E_land': 'pose/jump_E_land_r2_hires.png'}
FIX = {}
OWN = ['slash_SE_k0', 'slash_SE_k1', 'slash_SE_k2', 'slash_SE_k3', 'jump_E_crouch', 'jump_E_apex', 'jump_E_land',
       'run_SE_f1', 'dash_SE_f1']

def sha(p): return hashlib.sha256(open(p, 'rb').read()).hexdigest()

def run():
    if os.path.isdir(OUT): shutil.rmtree(OUT)
    os.makedirs(OUT); os.makedirs(f'{OUT}/bonus'); os.makedirs(f'{R3}/hires', exist_ok=True)
    src = {}
    for d in ['S', 'SE', 'E', 'NE', 'N', 'NW', 'W', 'SW']:
        n = f'turn_{d}'; shutil.copy(f'{S3}/{n}.png', f'{OUT}/{n}.png'); src[n] = sha(f'{S3}/{n}.png')
    for k in range(4):
        n = f'walk_SE_k{k}'; shutil.copy(f'{S3}/{n}.png', f'{OUT}/{n}.png'); src[n] = sha(f'{S3}/{n}.png')
    for n in src:
        for suf in ('_hires.png',):
            if os.path.exists(f'{S3}/{n}{suf}'): shutil.copy(f'{S3}/{n}{suf}', f'{OUT}/{n}{suf}')
    orph = {}
    for n in OWN:
        a = P.load(f'{R3}/fx/{n}.png'); base = P.load(f'{R3}/base/{n}.png')
        fxm = np.any(a != base, -1)
        if n in FIX: FIX[n](a, n)
        a, nf = deorphan.clean(a, None)
        orph[n] = nf
        if nf: note(n, f'orphan merge: {nf} px took their same-material neighbour tone', 'lint orphans 0, no exclusions')
        d = OUT + ('/bonus' if n.startswith(('run_', 'dash_')) else '')
        P.save(a, f'{d}/{n}.png')
        Image.fromarray(a).resize((512, 512), Image.NEAREST).save(f'{d}/{n}_4x.png')
        m = np.zeros((128, 128, 4), np.uint8); m[fxm & (a[..., 3] > 0)] = (255, 0, 255, 255)
        Image.fromarray(m).save(f'{d}/{n}_fxmask.png')
        meta = json.load(open(f'{R3}/base/{n}_meta.json'))
        meta['fx_px'] = int((fxm & (a[..., 3] > 0)).sum())
        if n in HIRES and os.path.exists(f'{R3}/{HIRES[n]}'):
            shutil.copy(f'{R3}/{HIRES[n]}', f'{d}/{n}_hires.png'); shutil.copy(f'{R3}/{HIRES[n]}', f'{R3}/hires/{n}.png')
            meta['hires'] = f'Gemini pixel-native acting ref ({HIRES[n]}); the sprite is a Claude retrace on the lock3 cels'
        json.dump(meta, open(f'{d}/{n}_meta.json', 'w'), indent=1)
    for n in src:
        if os.path.exists(f'{OUT}/{n}.png'):
            Image.open(f'{OUT}/{n}.png').resize((512, 512), Image.NEAREST).save(f'{OUT}/{n}_4x.png')
    fx = json.load(open(f'{R3}/work/edits_fx.json')) if os.path.exists(f'{R3}/work/edits_fx.json') else []
    json.dump(dict(s3_copied_sha256=src, s3_src=S3, edits=fx + LOG), open(f'{R3}/work/edits.json', 'w'), indent=1)
    print('polish: orphans merged', orph, '| edits', len(fx) + len(LOG))

if __name__ == '__main__': run()
