"""S7 r3 STANDARD TEST SET build: FX kit (tools/hybrid/fx/kit.py) + acting driver (tools/hybrid/fx/acting.py) on
the shared bodies.  Bodies:
  - turn_* and walk_SE_k*: S3 r2 POLISHED (the frozen identity base; walk has no smears by spec) - copied as-is.
  - slash_SE_k*, jump_E_*: S5 r2 acted keys re-rendered through the h3 compositor with ALL old FX removed, plus S7
    acting overrides (bow lag from acting.lag, ribbons from acting.ribbon, apex lifted 10 px into the air, k3 low
    follow-through) - then every smear / spark / dust / streak comes from the kit.
  - bonus run_SE_f1 / dash_SE_f1 (S3 r2 bonus poses, FX removed): kit demo of the S3 run / dash language.
  .venv/bin/python tools/hybrid/s7/build.py [OUT]     (default hybrid/S7_fxkit/r3)
"""
import copy
import json
import math
import os
import shutil
import sys

import numpy as np

ROOT = '/Users/waylonhuang/Documents/other/pixelart/swordswoman'
sys.path.insert(0, f'{ROOT}/tools/hybrid/fx'); sys.path.insert(0, f'{ROOT}/tools/hybrid/s7')
import kit as K
import acting as A
import base as BASE

OUT = sys.argv[1] if len(sys.argv) > 1 else f'{ROOT}/hybrid/S7_fxkit/r3'
S3POL = f'{ROOT}/hybrid/S3_editchain/r2/polished'
S5POL = f'{ROOT}/hybrid/S5_pixelnative/r2/polished'
LOG = []
DIRS = ['S', 'SE', 'E', 'NE', 'N', 'NW', 'W', 'SW']


def note(name, what):
    LOG.append(dict(sprite=name, op=what))


def clampbow(o):
    return (max(-3, min(3, o[0])), max(-1, min(2, o[1])))


# ------------------------------------------------------------------ frame overrides (acting)
def slash_frames():
    F = BASE.spec('slash_SE')
    import importlib.util
    s = importlib.util.spec_from_file_location('s5slash', f'{ROOT}/tools/hybrid/s5r2/anims/slash_SE.py')
    m = importlib.util.module_from_spec(s); s.loader.exec_module(m)
    # bow / bun lag: acting.lag on the head path (rest key first), hit-stop k2 frozen
    H = [(0, 0)] + [tuple(h) for h in m.HEAD]
    bow = [clampbow(o) for o in A.lag(H, overshoot=2, cap=3, holds=(3,))[1:]]
    # ribbons: acting.ribbon on the cut's travel (coil back, whip, stop at the hit, drift)
    virt = [(0, 0), (-10, 0), (6, 2), (14, 3), (14, 2)]
    rootN = [(58, 75)] + [(58 + m.BODY[k][0] + m.TORSO[k][0], 75 + m.BODY[k][1] + m.TORSO[k][1]) for k in range(4)]
    rootF = [(71, 74)] + [(71 + m.BODY[k][0] + m.TORSO[k][0], 74 + m.BODY[k][1] + m.TORSO[k][1]) for k in range(4)]
    restN = [(58, 75), (55, 77), (52, 79), (50, 82), (50, 85), (48, 88), (48, 91)]     # turn_SE cel rest chains
    restF = [(71, 74), (75, 76), (78, 79), (79, 83), (78, 86), (80, 89)]
    RN = A.ribbon(rootN, (-0.3, 1.0), virt, overshoot=3, cap=5, holds=(3,), rest_shape=restN)[1:]
    RF = A.ribbon(rootF, (0.6, 1.0), virt, overshoot=2, cap=4, holds=(3,), rest_shape=restF)[1:]
    for k in range(4):
        f = F[f'slash_SE_k{k}']
        f['bow'] = bow[k]
        f['pose']['ribbonN'] = RN[k]; f['pose']['ribbonF'] = RF[k]
        f.pop('fx', None)
    # k3: LOW follow-through (r2 decision: blade low and across ~30 deg below horizontal, body settling over the
    # lead knee) instead of the r2 high snap that read as a second wind-up
    f = F['slash_SE_k3']
    f['pose']['armN'] = dict(upper=((63, 81), (68, 84)), cuff=((66, 83), (77, 88), 4, 8), hand=(78, 88))
    f['pose']['armF'] = dict(upper=None, cuff=((78, 82), (79, 83), 1, 1))
    f['pose']['katana'] = (80, 89, 30.0, 18, 1)
    f['pose'].pop('extra', None)
    f['head'] = (m.HEAD[3][0] - 1, m.HEAD[3][1] + 1)
    return F, m, bow


