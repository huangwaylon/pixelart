"""bonus smear GIFs: walk passing -> run flight smear -> ..., turn -> dash travel smear. 4x, slate + grass."""
import sys, os
import numpy as np
from PIL import Image
sys.path.insert(0, '/Users/waylonhuang/Documents/other/pixelart/swordswoman/tools/pixel')
from gif import grass_tile, save_gif
R, pre = sys.argv[1], sys.argv[2]
SP = f'{R}/sprite'
def frame(n, bg):
    a = np.array(Image.open(f'{SP}/{n}.png').convert('RGBA'))[20:112, 8:120]
    h, w = a.shape[:2]
    base = np.zeros((h, w, 3), np.uint8)
    base[:] = bg if isinstance(bg, tuple) else bg[:h, :w]
    m = a[..., 3] > 0; base[m] = a[..., :3][m]
    return np.array(Image.fromarray(base).resize((w * 4, h * 4), Image.NEAREST))
for name, seq, ms in [('run_SE_smear', ['walk_SE_k2', 'run_SE_f1', 'walk_SE_k0', 'run_SE_f1'], [140, 70, 140, 70]),
                      ('dash_SE_smear', ['turn_SE', 'dash_SE_f1', 'turn_SE'], [300, 60, 300])]:
    if not all(os.path.exists(f'{SP}/{n}.png') for n in seq): continue
    for bgn, bg in (('grey', (36, 32, 44)), ('grass', grass_tile(112, 92))):
        save_gif([frame(n, bg) for n in seq], ms, f'{pre}_{name}_4x_{bgn}.gif')
print('bonus gifs ok')
