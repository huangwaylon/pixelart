"""face2/measure.py: face measurements of the turnE_final illustrations (face round 2).
Writes v2/m96/face_measure.json + face2/measure_<V>.png overlays (<=800px).
- raw: landmarks read on the raw illustration (px), as fractions of crown(hair top)->chin(chin outline) and of the face width.
- spr: the same landmarks in sprite (128-cell) coords, read on the WARPED source geo/src_V.png (the masters' own frame,
  tools/geom.py), plus the auto face contour (skin edge per sprite row) from that warped source.
Sprite target = round to pixels: row r covers [r, r+1)."""
import sys, json, numpy as np
R = '/Users/waylonhuang/Documents/other/pixelart/swordswoman/'
sys.path.insert(0, R + 'v2/pixelize/tools'); import pzlib as Z
from PIL import Image, ImageDraw

RAW = {  # raw illustration px (752x1424), read on grid crops (face2/gridcrop.py) + dark-pixel scans
 'S': dict(src='iso_S', crown=60, chin=[384, 507], face_w=[279, 478, 'skin edge at the eye line y=400'],
           lash_top=367, lash_band=[367, 379], iris_c=[[315, 393], [435, 393]], eye_bottom=418, eye_x=[[278, 337], [412, 472]],
           brow=[[290, 345, 333, 345], [405, 470, 335, 348]], nose=[372, 436], mouth=[350, 402, 460],
           jaw=[[288, 460, 460], [316, 432, 484], [344, 412, 500]], chin_flat=[352, 404, 504]),
 'SE': dict(src='iso_SE_fixed', crown=69, chin=[440, 514], lash_top_near=386, lash_top_far=372, eye_bottom_near=450, eye_bottom_far=432,
           eye_x=[[345, 412], [470, 520]], brow_far=[470, 525, 350, 357], nose=[468, 455], mouth=[423, 462, 481],
           far_cheek_x=[[497, 473], [477, 498]], blush=[[340, 407, 453, 477], [477, 497, 450, 470]]),
 'E': dict(src='iso_E', crown=76, chin=[500, 488], lash_top=347, iris_c=[483, 375], eye_bottom=400, eye_x=[448, 499],
           brow=[470, 525, 315, 322], nose_tip=[541, 412], mouth=[497, 520, 442],
           profile=[[545, 330, 'forehead'], [528, 362, 'bridge'], [541, 412, 'nose tip'], [527, 428, 'philtrum'], [530, 437, 'upper lip'],
                    [528, 452, 'lower lip'], [511, 466, 'chin front'], [500, 488, 'chin bottom']]),
}
SPR = {  # sprite coords (continuous; row r = [r, r+1)) read on face2/sprgrid.py crops of the warped sources
 'S': dict(lash_top=49.7, lash_band=[49.7, 50.7], iris_c=[[59.0, 52.0], [68.5, 52.0]], eye_bottom=53.8, eye_x=[[56.0, 60.8], [67.0, 72.3]],
           brow=[[56.2, 61.2, 47.9, 48.5], [66.8, 72.0, 48.5, 49.0]], nose=[63.5, 54.7, 55.5], mouth=[62.0, 66.0, 57.0, 57.3],
           chin=[63.0, 61.0], chin_flat=[61.7, 64.3], blush=[[56.7, 60.7, 54.7, 56.7], [67.7, 71.7, 54.7, 56.7]]),
 'SE': dict(lash_top=[51.5, 50.8], iris_c=[[65.3, 54.0], [73.0, 53.0]], eye_bottom=[56.0, 55.0], eye_x=[[62.2, 67.0], [71.7, 75.2]],
           brow_far=[70.5, 75.5, 49.3, 49.8], nose=[71.2, 55.8, 56.8], mouth=[68.0, 71.0, 58.3, 58.7], chin=[69.7, 60.8],
           blush=[[62.2, 66.0, 56.2, 58.0], [71.7, 74.7, 55.5, 57.3]]),
 'E': dict(lash_top=50.0, iris_c=[74.8, 52.3], eye_bottom=54.5, eye_x=[72.0, 76.0], brow=[73.0, 76.7, 47.0, 47.5],
           nose_tip=[79.2, 54.8], mouth=[76.0, 77.7, 58.0, 58.3], chin_bottom=[75.8, 62.0], blush=[72.0, 75.3, 54.7, 56.7],
           profile=[[80.2, 49.0, 'forehead'], [79.0, 50.5, ''], [78.0, 52.0, ''], [77.7, 53.0, 'bridge'], [79.2, 54.8, 'nose tip'],
                    [78.3, 56.3, 'philtrum'], [78.5, 57.5, 'upper lip'], [77.7, 58.0, 'mouth'], [77.8, 58.7, 'lower lip'], [77.0, 60.0, 'chin'],
                    [76.5, 61.0, ''], [75.8, 62.0, 'chin bottom']]),
}


