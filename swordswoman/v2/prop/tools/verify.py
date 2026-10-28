# Measure blockouts from their material codes and check every section against prop/template.json (range +-0.5 px).
import sys, json, numpy as np
R = '/Users/waylonhuang/Documents/other/pixelart/swordswoman/v2/'
T = json.load(open(R + 'prop/template.json')); TOL = 0.5 / 48
def runs(row, codes):
    out, cur = [], 0
    for c in row:
        if c in codes: cur += 1
        else:
            if cur: out.append(cur)
            cur = 0
    if cur: out.append(cur)
    return out
def width(row, codes):
    xs = [i for i, c in enumerate(row) if c in codes]; return (max(xs) - min(xs) + 1) if xs else 0
def measure(g, side=False, body=None):
    body_g = g if body is None else body
    rows_with = lambda cs: [r for r in range(64) if any(c in cs for c in g[r])]
    m = {}; w = {}
    m['crown'] = min(rows_with('H')); T_ = rows_with('T'); m['sole'] = max(T_) + 1; m['ankle'] = min(T_)
    e = rows_with('e'); m['eye'] = (min(e) + max(e) + 1) / 2 if e else None
    n = rows_with('N' if not side else 'N'); n = [r for r in n if r < 40]
    m['chin'] = min(n); m['shoulder'] = min(rows_with('DA'))
    D = rows_with('D'); m['hem'] = max(D) + 1; m['crotch'] = m['hem']
    # armpit: first row where a background gap separates arm from torso
    m['armpit'] = None
    for r in range(m['shoulder'], m['hem']):
        if not side and len([x for x in ''.join(c if c in 'DOAh' else ' ' for c in g[r]).split()]) >= 3: m['armpit'] = r; break
    if side: m['armpit'] = None
    body = 'DO'
    hipzone = range(m['shoulder'] + 3, m['hem'])
    bw = {r: (max(runs(body_g[r], body)) if runs(body_g[r], body) else 0) for r in hipzone}
    mx = max(bw.values()); m['hip'] = min(r for r in hipzone if bw[r] == mx); w['hip'] = mx
    wz = [r for r in hipzone if r < m['hip']]; mn = min(bw[r] for r in wz); wr = [r for r in wz if bw[r] == mn]
    m['waist'] = (min(wr) + max(wr) + 1) / 2; w['waist'] = mn
    w['head'] = max(width(g[r], 'H') for r in range(m['crown'], m['chin']))
    w['neck'] = max(max(runs(g[r], 'N')) for r in range(m['chin'], m['shoulder']))
    w['shoulder'] = max(width(g[r], 'DAO') for r in (m['shoulder'], m['shoulder'] + 1))
    lg = lambda r: max(runs(body_g[r], 'L') or [0])
    w['thigh'] = lg(m['hem']); kr = [r for r in range(m['hem'] + 1, m['ankle']) if lg(r) < w['thigh']]
    m['knee'] = min(kr) if kr else None; w['calf'] = lg(m['knee'] + 2) if kr else lg(m['ankle'] - 2)
    w['foot'] = max(runs(g[m['sole'] - 1], 'T'))
    return m, w
def check(v, g, body=None):
    side = v == 'E'; m, w = measure(g, side, body); H = m['sole'] - m['crown']; bad = []; rep = []
    for k, t in T['rows'].items():
        if m.get(k) is None:
            if (k == 'eye' and v in ('N', 'NE')) or (k == 'armpit' and side): continue
            bad.append(f'row {k} not found'); rep.append(f'{k}=MISSING!'); continue
        f = (m[k] - m['crown']) / H; ok = t['min'] - TOL <= f <= t['max'] + TOL
        rep.append(f"{k}={m[k]}({f:.3f})" + ('' if ok else '!')); bad += [] if ok else [f'row {k} {f:.3f} not in [{t["min"]},{t["max"]}]']
    for k, t in T['widths'].items():
        if side and k not in ('head', 'neck', 'calf', 'foot'): continue  # side view: torso/hip are depths
        if side and k == 'foot': continue
        f = w[k] / H; ok = t['min'] - TOL <= f <= t['max'] + TOL
        rep.append(f"w{k}={w[k]}({f:.3f})" + ('' if ok else '!')); bad += [] if ok else [f'w {k} {w[k]}px {f:.3f} not in [{t["min"]},{t["max"]}]']
    return H, m, w, rep, bad
if __name__ == '__main__':
    allok = True; res = {}
    for v in sys.argv[1:] or ['S', 'SE', 'E', 'NE', 'N']:
        g = np.array([list(l.rstrip('\n')) for l in open(R + f'prop/blockout/{v}.txt')])
        b = np.array([list(l.rstrip('\n')) for l in open(R + f'prop/blockout/{v}_body.txt')])
        H, m, w, rep, bad = check(v, g, b); res[v] = dict(H=H, rows=m, widths=w, fails=bad)
        print(v, 'H', H, 'PASS' if not bad else 'FAIL', ' '.join(rep)); allok &= not bad
    json.dump(res, open(R + 'prop/blockout/verify.json', 'w'), indent=1)
    print('ALL PASS' if allok else 'FAILURES'); sys.exit(0 if allok else 1)
