from build import F
# r10 idle: a bouncy ready-stance breath (6 beats) played twice, the second with a blink (half -> closed -> half).
# Eye height (rest = 0): top +2, fall 0, low -4, hold -4, rise -2, rise2 +1; eased timing 160/120/100/180/140/140.
#   hip  : legs st 16 / m 15 / lo 14 (knees bulge out on lo); boots never move.
#   torso: st2 +2 / torso_iw_st +1 / sq2 -2 / sq1 -1 / ln; sq parts shift the neck+shoulders 1px forward (lean).
# Everything secondary lags the body by one beat:
#   hair : shared head_{hd,hu,hf} tips (dragged on top, neutral on fall, lifted on low, flared on hold, neutral, dragged).
#   bow  : str on top (overshoots up), flat, up (lags the drop), sqz (contact+1), tl (tilts against the lean), dn (drags on the rise).
#   sleeves: 1px only (idle10_arm*_u/_d = base sleeve with the pivot moved), so the shoulder seam never changes.
#   blade: half-step angles only (kat_10 / kat_iw6_095 / kat_run7_105) drawn at armN.hand, tip lags the hand.
KAT = {10: 'kat_10', 9.5: 'kat_iw6_095', 10.5: 'kat_run7_105'}
SH = {'u': ('idle10_armN_u', 'idle10_armF_u'), 'm': ('armN', 'armF'), 'd': ('idle10_armN_d', 'idle10_armF_d')}

def B(ms, lab, legs, torso, skirt, arms, kat, hair, bow, face='head', hd=(0, 0), shadow=8, **k):
    n, f = (arms * 2)[0], arms[-1]
    head = ('idle10_head' if hair == 'hf' else 'head') if face == 'head' else 'idle10_' + face
    head += '' if hair == '-' else '_' + hair
    return F(ms, lab, legs='idle9_legs_' + legs, torso=torso, skirt=skirt, aN=SH[n][0], aF=SH[f][1], kat=None,
             fx=[(KAT[kat], 0, 0, 1, 'armN.hand')], fx_ns=[], head=head, hd=hd, bow=bow, shadow=shadow, **k)

def cycle(blink, t=''):
    fc = (lambda a, b: b) if blink else (lambda a, b: a)
    hold = [B(180, 'hold', 'lo', 'idle9_torso_sq1', 'idle9_skirt_bell', 'd', 10, 'hf', 'bow_sqz', hd=(0, 1), shadow=9)] if not blink else [
            B(100, 'blink-b', 'lo', 'idle9_torso_sq1', 'idle9_skirt_bell', 'd', 10, 'hf', 'bow_sqz', 'blink', hd=(0, 1), shadow=9),
            B(80, 'half-b', 'lo', 'idle9_torso_sq1', 'idle9_skirt_bell', 'd', 10,   'hf', 'bow_tl', 'half', hd=(0, 1), shadow=9)]
    return [
 B(160, 'top' + t,  'st', 'idle9_torso_st2', 'idle9_skirt_top', 'm',  10,  'hd', 'bow_str', shadow=7),
 B(120, 'fall' + t, 'm',  'torso_iw_st',     'idle9_skirt_up',  'u',  10,  '-',  'bow'),
 B(100, 'low' + t,  'lo', 'idle9_torso_sq2', 'skirt_sq',        'u',  9.5, 'hu', 'bow_up', fc('head', 'half'), shadow=9),
    ] + hold + [
 B(140, 'rise' + t, 'm',  'idle9_torso_ln',  'idle9_skirt_long', 'd', 10,   '-',  'bow_tl', hd=(0, 1)),
 B(140, 'rise2' + t,'st', 'torso_iw_st',     'skirt_iw6_nar',   'm',  10.5, 'hd', 'bow_dn'),
    ]

idle = cycle(False) + cycle(True, '-b')
ACTIONS = {'idle_SE': (idle, True)}
