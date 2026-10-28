# Hand-keyed poses for pose48.py (SE view). Angles in degrees.
# legs: lt/rt thigh from vertical (+ forward), lk/rk knee bend (+ shin back). arms: la/ra upper arm (+ forward,
# 180 = straight up), le/re elbow (+ forearm forward). l = her LEFT (far, screen-right), r = her RIGHT (near, sword hand).
# bob = pelvis up (px), fwd = pelvis forward (px), lean (+ forward), sq = torso squash. blade = screen angle of the
# katana from the near fist (atan2(dy,dx), y down; 180 = pointing left) or None. bow = [dx,dy] lag offset.


def mirror_run(k):
    m = dict(k)
    for a, b in (('lt', 'rt'), ('lk', 'rk')):
        m[a], m[b] = k.get(b, 0), k.get(a, 0)
    return m


RUN_HALF = [
    dict(rt=48, rk=12, lt=-52, lk=85, la=75, le=85, ra=-60, re=35, lean=24, bob=0.0, ms=70, blade=165, bow=[0, 1],
         hint='RUN contact: big stride, her near (right) leg reaching far forward with the heel striking the ground, far leg kicked up high behind; strong forward lean'),
    dict(rt=16, rk=55, lt=-18, lk=115, la=45, le=90, ra=-45, re=40, lean=26, bob=-2.0, ms=80, blade=170, bow=[0, -1], head='squash',
         hint='RUN down: weight on the deeply bent near leg, far leg folded tight under the body, body lowest'),
    dict(rt=-50, rk=12, lt=62, lk=95, la=-35, le=70, ra=-70, re=30, lean=24, bob=1.5, ms=55, blade=160, bow=[0, 0],
         hint='RUN push-off: near leg fully extended behind pushing off the toe, far knee driven high forward'),
    dict(rt=-58, rk=75, lt=62, lk=40, la=-60, le=60, ra=-75, re=30, lean=22, bob=4.0, ms=65, blade=158, bow=[0, 1],
         hint='RUN flight: both feet high off the ground, far leg reaching forward, near leg kicked up behind'),
]
RUN = RUN_HALF + [dict(mirror_run(k), la=-k['la'] * 0.7, le=k['le'], hint=k['hint'].replace('near', 'XX').replace('far', 'near').replace('XX', 'far'))
                  for k in RUN_HALF]

WALK_HALF = [
    dict(rt=22, rk=4, lt=-20, lk=12, la=25, le=20, ra=-15, re=25, lean=4, bob=0.0, ms=100, blade=150, bow=[0, 0],
         hint='WALK contact: near leg forward heel down, far leg back toe down, arms opposite'),
    dict(rt=12, rk=18, lt=-24, lk=40, la=15, le=25, ra=-10, re=25, lean=5, bob=-1.0, ms=100, blade=152, bow=[0, -1],
         hint='WALK down: weight on the near leg, knee soft, far heel lifting'),
    dict(rt=0, rk=6, lt=8, lk=50, la=0, le=20, ra=-5, re=25, lean=4, bob=0.5, ms=100, blade=150, bow=[0, 0],
         hint='WALK passing: near leg straight under the body, far knee bent passing forward'),
    dict(rt=-14, rk=2, lt=22, lk=22, la=-15, le=15, ra=-20, re=25, lean=4, bob=1.0, ms=100, blade=148, bow=[0, 1],
         hint='WALK up: up on the near toe, far leg reaching forward'),
]
WALK = WALK_HALF + [dict(mirror_run(k), la=-k['la'], hint=k['hint'].replace('near', 'XX').replace('far', 'near').replace('XX', 'far'))
                    for k in WALK_HALF]

IDLE = [dict(rt=-4, rk=0, lt=4, lk=0, spread=0.6, la=-10, le=10, ra=-12, re=20, ms=600, blade=120, hint='idle stance')]

JUMP = [
    dict(lt=32, lk=72, rt=32, rk=72, bob=-4.0, lean=22, la=-45, le=20, ra=-50, re=20, sq=0.9, ms=110, head='squash', blade=160, bow=[0, -1],
         hint='JUMP anticipation: deep crouch, knees bent forward, arms swung back'),
    dict(lt=-8, lk=0, rt=-4, rk=0, bob=7.0, lean=5, la=150, le=10, ra=120, re=10, sq=1.1, ms=60, head='stretch', blade=250, bow=[0, 2],
         hint='JUMP launch: whole body stretched upward, legs straight down, toes pointed, arms thrown up'),
    dict(lt=35, lk=70, rt=45, rk=80, bob=14.0, lean=0, la=120, le=20, ra=100, re=20, ms=80, blade=230, bow=[0, 1],
         hint='JUMP rising: knees tucking up, arms up'),
    dict(lt=55, lk=105, rt=65, rk=110, bob=17.0, lean=-5, la=80, le=30, ra=70, re=30, ms=130, blade=210, bow=[0, 0],
         hint='JUMP apex: compact tuck, both knees high, arms out to the sides'),
    dict(lt=25, lk=45, rt=15, rk=35, bob=16.0, lean=-5, la=100, le=20, ra=95, re=20, ms=90, blade=215, bow=[0, -1],
         hint='JUMP apex 2: legs starting to extend down, arms raised'),
    dict(lt=8, lk=12, rt=-4, rk=10, bob=7.0, lean=-3, la=140, le=10, ra=130, re=10, ms=60, blade=240, bow=[0, -2],
         hint='JUMP falling: legs straight down reaching for the ground, arms up high, hair lifting'),
    dict(lt=32, lk=72, rt=32, rk=72, bob=-4.0, lean=18, la=-25, le=30, ra=-30, re=30, sq=0.86, ms=90, head='squash', blade=170, bow=[0, 1],
         hint='JUMP landing: deep squash, knees bent, arms down and out for balance'),
    dict(lt=12, lk=25, rt=12, rk=25, bob=-1.5, lean=8, la=-15, le=20, ra=-15, re=20, sq=0.96, ms=80, blade=140, bow=[0, 0],
         hint='JUMP recover: rising from the crouch'),
    dict(rt=-4, lt=4, spread=0.6, la=-10, le=10, ra=-12, re=20, ms=130, blade=120, bow=[0, 0], hint='standing'),
]

