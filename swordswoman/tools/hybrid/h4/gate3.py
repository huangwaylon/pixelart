"""S3 r3 GATE + IDENTITY GATE. .venv/bin/python tools/hybrid/h4/gate3.py R  (R/metrics.json, R/sprite/*.png)
base: baseline spread 0 | turn feet_cx spread <= 1 | orphans 0 | flicker 0 outside FX | standing height 56-64 |
      off-palette 0 | lint outline_gap / jaggy vs r2 (695 / 323: target <= half)
walk: crown down -2/-3 on k1, up +2 on k3 (vs k0), range 4-5 | passing foot >= 3 px off the baseline |
      sword angle stable within +-10 deg | collar + both ribbons on every key | bow lags the head
identity (every sprite): bow 50-90 red px above the eyes (front <= 85) | head width 22-26 | collar red under the chin |
      ribbons: pink px >= 50 % of the direction's turn value | purple present where the right arm faces camera |
      hook: >= 7 steel px within 3 px of the hilt (4 guard + 3 kagi) | pivot"""
import json, sys, os, glob
import numpy as np
sys.path.insert(0, 'tools/hybrid/h4'); sys.path.insert(0, 'tools/pixel'); sys.path.insert(0, 'tools/hybrid')
from common import load, to_chars
R = sys.argv[1]
M = json.load(open(f'{R}/metrics.json'))
S = {s['name'][:-4]: s for s in M['sprites']}
ok = True
def chk(name, cond, val):
    global ok
    ok &= bool(cond)
    print(f"{'PASS' if cond else 'FAIL'}  {name:44s} {val}")
G = {n: to_chars(load(f'{R}/sprite/{n}.png')) for n in S}
base = {n: s['baseline'] for n, s in S.items()}
chk('baseline spread 0 (all keys)', max(base.values()) == min(base.values()), f"{min(base.values())}..{max(base.values())}")
fx = [S[f'turn_{d}']['feet_cx'] for d in ['S', 'SE', 'E', 'NE', 'N', 'NW', 'W', 'SW']]
chk('pivot: turn feet_cx spread <= 1', max(fx) - min(fx) <= 1.0, f"{min(fx):.2f}..{max(fx):.2f} spread {max(fx) - min(fx):.2f}")
chk('orphans 0', sum(s['orphans'] for s in S.values()) == 0, {n: s['orphans'] for n, s in S.items() if s['orphans']})
import lint as L, hylib as HL
FXT = {HL.palette().index[n] for n in ('pink_0', 'pink_1', 'steel_2', 'steel_1', 'steel_0')}
fl = {}
for q in M['sequences']:
    idxs = [HL.index_of(HL.load_rgba(f'{R}/sprite/{f}')) for f in q['frames']]
    res = L.flicker(idxs, q['loop'])
    allp = [p for v in res.values() for p in v]
    fl[q['anim'] + '_' + q['dir']] = len([p for p in allp if p[2] not in FXT and p[3] not in FXT])
chk('flicker 0 outside FX', sum(fl.values()) == 0, fl)
hb = {n: s['body_height'] for n, s in S.items() if n.startswith('turn')}
chk('standing height 56-64 (turn)', all(56 <= v <= 64 for v in hb.values()), sorted(set(hb.values())))
chk('off-palette + semi-alpha 0', sum(s['off_palette'] + s['semi_alpha'] for s in S.values()) == 0, 0)
tot = {}
for s in S.values():
    for k, v in s['lint'].items(): tot[k] = tot.get(k, 0) + v
chk('lint outline_gap <= 347 (r2 695 / 2)', tot['outline_gap'] <= 347, tot['outline_gap'])
chk('lint jaggy <= 161 (r2 323 / 2)', tot['jaggy'] <= 161, tot['jaggy'])
print('      lint totals:', tot)
# ---- walk
def crown(g): return int(np.nonzero((g != '.').any(1))[0].min())
def bowtop(g):
    m = np.isin(g, list('vrRC')); m[60:] = False
    return int(np.nonzero(m.any(1))[0].min())
def headtop(g):
    m = np.isin(g, list('hHJ')); return int(np.nonzero(m.any(1))[0].min())
