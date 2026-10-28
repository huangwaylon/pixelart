"""slash_SE k0..k3 (S5 r3) on the h4 rigs (S3 r3 cels) + lock3 head stamps. Acting refs: Gemini pixel-native keys
hybrid/S5_pixelnative/r3/pose/slash_SE_k{0,2,3}.png (+ r2 k1). Coordinates are PRE-SHIFT rig coords
(turn_SE SHIFT -1, turn_E SHIFT +1); FX geometry (fxpass.py) is in FINAL cell coords.
Cut: two-handed, coil over her RIGHT (near, viewer-left) shoulder with the torso turned one step to E (twist away),
sweep DOWN through the front of the legs, impact at chest height viewer-right, LOW recovery (blade ~30 deg below
horizontal) with the body settling over the lead knee.
Blade-tip circle (final coords): C=(65,54) r=36; tip angles k0 ~174, k1 ~57, k2 ~27; k3 leaves the circle on the
lower recovery arc (centre (75,80) r 24, -20 -> 29 deg)."""
import sys
sys.path.insert(0, '/Users/waylonhuang/Documents/other/pixelart/swordswoman/tools/hybrid/h4')
import ribbons as RB
sys.path.insert(0, '/Users/waylonhuang/Documents/other/pixelart/swordswoman/tools/hybrid/s5r3/anims')
from s5c import torso_split, torso_bands
MS = [220, 50, 180, 260]
C, R = (65, 54), 36

# k0 hand pixels (final coords, x0=44 y0=71): two fists stacked on the hilt behind the nape (near fist at the guard),
# far forearm + far sleeve pulled ACROSS the chest toward the grip, near forearm dropping from the grip into the
# big near bell sleeve that drapes down behind the hip (the coil silhouette of the Gemini k0 ref).
K0_ARMS = [
 #45 47 49 51 53 55 57 59
 "KKKKKKK_____________",   # 71
 "sSsKSsK_____________",   # 72
 "sssmssKdRK__________",   # 73   hilt pommel peeks right of the far fist
 "msmKmsmKKKKKKKK_____",   # 74
 "KsKKKssssssssCK_____",   # 75   far forearm runs right across the chest
 "KsmKKKKKCCRRRRRK____",   # 76   far sleeve (bell opens at the wrist, left)
 "_KssKvvRRRRRRRrK____",   # 77
 "_KKsmKvrRRRRrrK_____",   # 78
 "_KCKsKKKKKCRRK______",   # 79   near forearm drops into the near sleeve; near shoulder band
 "KCCRKsmKCRRRrK______",   # 80
 "KCRRRKsKRRRRrK______",   # 81
 "CCRRRRKKRRRRrK______",   # 82
 "CRRRRRRRRRRrrK______",   # 83
 "CRRRRRRRRRrrK_______",   # 84
 "CRRRRRRRRrrrK_______",   # 85
 "KvrRRRRrrrrK________",   # 86
 "KvvvrrvvvvK_________",   # 87
 "_KKKKKKKKK__________",   # 88
]

