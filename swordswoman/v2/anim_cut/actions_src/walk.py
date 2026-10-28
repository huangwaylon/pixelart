from build import F
# r10 walk: c=contact d=down p=pass u=up, x2 (near leg forward in c1, far leg forward in c2).
# Legs: walk10 contact/down/pass with a wide planted stride (heels ~12px apart), toe-off back foot,
#   passing foot lifted 3-4px with the shin visible under the hem; walk9 up frames.
# Body: hip heights c12 d11 p13 u14; torso swaps lean2 (c) / squash-lean (d) / lean (p) / stretch (u).
# Secondary (1 frame late): hair c=hu (falling) d=hf (squash) p=hd (rising) u=hb (forward push);
#   bow c=up d=sqz p=str u=tilt; hem differs on every frame.
# Arms oppose legs with a 1-frame hold; blade low and trailing behind (z1), 10 <-> 10.5 <-> 11, lagging the arm.
L = 'walk10_legs_'
K105 = 10.5
KAT = {10: 'kat_10', 10.5: 'kat_run7_105', 11: 'kat_11'}


def W(ms, lab, legs, sk, torso, aN, aF, kat, head, bow, tor=(1, 0), hd=(0, 0), bw=(0, 0), ko=(0, 0), sh=8, **k):
    lg = legs if legs.startswith('walk9') else L + legs
    return F(ms, lab, legs=lg, skirt='walk9_skirt_' + sk, torso=torso, tor=tor, hd=hd, bw=bw, bow=bow,
             head=head, aN=aN, aF=aF, kat=None, fx=[(KAT[kat], ko[0], ko[1], 1, 'armN.hand')], fx_ns=[], shadow=sh, **k)


walk = [
 W(100, 'contact', 'c1', 'c1', 'walk9_torso_lean2', 'armN_back', 'walk10_armF_f', 11, 'head_hu', 'bow_up', sh=9),
 W(90, 'down', 'd1', 'd1', 'walk9_torso_sql', 'armN_back', 'walk10_armF_f', K105, 'walk10_head_hf', 'bow_sqz', hd=(0, 1), sh=9),
 W(80, 'pass', 'p1', 'p1', 'walk9_torso_lean', 'armN_iw5_b1', 'armF_iw5', K105, 'head_hd', 'bow_str', tor=(0, 0), sh=7),
 W(100, 'up', 'walk9_legs_u1', 'u1', 'torso_iw_st', 'armN', 'armF_iw5', 10, 'head_hb', 'bow_tl', tor=(0, 0), sh=7),
 W(100, 'contact2', 'c2', 'c2', 'walk9_torso_lean2', 'walk10_armN_f', 'walk10_armF_b', 10, 'head_hu', 'bow_up', sh=9),
 W(90, 'down2', 'd2', 'd2', 'walk9_torso_sql', 'walk10_armN_f', 'walk10_armF_b', 10, 'walk10_head_hf', 'bow_sqz', hd=(0, 1), sh=9, ko=(-1, 0)),
 W(80, 'pass2', 'p2', 'p2', 'walk9_torso_lean', 'armN', 'armF_iw5', K105, 'head_blink_hd', 'bow_str', tor=(0, 0), sh=7),
 W(100, 'up2', 'walk9_legs_u2', 'u2', 'torso_iw_st', 'armN_iw5_b1', 'walk10_armF_f', 11, 'head_hb', 'bow_tr', tor=(0, 0), sh=7),
]
ACTIONS = {'walk_SE': (walk, True)}
