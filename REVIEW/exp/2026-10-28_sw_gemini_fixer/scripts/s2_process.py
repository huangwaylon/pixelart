"""Step 2 processing. Fixer venv.
a*/b*: pixel-art-fixer (detect + square check) -> figure crop -> rescale to 96 -> palette lock  (work/proc/<name>_*)
c*:    E2 pixelize: pz.py EC0 SE 96 --src <c image> --pal palette.json (work/proc/EC0<name>_SE_96.*)"""
import os, sys, glob, json, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fixlib as F

E = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/'
G = E + 'work/gen/'; O = E + 'work/proc/'; os.makedirs(O, exist_ok=True)
PY = '/Users/waylonhuang/Documents/other/pixelart/.models/pixel-art-fixer/venv/bin/python'
res = {}
if os.path.exists(O + 'proc.json'): res = json.load(open(O + 'proc.json'))
for p in sorted(glob.glob(G + '*.png')):
    n = os.path.basename(p)[:-4]
    if n in res: continue
    if n.startswith(('a', 'b')):
        try: res[n] = F.run(p, O + n, 'SE')
        except Exception as e: res[n] = {'error': str(e)}; print('FAIL', n, e)
    elif n.startswith('c'):
        r = subprocess.run([PY, '-I', F.SW + 'v2/pixelize/tools/pz.py', 'EC0', 'SE', '96', '--src', p, '--pal', F.PAL,
                            '--out', O, '--tag', '_' + n], capture_output=True, text=True)
        res[n] = {'in': p, 'pz': (r.stdout + r.stderr)[-300:], 'stem': O + f'EC0_{n}_SE_96'}
        print(n, r.stdout.strip()[-100:], r.stderr[-200:])
json.dump(res, open(O + 'proc.json', 'w'), indent=1)
