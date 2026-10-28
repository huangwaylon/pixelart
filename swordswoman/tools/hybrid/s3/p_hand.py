"""All hand pixel edits (Claude), replayable: run after compose -> p_retone -> p_slash k1 -> p_auto."""
import sys, subprocess; sys.path.insert(0, 'tools/hybrid/s3')
import numpy as np
from PIL import Image, ImageDraw
from pol import *
import p_squash, json
R = 'hybrid/S3_editchain/r1'; A = f'{R}/wip/auto'; P = f'{R}/wip/pol'
BODYC = 'rvRClLsmSdhH'
def clean_k(a, x0, y0, x1, y1, pink=True):
    c = chars(a)
    for y in range(y0, y1):
        for x in range(x0, x1):
            if pink and c[y, x] in 'pP': a[y, x] = 0
    c = chars(a)
    for y in range(y0, y1):
        for x in range(x0, x1):
            if c[y, x] == 'K' and not any(v in BODYC for v in c[y-1:y+2, x-1:x+2].ravel()): a[y, x] = 0
# ---- slash k0: blade passes behind the bun (connect the floating segment)
draw(f'{A}/slash_SE_k0.png', f'{P}/slash_SE_k0_s.png', ["line 44,51 50,53 w", "line 44,52 50,54 t"])
# ---- slash k1: full-motion blade-arc crescent (tail behind on the coil side, lead over the body at the blade)
a = load(f'{A}/slash_SE_k1.png'); c = chars(a)
for y in range(78, 96):
    for x in range(86, 100):
        if c[y, x] in 'pP': a[y, x] = 0
a[60:76, 25:36] = 0
save(a, '/tmp/k1a.png')
draw('/tmp/k1a.png', f'{P}/slash_SE_k1_s.png', ["smear 75,80 41,20 195 140 4 tones=P,p taper=lead grow=in",
                                                 "smear 75,80 41,20 195 44 6 tones=w,P,p taper=lead grow=in over"])
a = load(f'{P}/slash_SE_k1_s.png')
m = Image.new('L', (128, 128), 0); ImageDraw.Draw(m).polygon([(99, 86), (103, 95), (92, 99), (84, 99), (94, 94)], fill=255)
m = np.array(m) > 0; c = chars(a)
for y, x in zip(*np.nonzero(m)):
    if c[y, x] in '.K': put(a, x, y, 'P')
c = chars(a)
for y, x in zip(*np.nonzero(m)):
    if c[y, x] == 'P' and (c[y-1, x] == '.' or c[y, x-1] == '.'): put(a, x, y, 'p')
save(a, f'{P}/slash_SE_k1_s2.png')
# ---- slash k2: blade re-angled to the end of the arc, thin trailing sliver, steel_2 impact star
a = load(f'{A}/slash_SE_k2.png'); c = chars(a)
for y in range(76, 100):
    for x in range(92, 108):
        if c[y, x] in 'tTwK': a[y, x] = 0
clean_k(a, 40, 93, 102, 102)
save(a, '/tmp/k2a.png')
draw('/tmp/k2a.png', f'{P}/slash_SE_k2_s.png', ["smear 75,80 41,20 62 6 3 tones=P,p taper=lead grow=in",
    "line 93,75 111,81 w", "line 93,76 111,82 t", "line 92,74 92,77 T",
    "stamp 110,75 P.....P/...w.../...w.../.wwwww./...w.../...w.../P.....P", "stamp 116,78 ..p/.../..."])
# ---- slash k3: follow-through blade up-right behind the raised arms + pink_0 wisps at the arc tail
a = load(f'{A}/slash_SE_k3.png'); c = chars(a)
for y in range(30, 41):
    for x in range(46, 65):
        if c[y, x] in 'tTwK': a[y, x] = 0
save(a, '/tmp/k3a.png')
draw('/tmp/k3a.png', f'{P}/slash_SE_k3_s.png', ["line 86,47 100,29 w", "line 87,47 101,29 t", "line 85,48 85,50 T",
                                                 "line 102,33 104,38 p", "line 100,26 103,25 p"])
# ---- jump land: volume-paired squash (x1.15, y0.82), head sinks 2 px, dust ticks both sides
p_squash.squash(f'{A}/jump_E_crouch.png', f'{R}/sprite_px/jump_E_crouch_meta.json', 'E', 1.12, 0.88, f'{P}/jump_E_land_q.png', head_drop=2)
draw(f'{P}/jump_E_land_q.png', f'{P}/jump_E_land_s.png', ["cluster 50,102 T X.X/.XX", "cluster 47,100 S ..X/X..",
                                                          "cluster 87,102 T XX./X.X", "cluster 90,99 S X../..X"])
