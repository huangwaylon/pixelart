# slash_SE k0..k3 (ANIM_DIRECTION 5.5: k0 COIL held, k1 SMEAR 40 ms, k2 IMPACT + hit-stop, k3 FOLLOW-THROUGH).
# Horizontal two-handed cut from her RIGHT (viewer left, behind) across the front (toward the camera) to her LEFT
# (viewer right). Pose traced from the S5 r1 slash acting (k0 wide coil, blade back over the right shoulder; k2 long
# lunge, blade level) and the S2 overhead coil; built on the turn_SE rig + lock2 head + smear kit + secondary.py.
import sys
sys.path.insert(0, 'tools/hybrid/anim')
import secondary as S2

# drag = direction the cloth trails (against the body / blade velocity)
DRAG0 = [(4.0, -1.0), (-5.0, -1.0), (-7.0, 0.0), (0.0, 0.0)]
DRAG = S2.with_overshoot(DRAG0, os=0.55)        # k3: overshoot PAST rest to the right (+3.9 px), S-curve
# cut-plane ellipse (chest height), shared by k1 arc / k2 sliver / k3 wisps
ARC = dict(cx=70, cy=82, rx=34, ry=15)
A0, A1 = 200, 6                                   # tail (k0 side, behind upper-left) -> lead (short of the k2 tip)


def arm(sh, el, hand, flare, cuffw=(4, 8)):
    return dict(upper=(sh, el), cuff=(el, flare, cuffw[0], cuffw[1]), hand=hand)


def rib(k, rootN, rootF, ampN=8, ampF=6):
    rN = S2.ribbon(rootN, [(-3, 2), (-3, 2), (-3, 2), (-2, 3), (-2, 3), (-1, 3)], DRAG, k, False, tip_amp=ampN, wave=1.5)
    rF = S2.ribbon(rootF, [(4, 2), (3, 2), (3, 3), (1, 3), (1, 3)], DRAG, k, False, tip_amp=ampF, wave=1.0)
    return rN, rF


FRAMES = {}

# ---- k0 COIL: weight sinks onto the back (near, her right) leg, hips back 3 px, -6 % h / +4 % w, torso twisted
#      back to her right, two-hand grip over the right shoulder (clear of the head), blade tip up-back, glare,
#      head tilted, cloth trails to her left (viewer right).
bx, by = -3, 3
rN, rF = rib(0, (58 + bx, 75 + by), (71 + bx, 74 + by))
FRAMES['slash_SE_k0'] = dict(
    base='turn_SE', head=(-2, 3), tilt=-1, bow=(1, 0), expr='glare',
    pose=dict(
        body=(bx, by), torso=(-1, 0), collar=(bx - 1, by),
        skirt=dict(tips=[(47, 95), (53, 98), (64, 98), (76, 95)], sway=2, slit=(63, 88, 2, 2)),
        tail=dict(tips=[(44, 100), (78, 98)]),
        legs=[((58, 96), (55, 99), (54, 101), 'se', 0), ((66, 96), (71, 98), (74, 101), 'sef', 0)],
        armN=dict(upper=((53, 77), (50, 81)), cuff=None, sleeve=((51, 82), (48, 76), (-4, 8), 4), hand=(46, 75)),
        armF=dict(upper=((69, 77), (62, 80)), cuff=None, sleeve=((62, 80), (54, 77), (0, 8), 4), hand=None),
        katana=(49, 75, 206.6, 21, -1), kat_layer='front',
        ribbonN=rN, ribbonF=rF,
    ),
)

