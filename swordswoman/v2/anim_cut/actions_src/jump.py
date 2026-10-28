from build import F
# RUN r9: legs_run9_* = run8 with the kicked-back leg bent into a V (boot up behind) and the push-frame recovery
# foot lifted 3px; head 4px ahead of the hips (tor+1, hd+3) for the lean; torso_run9_st (+1 row) on air; darker far
# arm armF_run9_{F,M,D} stays visible; blade 9.5/10 only, z0.5 behind the legs.
# RUN r8: 8f, retargeted from the anim_redraw run poses (legs_run8_*, work/rj8/legs.py): contact (front leg planted,
# back boot kicked up behind) -> down (hip 15, lowest) -> push (toe-off, other knee driving) -> air (both feet off, +2).
# torso_run8 = rotated ~15deg (rows shift forward toward the top, obi slants down to the front), head 2 fwd/1 down;
# skirt_run8_{a,d,p,air} slanted hem that flares with the stride. Blade follows the bob (tip lags): 10 9.5 10 10.5;
# sword arm swings back-up -> back -> back-down -> down (never forward of the hip in the katana build).
KAT8 = {9: 'kat_09', 9.5: 'kat_iw6_095', 10: 'kat_10', 10.5: 'kat_run7_105', 11: 'kat_11'}
def R(ms, lab, legs, aNk, kd, aN, aF, sk, bw, root, torso='torso_run8', **k):
    if kd in (9.5, 10.5):   # in-between blade drawn as an fx at the sword hand
        k.update(fx=k.get('fx', []) + [(KAT8[kd], 0, 0, 0.5, 'armN.hand')], fx_ns=k.get('fx_ns', []))
        kat = None
    else:
        kat = (int(kd), 0.5)   # behind the legs: the trailing blade never paints over the kicked-back boot
    k.setdefault('hd', (4, 1)); k.setdefault('tor', (1, 0))
    return F(ms, lab, legs=legs, aN=aNk, aN_ns=aN, aF=aF, skirt=sk, bow='bow', bw=bw, root=root,
             torso=torso, kat=kat, head='head_lean', **k)
run = [   # near arm hi->B->B2->B2->B2->B->B->hi with the blade 1/2 step behind it; far arm (darker) F F M D D M M F
 R(70, 'contact', 'legs_run9_c1', 'armN_run6_hi', 9.5, 'armN_runB', 'armF_run9_F', 'skirt_run8_a', (-1, -1), (0, 0)),
 R(60, 'down', 'legs_run8_d1', 'armN_runB', 9.5, 'armN', 'armF_run9_F', 'skirt_run8_d', (-1, -1), (0, 0), torso='torso_run8_sq', hd=(4, 2)),
 R(60, 'push', 'legs_run9_p1', 'armN_run5_B2', 10, 'armN', 'armF_run9_M', 'skirt_run8_p', (-2, 1), (0, 0)),
 R(80, 'air', 'legs_run9_a1', 'armN_run5_B2', 10, 'armN_runF', 'armF_run9_D', 'skirt_run8_air', (-2, 2), (0, -2), torso='torso_run9_st'),
 R(70, 'contact2', 'legs_run9_c2', 'armN_run5_B2', 10, 'armN_runF', 'armF_run9_D', 'skirt_run8_a', (-1, -1), (0, 0)),
 R(60, 'down2', 'legs_run8_d2', 'armN_runB', 10, 'armN', 'armF_run9_M', 'skirt_run8_d', (-1, -1), (0, 0), torso='torso_run8_sq', hd=(4, 2)),
 R(60, 'push2', 'legs_run9_p2', 'armN_runB', 9.5, 'armN', 'armF_run9_M', 'skirt_run8_p', (-2, 1), (0, 0)),
 R(80, 'air2', 'legs_run9_a2', 'armN_run6_hi', 9.5, 'armN_runB', 'armF_run9_F', 'skirt_run8_air', (-2, 2), (0, -2), torso='torso_run9_st'),
]
# JUMP r10 (76x80 cell): r9 swap-part keys kept; shared secondary-motion heads on every frame, hair 1 frame late
# (hu while dipping/at apex/falling, hf on the crouch + recover, hd while rising), bow lags 1 frame (up on the dip,
# sqz on launch, str on rise, up through the fall, sqz on contact+1). Per-frame ground shadow (9 crouch -> 4 apex ->
# 10 land). Launch smear dropped (critics: inverted/banded); solid 2-tone dust puffs instead of single specks.
# Blade 1-2 steps/frame following the arm, tip always above the soles: 10 9 10 11 10 9 7 8 9 10 rest.
# JUMP r9: every key has its own torso/skirt/leg swap part (jump9_*): crouch torso squashed + sheared forward,
# launch torso stretched 2 rows / 2px narrower, bell hem at apex, hem flipped up on the fall, wide flare on land.
import os
JK = {'b': 'kat_iw7_b'}
def J(ms, lab, kd, ko=(0, 0), **k):
    if kd in JK:
        k['fx'] = k.get('fx', []) + [(JK[kd], ko[0], ko[1], 1, 'armN.hand')]
        k['fx_ns'] = [f for f in k['fx'] if not f[0].startswith('kat')]
        k['kat'] = None
    else:
        k['kat'] = (kd, 1, ko)
    k.setdefault('bow', 'bow')
    k.setdefault('aN_ns', k.get('aN', 'armN'))
    return F(ms, lab, **k)
