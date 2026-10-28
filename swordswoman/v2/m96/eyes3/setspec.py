"""eyes3/setspec.py VARIANT : write the eye-round lid/lash templates into eye_spec.json (variants A/C for prototyping)"""
import json, sys
P = '/Users/waylonhuang/Documents/other/pixelart/swordswoman/v2/m96/eye_spec.json'; d = json.load(open(P)); v = sys.argv[1]
c3 = 'K' if v == 'C' else '.'   # C: outer corner 3 rows thick (parallel flicks)
OPEN = {
 'neutral':     ["......", "KKKKK.", "Kh@hhK", c3 + "g@Kg.", "hgLLg.", "_....."],
 'cheerful':    ["......", "KKKKK.", "Kh@hhK", c3 + "g@Kg.", "h.LL..", "_....."],
 'embarrassed': ["......", "KKKKK.", "Kh@hhK", c3 + "g@Kg.", "hgLLg.", "_....."],
 'determined':  ["......", "KKKKK.", "Kh@hhK", c3 + "g@Kg.", "hgLLg.", "_....."],
 'shout':       ["......", "KKKKK.", "Kh@hhK", c3 + "g@Kg.", "h.LL..", "_....."],
 'surprised':   [".KKK..", "K...K.", "Kh@hhK", ".g@Kg.", "hgLLg.", "_....."],
 'blink_half':  ["......", "......", "KKKKK.", "Kg@KgK", "hgLLg.", "_....."],
 'joy':         ["......", "......", ".KKK..", "K...K.", "......", "_....."],
 'blink_closed':["......", "......", "......", "K.....", ".KKKK.", "_....."],
}
for e, t in OPEN.items(): d['front_left'][e] = t
W = {'neutral': [[-1, 0], [-1, 2]], 'cheerful': [[-1, 0], [-1, 2]], 'embarrassed': [[-1, 0], [-1, 2]], 'determined': [[-1, 0], [-1, 2]],
     'shout': [[-1, 0], [-1, 2]], 'surprised': [[-1, 0], [-1, 2]], 'blink_half': [[-1, 1], [-1, 3]], 'joy': [[-1, 2]], 'blink_closed': [[-1, 2]],
     'effort': [], 'pain': []}
if v == 'D':   # round top: middle 4 lash px 1 row above BOTH ends; outer end 2 rows thick; two outer flicks (-1,1) + (-1,3)
    T = lambda r4: ["......", ".KKKK.", "Kh@hhK", "Kg@Kg.", r4, "_....."]
    for e in ('neutral', 'embarrassed', 'determined'): d['front_left'][e] = T("hgLLg.")
    for e in ('cheerful', 'shout'): d['front_left'][e] = T("h.LL..")
    d['front_left']['surprised'] = ["..KK..", ".K..K.", "Kh@hhK", "Kg@Kg.", "hgLLg.", "_....."]
    d['front_left']['blink_half'] = ["......", "......", ".KKKK.", "Kg@KgK", "hgLLg.", "_....."]
    P_ = lambda r4: ["......", ".KKK..", "Kh@hK.", "Kg@Kg.", r4, "_....."]   # E profile: inner drop 1 col in (col 5 touches the profile outline)
    d['kind_override'] = {'_doc': 'eye round: per-kind templates that replace the derived ones (profile = E profile eye: the inner-corner drop sits 1 col in, on the iris top-right, because col 5 touches the profile outline)',
        'profile': {'neutral': P_("hgLLg."), 'embarrassed': P_("hgLLg."), 'determined': P_("hgLLg."), 'cheerful': P_("h.LL.."), 'shout': P_("h.LL.."),
                    'surprised': ["..KK..", ".K..K.", "Kh@hh.", "Kg@Kg.", "hgLLg.", "_....."], 'blink_half': ["......", "......", ".KKK..", "Kg@KK.", "hgLLg.", "_....."]}}
    d['kinds_by_view']['E'] = ['profile']
    W.update({k: [[-1, 1], [-1, 3]] for k in ('neutral', 'cheerful', 'embarrassed', 'determined', 'shout', 'surprised')})
    W['blink_half'] = [[-1, 2]]
if v == 'C': W.update({k: [[-1, 0], [-1, 2]] for k in ('neutral', 'cheerful', 'embarrassed', 'determined', 'shout')})
d['wing'].update(W)
d['front_right_override'] = {'_doc': d['front_right_override']['_doc']}
json.dump(d, open(P, 'w'), indent=1); print('spec variant', v)
