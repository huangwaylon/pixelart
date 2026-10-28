"""writes slash_SE_k{0..3}.txt (hand-built keys on the guide's head path; the turn_SE torso cel leans by shearing).
Per key: torso lean, skirt cel, legs, arms + bell cuff, two-hand grip, katana (hand -> tip), smear / spark / wisps,
2 px ribbons and the flying sleeve (secondary motion: trail against velocity, freeze on the hit-stop, overshoot after)."""
D = '/Users/waylonhuang/Documents/other/pixelart/swordswoman/archive/v1/tools/hybrid/s1/bodies/'
SK_BACK = """________________KRRRRRRRRRRRRRRK____
____________KKKKRdRRRRRRRRRRRRRRK___
_________KKKRRRRRRddRRRRRRRRRRRRRK__
______KKKRRRRRRRRKddKRRRRRRRRRRRRRK_
___KKKRRRRRRRRRRRKdKRRRRRRRRRRRRRRK_
__KvrrrrRRRRRRRKK_KvrrrrrrrrrrrRRRK_
____KKvvvvvvvKK____KKvvvvvvvvvKKrK__
______KKKKKKK_______KKKKKKKKKKKKK___"""
SK_FWD = """______KRRRRRRRRRRRRRRRK______
_____KdRRRRRRRRRRRRRRRRK_____
_____KddRRRRRRRRRRRRRRRRK____
____KRddKRRRRRRRRRRRRRRRRK___
____KRRdKRRRRRRRRRRRRRRRRRK__
___KRRRKKRRRRRRRRRRRRRRRRRRK_
___KvrrK.KvrrrrrrrrrrrrrrRRRK
____KKK...KKvvvvKKvvvvvvKrRK_
________________________KrK__
_________________________KK__"""
CUFF = "KKK__/KRRK_/KRRRK/KvvvK/_KKK_"
FISTS = ['_KKKK_', 'KssssK', 'KmsssK', '_KKKK_']
SLEEVE_BACK = "________KKKKK/_____KKKRRRRK/__KKKRRRRRRrK/_KRRRRRRRrrK_/KRRRRRrrrrK__/_KvvvvvvKK___/__KKKKKK_____"
SLEEVE_FWD = "KKKKK________/KRRRRKKK_____/KrRRRRRRKKK__/_KrrRRRRRRRK_/__KrrrrRRRRRK/___KKvvvvvvK_/_____KKKKKK__"


def rib(p0, c, p1, behind=True):
    """2 px ribbon: lit pink_1 curve + pink_0 underside 1 px below"""
    op = 'opb' if behind else 'op'
    (x0, y0), (cx, cy), (x1, y1) = p0, c, p1
    return [f'{op}: curve {x0},{y0 + 1} {cx},{cy + 1} {x1},{y1 + 1} p', f'{op}: curve {x0},{y0} {cx},{cy} {x1},{y1} P']


