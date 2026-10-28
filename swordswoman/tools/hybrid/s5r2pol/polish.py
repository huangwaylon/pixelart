"""S5 r2 POLISH (Claude hand pixel pass). sprite/ -> polished/ ; every edit is listed with its reason in polwork/edits.json"""
import sys, os, shutil, json, math
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pk
R = '/Users/waylonhuang/Documents/other/pixelart/swordswoman/hybrid/S5_pixelnative/r2'
SRC, DST = R + '/sprite', R + '/polished'
LOG = []
def note(name, what, why): LOG.append(dict(sprite=name, edit=what, reason=why))
def head(name):
    f = R + '/work/%s_head.npy' % name
    return np.load(f) if os.path.exists(f) else None

def slash_k1(a, n):
    CX, CY, CR = 64, 53, 36
    hm = head(n)
    # 1 remove the 1 px red_1 limb-smear seam inside the crescent tail (reads as a dark crack)
    for y in range(74, 85):
        for x in range(36, 54):
            if pk.ch(a, x, y) == 'r': a[y, x] = 0
    note(n, 'cleared red_1 seam x36-53 y74-84', 'stray limb-smear residue reads as a crack inside the smear tail')
    # 2 sleeve multiple-limb smear: red band inside the tail of the blade arc (arms sweeping down)
    for k in range(60):
        s = k / 59; ang = math.radians(150 - 50 * s); sb = (157 - math.degrees(ang)) / 127
        rr = CR + 0.5 - (1.5 + 8.5 * sb) - 0.6 - (1.0 + 2.6 * s) / 2
        x, y = CX + rr * math.cos(ang), CY + rr * math.sin(ang)
        w = 1.0 + 2.6 * s
        pk.thick_line(a, (x, y), (x, y), w, w, 'C' if s < 0.45 else 'R', 'behind')
    note(n, 'sleeve smear band hugging the crescent inner edge ang 150->98 (red_3 -> red_2)', 'multiple-limb smear: arms swept with the blade')
    # 3 bold blade crescent: tail 1.5 px -> lead 10 px, steel_2 rim 2 px on the lead half, front of legs over 3 rows
    front = lambda x, y, ang: 55 <= ang <= 128 and y >= 83
    pk.crescent(a, CX, CY, CR, 157, 30, wmax=10, w0=1.5, pw=1.0, front=front, over_rows=3, protect=hm, clear_old=11,
                rim=(0.15, 1.5, 0.55, 2.5))
    note(n, 'repainted blade-arc crescent c(64,53) r36 157->30 deg, w 1.5->10', 'old band was 1 px for 2/3 of its length (thin at 1x)')


def slash_k2(a, n):
    X, Y = 93, 66
    bl = lambda x, y: abs((x - 80) + (y - 79)) <= 1 and x <= 92      # blade pixels on the -45 deg line (80,79)->(93,66)
    for y in range(52, 80):
        for x in range(84, 110):
            if pk.ch(a, x, y) in 'pPw' and not bl(x, y): a[y, x] = 0
    note(n, 'cleared old 4-arm spark + 5 ticks', 'replaced by a bigger hit-stop burst')
    # 8-point impact star: long cardinal arms (7), short diagonals (3), 3x3 white core
    for k in range(-7, 8):
        c = 'w' if abs(k) <= 4 else ('P' if abs(k) <= 6 else 'p')
        if abs(k) <= 7: pk.put(a, X + k, Y, c); pk.put(a, X, Y + k, c)
    for k in range(1, 4):
        c = 'w' if k == 1 else ('P' if k == 2 else 'p')
        for sx, sy in ((1, 1), (1, -1), (-1, -1)): pk.put(a, X + sx * k, Y + sy * k, c)
    pk.stamp(a, X - 1, Y - 1, ['www', 'www', 'www'])
    pk.put(a, X + 1, Y - 2, 'w'); pk.put(a, X - 2, Y + 1, 'P', 'behind')
    # burst ring: 8 radial strokes r 9..13 between the arms (behind the body), steel_2 head -> pink tail
    for i in range(8):
        ang = math.radians(22.5 + 45 * i)
        if 100 < (22.5 + 45 * i) < 250: continue                 # skip the strokes that would hit her arm / face
        for r in range(9, 14):
            c = 'w' if r <= 10 else ('P' if r <= 12 else 'p')
            pk.put(a, round(X + r * math.cos(ang)), round(Y + r * math.sin(ang)), c, 'behind')
    # impact shock arcs: two short pink_1 arcs either side of the cut, r 16
    for ang in range(-70, -35, 3): pk.put(a, round(X + 16 * math.cos(math.radians(ang))), round(Y + 16 * math.sin(math.radians(ang))), 'P', 'behind')
    for ang in range(5, 45, 3): pk.put(a, round(X + 16 * math.cos(math.radians(ang))), round(Y + 16 * math.sin(math.radians(ang))), 'P', 'behind')
    note(n, '8-point star (arms 7/3) + 5 radial burst strokes r9-13 + 2 shock arcs r16 at the tip (93,66)', 'hit-stop impact reads at 1x (old spark was 9 px wide)')