DASH = [
    dict(rt=22, rk=40, lt=-22, lk=40, lean=-10, bob=-2.0, fwd=-4, la=-30, le=30, ra=-40, re=20, ms=110, blade=170, head='back', bow=[0, 0],
         hint='DASH anticipation: coil back, knees bent, leaning back'),
    dict(rt=55, rk=15, lt=-55, lk=15, lean=38, bob=-2.0, fwd=4, la=-75, le=10, ra=-85, re=10, ms=45, blade=185, head='lean', bow=[-2, 0],
         hint='DASH burst: body stretched forward almost horizontal, legs in a long split stride, arms swept back'),
    dict(rt=55, rk=15, lt=-55, lk=15, lean=38, bob=-2.0, fwd=10, la=-75, le=10, ra=-85, re=10, ms=45, blade=185, head='lean', bow=[-3, 0],
         hint='DASH burst (continued), same pose further forward'),
    dict(rt=40, rk=20, lt=-25, lk=65, lean=-16, bob=-3.0, fwd=11, la=45, le=20, ra=20, re=20, ms=90, blade=150, head='back', bow=[2, 0],
         hint='DASH skid: braking, front leg braced forward, leaning back, arms forward for balance'),
    dict(rt=18, rk=22, lt=-15, lk=32, lean=-5, bob=-1.5, fwd=9, la=10, le=20, ra=0, re=20, ms=80, blade=135, bow=[1, 0],
         hint='DASH settle'),
    dict(rt=-4, lt=4, spread=0.6, fwd=8, la=-10, le=10, ra=-12, re=20, ms=130, blade=120, bow=[0, 0], hint='standing'),
]

SLASH = [
    dict(rt=18, rk=18, lt=-16, lk=18, spread=0.8, la=-15, le=30, ra=25, re=30, ms=100, blade=-25,
         hint='SLASH ready stance, fist forward at waist'),
    dict(rt=10, rk=25, lt=-22, lk=25, spread=0.8, lean=-10, bob=-1.0, la=20, le=40, ra=200, re=15, ms=150, blade=225, head='back', bow=[1, 0],
         hint='SLASH wind-up: near fist raised high above and behind the head, leaning back'),
    dict(rt=38, rk=40, lt=-28, lk=12, spread=0.8, lean=20, bob=-2.0, fwd=2, la=-30, le=30, ra=60, re=10, ms=40, blade=25, head='lean', bow=[-2, 0],
         hint='SLASH strike: lunging forward, near arm swung down and forward'),
    dict(rt=42, rk=45, lt=-30, lk=10, spread=0.8, lean=24, bob=-2.5, fwd=3, la=-40, le=30, ra=40, re=0, ms=90, blade=40, head='lean', bow=[-2, 1],
         hint='SLASH impact: deep lunge, near arm extended forward and down'),
    dict(rt=42, rk=45, lt=-30, lk=10, spread=0.8, lean=24, bob=-2.5, fwd=3, la=-40, le=30, ra=40, re=0, ms=50, blade=40, head='lean', bow=[-1, 1],
         hint='SLASH impact hold'),
    dict(rt=35, rk=40, lt=-28, lk=14, spread=0.8, lean=16, bob=-2.0, fwd=3, la=-30, le=30, ra=10, re=0, ms=80, blade=85, head='lean', bow=[0, 1],
         hint='SLASH follow-through: near arm down by the side'),
    dict(rt=24, rk=25, lt=-20, lk=20, spread=0.8, lean=6, bob=-1.0, fwd=1, la=-20, le=30, ra=15, re=25, ms=90, blade=20, bow=[0, 0],
         hint='SLASH recover'),
    dict(rt=18, rk=18, lt=-16, lk=18, spread=0.8, la=-15, le=30, ra=25, re=30, ms=120, blade=-25, hint='SLASH ready stance'),
]

KEYS = dict(run=RUN, walk=WALK, idle=IDLE, jump=JUMP, dash=DASH, slash=SLASH)
