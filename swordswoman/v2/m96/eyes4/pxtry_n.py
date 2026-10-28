# pxtry.py SRC_STEM VIEW x,y,c ... : face_ssim of SRC master with pixel edits (temp copy in /tmp/m96t/px_%d)
import sys, os, json, shutil, subprocess
R = '/Users/waylonhuang/Documents/other/pixelart/swordswoman/'; src, v = sys.argv[1], sys.argv[2]; od = '/tmp/m96t/px_%d' % os.getpid(); os.makedirs(od, exist_ok=True)
g = [list(l.rstrip('\n')) for l in open(src + '.txt')]
for e in sys.argv[3:]:
    x, y, c = e.split(','); g[int(y)][int(x)] = c
n = os.path.basename(src); open(f'{od}/{n}.txt', 'w').write('\n'.join(''.join(r) for r in g) + '\n'); shutil.copy(src + '.json', f'{od}/{n}.json')
subprocess.run([R + '.scratch/pixtools/venv/bin/python', '-I', R + 'v2/pixelize/tools/metrics.py', f'{od}/{n}', '--json', od + '/m.json'], capture_output=True, cwd=R)
r = json.load(open(od + '/m.json')); r = r[0] if isinstance(r, list) else r
print('%.4f' % r['face_ssim']); shutil.rmtree(od)
