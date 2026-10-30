"""Gates for the gold frames: lamet.py line metrics + palette check.  Usage: gates.py [--board] -> prints table, writes gates.json"""
import os, sys, json
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = '/Users/waylonhuang/Documents/other/pixelart'
sys.path.insert(0, ROOT + '/docs/team_review/2026-10-30/line_art')
sys.path.insert(0, ROOT + '/docs/team_review/2026-10-30/face_palette/scripts')
import lamet as L
import facesys as FS
sys.path.insert(0, HERE)
LOCK = set('KhHgLsSeERQOoW')


def face_boxes(bob):
    m = np.zeros((128, 128), bool)
    for (ox, oy), side, kind in FS.LAYOUT['SE']:
        w = 5 if kind == 'front' else 4
        import build_gold as B_
        ox += getattr(B_, 'EYEDX', 0)
        m[oy + bob:oy + bob + 8, ox:ox + w] = True
    return m


res = {}
import build_gold as B
for f, bob in (('contact', B.BOB['contact']), ('passing', B.BOB['passing'])):
    g = L.load_txt(f'{HERE}/walk_SE_{f}.txt')
    m = L.metrics(g)
    K = g == 'K'
    c = K[:-1, :-1] & K[1:, :-1] & K[:-1, 1:] & K[1:, 1:]
    fb = face_boxes(bob)[:-1, :-1]
    cols = sorted(set(g[g != '.']))
    off = [c_ for c_ in cols if c_ not in LOCK]
    m['clump_line'] = int((c & ~fb).sum())     # clumps outside the facesys eye templates
    m['clump_face'] = int((c & fb).sum())      # clumps that are part of the exact eye template (lock 1)
    m['colours'] = len(cols); m['palette'] = ''.join(cols); m['offpal'] = off
    ok = dict(zig=m['zig'] <= 1, Lcorner=m['dbl'] <= 2, gap=m['gap'] == 0, clump=m['clump_line'] == 0,
              colours=m['colours'] <= 14, offpal=not off)
    # interior K audit: every K px not on the silhouette must sit on a listed overlap (lock 3), the eye template, the bow stamp,
    # or a hand-drawn REGION (hand/sleeve + arm/body lines)
    import build_gold as B
    lab, _ = B.build(f)
    sil = B.silmask(g)
    groups = B.lines_for(f)
    reg = np.zeros_like(K)
    for x0, y0, why, rows in B.REGION.get(f, []):
        reg[y0:y0 + len(rows), x0:x0 + max(len(r) for r in rows)] = True
    eyes = face_boxes(bob)
    bad = []
    for y, x in zip(*np.nonzero(K & ~sil)):
        if eyes[y, x] or reg[y, x] or lab[y, x] == 'stamp': continue
        nb = {lab[yy, xx] for yy in range(y - 1, y + 2) for xx in range(x - 1, x + 2)}
        if any((nb & F_) and (nb & B_) for F_, B_ in groups): continue
        bad.append((int(x), int(y)))
    m['intK_unlisted'] = bad
    from scipy import ndimage as nd
    m['components'] = int(nd.label(g != '.', np.ones((3, 3)))[1])   # 1 = one connected sprite, no stray pixels
    ok['one_piece'] = m['components'] == 1
    ok['interior_listed'] = not bad
    m['pass'] = ok; m['PASS'] = all(ok.values())
    res[f] = m
    print(f"{f:8s} zig={m['zig']} Lcorner(dbl)={m['dbl']} gap={m['gap']} clump={m['clump']} (line {m['clump_line']}, eye-template {m['clump_face']}) "
          f"intK_unlisted={len(m['intK_unlisted'])} comps={m['components']} irr={m['irr']} kink={m['kink']} orphK={m['orphK']} intK={m['intK']} colours={m['colours']} [{m['palette']}] off={off} -> {'PASS' if m['PASS'] else 'FAIL ' + str([k for k, v in ok.items() if not v])}")
json.dump(res, open(f'{HERE}/gates.json', 'w'), indent=1, default=str)
if '--board' in sys.argv:
    L.board([(f, L.load_txt(f'{HERE}/walk_SE_{f}.txt')) for f in ('contact', 'passing')], f'{HERE}/_work/lamet_board.png', s=6)
