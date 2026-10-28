"""S5 r3 FX pass (Claude exact pixels, FINAL cell coords): base/<name>.png -> fx/<name>.png. Every op is logged in
hybrid/S5_pixelnative/r3/work/edits_fx.json.
Recipes:
  crescent2  two-circle blade-arc crescent: outer edge = rasterized blade-tip circle (C, R); inner edge = a second
             rasterized circle (C - d*u(lead), R - t0) -> thickness tail t0-d*cos(span) -> lead t0+d, monotone, and
             BOTH edges are plain circles so the stair runs progress evenly (3-2-1, no kinks, no stripe bands).
             tones: steel_2 rim (1 px over the leading 75 %, 2 px over the leading 30 %), pink_0 body, 1 px pink_0
             inner echo arc (double crescent) over the leading 55 %. front rule: only the outer `over_rows` rows
             paint over the body below `ymin`; the rest stays behind. cut mask = fist + hilt (+1 px) never painted.
"""
import sys, os, json, math
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import patch as P
ROOT = '/Users/waylonhuang/Documents/other/pixelart/swordswoman'
R3 = f'{ROOT}/hybrid/S5_pixelnative/r3'
LOG = []
def note(n, what, why): LOG.append(dict(sprite=n, stage='fx', edit=what, reason=why))

def angf(ang, a0, a1):
    span = a1 - a0
    for k in (-360, 0, 360):
        f = (ang + k - a0) / span
        if 0 <= f <= 1: return f
    return None

def dil(m, k=1):
    o = m.copy()
    for _ in range(k):
        q = o.copy()
        q[1:] |= o[:-1]; q[:-1] |= o[1:]; q[:, 1:] |= o[:, :-1]; q[:, :-1] |= o[:, 1:]
        o = q
    return o

def crescent2(a, C, R, a0, a1, lead=10.0, tail=1.5, rim=(0.25, 0.70), over_rows=2, ymin=200, cut=None, guard=None,
              echo=True, echo_frac=0.55, body='p', rimc='w', mode='behind'):
    cx, cy = C
    span = abs(a1 - a0)
    # thickness T(D) = t0 + d*cos(D), D = angle from the lead; T(0)=lead, T(span)=tail
    cs = math.cos(math.radians(span))
    d = (lead - tail) / (1 - cs); t0 = lead - d
    ul = (math.cos(math.radians(a1)), math.sin(math.radians(a1)))
    ci = (cx - d * ul[0], cy - d * ul[1]); Ri = R - t0
    pts = {}
    for y in range(128):
        for x in range(128):
            ro = math.hypot(x - cx, y - cy)
            if ro > R + 0.5: continue
            ang = math.degrees(math.atan2(y - cy, x - cx))
            f = angf(ang, a0, a1)
            if f is None: continue
            ri = math.hypot(x - ci[0], y - ci[1])
            if ri <= Ri + 0.5: 
                if echo and f >= 1 - echo_frac and f < 0.93 and abs(ri - (Ri - 1.5)) < 0.5: pts[(x, y)] = (body, 99)
                continue
            dep = R + 0.5 - ro
            rw = 2 if f >= 1 - rim[0] else (1 if f >= 1 - rim[1] else 0)
            c = rimc if dep < rw else body
            pts[(x, y)] = (c, dep)
    n = 0
    for (x, y), (c, dep) in pts.items():
        if cut is not None and cut[y, x]: continue
        if guard is not None and guard[y, x]: continue
        m = 'over' if (y >= ymin and dep < over_rows) else mode
        if m == 'behind' and a[y, x, 3] > 0: continue
        P.put(a, x, y, c); n += 1
    return n

def rotate_pts(pts, C, deg):
    t = math.radians(deg); c, s = math.cos(t), math.sin(t)
    return [(round(C[0] + (x - C[0]) * c - (y - C[1]) * s), round(C[1] + (x - C[0]) * s + (y - C[1]) * c)) for x, y in pts]

def spec_mask(text):
    b = np.zeros((128, 128, 4), np.uint8); P.spec(b, text); return b[..., 3] > 0

def clear_orphans(a, tones='wpP'):
    """FX pixels with no same-tone 8-neighbour are removed (cluster >= 2)"""
    n = 0
    for y in range(1, 127):
        for x in range(1, 127):
            c = P.ch(a, x, y)
            if c not in tones: continue
            if not any(P.ch(a, x + i, y + j) == c for i in (-1, 0, 1) for j in (-1, 0, 1) if i or j):
                a[y, x] = 0 if True else a[y, x]; n += 1
    return n

