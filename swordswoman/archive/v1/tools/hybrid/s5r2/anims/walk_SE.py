"""walk_SE k0..k3 = contact / down / passing / up RETRACE (S5 r2) on the S3 r2 SE rig.
k2 PASSING acting = Gemini pixel-native a1 (pose/walk_SE_k2.png: planted far leg under her, near knee lifted and
passing, free arm swinging, katana swinging back); k0 / k1 / k3 are Claude in-betweens built around it (the brief has
Gemini act only the passing key). Travel = screen down-right. Near leg = her RIGHT (viewer-left), far = her LEFT.
Bounce body dy +1 / +3 / +1 / -1 (4 px crown range + 1 px head lag), free-arm cuff swing 5 px, katana pendulum
26.6 deg lagging the arm, stride 8 px, ribbons from the follow-through driver (travelling wave, loop)."""
import sys
sys.path.insert(0, '/Users/waylonhuang/Documents/other/pixelart/swordswoman/archive/v1/tools/hybrid/s5r2')
import secondary as SEC
MS = [140, 110, 140, 110]
B = [1, 3, 1, -2]
HEAD = [(0, -2), (0, 1), (0, 3), (0, 1)]           # = the body bounce one key late (head lags the hips)
LEAN = [(1, 0), (1, 1), (0, 0), (-1, 0)]           # torso twist with the stride
LEGS = [
    [((61, 93), (59, 97), (57, 100), 'heelup', -1), ((69, 93), (71, 97), (73, 101), 'se', 0)],   # contact
    [((61, 95), (59, 98), (57, 100), 'heelup', -1), ((69, 95), (72, 98), (72, 101), 'se', 0)],   # down
    [((61, 93), (63, 96), (61, 98), 'toe', 0), ((69, 93), (69, 97), (68, 101), 'se', 0)],        # passing (Gemini)
    [((61, 91), (63, 94), (64, 97), 'se', 0), ((69, 91), (68, 96), (67, 100), 'sef', 0)],        # up
]
CUFFN = [(58, 90), (57, 91), (54, 90), (50, 88)]   # free (near) arm: forward with the far leg, back on 'up'
KAT = [(78, 90, 71.6), (79, 90, 63.4), (78, 90, 45.0), (76, 90, 63.4)]   # far-hand katana pendulum (lags 1 key)
SKIRT_SWAY = [0, 1, -1, 0]
TAILT = [[(46, 101), (79, 99)], [(45, 102), (79, 100)], [(44, 100), (80, 98)], [(46, 100), (79, 99)]]

BOWW = [(0, 1), (1, 0), (0, -0), (-1, 0)]   # bow lags the head 1 key (drops after the low, swings with the twist)
def ribbons():
    rN = [(58 + LEAN[k][0], 75 + B[k]) for k in range(4)]
    rF = [(71 + LEAN[k][0], 74 + B[k]) for k in range(4)]
    virt = [(4 * k, 2 * k + B[k] * 2) for k in range(4)]
    # loop: the 4th->1st step continues the travel; express it as velocity with loop=True by unwrapping
    vN = SEC.chain(rN, virt, rest_dir=(-0.5, 1.0), nodes=8, seg=2.0, amp=0.09, lags=(0.8, 2.5), loop=False)
    vF = SEC.chain(rF, virt, rest_dir=(0.45, 1.0), nodes=6, seg=2.0, amp=0.09, lags=(0.8, 2.2), loop=False)
    return vN, vF

def frames():
    RN, RF = ribbons(); F = {}
    for k in range(4):
        bx, by = 0, B[k]
        c1 = CUFFN[k]
        pose = dict(body=(bx, by), torso=LEAN[k],
                    skirt=dict(sway=SKIRT_SWAY[k]), tail=dict(tips=TAILT[k]),
                    legs=LEGS[k],
                    armN=dict(cuff=((55.5 + LEAN[k][0], 76 + by), (c1[0], c1[1] + by - 1), 5, 10),
                              hand=(c1[0] - 1, c1[1] + by - 1), upper=None),
                    armF=dict(cuff=((73 + LEAN[k][0], 78 + by), (75, 89 + by), 4, 8), upper=((72, 75 + by), (73, 79 + by))),
                    katana=(KAT[k][0], KAT[k][1] + by - 1, KAT[k][2], 21, 1),
                    ribbonN=SEC.ints(RN[k]), ribbonF=SEC.ints(RF[k]))
        F[f'walk_SE_k{k}'] = dict(base='turn_SE', pose=pose, head=HEAD[k], bow=BOWW[k], expr='calm',
                                  xf={'torso': [('sh', 70, 86, LEAN[k][0])]})
    return F
