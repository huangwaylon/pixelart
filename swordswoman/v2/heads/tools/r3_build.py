#!/usr/bin/env python3
"""r3: derive head_lean/lookup/squash(/blink) from the hand-drawn se|e head_neutral.txt. usage: r3_build.py
lean   = whole head +1x+1y about the neck (pivot -1,-1) and crown rows (above the bangs) 1px further forward = forward tilt;
         bow/bun anchors follow the crown (+1x).
lookup = one dome row above the bangs removed -> bangs+brows+eyes+chin move up 1px as a block; crown, anchors, pivot,
         bob-tip bottom unchanged (tip row repeated).
squash = dome row + one face row removed (2px shorter), back hair/crown/near cheek widened (+2px); anchors keep their
         place relative to the crown; bow_squash/bun_squash are 1px lower."""
import os
H = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
def load(p):
    meta, rows = {}, []
    for l in open(p).read().split('\n'):
        if l.startswith(';'):
            t = l[1:].split(); meta['pivot' if t[0] == 'pivot' else t[1]] = tuple(map(int, t[-2:]))
        elif l.strip(): rows.append(l)
    return rows, meta
def save(p, rows, piv, bow, bun):
    w = max(map(len, rows)); rows = [r.ljust(w, '.') for r in rows]
    open(p, 'w').write(f'; pivot {piv[0]} {piv[1]}\n; anchor bow {bow[0]} {bow[1]}\n; anchor bun {bun[0]} {bun[1]}\n' + '\n'.join(rows) + '\n')
def dup(rows, col_of_row):  # duplicate one column per row (col_of_row(i) -> column)
    return [r[:c + 1] + r[c:] for r, c in ((r, col_of_row(i)) for i, r in enumerate(rows))]
def shear(rows, n):
    for r in rows[:n]: assert r[-1] == '.', r
    return ['.' + r[:-1] for r in rows[:n]] + rows[n:]
def sub(rows, y, x, s): rows[y] = rows[y][:x] + s + rows[y][x + len(s):]
def blank(r, a, b): return r[:a] + '.' * (b - a) + r[b:]
def build(view, bangs_top, tip_gap, sq_face_row, sq_cols, lean_n=None, lean_fix=None, sq_bow=2):
    n, m = load(f'{H}/{view}/head_neutral.txt'); p, bw, bn = m['pivot'], m['bow'], m['bun']
    d = f'{H}/{view}'
    ln = shear(n, lean_n or bangs_top)
    if lean_fix: lean_fix(ln)
    save(f'{d}/head_lean.txt', ln, (p[0] - 1, p[1] - 1), (bw[0] + 1, bw[1]), (bn[0] + 1, bn[1]))
    lk = n[:bangs_top - 1] + n[bangs_top:]
    lk = lk[:-1] + [blank(lk[-2], *tip_gap), lk[-1]]
    save(f'{d}/head_lookup.txt', lk, p, bw, bn)
    sq = n[:bangs_top - 1] + n[bangs_top:sq_face_row] + n[sq_face_row + 1:]
    sq = dup(sq, sq_cols)
    sq = dup(sq, lambda i: sq_cols2(view, i, bangs_top))
    save(f'{d}/head_squash.txt', sq, (p[0] + 2, p[1] - 2), (bw[0] + sq_bow, bw[1]), (bn[0] + 1, bn[1]))  # anchors follow the widened crown centre
    return n, m
def sq_cols2(view, i, bt):  # second widening column: crown above the bangs, near cheek below
    if view == 'se': return 13 if i < bt + 1 else 12
    return 14 if i < bt + 1 else 13
n, m = build('se', 8, (12, 16), 15, lambda i: 5)
b = list(n)  # blink: closed lids = 2px lash line + 1px outer flick, lids at mid-eye
sub(b, 11, 12, '222222222'); sub(b, 12, 12, '#22222222'); sub(b, 12, 19, '#')
sub(b, 13, 12, '2##22##22'); sub(b, 14, 12, '222222222')
save(f'{H}/se/head_blink.txt', b, m['pivot'], m['bow'], m['bun'])
build('e', 8, (13, 19), 15, lambda i: 6, 5, lambda r: sub(r, 5, 20, 'h#'), 1)  # E: tilt the top 5 rows, close row 5 to the right
print('ok')
