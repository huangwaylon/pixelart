"""S7 r3 POLISH (Claude hand pixel pass). sprite/ -> polished/ ; every edit + reason in polwork/edits.json.
  .venv/bin/python tools/hybrid/s7pol/polish.py
"""
import sys, os, shutil, json, math
import numpy as np
ROOT = '/Users/waylonhuang/Documents/other/pixelart/swordswoman'
sys.path.insert(0, ROOT + '/tools/hybrid/s5r2pol')
import pk
R = ROOT + '/hybrid/S7_fxkit/r3'
SRC, DST, BASE = R + '/sprite', R + '/polished', R + '/base'
LOG = []
def note(name, what, why): LOG.append(dict(sprite=name, edit=what, reason=why))
def base(n): return pk.load(f'{BASE}/{n}.png')
def fxonly(a, b, x0, y0, x1, y1, chars='pPwtT'):
    """clear FX pixels (differ from the FX-free base, in chars) inside the box; base pixels restored"""
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            if pk.ch(a, x, y) != pk.ch(b, x, y) and pk.ch(a, x, y) in chars:
                a[y, x] = b[y, x]

def lonely(a, box, chars='pPw'):
    """drop FX pixels with no same-family 8-neighbour (orphans)"""
    x0, y0, x1, y1 = box
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            if pk.ch(a, x, y) in chars and not any(pk.ch(a, x + i, y + j) in chars for i in (-1, 0, 1) for j in (-1, 0, 1) if i or j):
                a[y, x] = 0

# ---------------------------------------------------------------- slash
def slash_k0(a, n):
    b = base(n)
    fxonly(a, b, 24, 56, 46, 68)
    # blade gleam at the coiled tip: 4-point glint (steel_2 core, pink_0 ends) = "the blade is about to go"
    tip = (30, 69)
    for y in range(60, 76):
        for x in range(22, 34):
            pass
    X, Y = 29, 66
    for k, c in ((0, 'w'), (1, 'w'), (2, 'w'), (3, 'p')):
        for dx, dy in ((k, 0), (-k, 0), (0, k), (0, -k)):
            pk.put(a, X + dx, Y + dy, c, 'behind')
    pk.put(a, X + 4, Y, 'p', 'behind'); pk.put(a, X - 4, Y, 'p', 'behind')
    for dx, dy in ((1, 1), (-1, -1), (1, -1), (-1, 1)): pk.put(a, X + dx, Y + dy, 'p', 'behind')
    note(n, 'removed the 2 scattered wind-up flick dashes; added a 9x7 blade glint (steel_2 core, pink_0 tips) above the drawn-back tip',
         'the flicks read as stray pink noise at 1x; a glint is the classic anticipation cue and keeps the no-smear rule for k0')

def slash_k1(a, n):
    # merge the 3 separate red limb-multiple dashes (x43-53 y76-81) into one tapered sleeve smear band
    for y in range(74, 90):
        for x in range(42, 56):
            if pk.ch(a, x, y) in 'RC' and pk.ch(a, x - 1, y) in 'pP.' and x < 54:
                a[y, x] = 0
    # tapered band: tail (44,76) 1 px -> arm end (55,82) 3 px; red_3 lit top, red_2 body
    for k in range(40):
        t = k / 39
        x = 44 + 11 * t; y = 76 + 6 * t; w = 1 + 1.2 * t
        for j in range(int(math.ceil(w))):
            pk.put(a, round(x), round(y + j), 'C' if j == 0 else 'R')
    note(n, 'replaced the 3 broken red limb dashes with one tapered sleeve smear (1->2 px, red_3 lit edge) along the arc',
         'stretched-limb smear must read as ONE dragged sleeve, not three red scratches on the pink')
    # stray red fragments inside the lower tail
    for (x, y) in ((50, 86), (50, 87), (51, 87), (52, 87), (53, 87)):
        if pk.ch(a, x, y) == 'R': pk.put(a, x, y, 'p')
    note(n, 'recoloured 5 floating red_2 px inside the pink tail (x50-53 y86-87) to pink_0', 'orphan red specks in the smear body')

    # thicken the lead half of the crescent by 1 px on its inner edge (angles 31-80 deg of c(64,53))
    CX, CY = 64, 53; add = []
    for y in range(50, 100):
        for x in range(60, 104):
            if a[y, x, 3]: continue
            d = math.hypot(x - CX, y - CY); ang = math.degrees(math.atan2(y - CY, x - CX))
            if not (33 <= ang <= 80) or d < 20: continue
            ox, oy = x + (x - CX) / d * 1.2, y + (y - CY) / d * 1.2
            if pk.ch(a, round(ox), round(oy)) == 'p': add.append((x, y))
    for x, y in add: pk.put(a, x, y, 'p')
    note(n, f'crescent lead half thickened 1 px on the inner edge ({len(add)} px pink_0)', 'bolder lead mass at the fastest point of the swing; keeps the smear >= 300 px after the sleeve fix')

def star(a, X, Y, arm=9, diag=4):
    for k in range(-arm, arm + 1):
        c = 'w' if abs(k) <= arm - 3 else 'p'
        pk.put(a, X + k, Y, c); pk.put(a, X, Y + k, c)
    for k in range(1, diag + 1):
        c = 'w' if k <= 2 else 'p'
        for sx, sy in ((1, 1), (1, -1), (-1, -1), (-1, 1)): pk.put(a, X + sx * k, Y + sy * k, c, 'behind')
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1): pk.put(a, X + dx, Y + dy, 'w')

