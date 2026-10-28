"""Round-2 GATE (run before any judge): reads R/metrics.json + measures the walk crown/head lag on R/std.
  baseline spread 0 | feet_cx spread <= 1 (turn set) | body orphans 0 | flicker 0 outside FX | height 56-64 (body)
  | off-palette 0 | guide IoU for every key | walk crown range 4-5 px with the head lagging the body."""
import json, sys, os
import numpy as np
from PIL import Image
R = sys.argv[1]
M = json.load(open(f'{R}/metrics.json'))
S = {s['name'][:-4]: s for s in M['sprites']}
ok = True
def chk(name, cond, val):
    global ok
    ok &= bool(cond)
    print(f"{'PASS' if cond else 'FAIL'}  {name:34s} {val}")
base = {n: s['baseline'] for n, s in S.items()}
chk('baseline spread 0 (all keys)', max(base.values()) - min(base.values()) == 0, f"{min(base.values())}..{max(base.values())}")
fx = [S[f'turn_{d}']['feet_cx'] for d in ['S', 'SE', 'E', 'NE', 'N', 'NW', 'W', 'SW']]
chk('feet_cx spread <= 1 (turn set)', max(fx) - min(fx) <= 1.0, f"{min(fx):.2f}..{max(fx):.2f} spread {max(fx) - min(fx):.2f}")
orph = {n: s['orphans'] for n, s in S.items()}
chk('body orphans 0', sum(orph.values()) == 0, {n: v for n, v in orph.items() if v})
sys.path.insert(0, 'tools/pixel'); sys.path.insert(0, 'tools/hybrid')
import lint as L, hylib as HL
FXT = {HL.palette().index[n] for n in ('pink_0', 'pink_1', 'steel_2', 'steel_1', 'steel_0')}
fl, flfx = {}, {}
for q in M['sequences']:
    idxs = [HL.index_of(HL.load_rgba(f'{R}/std/{f}')) for f in q['frames']]
    res = L.flicker(idxs, q['loop'])
    allp = [p for v in res.values() for p in v]
    body = [p for p in allp if p[2] not in FXT and p[3] not in FXT]
    fl[q['anim'] + '_' + q['dir']] = len(body); flfx[q['anim'] + '_' + q['dir']] = len(allp) - len(body)
chk('flicker 0 outside FX (sequences)', sum(fl.values()) == 0, f"body {fl}  fx-only {flfx}")
hb = {n: s['body_height'] for n, s in S.items() if n.startswith('turn')}
chk('standing body height 56-64 (turn)', all(56 <= v <= 64 for v in hb.values()), sorted(set(hb.values())))
hh = {n: s['height'] for n, s in S.items()}
print(f"      heights incl. sword/FX: {hh}")
offp = sum(s['off_palette'] for s in S.values()) + sum(s['semi_alpha'] for s in S.values())
chk('off-palette + semi-alpha 0', offp == 0, offp)
iou = {n: s.get('iou') for n, s in S.items()}
chk('guide IoU reported for every key', all(v is not None for v in iou.values()), {n: v for n, v in iou.items()})
# walk crown: top row of the hair/bow per key; body = corset top row
def rows(p):
    a = np.array(Image.open(p).convert('RGBA'))
    op = a[..., 3] > 0
    ys = np.nonzero(op.any(1))[0]
    L = (a[..., 0] == 0x4a) & (a[..., 1] == 0x2e) & (a[..., 2] == 0x20)   # leather_1
    ly = np.nonzero(L.any(1))[0]
    return int(ys.min()), int(ly.min()) if len(ly) else None
cr = [rows(f'{R}/std/walk_SE_k{k}.png') for k in range(4)]
crown = [c[0] for c in cr]; body = [c[1] for c in cr]
rng = max(crown) - min(crown)
lag = (int(np.argmax(crown)) - int(np.argmax(body))) % 4
chk('walk crown range 4-5 px', 4 <= rng <= 5, f"crown rows {crown} range {rng}")
chk('walk head lags the body (1 key)', lag == 1, f"body(corset) rows {body}, lowest-crown key {int(np.argmax(crown))} vs lowest-body key {int(np.argmax(body))}")
lint = {n: s['lint'] for n, s in S.items()}
tot = {k: sum(l[k] for l in lint.values()) for k in next(iter(lint.values()))}
print(f"      lint totals (std set): {tot}")
print('GATE', 'PASS' if ok else 'FAIL')