# ---- k1 SMEAR: half unwound, lunge starts (front foot slides 2 px, back heel lifts), blade at mid-arc in the
#      leading third, FULL arc smear coil -> near impact (far half behind, near half over the body), the sleeves
#      dragged back along the arc as one stretched red shape + a pink_0 hand echo, eyes snap wide.
bx, by = 0, 2
rN, rF = rib(1, (58 + bx, 75 + by), (71 + bx, 74 + by))
FRAMES['slash_SE_k1'] = dict(
    base='turn_SE', head=(0, 2), bow=(-1, 0), expr='wide',
    pose=dict(
        body=(bx, by), torso=(0, 0),
        skirt=dict(tips=[(49, 95), (56, 98), (68, 98), (79, 95)], sway=-1),
        tail=dict(tips=[(43, 100), (79, 98)]),
        legs=[((61, 95), (58, 98), (55, 101), 'heelup', 0), ((69, 95), (73, 98), (76, 101), 'sef', 0)],
        armN=dict(upper=((57, 78), (64, 84)), cuff=None, sleeve=((63, 83), (72, 87), (-9, 5), 4), hand=(72, 86)),
        armF=dict(upper=((73, 77), (75, 82)), cuff=None, sleeve=((75, 82), (75, 87), (-5, 3), 3), hand=None),
        katana=(76, 88, 18.4, 21, 1), kat_layer='front',
        ribbonN=rN, ribbonF=rF,
    ),
    fx=[('limb', dict(path=[(68, 86), (61, 84), (54, 81), (48, 78)], w0=5, w1=1.5, tones='Rrv', hand=(62, 85),
                      mode='behind', ol_lead=False)),
        ('arc', dict(**ARC, a0=A0, a1=A1, lead=6, cap=7, front='lower', echo=True))],
)

# ---- k2 IMPACT (hit-stop hold): full lunge +14 % w, back heel up, front knee over the toe, hips low, head dipped
#      2 px, elbows bent so the corset reads, blade level and crisp at the far end, thin pink sliver behind it,
#      steel_2 spark star + burst ticks at the tip, kiai.
bx, by = 4, 3
rN, rF = rib(2, (58 + bx, 75 + by), (71 + bx, 74 + by))
FRAMES['slash_SE_k2'] = dict(
    base='turn_SE', head=(4, 5), bow=(-1, 0), expr='kiai',
    pose=dict(
        body=(bx, by), torso=(1, 0), collar=(bx + 1, by + 1),
        skirt=dict(tips=[(52, 96), (59, 99), (74, 99), (85, 95)], sway=-2, slit=(67, 88, 3, 2)),
        tail=dict(tips=[(45, 101), (83, 98)]),
        legs=[((65, 96), (59, 99), (53, 101), 'heelup', 0), ((73, 96), (79, 97), (80, 101), 'sef', 0)],
        armN=dict(upper=((61, 79), (68, 84)), cuff=None, sleeve=((67, 84), (78, 86), (-8, 6), 4), hand=(79, 85)),
        armF=dict(upper=((77, 78), (80, 82)), cuff=None, sleeve=((80, 82), (81, 85), (-4, 5), 3), hand=None),
        katana=(83, 85, 0, 21, 1), kat_layer='front',
        ribbonN=rN, ribbonF=rF,
    ),
    fx=[('sliver', dict(**ARC, a0=A0, a1=A1 - 4, keep=0.30, thick=2, front='lower')),
        ('spark', dict(x=105, y=85, r=3))],
)

# ---- k3 FOLLOW-THROUGH: front foot planted, hips low, the blade carries past and drops on a LOWER recovery arc
#      (1 px downward overshoot), chest overshoots ahead of the hips, ribbons + tail swing 3+ px past rest as an
#      S-curve (root reversed, tip still trailing), pink wisps at the arc tail only.
bx, by = 3, 3
rN, rF = rib(3, (58 + bx, 75 + by), (71 + bx, 74 + by), ampN=9, ampF=7)
FRAMES['slash_SE_k3'] = dict(
    base='turn_SE', head=(4, 3), bow=(2, 1), expr='glare',
    pose=dict(
        body=(bx, by), torso=(2, 0), collar=(bx + 1, by),
        skirt=dict(tips=[(51, 95), (58, 98), (72, 98), (83, 96)], sway=3, slit=(66, 88, 2, 2)),
        tail=dict(tips=[(49, 101), (84, 100)]),
        legs=[((64, 95), (59, 99), (55, 101), 'heelup', 0), ((72, 95), (78, 97), (79, 101), 'sef', 0)],
        armN=dict(upper=((60, 79), (69, 85)), cuff=None, sleeve=((68, 85), (80, 88), (5, 6), 4), hand=(81, 88)),
        armF=dict(upper=((76, 78), (80, 83)), cuff=None, sleeve=((80, 83), (82, 87), (5, 4), 3), hand=None),
        katana=(84, 89, 18.4, 21, 1), kat_layer='front',
        ribbonN=rN, ribbonF=rF,
    ),
    fx=[('wisps', dict(pts=[[(44, 79), (40, 78), (37, 76), (37, 74), (39, 73)]]))],
)
