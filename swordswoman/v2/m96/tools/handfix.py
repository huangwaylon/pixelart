"""handfix.py IN_DIR OUT_DIR : face-round hand mitts (thumb hint) + S/SE thigh skin band. '_' keep, ',' transparent.
Templates are absolute (x0, y0) in the 128 cell of the current masters (face round, 2026-10-27)."""
import sys, os, shutil
H = {   # slender down-pointing hands like the illustration: wrist, palm, thumb | K notch | fingers to a 1px tip
 'S': [
  (41, 87, ['__KssK',
            '_KsssK',
            'KssKsK',
            'KsK_K_',
            '_K____']),
  (82, 87, ['KssK__',
            'KsssK_',
            'KsKssK',
            '_K_KsK',
            '____K_']),
 ],
 'SE': [
  (45, 89, ['__Kss___',
            '_KsssKKK',
            'KssKsK,_',
            'KsK,K,,_',
            ',K,,,,,_']),
  (79, 82, ['KssK__',
            'KsssK_',
            'KsKssK',
            '_K_KsK',
            '____K_']),
 ],
 'N': [
  (41, 84, ['_Ks___',
            '_KssSK',
            '_KsssK',
            '_KssK,',
            '__KK__']),
  (82, 85, ['_KSK_',
            'KssSK',
            'KsssK',
            '_KsK,',
            '__K__']),
 ],
}
def band(g, v):
    """S/SE: the thigh band reads too thin - S (shade) under the hem only in the first band row, rest s; SE sock-top red row -> skin"""
    if v == 'S':
        for x in range(56, 74):
            if g[91][x] == 'S' and g[90][x] != 'S' and g[90][x] not in 'K.': pass
            if g[91][x] == 'S' and x not in (56, 73): g[91][x] = 's'
    if v == 'SE':
        for x in range(58, 74):
            if g[94][x] == 'E': g[94][x] = 's'
BOW = set('eER'); HAIRC = set('HhgL')
def nb4(g, x, y): return [(x + a, y + b) for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1))]
def nb8(g, x, y): return [(x + a, y + b) for a in (-1, 0, 1) for b in (-1, 0, 1) if a or b]
def se_hair(g, box=(44, 28, 84, 50)):
    """SE: separate the bow from the hair (K line where bow touches hair, lit 'e' top edge on the bow) and calm the hair
    highlights (lone h specks / small L-g clusters inside the H mass -> H)"""
    x0, y0, x1, y1 = box
    cand = set()
    for y in range(y0, y1):
        for x in range(x0, x1):
            if g[y][x] in BOW:
                for (a, b) in nb4(g, x, y):
                    if g[b][a] in HAIRC: cand.add((a, b))
    for (a, b) in cand:
        if b > 30: g[b][a] = 'K'   # rows <= 30: qc crown px (SE bun top 61-62,30 must stay h)
    for y in range(y0 + 1, y1):
        for x in range(x0, x1):
            if g[y][x] == 'E' and (g[y - 1][x] in 'K.' or (g[y - 1][x] in 'eE' and g[y - 2][x] in 'K.')) and any(g[y][x + d] in BOW for d in (-1, 1)): g[y][x] = 'e'
    # highlight calm: connected L/g clusters < 4 px -> H; lone h with >= 6 H neighbours -> H
    seen = set()
    for y in range(32, y1):
        for x in range(x0, x1):
            if g[y][x] in 'Lg' and (x, y) not in seen:
                st, comp = [(x, y)], []
                seen.add((x, y))
                while st:
                    p = st.pop(); comp.append(p)
                    for q in nb8(g, *p):
                        if q not in seen and x0 <= q[0] < x1 and 32 <= q[1] < y1 and g[q[1]][q[0]] in 'Lg': seen.add(q); st.append(q)
                if len(comp) < 4:
                    for (a, b) in comp: g[b][a] = 'H'
    for y in range(32, y1):
        for x in range(x0, x1):
            if g[y][x] == 'h' and sum(g[b][a] == 'H' for a, b in nb8(g, x, y)) >= 6: g[y][x] = 'H'


def apply(g, v):
    for x0, y0, t in H.get(v, []):
        for j, r in enumerate(t):
            for i, c in enumerate(r):
                if c == '_': continue
                g[y0 + j][x0 + i] = '.' if c == ',' else c
    band(g, v)
    if v == 'SE': se_hair(g)
    orphans(g)


def orphans(g):
    """qc S4: lone S -> s; lone bow px -> majority bow neighbour"""
    from collections import Counter
    for y in range(1, len(g) - 1):
        for x in range(1, len(g[0]) - 1):
            c = g[y][x]
            if c not in 'SeE': continue
            nb = [g[b][a] for a, b in nb8(g, x, y)]
            if c in nb: continue
            if c == 'S' and 's' in nb: g[y][x] = 's'
            elif c in 'eE':
                bw = [n for n in nb if n in BOW]
                if bw: g[y][x] = Counter(bw).most_common(1)[0][0]
if __name__ == '__main__':
    I, O = sys.argv[1:3]; os.makedirs(O, exist_ok=True)
    for v in ['S', 'SE', 'E', 'NE', 'N']:
        for ext in ('json', 'png'):
            p = f'{I}/EC0_{v}_96.{ext}'
            if os.path.exists(p) and I != O: shutil.copy(p, O)
        L = [l.rstrip('\n') for l in open(f'{I}/EC0_{v}_96.txt')]
        meta = [l for l in L if l.startswith(';')]; g = [list(l) for l in L if not l.startswith(';')]
        apply(g, v); open(f'{O}/EC0_{v}_96.txt', 'w').write('\n'.join(meta + [''.join(r) for r in g]) + '\n')
    print('handfix ->', O)
