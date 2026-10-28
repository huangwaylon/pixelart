import subprocess, itertools
base = ["_.......", "_K.gKKg.", "_.KKiiK.", "_..iiii.", "_..iiii."]
free = {(4, 0): '.S', (5, 0): '.S', (6, 2): 'Kg', (2, 3): '.g', (6, 1): 'gh', (3, 1): 'gh', (7, 1): '.S', (1, 2): '.S'}
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