def slash_k3(a, n):
    CX, CY, CR = 64, 53, 36
    for y in range(56, 70):
        for x in range(94, 106):
            if pk.ch(a, x, y) in 'pP': a[y, x] = 0
    note(n, 'cleared 2 tiny wisps', 'replaced by a dissipating arc')
    # dissipating smear trail behind the blade: thin crescent 38 -> -6 deg (4 px at the blade, 1 px tail), tail broken up
    tmp = np.zeros_like(a)
    pk.crescent(tmp, CX, CY, CR, 38, -6, wmax=4, w0=1, pw=1.0, rim=(0.75, 1.5, 0.99, 0), inner_echo=False)
    for y, x in zip(*np.nonzero(tmp[:, :, 3])):
        ang = math.degrees(math.atan2(y - CY, x - CX)); sp = (38 - ang) / 44
        if sp < 0.45 and (x + y) % 2: continue           # break up the decaying tail (dissolve)
        if sp < 0.2 and (x + y) % 4: continue
        if a[y, x, 3] == 0: a[y, x] = tmp[y, x]
    for y in range(40, 90):                              # drop dissolve pixels left without a same-tone neighbour
        for x in range(84, 108):
            c = pk.ch(a, x, y)
            if c in 'pP' and tmp[y, x, 3] and not any(pk.ch(a, x + i, y + j) in 'pPw' for i in (-1, 0, 1) for j in (-1, 0, 1) if i or j): a[y, x] = 0
    note(n, 'dissipating follow-through crescent c(64,53) r36 38->-6 deg (4 px at the blade, dissolved tail)', 'smear decays after the hit instead of vanishing')
    # far ribbon: thicken the overshooting ribbon to 2 px (pink_1 top, pink_0 under) so it reads as cloth at 1x
    pts = [(x, y) for y in range(78, 94) for x in range(78, 94) if pk.ch(a, x, y) in 'pP']
    for x, y in pts:
        if pk.ch(a, x, y + 1) == '.': pk.put(a, x, y + 1, 'p')
        pk.put(a, x, y, 'P')
    tip = max(pts, key=lambda p: p[1]) if pts else None
    if tip: pk.stamp(a, tip[0] - 1, tip[1] + 1, ['_pP', '__p'], 'behind')
    note(n, 'far ribbon thickened to 2 px + curled tip', 'secondary overlap readable at 1x')

def jump_apex(a, n):
    for y in range(100, 112):
        for x in range(40, 60):
            if pk.ch(a, x, y) in 'pPTtw' and y >= 103: a[y, x] = 0
    for x, y0, L in ((46, 100, 8), (50, 103, 6), (54, 104, 9), (58, 105, 5), (63, 104, 7)):
        for k in range(L):
            pk.put(a, x, y0 + k, 'P' if k < L * 0.4 else 'p', 'behind')
    note(n, '5 tapered vertical take-off streaks below the feet (5-9 px)', 'rise smear: speed of the launch at the stretch key')

def jump_land(a, n):
    for y in range(96, 108):
        for x in range(24, 100):
            if pk.ch(a, x, y) in 'tT': a[y, x] = 0
    L = ['____TTT____', '__TTwwTT_T_', '_TwwTTTTTT_', 'TTTTTTTtTTT', '_tttTTttt__']
    for x0, flip in ((26, False), (82, True)):
        rows = [r[::-1] for r in L] if flip else L
        pk.stamp(a, x0, 100, rows, 'behind')
    for (x, y), c in (((24, 98), 'T'), ((23, 96), 't'), ((95, 98), 'T'), ((97, 96), 't'), ((30, 96), 't'), ((89, 96), 't')):
        pk.put(a, x, y, c, 'behind')
    note(n, 'landing dust: two 11x5 puffs (steel_2 lit top, steel_0 under) + 6 flying grit px', 'impact weight on the landing squash (old puffs were 4x3)')

def bow_peek(side):
    def f(a, n):
        if side == 'L': pk.stamp(a, 51, 44, ['_KK', 'KRR', 'KRR', 'Krr', '_Kr', '__K'])
        else: pk.stamp(a, 75, 44, ['KK_', 'RRK', 'RRK', 'rrK', 'rK_', 'K__'])
        note(n, 'second bow loop tip peeking past the bun (%s)' % side, 'two-loop bow identity held in the back 3/4 views')
    return f

def run():
    os.makedirs(DST, exist_ok=True)
    for f in sorted(os.listdir(SRC)):
        if f.endswith('_4x.png'): continue
        shutil.copy(os.path.join(SRC, f), os.path.join(DST, f))
    for n, fn in FIX.items():
        p = os.path.join(DST, n + '.png'); a = pk.load(p); fn(a, n); pk.save(a, p)
    from PIL import Image
    for f in os.listdir(DST):
        if f.endswith('.png') and not f.endswith(('_4x.png', '_hires.png', '_pose.png')):
            im = Image.open(os.path.join(DST, f)); im.resize((512, 512), Image.NEAREST).save(os.path.join(DST, f[:-4] + '_4x.png'))
    json.dump(LOG, open(R + '/polwork/edits.json', 'w'), indent=1)
    print(len(LOG), 'edits')

FIX = {'slash_SE_k1': slash_k1, 'slash_SE_k2': slash_k2, 'slash_SE_k3': slash_k3, 'jump_E_apex': jump_apex,
       'jump_E_land': jump_land, 'turn_NE': bow_peek('L'), 'turn_NW': bow_peek('R')}
if __name__ == '__main__': run()
