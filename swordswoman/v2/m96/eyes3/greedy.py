"""eyes3/greedy.py SRC : greedy single-px search (S eye region, arch rows kept) for face_ssim; prints gains (experiment only)"""
import sys, json, subprocess, os, shutil
R = '/Users/waylonhuang/Documents/other/pixelart/swordswoman/'; src = sys.argv[1]; V = os.environ.get('VW', 'S'); tmp = '/tmp/m96e_g'; os.makedirs(tmp, exist_ok=True)
shutil.copy(f'{src}/EC0_{V}_96.json', f'{tmp}/EC0_{V}_96.json')
g = [list(l.rstrip('\n')) for l in open(f'{src}/EC0_{V}_96.txt') if l.strip()]
def score(g):
    open(f'{tmp}/EC0_{V}_96.txt', 'w').write('\n'.join(''.join(r) for r in g) + '\n')
    subprocess.run([R + '.scratch/pixelize/pixeloe/venv/bin/python', '-I', R + 'v2/pixelize/tools/metrics.py', f'{tmp}/EC0_{V}_96', '--json', tmp + '/m.json'], capture_output=True, cwd=R)
    return json.load(open(tmp + '/m.json'))[0]['face_ssim']
base = score(g); print('base', round(base, 4))
cells = [(x, y) for y in range(49, 55) for x in (list(range(55, 62)) + list(range(66, 73)) if V == 'S' else range(70, 78))]
IRIS = ({(x, y) for y in (51, 52, 53) for x in list(range(57, 61)) + list(range(67, 71))} - {(60, 51), (67, 51)}) if V == 'S' else ({(x, y) for y in (51, 52, 53) for x in range(73, 77)} - {(76, 51)})
LOCK = {(73, 50), (74, 50), (75, 50), (72, 51), (76, 51)} if V == 'E' else {(57, 50), (58, 50), (59, 50), (56, 51), (60, 51), (68, 50), (69, 50), (70, 50), (67, 51), (71, 51)}
res = []
for x, y in cells:
    if (x, y) in LOCK or g[y][x] in 'W': continue
    if (x, y) in IRIS: continue
    for c in 'Khgs':
        if c == g[y][x] or (y == 49 and c == 'K') or (y == 50 and x in (56, 60, 67, 71) and c == 'K'): continue
        o = g[y][x]; g[y][x] = c; s = score(g); g[y][x] = o
        if s > base + float(os.environ.get("TH", "0.002")): res.append((round(s - base, 4), x, y, o, c))
for r in sorted(res, reverse=True)[:25]: print(r)