def jump_frames():
    F = BASE.spec('jump_E')
    import importlib.util
    s = importlib.util.spec_from_file_location('s5jump', f'{ROOT}/tools/hybrid/s5r2/anims/jump_E.py')
    m = importlib.util.module_from_spec(s); s.loader.exec_module(m)
    H = [(0, 0)] + [tuple(h) for h in m.HEAD]
    bow = [clampbow(o) for o in A.lag(H, overshoot=2, cap=3)[1:]]
    for k, n in enumerate(['jump_E_crouch', 'jump_E_apex', 'jump_E_land']):
        F[n]['bow'] = bow[k]; F[n].pop('fx', None)
    # apex: 10 px of REAL air inside the cell (r2 gate amendment: airborne feet >= 8 px above the baseline);
    # the ground shadow stays on the pivot row (engine layer)
    F['jump_E_apex']['shift'] = (0, -6)
    return F, m, bow


# ------------------------------------------------------------------ FX per key (kit only)
def owner_mask(own, layers, box=None):
    m = np.isin(np.asarray(own, dtype='<U16'), list(layers))
    if box:
        x0, y0, x1, y1 = box
        r = np.zeros_like(m); r[y0:y1 + 1, x0:x1 + 1] = True; m &= r
    return m


def fx_slash(name, g, own, m):
    gd = K.head_guard(own)
    CX, CY, CR = m.CX, m.CY, m.CR
    src = g.copy()
    if name.endswith('k0'):
        # anticipation: no smear (ANIM 4); a 2-band wind-up flick behind the drawn-back blade tip only
        K.speed_bands(g, (1, 0.45), n=2, lengths=(5, 4), origins=[(33, 61), (31, 65)], guard=gd, thick_frac=0.5)
        note(name, 'speed_bands x2 (5/4 px) behind the coiled blade tip: wind-up flick')
    elif name.endswith('k1'):
        hand = owner_mask(own, ('armX', 'katana'), (60, 80, 82, 92)) & np.isin(src, list('sSmKtTwvrR'))
        arms = owner_mask(own, ('armX', 'armL'), (56, 76, 80, 92)) & ~np.isin(src, list('K'))
        # stretched-limb: arms + sleeves dragged back along the swing toward the coil side (one elongated shape)
        p = K.crescent(g, (CX, CY), CR, 155, 31, lead_px=8, tail_px=1.5, rim_px=3, echo=True, echo_px=3, cut=hand, guard=gd,
                       front=lambda x, y: y >= 81, front_rows=99)
        note(name, f'crescent c({CX},{CY}) r{CR} 155->31 lead 8 rim 2 + echo; front plane (y>=81) over the body; '
                   f'hand/hilt cut-mask: {len(p)} px')
        # stretched-limb: arms + sleeves dragged back along the swing (toward the coil side), hugging the arc
        K.limb_multiples(g, src, arms, [(-6, 0), (-12, -2), (-17, -6)], mode='stretch', guard=gd, erode_tail=2)
        note(name, 'limb_multiples stretch: arms/sleeves swept back 17 px along the arc')
    elif name.endswith('k2'):
        tip = (93, 66)
        K.sliver(g, (CX, CY), CR, 155, 24, keep=0.4, thick=2, guard=gd, front=lambda x, y: y >= 84)
        K.impact_star(g, tip, stage=0, star='plus', stroke_r=8, stroke_len=6, rot=-50, skip=((140, 250),), guard=gd)
        note(name, 'sliver (lead 40 %) + impact_star stage 0 at the blade tip (93,66), shock arc rot -50')
    elif name.endswith('k3'):
        # the blade carried on DOWN past the hit (low recovery arc): 2 dissolving wisps along that new arc,
        # just behind the k3 tip; no arc on the body, nothing left at the old hit point (no confetti)
        K.sliver(g, (78, 82), 18, -50, 36, keep=0.75, thick=2, guard=gd)
        note(name, 'thin dissolving sliver on the low recovery arc c(78,82) r18 -50->36 deg (ends at the tip)')
    return g


