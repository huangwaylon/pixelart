#!/usr/bin/env python3
"""Hand-keyed mannequin pose guides for the 48px SE pipeline (replaces the weak r6 3D guides: tiny legs, no leg swap).
pose48.py ACT  -> work48/<act>/guide/fNN.png (512px = 64 cell @8x, light grey bg) + guide/frames.json + guide/sheet.png
Keys live in tools/keys48.py (one dict per frame, degrees). 3D frame: f = forward (SE), u = up, z = her left.
Near side (screen-left) = her RIGHT limbs (z<0), drawn in front and lighter; far side = her LEFT, darker."""
import json, math, os, sys
from PIL import Image, ImageDraw
ROOT = '/Users/waylonhuang/Documents/other/pixelart/swordswoman'; A = ROOT + '/v2/anim_redraw'
sys.path.insert(0, A + '/tools'); from keys48 import KEYS  # noqa
S, CELL, FOOT, CX = 8, 64, 59.5, 30.5
HIP_H, THIGH, SHIN, TORSO, UARM, FARM = 10.5, 5.5, 5.5, 11.0, 4.5, 4.0
HIP_Z, SH_Z, SH_DOWN = 2.2, 4.6, 2.2
HEAD_R, NECK_HEAD = 10.0, 9.0
COL = dict(bg=(192, 192, 192), hair=(60, 50, 54), face=(248, 218, 194), red=(192, 58, 60), redfar=(132, 38, 62),
           obi=(44, 32, 44), skin=(248, 218, 194), skinfar=(200, 150, 140), boot=(40, 30, 42), bootfar=(70, 60, 80),
           eye=(42, 57, 90))
DEF = dict(lt=0, lk=0, rt=0, rk=0, la=-8, le=10, ra=-8, re=10, lean=0, bob=0, fwd=0, sq=1.0, head='neutral',
           tilt=0, ms=100, blade=None, fx=[], hem=0, bow=[0, 0], la_z=0, ra_z=0, spread=0, foot_l=0, foot_r=0)


def proj(f, u, z):
    return CX + 0.70 * (f + z), FOOT - 0.87 * u + 0.30 * (f - z)


def rot(f, u, deg, of, ou):
    a = math.radians(deg); df, du = f - of, u - ou
    return of + df * math.cos(a) + du * math.sin(a), ou - df * math.sin(a) + du * math.cos(a)


def pose(k):
    p = dict(DEF); p.update(k)
    pf, pu = p['fwd'], HIP_H + p['bob']
    J = {}
    # legs (angles from vertical, + = forward; knee bend + = shin swings back)
    for side, z in (('l', HIP_Z + p['spread']), ('r', -HIP_Z - p['spread'])):
        a = math.radians(p[side + 't']); b = math.radians(p[side + 't'] - p[side + 'k'])
        hip = (pf, pu, z)
        knee = (pf + THIGH * math.sin(a), pu - THIGH * math.cos(a), z)
        ank = (knee[0] + SHIN * math.sin(b), knee[1] - SHIN * math.cos(b), z)
        toe = (ank[0] + 1.6 * math.cos(math.radians(p['foot_' + side])), ank[1] + 1.6 * math.sin(math.radians(p['foot_' + side])), z)
        J[side + 'leg'] = (hip, knee, ank, toe)
    # torso (lean + squash around the pelvis)
    def up(f, u, z):
        u2 = pu + (u - pu) * p['sq']
        f2, u3 = rot(f, u2, p['lean'], pf, pu); return (f2, u3, z)
    neck = up(pf, pu + TORSO, 0)
    J['neck'] = neck
    hc = up(pf, pu + TORSO + NECK_HEAD, 0)
    hc = (hc[0] + math.sin(math.radians(p['tilt'])) * 2, hc[1], 0)
    J['head'] = hc
    for side, z in (('l', SH_Z), ('r', -SH_Z)):
        sh = up(pf, pu + TORSO - SH_DOWN, z)
        a = math.radians(p[side + 'a'] + p['lean']); b = math.radians(p[side + 'a'] + p[side + 'e'] + p['lean'])
        zz = p[side + 'a_z']
        el = (sh[0] + UARM * math.sin(a), sh[1] - UARM * math.cos(a), z + zz * 0.5)
        ha = (el[0] + FARM * math.sin(b), el[1] - FARM * math.cos(b), z + zz)
        J[side + 'arm'] = (sh, el, ha)
    J['waist'] = up(pf, pu + 3.0, 0); J['hem'] = up(pf + p['hem'] * 0.3, pu - 1.5, 0); J['pelvis'] = (pf, pu, 0)
    return p, J


