"""S5 r2 polish kit: palette-locked exact-pixel helpers (Claude hand pixel art)."""
import json, math
import numpy as np
from PIL import Image
PAL = json.load(open('/Users/waylonhuang/Documents/other/pixelart/swordswoman/docs/palette.json'))
def hx(h): return (int(h[1:3], 16), int(h[3:5], 16), int(h[5:7], 16))
R = PAL['ramps']
CH = {'K': PAL['outline'], 'm': R['skin'][0], 's': R['skin'][1], 'S': R['skin'][2], 'h': R['hair'][0], 'H': R['hair'][1],
      'J': R['hair'][2], 'v': R['red'][0], 'r': R['red'][1], 'R': R['red'][2], 'C': R['red'][3], 'l': R['leather'][1],
      'L': R['leather'][2], 'd': R['dark'][1], 't': R['steel'][0], 'T': R['steel'][1], 'w': R['steel'][2],
      'e': R['eye'][0], 'E': R['eye'][1], 'p': R['pink'][0], 'P': R['pink'][1], 'u': R['purple'][0]}
RGB = {k: hx(v) for k, v in CH.items()}
INV = {v: k for k, v in RGB.items()}

def load(f): return np.array(Image.open(f).convert('RGBA'))
def save(a, f): Image.fromarray(a).save(f)
def ch(a, x, y):
    if not (0 <= x < a.shape[1] and 0 <= y < a.shape[0]) or a[y, x, 3] == 0: return '.'
    return INV.get(tuple(int(v) for v in a[y, x, :3]), '?')
def put(a, x, y, c, mode='over'):
    if not (0 <= x < a.shape[1] and 0 <= y < a.shape[0]): return False
    if mode == 'behind' and a[y, x, 3] > 0: return False
    if c == '.': a[y, x] = 0; return True
    a[y, x, :3] = RGB[c]; a[y, x, 3] = 255; return True
def stamp(a, x0, y0, rows, mode='over'):
    """rows: list of strings of palette chars; '_' skip, '.' clear"""
    for j, r in enumerate(rows):
        for i, c in enumerate(r):
            if c != '_': put(a, x0 + i, y0 + j, c, mode)
def dump(a, x0, y0, x1, y1):
    for y in range(y0, y1 + 1): print('%3d ' % y + ''.join(ch(a, x, y) for x in range(x0, x1 + 1)))
def line(a, p0, p1, c, mode='over'):
    (x0, y0), (x1, y1) = p0, p1; n = max(abs(x1 - x0), abs(y1 - y0), 1)
    for k in range(n + 1): put(a, round(x0 + (x1 - x0) * k / n), round(y0 + (y1 - y0) * k / n), c, mode)
def angd(ang, a0, a1):
    """progress s of ang along a0->a1 (deg, either direction), None if outside"""
    span = a1 - a0
    for k in (-360, 0, 360):
        s = (ang + k - a0) / span if span else 0
        if 0 <= s <= 1: return s
    return None
def crescent(a, cx, cy, r, a0, a1, wmax=9, w0=1.2, pw=1.15, front=None, over_rows=3, protect=None,
             rim=(0.25, 1.6, 0.6, 2.3), clear_old=None, inner_echo=True):
    """Blade-arc crescent: outer edge = tip path (radius r), band grows inward; thickness w0 at tail (a0) -> wmax at lead (a1).
    tones: steel_2 rim (depth < rim[1] after s>rim[0]; < rim[3] after s>rim[2]), pink_1 body, pink_0 inner third.
    front(x,y,ang) -> True where the band is in front of the body (paints over for depth < over_rows)."""
    H, W = a.shape[:2]
    if clear_old:
        for y in range(H):
            for x in range(W):
                d = math.hypot(x - cx, y - cy); ang = math.degrees(math.atan2(y - cy, x - cx))
                if r - clear_old <= d <= r + 1.5 and angd(ang, a0 - 4 * np.sign(a1 - a0), a1 + 3 * np.sign(a1 - a0)) is not None:
                    if ch(a, x, y) in 'pPw' and (protect is None or not protect[y, x]): a[y, x] = 0
    pend = []
    for y in range(H):
        for x in range(W):
            d = math.hypot(x - cx, y - cy); ang = math.degrees(math.atan2(y - cy, x - cx))
            s = angd(ang, a0, a1)
            if s is None: continue
            th = w0 + (wmax - w0) * s ** pw
            dep = r + 0.5 - d
            if not (0 <= dep < th): continue
            if (s > rim[2] and dep < rim[3]) or (s > rim[0] and dep < rim[1]): c = 'w'
            elif dep >= th * 0.62 and th >= 3: c = 'p'
            else: c = 'P'
            fr = front(x, y, ang) if front else False
            mode = 'over' if (fr and dep < over_rows) else 'behind'
            if protect is not None and protect[y, x]: continue
            pend.append((x, y, c, mode))
    for x, y, c, mode in pend: put(a, x, y, c, mode)
    if inner_echo:   # double crescent: a thin pink_0 echo arc 2 px inside the band, lead 60 % only
        for k in range(400):
            s = 0.4 + 0.52 * k / 399; ang = math.radians(a0 + (a1 - a0) * s)
            th = w0 + (wmax - w0) * s ** pw; rr = r - th - 1.5
            put(a, round(cx + rr * math.cos(ang)), round(cy + rr * math.sin(ang)), 'p', 'behind')
def thick_line(a, p0, p1, w0, w1, tones, mode='behind'):
    (x0, y0), (x1, y1) = p0, p1; L = math.hypot(x1 - x0, y1 - y0); n = int(L * 3) + 2
    for k in range(n + 1):
        t = k / n; x, y = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t; rr = (w0 + (w1 - w0) * t) / 2
        for yy in range(int(y - rr - 1), int(y + rr + 2)):
            for xx in range(int(x - rr - 1), int(x + rr + 2)):
                if (xx - x) ** 2 + (yy - y) ** 2 <= rr * rr + 0.25:
                    put(a, xx, yy, tones[min(len(tones) - 1, int(t * len(tones)))], mode)
def orphans(a, keep='wK'):
    """remove isolated single pixels (no 8-neighbours) except those tones in keep"""
    H, W = a.shape[:2]; n = 0
    al = a[:, :, 3] > 0
    for y in range(H):
        for x in range(W):
            if al[y, x] and not al[max(0, y - 1):y + 2, max(0, x - 1):x + 2].sum() > 1 and ch(a, x, y) not in keep:
                a[y, x] = 0; n += 1
    return n
