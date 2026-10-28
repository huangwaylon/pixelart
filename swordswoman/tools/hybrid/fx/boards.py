"""FX KIT preview boards: every effect, a few parameter variants each, at 6x on SLATE and GRASS plus a 1x strip.

  .venv/bin/python tools/hybrid/fx/boards.py [OUT_DIR]       (default hybrid/S7_fxkit/r3/kit)
Writes <fx>_6x.png (slate row over grass row), <fx>_1x.png (1x strip on both grounds), kit_board_6x.png (all),
kit_strip_1x.png, and the demo grids as <fx>_<variant>.png (128 cells, for the unit test)."""
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kit as K
import acting as A

ROOT = K.ROOT
BASE = os.path.join(ROOT, 'hybrid', 'S7_fxkit', 'r3', 'base')
SLATE = (58, 62, 74)
GRASS = (84, 132, 66)


def base(name):
    p = os.path.join(BASE, name + '.png')
    g = K.load(p)
    own = np.load(os.path.join(BASE, name + '_owner.npy'), allow_pickle=True) if os.path.exists(
        os.path.join(BASE, name + '_owner.npy')) else None
    return g, own


# ---------------------------------------------------------------- demos: name -> list of (label, grid, box)
def demos():
    D = {}
    # (1) crescent
    v = []
    g = K.blank(); K.crescent(g, (64, 64), 36, 155, 30, lead_px=6, rim_px=2); v.append(('slash r36 155->30 lead6', g, (20, 40, 108, 108)))
    g = K.blank(); K.crescent(g, (64, 72), (34, 17), 200, -15, lead_px=5, rim_px=1); v.append(('iso cut-plane ry=.5rx', g, (20, 40, 108, 108)))
    g = K.blank(); K.crescent(g, (64, 70), (20, 30), -100, 80, lead_px=7, rim_px=2, echo=False); v.append(('overhead vertical lead7', g, (20, 30, 108, 108)))
    g, own = base('slash_SE_k1')
    fist = K.limb_mask(g, (62, 82, 76, 92), chars='sSmK')
    K.crescent(g, (64, 53), 36, 155, 31, lead_px=6, rim_px=2, cut=fist, guard=K.head_guard(own),
               front=lambda x, y: y >= 86, front_rows=2)
    v.append(('on k1 + hand cut-mask', g, (20, 30, 108, 118)))
    D['crescent'] = v
    # sliver / wisps (the arc's k2 / k3 states)
    v = []
    g = K.blank(); K.sliver(g, (64, 64), 36, 155, 30, keep=0.35, thick=2); v.append(('k2 sliver keep .35', g, (20, 40, 108, 108)))
    g = K.blank(); K.wisps(g, (64, 64), 36, 60, 10, n=2); v.append(('k3 wisps', g, (20, 40, 108, 108)))
    D['sliver_wisps'] = v
    # (2) limb multiples
    v = []
    g, own = base('slash_SE_k1')
    src = g.copy(); gd = K.head_guard(own)
    arm = K.limb_mask(src, owner=own, layers=('armX', 'armL')) & ~np.isin(src, list('K'))
    gg = g.copy(); K.limb_multiples(gg, src, arm, [(-6, -2), (-12, -6)], n=2, mode='multiples', guard=gd)
    v.append(('arm multiples n2', gg, (24, 50, 104, 110)))
    gg = g.copy(); K.limb_multiples(gg, src, arm, [(-5, -1), (-10, -4), (-14, -8)], mode='stretch', guard=gd)
    v.append(('arm stretch', gg, (24, 50, 104, 110)))
    g, own = base('run_SE_f1'); src = g.copy()
    leg = K.limb_mask(src, (40, 90, 60, 104), owner=own, layers=('legs',))
    gg = g.copy(); K.limb_multiples(gg, src, leg, [(-3, -1), (-7, -2)], mode='stretch', erode_tail=1)
    v.append(('run back-leg stretch', gg, (24, 50, 104, 110)))
    gg = g.copy(); K.limb_multiples(gg, src, leg, [(-4, -1), (-8, -2)], n=2, mode='multiples')
    v.append(('run back-leg multiples', gg, (24, 50, 104, 110)))
    D['limb_multiples'] = v
    # (3) speed bands
    v = []
    g, own = base('dash_SE_f1')
    body = g != '.'
    gg = g.copy(); K.speed_bands(gg, (-1, 0), n=3, lengths=(12, 9, 14), body=body); v.append(('dash 3 bands', gg, (16, 40, 104, 110)))
    gg = g.copy(); K.speed_bands(gg, (-1, -0.5), n=4, lengths=(12, 8, 14, 7), body=body); v.append(('diag 4 bands', gg, (16, 40, 104, 110)))
    D['speed_bands'] = v
    # (4) afterimage
    v = []
    g, own = base('dash_SE_f1')
    sil = (g != '.') & ~np.isin(g, list('tTw'))
    gg = g.copy(); K.afterimage(gg, sil); v.append(('2 multiples -7/-14', gg, (4, 36, 100, 110)))
    gg = g.copy(); K.afterimage(gg, sil, offsets=((-7, -3), (-14, -6))); v.append(('diagonal travel', gg, (4, 30, 100, 110)))
    D['afterimage'] = v
    # (5) impact star
    v = []
    for st in (0, 1, 2):
        g = K.blank(); K.impact_star(g, (64, 64), stage=st, rot=-30); v.append((f'stage {st}', g, (40, 40, 88, 88)))
    g = K.blank(); K.impact_star(g, (64, 64), star='x', rot=60); v.append(('x star', g, (40, 40, 88, 88)))
    g, own = base('slash_SE_k2')
    K.impact_star(g, (93, 66), rot=-40, skip=((150, 240),), guard=K.head_guard(own)); v.append(('on k2 tip, skip arm', g, (40, 30, 120, 110)))
    D['impact_star'] = v
    # (6) dust
    v = []
    for st in (0, 1, 2):
        g = K.blank(); K.dust(g, [(62, 70, -1), (66, 70, 1)], stage=st); v.append((f'stage {st}', g, (40, 54, 88, 78)))
    g, own = base('jump_E_land')
    feet = A.feet_points(g)
    K.dust(g, feet, stage=1); v.append(('land feet', g, (24, 60, 104, 110)))
    D['dust'] = v
    # (7) streaks
    v = []
    g, own = base('jump_E_apex')
    lo = A.feet_points(g, ground=None)
    gg = g.copy(); K.streaks(gg, [(x, y) for x, y, _ in lo[:1]], vector=(0, 1), n=3, lengths=(6, 9, 5)); v.append(('rise, under feet', gg, (24, 40, 104, 120)))
    g, own = base('dash_SE_f1')
    gg = g.copy(); K.streaks(gg, [(50, 101)], vector=(-1, 0), n=2, lengths=(10, 6), spacing=3); v.append(('dash ground', gg, (16, 60, 104, 110)))
    D['streaks'] = v
    # (8) acting: head offsets + bow lag (driver curve) is a chart, drawn separately
    return D


