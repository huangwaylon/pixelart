"""Overlay an Omni pose skeleton (normalised frame) on a front/side render (render.py framing) for checking.
Usage: venv/bin/python -I skel_overlay.py POSE.txt RENDER_PREFIX OUT.png [scale=0.98]
"""
import sys
import numpy as np
from PIL import Image, ImageDraw
P = np.loadtxt(sys.argv[1]); pre = sys.argv[2]; out = sys.argv[3]
k = float(sys.argv[4]) if len(sys.argv) > 4 else 0.98
ims = []
for view in ('front', 'side'):
    im = Image.open(f'{pre}_{view}.png').convert('RGBA'); R = im.size[0]
    bg = Image.new('RGBA', im.size, (255, 255, 255, 255)); bg.alpha_composite(im); d = ImageDraw.Draw(bg)
    FEET = R / 2 + R / 2.3; u_ = R / 2.3
    def px(p):
        h = p[0] if view == 'front' else -p[2]  # side camera at +X: screen right = -Z
        return (R / 2 + h / k * u_, FEET - (p[1] / k + 1) * u_)
    for r in P:
        d.line([px(r[:3]), px(r[3:])], fill=(220, 0, 0) if r[0] < -0.005 else (0, 60, 230), width=2)
    ims.append(bg)
S = Image.new('RGBA', (sum(i.size[0] for i in ims), ims[0].size[1]))
x = 0
for i in ims:
    S.paste(i, (x, 0)); x += i.size[0]
S.convert('RGB').save(out)
