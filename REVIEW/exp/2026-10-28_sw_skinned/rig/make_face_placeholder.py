"""make_face_placeholder.py (R, round 5): placeholder anime face textures for the 3D head until F's art lands (F owns face/tex3d/).
UV = front-orthographic planar map of the head (H2 frame): u = 0.5 + x / 0.44 (her left = image right), v = (z - 1.38) / 0.44; 1024 x 1024,
image row = (1 - v) * 1024. Pixels are MATID-coded (flat colours of rig/face_mats.json; alpha 0 = keep the base skin). Feature centres
come from rig/face_anchors.json (uv). One file per expression and blink/mouth state: <expr>.png, <expr>_blink.png, <expr>_half.png,
<expr>_open.png (+ _blink_open / _half_open), and <name>_col.png preview colours (palette base colours)."""
import os, json, math
import numpy as np
from PIL import Image, ImageDraw
H = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(H, 'face_tex'); os.makedirs(OUT, exist_ok=True)
FM = json.load(open(os.path.join(H, 'face_mats.json')))['mats']
A = json.load(open(os.path.join(H, 'face_anchors.json')))['anchors']; S = 1024
def uv(n): u, v = A[n]['uv']; return u * S, (1 - v) * S
EW, EH = 0.19 * S, 0.19 * S  # eye box
COL = {'eye_white': '#f6eeea', 'iris': '#5e4a45', 'lash': '#160c0d', 'mouth': '#a5706b', 'blush': '#e58f84', 'skin': '#eaa991'}
def draw(expr, blink='', mouth=''):
    im = Image.new('RGBA', (S, S), (0, 0, 0, 0)); d = ImageDraw.Draw(im); c = lambda k: tuple(FM[k]) + (255,)
    eyes = {'neutral': 'open', 'smile': 'open', 'determined': 'open', 'focused': 'open', 'surprised': 'wide', 'joyful': 'happy', 'squint': 'squint',
            'effort': 'squint', 'pained': 'x', 'hurt': 'x', 'wince': 'squint'}.get(expr, 'open')
    if blink == 'blink': eyes = 'closed'
    elif blink == 'half' and eyes in ('open', 'wide'): eyes = 'half'
    brow = {'determined': 'angry', 'focused': 'angry', 'effort': 'angry', 'pained': 'worried', 'hurt': 'worried', 'wince': 'worried', 'surprised': 'up'}.get(expr, 'soft')
    mo = {'smile': 'smile', 'joyful': 'open', 'surprised': 'o', 'effort': 'open', 'pained': 'open', 'hurt': 'open', 'determined': 'flat', 'focused': 'flat', 'wince': 'flat'}.get(expr, 'line')
    if mouth == 'open' and mo in ('line', 'flat', 'smile'): mo = 'open'
    for side in ('L', 'R'):
        x, y = uv('eye.' + side); inner = -1 if side == 'L' else 1  # inner corner toward the nose (image centre)
        if eyes in ('open', 'wide', 'half'):
            h = EH * (1.15 if eyes == 'wide' else 0.55 if eyes == 'half' else 1.0); top = y - h / 2 + (EH * 0.45 if eyes == 'half' else 0)
            d.ellipse((x - EW / 2, top, x + EW / 2, y + EH / 2), fill=c('eye_white'))
            iw = EW * (0.5 if eyes == 'wide' else 0.62); d.ellipse((x - iw / 2, top + EH * 0.05, x + iw / 2, y + EH / 2), fill=c('iris'))
            d.ellipse((x - iw * 0.18, top + EH * 0.35, x + iw * 0.18, top + EH * 0.65), fill=c('lash'))  # pupil
            d.ellipse((x - iw * 0.42, top + EH * 0.12, x - iw * 0.12, top + EH * 0.40), fill=c('eye_white'))  # catchlight
            d.rectangle((x - EW * 0.58, top - EH * 0.10, x + EW * 0.58, top + EH * 0.12), fill=c('lash'))  # thick upper lash
            d.polygon([(x - inner * EW * 0.58, top - EH * 0.1), (x - inner * EW * 0.78, top - EH * 0.28), (x - inner * EW * 0.5, top + EH * 0.1)], fill=c('lash'))  # wing
        elif eyes in ('closed', 'squint'):
            yy = y + (EH * 0.1 if eyes == 'closed' else 0); d.arc((x - EW * 0.6, yy - EH * 0.35, x + EW * 0.6, yy + EH * 0.35), 200 if eyes == 'squint' else 10, 340 if eyes == 'squint' else 170, fill=c('lash'), width=int(EH * 0.16))
        elif eyes == 'happy':
            d.arc((x - EW * 0.55, y - EH * 0.2, x + EW * 0.55, y + EH * 0.6), 200, 340, fill=c('lash'), width=int(EH * 0.17))
        elif eyes == 'x':
            for a_ in (1, -1): d.line((x - EW * 0.45, y - a_ * EH * 0.3, x + EW * 0.45, y), fill=c('lash'), width=int(EH * 0.14))
        bx, by = uv('brow.' + side); tilt = {'angry': 0.10, 'worried': -0.10, 'up': 0.0, 'soft': 0.03}[brow] * S * inner * -1
        by -= 0.05 * S if brow == 'up' else 0
        d.line((bx - EW * 0.5, by - tilt, bx + EW * 0.5, by + tilt), fill=c('lash'), width=int(0.035 * S))
        cx, cy = uv('cheek.' + side); d.ellipse((cx - 0.06 * S, cy - 0.025 * S, cx + 0.06 * S, cy + 0.025 * S), fill=c('blush'))
    mx, my = uv('mouth'); w = 0.07 * S
    if mo == 'line': d.line((mx - w / 2, my, mx + w / 2, my), fill=c('mouth'), width=int(0.02 * S))
    elif mo == 'flat': d.line((mx - w * 0.4, my, mx + w * 0.4, my), fill=c('mouth'), width=int(0.024 * S))
    elif mo == 'smile': d.arc((mx - w / 2, my - 0.04 * S, mx + w / 2, my + 0.02 * S), 20, 160, fill=c('mouth'), width=int(0.02 * S))
    elif mo == 'o': d.ellipse((mx - w * 0.3, my - w * 0.35, mx + w * 0.3, my + w * 0.35), fill=c('mouth'))
    else: d.chord((mx - w / 2, my - 0.03 * S, mx + w / 2, my + 0.05 * S), 0, 180, fill=c('mouth'))
    return im
EXPR = ['neutral', 'smile', 'joyful', 'determined', 'focused', 'effort', 'surprised', 'squint', 'pained', 'hurt', 'wince']
inv = {tuple(v): k for k, v in FM.items()}
n = 0
for e in EXPR:
    for b in ('', 'blink', 'half'):
        for m in ('', 'open'):
            im = draw(e, b, m); nm = '_'.join([x for x in (e, b, m) if x]); im.save(os.path.join(OUT, nm + '.png'))
            a = np.asarray(im).copy(); out_ = np.zeros_like(a)
            for k, v in FM.items():
                m_ = (a[..., 3] > 0) & np.all(a[..., :3] == np.array(v), -1); h = COL.get(k, COL['skin'])
                out_[m_] = [int(h[1:3], 16), int(h[3:5], 16), int(h[5:7], 16), 255]
            col = Image.fromarray(out_, 'RGBA')
            col.save(os.path.join(OUT, nm + '_col.png')); n += 1
print('wrote', n, 'expression textures to', OUT)