def render_panel(g, box, z, bg, label=None):
    x0, y0, x1, y1 = box
    a = K.to_rgba(g)[y0:y1, x0:x1]
    im = Image.new('RGBA', (a.shape[1], a.shape[0]), bg + (255,))
    im.alpha_composite(Image.fromarray(a))
    im = im.resize((a.shape[1] * z, a.shape[0] * z), Image.NEAREST)
    if label:
        d = ImageDraw.Draw(im); d.rectangle([0, 0, len(label) * 6 + 6, 12], fill=(20, 20, 26)); d.text((3, 1), label, fill=(240, 240, 240))
    return im


def board(name, items, out, z=6):
    rows = []
    for bg in (SLATE, GRASS):
        ims = [render_panel(g, box, z, bg, lab) for lab, g, box in items]
        W = sum(i.width for i in ims) + 6 * (len(ims) - 1); H = max(i.height for i in ims)
        r = Image.new('RGBA', (W, H), (20, 20, 26, 255)); x = 0
        for i in ims: r.paste(i, (x, 0)); x += i.width + 6
        rows.append(r)
    W = max(r.width for r in rows); H = sum(r.height for r in rows) + 6 + 18
    b = Image.new('RGBA', (W, H), (20, 20, 26, 255))
    ImageDraw.Draw(b).text((4, 3), f'{name}  (6x: slate / grass)', fill=(255, 220, 120))
    y = 18
    for r in rows: b.paste(r, (0, y)); y += r.height + 6
    b.save(os.path.join(out, f'{name}_6x.png'))
    # 1x strip: each panel at 1x on slate and grass, 2x upscale of the strip for legibility is NOT applied
    strip = []
    for bg in (SLATE, GRASS):
        ims = [render_panel(g, box, 1, bg) for lab, g, box in items]
        W = sum(i.width for i in ims) + 2 * len(ims); H = max(i.height for i in ims)
        r = Image.new('RGBA', (W, H), (20, 20, 26, 255)); x = 0
        for i in ims: r.paste(i, (x, 0)); x += i.width + 2
        strip.append(r)
    s = Image.new('RGBA', (max(r.width for r in strip), sum(r.height for r in strip) + 2), (20, 20, 26, 255))
    s.paste(strip[0], (0, 0)); s.paste(strip[1], (0, strip[0].height + 2))
    s.save(os.path.join(out, f'{name}_1x.png'))
    return b, s


