"""eyes3/setspec_f.py : eye round FINAL lid/lash construction -> eye_spec.json (front_left, front_right_override, wing, kinds_by_view)
One 5-wide construction (cols 0-4, col 5 empty) for every open eye: arched top = 3 K px (cols 1-3) on the lash row with h anti-alias
px at both ends, both K ends 1 row lower (outer K col 0 row lash+1, inner-corner K col 4 row lash+1 on the iris top-right), 2 separate outer
lash flicks outside the block forking from the outer corner K: up-out (-1,-1 rel.) and down-out (-1,+1 rel.).
(crit r1: h ends read ~K -> g mid-tone ends, lower flick soft h. Variant F = skin arch ends + 2-row outer K: rounder but S face_ssim .573 -> .553; h ends + 1-row outer = .575.)"""
import json
P = '/Users/waylonhuang/Documents/other/pixelart/swordswoman/v2/m96/eye_spec.json'; d = json.load(open(P))
T = lambda r4: ["......", "gKKKg.", "Kh@hK.", ".g@Kg.", r4, "_....."]
R = lambda r4: ["......", ".gKKKg", ".K@hhK", ".g@Kg.", r4, "....._"]
FL = {'neutral': T("hgLLg."), 'embarrassed': T("hgLLg."), 'determined': T("hgLLg."), 'cheerful': T("h.LL.."), 'shout': T("h.LL.."),
      'surprised': ["gKKKg.", "K...K.", ".h@hh.", ".g@Kg.", "hgLLg.", "_....."],
      'blink_half': ["......", "......", "gKKKg.", "Kg@KK.", "hgLLg.", "_....."],
      'joy': ["......", "......", ".KKK..", "K...K.", "......", "_....."],
      'blink_closed': ["......", "......", "......", "K.....", ".KKKK.", "_....."]}
FR = {'neutral': R(".gLLgh"), 'embarrassed': R(".gLLgh"), 'determined': R(".gLLgh"), 'cheerful': R("..LL.h"), 'shout': R("..LL.h"),
      'surprised': [".gKKKg", ".K...K", ".h@hh.", ".g@Kg.", ".gLLgh", "....._"],
      'blink_half': ["......", "......", ".gKKKg", ".K@KgK", ".gLLgh", "....._"]}
d['front_left'].update(FL)
d['front_right_override'] = {'_doc': 'hand-mirrored right eyes (eye round): the lid/lash geometry mirrors (outer = col 5, inner-corner drop = col 1 on the iris top-left) but the catchlight/pupil columns may not', **FR}
d['wing'].update({k: [[-1, 1], [-1, 3, 'h']] for k in ('neutral', 'cheerful', 'embarrassed', 'determined', 'shout')})
d['wing'].update({'surprised': [[-1, 0], [-1, 2, 'h']], 'blink_half': [[-1, 2]], 'joy': [[-1, 2]], 'blink_closed': [[-1, 2]], 'effort': [], 'pain': []})
P_ = lambda r4: ["......", ".KKK..", "Kh@hK.", "Kg@Kg.", r4, "_....."]   # E profile: skin arch ends + 2-row outer K (h ends: E face_ssim .319 -> .302; this: .337)
d['kind_override'] = {'_doc': 'eye round: per-kind templates replacing the derived ones. profile = E profile eye (same arch: 3 K top cols 1-3, outer K col 0, inner K col 4 one row lower; ends are skin instead of h and the outer K is 2 rows: measured E face_ssim .337 vs .302 with the S/SE h-end version).',
    'profile': {'neutral': P_("hgLLg."), 'embarrassed': P_("hgLLg."), 'determined': P_("hgLLg."), 'cheerful': P_("h.LL.."), 'shout': P_("h.LL.."),
                'surprised': [".KKK..", "K...K.", "Kh@hh.", ".g@Kg.", "hgLLg.", "_....."], 'blink_half': ["......", "......", ".KKK..", "Kg@KK.", "hgLLg.", "_....."]}}
d['kinds_by_view']['E'] = ['profile']
d['wing_override'] = {'_doc': 'eye round crit r1: per-kind flick lists. profile (E): one up-out K flick (the soft lower flick sits on the side hair; E face_ssim .354 vs .337)',
    'profile': {e: [w[0]] for e, w in d['wing'].items() if not e.startswith('_') and w}}
json.dump(d, open(P, 'w'), indent=1); print('spec F')
