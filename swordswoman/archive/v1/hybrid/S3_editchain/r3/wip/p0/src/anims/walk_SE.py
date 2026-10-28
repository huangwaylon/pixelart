# walk_SE k0..k3 = walk f0..f3: CONTACT (L heel strikes, forward = down-right), DOWN (weight, knee bent, lowest),
# PASSING (R swings through, foot lifted), UP (stance on the ball of the foot, highest).
# Body driver: cog screen dy [+1, +3, 0, -1] (4 px range, down -4 %, up +2 %); the head and bun lag 1 key, the bow
# 2 keys (secondary.py), ribbons a root->tip travelling wave (tip 3-4 px), skirt front panel flicks with the leading
# knee on down/passing, tail overshoots on k2. Free arm (her right, near) swings opposite to the legs 1 key late
# (cuff >= 3 px); the katana (far hand) is a pendulum 45 -> 63 -> 90 -> 72 deg, 2 keys behind the arm.
import sys
sys.path.insert(0, 'tools/hybrid/anim')
import secondary as S2

COG = [1, 4, 1, -1]                       # body screen dy per key
DX = [0, 1, 1, 0]                         # cog sway over the stance foot
# drag (direction the cloth trails = against the body velocity): walking toward down-right -> trails up-left,
# plus the vertical bounce velocity (falling into k1 -> cloth lifts, rising into k3 -> cloth drops)
DRAG = [(-2.0, 0.5), (-2.0, -2.0), (-2.5, 1.5), (-2.0, 1.0)]

HEAD_DY = [0, 2, 3, -1]                                 # head lags the bounce ~1 key -> crown range 4
BOW = S2.part_offsets(DRAG, True, dict(head=0, bun=0.3, bow=0.5, tail=0.8, cuff=0.6, front=0.5))['bow']

LEGS = [
    # k0 CONTACT: far (L) leg forward heel strike, near (R) leg back on the toe
    [((61, 94), (58, 98), (56, 101), 'heelup', 0), ((69, 94), (71, 98), (72, 101), 'sef', 0)],
    # k1 DOWN: L planted, knee bent forward; R toe pushing off
    [((61, 96), (59, 99), (57, 101), 'heelup', 0), ((69, 96), (72, 98), (71, 101), 'sef', 0)],
    # k2 PASSING: L stance under the body; R swings through, foot lifted 3 px, knee forward
    [((61, 93), (63, 96), (62, 98), 'se', 0), ((69, 93), (68, 97), (68, 101), 'sef', 0)],
    # k3 UP: L straight on the ball of the foot; R reaching forward
    [((61, 92), (64, 96), (66, 100), 'se', 0), ((69, 92), (68, 96), (67, 101), 'heelup', 0)],
]
# near (free) arm cuff end swings opposite the far leg, 1 key late; far arm (katana) small swing
ARMN = [(51.5, 89), (51.5, 90), (54.5, 90), (56.5, 89)]
ARMN0 = [(55.5, 76), (55.5, 76), (55.5, 76), (55.5, 76)]
ARMF = [(77, 88), (76, 89), (75, 89), (74, 88)]
KAT = [26.6, 45, 63.4, 45]      # pendulum 37 deg, tip travel ~13 px, no vertical pop
SWAY = [0, 1, 2, -1]                      # skirt front panel flick
TAIL = [(46, 101), (45, 100), (44, 98), (46, 100)]   # tail tip lags the bounce, overshoots up on k2

FRAMES = {}
for k in range(4):
    bx, by = DX[k], COG[k]
    rN = S2.ribbon((58 + bx, 75 + by), [(-3, 2), (-3, 2), (-2, 3), (0, 3), (-2, 3), (0, 3)], DRAG, k, True,
                   tip_amp=4, wave=1.2)
    rF = S2.ribbon((71 + bx, 74 + by), [(4, 2), (3, 3), (1, 4), (-1, 3), (2, 3)], DRAG, k, True, tip_amp=3, wave=1.0)
    ax, ay = ARMN[k]
    fx, fy = ARMF[k]
    pose = dict(
        body=(bx, by),
        collar=(bx, (by + HEAD_DY[k] + 1) // 2),
        torso=(1 if k in (1, 2) else 0, 0),                    # twist: chest leads toward the stride 1 px
        skirt=dict(sway=SWAY[k],
                   tips=[(51 + (0 if k != 1 else -1), 95 + (0 if k != 1 else 1)), (57, 98), (68 + (1 if k == 2 else 0), 98),
                         (77 + (1 if k == 1 else 0), 95)]),
        tail=dict(tips=[(TAIL[k][0] + bx, TAIL[k][1]), (79, 99)]),
        armN=dict(cuff=((55.5 + bx, 76 + by), (ax + bx, ay + by), 5, 10), hand=(int(ax + bx) - 1, int(ay + by))),
        armF=dict(cuff=((73 + bx, 78 + by), (fx + bx, fy + by), 4, 8), upper=((72 + bx, 75 + by), (73 + bx, 79 + by))),
        katana=(int(fx + 1 + bx), int(fy + 1 + by), KAT[k], 21, 1),
        ribbonN=rN, ribbonF=rF,
    )
    # legs: hips ride the body, knees/ankles are absolute (feet stay planted)
    pose['legs'] = [((h[0] + bx, h[1]), kn, an, f, ffx) for (h, kn, an, f, ffx) in LEGS[k]]
    FRAMES[f'walk_SE_k{k}'] = dict(
        base='turn_SE', pose=pose,
        head=(bx, HEAD_DY[k]), bow=BOW[k], expr='calm',
        xf={'skirt': [('sq', 84, 92, 1)] if k == 1 else []},
    )
