from build import F
# RUN r10: r9 legs/skirts/torsos kept; secondary motion now from the shared hair/bow variant parts, 1 frame late:
# hair hu (falling) on contact -> hf (flare) on down -> hb (swept back) on the push lean -> hd (dragged) rising in air;
# bow up on contact -> sqz on down (contact+1) -> tl (tilts against the forward lean) on push -> str rising.
# Blade swings as a pendulum (half steps, every frame changes) lagging the arm by a frame; on the kicked-back-boot
# frames the hand rides higher and the blade stays shallow so it clears the boot. Shadow shrinks in the air.
KAT9 = {9: 'kat_09', 9.5: 'kat_iw6_095', 10: 'kat_10', 10.5: 'kat_run7_105', 11: 'kat_11'}
def R(ms, lab, n, aNk, kd, aF, torso, head, bow, bw, hd, root, tor=(1, 0), aN_ns=None, kz=3.5, ko=(0, 0), **k):
    if kd in (9.5, 10.5):   # in-between blade drawn as an fx at the sword hand
        k.update(fx=k.get('fx', []) + [(KAT9[kd], ko[0], ko[1], kz, 'armN.hand')], fx_ns=k.get('fx_ns', k.get('fx', [])))
        kat = None
    else:
        kat = (int(kd), kz, ko)   # z between skirt and torso: held in front of the hem, never over a boot
    return F(ms, lab, legs='run9_legs_' + n, skirt='run9_skirt_' + n, aN=aNk, aN_ns=aN_ns or aNk, aF=aF, torso=torso,
             head=head, bow=bow, bw=bw, hd=hd, root=root, tor=tor, kat=kat, **k)
T8, TSQ, TST, TLN = 'torso_run8', 'run9_torso_sq', 'run9_torso_st', 'run9_torso_lean'
HU, HF, HB, HD = 'head_lean_hu', 'run10_head_hf', 'head_lean_hb', 'head_lean_hd'
run = [
 R(80, 'contact', 'c1', 'armN_run6_hi', 9, 'run9_armF_hi', T8, HU, 'bow_up', (-1, 0), (4, 1), (0, 1), aN_ns='armN_runB', shadow=8),
 R(70, 'down', 'd1', 'armN_runB', 9.5, 'armF_run9_F', TSQ, HF, 'bow_sqz', (-1, 1), (5, 2), (0, 2), aN_ns='armN_run5_B2', shadow=9),
 R(60, 'push', 'p1', 'armN_run5_B2', 10.5, 'armF_run9_M', TLN, HB, 'bow_tl', (-2, 0), (5, 1), (0, 1), tor=(2, 0), aN_ns='armN', shadow=7, fx=[('dust1', -13, 0, 0.5)]),
 R(90, 'air', 'a1', 'armN', 9.5, 'armF_run9_D', TST, HD, 'bow_str', (-1, 0), (3, 0), (0, -4), aN_ns='armN_runF', shadow=5, ko=(0, -1), fx=[('dust2', -17, 0, 0.5)]),
 R(80, 'contact2', 'c2', 'armN_run5_B2', 9, 'armF_run9_D', T8, HU, 'bow_up', (-1, 0), (4, 1), (0, 1), aN_ns='armN_runF', shadow=8, ko=(0, -1)),
 R(70, 'down2', 'd2', 'armN_run5_B2', 10, 'armF_run9_M', TSQ, HF, 'bow_sqz', (-1, 1), (5, 2), (0, 2), aN_ns='armN', shadow=9),
 R(60, 'push2', 'p2', 'armN_runB', 10.5, 'armF_run9_F', TLN, HB, 'bow_tl', (-2, 0), (5, 1), (0, 1), tor=(2, 0), aN_ns='armN_run5_B2', shadow=7, fx=[('dust1', -9, 0, 0.5)]),
 R(90, 'air2', 'a2', 'armN_run6_hi', 10, 'run9_armF_hi', TST, HD, 'bow_str', (-1, 0), (3, 0), (0, -4), aN_ns='armN_runB', shadow=5, fx=[('dust2', -13, 0, 0.5)]),
]
# JUMP r8 (76x80 cell). One head shape (face swaps only). The sword hand stays on the near (screen-left) side the
# whole jump and the blade trails out/behind it (z1), never across the body: idle-style flat carry b -> 10 (antic)
# -> 9 antic+crouch (tip clears the floor) -> 10 launch -> 11 rise (tip lags down) -> 10.5 apex -> 10 hang -> 9.5
# fall (tip floats up) -> 9 land/recover -> 10 rebound -> 9.5 settle -> b rest.
SQ = dict(head='head', torso='torso_sq', hd=(0, 1))
JK = {'b': 'kat_iw7_b', 9.5: 'kat_iw6_095', 10.5: 'kat_run7_105'}
def J(ms, lab, kd, ko=(0, 0), **k):
    if kd in JK:
        k['fx'] = k.get('fx', []) + [(JK[kd], ko[0], ko[1], 1, 'armN.hand')]
        k['fx_ns'] = [f for f in k['fx'] if not f[0].startswith('kat')]
        k['kat'] = None
    else:
        k['kat'] = (kd, 1, ko)
    k.setdefault('bow', 'bow')
    return F(ms, lab, **k)