def draw(p, J):
    im = Image.new('RGB', (CELL * S, CELL * S), COL['bg']); d = ImageDraw.Draw(im)
    P = lambda q: (proj(*q)[0] * S, proj(*q)[1] * S)
    def limb(pts, col, w):
        xy = [P(q) for q in pts]
        d.line(xy, fill=col, width=int(w * S), joint='curve')
        for x, y in xy: d.ellipse([x - w * S / 2, y - w * S / 2, x + w * S / 2, y + w * S / 2], fill=col)
    def leg(side, far):
        hip, knee, ank, toe = J[side + 'leg']
        limb([hip, knee, ank], COL['skinfar' if far else 'skin'], 2.6)
        limb([(ank[0], ank[1] + 1.2, ank[2]), ank, toe], COL['bootfar' if far else 'boot'], 3.0)
    def arm(side, far):
        sh, el, ha = J[side + 'arm']
        limb([sh, el], COL['redfar' if far else 'red'], 3.4)
        limb([el, ha], COL['redfar' if far else 'red'], 3.0)
        x, y = P(ha); r = 1.3 * S
        d.ellipse([x - r, y - r, x + r, y + r], fill=COL['skinfar' if far else 'skin'])
    arm('l', True); leg('l', True)
    # dress: hull of shoulder ring + flared hem ellipse
    import numpy as np
    pts = []
    nf, nu, _ = J['neck']; hf, hu, _ = J['hem']
    for t in np.linspace(0, 2 * math.pi, 24, endpoint=False):
        pts.append(P((nf + 2.6 * math.sin(t), nu - 1.0, 3.6 * math.cos(t))))
        pts.append(P((hf + 4.2 * math.sin(t), hu, 7.0 * math.cos(t))))
    from scipy.spatial import ConvexHull
    h = ConvexHull(np.array(pts)); d.polygon([tuple(pts[i]) for i in h.vertices], fill=COL['red'])
    wf, wu, _ = J['waist']
    d.line([P((wf + 2.8, wu, -5.0)), P((wf + 3.4, wu, 0)), P((wf + 2.8, wu, 5.0))], fill=COL['obi'], width=int(2.2 * S))
    leg('r', False)
    # head: hair disc, face patch toward the facing direction, eyes, bow
    hx, hy = P(J['head']); r = HEAD_R * S
    d.ellipse([hx - r, hy - r, hx + r, hy + r * 0.95], fill=COL['hair'])
    fx, fy = hx + 0.22 * r, hy + 0.30 * r
    d.ellipse([fx - 0.62 * r, fy - 0.42 * r, fx + 0.62 * r, fy + 0.50 * r], fill=COL['face'])
    d.rectangle([hx - 0.75 * r, hy - 0.55 * r, hx + 0.95 * r, fy - 0.25 * r], fill=COL['hair'])
    if p['head'] != 'blink':
        for ex in (fx - 0.28 * r, fx + 0.30 * r):
            d.rectangle([ex - 0.08 * r, fy - 0.12 * r, ex + 0.08 * r, fy + 0.16 * r], fill=COL['eye'])
    else:
        for ex in (fx - 0.28 * r, fx + 0.30 * r):
            d.rectangle([ex - 0.10 * r, fy + 0.04 * r, ex + 0.10 * r, fy + 0.10 * r], fill=COL['eye'])
    bx, by = hx + p['bow'][0] * S, hy - r * 0.95 + p['bow'][1] * S
    for s in (-1, 1):
        d.polygon([(bx, by), (bx + s * 0.55 * r, by - 0.35 * r), (bx + s * 0.6 * r, by + 0.2 * r)], fill=COL['red'])
    d.ellipse([bx - 0.12 * r, by - 0.12 * r, bx + 0.12 * r, by + 0.12 * r], fill=COL['redfar'])
    arm('r', False)
    if p['blade'] is not None:                       # katana in the near fist: dark hilt behind, 2px steel blade ahead
        hx_, hy_ = P(J['rarm'][2]); a = math.radians(p['blade']); c, s_ = math.cos(a), math.sin(a)
        d.line([(hx_ - c * 3.5 * S, hy_ - s_ * 3.5 * S), (hx_ + c * 1.0 * S, hy_ + s_ * 1.0 * S)], fill=(68, 55, 74), width=int(1.6 * S))
        d.line([(hx_ + c * 1.5 * S, hy_ + s_ * 1.5 * S), (hx_ + c * 17 * S, hy_ + s_ * 17 * S)], fill=(238, 240, 245), width=int(1.8 * S))
        x, y = hx_ + c * 1.0 * S, hy_ + s_ * 1.0 * S
        d.line([(x - s_ * 1.5 * S, y + c * 1.5 * S), (x + s_ * 1.5 * S, y - c * 1.5 * S)], fill=(26, 18, 32), width=int(1.0 * S))
        x, y = P(J['rarm'][2]); r = 1.3 * S
        d.ellipse([x - r, y - r, x + r, y + r], fill=COL['skin'])
    return im


def main():
    act = sys.argv[1]; ks = KEYS[act]
    out = f'{A}/work48/{act}/guide'; os.makedirs(out, exist_ok=True)
    meta = []
    for i, k in enumerate(ks):
        p, J = pose(k); im = draw(p, J); im.save(f'{out}/f{i:02d}.png')
        hand = proj(*J['rarm'][2]); el = proj(*J['rarm'][1])
        feet = max(proj(*J['lleg'][3])[1], proj(*J['rleg'][3])[1], proj(*J['lleg'][2])[1] + 1.2, proj(*J['rleg'][2])[1] + 1.2)
        meta.append(dict(ms=p['ms'], head=p['head'], blade=p['blade'], fx=p['fx'], bow=p['bow'],
                         hand=[round(hand[0], 1), round(hand[1], 1)], forearm=round(math.degrees(math.atan2(hand[1] - el[1], hand[0] - el[0])), 1),
                         pelvis_x=round(proj(*J['pelvis'])[0], 1), lift=round(max(0.0, FOOT - feet), 1),
                         hint=p.get('hint', '')))
    json.dump(dict(action=act, frames=meta), open(f'{out}/frames.json', 'w'), indent=1)
    n = len(ks); sh = Image.new('RGB', (n * 130, 130), (40, 40, 40))
    for i in range(n):
        sh.paste(Image.open(f'{out}/f{i:02d}.png').resize((128, 128), Image.LANCZOS), (i * 130, 0))
    sh.save(f'{out}/sheet.png'); print(f'{out}/sheet.png', n)


if __name__ == '__main__':
    main()
