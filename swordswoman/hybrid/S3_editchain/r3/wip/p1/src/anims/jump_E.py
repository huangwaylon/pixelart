# jump_E crouch / apex / land (= jump f0, f2-ish take-off stretch, f4). Root-locked (engine z lifts the apex).
# crouch: -12 % h / +8 % w, knees forward 3 px, torso pitched forward 2 px, arms swung back, head sunk 2 px, squint.
# apex : take-off STRETCH smear: legs + skirt elongated, toes pointed, 4 motion lines trailing down, sword flung up,
#        arms out, true E profile, wide eyes; cloth drags down (lag).
# land : -16 % h, feet wide, knees out, hem flared 3 px each side down to the ground line with the petal tips flicked
#        up 1 px, 2 expanding dust puffs, squeeze face, arms forward/out for balance. The katana never crosses y 104.
FRAMES = {}

# ---------------- crouch
by = 5
FRAMES['jump_E_crouch'] = dict(
    base='turn_E', head=(3, 7), sink=0, expr='squint', bow=(-1, -1), move=[('legF', 'after:skirt'), ('legs', 'after:legF')],
    pose=dict(
        body=(1, by), torso=(1, 0), collar=(2, by + 1),
        skirt=dict(top=82, cx=62.5, tw=12, tips=[(48, 98), (55, 99), (63, 98), (70, 95)], slit=None),
        tail=dict(top=84, cx=61, tw=13, tips=[(46, 101), (62, 99)]),
        legs=[((63, 95), (69, 97), (64, 101), 'e', 0)],
        legF=[((66, 95), (72, 97), (68, 101), 'e', 0)],
        armN=dict(upper=((63, 82), (60, 86)), cuff=((60, 85), (54, 91), 4, 8), hand=(51, 91)),
        katana=(56, 93, 180 - 18.4, 18, -1), kat_layer='back',
        ribbon=[(60, 81), (57, 80), (54, 80), (51, 81), (48, 82), (46, 84), (44, 85)],
    ),
    xf={'skirt': [('sq', 88, 96, 1)], 'torso': [('sh', 76, 89, 2)], 'collar': [('mv', 1, 0)], 'collar_over': [('mv', 1, 0)]},
)

# ---------------- apex (take-off stretch)
# legs + skirt elongated (+8 %), toes pointed; the bell skirt is pulled DOWN and narrow at the knees but its back
# tail streams down-back 4 px (cloth drags against the upward launch); arms thrown out: the sword arm up-forward
# (blade up, never near the ground), the free arm out-back with its bell sleeve hanging; 4 motion lines below the
# hem / heels trail downward; wide eyes.
FRAMES['jump_E_apex'] = dict(
    base='turn_E', head=(1, -4), expr='wide', bow=(-1, 2),
    pose=dict(
        body=(0, -4), torso=(0, 0), collar=(0, -4),
        skirt=dict(top=82, cx=62.5, tw=11, tips=[(50, 95), (56, 97), (65, 97), (72, 94)], slit=(68, 86, 1, 2), shorts=91),
        tail=dict(top=80, cx=60, tw=12, tips=[(45, 100), (60, 97)], slope=0.6),
        legs=[((60, 91), (60, 96), (60, 101), 'etoe', 0)],
        legF=[((64, 91), (65, 95), (64, 100), 'etoe', 0)],
        armN=dict(upper=((62, 72), (67, 67)), cuff=None, sleeve=((67, 67), (72, 62), (3, 7), 4), hand=(72, 60)),
        armF=dict(upper=((58, 72), (53, 70)), cuff=None, sleeve=((53, 70), (48, 67), (-2, 7), 3), hand=None),
        katana=(74, 60, -63.4, 21, 1), kat_layer='front',
        ribbon=[(59, 70), (57, 73), (55, 77), (54, 81), (53, 85), (51, 88), (50, 92)],
    ),
    xf={},
    fx=[('lines', dict(x=50, y=94, dx=0, dy=1, n=2, L=[7, 4], gap=3, tones='p', perp=(-1, 0))),
        ('lines', dict(x=73, y=93, dx=0, dy=1, n=2, L=[6, 4], gap=3, tones='p', perp=(1, 0)))],
)

# ---------------- land
by = 10
FRAMES['jump_E_land'] = dict(
    base='turn_E', head=(1, 11), sink=0, expr='squeeze', bow=(1, 2),
    pose=dict(
        body=(0, by), torso=(0, 0), collar=(0, by),
        skirt=dict(top=82, cx=62.5, tw=14, tips=[(46, 103), (53, 103), (63, 103), (70, 103), (77, 102)], slit=None,
                   slope=0.45, wedge=4),
        tail=dict(top=86, cx=61, tw=16, tips=[(43, 103), (62, 101)], slope=0.35),
        legs=[((59, 100), (56, 101), (55, 101), 'e', 0)],
        legF=[((65, 100), (69, 101), (70, 101), 'e', 0)],
        armN=dict(upper=((61, 86), (66, 88)), cuff=((65, 87), (72, 91), 4, 9), hand=(73, 90)),
        katana=(75, 92, 18.4, 18, 1), kat_layer='front',
        ribbon=[(59, 84), (56, 82), (53, 81), (50, 81), (47, 82), (45, 84), (43, 86)],
    ),
    xf={'skirt': [('sq', 90, 100, 1)]},
    fx=[('px', dict(pts=[(45, 102, 'K'), (46, 101, 'K'), (77, 101, 'K'), (78, 100, 'K')])),
        ('dust', dict(x=50, y=104, stage=1, mode='over')), ('dust', dict(x=78, y=104, stage=1, flip=True, mode='over'))],
)
