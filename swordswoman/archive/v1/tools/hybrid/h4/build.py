"""h3 build: render the STANDARD TEST SET (+ bonus run/dash smear frames) from the cels and anim specs.
  .venv/bin/python tools/hybrid/h3/build.py OUT_DIR [--only name,...]
writes OUT_DIR/sprite/<name>.png (+ _4x), OUT_DIR/src/ (cels, anim specs, lock2 heads used, frame json),
OUT_DIR/view_<group>_x6.png (quick zoom strips)."""
import sys, os, json, shutil, importlib.util
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kit
from common import save, strip, zoom

H3 = os.path.dirname(os.path.abspath(__file__))
DIRS = ['S', 'SE', 'E', 'NE', 'N', 'NW', 'W', 'SW']
ANIMS = ['walk_SE', 'slash_SE', 'jump_E', 'bonus_SE']


def feet_cx(g):
    m = (g != '.') & ~np.isin(g, list('tTw'))
    ys = np.nonzero(m.any(1))[0]
    yb = ys.max()
    xs = np.nonzero(m[yb - 1:yb + 1].any(0))[0]
    return float(xs.mean())


def load_frames(name):
    p = os.path.join(H3, 'anims', name + '.py')
    if not os.path.exists(p): return {}
    sp = importlib.util.spec_from_file_location('a_' + name, p)
    m = importlib.util.module_from_spec(sp); sp.loader.exec_module(m)
    return m.FRAMES


def main():
    out = sys.argv[1]
    only = sys.argv[sys.argv.index('--only') + 1].split(',') if '--only' in sys.argv else None
    os.makedirs(f'{out}/sprite', exist_ok=True); os.makedirs(f'{out}/src', exist_ok=True)
    frames = {}
    for d in DIRS: frames[f'turn_{d}'] = dict(base=f'turn_{d}')
    for a in ANIMS: frames.update(load_frames(a))
    groups = {}
    for n, fs in frames.items():
        if only and not any(n.startswith(o) for o in only): continue
        a, info = kit.render(fs)
        if n.startswith('turn_'):          # centre the feet on the pivot exactly as metrics.py measures them
            sys.path.insert(0, os.path.join(H3, '..'))
            import hylib as HL
            gm = json.load(open('hybrid/S3_editchain/r1/guide_map.json'))
            gd = HL.load_guide(gm[n]) if n in gm else None
            fxm = HL.features(a, gd)['feet_cx']
            dx = int(round(64 - fxm))
            if dx:
                fs = dict(fs, shift=(dx, 0)); a, info = kit.render(fs)
                frames[n] = fs
        save(a, f'{out}/sprite/{n}.png')
        zoom(a, 4, grid=False).save(f'{out}/sprite/{n}_4x.png')
        json.dump({k: v for k, v in fs.items()}, open(f'{out}/src/{n}.json', 'w'), indent=1, default=str)
        g = info['chars']
        if n.startswith('turn_'): print(n, 'feet_cx', feet_cx(g))
        groups.setdefault(n.rsplit('_', 1)[0] if not n.startswith('turn') else 'turn', []).append((n, a))
    for gname, lst in groups.items():
        crops = [a[24:112, 8:120] for _, a in lst]
        strip(crops, z=5, labels=[n for n, _ in lst]).save(f'{out}/view_{gname}_x5.png')
    for sub in ('cels', 'anims'):
        dst = f'{out}/src/{sub}'; os.makedirs(dst, exist_ok=True)
        for f in os.listdir(os.path.join(H3, sub)):
            if f.endswith('.py'): shutil.copy(os.path.join(H3, sub, f), dst)


if __name__ == '__main__':
    main()