# ---- slash k0 anticipation: coil lower and wider (volume-paired squash, head sinks 1 px)
p_squash.squash(f'{P}/slash_SE_k0_s.png', f'{R}/sprite_px/slash_SE_k0_meta.json', 'SE', 1.05, 0.92, f'{P}/slash_SE_k0_s.png', head_drop=1)
# ---- walk: one katana cel for all four keys (same 2 px blade, same length), swinging 2 frames behind the arm
import math
def reblade(src, out, ang, L=19, box=(60, 70, 128, 128)):
    a = load(src); c = chars(a)
    x0, y0, x1, y1 = box
    pts = [(x, y) for y in range(y0, y1) for x in range(x0, x1) if c[y, x] in 'tTw']
    gx, gy = min(pts, key=lambda p: p[0] + p[1])            # blade root = the steel pixel nearest the hand
    for x, y in pts: a[y, x] = 0
    clean_k(a, x0, y0, x1 - 1, y1 - 1, pink=False)
    save(a, out)
    ex, ey = gx + L * math.cos(math.radians(ang)), gy + L * math.sin(math.radians(ang))
    draw(out, out, [f"line {gx},{gy} {round(ex)},{round(ey)} w", f"line {gx+1},{gy} {round(ex)+1},{round(ey)} t"])
for k, ang in zip(range(4), (40, 42, 46, 43)):
    reblade(f'{A}/walk_SE_k{k}.png', f'{P}/walk_SE_k{k}_s.png', ang)
# ---- slash k2/k3: delete the floating red streak island left of the bun (Gemini hair-whip artefact)
for k in ('k2', 'k3'):
    a = load(f'{P}/slash_SE_{k}_s.png'); c = chars(a)
    Ms = stamp_mask(f'{R}/sprite_px/slash_SE_{k}_meta.json', 'SE')
    for y in range(46, 67):
        for x in range(36, 59):
            if c[y, x] in 'rvRCK' and not Ms[y, x]: a[y, x] = 0
    save(a, f'{P}/slash_SE_{k}_s.png')
# ---- secondary motion: the locked bow cel lags 1 px against the body's motion (bow loops lag 2 frames)
LAG = {'walk_SE_k1': (0, -1), 'walk_SE_k3': (0, 1), 'slash_SE_k1': (-1, 0), 'slash_SE_k2': (-1, 0), 'slash_SE_k3': (1, 0),
       'jump_E_crouch': (0, -1), 'jump_E_land': (0, -1)}
SRCF = {'walk_SE_k1': f'{P}/walk_SE_k1_s.png', 'walk_SE_k3': f'{P}/walk_SE_k3_s.png', 'slash_SE_k1': f'{P}/slash_SE_k1_s2.png',
        'slash_SE_k2': f'{P}/slash_SE_k2_s.png', 'slash_SE_k3': f'{P}/slash_SE_k3_s.png', 'jump_E_crouch': f'{A}/jump_E_crouch.png',
        'jump_E_land': f'{P}/jump_E_land_s.png'}
for n, (dx, dy) in LAG.items():
    a = load(SRCF[n]); d = 'E' if n.startswith('jump') else 'SE'
    meta = f'{R}/sprite_px/{"jump_E_crouch" if n == "jump_E_land" else n}_meta.json'
    save(bow_lag(a, meta, d, dx, dy), f'{P}/{n}_bow.png')
# ---- slash k0: one straight katana: the hilt below the hands points down-right, so the blade runs up-left behind the head
a = load(f'{P}/slash_SE_k0_s.png'); c = chars(a)
for y in range(36, 60):
    for x in range(25, 52):
        if c[y, x] in 'tTw': a[y, x] = 0
a[69:72, 80:84] = 0
save(a, f'{P}/slash_SE_k0_s.png')
draw(f'{P}/slash_SE_k0_s.png', f'{P}/slash_SE_k0_s.png', ["line 50,55 35,45 w", "line 50,56 35,46 t", "line 49,55 50,55 T"])
# ---- slash k3: remove the old down-pointing hilt stub and the doubled blade piece
a = load(f'{P}/slash_SE_k3_bow.png'); c = chars(a)
for y in range(50, 59):
    for x in range(87, 99):
        if x >= 88 and abs((y - 52.5) - (x - 87) * 0.75) <= 1.6 and c[y, x] in "Kvrlh": a[y, x] = 0
for y in range(44, 51):
    for x in range(83, 86):
        if c[y, x] in 'tT': a[y, x] = 0
clean_k(a, 88, 50, 99, 61, pink=False)
save(a, f'{P}/slash_SE_k3_bow.png')
# ---- combat expression on attack frames (ANIM_DIRECTION 2.5 'focused'): inner-corner brow-down slant on the SE face
for k in range(4):
    f = f'{P}/slash_SE_k{k}_bow.png' if k else f'{P}/slash_SE_k0_s.png'
    a = load(f); m = json.load(open(f'{R}/sprite_px/slash_SE_k{k}_meta.json'))['s3']
    hx, hy = find_head(a, 'SE', (m['stamp_left'], m['stamp_top']))
    for x, y in ((11, 23), (12, 23), (18, 23), (19, 23), (10, 22), (20, 22)):
        put(a, hx + x, hy + y, 'K' if (x, y) not in ((10, 22), (20, 22)) else ('h'))
    save(a, f'{P}/slash_SE_k{k}_face.png')
print('hand ok')