jump = [
 J(90, 'antic', 9.5, legs='legs_jmp9_mid', aN='armN_back', aN_ns='armN_back', aF='armF_back', bw=(0, -1), skirt='skirt_sq',
   head='head', torso='torso', hd=(0, 1)),
 J(140, 'crouch', 9, legs='legs_jmp7_land', aN='armN_back', aN_ns='armN_back', aF='armF_back', bw=(0, 1), skirt='skirt_jmp_land',
   head='head_shout', torso='torso_jmp5_sq', hd=(0, 2)),
 J(50, 'launch', 9.5, legs='legs_jmp8_launch', head='head_shout', torso='torso_jmp_st', skirt='skirt_jmp_st', aN='armN_out', aN_ns='armN_out',
   aF='armF_jmp_v', bw=(0, 2)),
 J(70, 'rise', 10, legs='legs_jmp8_launch', head='head', torso='torso_jmp_st', skirt='skirt_jmp_st', aN='armN_jmp_v', aN_ns='armN_jmp_v',
   aF='armF_jmp_v', bw=(0, 2), root=(0, -11)),
 J(110, 'apex', 10, legs='legs_jmp7_tuck', aN='armN_jmp_hi', aN_ns='armN_jmp_hi', aF='armF_jmp_hi', skirt='skirt_jmp7_droop', bw=(0, 0),
   root=(0, -21)),
 J(130, 'hang', 9.5, legs='legs_jmp7_tuck', aN='armN_jmp_top', aN_ns='armN_jmp_top', aF='armF_jmp_v', skirt='skirt', bw=(0, -1),
   root=(0, -19)),
 J(100, 'fall', 9, legs='legs_jmp_fall2', torso='torso_jmp_st', aN='armN_jmp_v', aN_ns='armN_jmp_v', aF='armF_jmp_hi', skirt='skirt_run_air',
   bw=(0, -1), root=(0, -9)),
 J(100, 'land', 9, legs='legs_jmp_land', skirt='skirt_jmp7_land', aN='armN_out', aN_ns='armN_out', aF='armF_fwd', bw=(0, -2),
   fx=[('fx_jmp7_land', 0, 0, 0.5)], head='head', torso='torso_jmp5_sq', hd=(0, 3)),
 J(80, 'recover', 9, legs='legs_jmp9_mid', skirt='skirt_jmp_land', aN='armN_back', aN_ns='armN_back', aF='armF_fwd', bw=(0, 2),
   fx=[('fx_jmp9_land2', 0, 0, 0.5)], head='head', torso='torso_sq', hd=(0, 1)),
 J(70, 'rebound', 9.5, torso='torso_jmp_st', skirt='skirt_swR', aN='armN_back', aN_ns='armN', aF='armF', bw=(0, 1)),
 J(70, 'settle', 10, aN='armN_back', aN_ns='armN', skirt='skirt_sq', bw=(0, -1), torso='torso_sq', hd=(0, 1)),
 J(110, 'rest', 'b', ko=(2, -2), aN='armN_hold', aN_ns='armN', bw=(0, 0)),
]
CELLS = {'jump_SE': dict(cell=(76, 80), ground=(40, 76))}
ACTIONS = {'run_SE': (run, True)}
