# Programmatic silhouette blockouts on the measured template (prop/template.json), 64x64 cell, soles on row 61.
# v3: even grid, body centre between cols 31|32. Codes: H hair B bun W bow F face N neck e eye D dress O obi
# A sleeve h hand/forearm L leg T boot. Character is UNARMED (user 2026-10-26). Head (H,B,W,F,e) = placeholder,
# see blockout/head_region.json. <V>_body.txt = same map without the arms (used to measure waist/hip body-only).
import numpy as np
from PIL import Image
OUT = '/Users/waylonhuang/Documents/other/pixelart/swordswoman/v2/prop/blockout/'
PAL = dict(H=(48, 38, 64), B=(64, 50, 80), W=(226, 52, 70), F=(246, 208, 182), N=(230, 186, 160), e=(20, 20, 30), D=(196, 44, 52),
           O=(236, 222, 190), A=(168, 34, 46), h=(246, 208, 182), L=(240, 198, 172), T=(110, 64, 44))
def blank(): return np.full((64, 64), '.', dtype='<U1')
def put(g, r, x0, x1, c):
    for x in range(max(0, x0), min(64, x1 + 1)): g[r, x] = c
def cw(g, r, w, c, dx=0):  # even width centred between cols 31|32 (+dx)
    put(g, r, 32 - w // 2 + dx, 32 - w // 2 + w - 1 + dx, c)
def ell(g, cx, cy, rx, ry, c):
    for r in range(64):
        for x in range(64):
            if ((x - cx) / rx) ** 2 + ((r - cy) / ry) ** 2 <= 1: g[r, x] = c
def bow(g, cx, cy, span=5, rx=3.6, ry=2.8, up=0):
    ell(g, cx - span, cy - up, rx, ry, 'W'); ell(g, cx + span, cy + up, rx, ry, 'W'); ell(g, cx, cy, 1.5, 1.8, 'W')
HAIR = [(14, 6), (15, 10), (16, 12)] + [(r, 14) for r in range(17, 28)]
FACE = [(r, 8) for r in range(21, 26)] + [(26, 6), (27, 4)]
def head_front(g, view):
    back = view in ('N', 'NE'); fx = 2 if view == 'SE' else 0
    bx = {'S': 31.5, 'SE': 27, 'N': 31.5, 'NE': 30.5}[view]
    ell(g, bx + (2 if view == 'SE' else 0), 12, 2.5, 2.2, 'B')          # bun peeks above crown (behind hair)
    if not back: bow(g, bx, 13, up=1 if view == 'SE' else 0)            # bow behind head
    for r, w in HAIR: cw(g, r, w, 'H')
    if not back:
        for r, w in FACE: cw(g, r, w, 'F', fx)
        for r in (22, 23):
            if view == 'S': put(g, r, 29, 30, 'e'); put(g, r, 33, 34, 'e')
            else: put(g, r, 31, 32, 'e'); put(g, r, 35, 36, 'e')
    else:
        bow(g, bx, 18, up=-1 if view == 'NE' else 0)                     # bow on the back of the head
        if view == 'NE':
            for r in range(24, 28): g[r, 38] = 'F'                       # cheek sliver
    cw(g, 28, 2, 'N', 1 if view == 'SE' else 0)
def body_front(g, view):
    asym = 1 if view in ('SE', 'NE') else 0
    for r in range(29, 34): cw(g, r, 8, 'D')                             # chest 8
    for r in range(34, 37): cw(g, r, 6, 'O')                             # obi 6 = waist pinch
    for r, w in [(37, 8), (38, 10), (39, 12), (40, 12), (41, 12)]: cw(g, r, w, 'D')   # A-line flare
    if asym:  # 3/4: hem swings 1 px further on the near (right) side
        for r in (39, 40, 41): g[r, 38] = 'D'; g[r, 26] = '.'
        for r in (39, 40, 41): g[r, 37] = 'D'
    for r in range(42, 48): put(g, r, 26, 30, 'L'); put(g, r, 33, 37, 'L')   # thigh 5, 2 px gap
    for r in range(48, 51): put(g, r, 27, 30, 'L'); put(g, r, 33, 36, 'L')   # calf 4
    for r in range(51, 55): put(g, r, 26, 29, 'L'); put(g, r, 34, 37, 'L')   # A-stance
    for r in range(55, 59): put(g, r, 26, 29, 'T'); put(g, r, 34, 37, 'T')   # boot shaft 4
    put(g, 59, 25, 29, 'T'); put(g, 59, 34, 38, 'T')
    for r in (60, 61):
        if view == 'SE': put(g, r, 25, 29, 'T'); put(g, r, 34, 39, 'T')
        else: put(g, r, 24, 29, 'T'); put(g, r, 34, 39, 'T')
    if asym:  # 3/4: far (left) thigh tucks 1 px toward the centre
        for r in range(42, 48): g[r, 26] = '.'; g[r, 31] = 'L'
def arms_front(g, view):
    far = 1 if view in ('SE', 'NE') else 0
    put(g, 29, 27, 27, 'A'); put(g, 29, 36, 36, 'A')                     # shoulder caps -> 10
    for r in (30, 31): put(g, r, 26, 27, 'A'); put(g, r, 36, 37, 'A')   # -> 12
    for r in range(32, 42):
        c = 'A' if r < 36 else 'h'
        put(g, r, 25 + far, 26, c); put(g, r, 37, 38, c)                # 1 px gap at chest, 2 px at obi
    put(g, 42, 25 + far, 26, 'h'); put(g, 42, 37, 38, 'h')              # fingertips just below the hem
def side():
    g = blank()
    ell(g, 27, 12, 2.5, 2.2, 'B')
    for r, w in HAIR: put(g, r, 39 - w if r >= 17 else 32 - w // 2 + 1, 38 if r >= 17 else 32 - w // 2 + w, 'H')
    for r, a, b in [(21, 33, 38), (22, 33, 38), (23, 33, 38), (24, 33, 38), (25, 33, 38), (26, 33, 37), (27, 34, 36)]: put(g, r, a, b, 'F')
    put(g, 22, 36, 36, 'e'); put(g, 23, 36, 36, 'e')
    ell(g, 25, 16, 3.2, 3.0, 'W'); ell(g, 26, 16, 1.4, 1.6, 'W')           # bow on the back of the head (side-on)
    put(g, 28, 31, 32, 'N')
    put(g, 29, 29, 34, 'D')
    for r in range(30, 34): put(g, r, 29, 35, 'D')
    for r in range(34, 37): put(g, r, 29, 34, 'O')
    for r, a, b in [(37, 28, 35), (38, 27, 36), (39, 25, 37), (40, 24, 37), (41, 24, 37)]: put(g, r, a, b, 'D')
    for r in range(42, 48): put(g, r, 29, 34, 'L')
    for r in range(48, 55): put(g, r, 30, 33, 'L')
    for r in range(49, 53): g[r, 29] = 'L'          # calf bulge behind
    for r in range(55, 60): put(g, r, 29, 33, 'T')
    put(g, 60, 29, 35, 'T'); put(g, 61, 29, 36, 'T')
    body = g.copy()
    for r in range(29, 36): put(g, r, 31, 32, 'A')
    for r in range(36, 43): put(g, r, 32, 33, 'h')
    return g, body
def front(view):
    g = blank(); head_front(g, view); body_front(g, view); body = g.copy(); arms_front(g, view); return g, body
def render(g, s=1, outline=True):
    a = np.zeros((64, 64, 4), np.uint8)
    for c, col in PAL.items(): a[g == c] = col + (255,)
    if outline:  # 1 px dark selout INSIDE the silhouette (refs' widths include their outline)
        m = g != '.'; p = np.pad(m, 1); edge = m & ~(p[:-2, 1:-1] & p[2:, 1:-1] & p[1:-1, :-2] & p[1:-1, 2:])
        a[edge, :3] = (a[edge, :3] * 0.3).astype(np.uint8)
    im = Image.fromarray(a); return im.resize((64 * s, 64 * s), Image.NEAREST) if s > 1 else im
if __name__ == '__main__':
    for v in ['S', 'SE', 'E', 'NE', 'N']:
        g, body = side() if v == 'E' else front(v)
        for name, m in [(v, g), (v + '_body', body)]: open(OUT + name + '.txt', 'w').write('\n'.join(''.join(r) for r in m) + '\n')
        render(g).save(OUT + v + '.png'); render(g, outline=False).save(OUT + v + '_flat.png')
    print('ok')
