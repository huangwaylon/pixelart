"""slash_SE k0..k3 RETRACE (S5 r2) on the S3 r2 SE rig (tools/hybrid/h3/cels/turn_SE.py make(pose)).
Acting = Gemini pixel-native keys (hybrid/S5_pixelnative/r2/pose/<name>.png + _hires.png; k0 b1 coil, k1 b1 mid-
swing, k2 a2 lunge, k3 a1 follow-through; generated in mirror space and flipped). Claude retraced each pose with the
rig's own primitives (body/torso offsets, @skirt tips, @leg joints, @cuff arms, @katana, @ribbon) - no Gemini pixel
is used. FX = the shared smear kit (tools/hybrid/fx/smear.py) via kit 'fx'.
Two-hand diagonal cut: coil back over her RIGHT (near, viewer-left) shoulder, sweep DOWN through the FRONT of the
cut plane (camera side, in front of the legs), impact at chest height viewer-right, follow-through overshoots
up-right. Blade-tip path = ONE circle, centre (64,53) r 36 (tip angles ~155 / 70 / 25 / -5): the arc runs at hip-to-chest
height (no ground ring) -> tip-arc rms <= 1.
Coordinates are pre-SHIFT (the rig shifts the frame by SHIFT after building)."""
import sys, math
sys.path.insert(0, '/Users/waylonhuang/Documents/other/pixelart/swordswoman/archive/v1/tools/hybrid/s5r2')
import secondary as SEC
MS = [220, 50, 160, 240]
CX, CY, CR = 64, 53, 36

BODY = [(-3, 4), (1, 4), (3, 5), (4, 4)]
TORSO = [(-2, 1), (2, 1), (4, 2), (3, 0)]
HEAD = [(-6, 5), (3, 4), (8, 6), (7, 3)]
EXPR = ['glare', 'wide', 'kiai', 'glare']
TILT = [-1, 0, 1, 1]

def tip(a): return (CX + CR * math.cos(math.radians(a)), CY + CR * math.sin(math.radians(a)))

def skirt(k, tips, tw=14, sway=0, top=82):
    """skirt with ABSOLUTE tip positions (the rig adds body x to tips; y is absolute)"""
    bx = BODY[k][0]
    return dict(tips=[(x - bx, y) for x, y in tips], tw=tw, sway=sway, top=top)

def tail(k, tips, tw=20):
    bx = BODY[k][0]
    return dict(tips=[(x - bx, y) for x, y in tips], tw=tw)

def ribbons():
    """follow-through driver (secondary.chain): the travel the cut implies (coil back, whip, stop, drift);
    the cloth trails against it, root-to-tip lag 0.6 -> 2.4 frames, overshoot + settle, frozen on the hit-stop."""
    root = lambda b, t, x, y: (x + b[0] + t[0], y + b[1] + t[1])
    # key -1 = the idle stance she winds up from (dropped after the sim)
    rN = [(58, 75)] + [root(BODY[k], TORSO[k], 58, 75) for k in range(4)]
    rF = [(71, 74)] + [root(BODY[k], TORSO[k], 71, 74) for k in range(4)]
    virt = [(0, 0), (-10, 0), (6, 2), (14, 3), (14, 2)]
    ker = (1.0, -0.9, -0.3)          # trail, then a hard OVERSHOOT the frame after the stop (S-curve settle)
    N = SEC.chain(rN, virt, rest_dir=(-0.3, 1.0), nodes=10, seg=2.0, amp=0.18, holds=(3,), lags=(0.3, 1.8), kernel=ker, maxdev=0.85, sag=0.09)[1:]
    F = SEC.chain(rF, virt, rest_dir=(0.6, 1.0), nodes=10, seg=2.0, amp=0.22, holds=(3,), lags=(0.3, 1.6), kernel=ker, maxdev=0.95, sag=0.08)[1:]
    return N, F

