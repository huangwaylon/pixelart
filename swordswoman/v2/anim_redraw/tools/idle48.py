#!/usr/bin/env python3
"""Procedural idle from ONE finished frame (zero shimmer): breathing squash (rows above the cut shift 1px down),
head lag, bow lag, blink. idle48.py BASE_c.png NAME [cut_row]
-> work48/idle/<NAME>/fNN.png + gifs/<NAME>.gif + sheets/<NAME>.png"""
import os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(__file__))
from fin48 import to_grid, to_img, export, isin, master_head, A, CELL  # noqa

base = to_grid(sys.argv[1]); name = sys.argv[2]
ys, xs = np.nonzero(base != '.')
hair = isin(base, 'hHj')
from fin48 import comps
_lab, _n = comps(hair); _sz = np.bincount(_lab.ravel()); _sz[0] = 0; hair = _lab == _sz.argmax()   # head hair only
hy = np.nonzero(hair.any(1))[0]
head_bot = hy.max()                                     # last hair row ~ chin
cut = int(sys.argv[3]) if len(sys.argv) > 3 else head_bot + 8
print('blink rows <=', head_bot + 3)    # torso rows above this breathe
_rows = np.arange(CELL)[:, None] * np.ones((1, CELL), int)
bow = (base != '.') & ((_rows < hy.min()) | (isin(base, 'rREe') & (_rows < hy.min() + 2)))


def move(g, mask, dy):
    o = g.copy(); src = g.copy()
    o[mask] = '.'
    yy, xx = np.nonzero(mask)
    for y, x in sorted(zip(yy, xx), key=lambda t: -t[0] if dy > 0 else t[0]):
        if 0 <= y + dy < CELL: o[y + dy, x] = src[y, x]
    return o


def squash(g, row, d):
    """delete d rows starting at `row` (everything above slides down d px), pad empty rows on top"""
    if d == 0: return g
    if d < 0:                                      # stretch: repeat row, drop empty top rows
        return np.vstack([g[-d:row], np.repeat(g[row:row + 1], -d, 0), g[row:]])
    o = np.delete(g, range(row, row + d), axis=0)
    return np.vstack([np.full((d, CELL), '.', dtype=g.dtype), o])


def frame(torso=0, head=0, bowd=0, blink=False):
    g = squash(base.copy(), cut, torso)              # chest/arms/head drop by `torso` (waist rows absorb it)
    g = squash(g, head_bot + 1 + torso, head - torso)  # head drops further (neck/collar row absorbs it)
    if blink == 'half':                            # upper lid down 1 row
        ey = np.nonzero(isin(g, 'iIw') & (np.arange(CELL)[:, None] <= head_bot))
        for y, x in zip(*ey):
            if y == ey[0].min(): g[y, x] = '#'
    elif blink:
        ey = np.nonzero(isin(g, 'iIw') & (np.arange(CELL)[:, None] <= head_bot))
        for y, x in zip(*ey):
            g[y, x] = '#' if y == ey[0].max() else '2'
    return g


seq = [  # (torso, head, bow, blink, ms): knees give 2px with the head trailing 1px, blink at the low hold, overshoot up
    (0, 0, 0, False, 320), (1, 1, 0, False, 140), (2, 2, 0, False, 140), (2, 3, 0, False, 260),
    (2, 3, 0, 'half', 80), (2, 3, 0, True, 120), (2, 3, 0, 'half', 80), (1, 2, 0, False, 140),
    (0, 1, 0, False, 140), (-1, -1, 0, False, 200)]
out = f'{A}/work48/idle/{name}'; os.makedirs(out, exist_ok=True)
frames = []
for i, (t, h, b, bl, ms) in enumerate(seq):
    f = frame(t, h, b, bl); frames.append(f); to_img(f).save(f'{out}/f{i:02d}.png')
export(frames, [s[4] for s in seq], name)
print(name, 'cut', cut, 'head_bot', head_bot)
