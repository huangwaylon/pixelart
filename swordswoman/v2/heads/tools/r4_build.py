#!/usr/bin/env python3
"""r4: derive variants from the hand-drawn se|e head_neutral.txt. usage: r4_build.py (then preview.py, runs.py)
SE (neutral 26x22, pivot = chin-bottom/neck):
  lookup = dome row 8 removed -> bangs/brows/eyes/chin/bob up 1 as a block; crown, anchors and pivot unchanged (chin lifts off the neck).
  lean   = dome row 4 doubled (face/chin drop 1, crown height kept) + crown rows 0-2 1px forward = forward-down tilt; pivot -1x = head 1px forward.
  squash = dome rows 7 and 8 removed (2px shorter), +2px wide (col 5 back hair; col 18 crown above the bangs / col 22 far strand below),
           anchors follow the crown; bow_squash/bun_squash are 1px lower.
  blink  = lash row -> skin, eyes -> flat closed lids on the mid-eye row (calm, no downward slope).
E (neutral 23x23, pivot = under the jaw/neck): lookup = dome row 7 removed; lean = dome row 4 doubled, crown rows 0-2 +1x, pivot -1x;
  squash = dome rows 7 and 8 removed, +2px (col 5 back hair; col 16 crown above the bangs / col 13 face-back edge / col 8 nape hair at the bottom)."""
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
    ln = tilt(n[:5] + n[4:], 3)
    save(f'{d}/head_lean.txt', ln, (px - 1, py), (bw[0] + 1, bw[1]), (bn[0] + 1, bn[1]))
    sq = n[:7] + n[9:]
    sq = dup(sq, lambda i: 5)
    sq = dup(sq, lambda i: 19 if i < 9 else 23)  # (cols +1 after the first dup)
    save(f'{d}/head_squash.txt', sq, (px + 1, py - 2), (bw[0] + 1, bw[1]), (bn[0] + 1, bn[1]))
    b = list(n)
    sub(b, 12, 12, '222222222'); sub(b, 13, 12, '222222222'); sub(b, 14, 12, '###22##22'); sub(b, 15, 12, '222222222')
    save(f'{d}/head_blink.txt', b, (px, py), bw, bn)
def build_e():
    n, m = load(f'{H}/e/head_neutral.txt'); (px, py), bw, bn = m['pivot'], m['bow'], m['bun']; d = f'{H}/e'
    save(f'{d}/head_lookup.txt', n[:7] + n[8:], (px, py), bw, bn)
    ln = tilt(n[:5] + n[4:], 3)
    save(f'{d}/head_lean.txt', ln, (px - 1, py), (bw[0] + 1, bw[1]), (bn[0] + 1, bn[1]))
    sq = n[:7] + n[9:]
    sq = dup(sq, lambda i: 5)
    sq = dup(sq, lambda i: 17 if i < 8 else 14 if i < 17 else 9)  # (cols +1 after the first dup)
    save(f'{d}/head_squash.txt', sq, (px + 2, py - 2), (bw[0] + 1, bw[1]), (bn[0] + 1, bn[1]))
build_se()
build_e()
print('ok')
