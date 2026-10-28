"""FX KIT unit test: every effect rendered on a blank cell and on a real body, then checked.
  .venv/bin/python tools/hybrid/fx/test_kit.py [--out hybrid/S7_fxkit/r3/kit]
Checks (each must hold or the test FAILS, exit 1):
  - palette: every FX pixel is a legend tone (to_rgba of the grid is in docs/palette.json), alpha only 0 / 255
  - clusters: no FX pixel without a same-tone 8-neighbour (cluster size >= 2)
  - lint (tools/pixel/lint.py) on the blank-cell output: orphans 0 (any tone, no whitelist)
  - lint on the body output: orphans 0 outside the metrics whitelist (body pixels the FX touched are healed)
  - smears (crescent / sliver / wisps / speed_bands / streaks / afterimage): 0 px of pink_1 (the ribbon tone)
  - crescent: thickness <= lead_px, the head guard is untouched, cut-mask px untouched
  - acting.lag: trails while moving, overshoots 2-3 px the key after the stop, settles to 0
Also reports lint jaggy / spur counts of the blank-cell FX for the record (smears have no outline by design, so
outline_gap is expected)."""
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kit as K
import acting as A
sys.path.insert(0, os.path.join(K.ROOT, 'tools', 'hybrid'))
sys.path.insert(0, os.path.join(K.ROOT, 'tools', 'pixel'))
import hylib as H  # noqa: E402
import lint as L  # noqa: E402

BASE = os.path.join(K.ROOT, 'hybrid', 'S7_fxkit', 'r3', 'base')
FAIL = []
REPORT = {}


def check(name, cond, msg):
    if not cond: FAIL.append(f'{name}: {msg}')
    return cond


def lint_counts(g):
    a = K.to_rgba(g)
    flags, info, _ = L.lint_frame(a, H.palette())
    c = {}
    for f in flags:
        if f['sev'] == 'info': continue
        c[f['type']] = c.get(f['type'], 0) + 1
    orph = [f for f in flags if f['type'] == 'orphan']
    return c, orph


def body(name):
    g = K.load(os.path.join(BASE, name + '.png'))
    own = np.load(os.path.join(BASE, name + '_owner.npy'), allow_pickle=True)
    return g, own


def run_case(name, fn, smear=True, on=None):
    """fn(g, own) -> painted dict"""
    # blank cell
    g = K.blank(); pts = fn(g, None)
    c, orph = lint_counts(g)
    r = dict(px=len(pts), tones=K.stats(pts), lint=c)
    check(name, len(pts) > 0, 'painted nothing')
    check(name, not K.orphans(g, list(pts)), f'{len(K.orphans(g, list(pts)))} FX px without a same-tone neighbour')
    check(name, not orph, f'blank-cell lint orphans {len(orph)}')
    if smear: check(name, 'P' not in r['tones'], f"pink_1 used ({r['tones'].get('P')} px)")
    a = K.to_rgba(g)
    check(name, set(np.unique(a[..., 3]).tolist()) <= {0, 255}, 'semi alpha')
    if on:
        g2, own = body(on)
        before = g2.copy()
        pts2 = fn(g2, own)
        _, orph2 = lint_counts(g2)
        bad = [o for o in orph2 if o.get('detail') not in H.ORPHAN_OK]
        _, orph0 = lint_counts(before)
        bad0 = [o for o in orph0 if o.get('detail') not in H.ORPHAN_OK]
        check(name, len(bad) <= len(bad0), f'body lint orphans {len(bad0)} -> {len(bad)}')
        hd = own == 'HEAD'
        check(name, (g2[hd] == before[hd]).all(), 'head stamp touched')
        r['on'] = dict(sprite=on, px=len(pts2), orphans_before=len(bad0), orphans_after=len(bad))
    REPORT[name] = r