BOWK = [(2, 0), (-2, 0), (-2, 0), (2, 0)]   # bun+bow lag: trails the wind-up, the whip, held on the hit-stop, overshoots
# spine lean (S1 bodykit shear on the torso / collar cels: + = top leans to viewer-right)
LEANX = [-2, 2, 3, 2]
def XF(k):
    L = LEANX[k]; h = (L // 2) if L > 0 else -((-L) // 2)
    return {'torso': [('sh', 70, 86, L)], 'collar': [('sh', 66, 80, h)], 'collar_over': [('sh', 64, 80, h)]}
def bowlag_spring():
    h = [(float(x), float(y)) for x, y in HEAD]
    s = SEC.spring(h, MS, k=0.010, c=0.09, holds=(2,), cycles=2)
    return [(max(-2, min(2, round(sx - hx))), max(0, min(1, round(sy - hy)))) for (sx, sy), (hx, hy) in zip(s, h)]

def front2(cx, cy, r, rows=2, ymin=88):
    """front-plane rule: only the `rows` outer (leading) rows of the band pass OVER the body, and only in front
    of the legs (y >= ymin); the bulk of the band goes behind."""
    def f(x, y):
        if y < ymin: return False
        d = r - math.hypot(x - cx, y - cy)
        return d < rows
    return f

def ticks5(x, y, r0=6, r1=8, a0=-72):
    """5 burst ticks round the spark (2-3 px each, steel_2 -> pink_1)"""
    pts = []
    for i in range(5):
        a = math.radians(a0 + 72 * i)
        for r in range(r0, r1 + 1):
            pts.append((round(x + r * math.cos(a)), round(y + r * math.sin(a)), 'P' if r == r0 else 'p'))
    return pts

def frames():
    RN, RF = ribbons(); BOW = BOWK
    F = {}
    def base(k, **pose):
        p = dict(body=BODY[k], torso=TORSO[k], ribbonN=SEC.ints(RN[k]), ribbonF=SEC.ints(RF[k]))
        p.update(pose)
        return dict(base='turn_SE', pose=p, expr=EXPR[k], tilt=TILT[k], head=HEAD[k], bow=BOW[k], xf=XF(k))
    # ---------------- k0 COIL (220 ms hold): weight sunk on the back (near) leg, hips back-left, torso leaned back
    # and twisted, both hands up by her right shoulder, blade drawn back past the shoulder (tip ~155 deg).
    f = base(0,
        skirt=skirt(0, [(47, 98), (54, 101), (65, 100), (75, 97)], tw=15),
        tail=tail(0, [(43, 102), (78, 100)]),
        legs=[((58, 96), (53, 99), (52, 101), 'se', -1), ((66, 96), (72, 99), (76, 101), 'toe', 1)],
        armN=dict(upper=((54, 79), (52, 81)), cuff=((53, 79), (46, 80), 4, 9), hand=(45, 76)),
        armF=dict(upper=None, cuff=((70, 79), (70, 80), 1, 1)),
        katana=(48, 77, 206.6, 19, -1), kat_layer='mid',
        extra={'armX': ('after:armL', "@limb 69,79,1.5 64,82,1.3\n@cuff 65,81 51,80 4 7")})
    f['drop'] = ('armR',)
    f['fx'] = [('lines', dict(x=37, y=64, dx=-1, dy=-0.4, n=2, L=[5, 3], gap=3, tones='p'))]
    F['slash_SE_k0'] = f
    # ---------------- k1 SMEAR (50 ms): unwinding into the lunge (front foot slides out, back heel lifts), arms
    # swept down-forward to the camera side, blade foreshortened toward the viewer at the lead of the arc.
    f = base(1,
        skirt=skirt(1, [(49, 97), (56, 100), (68, 100), (79, 96)], tw=15, sway=1),
        tail=tail(1, [(43, 101), (80, 99)]),
        legs=[((60, 97), (55, 100), (51, 101), 'heelup', -1), ((68, 97), (75, 99), (80, 101), 'se', 0)],
        armN=dict(upper=((60, 80), (63, 84)), cuff=((62, 83), (68, 89), 4, 9), hand=None),
        armF=dict(upper=None, cuff=((75, 80), (75, 81), 1, 1)),
        katana=(68, 86, 18.4, 9, 1), kat_layer="front",
        extra={'armX': ('after:armL', "@limb 75,79,1.5 73,84,1.3\n@cuff 73,83 71,88 4 7\n= 67 88\n|KssK\n|.KK.")})
    f['drop'] = ('armR',)
    f['fx'] = [
        ('arc', dict(cx=CX, cy=CY, rx=CR, ry=CR, a0=155, a1=31, lead=7, front=front2(CX, CY, CR, 2, 84), echo=True)),
        ('limb', dict(path=[(68, 88), (61, 89), (53, 87), (46, 82), (40, 76)], w0=5, w1=1, tones='CRr',
                      hand=(50, 85), mode='behind')),
    ]
    F['slash_SE_k1'] = f
    # ---------------- k2 IMPACT (hit-stop 160 ms): deep lunge, front knee over the toe, back leg long with the heel
    # up, torso pitched into the cut, both arms out to viewer-right, blade level at chest height, spark + 5 ticks.
    t2 = (93, 66)                      # blade tip = katana (80,79) -45 deg L19 (r 33); spark arms reach the r 36 circle
    f = base(2,
        skirt=skirt(2, [(51, 98), (58, 101), (71, 100), (81, 96)], tw=15, sway=2),
        tail=tail(2, [(42, 100), (83, 99)]),
        legs=[((62, 98), (53, 100), (45, 101), 'heelup', -1), ((71, 98), (79, 99), (82, 101), 'se', 0)],
        armN=dict(upper=((63, 82), (69, 82)), cuff=((67, 82), (77, 80), 4, 8), hand=(77, 77)),
        armF=dict(upper=None, cuff=((79, 80), (80, 81), 1, 1)),
        katana=(80, 79, -45, 19, 1), kat_layer='front')
    f['fx'] = [
        ('sliver', dict(cx=CX, cy=CY, rx=CR, ry=CR, a0=75, a1=28, keep=0.6, thick=2, front=front2(CX, CY, CR, 1, 84))),
        ('spark', dict(x=round(t2[0]), y=round(t2[1]), r=4, ticks=False)),
        ('px', dict(pts=ticks5(round(t2[0]), round(t2[1]), r0=7, r1=10))),
    ]
    F['slash_SE_k2'] = f
    # ---------------- k3 FOLLOW-THROUGH (240 ms): blade carried past, up-right; chest overshoots ahead of the hips,
    # cuffs flare, hem flicks past rest, ribbons overshoot (driver); pink wisps at the arc tail only.
    f = base(3,
        skirt=skirt(3, [(51, 97), (58, 100), (71, 99), (82, 95)], tw=15, sway=2),
        tail=tail(3, [(44, 100), (84, 97)]),
        legs=[((62, 96), (56, 99), (51, 101), 'se', -1), ((70, 96), (75, 99), (78, 101), 'se', 0)],
        armN=dict(upper=((63, 81), (72, 76)), cuff=((70, 77), (83, 66), 4, 9), hand=(84, 62)),
        armF=dict(upper=None, cuff=((79, 77), (80, 77), 1, 1)),
        katana=(88, 62, -45, 17, 1), kat_layer='front',
        extra={'armX': ('after:armL', "@cuff 80,70 87,63 3 6")})
    f['fx'] = [('wisps', dict(pts=[[(97, 61), (100, 59), (102, 60)], [(95, 67), (98, 66), (100, 67)]]))]
    F['slash_SE_k3'] = f
    return F
