import sys, numpy as np
ch = '.HBOFEcTLsuxAZaz12QW34pqk!'
n = sys.argv[1]; x0 = int(sys.argv[2]) if len(sys.argv) > 2 else 36
ids = np.load(f"hybrid/S6_claude_pixel/r1/guide/{n}_ids.npy")
ys = np.nonzero(ids.any(1))[0]
print('    ' + ''.join(str((x // 10) % 10) for x in range(x0, x0 + 64)))
print('    ' + ''.join(str(x % 10) for x in range(x0, x0 + 64)))
for y in range(ys.min(), ys.max() + 1):
    print('%3d ' % y + ''.join(ch[v] for v in ids[y, x0:x0 + 64]))