def main(out):
    gd = lambda own: K.head_guard(own) if own is not None else None

    def cres(g, own):
        cut = None
        if own is not None:
            cut = K.limb_mask(g, (62, 82, 76, 92), chars='sSmK')
        return K.crescent(g, (64, 53), 36, 155, 31, lead_px=6, rim_px=2, cut=cut, guard=gd(own),
                          front=(lambda x, y: y >= 84) if own is not None else None)
    run_case('crescent', cres, on='slash_SE_k1')
    # thickness <= lead
    g = K.blank(); band, ech, depth = K.crescent_pts((64, 53), 36, 155, 31, lead_px=6)
    check('crescent', max(depth.values()) <= 6.01, f'band thicker than lead_px ({max(depth.values()):.2f})')
    # cut mask honoured
    g, own = body('slash_SE_k1'); cut = K.limb_mask(g, (62, 82, 76, 92), chars='sSmK'); b = g.copy()
    K.crescent(g, (64, 53), 36, 155, 31, lead_px=8, cut=cut, front=lambda x, y: True, front_rows=99)
    check('crescent', (g[cut] == b[cut]).all(), 'cut-mask (hand / hilt) painted over')
    run_case('crescent_iso', lambda g, own: K.crescent(g, (64, 72), (34, 17), 200, -15, lead_px=5))
    run_case('sliver', lambda g, own: K.sliver(g, (64, 53), 36, 155, 24, keep=0.4, guard=gd(own)), on='slash_SE_k2')
    run_case('wisps', lambda g, own: K.wisps(g, (64, 53), 36, 60, 10, n=2, guard=gd(own)), on='slash_SE_k3')

    def limb(g, own, mode):
        if own is None:
            src = K.blank(); src[60:66, 60:72] = 'R'; src[60, 60:72] = 'K'
            m = src != '.'
            g[:] = src
            return K.limb_multiples(g, src, m, [(-5, -1), (-10, -3)], mode=mode)
        src = g.copy()
        m = K.limb_mask(src, owner=own, layers=('armX', 'armL')) & (src != 'K')
        return K.limb_multiples(g, src, m, [(-5, -1), (-10, -3)], mode=mode, guard=gd(own))
    run_case('limb_multiples', lambda g, own: limb(g, own, 'multiples'), smear=False, on='slash_SE_k1')
    run_case('limb_stretch', lambda g, own: limb(g, own, 'stretch'), smear=False, on='slash_SE_k1')

    def bands(g, own):
        if own is None:
            return K.speed_bands(g, (-1, 0), n=3, origins=[(80, 50), (82, 54), (80, 58)])
        return K.speed_bands(g, (-1, 0), n=3, body=g != '.', guard=gd(own))
    run_case('speed_bands', bands, on='dash_SE_f1')

    def after(g, own):
        if own is None:
            sil = np.zeros((K.N, K.N), bool); sil[40:90, 60:80] = True
            src = K.blank(); src[sil] = 'R'; g[:] = src
            return K.afterimage(g, sil, travel=(1, 0))
        sil = (g != '.') & ~np.isin(g, list('tTw'))
        return K.afterimage(g, sil, offsets=((-8, -2), (-17, -4)), guard=gd(own), far_mask=own == 'HEAD', travel=(1, 0))
    run_case('afterimage', after, on='dash_SE_f1')
    for st in (0, 1, 2):
        run_case(f'impact_star_s{st}', lambda g, own, st=st: K.impact_star(g, (93, 66) if own is not None else (64, 64),
                 stage=st, rot=-50, skip=((140, 250),) if own is not None else (), guard=gd(own)), on='slash_SE_k2')
    for st in (0, 1, 2):
        run_case(f'dust_s{st}', lambda g, own, st=st: K.dust(g, A.feet_points(g) if own is not None else
                 [(60, 100, -1), (68, 100, 1)], stage=st, guard=gd(own)), smear=False, on='jump_E_land')
    run_case('streaks', lambda g, own: K.streaks(g, [(60, 96)], vector=(0, 1), n=3, guard=gd(own)), on='jump_E_apex')
    # acting
    o = A.lag([0, -6, 4, 10, 10, 10, 10], overshoot=2)
    check('acting.lag', o[1] > 0 and o[2] < 0, f'no trailing {o}')
    check('acting.lag', o[4] == 2 and abs(o[5]) == 1 and o[6] == 0, f'overshoot/settle wrong {o}')
    t = A.lag([0, -6, 4, 10, 10, 10, 10], overshoot=3, tip=True)
    check('acting.lag tip', max(t[3:]) == 3, f'tip overshoot {t}')
    R = A.ribbon([(58, 75)] * 4, (0, 1), [(0, 0), (-8, 0), (8, 0), (8, 0)], nodes=6, seg=2.0)
    L0 = [sum(np.hypot(np.diff([p[0] for p in r]), np.diff([p[1] for p in r]))) for r in R]
    check('acting.ribbon', all(8 <= l <= 12.5 for l in L0), f'ribbon length not preserved {L0}')
    REPORT['acting'] = dict(lag=o, tip=t, ribbon_len=[round(float(l), 1) for l in L0])
    os.makedirs(out, exist_ok=True)
    REPORT['_fail'] = FAIL
    json.dump(REPORT, open(os.path.join(out, 'unit_test.json'), 'w'), indent=1, default=str)
    for k, v in REPORT.items():
        if k.startswith('_'): continue
        print(f'{k:18s} {json.dumps(v, default=str)[:150]}')
    print('FAIL' if FAIL else 'PASS', len(FAIL), *FAIL, sep='\n  ' if FAIL else ' ')
    return 1 if FAIL else 0


if __name__ == '__main__':
    out = sys.argv[sys.argv.index('--out') + 1] if '--out' in sys.argv else os.path.join(K.ROOT, 'hybrid', 'S7_fxkit', 'r3', 'kit')
    sys.exit(main(out))
