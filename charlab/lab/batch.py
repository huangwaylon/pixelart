"""charlab batch: one spec -> every (tier, body) variant -> model -> Blender walk passes -> pixel chain per size -> boards.
  python batch.py SPEC.json [tiers=simple,medium,detailed] [bodies=chibi,compact,slim] [sizes=32,48,64,96] [-j N]
Writes   work/<id>/<tier>_<body>/{model.npz,model.json,r/}   (big intermediates, gitignored)
         out/<id>/<tier>_<body>/<size>/{walk_4x.gif,walk_strip1x.png,sheet_4x.png,<view>_fNN.png/.txt,gates.json}
         out/<id>/grid_SE_4x.gif, out/<id>/boards.png, out/<id>/summary.json  (boards.py)"""
import json, os, subprocess, sys, time
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
PY = '/Users/waylonhuang/Documents/other/pixelart/.models/pixtools/venv/bin/python'
BL = '/Applications/Blender.app/Contents/MacOS/Blender'


def sh(cmd, log):
    with open(log, 'a') as f:
        f.write('$ ' + ' '.join(cmd) + '\n'); f.flush()
        r = subprocess.run(cmd, stdout=f, stderr=subprocess.STDOUT, cwd=HERE)
    if r.returncode: raise RuntimeError(f'failed ({r.returncode}): {" ".join(cmd)}  -> see {log}')


def variant(spec, sid, tier, body, sizes, views):
    w = os.path.join(HERE, 'work', sid, f'{tier}_{body}'); o = os.path.join(HERE, 'out', sid, f'{tier}_{body}')
    os.makedirs(w, exist_ok=True); os.makedirs(o, exist_ok=True)
    log = os.path.join(w, 'build.log'); open(log, 'w').close()
    t = time.time()
    sh([PY, 'model.py', spec, tier, body, os.path.join(w, 'model.npz')], log)
    env_blend = os.environ.copy()
    if tier == 'medium' and body == json.load(open(spec))['body'].get('recommended'): env_blend['CHARLAB_SAVE_BLEND'] = '1'
    with open(log, 'a') as f:
        r = subprocess.run([BL, '-b', '-P', 'blender_walk.py', '--', os.path.join(w, 'model.npz'), os.path.join(w, 'r'), views, '8'],
                           stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=HERE, env=env_blend, text=True)
        f.write('\n'.join(l for l in r.stdout.splitlines() if 'Saved:' not in l and not l.startswith('Fra:')) + '\n')
    if r.returncode or 'WALK_RENDERED' not in r.stdout: raise RuntimeError(f'blender failed for {sid} {tier} {body}: see {log}')
    sh([PY, 'pixel.py', os.path.join(w, 'r'), os.path.join(w, 'model.json'), o, sizes], log)
    m = json.load(open(os.path.join(w, 'model.json')))
    json.dump(dict(model={k: m[k] for k in ('verts', 'tris', 'warnings', 'mats', 'palette')}, seconds=round(time.time() - t, 1)),
              open(os.path.join(o, 'variant.json'), 'w'), indent=1)
    return f'{sid} {tier:8s} {body:7s} {time.time() - t:5.1f}s'


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('-j')]
    jobs = next((int(a[2:]) for a in sys.argv[1:] if a.startswith('-j')), 6)
    spec = os.path.abspath(args[0]); sid = json.load(open(spec))['id']
    tiers = (args[1] if len(args) > 1 else 'simple,medium,detailed').split(',')
    bodies = (args[2] if len(args) > 2 else 'chibi,compact,slim').split(',')
    sizes = args[3] if len(args) > 3 else '32,48,64,96'
    views = os.environ.get('CHARLAB_VIEWS', 'SE,S,E')
    t = time.time()
    with ThreadPoolExecutor(jobs) as ex:
        futs = [ex.submit(variant, spec, sid, tr, bd, sizes, views) for tr in tiers for bd in bodies]
        for f_ in futs: print(f_.result(), flush=True)
    subprocess.run([PY, 'boards.py', spec, ','.join(tiers), ','.join(bodies), sizes], cwd=HERE, check=True)
    print(f'BATCH {sid}: {len(tiers) * len(bodies)} variants x {len(sizes.split(","))} sizes in {time.time() - t:.0f}s', flush=True)


if __name__ == '__main__':
    main()
