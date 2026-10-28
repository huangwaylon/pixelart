#!/usr/bin/env python3
"""FX + export stage. fxs.py PLAN.json [--name walk_SE_v1]
Reads <out>/cNN.png from fin.py, applies per-frame fx, writes <out>/fNN.png, gifs/<name>.gif (5x, #6e6e6e), sheets/<name>.png.
fx: afterimage | speed | feet | launch | dust1..3 | arc (needs "arc":{"a0":deg,"a1":deg,"grip":[x,y],"r0":.35,"flat":.55,"dir":1})
    | flash (blade white) | spark | footsmear | skidlines"""
import json, math, os, sys, subprocess
import numpy as np
from PIL import Image
ROOT = '/Users/waylonhuang/Documents/other/pixelart/swordswoman'
sys.path.insert(0, ROOT + '/v2/pixel/anim'); import fx2  # noqa
from fx2 import m, put, RGB, FOOT  # noqa


def op(a):
    return a[..., 3] >= 128


def afterimage(a, motion, n=2, step=7):
    out = a.copy(); sil = op(a)
    mx, my = motion; L = math.hypot(mx, my) or 1
    for g in range(n, 0, -1):
        dx, dy = int(round(-mx / L * step * g)), int(round(-my / L * step * g))
        ys, xs = np.nonzero(sil)
        for y, x in zip(ys + dy, xs + dx):
            if 0 <= y < 128 and 0 <= x < 128 and not op(out)[y, x]:
                if g == 1:
                    put(out, y, x, 'E')
                elif (x + y) % 2 == 0:
                    put(out, y, x, 'R')
    # trim ghost 1px rim so it reads as a soft echo: remove ghost px with <3 ghost neighbours
    return out


def arc(a, p):
    """blade-arc crescent: swept from angle a0 to a1 (deg, screen, y down) around grip, iso-flattened."""
    out = a.copy(); gx, gy = p['grip']; L = p.get('L', 36); r0 = p.get('r0', 0.38) * L
    flat = p.get('flat', 0.6); a0, a1 = math.radians(p['a0']), math.radians(p['a1'])
    span = a1 - a0
    body = op(a)
    for y in range(128):
        for x in range(128):
            dx, dy = x - gx, (y - gy) / flat
            r = math.hypot(dx, dy)
            if r > L + 0.5 or r < r0 * 0.6:
                continue
            th = math.atan2(dy, dx)
            # param along sweep, 0 = start (tail), 1 = blade (head)
            t = ((th - a0) / span) if span else 0
            # wrap
            for k in (-2, -1, 0, 1, 2):
                tt = (th + k * 2 * math.pi - a0) / span
                if 0 <= tt <= 1:
                    t = tt; break
            else:
                continue
            inner = L - (L - r0) * (t ** 1.4)          # thickness grows toward the blade end
            if r < inner:
                continue
            if body[y, x] and not p.get('front', 0):
                continue
            if m(a[y:y + 1, x:x + 1], 'hHj123iIp').any():
                continue
            band = (r - inner) / max(1e-3, (L - inner))
            col = 'w' if band > 0.55 else ('n' if band > 0.2 else 'm')
            if t < 0.25 and (x + y) % 2:
                continue                                  # dithered tail
            put(out, y, x, col)
    return out


def flash(a):
    out = a.copy(); st = m(a, 'n')
    hb = fx2.head_box(a); st[hb[0]:hb[1] + 1, hb[2]:hb[3] + 1] = False
    out[st] = np.append(RGB['w'], 255); return out


def spark(a, at, n=4, ln=4):
    out = a.copy(); x0, y0 = at
    for k in range(n):
        th = 2 * math.pi * k / n + 0.4
        for t in range(2, 2 + ln):
            x, y = int(round(x0 + math.cos(th) * t)), int(round(y0 + math.sin(th) * t * 0.8))
            if 0 <= x < 128 and 0 <= y < 128 and not op(out)[y, x]:
                put(out, y, x, 'w' if t < 2 + ln // 2 else 'n')
    return out


def footsmear(a, motion, rows=14):
    """subtle motion smear on the lower legs/boots: echo boot+skin pixels 2 and 4px behind, light."""
    out = a.copy(); ys = np.nonzero(op(a).any(1))[0]; yb = ys.max()
    ux = 1 if motion[0] > 0 else -1
    low = op(a).copy(); low[:yb - rows] = False
    leg = low & m(a, '#Dd123')
    for s, col in ((2, 'd'), (4, 'D')):
        for y, x in zip(*np.nonzero(leg)):
            xx = x - ux * s
            if 0 <= xx < 128 and not op(out)[y, xx] and (s == 2 or (x + y) % 2 == 0):
                put(out, y, xx, col)
    return out


def main():
    plan = json.load(open(sys.argv[1])); outd = plan['out']
    name = sys.argv[sys.argv.index('--name') + 1] if '--name' in sys.argv else plan['name']
    files, ms = [], []
    prev = None
    for i, fr in enumerate(plan['frames']):
        a = np.array(Image.open(f'{outd}/c{i:02d}.png').convert('RGBA'))
        mo = fr.get('motion', [1, 0.5])
        for f in fr.get('fx', []):
            if f == 'afterimage': a = afterimage(a, mo, fr.get('ghosts', 2), fr.get('step', 7))
            elif f == 'speed': a = fx2.speed_lines(a, mo, seed=i)
            elif f == 'feet': a = fx2.foot_lines(a, mo)
            elif f == 'launch': a = fx2.launch(a)
            elif f.startswith('dust'): a = fx2.dust(a, int(f[-1]), FOOT)
            elif f == 'arc': a = arc(a, fr['arc'])
            elif f == 'flash': a = flash(a)
            elif f == 'spark': a = spark(a, fr['spark'])
            elif f == 'footsmear': a = footsmear(a, mo)
        p = f'{outd}/f{i:02d}.png'; Image.fromarray(a).save(p); files.append(p); ms.append(str(fr.get('ms', 100)))
    px = [ROOT + '/.venv/bin/python', '-I', ROOT + '/v2/pixel/tools/px.py']
    g = f'{ROOT}/v2/anim_redraw/gifs/{name}.gif'; s = f'{ROOT}/v2/anim_redraw/sheets/{name}.png'
    subprocess.run(px + ['gif', g] + files + ['--ms', ','.join(ms), '--s', '5', '--bg', '#6e6e6e'], capture_output=True)
    subprocess.run(px + ['sheet', s, '--s', '4', '--cols', str(len(files))] + files, capture_output=True)
    print('wrote', g, s)


if __name__ == '__main__':
    main()