def acting_chart(out, z=6):
    """the lag driver on a test move: driver (grey), bow (red) and ribbon tip (pink), per key"""
    drv = [0, -6, 4, 10, 10, 10, 10]
    bow = A.lag(drv, lag=1, overshoot=2)
    rib = A.lag(drv, lag=1, overshoot=3, tip=True)
    W, H = 40 * len(drv), 120
    im = Image.new('RGBA', (W, H), (20, 20, 26, 255)); d = ImageDraw.Draw(im)
    def y(v): return H / 2 - v * 3.5
    for i in range(len(drv)):
        d.line([(i * 40 + 20, 0), (i * 40 + 20, H)], fill=(50, 50, 60)); d.text((i * 40 + 14, H - 12), f'k{i}', fill=(200, 200, 200))
    for seq, col in ((drv, (160, 160, 170)), ([a + b for a, b in zip(drv, bow)], (216, 52, 62)), ([a + b for a, b in zip(drv, rib)], (248, 181, 200))):
        pts = [(i * 40 + 20, y(v)) for i, v in enumerate(seq)]
        d.line(pts, fill=col, width=2)
        for p in pts: d.rectangle([p[0] - 2, p[1] - 2, p[0] + 2, p[1] + 2], fill=col)
    d.text((4, 3), 'acting.lag: driver grey / bow red (1-key lag, +2 overshoot) / ribbon tip pink (+3)', fill=(255, 220, 120))
    im.save(os.path.join(out, 'acting_lag_chart.png'))
    return im


def main(out):
    os.makedirs(out, exist_ok=True)
    D = demos()
    bs, ss = [], []
    for name, items in D.items():
        b, s = board(name, items, out)
        bs.append(b); ss.append(s)
        for i, (lab, g, box) in enumerate(items):
            K.save(g, os.path.join(out, f'{name}_v{i}.png'))
    ch = acting_chart(out)
    bs.append(ch)
    W = max(b.width for b in bs); H = sum(b.height for b in bs) + 8 * len(bs)
    big = Image.new('RGBA', (W, H), (12, 12, 16, 255)); y = 0
    for b in bs: big.paste(b, (0, y)); y += b.height + 8
    big.save(os.path.join(out, 'kit_board_6x.png'))
    W = max(s.width for s in ss); H = sum(s.height for s in ss) + 4 * len(ss)
    st = Image.new('RGBA', (W, H), (12, 12, 16, 255)); y = 0
    for s in ss: st.paste(s, (0, y)); y += s.height + 4
    st.save(os.path.join(out, 'kit_strip_1x.png'))
    print('boards ->', out, [n for n in D])


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'hybrid', 'S7_fxkit', 'r3', 'kit'))
