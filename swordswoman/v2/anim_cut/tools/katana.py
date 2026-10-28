#!/usr/bin/env python3
"""Generate pre-drawn katana sprites at 16 pixel-friendly directions (slopes 0, 1:2, 1:1, 2:1).
dir index d: 0=E(right), counter-clockwise in screen (4=up, 8=W, 12=down). Pivot = grip (hand).
Writes parts/common/kat_DD.txt.  Hand-clean afterwards if needed (files are plain char-maps).
"""
import os, sys, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cm
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
# direction table: (major_axis, sx, sy, p, q)  step along major p, minor q per p
base = [(1, 0), (2, 1), (1, 1), (1, 2), (0, 1)]  # (x,y) per unit in first quadrant, y up
dirs = []
for quad in range(4):
    for i in range(4):
        vx, vy = base[i]
        # rotate by quad*90 (y up)
        for _ in range(quad):
            vx, vy = -vy, vx
        dirs.append((vx, -vy))  # convert to screen y-down

def line(vx, vy, n):
    """n pixels from origin along (vx,vy) integer direction, pixel-perfect pattern."""
    ax, ay = abs(vx), abs(vy); sx, sy = (1 if vx > 0 else -1 if vx < 0 else 0), (1 if vy > 0 else -1 if vy < 0 else 0)
    pts = []
    if ax >= ay:
        for k in range(n):
            pts.append((sx * k, sy * ((k * ay) // ax if ax else 0)))
    else:
        for k in range(n):
            pts.append((sx * ((k * ax) // ay), sy * k))
    return pts

BL, HL = 19, 6   # blade px, handle px (pommel..guard), along major axis
def make(d):
    vx, vy = dirs[d]
    px = {}
    # handle goes backward from grip, blade forward
    import math
    ax, ay = abs(vx), abs(vy); f = math.hypot(ax, ay) / max(ax, ay)
    back = line(-vx, -vy, max(3, round(4 / f)))
    fwd = line(vx, vy, round((BL + 3) / f))
    major_x = abs(vx) >= abs(vy)
    # perpendicular offset for 2px-wide blade: shift along minor axis toward screen-up/left (lit side)
    if major_x:
        off = (0, -1)
    else:
        off = (-1, 0) if True else (1, 0)
    for k, (x, y) in enumerate(back):
        px[(x, y)] = 'D' if k % 2 == 0 else 'd'
    for k, (x, y) in enumerate(fwd):
        if k == 0:
            px[(x, y)] = 'd'
        elif k == 1:
            px[(x, y)] = 'D'
        elif k == 2:   # guard
            px[(x, y)] = 'k'
            px[(x + off[0], y + off[1])] = 'k'
            px[(x - off[0], y - off[1])] = 'k'
        else:
            px[(x, y)] = 'n' if k < len(fwd) - 1 else 'w'
            if k < len(fwd) - 2:
                px[(x + off[0], y + off[1])] = 'w'
    # outline (8-neigh not; 4-neigh dark outline around everything)
    out = {}
    for (x, y) in list(px):
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            q = (x + dx, y + dy)
            if q not in px:
                out[q] = '#'
    allp = dict(out); allp.update(px)
    xs = [p[0] for p in allp]; ys = [p[1] for p in allp]
    x0, y0 = min(xs), min(ys)
    g = np.full((max(ys) - y0 + 1, max(xs) - x0 + 1), '.', dtype='<U1')
    for (x, y), c in allp.items():
        g[y - y0, x - x0] = c
    return g, (-x0, -y0)

os.makedirs(os.path.join(ROOT, 'parts', 'common'), exist_ok=True)
for d in range(16):
    g, piv = make(d)
    cm.write_cm(os.path.join(ROOT, 'parts', 'common', 'kat_%02d.txt' % d), g, {'pivot': piv, 'anchors': {}})
print('ok', len(dirs))