def warped(v):
    meta = json.load(open(f'{R}v2/m96/masters/EC0_{v}_96.json')); x, m = Z.load(v, meta['src']); Hh, Ww = m.shape
    fx = lambda X: (X - meta['ox']) * Ww / meta['w']; fy = lambda Y: (Y - meta['oy']) * Hh / meta['h']
    ix = lambda X: meta['ox'] + X * meta['w'] / Ww
    return x, fx, fy, ix


def contour(v):
    """skin edge per sprite row (rows centre r+.5) from the warped source: S/SE left+right edge scanning out from the face
    centre below the mouth; SE far cheek + E profile = right-most skin scanning in from the right"""
    x, fx, fy, ix = warped(v); out = {}
    skin = lambda p: p[0] > 185 and p[1] > 120 and p[0] - p[2] > 35
    dark = lambda p: p.max() < 90 or p.min() > 235
    if v in ('S', 'SE'):
        cx = 63.5 if v == 'S' else 68.5
        for r in range(56, 61):
            row = x[int(fy(r + .5))]; res = []
            for d in (-1, 1):
                X = int(fx(cx))
                while 0 < X < len(row) - 1 and not dark(row[X]): X += d
                res.append(round(ix(X), 2))
            out[r] = res
    if v in ('SE', 'E'):
        a, b = (79, 66) if v == 'SE' else (83, 70)
        rows = range(53, 61) if v == 'SE' else range(49, 62)
        for r in rows:
            row = x[int(fy(r + .5))]; X = min(int(fx(a)), len(row) - 1)
            while X > int(fx(b)) and not skin(row[X]): X -= 1
            out.setdefault(r, [None, None])[1] = round(ix(X + 1), 2)
    return out


def frac(v):
    d = RAW[v]; c = d['crown']; ch = d['chin'][1]; hh = ch - c; f = lambda y: round((y - c) / hh, 3)
    o = dict(head_h_px=hh)
    for k in ('lash_top', 'lash_top_near', 'lash_top_far', 'eye_bottom', 'eye_bottom_near', 'eye_bottom_far'):
        if k in d: o[k] = f(d[k])
    if 'iris_c' in d: o['iris_c'] = f(d['iris_c'][0][1] if isinstance(d['iris_c'][0], list) else d['iris_c'][1])
    if 'brow' in d: b = d['brow'][0] if isinstance(d['brow'][0], list) else d['brow']; o['brow'] = f((b[2] + b[3]) / 2)
    if 'brow_far' in d: o['brow_far'] = f(sum(d['brow_far'][2:]) / 2)
    o['nose'] = f(d['nose'][1] if 'nose' in d else d['nose_tip'][1]); o['mouth'] = f(d['mouth'][2])
    if v == 'S':
        fw = d['face_w'][1] - d['face_w'][0]; o['face_w_px'] = fw
        o['eye_w_over_face_w'] = round((d['eye_x'][0][1] - d['eye_x'][0][0]) / fw, 3)
        o['eye_h_over_head_h'] = round((d['eye_bottom'] - d['lash_top']) / hh, 3)
        o['inter_eye_gap_over_face_w'] = round((d['eye_x'][1][0] - d['eye_x'][0][1]) / fw, 3)
        o['mouth_w_over_face_w'] = round((d['mouth'][1] - d['mouth'][0]) / fw, 3)
        o['jaw_w_over_face_w'] = {str(round((y - c) / hh, 3)): round((b - a) / fw, 3) for a, b, y in d['jaw']}
        o['chin_flat_over_face_w'] = round((d['chin_flat'][1] - d['chin_flat'][0]) / fw, 3)
    return o


