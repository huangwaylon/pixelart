#!/usr/bin/env python3
"""r2 SE head set: hand-drawn neutral + squash literals, variants by row edits. Writes se/*.txt."""
import os
H = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

def write(path, rows, meta):
    w = len(rows[0]); assert all(len(r) == w for r in rows), (path, [len(r) for r in rows])
    assert all(c in '.#123hHjrREeDdmnwiIpkuU' for r in rows for c in r), path
    open(f'{H}/{path}', 'w').write('\n'.join(meta + rows) + '\n')

def put(rows, y, x, s):
    r = rows[y]; rows[y] = r[:x] + s + r[x + len(s):]

def shift(rows, dx, dy, w=None):
    """translate a whole map by dx,dy (canvas grows)"""
    w = w or len(rows[0]) + abs(dx)
    out = ['.' * w for _ in range(len(rows) + abs(dy))]
    for y, r in enumerate(rows):
        for x, c in enumerate(r):
            if c != '.': put(out, y + max(dy, 0), x + max(dx, 0), c)
    return out

# ---- neutral (25x22): hair silhouette by per-row outline extents, then the old master face pasted pixel-for-pixel
OLD = [l for l in open(H + '/../anim_redraw/m48/heads/neutral.txt').read().split('\n') if l and not l.startswith(';')]
def hair(ext, w):
    rows = []
    for y, (l, r) in enumerate(ext):
        row = ['.'] * w
        if l is not None:
            for x in range(l, r + 1): row[x] = 'H'
            row[l] = row[r] = '#'
        rows.append(''.join(row))
    return rows
EXT = [(10, 14), (7, 17), (5, 19), (4, 20), (3, 21), (2, 22), (1, 22), (1, 23), (0, 23), (0, 24), (0, 24),
       (0, 23), (0, 23), (0, 23), (1, 23), (1, 23), (2, 23), (2, 22), (3, 21), (4, 20), (5, 20), (6, 7)]
N = hair(EXT, 25)
def shade(rows, rim_rows=9, back_from=10):
    g = [list(r) for r in rows]; Hh, W = len(g), len(g[0])
    at = lambda y, x: g[y][x] if 0 <= y < Hh and 0 <= x < W else '.'
    for y in range(Hh):
        xs = [x for x in range(W) if g[y][x] == 'H']
        for x in xs:
            if y < rim_rows and (at(y, x - 1) == '#' or at(y - 1, x) == '#') and x < W // 2 - 2: g[y][x] = 'j'
            elif y >= back_from and (at(y, x - 1) == '#' or (y >= back_from + 2 and at(y, x - 2) == '#')) and x < 8: g[y][x] = 'h'
            elif y >= 6 and at(y, x + 1) == '#' and x > W // 2: g[y][x] = 'h'
            elif y >= Hh - 5 and at(y + 1, x) in '#.' and x < 10: g[y][x] = 'h'
    return [''.join(r) for r in g]
put(N, 0, 10, '#####')
put(N, 1, 7, '###'); put(N, 1, 15, '###'); put(N, 2, 5, '##'); put(N, 2, 18, '##')
put(N, 20, 8, '#.........#'); put(N, 21, 6, '##..........##')
N = shade(N)
put(N, 10, 21, 'Hhh#'); put(N, 11, 21, '###.')  # bangs shelf: outlined underside overhangs the far strand by 1px
# bangs: sheen arc on the lit dome, fringe block with strand splits, side lock edge
N = [r[:5] + r[5:22].replace('j', 'H') + r[22:] if y < 5 else r for y, r in enumerate(N)]  # no sheen under the bow
put(N, 9, 10, 'h'); put(N, 10, 10, 'h'); put(N, 11, 10, 'h')
put(N, 10, 15, 'h'); put(N, 11, 15, 'h'); put(N, 9, 19, 'h'); put(N, 10, 19, 'h')
# face: old rows 17..25, cols 13..23 -> rows 11..19, cols 10..20
for oy in range(17, 26):
    for ox in range(13, 24):
        c = OLD[oy][ox]
        if c in '#123wiI' or (oy, ox) in ((17, 13), (17, 14), (17, 17), (17, 18), (17, 19), (17, 22), (17, 23), (18, 13), (18, 14)):
            put(N, oy - 6, ox - 3, c)
