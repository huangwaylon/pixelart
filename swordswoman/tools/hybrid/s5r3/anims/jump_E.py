"""jump_E crouch / apex / land (S5 r3) on the h4 turn_E rig (S3 r3 cels) + lock3 head stamps. PRE-SHIFT rig coords
(turn_E SHIFT +1); patches are FINAL coords. Acting refs: S5 r2 Gemini keys (pose/jump_E_*_r2.png) + r3 apex.
crouch: knees forward, torso pitched down (stepped integer lean, cels untouched), bell skirt, collar on.
apex: the whole body drawn 10 px above the foot baseline (air_px 10; the ground shadow stays on the ground row in the
      GIF), stretched vs the crouch, knees tucked, hem trailing 1-2 rows, arms + sword flung up (sleeves on the
      shoulder).
land: squash in the legs + bell (head NOT sunk: the closed-eye line sits on turn_E's eye row 65), dust at the feet."""
import sys
sys.path.insert(0, '/Users/waylonhuang/Documents/other/pixelart/swordswoman/tools/hybrid/h4')
import ribbons as RB
sys.path.insert(0, '/Users/waylonhuang/Documents/other/pixelart/swordswoman/tools/hybrid/s5r3/anims')
from s5c import torso_bands
MS = [160, 220, 200]
AIR = 10

def frames():
    F = {}
    F['jump_E_crouch'] = dict(
        base='turn_E', head=(4, 7), expr='glare', act='down', tilt=1, bow=(-1, -1),
        replace={'torso': torso_bands('turn_E', [(76, (3, 6)), (78, (2, 6)), (200, (1, 5))])},
        move=[('ribbon', 'back')],
        pose=dict(body=(0, 5), collar=(3, 6),
                  skirt=dict(tw=13, tips=[(45, 100), (52, 102), (61, 102), (69, 99)], sway=-1),
                  tail=dict(tw=14, tips=[(41, 102), (58, 100)]),
                  legs=[((60, 97), (68, 98), (63, 101), 'e', 0)],
                  legF=[((63, 96), (71, 97), (67, 101), 'e', 0)],
                  armN=dict(upper=((62, 81), (57, 85)), cuff=((59, 82), (50, 87), 3, 8), hand=(47, 86)),
                  katana=(49, 88, 198.435, 19, -1), kat_layer='mid',
                  ribbon=RB.path((60, 81), 'trail_in', -1, sy=0.7)),
        meta=dict(key='crouch', ms=160))
    F['jump_E_apex'] = dict(
        base='turn_E', head=(1, -1 - AIR), expr='smile', act='back', tilt=-1, bow=(-1, 1),
        replace={'torso': torso_bands('turn_E', [(76, (0, -AIR)), (78, (0, -AIR)), (200, (0, -AIR))])},
        move=[('ribbon', 'back')],
        pose=dict(body=(0, 1 - AIR), collar=(0, -AIR),
                  skirt=dict(top=82 - AIR + 1, tw=10, tips=[(51, 96 - AIR + 2), (56, 98 - AIR + 2), (63, 98 - AIR + 2), (69, 95 - AIR + 2)], sway=-1),
                  tail=dict(top=84 - AIR + 1, tw=11, tips=[(44, 100 - AIR + 1), (59, 97 - AIR + 1)]),
                  legs=[((60, 93 - AIR + 2), (65, 95 - AIR), (60, 98 - AIR), 'etoe', 0)],
                  legF=[((64, 93 - AIR + 2), (70, 93 - AIR), (67, 96 - AIR), 'etoe', 0)],
                  armN=dict(upper=((62, 76 - AIR), (71, 66 - AIR)), cuff=((63, 75 - AIR), (71, 68 - AIR), 3, 7), hand=None),
                  katana=(77, 59 - AIR, -63.435, 20, 1), kat_layer='front',
                  extra={'fore': ('after:armN', f'@limb 70,{66 - AIR},1.4 76,{60 - AIR},1.3 tone=skin')},
                  ribbon=RB.path((58, 74 - AIR), 'float', -1)),
        meta=dict(key='apex', ms=220, air_px=AIR))
    F['jump_E_land'] = dict(
        base='turn_E', head=(1, 6), expr='closed', act='squash', tilt=0, bow=(0, 2),
        replace={'torso': torso_bands('turn_E', [(76, (1, 6)), (78, (1, 6)), (200, (1, 6))])},
        move=[('ribbon', 'back')],
        pose=dict(body=(0, 6), collar=(1, 6),
                  skirt=dict(tw=15, top=81, tips=[(42, 102), (49, 104), (65, 104), (76, 101)], slope=0.55, sway=0),
                  tail=dict(tw=16, top=83, tips=[(38, 103), (68, 102)]),
                  legs=[((58, 99), (54, 101), (55, 101), 'e', 0)],
                  legF=[((65, 99), (70, 100), (70, 101), 'e', 0)],
                  armN=dict(upper=((62, 85), (67, 88)), cuff=((64, 86), (73, 90), 3, 8), hand=(74, 89)),
                  katana=(76, 91, 18.435, 17, 1), kat_layer='front',
                  ribbon=RB.path((60, 82), 'trail_in', -1, sy=0.6)),
        meta=dict(key='land', ms=200))
    return F