def frames():
    F = {}
    # ---------------- k0 COIL: one direction step toward E (twist away from the target), hips down 2, torso
    # sheared 4 px back (away from the swing), near (sword) shoulder pulled back, far sleeve pulled across the chest,
    # both fists by the back of the neck, blade back over the shoulder. Head: lock3 squash + tilt-back, glare.
    F['slash_SE_k0'] = dict(
        base='turn_E', head=(-5, 2), expr='glare', act=('squash', 'back'), tilt=0, bow=(1, 0), sink=0,
        replace={'torso': torso_bands('turn_E', [(76, (-4, 2)), (78, (-3, 2)), (200, (-2, 2))])}, move=[('ribbon', 'back')],
        pose=dict(body=(-1, 2), torso=(0, 0), collar=(-4, 2),
                  skirt=dict(tw=12, tips=[(46, 97), (52, 100), (61, 100), (69, 97)], sway=-1),
                  tail=dict(tw=13, tips=[(42, 102), (60, 99)]),
                  legs=[((56, 95), (52, 98), (51, 101), 'e', 0)],
                  legF=[((62, 95), (68, 98), (71, 101), 'e', 0)],
                  armN=None, armF=None,
                  katana=(45, 74, 198.435, 19, -1), kat_layer='front',
                  ribbon=RB.path((54, 76), 'trail_in', 1)),
        patch=[(45, 71, K0_ARMS, 'over'), (44, 80, ['K', 'K', 'K', 'K', 'K', 'K', '_'], 'behind')],
        meta=dict(key='coil', ms=220))
    # ---------------- k1 SMEAR: whip through to SE, lunge starts (front foot slides, back heel lifts), both fists
    # low in front, blade foreshortened at the lead of the arc; head leans 2 px into the swing.
    F['slash_SE_k1'] = dict(
        base='turn_SE', head=(5, 3), expr='wide', act=None, tilt=1, bow=(-2, 0), drop=('armL', 'armR'), move=[('ribbonN', 'back'), ('ribbonF', 'back')],
        replace={'torso': torso_bands('turn_SE', [(76, (3, 3)), (78, (3, 3)), (200, (2, 3))])},
        pose=dict(body=(1, 3), torso=(2, 0), collar=(3, 3),
                  skirt=dict(tw=15, tips=[(48, 97), (55, 100), (67, 100), (78, 96)], sway=2),
                  tail=dict(tw=20, tips=[(42, 101), (80, 99)]),
                  legs=[((59, 96), (54, 99), (50, 101), 'heelup', -1), ((68, 96), (75, 99), (79, 101), 'se', 0)],
                  armN=dict(upper=((60, 79), (64, 82)), cuff=((62, 81), (67, 85), 3, 8), hand=None),
                  armF=dict(upper=((74, 78), (72, 82)), cuff=((73, 80), (71, 84), 3, 6)),
                  katana=(78, 85, 18.435, 11, 1), kat_layer='front',
                  ribbonN=RB.path((60, 78), 'trail_out', -1), ribbonF=RB.path((73, 77), 'trail_in', 1)),
        patch=[('spec', '@limb 74,78,2.0 75,83,1.6 tone=redsh'),
               ('spec', '@limb 57,78,3.4 65,82,2.8 72,84,2.2 tone=red'),
               (56, 77, ['_u', 'uu'], 'over'),
               (71, 82, ['_KKKK_', 'KsSssK', 'KssmsK', 'KmsmK_', '_KKK__'], 'over')],
        meta=dict(key='smear', ms=50))
    # ---------------- k2 IMPACT (hit-stop): WIDE lunge, front (viewer-right) knee bent over the toe, back leg long
    # with the heel lifted, torso pitched forward, head forward-down 2, both arms driving out from the shoulder to
    # the fists, blade level-ish at chest height (tip on the arc end). Gritted mouth.
    F['slash_SE_k2'] = dict(
        base='turn_SE', head=(8, 7), expr='grit', act='down', tilt=1, bow=(-2, 1), drop=('armL', 'armR'), move=[('ribbonN', 'back'), ('ribbonF', 'back')],
        replace={'torso': torso_bands('turn_SE', [(76, (6, 5)), (78, (5, 5)), (200, (4, 4))])},
        pose=dict(body=(3, 4), torso=(3, 1), collar=(6, 5),
                  skirt=dict(tw=16, tips=[(48, 98), (56, 101), (70, 100), (82, 96)], sway=3),
                  tail=dict(tw=20, tips=[(40, 101), (84, 99)]),
                  legs=[((60, 97), (51, 100), (43, 101), 'heelup', -1), ((71, 97), (80, 98), (83, 101), 'se', 0)],
                  armN=dict(upper=((66, 79), (73, 79)), cuff=((70, 79), (79, 78), 3, 7), hand=None),
                  armF=dict(upper=((76, 78), (80, 78)), cuff=((77, 78), (81, 77), 3, 5)),
                  katana=(84, 77, -18.435, 19, 1), kat_layer='front',
                  ribbonN=RB.path((62, 80), 'trail_out', -1, sy=0.8), ribbonF=RB.path((76, 79), 'trail_out', 1, sy=0.6)),
        patch=[('spec', '@limb 77,80,2.0 80,79,1.5 tone=skinsh'),
               ('spec', '@limb 60,80,3.2 70,79,2.6 tone=red'),
               ('spec', '@limb 70,79,1.6 80,78,1.4 tone=skin'),
               (61, 79, ['u', 'u'], 'over'),
               (79, 75, ['_KKKK_', 'KsSssK', 'KssmsK', 'KmssK_', '_KKK__'], 'over')],
        meta=dict(key='impact', ms=180, hitstop=True))
    # ---------------- k3 FOLLOW-THROUGH: LOW recovery, blade low and across (+26.6 deg, below horizontal), body
    # settles forward over the lead knee with 1 px downward overshoot; ribbons trail behind the arm (S-curve).
    F['slash_SE_k3'] = dict(
        base='turn_SE', head=(6, 6), expr='glare', act=None, tilt=1, bow=(1, 1), drop=('armL', 'armR'), move=[('ribbonN', 'back'), ('ribbonF', 'back')],
        replace={'torso': torso_bands('turn_SE', [(76, (5, 5)), (78, (5, 5)), (200, (4, 5))])},
        pose=dict(body=(3, 5), torso=(2, 1), collar=(5, 5),
                  skirt=dict(tw=16, tips=[(49, 98), (57, 101), (70, 100), (81, 97)], sway=1),
                  tail=dict(tw=20, tips=[(42, 101), (82, 99)]),
                  legs=[((61, 97), (53, 100), (46, 101), 'heelup', -1), ((71, 97), (79, 98), (82, 101), 'se', 0)],
                  armN=dict(upper=((65, 80), (70, 84)), cuff=((68, 82), (75, 86), 3, 7), hand=None),
                  armF=dict(upper=((76, 79), (77, 83)), cuff=((76, 81), (78, 85), 3, 5)),
                  katana=(80, 86, 26.565, 18, 1), kat_layer='front',
                  ribbonN=RB.path((62, 81), 'swing_mid', -1), ribbonF=RB.path((75, 80), 'trail_in', 1, sx=0.6)),
        patch=[('spec', '@limb 75,80,2.0 77,84,1.5 tone=skinsh'),
               ('spec', '@limb 59,80,3.2 68,84,2.6 tone=red'),
               ('spec', '@limb 68,84,1.6 76,86,1.4 tone=skin'),
               (60, 79, ['u', 'u'], 'over'),
               (75, 83, ['_KKKK_', 'KsSssK', 'KssmsK', 'KmssK_', '_KKK__'], 'over')],
        meta=dict(key='follow', ms=260))
    return F