jump = [
 J(80, 'antic', 10, ko=(1, -2), legs='legs_jmp9_mid', skirt='skirt_sq', torso='jump9_torso_lean', head='head_lean_hu', hd=(0, 1),
   aN='armN', aF='armF', bow='bow_tl', bw=(0, 0), shadow=8),
 J(130, 'crouch', 9, legs='jump9_legs_crouch', skirt='jump9_skirt_crouch', torso='jump9_torso_crouch', head='jump10_head_shout_hf', hd=(0, 2),
   aN='armN_back', aF='armF_back', bow='bow_up', bw=(0, -1), shadow=10),
 J(50, 'launch', 10, legs='jump9_legs_launch', skirt='jump9_skirt_st', torso='jump9_torso_st', head='jump9_head_shout_dn',
   aN='armN_out', aF='armF_jmp_v', bow='bow_sqz', bw=(0, 2), fx=[('jump10_fx_launch', 0, 0, 0.5)], shadow=7),
 J(70, 'rise', 11, legs='jump9_legs_rise', skirt='skirt_jmp_st', torso='jump9_torso_st', head='head_hd',
   aN='armN_jmp_v', aF='armF_jmp_hi', zN=7.5, bow='bow_str', bw=(0, 1), root=(0, -12),
   fx=[('jump10_fx_launch2', 0, 0, 0.5)], shadow=5),
 J(100, 'apex', 10, legs='jump9_legs_tuck', skirt='jump9_skirt_bell', torso='torso', head='head_hu',
   aN='armN_jmp_top', aF='armF_jmp_hi', bow='bow_str', bw=(0, -1), root=(0, -24), shadow=5),
 J(120, 'hang', 9, legs='jump9_legs_fall', skirt='skirt_jmp7_droop', torso='torso_sq', head='head_blink_hu', hd=(0, 1),
   aN='armN_jmp_hi', aF='armF_jmp_v', bow='bow_up', bw=(0, -1), root=(0, -21), shadow=5),
 J(80, 'fall', 8, legs='jump9_legs_launch', skirt='jump9_skirt_up', torso='jump9_torso_st', head='head_hu',
   aN='armN_jmp_v', aF='armF_jmp_hi', zN=7.5, bow='bow_up', bw=(0, -2), root=(0, -9), shadow=6),
 J(110, 'land', 9, ko=(1, -2), legs='legs_jmp_land', skirt='jump9_skirt_land', torso='jump9_torso_crouch', head='head_hu', hd=(0, 3),
   aN='armN_out', aF='armF_fwd', bow='bow_up', bw=(0, 0), fx=[('fx_jmp7_land', 0, 0, 0.5)], shadow=10),
 J(80, 'recover', 10, ko=(1, -3), legs='legs_jmp9_mid', skirt='skirt_jmp_land', torso='torso_jmp5_sq', head='jump10_head_hf', hd=(0, 1),
   aN='armN_back', aF='armF_fwd', bow='bow_sqz', bw=(0, 1), fx=[('jump10_fx_land2', 0, 0, 0.5)], shadow=9),
 J(70, 'settle', 'b', ko=(1, -2), skirt='skirt_swR', torso='torso_jmp_st', head='head_hd', aN='armN', aF='armF', bow='bow_str', bw=(0, 0),
   fx=[('jump10_fx_land3', 0, 0, 0.5)], shadow=8),
 J(100, 'rest', 'b', ko=(2, -2), aN='armN_hold', aN_ns='armN', bw=(0, 0), shadow=8),
]
CELLS = {'jump_SE': dict(cell=(76, 80), ground=(40, 76))}
ACTIONS = {'jump_SE': (jump, True)}