K = {
 0: dict(note='ANTICIPATION (coil, 220 ms hold): head on the guide (62,70) -> stamp 54,48, torso leans BACK 2 px over the hips, '
              'two-hand grip at her right shoulder, blade drawn back up-left past the head, weight on the back leg, front knee bent; '
              'skirt tail, ribbons, sleeve and bow pulled the other way (right)',
         dx=2, dy=4, lean=-4, wshift=2, stamp=(54, 50), bow=(1, -1), expr='frown', skirt=(SK_FWD, 54, 92),
         legs=[('s', [(59, 98), (54, 101), (51, 103)]), ('d', [(50, 103), (50, 104)]), ('s', [(70, 98), (75, 100), (74, 103)]), ('d', [(74, 103), (76, 104)])],
         arm=[(69, 86), (61, 88)], cuff=(53, 88, "_KRRK/KRRRK/KvvvK/_KKK_"), fists=(54, 85), sword=((56, 87), (32, 58)),
         sleeve=(SLEEVE_FWD, 70, 86),
         ribs=[((66, 84), (75, 81), (82, 86)), ((82, 86), (86, 89), (89, 86)), ((64, 85), (71, 90), (79, 93))],
         fx=[]),
 1: dict(note='SMEAR (50 ms): lunge, head on the guide (67,72) -> stamp 59,50, torso leans FORWARD 2 px; blade-arc smear along the '
              'tip path from the k0 tip (up-left, behind) round the front and under her to the blade (steel_2 core, pink_1 -> pink_0 '
              'edge, 7 px at the lead, tapering to the tail) + 2 pink_0 echoes of the arms/cuff along the arc (multiple-limb smear); '
              'skirt, tail, sleeve and ribbons stretched flat behind, bow lags up-left, speed lines',
         dx=-2, dy=4, lean=5, wshift=-3, stamp=(59, 50), bow=(-1, -1), expr='frown', skirt=(SK_BACK, 44, 92),
         legs=[('s', [(63, 98), (58, 101), (55, 103)]), ('d', [(54, 103), (54, 104)]), ('s', [(73, 99), (76, 101), (77, 103)]), ('d', [(77, 103), (79, 104)])],
         arm=[(63, 86), (70, 89)], cuff=(67, 88, CUFF), fists=(71, 88), sword=((75, 90), (99, 97)),
         sleeve=(SLEEVE_BACK, 49, 84),
         ribs=[((62, 83), (52, 80), (40, 84)), ((40, 84), (35, 86), (30, 84)), ((63, 86), (53, 88), (44, 93))],
         fx=['op: echo 67,87 76,92 -10,-6 2 tone=p', 'op: smear 66,92 34,15 200 12 7 tones=w,P,p taper=lead',
             'op: smear 66,92 34,15 238 200 3 tones=P,p taper=tail', 'opb: speed 50,78 -1,0 3 7 3 p']),
 2: dict(note='IMPACT (hit-stop, 160 ms): deepest lunge (guide head 70,74 -> stamp 62,52), torso leans forward 4 px, blade level at '
              'full reach (guide tip 106,86), 1-frame steel_2 spark star on the hit point, thin tail of the crescent behind the blade; '
              'HELD frame: ribbons, sleeve and bow frozen in their k1 trail (no secondary motion)',
         dx=-1, dy=6, lean=7, wshift=-3, stamp=(62, 52), bow=(-1, -1), expr='frown', skirt=(SK_BACK, 45, 94),
         legs=[('s', [(66, 99), (60, 102), (56, 103)]), ('d', [(55, 103), (55, 104)]), ('s', [(77, 100), (79, 102), (80, 103)]), ('d', [(80, 103), (82, 104)])],
         arm=[(66, 88), (74, 91)], cuff=(70, 90, CUFF), fists=(74, 89), sword=((78, 91), (107, 87)),
         sleeve=(SLEEVE_BACK, 52, 86),
         ribs=[((65, 85), (55, 82), (43, 86)), ((43, 86), (38, 88), (33, 86)), ((66, 88), (56, 90), (47, 95))],
         fx=['op: smear 70,93 37,14 62 8 3 tones=P,p taper=tail', 'op: smear 96,87 12,6 120 20 3 tones=w,P taper=lead',
             'op: cluster 104,82 w ___X___/___X___/__XXX__/XXXXXXX/__XXX__/___X___/___X___', 'op: cluster 104,82 T _______/_X___X_/_______/_______/_______/_X___X_/_______']),
 3: dict(note='FOLLOW-THROUGH (240 ms): body rises and settles back (guide head 68,71 -> stamp 60,49), blade carries on past the target '
              'down-right; secondary OVERSHOOT: ribbons, skirt tail, sleeve and bow swing past rest to the right (they trailed left on '
              'k1/k2) and will settle; fading pink_0 wisps of the arc',
         dx=1, dy=3, lean=3, wshift=-1, stamp=(60, 49), bow=(1, 0), expr=None, skirt=(SK_FWD, 52, 91),
         legs=[('s', [(64, 97), (60, 101), (58, 103)]), ('d', [(57, 103), (57, 104)]), ('s', [(74, 97), (76, 100), (76, 103)]), ('d', [(76, 103), (78, 104)])],
         arm=[(64, 86), (72, 89)], cuff=(68, 88, CUFF), fists=(72, 87), sword=((76, 89), (96, 103)),
         sleeve=(SLEEVE_FWD, 72, 85),
         ribs=[((66, 84), (77, 79), (86, 84)), ((86, 84), (90, 88), (94, 86)), ((67, 86), (78, 90), (87, 93))],
         fx=['op: arc 70,95 33,13 25 58 p', 'op: arc 70,95 31,12 34 50 P']),
}
for k, c in K.items():
    dx, dy = c['dx'], c['dy']
    L = [f"# slash_SE_k{k} {c['note']}", 'fx: none', f'from: turn_SE {dx} {dy}', f"stamp: {c['stamp'][0]} {c['stamp'][1]}",
         f"bow: {c['bow'][0]} {c['bow'][1]}"]
    if c['expr']: L.append(f"expr: {c['expr']}")
    L.append(f'clear: {55 + dx},{81 + dy},{61 + dx},{93 + dy}')      # near arm of the rest cel: redrawn
    L.append(f'shear: {76 + dy} {87 + dy} {c["lean"]}')              # torso lean over the hips
    L.append(f'clear: 30,{88 + dy},120,112')                         # rest skirt / legs: redrawn
    sk, sx, sy = c['skirt']; ws = c.get('wshift', 0); sx += ws
    c['legs'] = [(t, [(pts[0][0] + ws, pts[0][1])] + pts[1:]) if t == 's' else (t, pts) for t, pts in c['legs']]
    L.append(f'patch: {sx} {sy}'); L += sk.split('\n')
    for tone, pts in c['legs']:
        L.append(f'limb: {tone} 2 ' + ' '.join(f'{x},{y}' for x, y in pts) + ' behind')
    L.append('limb: R 3 ' + ' '.join(f'{x},{y}' for x, y in c['arm']))
    cx, cy, cp = c['cuff']
    L.append(f'patch: {cx} {cy}'); L += cp.split('/')
    fx_, fy_ = c['fists']
    L.append(f'top: {fx_} {fy_}'); L += FISTS
    (hx, hy), (tx, ty) = c['sword']
    L.append(f'sword: {hx},{hy} {tx},{ty}')
    sp, sxx, syy = c['sleeve']
    L.append(f'opb: stamp {sxx},{syy} {sp}')
    for r in c['ribs']:
        L += rib(*r)
    L += c['fx']
    open(D + f'slash_SE_k{k}.txt', 'w').write('\n'.join(L) + '\n')
print('ok')
