#!/usr/bin/env python3
"""Sequence fixer: head stamp + root pin + face check.

head stamp: the master's head (hair+bow+face, rows above its hair bottom) is pasted onto each frame, aligned to
the frame's own hair-mass bbox (top + centre), after erasing the frame's head pixels (keeps steel/sword).
root pin: lowest non-steel opaque row -> FOOT (feet planted); optional x lock to frame 0's boot centre.

Usage: fixseq.py MASTER OUT_DIR f0.png f1.png ... [--no-xlock] [--keep-y i,j] (frames listed in --keep-y are not
vertically pinned, e.g. airborne)."""
import sys, os, json
import numpy as np
from PIL import Image

PAL = json.load(open('/Users/waylonhuang/Documents/other/pixelart/swordswoman/v2/pixel/palette.json'))['colors']
RGB = {c: np.array([int(v[0][i:i + 2], 16) for i in (1, 3, 5)]) for c, v in PAL.items()}
FOOT = 120


def m(a, cs):
    r = np.zeros(a.shape[:2], bool)
    for c in cs:
        r |= (a[..., 3] >= 128) & (a[..., :3] == RGB[c]).all(-1)
    return r


def obi_top(a):
    rows = [y for y in range(a.shape[0]) if m(a[y:y + 1], 'Dd').sum() >= 5]
    # first row of the first run of >=2 consecutive obi rows (boots are lower and shorter)
    for y in rows:
        if y + 1 in rows:
            return y
    return a.shape[0]


def head_box(a):
    """bbox of the hair mass above the obi, plus the bow (red) directly above/inside the hair columns."""
    ot = obi_top(a)
    hair = m(a, 'hHj'); hair[ot:] = False
    ys, xs = np.nonzero(hair)
    y0, y1, x0, x1 = ys.min(), ys.max(), xs.min(), xs.max()
    red = m(a, 'rREe'); red[y0 + (y1 - y0) // 3:] = False   # bow lives in the top third and above
    red[:, :max(0, x0 - 2)] = False; red[:, x1 + 3:] = False
    ry, rx = np.nonzero(red)
    if len(ry):
        y0 = min(y0, ry.min()); x0 = min(x0, rx.min()); x1 = max(x1, rx.max())
    return y0, y1, x0, x1


def face_ok(a):
    y0, y1, x0, x1 = head_box(a)
    reg = a[y0:y1 + 1, x0:x1 + 1]
    return m(reg, '23').sum() >= 25 and m(reg, 'iI').sum() >= 3


def stamp(master, fr):
    my0, my1, mx0, mx1 = head_box(master)
    fy0, fy1, fx0, fx1 = head_box(fr)
    dy = fy0 - my0
    dx = int(round((fx0 + fx1) / 2 - (mx0 + mx1) / 2))
    out = fr.copy()
    head_cols = set('hHjrREe123ipI#w')
    erase = np.zeros(fr.shape[:2], bool)
    erase[max(0, fy0 - 1):fy1 + 2, max(0, fx0 - 1):fx1 + 2] = True
    steel = m(fr, 'mnw') & ~m(fr, 'w')
    keep = steel
    for c in head_cols:
        pass
    # erase only head-ish colours inside the frame's head box (never the sword)
    top3 = np.zeros_like(erase); top3[:fy0 + (fy1 - fy0) // 3] = True
    er = erase & ~keep & (m(fr, 'hHj123iIp') | (top3 & m(fr, 'rREe#')))   # never erase the collar/shoulders
    out[er] = 0
    H = master[my0:my1 + 1, mx0:mx1 + 1]
    for y in range(H.shape[0]):
        for x in range(H.shape[1]):
            if H[y, x, 3] >= 128:
                yy, xx = my0 + y + dy, mx0 + x + dx
                if 0 <= yy < out.shape[0] and 0 <= xx < out.shape[1]:
                    out[yy, xx] = H[y, x]
    # prune dangling outline left over from the generated head: '#' with no opaque non-'#' 8-neighbour
    for _ in range(3):
        op_ = out[..., 3] >= 128
        ol = op_ & (out[..., :3] == RGB['#']).all(-1)
        fill = np.pad(op_ & ~ol, 1)
        nb = np.zeros_like(ol)
        for yy in (-1, 0, 1):
            for xx in (-1, 0, 1):
                if yy or xx:
                    nb |= fill[1 + yy:1 + yy + ol.shape[0], 1 + xx:1 + xx + ol.shape[1]]
        out[ol & ~nb] = 0
    return out, (dx, dy)


def pin(a, xref=None):
    op = a[..., 3] >= 128
    body = op & ~m(a, 'mnw')
    ys = np.nonzero(body.any(1))[0]
    dy = FOOT - ys.max()
    dx = 0
    if xref is not None:
        low = body.copy(); low[:ys.max() - 6] = False
        dx = int(round(xref - np.nonzero(low)[1].mean()))
    o = np.zeros_like(a)
    H, W = a.shape[:2]
    yy, xx = np.nonzero(op)
    ny, nx = yy + dy, xx + dx
    ok = (ny >= 0) & (ny < H) & (nx >= 0) & (nx < W)
    o[ny[ok], nx[ok]] = a[yy[ok], xx[ok]]
    return o, dx, dy


args = sys.argv[1:]
xlock = '--no-xlock' not in args
keep_y = set()
if '--keep-y' in args:
    keep_y = {int(v) for v in args[args.index('--keep-y') + 1].split(',')}
files = [x for x in args if x.endswith('.png')]
master = np.array(Image.open(files[0]).convert('RGBA'))
outdir = [x for x in args if not x.endswith('.png') and not x.startswith('--') and not x.replace(',', '').isdigit()][0]
os.makedirs(outdir, exist_ok=True)
xref = None
for i, f in enumerate(files[1:]):
    a = np.array(Image.open(f).convert('RGBA'))
    ok = face_ok(a)
    a, (sdx, sdy) = stamp(master, a)
    if i in keep_y:
        b, pdx, pdy = a, 0, 0
    else:
        if xref is None and xlock:
            body = (a[..., 3] >= 128) & ~m(a, 'mnw'); ys = np.nonzero(body.any(1))[0]
            low = body.copy(); low[:ys.max() - 6] = False
            xref = np.nonzero(low)[1].mean()
        b, pdx, pdy = pin(a, xref if xlock else None)
    out = os.path.join(outdir, os.path.basename(f).replace('.png', '_fx.png'))
    Image.fromarray(b).save(out)
    print(f'{os.path.basename(f)} face_ok_before={ok} stamp_d=({sdx},{sdy}) pin_d=({pdx},{pdy})')
