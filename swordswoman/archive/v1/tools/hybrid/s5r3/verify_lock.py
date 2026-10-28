"""S5 r3: verify hybrid/lock3/MANIFEST.json sha256 for every listed file (exit 1 on any mismatch / missing file),
then check that the h4 compositor's head stamps (tools/hybrid/h4/heads.head) are pixel-identical to the lock3 PNGs
for every (dir, expr|tilt|act) stamp this build uses. Writes the verified manifest digest + the sha256 of the h4 code
used to hybrid/S5_pixelnative/r3/lock_check.json."""
import hashlib, json, os, sys, glob
ROOT = '/Users/waylonhuang/Documents/other/pixelart/swordswoman'
os.chdir(ROOT)
L3 = 'hybrid/lock3'
def sha(p): return hashlib.sha256(open(p, 'rb').read()).hexdigest()
m = json.load(open(f'{L3}/MANIFEST.json'))
bad = []
for f, h in m['files'].items():
    p = f'{L3}/{f}'
    if not os.path.exists(p): bad.append((f, 'missing'))
    elif sha(p) != h: bad.append((f, 'sha mismatch'))
if bad:
    for b in bad: print('LOCK3 FAIL', *b)
    sys.exit(1)
# stamps used by the S5 r3 action specs must equal what the compositor renders
sys.path.insert(0, f'{ROOT}/tools/hybrid/h4')
import numpy as np
import heads as HEADS
from common import to_rgba
from PIL import Image
USED = [('SE', 'glare', 0, None), ('SE', 'wide', 0, None), ('SE', 'grit', 0, None), ('SE', 'calm', 0, None),
        ('E', 'glare', 0, None), ('E', 'smile', 0, None), ('E', 'wide', 0, None), ('E', 'closed', 0, None), ('E', 'squeeze', 0, None)]
for d, a in (('SE', 'back'), ('SE', 'down'), ('SE', 'squash'), ('E', 'squash'), ('E', 'back'), ('E', 'down')): USED.append((d, 'calm', 0, a))
stamp_bad = []
for d, e, t, a in USED:
    name = f'head_{d}' + (f'_act-{a}' if a else (f'_{e}' if e != 'calm' else ''))
    p = f'{L3}/{name}.png'
    if not os.path.exists(p): stamp_bad.append((name, 'no lock3 png')); continue
    ref = np.array(Image.open(p).convert('RGBA'))
    got = to_rgba(HEADS.head(d, e, t, a))
    if ref.shape != got.shape or (ref[..., 3] > 0).tolist() != (got[..., 3] > 0).tolist() or not np.array_equal(ref[ref[..., 3] > 0][:, :3], got[got[..., 3] > 0][:, :3]):
        stamp_bad.append((name, 'compositor != lock3'))
if stamp_bad:
    for b in stamp_bad: print('STAMP FAIL', *b)
    sys.exit(1)
code = {p: sha(p) for p in sorted(glob.glob('tools/hybrid/h4/*.py') + glob.glob('tools/hybrid/h4/cels/*.py') + glob.glob('tools/hybrid/fx/*.py'))}
os.makedirs('hybrid/S5_pixelnative/r3', exist_ok=True)
json.dump(dict(manifest_sha=sha(f'{L3}/MANIFEST.json'), files_ok=len(m['files']), stamps_checked=[u[0] + ':' + (u[3] or u[1]) for u in USED], code_sha=code),
          open('hybrid/S5_pixelnative/r3/lock_check.json', 'w'), indent=1)
print('lock3 OK:', len(m['files']), 'files,', len(USED), 'stamps == compositor')
