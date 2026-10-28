#!/usr/bin/env python3
"""Pixel blade-arc smear. Draws a crescent from the blade tip of frame A to the blade tip of frame B around the
hand (grip) onto frame S (the smear frame), behind or in front of the character.

Usage: smear.py FRAME_A FRAME_B FRAME_S OUT [--front] [--inner 0.45] [--ccw]
Blade = steel pixels (m/n/w). Grip = steel pixel nearest the body centre (red centroid); tip = farthest.
Crescent palette (from palette.json): core 'w' at the outer 40%, body 'n', 1px trailing edge 'p' (pink) to
read as speed; no outline (smears never get a dark outline)."""
import sys, json, math
import numpy as np
from PIL import Image

PAL = json.load(open('/Users/waylonhuang/Documents/other/pixelart/swordswoman/v2/pixel/palette.json'))['colors']
rgb = lambda c: [int(PAL[c][0][i:i + 2], 16) for i in (1, 3, 5)]
STEEL = [rgb(c) for c in 'mnw']; RED = [rgb(c) for c in 'rREe']


def mask(a, cols):
    m = np.zeros(a.shape[:2], bool)
    for c in cols:
        m |= (a[..., 3] >= 128) & (a[..., :3] == c).all(-1)
    return m


def blade(a):
    st = mask(a, STEEL); rd = mask(a, RED)
    ys, xs = np.nonzero(st); ry, rx = np.nonzero(rd)
    cx, cy = rx.mean(), ry.mean()
    d = (xs - cx) ** 2 + (ys - cy) ** 2
    return (xs[d.argmin()], ys[d.argmin()]), (xs[d.argmax()], ys[d.argmax()])


args = sys.argv[1:]
front = '--front' in args; ccw = '--ccw' in args; hide = '--hideblade' in args
inner = float(args[args.index('--inner') + 1]) if '--inner' in args else 0.45
flat = float(args[args.index('--flat') + 1]) if '--flat' in args else 1.0      # iso ellipse: y radius = flat*R
via = args[args.index('--via') + 1] if '--via' in args else 'short'           # short | down | up
NUMS = {inner, flat}
fa, fb, fs, out = [x for x in args if x.endswith('.png')][:4]
A = np.array(Image.open(fa).convert('RGBA')); B = np.array(Image.open(fb).convert('RGBA'))
Sx = np.array(Image.open(fs).convert('RGBA'))
(gx, gy), (ax, ay) = blade(A)
(hx, hy), (bx, by) = blade(B)
px_, py_ = (gx + hx) / 2, (gy + hy) / 2                       # pivot = mean grip
E = lambda x, y: (x - px_, (y - py_) / flat)
R = max(math.hypot(*E(ax, ay)), math.hypot(*E(bx, by))) + 1
t0 = math.atan2(E(ax, ay)[1], E(ax, ay)[0]); t1 = math.atan2(E(bx, by)[1], E(bx, by)[0])
dt = (t1 - t0) % (2 * math.pi)          # positive = clockwise on screen (y down)
mid = t0 + dt / 2
if via == 'down' and math.sin(mid) < 0:  # make the arc pass below the pivot (in front of the body in iso)
    dt -= 2 * math.pi
elif via == 'up' and math.sin(mid) > 0:
    dt -= 2 * math.pi
elif via == 'short' and dt > math.pi:
    dt -= 2 * math.pi
if ccw:
    dt = dt - 2 * math.pi if dt > 0 else dt + 2 * math.pi
layer = np.zeros_like(Sx)
H, W = Sx.shape[:2]
for y in range(H):
    for x in range(W):
        ex, ey = E(x, y); r = math.hypot(ex, ey)
        if r > R or r < R * inner:
            continue
        t = (math.atan2(ey, ex) - t0)
        u = (t % (2 * math.pi)) / dt if dt > 0 else ((t % (2 * math.pi)) - 2 * math.pi) / dt
        if not (0 <= u <= 1):
            continue
        # crescent: thicker at the leading end (u->1), thin tail (u->0)
        rin = R - (R - R * inner) * (u ** 1.3)          # tapers to ~1px at the tail, full width at the blade
        if r < rin or (R - rin) < 0.8:
            continue
        if u < 0.35 and int(u * 30) % 2 == 0:           # dashed speed-tail
            continue
        rr = (r - rin) / max(1e-6, R - rin)
        c = 'w' if rr > 0.6 else ('n' if rr > 0.25 else 'm')
        layer[y, x, :3] = rgb(c); layer[y, x, 3] = 255
if hide:   # smear frame: the blade becomes the smear (remove the drawn steel, keep the hand)
    st = mask(Sx, STEEL)
    Sx[st] = 0
    zone = st.copy()
    for _ in range(2):   # dilate the removed-blade area by 2px
        z = np.pad(zone, 1); zone = zone | z[:-2, 1:-1] | z[2:, 1:-1] | z[1:-1, :-2] | z[1:-1, 2:] | z[:-2, :-2] | z[2:, 2:] | z[:-2, 2:] | z[2:, :-2]
    for _ in range(40):  # prune 1px spurs (blade outline) inside that zone
        op_ = Sx[..., 3] >= 128; p_ = np.pad(op_, 1)
        cnt = sum(p_[1 + dy:1 + dy + op_.shape[0], 1 + dx:1 + dx + op_.shape[1]].astype(int)
                  for dy in (-1, 0, 1) for dx in (-1, 0, 1) if dy or dx)
        kill = op_ & zone & (cnt <= 2)
        if not kill.any():
            break
        Sx[kill] = 0
    # keep only the largest 8-connected opaque component (drops the detached blade outline / guard specks)
    op_ = Sx[..., 3] >= 128
    lab = np.zeros(op_.shape, int); cur = 0; sizes = {}
    for y0, x0 in zip(*np.nonzero(op_)):
        if lab[y0, x0]:
            continue
        cur += 1; stack = [(y0, x0)]; lab[y0, x0] = cur; n = 0
        while stack:
            y, x = stack.pop(); n += 1
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    yy, xx = y + dy, x + dx
                    if 0 <= yy < op_.shape[0] and 0 <= xx < op_.shape[1] and op_[yy, xx] and not lab[yy, xx]:
                        lab[yy, xx] = cur; stack.append((yy, xx))
        sizes[cur] = n
    small = [k for k, n in sizes.items() if n < 30]
    Sx[op_ & np.isin(lab, small)] = 0
op = Sx[..., 3] >= 128
out_a = Sx.copy()
if front:
    out_a[layer[..., 3] > 0] = layer[layer[..., 3] > 0]
else:
    m = (layer[..., 3] > 0) & ~op
    out_a[m] = layer[m]
Image.fromarray(out_a).save(out)
print(f'smear pivot=({px_:.0f},{py_:.0f}) R={R:.1f} from {math.degrees(t0):.0f} sweep {math.degrees(dt):.0f}')
