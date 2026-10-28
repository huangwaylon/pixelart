# walk_SE k0..k3 = contact(L leads) / down / passing / up, built on cels/turn_SE.cel (hand-placed legs, ribbons, katana).
# bounce (body dy): +1 / +3 / +1 / -1 (4 px range, ANIM_DIRECTION 5.2); head lags 1 f (half step), bun+bow lag 2 f.
# far leg = her LEFT (viewer right); near leg = her RIGHT (viewer left). Forward = screen down-right.
B = [1, 3, 1, -1]
HEAD = [-1, 1, 3, 1]   # = body bounce of the previous key (1 f lag), 4 px range
BOW = [(0, 0), (0, -1), (0, 0), (0, 1)]
ARM_N = [(1, 0), (1, 1), (0, 0), (-1, 0)]      # free arm swings opposite the legs, cuff 1 f behind
ARM_F = [(-1, 0), (-1, 0), (0, 0), (1, 0)]     # sword arm, smaller swing
ANG = [44, 46, 50, 48]                          # blade angle swings 2 f behind the arm
TAIL = [(0, 0), (0, 0), (-1, -2), (0, 1)]       # skirt back tail lifts the frame after down, drops on up
LEGS = [
 # k0 contact: far (L) leg forward heel-strike, near (R) leg back rolling onto the toe
 """@limb 67,90,2.6 69,96,2.3 71,100,1.8
@foot se 69,101
@limb 60,91,2.6 59,96,2.3 58,99,1.8
@foot toe 56,99""",
 # k1 down: front foot planted, knee bent (lowest), back foot peeling off
 """@limb 67,92,2.6 70,97,2.3 70,100,1.8
@foot se 68,101
@limb 60,93,2.6 58,97,2.3 57,99,1.8
@foot toe 55,99""",
 # k2 passing: stance far leg under the body, near swing foot lifted 3 px, knee forward
 """@limb 66,90,2.6 67,96,2.3 66,100,1.8
@foot se 64,101
@limb 60,91,2.6 62,95,2.3 60,98,1.8
@foot toe 58,97""",
 # k3 up: stance leg straight on the ball of the foot (highest), near leg swinging forward
 """@limb 66,88,2.6 66,94,2.3 66,99,1.8
@foot sef 64,100
@limb 60,89,2.6 63,93,2.3 63,97,1.8
@foot se 61,97""",
]
RIB = [   # trailing back (up-left, against the down-right travel) + gravity; travelling wave root -> tip
 ("54,76 50,78 47,81 45,85 45,89 46,92", "73,76 76,78 78,82 78,86"),
 ("54,78 50,79 47,82 44,85 43,89 43,92", "73,78 76,80 79,83 79,87"),
 ("54,76 50,77 46,79 43,83 42,87 42,90", "73,76 76,78 79,81 80,85"),
 ("54,74 50,76 47,80 46,84 46,88 47,91", "73,74 76,76 78,80 79,84"),
]
FRAMES = {}
for k in range(4):
    b = B[k]
    an, af = ARM_N[k], ARM_F[k]
    FRAMES[f'walk_SE_k{k}'] = dict(
        base='turn_SE.cel',
        replace={'legs': LEGS[k],
                 'ribbons': f"@ribbon {RIB[k][0]} side=1\n@ribbon {RIB[k][1]} side=-1",
                 'katana': f"@katana {73 + af[0]},{89 + b + af[1]} {ANG[k]} 22".replace(',', ' ', 1).replace(',', ' ')},
        off={'skirt': (0, b), 'skirttail': (TAIL[k][0], b + TAIL[k][1]), 'torso': (0, b),
             'sleeveN': (an[0], b + an[1]), 'sleeveF': (af[0], b + af[1])},
        head=(0, HEAD[k]), bow=BOW[k], expr='calm')