C, RR = (65, 54), 39
def guard_of(n):
    o = np.load(f'{R3}/base/{n}_owner.npy', allow_pickle=True)
    return dil(o == 'HEAD', 1)

def k1(a, n):
    g = guard_of(n)
    # cut: fists + hilt + guard at the lead (fist box from the anims spec, + 1 px)
    cut = np.zeros((128, 128), bool)
    for y in range(81, 90):
        for x in range(70, 82):
            if P.ch(a, x, y) in 'sSmdRTK': cut[y, x] = True
    cut = dil(cut, 1)
    # multiple-limb sleeve smear: the swept sleeves as ONE elongated red streak riding inside the crescent (radius
    # R-13 .. R-9), from the coil side (150 deg, 1 px) to the arm (100 deg, 4 px): red_2 core, red_1 underside,
    # behind the body only (it reads where it leaves the silhouette)
    for y in range(128):
        for x in range(128):
            ro = math.hypot(x - C[0], y - C[1]); ang = math.degrees(math.atan2(y - C[1], x - C[0]))
            f = angf(ang, 150, 100)
            if f is None: continue
            w = 1 + 3.2 * f; rc = RR - 12
            if abs(ro - rc) <= w / 2 and a[y, x, 3] == 0 and not g[y, x]:
                P.put(a, x, y, 'R' if ro < rc + w / 2 - 1 else 'r')
    note(n, 'multiple-limb sleeve smear: red streak r=R-12 from 150 deg (1 px) to 100 deg (4 px), red_2 + red_1 underside, behind', 'arms/sleeves read as one elongated fast swing (ANIM 4.2)')
    # hand echo: 2x2 skin_1, 5 px back along the arc from the fist
    for x, y in rotate_pts([(73, 84), (74, 84), (73, 85), (74, 85)], C, 9):
        if a[y, x, 3] == 0: P.put(a, x, y, 's')
    note(n, 'hand echo 2x2 skin_1 at +9 deg behind the fist', 'ANIM 4.2 hand echo')
    nn = crescent2(a, C, RR, 160, 28, lead=10, tail=1.5, over_rows=2, ymin=84, cut=cut, guard=g)
    note(n, f'blade-arc crescent2 C{C} R{RR} 160->28 deg, 1.5 -> 10 px, steel_2 rim + pink_0 body + inner echo; {nn} px', 'the smear: full coil->impact sweep, front rows over the legs, fist + hilt cut out at the lead')

sys.path.insert(0, f'{ROOT}/tools/hybrid/fx')
import kit as FK          # S7 shared FX kit (char grids)

def k0(a, n):
    # anticipation glint on the drawn-back blade tip (steel_2 4-arm cross, 5 px, over)
    tip = blade_tip(a, side='left')
    for dx, dy in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)): P.put(a, tip[0] + dx, tip[1] + dy, 'w')
    note(n, f'blade-tip glint cross at {tip}', 'coil reads as loaded (eye goes to the blade before the swing)')

def blade_tip(a, side='right'):
    ys, xs = np.nonzero(np.all(a[..., :3] == np.array(P.RGB['w']), -1) & (a[..., 3] > 0))
    i = np.argmin(xs) if side == 'left' else np.argmax(xs)
    return int(xs[i]), int(ys[i])

def k2(a, n):
    g0 = guard_of(n)
    g = FK.to_grid(a)
    cut = np.zeros((128, 128), bool)
    for y in range(72, 82):
        for x in range(76, 88):
            if P.ch(a, x, y) in 'sSmdRK': cut[y, x] = True
    v = FK.sliver(g, C, RR, 160, 28, keep=0.35, thick=2, guard=g0, cut=cut)
    note(n, f'impact sliver: leading 35 % of the k1 arc, 1 -> 2 px ({len(v)} px)', 'the arc stabilises behind the crisp blade (ANIM 4.1)')
    tip = blade_tip(a, 'right')
    v = FK.impact_star(g, (tip[0] + 1, tip[1]), stage=0, star='plus', strokes=4, stroke_r=9, stroke_len=5, shock=True,
                       shock_r=15, shock_span=60, rot=-60, skip=((115, 245),), guard=g0)
    note(n, f'impact star at the blade tip {tip}: 3x3 core + cardinal arms, 4 bold 2 px tapered strokes, ONE 2 px shock arc (rot -60), her side kept clear ({len(v)} px)', 'hit-stop impact reads at 1x; replaces the r2 broken burst dashes')
    a[:] = FK.to_rgba(g)

