"""eyeiso.py STEM VIEW: isolate spec eyes for the qc eye parser: (1) every 8-neighbour of an eye-block ink pixel outside the
block that is hair/eye-ramp (not skin, not silhouette edge) becomes skin s; (2) qc eye blobs that are not a spec eye (hair
strands inside the face span) are re-coloured to hair base H (K -> h). Pure python (qc_gate parts + eyecheck)."""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, '/Users/waylonhuang/Documents/other/pixelart/swordswoman/v2/qc'); sys.path.insert(0, '/Users/waylonhuang/Documents/other/pixelart/swordswoman/v2/anim_cut/tools')
import eyecheck as EC, eyetmpl as ET, qc_gate as QC, colorcheck as CC
PAL = CC.load('/Users/waylonhuang/Documents/other/pixelart/swordswoman/v2/pixelize/palette.json')
stem, view = sys.argv[1], sys.argv[2]
g = [list(l.rstrip('\n')) for l in open(stem + '.txt') if l.strip()]
H, W = len(g), len(g[0]); SK = set('sSmk')
met, fx = EC.check(g, view, 'auto')
ink = set(); box = set()
for e in met.get('eyes', []):
    t = ET.kind_tmpl(e['kind'], e['expr'])
    for j, r in enumerate(t):
        for i, c in enumerate(r):
            p = (e['x0'] + i, e['y0'] + j)
            if c != '_': box.add(p)
            if c not in '._': ink.add(p)
edge = lambda x, y: any(not (0 <= x + a < W and 0 <= y + b < H) or g[y + b][x + a] == '.' for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1)))
n1 = 0
for (x, y) in ink:
    for a in (-1, 0, 1):
        for b in (-1, 0, 1):
            q = (x + a, y + b)
            if q in box or not (0 <= q[0] < W and 0 <= q[1] < H): continue
            c = g[q[1]][q[0]]
            if c in SK or c == '.' or edge(*q): continue
            g[q[1]][q[0]] = 's'; n1 += 1
# lone dark dots on the skin just above the eyes (read as odd eyebrow dots) -> skin
n3 = 0
for e in met.get('eyes', []):
    w = len(ET.kind_tmpl(e['kind'], e['expr'])[0])
    for y in (e['y0'] - 1, e['y0']):
        for x in range(e['x0'] - 1, e['x0'] + w + 1):
            if (x, y) in box or not (0 <= x < W and 0 <= y < H): continue
            if g[y][x] in 'Kmh' and not edge(x, y) and sum(g[y + b][x + a] in SK for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1))) >= 3:
                g[y][x] = 's'; n3 += 1
P = QC.parts([''.join(r) for r in g], PAL); n2 = 0
for e in P['eyes']['list']:
    if any(p in ink for p in e['px']): continue
    for (x, y) in e['px']:
        c = g[y][x]
        if c in 'hgL': g[y][x] = 'H'; n2 += 1
        elif c == 'K' and not edge(x, y): g[y][x] = 'h'; n2 += 1
open(stem + '.txt', 'w').write('\n'.join(''.join(r) for r in g) + '\n')
print(stem, view, 'eyes', [(e['kind'], e['x0'], e['y0'], e['mismatch']) for e in met.get('eyes', [])], 'margin px', n1, 'stray blob px', n2, 'brow dots', n3)
