"""S7 r3 BODY BASES: the standard-set bodies rendered WITHOUT any FX, so the FX kit (tools/hybrid/fx/kit.py) is the
only thing that paints smears / sparks / dust.  Bodies = S5 r2 acted keys (slash, jump, walk) and the S3 r2 shared
turn cels (both via the S3 h3 compositor, read-only).  Writes hybrid/S7_fxkit/r3/base/<name>.png + <name>_owner.npy
(layer owner per pixel, 'HEAD' = face stamp) and <name>.json (shift + head box).

  .venv/bin/python tools/hybrid/s7/base.py [names...]"""
import sys, os, json, importlib.util
import numpy as np
from PIL import Image
ROOT = '/Users/waylonhuang/Documents/other/pixelart/swordswoman'
sys.path.insert(0, f'{ROOT}/tools/hybrid/h3'); sys.path.insert(0, f'{ROOT}/tools/hybrid/s5r2')
_s = importlib.util.spec_from_file_location('h3kit', f'{ROOT}/tools/hybrid/h3/kit.py')   # S3 compositor (read-only)
kit = importlib.util.module_from_spec(_s); _s.loader.exec_module(kit)                    # (name clash with fx/kit.py)
import deorphan
OUT = f'{ROOT}/hybrid/S7_fxkit/r3/base'
DIRS = ['S', 'SE', 'E', 'NE', 'N', 'NW', 'W', 'SW']


def spec(anim):
    p = f'{ROOT}/tools/hybrid/s5r2/anims/{anim}.py'
    s = importlib.util.spec_from_file_location('s7spec_' + anim, p)
    m = importlib.util.module_from_spec(s); s.loader.exec_module(m)
    return m.frames()


def bonus():
    p = f'{ROOT}/tools/hybrid/h3/anims/bonus_SE.py'
    cwd = os.getcwd(); os.chdir(ROOT)
    s = importlib.util.spec_from_file_location('s7bonus', p)
    m = importlib.util.module_from_spec(s); s.loader.exec_module(m)
    os.chdir(cwd)
    return m.FRAMES


def all_frames():
    F = {f'turn_{d}': dict(base=f'turn_{d}') for d in DIRS}
    for a in ('walk_SE', 'slash_SE', 'jump_E'): F.update(spec(a))
    F.update(bonus())
    return F


def render_body(fs):
    fs = dict(fs); fs.pop('fx', None); fs.pop('s5fx', None)
    a, info = kit.render(fs)
    a = np.ascontiguousarray(a).copy()
    a, _ = deorphan.clean(a, info['owner'] == 'HEAD')
    return a, info


if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    only = sys.argv[1:]
    for name, fs in all_frames().items():
        if only and name not in only: continue
        a, info = render_body(fs)
        Image.fromarray(a).save(f'{OUT}/{name}.png')
        own = np.array(info['owner'], dtype='<U16')
        np.save(f'{OUT}/{name}_owner.npy', own)
        json.dump(dict(shift=info['shift'], head=list(info['head'])), open(f'{OUT}/{name}.json', 'w'))
        print('base', name)