def fx_jump(name, g, own):
    gd = K.head_guard(own)
    feet = A.feet_points(g)
    if name.endswith('crouch'):
        K.dust(g, [(feet[0][0], feet[0][1], -1), (feet[1][0], feet[1][1], 1)], stage=0, grit=False, guard=gd)
        note(name, 'dust stage 0 at both feet (push-off)')
    elif name.endswith('apex'):
        body = (g != '.') & ~np.isin(g, list('tTw'))
        ys, xs = np.nonzero(body)
        low = xs[ys >= ys.max() - 1]
        cx = int(round(low.mean()))
        K.streaks(g, [(cx, int(ys.max()))], vector=(0, 1), n=3, lengths=(4, 6, 3), spacing=3, gap=3, guard=gd, thick_frac=0.3)
        note(name, 'streaks x3 (4/6/3), 3 px under the soles: the tail of the rise, detaching at the hang')
    elif name.endswith('land'):
        K.dust(g, [(feet[0][0], 104, -1), (feet[1][0] if False else feet[1][0], 104, 1)], stage=1, guard=gd)
        note(name, 'dust stage 1 attached to both feet + grit')
    return g


def fx_bonus(name, g, own):
    gd = K.head_guard(own)
    src = g.copy()
    if name == 'run_SE_f1':
        leg = owner_mask(own, ('legs',), (40, 90, 60, 104))
        K.limb_multiples(g, src, leg, [(-3, -1), (-7, -2)], mode='stretch', erode_tail=1, guard=gd)
        K.speed_bands(g, (-1, 0), n=2, lengths=(7, 5), origins=[(41, 86), (43, 89)], guard=gd)
        note(name, 'back-leg stretch + 2 speed bands behind the hem')
    elif name == 'dash_SE_f1':
        sil = (src != '.') & ~np.isin(src, list('tTw')) & ~np.isin(np.asarray(own, dtype='<U16'), ['ribbonN', 'ribbonF'])
        head = owner_mask(own, ('HEAD',)) | (owner_mask(own, ('collar', 'collar_over', 'torso')) & sil)
        K.afterimage(g, sil, offsets=((-8, -2), (-17, -4)), guard=gd, far_mask=head, smooth=1, travel=(1, 0))
        K.speed_bands(g, (-1, 0), n=3, lengths=(12, 9, 14), body=(src != '.'), guard=gd)
        K.streaks(g, [(52, 102)], vector=(-1, 0), n=1, lengths=(10,), gap=2, guard=gd)
        note(name, 'afterimage x2 contour multiples (near full -8, far head+torso partial -17) + 3 rimmed speed bands + ground streak')
    return g


def main():
    for d in ('sprite', 'hires', 'sprite/bonus', 'base'):
        os.makedirs(f'{OUT}/{d}', exist_ok=True)
    # 1 identity base (copied)
    for n in [f'turn_{d}' for d in DIRS] + [f'walk_SE_k{k}' for k in range(4)]:
        shutil.copy(f'{S3POL}/{n}.png', f'{OUT}/sprite/{n}.png')
        note(n, 'copied S3 r2 polished (frozen identity base, no FX by spec)')
    # 2 acted keys
    SF, sm, sbow = slash_frames()
    JF, jm, jbow = jump_frames()
    meta = dict(slash_bow=sbow, jump_bow=jbow)
    for name, fs in list(SF.items()) + list(JF.items()):
        a, info = BASE.render_body(fs)
        g = K.to_grid(a)
        own = np.array(info['owner'], dtype='<U16')
        K.save(g, f'{OUT}/base/{name}.png'); np.save(f'{OUT}/base/{name}_owner.npy', own)
        g = fx_slash(name, g, own, sm) if name.startswith('slash') else fx_jump(name, g, own)
        K.save(g, f'{OUT}/sprite/{name}.png')
        for src in (f'{S5POL}/{name}_hires.png',):
            if os.path.exists(src):
                shutil.copy(src, f'{OUT}/sprite/{name}_hires.png'); shutil.copy(src, f'{OUT}/hires/{name}.png')
    # 3 bonus
    B = BASE.bonus()
    for name, fs in B.items():
        a, info = BASE.render_body(fs)
        g = K.to_grid(a); own = np.array(info['owner'], dtype='<U16')
        g = fx_bonus(name, g, own)
        K.save(g, f'{OUT}/sprite/bonus/{name}.png')
    from PIL import Image
    for f in os.listdir(f'{OUT}/sprite'):
        if f.endswith('.png') and not f.endswith(('_4x.png', '_hires.png')):
            Image.open(f'{OUT}/sprite/{f}').resize((512, 512), Image.NEAREST).save(f'{OUT}/sprite/{f[:-4]}_4x.png')
    os.makedirs(f'{OUT}/work', exist_ok=True)
    json.dump(dict(edits=LOG, acting=meta), open(f'{OUT}/work/edits.json', 'w'), indent=1)
    print(len(LOG), 'ops ->', OUT)


if __name__ == '__main__':
    main()