def overlay(v, M):
    box = dict(S=(52, 44, 76, 63), SE=(56, 44, 80, 63), E=(62, 42, 84, 64))[v]; s = 30
    x, fx, fy, ix = warped(v); x0, y0, x1, y1 = box
    im = Image.fromarray(x.astype(np.uint8)).crop(tuple(int(round(t)) for t in (fx(x0), fy(y0), fx(x1), fy(y1)))).resize(((x1 - x0) * s, (y1 - y0) * s), Image.LANCZOS)
    d = ImageDraw.Draw(im); P = lambda X, Y: ((X - x0) * s, (Y - y0) * s)
    for X in range(x0, x1 + 1, 1): d.line([P(X, y0), P(X, y0 + .25)], fill=(0, 120, 255))
    for Y in range(y0, y1 + 1, 1): d.line([P(x0, Y), P(x0 + .25, Y)], fill=(0, 120, 255)); d.text(P(x0 + .3, Y), str(Y), fill=(0, 0, 255))
    sp = SPR[v]
    def hl(Y, col, lab):
        d.line([P(x0, Y), P(x1, Y)], fill=col, width=2); d.text(P(x1 - 3.5, Y - .5), lab, fill=col)
    lt = sp['lash_top'] if not isinstance(sp['lash_top'], list) else sp['lash_top'][0]
    hl(lt, (255, 0, 0), 'lash'); ic = sp['iris_c'][0] if isinstance(sp['iris_c'][0], list) else sp['iris_c']; hl(ic[1], (255, 140, 0), 'iris c')
    eb = sp['eye_bottom'] if not isinstance(sp['eye_bottom'], list) else sp['eye_bottom'][0]; hl(eb, (200, 0, 200), 'eye btm')
    n = sp.get('nose') or sp['nose_tip']; hl(n[1] if len(n) == 2 else (n[1] + n[2]) / 2, (0, 160, 0), 'nose')
    hl((sp['mouth'][2] + sp['mouth'][3]) / 2, (0, 0, 255), 'mouth')
    ch = sp.get('chin') or sp['chin_bottom']; hl(ch[1], (90, 60, 30), 'chin')
    if 'brow' in sp: b = sp['brow'][0] if isinstance(sp['brow'][0], list) else sp['brow']; hl((b[2] + b[3]) / 2, (120, 80, 0), 'brow')
    for r, (a, b) in M['spr']['contour'].items():
        for X in (a, b):
            if X is not None: c = P(X, int(r) + .5); d.ellipse([c[0] - 4, c[1] - 4, c[0] + 4, c[1] + 4], outline=(0, 255, 255), width=2)
    for bl in (sp.get('blush') if isinstance(sp.get('blush', [None])[0], list) else [sp['blush']] if 'blush' in sp else []):
        d.rectangle([P(bl[0], bl[2]), P(bl[1], bl[3])], outline=(255, 80, 160), width=2)
    for p in sp.get('profile', []): c = P(p[0], p[1]); d.ellipse([c[0] - 5, c[1] - 5, c[0] + 5, c[1] + 5], outline=(255, 0, 0), width=2)
    im.save(f'{R}v2/m96/face2/measure_{v}.png'); return im.size


if __name__ == '__main__':
    out = dict(_doc=__doc__, views={})
    for v in ('S', 'SE', 'E'):
        M = dict(raw=RAW[v], raw_frac=frac(v), spr=dict(SPR[v], contour={str(k): w for k, w in contour(v).items()}))
        out['views'][v] = M
        print(v, overlay(v, M), M['raw_frac'])
    out['views']['NE'] = dict(note='no face features (back 3/4): lash tip + cheek blush only; geometry unchanged')
    out['views']['N'] = dict(note='back view: no face')
    out['targets'] = json.load(open(R + 'v2/m96/face2/targets.json')) if __import__('os').path.exists(R + 'v2/m96/face2/targets.json') else None
    json.dump(out, open(R + 'v2/m96/face_measure.json', 'w'), indent=1)
