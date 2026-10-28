# joint.py : enumerate shared lid-template cell choices, score face_ssim per view (edits applied to eyes4/T masters), print best by min gain
import itertools, subprocess, json, os
from concurrent.futures import ThreadPoolExecutor
M = '/Users/waylonhuang/Documents/other/pixelart/swordswoman/v2/m96/eyes4/T/m/EC0_%s_96'; BASE = {'S': .574, 'SE': .610, 'E': .354}
EY = {'S': [(56, 49, 1), (66, 49, -1)], 'SE': [(62, 50, 1)], 'E': [(72, 49, 1)]}
def edits(v, cells):
    out = []
    for x0, y0, d in EY[v]:
        for (c, r), ch in cells.items():
            x = x0 + c if d == 1 else x0 + 5 - c
            out.append('%d,%d,%s' % (x, y0 + r, ch))
    return out
def score(v, cells):
    o = subprocess.run(['python3', 'eyes4/pxtry_n.py', M % v, v] + edits(v, cells), capture_output=True, text=True).stdout.split()
    return float(o[-1])
combos = []
for n0, o3, o4, e4, c4, c1 in itertools.product('sgh', 'shg', 'shg', 'gK', 'gh', 'hg'):
    if o4 != 's' and o3 == 's': continue
    combos.append({(0, 1): n0, (0, 3): o3, (0, 4): o4, (4, 2): e4, (4, 1): c4, (1, 1): c1})
def run(cells):
    r = {v: score(v, cells) for v in ('S', 'SE', 'E')}
    return cells, r
res = []
with ThreadPoolExecutor(8) as ex:
    for cells, r in ex.map(run, combos):
        res.append((min(r[v] - BASE[v] for v in r), ''.join(cells[k] for k in sorted(cells)), r))
res.sort(key=lambda t: -t[0])
for t in res[:12]: print('%.3f' % t[0], t[1], t[2])
