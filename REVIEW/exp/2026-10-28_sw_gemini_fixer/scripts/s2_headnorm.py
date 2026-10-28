"""Usage: s2_headnorm.py [hn|gh].  gh = h fixed to the rig guide figure height (true 96-px-figure scale).
Head-normalised scale for poses: a pose's figure bbox is not 96 px (tucked jump, crouched throw), so scaling every
bbox to 96 inflates the head. Here h is solved so the head-hair bbox height matches the master (35 px) - i.e. the same
pixel scale as the master. Fixer venv. b*: fixer -> lock at h; c*: pz.py EC0 at h. -> work/proc_hn/<name>.{txt,png,json}"""
import os, sys, json, glob, subprocess, shutil
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fixlib as F
import pzlib as Z
import s3_identity as I

E = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/'
MODE = sys.argv[1] if len(sys.argv) > 1 else 'hn'  # hn = head-normalised, gh = guide height (rig scale)
G = E + 'work/gen/'; O = E + f'work/proc_{MODE}/'; os.makedirs(O, exist_ok=True)
PY = '/Users/waylonhuang/Documents/other/pixelart/.models/pixel-art-fixer/venv/bin/python'
GH = json.load(open(E + 'work/refs/guide_heights.json'))
HAIR = I.measure(I.MASTER)['hair_bbox'][0]
keys, rgb, _ = Z.load_pal(F.PAL)


def make_b(name, h):
    im = np.array(Image.open(G + name + '.png').convert('RGBA'))
    fixed, info = F.fix_sq(im)
    m, _ = F.bgmask(fixed[..., :3]); nat, na = F.crop(fixed[..., :3], m)
    lo, al, w, how = F.to_h(nat, na, h)
    g, ox, oy = F.lock(lo, al, h, w, keys, rgb)
    Z.save(g, O + name, keys, rgb, {'view': 'SE', 'src': None, 'pal': F.PAL, 'method': 'GFX', 'h': h, 'w': w, 'ox': int(ox), 'oy': int(oy)})
    g2, ox2, oy2, shift = F.lock2(lo, al, h, w, keys, rgb)
    Z.save(g2, O + name + '_L2', keys, rgb, {'view': 'SE', 'src': None, 'pal': F.PAL, 'method': 'GFX_L2', 'h': h, 'w': w, 'ox': int(ox2), 'oy': int(oy2), 'shift': shift})
    return {'native_h': int(na.shape[0]), 'rescale': how}


def make_c(name, h):
    subprocess.run([PY, '-I', F.SW + 'v2/pixelize/tools/pz.py', 'EC0', 'SE', str(h), '--src', G + name + '.png', '--pal', F.PAL,
                    '--out', O + 'tmp', '--tag', '_x'], capture_output=True, text=True, check=True)
    for ext in ('txt', 'png', 'json'): shutil.move(O + f'tmp/EC0_x_SE_{h}.{ext}', O + f'{name}.{ext}')
    return {}


res = {}
for p in sorted(glob.glob(G + '[bc]_*.png')):
    n = os.path.basename(p)[:-4]; pose = n.split('_')[1]
    mk = make_b if n.startswith('b') else make_c
    h = 96 if MODE == 'hn' else int(round(GH[pose]['h'])); hist = []
    for it in range(4 if MODE == 'hn' else 1):
        extra = mk(n, h)
        hb = I.measure(O + n)['hair_bbox'][0]; hist.append((h, hb))
        h2 = int(round(h * HAIR / hb))
        if abs(hb - HAIR) <= 1 or h2 == h: break
        h = h2
    best = min(hist, key=lambda t: abs(t[1] - HAIR))  # hair-bbox measure is noisy (hair blob can merge/split): keep the closest
    if best != hist[-1]: extra = mk(n, best[0])
    h, hb = best
    res[n] = {'h': h, 'hair_h': hb, 'iters': hist, 'guide_h': GH[pose]['h'], **extra}
    print(n, res[n], flush=True)
json.dump(res, open(O + 'scale.json', 'w'), indent=1)