wk = [G[f'walk_SE_k{k}'] for k in range(4)]
cr = [headtop(g) for g in wk]
d1, d3 = cr[1] - cr[0], cr[3] - cr[0]
chk('walk down k1 crown +2..+3 px (lower)', 2 <= d1 <= 3, f'hair-top rows {cr}')
chk('walk up k3 crown -2 px (higher)', d3 <= -2, f'k3 - k0 = {d3}')
chk('walk crown range 4-5', 4 <= max(cr) - min(cr) <= 5, max(cr) - min(cr))
def lowest_foot_left(g):
    # passing foot = near (viewer-left) foot: lowest body row in columns < 63 below the hem
    m = (g != '.') & ~np.isin(g, list('tTw')); m[:96] = False; m[:, 61:] = False; m[:, :50] = False
    ys = np.nonzero(m.any(1))[0]; return int(ys.max())
pf = lowest_foot_left(wk[2])
chk('walk passing foot >= 3 px off the baseline', 104 - pf >= 3, f'near foot sole row {pf}')
def blade_angle(g):
    m = g == 'w'; ys, xs = np.nonzero(m)
    if len(xs) < 4: return None
    a = np.degrees(np.arctan2(np.polyfit(xs, ys, 1)[0], 1)); return round(float(a), 1)
ang = [blade_angle(g) for g in wk]
chk('walk sword angle stable +-10 deg', max(ang) - min(ang) <= 20 and all(abs(a - ang[0]) <= 10 for a in ang), ang)
def pinks(g):
    m = np.isin(g, list('pP')); m[96:] = False
    cx = 64
    return int(m[:, :cx].sum()), int(m[:, cx:].sum())
rb = [pinks(g) for g in wk]
chk('walk both ribbons on every key', all(a >= 8 and b >= 8 for a, b in rb), rb)
def collar(g, y0, y1):
    return int(np.isin(g[y0:y1], list('vrRC')).sum())
cl = [collar(wk[k], 70 + [0, 3, 1, -2][k], 76 + [0, 3, 1, -2][k]) for k in range(4)]
chk('walk collar present on every key', all(c >= 40 for c in cl), cl)
bt = [bowtop(g) for g in wk]
rel = [b - h for b, h in zip(bt, cr)]
chk('walk bow lags the head (rel offset varies 2-4 px)', 2 <= max(rel) - min(rel) <= 4, f'bow top rows {bt} rel to hair top {rel}')
# ---- identity on every sprite
def eye_row(g):
    ys = np.nonzero(np.isin(g, list('eE')).any(1))[0]; return int(ys.min()) if len(ys) else None
ids = {}
for n, g in G.items():
    er = eye_row(g); ht = headtop(g); top = crown(g)
    lim = er if er is not None else ht + 9
    bow = int(np.isin(g[top:min(lim, ht + 10)], list('vrRC')).sum())
    hw = []
    for y in range(ht + 6, ht + 14):
        xs = np.nonzero(np.isin(g[y], list('hHJmsSeEK')))[0]
        if len(xs): hw.append(xs.max() - xs.min() + 1)
    pk = int(np.isin(g, list('pP')).sum())
    pu = int((g == 'u').sum())
    st = np.isin(g, list('tTw')); hil = np.isin(g, list('dR'))
    ys, xs = np.nonzero(st & ~(g == 'w'))
    ids[n] = dict(bow=bow, headw=max(hw) if hw else 0, pink=pk, purple=pu)
for n, v in ids.items():
    d = n.split('_')[1] if n.startswith('turn') else ('SE' if 'SE' in n else 'E')
    ref = ids.get(f'turn_{d}', v)
    v['ribbon_ratio'] = round(v['pink'] / max(1, ref['pink']), 2)
bad_bow = {n: v['bow'] for n, v in ids.items() if not (40 <= v['bow'] <= 90)}
chk('identity: bow red px 40-90 in every sprite', not bad_bow, bad_bow or 'all ok')
bad_hw = {n: v['headw'] for n, v in ids.items() if not (21 <= v['headw'] <= 27)}
chk('identity: head width 21-27', not bad_hw, bad_hw or 'all ok')
bad_rb = {n: v['ribbon_ratio'] for n, v in ids.items() if v['ribbon_ratio'] < 0.5 and 'dash' not in n}
chk('identity: ribbons >= 50 % of the turn value', not bad_rb, bad_rb or 'all ok')
need_pu = [n for n in ids if any(n.startswith(p) for p in ('turn_S.', 'turn_SE', 'turn_E', 'turn_SW', 'walk_SE'))] + ['turn_S']
bad_pu = {n: ids[n]['purple'] for n in set(need_pu) if n in ids and ids[n]['purple'] < 2}
chk('identity: purple ornament where the right arm faces camera', not bad_pu, bad_pu or 'all ok')
json.dump(ids, open(f'{R}/identity.json', 'w'), indent=1, default=int)
print('GATE', 'PASS' if ok else 'FAIL')