def k3(a, n):
    g0 = guard_of(n)
    cut = np.zeros((128, 128), bool)
    for y in range(80, 92):
        for x in range(72, 84):
            if P.ch(a, x, y) in 'sSmdRK': cut[y, x] = True
    cut = dil(cut, 1)
    tmp = a.copy(); tmp[..., 3] = 0
    crescent2(tmp, (74, 78), 27, -15, 37, lead=3.2, tail=1.0, rim=(0.3, 0.6), echo=False, cut=cut, guard=g0)
    # fade: the trailing 45 % breaks into 2 dashes (gaps 2 px wide), every piece >= 3 px
    for y, x in zip(*np.nonzero(tmp[..., 3])):
        ang = math.degrees(math.atan2(y - 78, x - 74)); f = angf(ang, -15, 37)
        if f is not None and (0.10 < f < 0.17 or 0.30 < f < 0.36): tmp[y, x, 3] = 0
        elif a[y, x, 3] == 0: a[y, x] = tmp[y, x]
    note(n, 'fading recovery crescent: centre (74,78) r27, -15 -> 37 deg (1 -> 3 px, steel_2 rim on the lead), tail broken into dashes', 'the blade recovers on a LOWER arc and the smear decays')

def run_f1(a, n):
    g0 = guard_of(n)
    g = FK.to_grid(a); src = g.copy()
    leg = FK.limb_mask(src, region=(40, 92, 58, 103), chars='smSdK')
    v = FK.limb_multiples(g, src, leg, path=[(-4, -2), (-9, -4)], n=2, mode='multiples', guard=g0)
    note(n, f'trailing-leg multiples: 2 hard flat copies at (-3,-1) / (-7,-3) along the travel, skin then fading tone ({len(v)} px)', 'run flight smear: the swinging leg reads fast (ANIM 4.3)')
    hem = FK.limb_mask(src, region=(36, 90, 60, 100), chars='vrRC')
    hem &= ~np.roll(FK.limb_mask(src, chars='vrRCK'), 3, 0)          # only the bottom 3 hem rows
    v = FK.limb_multiples(g, src, hem, path=[(-5, -2)], n=1, mode='stretch', erode_tail=1, guard=g0)
    note(n, f'hem drag: bottom hem rows swept 5 px back along the travel into one tapered red shape ({len(v)} px)', 'cloth drags behind the run')
    v = FK.speed_bands(g, (-2, -1), n=2, lengths=(7, 5), origins=[(47, 78), (44, 87)], guard=g0)
    note(n, f'2 rimmed motion bands behind the shoulder and the hem ({len(v)} px)', 'ANIM 4.3 run motion lines, once per step')
    a[:] = FK.to_rgba(g)

def dash_f1(a, n):
    g0 = guard_of(n)
    g = FK.to_grid(a); src = g.copy()
    sil = src != '.'
    sil &= ~np.isin(src, list('tTw'))                    # the blade does not ghost
    own = np.load(f'{R3}/base/{n}_owner.npy', allow_pickle=True)
    v = FK.afterimage(g, sil, offsets=((-12, -4), (-23, -8)), tone='p', style='solid', smooth=1, body_gap=1, gap=2,
                      far_mask=(own == 'HEAD'), guard=g0)
    note(n, f'2 hard-edged afterimage multiples of the dash pose at (-8,-2) / (-16,-4) along the SE travel, solid flat style, 1 px clear ({len(v)} px)', 'dash travel smear (ANIM 4.3), crisp at 1x')
    v = FK.speed_bands(g, (-2, -1), n=3, lengths=(14, 10, 12), origins='auto', body=sil, gap=3, guard=g0)
    note(n, f'3 rimmed speed bands from the trailing edge ({len(v)} px)', 'travel speed')
    a[:] = FK.to_rgba(g)

FIX = {'run_SE_f1': run_f1, 'dash_SE_f1': dash_f1, 'slash_SE_k0': k0, 'slash_SE_k1': k1, 'slash_SE_k2': k2, 'slash_SE_k3': k3}
if __name__ == '__main__':
    os.makedirs(f'{R3}/fx', exist_ok=True); os.makedirs(f'{R3}/work', exist_ok=True)
    only = sys.argv[1:]
    for f in sorted(os.listdir(f'{R3}/base')):
        if not f.endswith('.png'): continue
        n = f[:-4]
        if only and n not in only: continue
        a = P.load(f'{R3}/base/{f}')
        if n in FIX: FIX[n](a, n)
        P.save(a, f'{R3}/fx/{f}')
    json.dump(LOG, open(f'{R3}/work/edits_fx.json', 'w'), indent=1)
    print(len(LOG), 'fx edits')
