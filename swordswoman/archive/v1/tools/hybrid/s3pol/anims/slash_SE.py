# slash_SE k0..k3 (ANIM_DIRECTION 5.5: k0 COIL held, k1 SMEAR 40 ms, k2 IMPACT + hit-stop, k3 FOLLOW-THROUGH).
# Built on cels/turn_SE.cel: the body cels move as units (weight shift / lunge), arms, sleeves, legs, katana and
# ribbons are hand-placed per key. Horizontal two-handed cut from her RIGHT (viewer left, behind) across the front
# (toward the camera) to her LEFT (viewer right). Arc = cut-plane ellipse ry = 0.5 rx (smears.json SE).
def arm(sh, el, ha, cuff_end, cuff_r=3.2, upper_r=1.6):
    """skin upper arm shoulder->elbow, detached flared sleeve elbow->cuff (droops), hand at ha"""
    return (f"@limb {sh[0]},{sh[1]},{upper_r} {el[0]},{el[1]},{upper_r}\n"
            f"@limb {el[0]},{el[1]},1.8 {cuff_end[0]},{cuff_end[1]},{cuff_r} tone=red\n"
            f"@limb {ha[0]},{ha[1]},1.2 {ha[0]},{ha[1]},1.2")
COMMON_DROP = ('sleeveN', 'sleeveF')
FRAMES = {
 # ---- k0 COIL: weight sinks onto the back (near, her right) leg, torso twisted back to her right (viewer left),
 #      blade raised up-back over her right shoulder (clear of the head), glare, secondaries trail to her left.
 'slash_SE_k0': dict(
    base='turn_SE.cel', drop=COMMON_DROP,
    off={'skirt': (-1, 2), 'skirttail': (-1, 2), 'torso': (-2, 2)},
    head=(-2, 3), bow=(1, 0), expr='glare',
    replace={
      'legs': """@limb 59,92,2.6 55,97,2.4 55,100,1.8
@foot se 53,101
@limb 66,92,2.5 70,97,2.2 73,100,1.7
@foot sef 71,101""",
      'ribbons': "@ribbon 70,78 75,78 79,79 83,81 86,84 88,87 side=-1\n@ribbon 69,80 73,81 77,83 80,86 82,89 side=-1",
      'katana': "@katana 49 80 214 24 hook=-1"},
    insert=[('before:katana', 'armF', arm((68, 80), (61, 84), (51, 81), (56, 87), 2.8)),
            ('before:katana', 'armN', arm((54, 80), (48, 85), (49, 80), (46, 89), 3.0))],
    ops=[]),
 # ---- k1 SMEAR: half unwound, lunge starts (front foot slides 2 px, back heel lifts), blade straight ahead at
 #      mid-arc, FULL arc smear coil -> near impact (behind on the far side, over the body on the near/front side),
 #      sleeves elongated into one red streak toward the coil side + near-hand echo, eyes snap wide.
 'slash_SE_k1': dict(
    base='turn_SE.cel', drop=COMMON_DROP,
    off={'skirt': (0, 2), 'skirttail': (-1, 1), 'torso': (0, 2)},
    head=(0, 2), bow=(-1, 0), expr='wide',
    replace={
      'legs': """@limb 60,92,2.6 57,97,2.4 56,100,1.8
@foot toe 54,100
@limb 67,92,2.5 71,97,2.2 75,100,1.7
@foot se 73,101""",
      'ribbons': "@ribbon 55,78 51,77 47,77 43,78 40,80 37,83 side=1\n@ribbon 72,78 70,76 66,75 side=-1",
      'katana': "@katana 69 90 31 22"},
    insert=[('before:katana', 'armN', arm((56, 80), (61, 88), (67, 90), (64, 91), 3.0)),
            ('before:armN', 'armF', arm((71, 80), (73, 86), (69, 89), (71, 90), 2.6)),
            ('before:armF', 'sleevesmear', "@limb 47,84,1.2 55,88,2.2 61,90,2.6 tone=red")],
    ops=["smear 72,90 32,16 -168 -354 5 tones=w,P,p taper=lead grow=in",
         "smear 72,90 32,16 -195 -340 5 tones=w,P,p taper=lead grow=in over",
         "cluster 61,93 s XX/XX"]),
 # ---- k2 IMPACT (hit-stop): full lunge, blade crisp at the far end of the arc, thin pink sliver behind it,
 #      steel_2 hit star at the tip, ribbons whip (S-curve), frown.
 'slash_SE_k2': dict(
    base='turn_SE.cel', drop=COMMON_DROP,
    off={'skirt': (2, 3), 'skirttail': (1, 2), 'torso': (2, 3)},
    head=(2, 3), bow=(-1, 1), expr='frown',
    replace={
      'legs': """@limb 62,93,2.6 56,98,2.3 51,100,1.8
@foot toe 49,100
@limb 69,93,2.6 75,97,2.3 79,100,1.8
@foot se 77,101""",
      'ribbons': "@ribbon 57,79 53,77 49,77 46,79 43,81 39,81 side=1\n@ribbon 75,79 78,77 81,77 side=-1",
      'katana': "@katana 80 86 -8 25"},
    insert=[('before:katana', 'armF', arm((73, 81), (77, 84), (79, 86), (79, 88), 2.6)),
            ('before:katana', 'armN', arm((58, 81), (68, 85), (78, 87), (72, 90), 3.2))],
    ops=["smear 72,90 30,15 40 -14 2 tones=P,p taper=lead grow=in",
         "stamp 102,83 P..w..P/...w.../..www../wwwwwww/..www../...w.../P..w..P"]),
 # ---- k3 FOLLOW-THROUGH: blade carries past up to her left-back, chest overshoots ahead of the hips,
 #      cuffs flare, ribbons overshoot out to the right, pink wisps at the arc tail only.
 'slash_SE_k3': dict(
    base='turn_SE.cel', drop=COMMON_DROP,
    off={'skirt': (2, 2), 'skirttail': (3, 1), 'torso': (4, 2)},
    head=(3, 2), bow=(2, -1), expr='frown',
    replace={
      'legs': """@limb 62,92,2.6 57,97,2.3 52,100,1.8
@foot toe 50,100
@limb 69,92,2.6 74,97,2.3 78,100,1.8
@foot se 76,101""",
      'ribbons': "@ribbon 77,78 81,78 85,80 88,83 90,87 91,91 side=-1\n@ribbon 76,80 80,81 83,84 85,88 side=-1",
      'katana': "@katana 83 80 -38 24"},
    insert=[('before:katana', 'armF', arm((76, 80), (80, 79), (82, 80), (84, 84), 2.6)),
            ('before:katana', 'armN', arm((60, 80), (71, 82), (81, 81), (76, 88), 3.4))],
    ops=["curve 101,60 105,56 109,58 p", "curve 105,66 109,64 111,67 p"]),
}
