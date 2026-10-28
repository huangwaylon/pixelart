"""jump_E crouch / apex / land RETRACE (S5 r2) on the S3 r2 E rig (tools/hybrid/h3/cels/turn_E.py make(pose)).
Acting = Gemini pixel-native keys (pose/<name>.png + _hires.png): crouch = a3 'crouch_g' (true profile, knees
forward, arms back, blade trailing), apex = a3 'apex_p' (true profile, arms flung up, sword raised high back, legs
tucked), land = a1 (wide flared bell, arms out). Every key keeps the E-profile torso cel but redraws it per key:
crouch = pitched FORWARD (shear), apex = stretched tall, land = upright and squashed (2 rows removed) under a wide bell.
Rig coordinates: skirt/tail tips and limb joints are absolute; body/torso offsets move the torso / collar cels."""
import sys, math
sys.path.insert(0, '/Users/waylonhuang/Documents/other/pixelart/swordswoman/tools/hybrid/s5r2')
import secondary as SEC
MS = [160, 220, 200]
BODY = [(-1, 5), (1, -8), (0, 8)]
HEAD = [(5, 8), (1, -9), (3, 10)]
EXPR = ['glare', 'wide', 'squeeze']
TILT = [1, -1, 1]

def ribbons():
    # key -1 = idle stand; virtual travel = the jump itself (down into the crouch, up 30 px, back down hard)
    roots = [(59, 74)] + [(59 + b[0], 74 + b[1]) for b in BODY]
    virt = [(0, 0), (0, 6), (2, -30), (3, 2)]
    R = SEC.chain(roots, virt, rest_dir=(-0.75, 1.0), nodes=8, seg=2.0, amp=0.07, lags=(0.6, 2.2))
    return R[1:]

def bowlag():
    h = [(0.0, 0.0)] + [(float(x), float(y)) for x, y in HEAD]
    s = SEC.spring(h, [150] + MS, k=0.010, c=0.08)
    return [(max(-2, min(2, round(sx - hx))), max(0, min(2, round(sy - hy)))) for (sx, sy), (hx, hy) in zip(s[1:], h[1:])]

def frames():
    RB = ribbons(); BOW = [(1, 0), (-2, 0), (0, 2)]   # crouch: bun lags up-forward; apex: tilted back; land: squashed down
    F = {}
    def base(k, **pose):
        p = dict(body=BODY[k], ribbon=SEC.ints(RB[k])); p.update(pose)
        return dict(base='turn_E', pose=p, expr=EXPR[k], tilt=TILT[k], head=HEAD[k], bow=BOW[k])
    # ---------------- CROUCH (160 ms): -12 % tall, +wide; hips back, knees forward 3 px, torso pitched forward,
    # both arms swung back, blade trailing low behind, head sunk 2 into the collar, squint.
    f = base(0, torso=(3, 1),
        skirt=dict(tw=12, tips=[(46, 100), (52, 102), (60, 101), (66, 97)], sway=-1),
        tail=dict(tw=13, tips=[(41, 102), (57, 100)]),
        legs=[((60, 95), (70, 97), (64, 101), 'e', 0)],
        legF=[((63, 94), (73, 96), (68, 101), 'e', 0)],
        armN=dict(upper=((62, 80), (58, 83)), cuff=((59, 82), (50, 86), 4, 9), hand=(47, 85)),
        katana=(49, 87, 198.4, 19, -1), kat_layer='mid')
    f['xf'] = {'torso': [('sh', 69, 84, 3)], 'collar': [('sh', 66, 76, 2)], 'collar_over': [('sh', 64, 72, 2)]}
    f['sink'] = 1
    F['jump_E_crouch'] = f
    # ---------------- APEX (220 ms hang): drawn 8 px up in the cell; body stretched (+3 rows in the skirt and
    # legs), legs tucked with pointed toes, both arms FLUNG up, sword raised high behind the head, smile;
    # take-off stretch smear: pink_0 / steel_1 motion lines under the feet.
    f = base(1,
        skirt=dict(top=82, tw=10, tips=[(51, 90), (56, 92), (63, 92), (70, 88)], sway=1),
        tail=dict(top=84, tw=11, tips=[(45, 93), (60, 90)]),
        legs=[((61, 86), (59, 92), (56, 97), 'etoe', 0)],
        legF=[((65, 85), (71, 87), (68, 91), 'etoe', 0)],
        armN=dict(upper=((63, 68), (70, 60)), cuff=((69, 61), (76, 49), 4, 8), hand=(75, 45)),
        armF=dict(upper=((58, 69), (54, 63)), cuff=((55, 64), (48, 56), 4, 8), hand=None),
        katana=(77, 46, -116.6, 22, -1), kat_layer='front')
    f['xf'] = {'torso': [('st', 76, 80, 1)]}
    f['shift'] = (0, 6)                     # root-locked: the engine lifts the apex (anim_spec engine_z 16)
    f['fx'] = [('lines', dict(x=55, y=105, dx=0, dy=1, n=3, L=[4, 6, 3], gap=4, tones='pTp'))]
    F['jump_E_apex'] = f
    # ---------------- LAND (200 ms): -16 % tall, the bell flares wide almost to the ground, petal tips lifted,
    # torso upright and squashed (2 rows out), arms out for balance, blade low out front (never under the ground
    # line), head sunk, squeeze face, 2 dust puffs + ticks.
    f = base(2,
        skirt=dict(tw=15, tips=[(43, 102), (50, 104), (66, 104), (76, 101)], slope=0.55, sway=0),
        tail=dict(tw=16, tips=[(39, 103), (69, 102)]),
        legs=[((58, 100), (55, 101), (55, 101), 'e', 0)],
        legF=[((65, 100), (69, 101), (70, 101), 'e', 0)],
        armN=dict(upper=((62, 84), (67, 85)), cuff=((65, 85), (74, 88), 4, 9), hand=(75, 87)),
        armF=dict(upper=((58, 84), (55, 85)), cuff=((56, 85), (48, 88), 4, 8), hand=None),
        katana=(77, 88, 26.6, 17, 1), kat_layer='front')
    f['xf'] = {'torso': [('sq', 76, 81, 2), ('sh', 69, 84, 2)], 'collar': [('sh', 66, 76, 1)]}
    f['sink'] = 2
    f['fx'] = [('dust', dict(x=41, y=105, stage=1)), ('dust', dict(x=84, y=105, stage=1, flip=True)),
               ('px', dict(pts=[(36, 101, 'T'), (35, 100, 'T'), (89, 101, 'T'), (90, 100, 'T')]))]
    F['jump_E_land'] = f
    return F
