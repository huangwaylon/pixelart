# try_s.py NAME 'r50' 'r51' 'r52' 'r53' : S face_ssim for a left-eye lash layout over cols 54-61 (8 chars per row, rows 49..53 given as 5 strings;
# '.' = skin, 'K' lash, 'i' = keep iris px, '_' keep base); right eye = mirror (col 127-c) for lash px, iris unmirrored.
import sys, os, json, shutil, subprocess
R = '/Users/waylonhuang/Documents/other/pixelart/swordswoman/'; M = R + 'v2/m96/'; src = M + 'snap/v13_preeyefix/masters/EC0_S_96'
name, rows = sys.argv[1], sys.argv[2:7]; od = '/tmp/m96t/' + name; os.makedirs(od, exist_ok=True)
g = [list(l.rstrip('\n')) for l in open(src + '.txt')]
IRIS = {51: 'hWhh', 52: 'gWKg', 53: 'gLLg'}; IR = {51: 'hWhh', 52: 'gWKg', 53: 'gLLg'}
for y in range(49, 54):
    for x in list(range(55, 62)) + list(range(66, 73)): g[y][x] = 's'
    if y in IRIS:
        for i, c in enumerate(IRIS[y]): g[y][57 + i] = c; g[y][67 + i] = IR[y][i]
for j, r in enumerate(rows):
    y = 49 + j
    for i, c in enumerate(r):
        x = 54 + i
        if c in '_i': continue
        if c == '.' and x == 54: continue
        g[y][x] = c if c != '.' else ('s' if not (57 <= x <= 60 and y in IRIS) else g[y][x])
        xr = 127 - x
        if c == 'K' or not (67 <= xr <= 70 and y in IRIS): g[y][xr] = c if c != '.' else 's'
open(od + '/EC0_S_96.txt', 'w').write('\n'.join(''.join(r) for r in g) + '\n'); shutil.copy(src + '.json', od + '/EC0_S_96.json')
tmp = od + '/m.json'
subprocess.run([R + '.scratch/pixtools/venv/bin/python', '-I', R + 'v2/pixelize/tools/metrics.py', od + '/EC0_S_96', '--json', tmp], capture_output=True, cwd=R)
r = json.load(open(tmp)); r = r[0] if isinstance(r, list) else r.get('EC0_S_96', r)
print(name, 'face_ssim %.3f eye_f1 %.3f' % (r['face_ssim'], r['eye_f1']))
for y in range(49, 54): print('  ', ''.join(g[y][53:75]))
