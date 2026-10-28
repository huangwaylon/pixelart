#!/usr/bin/env python3
"""r5: derive variants from the hand-drawn se|e head_neutral.txt. usage: r5_build.py (then preview.py, runs.py)
SE (neutral 24x23, pivot = under the chin/neck):
  lookup = dome row 8 removed -> bangs/eyes/chin/bob up 1 as a block; crown, anchors and pivot unchanged.
  lean   = dome row 4 doubled + crown rows 0-3 1px forward (row 3 keeps its front edge) = forward-down tilt; pivot -1x.
  squash = dome rows 7 and 8 removed (2px shorter), +2px wide (col 5 back hair; col 16 crown above the bangs / col 20 far strand below);
           bow/bun are the neutral parts, anchored 1px lower (no squashed bow: loops stay up).
  blink  = lash row -> skin, eyes -> flat closed lids on the w row (both eyes, calm).
E (neutral 23x22): lookup = dome row 7 removed; lean = dome row 4 doubled, crown rows 0-2 +1x, pivot -1x;
  squash = dome rows 7 and 8 removed, +2px (col 5 back hair; col 16 crown above the bangs / col 14 face below = wider cheek), bow/bun 1px lower."""
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
def dup(rows, col_of_row):
    return [r[:c + 1] + r[c:] for r, c in ((r, col_of_row(i)) for i, r in enumerate(rows))]
def sub(rows, y, x, s): rows[y] = rows[y][:x] + s + rows[y][x + len(s):]
def tilt(rows, n, k=1):  # rows[:n] shifted k px right (crown forward)
    return ['.' * k + r[:-k] if r.endswith('.' * k) else r for r in rows[:n]] + rows[n:]
def build_se():
    n, m = load(f'{H}/se/head_neutral.txt'); (px, py), bw, bn = m['pivot'], m['bow'], m['bun']; d = f'{H}/se'
    lk = n[:8] + n[9:]
    save(f'{d}/head_lookup.txt', lk, (px, py), bw, bn)
    ln = tilt(n[:5] + n[4:], 4)
    ln[3] = '.' + n[3].replace('H', '', 1)[:-1] + '.'  # row 3: back edge +1, front edge kept
    save(f'{d}/head_lean.txt', ln, (px - 1, py), (bw[0] + 1, bw[1]), (bn[0] + 1, bn[1]))
    sq = n[:7] + n[9:]
    sq = dup(sq, lambda i: 5)
    sq = dup(sq, lambda i: 17 if i < 9 else 21)  # (cols +1 after the first dup)
    save(f'{d}/head_squash.txt', sq, (px + 1, py - 2), (bw[0] + 1, bw[1] + 1), (bn[0] + 1, bn[1] + 1))
    b = list(n)  # eyes rows 12-15 (lash/w/i/I) -> calm closed lids on the w row
    sub(b, 12, 8, '22222222222'); sub(b, 13, 8, '22###22##22'); sub(b, 14, 8, '22222222222'); sub(b, 15, 8, '22222222222')
    save(f'{d}/head_blink.txt', b, (px, py), bw, bn)
def build_e():
    n, m = load(f'{H}/e/head_neutral.txt'); (px, py), bw, bn = m['pivot'], m['bow'], m['bun']; d = f'{H}/e'
    save(f'{d}/head_lookup.txt', n[:7] + n[8:], (px, py), bw, bn)
    ln = tilt(n[:5] + n[4:], 3)
    save(f'{d}/head_lean.txt', ln, (px - 1, py), (bw[0] + 1, bw[1]), (bn[0] + 1, bn[1]))
    sq = n[:7] + n[9:]
    sq = dup(sq, lambda i: 5)
    sq = dup(sq, lambda i: 17 if i < 8 else 15)  # (cols +1 after the first dup)
    save(f'{d}/head_squash.txt', sq, (px + 2, py - 2), (bw[0] + 1, bw[1] + 1), (bn[0] + 1, bn[1] + 1))
build_se()
build_e()
print('ok')