META_N = ['; pivot 14 19', '; anchor bow 13 4', '; anchor bun 8 -4']

BOW = [
    '.###.........###.',
    '#eeE##.....##eeE#',
    '#eEEEE#####EEEER#',
    '#eEEEER#e#EEEERR#',
    '#EEERRR#E#ERRRRR#',
    '#ERRRr##R##rRRRr#',
    '.#rr##.#r#.##rr#.',
    '..##...###...##..',
]
BUN = [
    '..###..',
    '.#jHH#.',
    '#jHHHh#',
    '#HHHHh#',
    '#HHHhh#',
    '.#hhh#.',
    '..###..',
]
def insert_col(rows, x, ys=None):
    return [r[:x + 1] + r[x:] if ys is None or y in ys else r + '.' for y, r in enumerate(rows)]

# blink: lash line closes into a low curved line, brows stay
B = N[:]
put(B, 12, 12, '22222222'); put(B, 13, 12, '222'); put(B, 13, 17, '22')
put(B, 14, 12, '###22##'); put(B, 15, 11, '#'); put(B, 15, 19, '#')
# lookup: bangs shelf up 1 as a solid block (brow/fringe-tip row moves to row 10), forehead skin band appears
#         under it, brows ride with the shelf, irises up 1 (white shows below)
U = N[:]
put(U, 9, 21, 'Hhh#'); put(U, 10, 10, 'HH33HHH33HH###.'); put(U, 11, 10, 'hh222222222Hh#')
put(U, 10, 9, 'h')
put(U, 12, 10, 'h')
put(U, 13, 12, 'wIi'); put(U, 13, 17, 'wI'); put(U, 14, 12, 'III'); put(U, 14, 17, 'II')
put(U, 15, 12, 'www'); put(U, 15, 17, 'ww')
# lean: whole head 1px forward (crown/bun/bow +1x), face block a further 1px down (an extra fringe row),
#       pivot kept at the neutral neck point so the chin overlaps the neck -> reads as a forward tilt
L = ['.' + r for r in N]
L = L[:10] + [L[9]] + L[10:]
# squash: +1 col in the back hair, +1 col in the cheek/chin (puffier), crown 2 rows shorter
S = insert_col(N, 4)
S = [r[:21] + r[20:] if y <= 16 else r[:16] + r[15:] for y, r in enumerate(S)]
S = S[:3] + S[4:6] + S[7:]
S[0] = '..........#######..........'
S[1] = '.......###HHHHHHH###.......'
S[2] = '....###jjHHHHHHHHHHH###....'
put(S, 8, 21, 'H'); put(S, 17, 5, 'h')
BOWS = [r[:3] + r[2:14] + r[13:] for r in BOW]
BOWS = BOWS[:3] + BOWS[4:]
BUNS = ['..###..', '.#jHH#.', '#jHHHh#', '#HHHhh#', '.#hhh#.', '..###..']
if __name__ == '__main__':
    write('se/head_blink.txt', B, META_N)
    write('se/head_lookup.txt', U, META_N)
    write('se/head_lean.txt', L, ['; pivot 14 19', '; anchor bow 14 4', '; anchor bun 9 -4'])
    write('se/head_squash.txt', S, ['; pivot 15 17', '; anchor bow 14 3', '; anchor bun 9 -4'])
    write('se/bow_squash.txt', BOWS, ['; pivot 9 6'])
    write('se/bun_squash.txt', BUNS, ['; pivot 3 3'])
    write('se/head_neutral.txt', N, META_N)
    write('se/bow.txt', BOW, ['; pivot 8 7'])
    write('se/bun.txt', BUN, ['; pivot 3 3'])
    print('ok')
