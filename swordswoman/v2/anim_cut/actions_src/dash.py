from build import F
# DASH r10: coil (lean back, hips -3, hair/bow lifted) -> low lunge burst x2 (torso pitched fwd, hair/bow swept back,
# far fist pumps, blade trailing low 10->10->09) with SOLID 2-tone afterimages of the lunge left behind ->
# skid (body thrown back, hair/bow still swept, dust kicked) -> brake (upper body pitches forward, hair/bow flare fwd,
# hem wraps the front thigh) -> settle squash -> recover stretch -> rest = idle f00.
# Shadow: the body travels (root x), so every frame carries its own shadow fx under the feet (dash10_shadowW).


def SH(w, x):   # ground shadow under the feet at root x
    return ('dash10_shadow%d' % w, x, 0, -2)


import os
NOG = os.environ.get('DASH_NOGHOST')


def GH(n):      # solid 2-tone afterimages of this burst pose (parts generated from the frame by work/dash10/mkghost.py)
    g = [('dash10_ghost%da' % n, -8, 0, -1)] + ([('dash10_ghost%db' % n, -17, 0, -1.5)] if n > 1 else [])
    return [] if NOG else g


dash = [
 F(150, 'antic', legs='legs_jmp_crouch', torso='dash6_torso_back', skirt='dash9_skirt_coil',
   tor=(-1, 0), head='head_hu', hd=(-3, 1), aN='armN_back', aF='armF_fwd', bow='bow_str', bw=(0, -1), root=(-8, 0),
   kat=None, shadow=False, fx=[SH(9, -8), ('kat_iw7_b', 0, 0, 1, 'armN.hand')], fx_ns=[SH(9, -8)]),
 F(40, 'burst', legs='dash10_legs_lunge', torso='dash6_torso_lean5', skirt='dash9_skirt_lean', head='head_lean_hb',
   hd=(2, 3), aN='armN_back', aF='armF_pumpF', bow='bow_back', bw=(-2, 2), root=(0, 0), kat=(10, 0.8),
   shadow=False, fx=[SH(7, 0), ('dash10_dust_push', -12, 0, 0.5)] + GH(1), fx_ns=[SH(7, 0), ('dash10_dust_push', -12, 0, 0.5)] + GH(1)),
 F(50, 'burst2', legs='dash10_legs_lunge2', torso='dash6_torso_lean5', skirt='dash9_skirt_lean2', head='head_lean_hb',
   hd=(3, 3), aN='armN_back', aF='armF_pumpM', bow='bow_back', bw=(-4, 3), root=(4, 0), kat=None,
   shadow=False, fx=[SH(7, 4), ('kat_iw6_095', 0, 0, 0.8, 'armN.hand')] + GH(2), fx_ns=[SH(7, 4)] + GH(2)),
 F(90, 'skid', legs='dash6_legs_skid', torso='dash6_torso_back', tor=(-1, 1), aN='armN_back', aF='armF_jmp_hi',
   head='dash10_head_hf', hd=(-3, 1), skirt='dash10_skirt_skid', bow='bow_tr', bw=(3, 0), root=(6, 0), kat=(9, 1),
   shadow=False, fx=[SH(9, 6), ('dash10_dust_skid', 6 + 11, 0, 0.5)], fx_ns=[SH(9, 6), ('dash10_dust_skid', 6 + 11, 0, 0.5)]),
 F(70, 'brake', legs='dash10_legs_brake', torso='dash6_torso_lean5', head='head_lean_hb', hd=(2, 3), aN='armN_back',
   aF='armF_fwd', kat=(10, 1), skirt='dash10_skirt_brake', bow='bow_tl', bw=(1, 1), root=(7, 0),
   shadow=False, fx=[SH(9, 7), ('dash10_dust_brake', 7 + 10, 0, 0.5)], fx_ns=[SH(9, 7), ('dash10_dust_brake', 7 + 10, 0, 0.5)]),
 F(90, 'settle', legs='idle9_legs_lo', torso='torso_sq', head='dash10_head_hf', hd=(0, 2), aN='armN_hold', aN_ns='armN',
   aF='armF_back', kat=(10, 1, (2, -3)), skirt='skirt_swL', bow='bow_sqz', bw=(0, 1), root=(7, 0),
   shadow=False, fx=[SH(9, 7), ('dash10_dust_fade', 7 + 11, 0, 0.5)], fx_ns=[SH(9, 7), ('dash10_dust_fade', 7 + 11, 0, 0.5)]),
 F(80, 'recover', torso='idle9_torso_st2', head='head_hd', aN='armN_hold', aN_ns='armN', bow='bow_str', bw=(0, -1),
   kat=None, fx=[('kat_iw7_b', 2, -2, 1, 'armN.hand'), SH(8, 7)], fx_ns=[SH(8, 7)], root=(7, 0), shadow=False),
 # rest = idle_SE f00 (torso_iw, kat_iw7_b at the hold hand) so dash hands off to idle without a pop
 F(140, 'rest', aN='armN_hold', aN_ns='armN', torso='torso_iw', kat=None, fx=[('kat_iw7_b', 2, -2, 1, 'armN.hand'), SH(8, 7)],
   fx_ns=[SH(8, 7)], bow='bow', root=(7, 0), shadow=False),
]
ACTIONS = {'dash_SE': (dash, True)}
CELLS = {'dash_SE': dict(cell=(84, 76), ground=(46, 64))}
