# joint3.py: arch-visible template search (light shoulders) on the promoted masters (G), per-view face_ssim vs v13 baselines
import itertools, subprocess
from concurrent.futures import ThreadPoolExecutor
M = '/Users/waylonhuang/Documents/other/pixelart/swordswoman/v2/m96/masters/EC0_%s_96'; BASE = {'S': .574, 'SE': .610, 'E': .354}
EY = {'S': [(56, 49, 1), (66, 49, -1)], 'SE': [(62, 50, 1)], 'E': [(72, 49, 1)]}
LID = {(0, 1), (1, 1), (4, 1), (0, 2), (1, 2), (4, 2), (2, 0), (3, 0), (0, 3), (0, 4)}   # lid cells (mirrored for the right eye)
def edits(v, cells):
    out = []
    for x0, y0, d in EY[v]:
        for (c, r), ch in cells.items():
            if d == -1 and r in (2, 3) and c in (1, 4):   # right eye iris rows: lid corner K at col 1 -> col 4, inner end at col 4 -> col 1
                x = x0 + 5 - c
            else: x = x0 + c if d == 1 else x0 + 5 - c
            out.append('%d,%d,%s' % (x, y0 + r, ch))
    return out
def score(v, cells):
    return float(subprocess.run(['python3', 'eyes4/pxtry_n.py', M % v, v] + edits(v, cells), capture_output=True, text=True).stdout.split()[-1])
combos = []
for s1, s4, c1, c4, n0, o3, o4, b1, b4 in itertools.product('sSg', 'sSg', 'Kh', 'Kg', 'sSg', 'sg', 'sg', 'sg', 'sg'):
    if o4 == 'g' and o3 == 's': continue
    if b1 != b4: continue
    combos.append({(1, 1): s1, (4, 1): s4, (1, 2): c1, (4, 2): c4, (0, 1): n0, (0, 3): o3, (0, 4): o4, (1, 4): b1, (4, 4): b4, (2, 1): 'K', (3, 1): 'K', (0, 2): 'K'})
def run(cells): return cells, {v: score(v, cells) for v in ('S', 'SE', 'E')}
res = []
with ThreadPoolExecutor(8) as ex:
    for cells, r in ex.map(run, combos):
        k = ' '.join('%d%d%s' % (c, rr, cells[(c, rr)]) for c, rr in sorted(cells) if (c, rr) not in ((2, 1), (3, 1), (0, 2)))
        res.append((min(r[v] - BASE[v] for v in r), k, r))
res.sort(key=lambda t: -t[0])
import json; json.dump([(a, b, c) for a, b, c in res], open('/tmp/m96t/j4.json', 'w'))
for t in [t for t in res if ' 11g' not in t[1] and ' 41g' not in t[1]][:10]: print('%.4f' % t[0], t[1], {v: round(x, 4) for v, x in t[2].items()})
