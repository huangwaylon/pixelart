# greedy_px.py STEM VIEW "x,y:chars;..." : greedy single-px improvements of face_ssim
import sys, subprocess
stem, v, spec = sys.argv[1:4]
free = [(tuple(map(int, a.split(':')[0].split(','))), a.split(':')[1]) for a in spec.split(';')]
def sc(ed): return float(subprocess.run(['python3', 'eyes4/pxtry.py', stem, v] + ['%d,%d,%s' % (x, y, c) for (x, y), c in ed.items()], capture_output=True, text=True).stdout.split()[-1])
cur = {}; best = sc(cur); print('base', best)
for it in range(2):
    for p, cs in free:
        for c in cs:
            ed = dict(cur); ed[p] = c
            s = sc(ed)
            if s > best + 0.0005: best, cur = s, ed; print('  ', p, c, best)
print('final', best, cur)
