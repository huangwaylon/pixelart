import subprocess, itertools
base = ["_.......", "_KgKKgg.", "_KKiiiK.", "_..iiii.", "_..iiii."]
free = {(0, 1): '_K', (1, 1): 'Ks', (6, 1): 'ghs.', (6, 2): 'Kg', (1, 3): '.Kh', (2, 3): '.g', (1, 4): '.h', (7, 1): '.g', (7, 2): '.g', (3, 0): '.S', (4, 0): '.S'}
def score(rows):
    o = subprocess.run(['python3', 'eyes4/try_s.py', 'gr'] + rows, capture_output=True, text=True).stdout.split()
    return float(o[2])
cur = list(base); best = score(cur); print('base', best)
for it in range(2):
    for (i, j), opts in free.items():
        for c in opts:
            r = list(cur); r[j] = r[j][:i] + c + r[j][i + 1:]
            if r == cur: continue
            s = score(r)
            if s > best + 0.0005: best, cur = s, r; print('  ', (54 + i, 49 + j), c, best, cur)
print('final', best, cur)
