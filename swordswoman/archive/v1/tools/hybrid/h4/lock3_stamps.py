"""lock3 body stamps + manifest. Renders the ribbon lag stamps, the katana guard glyph per snapped blade angle,
the sleeve/cuff and hand samples from the h4 kit specials, then writes hybrid/lock3/MANIFEST.json (sha256 of every
file). After the manifest is written lock3 is READ ONLY: changes go through the lead as lock3.1."""
import hashlib, json, os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kit, ribbons as RB
from common import to_rgba, save, write_grid, strip
L3 = 'hybrid/lock3'
os.makedirs(f'{L3}/stamps', exist_ok=True)
def crop(g):
    ys, xs = np.nonzero(g != '.')
    return g[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
out = []
for pr in RB.PRESETS:
    for d, nm in ((-1, 'L'), (1, 'R')):
        g = kit.blank(); kit.ribbon(g, RB.spec((64, 40), pr, d).split()[1:])
        c = crop(g); save(to_rgba(c), f'{L3}/stamps/ribbon_{pr}_{nm}.png')
        write_grid(c, f'{L3}/stamps/ribbon_{pr}_{nm}.pix', f'lock3 ribbon stamp {pr} {nm} (root = first K px)')
        out.append(to_rgba(c))
angs = [0, 18.435, 26.565, 45, 63.435, 71.565, 90, 108.435, 116.565, 135, 153.435, 161.565, 180,
        -18.435, -26.565, -45, -63.435, -71.565, -90, -108.435, -116.565, -135, -153.435, -161.565]
kats = []
for a in angs:
    for hook in (1, -1):
        g = kit.blank(); kit.katana(g, ['64', '64', str(a), '14', f'hook={hook}'])
        c = crop(g); tag = f'{a:+.0f}_h{hook:+d}'
        save(to_rgba(c), f'{L3}/stamps/katana_{tag}.png'); kats.append(to_rgba(c))
g = kit.blank(); kit.cuff(g, ['60,40', '57,54', '3', '11', 'orn=-1']); c = crop(g)
save(to_rgba(c), f'{L3}/stamps/sleeve_bell_orn.png'); write_grid(c, f'{L3}/stamps/sleeve_bell_orn.pix', 'lock3 sleeve sample')
strip(out, z=6).save(f'{L3}/stamps_ribbons_x6.png')
strip(kats[:24], z=6).save(f'{L3}/stamps_katana_a_x6.png'); strip(kats[24:], z=6).save(f'{L3}/stamps_katana_b_x6.png')
man = {}
for root, _, files in os.walk(L3):
    for f in sorted(files):
        p = os.path.join(root, f)
        if f == 'MANIFEST.json': continue
        man[os.path.relpath(p, L3)] = hashlib.sha256(open(p, 'rb').read()).hexdigest()
json.dump(dict(version='lock3', date='2026-10-25', owner='S3 r3 (base / identity owner)', read_only=True,
               change_policy='lock3 is READ ONLY after this manifest; changes only through the lead as lock3.1',
               built_by=['tools/hybrid/h4/heads.py', 'tools/hybrid/h4/lock3_stamps.py'],
               from_='hybrid/lock2', files=man), open(f'{L3}/MANIFEST.json', 'w'), indent=1)
print(len(man), 'files')
