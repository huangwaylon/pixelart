# BONUS smear frames (user priority: smears for fast movement).
# run_SE_f1 = run FLIGHT frame: body pitched forward, legs split, the trailing leg is a STRETCHED-LIMB smear
#   (shin elongated along the swing) plus a 2-copy multi-leg echo (pink_1 / pink_0), 2 motion lines behind the hem
#   and the shoulder, ribbons + tails streamed back flat, focused face.
# dash_SE_f1 = dash TRAVEL A: stretched frame (+12 % along the travel, -5 % across), the blade trails level behind
#   (iaido dash), 2 flat afterimages of the pose 6 px / 12 px back along the travel (pink_1 near, pink_0 far),
#   4 speed lines (steel_2 / pink_0 alternating) from the trailing edge.
import sys
sys.path.insert(0, 'tools/hybrid/anim')
import secondary as S2

FRAMES = {}
bx, by = 2, -2
FRAMES['run_SE_f1'] = dict(
    base='turn_SE', head=(3, -1), bow=(-2, 1), expr='glare',
    pose=dict(
        body=(bx, by), torso=(1, 0),
        skirt=dict(tips=[(48, 93), (55, 96), (68, 97), (77, 94)], sway=-3),
        tail=dict(tips=[(40, 96), (78, 96)]),
        legs=[((63, 91), (58, 95), (52, 97), 'heelup', 0), ((71, 91), (75, 95), (75, 100), 'sef', 0)],
        armN=dict(upper=((57, 74), (60, 79)), cuff=((60, 79), (64, 84), 4, 8), hand=(64, 85)),
        armF=dict(upper=((74, 73), (72, 78)), cuff=((72, 78), (68, 80), 3, 6), upper2=None),
        katana=(68, 81, 180 + 18.4, 21, -1), kat_layer='back',
        ribbonN=[(60, 73), (56, 73), (52, 73), (48, 74), (44, 74), (40, 75), (37, 76)],
        ribbonF=[(73, 72), (69, 70), (65, 69), (61, 69), (57, 70)],
    ),
    xf={'torso': [('sh', 70, 86, 2)], 'collar': [('mv', 1, 0)], 'collar_over': [('mv', 1, 0)]},
    fx=[('limb', dict(path=[(53, 97), (49, 96), (45, 95)], w0=3, w1=1, tones='smm', mode='behind', ol_lead=False)),
        ('echo_self', dict(region=(44, 92, 60, 101), offsets=[(-4, -1), (-8, -2)], tones=['P', 'p'], steps=[1, 2])),
        ('lines', dict(x=44, y=86, dx=-1, dy=0, n=2, L=[7, 5], gap=3, tones='p', perp=(0, 1))),
        ('lines', dict(x=50, y=70, dx=-1, dy=0, n=2, L=[6, 4], gap=3, tones='p', perp=(0, 1)))],
)

bx, by = 1, 0
FRAMES['dash_SE_f1'] = dict(
    base='turn_SE', head=(4, 1), bow=(-2, 0), expr='glare',
    pose=dict(
        body=(bx, by), torso=(2, 0),
        skirt=dict(tips=[(47, 94), (54, 97), (69, 97), (79, 94)], sway=-4),
        tail=dict(tips=[(38, 95), (80, 97)]),
        legs=[((62, 93), (57, 97), (51, 99), 'heelup', 0), ((70, 93), (76, 97), (79, 101), 'sef', 0)],
        armN=dict(upper=((58, 76), (56, 81)), cuff=((56, 81), (50, 84), 4, 8), hand=None),
        armF=dict(upper=((74, 76), (68, 81)), cuff=((68, 81), (55, 85), 3, 6)),
        katana=(51, 86, 180, 22, -1), kat_layer='front',
        ribbonN=[(60, 75), (55, 74), (50, 73), (45, 73), (40, 73), (36, 74), (33, 75)],
        ribbonF=[(73, 74), (68, 72), (63, 71), (58, 71), (54, 72)],
    ),
    xf_all=[('wd', 64, 3)], xf_skip=('HEAD',),
    # tapered afterimage WEDGES off the trailing masses (hair dome, sleeve, skirt, back leg): pink_1 at the body
    # end fading to pink_0 and a 1 px point, plus one far scan-streak afterimage and 2 steel_2 speed lines
    fx=[('limb', dict(path=[(54, 56), (46, 52), (37, 48)], w0=6, w1=1, tones='PPp', mode='behind', ol_lead=False)),
        ('limb', dict(path=[(51, 80), (43, 76), (33, 72)], w0=5, w1=1, tones='PPp', mode='behind', ol_lead=False)),
        ('limb', dict(path=[(47, 93), (39, 89), (30, 85)], w0=5, w1=1, tones='PPp', mode='behind', ol_lead=False)),
        ('limb', dict(path=[(50, 100), (44, 97), (37, 94)], w0=3, w1=1, tones='Pp', mode='behind', ol_lead=False)),
        ('echo_self', dict(offsets=[(-9, -4)], tones=['p'], region=(40, 50, 70, 104), steps=[1])),
        ('lines', dict(x=36, y=64, dx=-1, dy=-0.5, n=2, L=[12, 8], gap=14, tones='w', perp=(0, 1)))],
)