def slash_k2(a, n):
    b = base(n)
    X, Y = 93, 66
    fxonly(a, b, 84, 46, 112, 76, 'pPwT')
    # keep the blade sliver lower-left of the tip (part of the arc lead): only cleared above/right of the tip
    star(a, X, Y, arm=10, diag=5)
    # heavy-hit burst: 5 radial strokes r 13..17 (steel_2 head -> pink_0 tail), skipping her face side
    for ang in (-112, -67, -22, 23, 68):
        for r in range(13, 18):
            pk.put(a, round(X + r * math.cos(math.radians(ang))), round(Y + r * math.sin(math.radians(ang))), 'w' if r <= 14 else 'p', 'behind')
    note(n, 'rebuilt the impact: 8-point star (cardinal arms 10, diagonals 5, 3x3 steel_2 core) + 5 radial burst strokes r13-17 at the tip (93,66)',
         'heavy-hit tier: old plus (arm 7) + a detached hook and 3 floating 2x2 blocks read as noise and too small at 1x')

def slash_k3(a, n):
    b = base(n)
    fxonly(a, b, 86, 70, 100, 96, 'pPw')
    # tapered follow-through crescent around the hand (78,88): r 19.5, tail -40 deg -> lead 24 deg (just behind the blade)
    CX, CY, CR = 78, 88, 19.5
    tmp = np.zeros_like(a)
    pk.crescent(tmp, CX, CY, CR, -42, 24, wmax=5, w0=1, pw=1.3, rim=(0.55, 1.5, 0.85, 2.5), inner_echo=False)
    for y, x in zip(*np.nonzero(tmp[:, :, 3])):
        ang = math.degrees(math.atan2(y - CY, x - CX)); sp = (ang + 42) / 66
        if sp < 0.3 and (x + y) % 2: continue          # dissolving tail
        if a[y, x, 3] == 0: a[y, x] = tmp[y, x]
    lonely(a, (80, 60, 104, 100))
    note(n, 'replaced the uniform 2 px vertical sliver with a tapered follow-through crescent c(78,88) r19.5 -42->24 deg (1->5 px, steel_2 lead rim, dissolving tail)',
         'the constant-width line read as a THIRD ribbon; a tapering, decaying arc reads as the blade energy dying after the hit')

# ---------------------------------------------------------------- jump
def jump_apex(a, n):
    b = base(n)
    fxonly(a, b, 40, 94, 80, 110)
    for (x, y0, L) in ((53, 96, 4), (57, 95, 7), (61, 96, 5)):
        for k in range(L):
            pk.put(a, x, y0 + k, 'w' if k == 0 else 'p', 'behind')
    note(n, 'redrew the 3 rise streaks as clean 1 px lines 4/7/5 px, ending 3 px above the baseline (steel_2 head, pink_0 tail) under the soles', 'old streaks were 2-6 px broken bits that read as pink noise')

# ---------------------------------------------------------------- bonus dash
def dash(a, n):
    b = base(n)
    own = np.load(f'{BASE}/{n}_owner.npy')
    g = b.copy()
    sil = (b[:, :, 3] > 0)
    steel = np.zeros_like(sil); rib = np.isin(own, ['ribbonN', 'ribbonF'])
    for y, x in zip(*np.nonzero(sil)):
        if pk.ch(b, x, y) in 'tTw': steel[y, x] = True
    body = sil & ~steel & ~rib
    H, W = sil.shape
    for (dx, dy, step, tone, keep) in ((-9, -1, 2, 'p', 1.0), (-18, -2, 4, 'p', 0.6)):
        m = np.zeros_like(body)
        ys, xs = np.nonzero(body)
        for y, x in zip(ys, xs):
            yy, xx = y + dy, x + dx
            if 0 <= yy < H and 0 <= xx < W: m[yy, xx] = True
        x_lo = xs.min() + dx; x_hi = xs.max() + dx
        for y in range(H):
            if y % step: continue
            row = np.nonzero(m[y])[0]
            if not len(row): continue
            for x in row:
                frac = (x - x_lo) / max(1, x_hi - x_lo)
                if frac < 1 - keep: continue
                if g[y, x, 3] == 0:
                    pk.put(g, x, y, tone)
    # ground streak
    for k in range(12): pk.put(g, 40 - k, 102, 'w' if k < 3 else 'p', 'behind')
    a[:] = g
    note(n, 'afterimage rebuilt as INTERLACED scanline ghosts (near -9 px every 2nd row, far -18 px every 4th row, both pink_0, far trailing 40 % dropped) + ground streak',
         'third option for the unresolved dash: solid read as a slab, contour as wireframe; horizontal scanlines carry speed direction and her silhouette without a solid mass')

FIX = {'slash_SE_k0': slash_k0, 'slash_SE_k1': slash_k1, 'slash_SE_k2': slash_k2, 'slash_SE_k3': slash_k3,
       'jump_E_apex': jump_apex, 'bonus/dash_SE_f1': dash}

def run():
    if os.path.exists(DST): shutil.rmtree(DST)
    shutil.copytree(SRC, DST, ignore=shutil.ignore_patterns('*_4x.png'))
    for n, fn in FIX.items():
        p = os.path.join(DST, n + '.png'); a = pk.load(p); fn(a, n.split('/')[-1]); pk.save(a, p)
    from PIL import Image
    for d in (DST, DST + '/bonus'):
        for f in os.listdir(d):
            if f.endswith('.png') and not f.endswith(('_4x.png', '_hires.png')):
                Image.open(os.path.join(d, f)).resize((512, 512), Image.NEAREST).save(os.path.join(d, f[:-4] + '_4x.png'))
    os.makedirs(R + '/polwork', exist_ok=True)
    json.dump(LOG, open(R + '/polwork/edits.json', 'w'), indent=1)
    print(len(LOG), 'edits')

if __name__ == '__main__': run()
