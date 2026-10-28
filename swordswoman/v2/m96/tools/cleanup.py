"""cleanup.py STEM VIEW: programmatic finish (re-runnable): skin-band legfix, O1 (silhouette-edge px -> K), S4 orphans ->
4-neighbour majority (eye blocks, W and K exempt), re-render png. Eye blocks found by eyecheck are protected."""
import sys, os, subprocess, json
from collections import Counter
sys.path.insert(0, '/Users/waylonhuang/Documents/other/pixelart/swordswoman/v2/pixelize/tools'); sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pzlib as Z, m96 as M, eyecheck as EC, eyetmpl as ET
stem, view = sys.argv[1], sys.argv[2]
subprocess.run([sys.executable, '-I', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'legfix.py'), stem, '84', '100'], capture_output=True)
g, meta = Z.read(stem); keys, rgb, _ = Z.load_pal(M.PAL); H, W = g.shape
prot = set()
met, _ = EC.check(g.tolist(), view, 'auto')
for e in met.get('eyes', []):
    for j, r in enumerate(ET.kind_tmpl(e['kind'], e['expr'])):
        for i, c in enumerate(r):
            if c != '_': prot.add((e['x0'] + i, e['y0'] + j))
ANC = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'heads', 'anchor.json')))['views'].get(view, {})
if ANC.get('mouth'):
    mx, my = ANC['mouth']; prot |= {(mx + i, my + j) for i in range(4) for j in range(3)}
for bx, by, n in ANC.get('blush', []): prot |= {(bx + i, by + j) for i in range(-1, 4) for j in range(2)}
N4 = ((1, 0), (-1, 0), (0, 1), (0, -1)); N8 = [(a, b) for a in (-1, 0, 1) for b in (-1, 0, 1) if a or b]
n1 = n2 = n3 = 0
# grey (hair/sock ramp) specks on skin -> skin shadow S (neck, thighs, face): >=2 skin 4-neighbours and no H/h neighbour
for y in range(H):
    for x in range(W):
        if g[y, x] in 'gLdD' and (x, y) not in prot and y > meta['oy'] + 0.36 * meta['h']:   # below the chin only (face stays as drawn)
            nb = [g[y + b, x + a] for a, b in N4 if 0 <= x + a < W and 0 <= y + b < H]
            if sum(c in 'sSmk' for c in nb) >= 2 and not any(c in 'hHDd' for c in nb if c != g[y, x]): g[y, x] = 'S'; n3 += 1
for it in range(2):
    for y in range(H):
        for x in range(W):
            c = g[y, x]
            if c == '.' or (x, y) in prot: continue
            if c != 'K' and any(not (0 <= x + a < W and 0 <= y + b < H) or g[y + b, x + a] == '.' for a, b in N4):
                g[y, x] = 'K'; n1 += 1; continue
            if c in 'WK': continue
            if all(g[y + b, x + a] != c for a, b in N8 if 0 <= x + a < W and 0 <= y + b < H):
                nb = [g[y + b, x + a] for a, b in N4 if 0 <= x + a < W and 0 <= y + b < H and g[y + b, x + a] not in '.K']
                if not nb: nb = [g[y + b, x + a] for a, b in N8 if 0 <= x + a < W and 0 <= y + b < H and g[y + b, x + a] != '.']
                if nb: g[y, x] = Counter(nb).most_common(1)[0][0]; n2 += 1
# hair speckle: g/L clusters of <= 2 px fully inside hair (h/H/g/L/K neighbours only) above the chin -> H
from scipy import ndimage as nd
import numpy as np
n4 = 0; chin = int(meta['oy'] + 0.36 * meta['h'])
lab, nl = nd.label(np.isin(g, ['g', 'L']), np.ones((3, 3)))
for i in range(1, nl + 1):
    ys, xs = np.where(lab == i)
    if len(ys) > 2 or ys.max() > chin or any((x, y) in prot for x, y in zip(xs, ys)): continue
    nb = {g[y + b, x + a] for x, y in zip(xs, ys) for a, b in N8 if 0 <= x + a < W and 0 <= y + b < H and lab[y + b, x + a] != i}
    if nb <= set('hHK'): g[ys, xs] = 'H'; n4 += len(ys)
Z.save(g, stem, keys, rgb, meta); print(stem, 'O1->K', n1, 'orphans', n2, 'grey-on-skin', n3, 'hair specks', n4)
