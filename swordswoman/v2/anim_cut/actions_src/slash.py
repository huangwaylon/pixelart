from build import F
import os
# SLASH r12. Blade angle path (<=2 steps/frame except where the smear covers):
#   ready 9.5 (idle carry) -> antic 09 -> lift 08 -> wind 07 -> coil 05 (SQUASHED, backswing up-left)
#   -> swingA 04 (STRETCHED, blade overhead + tight edge wedge) -> SMEAR 15 (the ONE crescent) -> impact 14 (no smear, SQUASH
#   legs 2px lower, spark only) -> hitstops (shake R / back) -> follow 13 -> pass 12 (blade down between the feet)
#   -> recover 11 -> settle 10 -> rest. Blade never crosses the torso.
# Overlap: hair ends via head_{hf,hu,hd,hb} / slash10_shout_* one frame late; bow_{sqz,str,tl,tr} one frame late.
# Smear parts: work/r12/smear12.py (run after a SLASH_NOSMEAR=1 build).
NOSM = os.environ.get('SLASH_NOSMEAR')
TIP = 'armN.hand'
SM = lambda n, z=6.5: [] if NOSM else [('slash10_fx_sm%d' % n, 0, 0, z)]
SPK = lambda n: ('slash9_fx_spark%d' % n, 15, 15, 9, TIP)
IDLE = dict(legs='legs', aN='armN_hold', aF='armF', torso='torso_iw', kat=None, fx=[('kat_iw7_b', 2, -2, 1, 'armN.hand')])
# impact: deep low lunge, torso twisted into the cut, head thrown forward/down, arm fully out, far arm flung back
HIT = dict(legs='slash9_lg_lunge', root=(2, 0), torso='slash8_torso_lunge', tor=(3, 1), hd=(2, 0), head='slash10_shout_hf',
           skirt='slash9_sk_lunge', aN='slash9_armN_ext', aF='armF_back', kat=(14, 5), bow='bow_back', bw=(-3, 2), shadow=12)
# squash version of HIT: legs 2px lower + wider front knee
SQ = dict(HIT, legs='slash10_lg_sq', root=(3, 0))
slash = [
 F(100, 'ready', **IDLE, head='head', bow='bow', shadow=8),
 F(70, 'antic', legs='legs_stance', aN='armN_back', aF='armF_fwd', kat=(9, 1), bow='bow_tr', bw=(0, 0), root=(-1, 0),
   tor=(-1, 1), hd=(-2, 1), torso='torso_sq', skirt='skirt_sq', head='head_hu', shadow=9),
 F(50, 'lift', legs='legs_stance', aN='armN_out', aF='armF_fwd', kat=(8, 1), torso='torso_iw_st', tor=(-1, -1), hd=(-2, -1),
   bow='bow_sqz', bw=(1, 1), skirt='skirt_swR', root=(-2, 0), head='slash10_head_hf', shadow=8),
 F(50, 'wind', legs='legs_stance', torso='slash6_torso_coil', aF='armF_pumpF', skirt='skirt_swL', aN='armN_jmp_hi',
   kat=(7, 1), zN=8, root=(-2, 0), tor=(-2, 0), hd=(-1, 0), head='head_hd', bow='bow_str', bw=(1, -1), shadow=8),
 F(120, 'coil', legs='legs_crouch', torso='slash9_torso_csq', aF='armF_pumpF', skirt='skirt_sq', aN='armN_coil', kat=(5, 1),
   zN=8, root=(-3, 0), tor=(-3, 1), hd=(-2, 2), head='head_hu', bow='bow_str', bw=(1, -2), shadow=10),
 F(30, 'swingA', legs='legs_lunge', torso='slash9_torso_str', aF='armF_pumpF', skirt='skirt_swL', aN='armN_coil', kat=None,
   zN=8, root=(-1, -1), tor=(-1, 0), hd=(1, -1), head='slash10_head_hf', bow='bow_sqz', bw=(-1, 1), shadow=9,
   fx=[('slash10_kat04_str', 0, 0, 9, TIP)]),
 F(40, 'SMEAR', **dict(HIT, root=(1, -1), tor=(2, 0), hd=(2, -1), kat=(15, 5), head='head_lean_hb', bow='bow_tl', bw=(-4, 1),
   skirt='dash9_skirt_lean', shadow=11), fx=SM(2, 7.5)),
 F(40, 'impact', **dict(SQ, head='slash10_shout_hb', hd=(1, 1), bow='bow_back', bw=(-5, 2)), fx=[SPK(0)]),
 F(60, 'hitstop', **dict(SQ, kat=None, head='slash10_shout_hf', skirt='slash9_skirt_lunge', hd=(1, 1), bow='bow_tl', bw=(-4, 3)), shake=(1, 0),
   fx=[('kat14_slash10_flash', 0, 0, 5, 'armN.hand'), SPK(1)]),
 F(50, 'hitstop2', **dict(HIT, head='slash10_shout_hu', bow='bow_sqz', bw=(-1, 2)), fx=[SPK(2)]),
 F(80, 'follow', **dict(HIT, kat=(13, 5, (3, -1)), tor=(2, 0), hd=(2, 1), head='slash10_lean_hf', bow='bow_dn', bw=(1, 2),
   skirt='slash9_sk_lunge2', shadow=11)),
 F(60, 'pass', legs='slash9_lg_lunge', root=(2, 0), torso='torso_sq', tor=(2, 1), hd=(1, 1), skirt='dash9_skirt_fwd',
   aN='armN_fwd', aF='armF', kat=(12, 5, (1, -3)), head='head_hd', bow='bow_tr', bw=(0, 0), shadow=11),
 F(90, 'recover', legs='legs_lunge', root=(2, 0), tor=(1, 1), hd=(1, 0), aN='armN_back', aF='armF', kat=(11, 1), bow='bow_str',
   bw=(1, -1), torso='torso_sq', skirt='skirt_swR', head='head_hd', shadow=9),
 F(110, 'settle', legs='legs_stance', aN='armN_hold', aF='armF', torso='torso_iw_st', kat=(10, 1, (2, -3)), bow='bow_sqz',
   bw=(0, 1), skirt='skirt_swL', tor=(0, -1), hd=(0, -1), head='slash10_head_hf', shadow=8),
 F(140, 'rest', **IDLE, head='head_hu', bow='bow', shadow=8),
]
ACTIONS = {'slash_SE': (slash, False)}
CELLS = {'slash_SE': dict(cell=(92, 76), ground=(46, 62))}
