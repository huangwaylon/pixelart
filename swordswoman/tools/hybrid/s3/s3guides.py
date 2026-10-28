"""S3 pixelize wrapper: normalise scale by the HEAD (hair-mass width) so every sprite of the set shares
one head size, then run tools/hybrid/pixelize.pixelize with the guide as the material prior.
usage: px.py NAME [NAME...]   (reads hires/<NAME>.png, writes sprite_px/<NAME>.png + aux)"""
import sys, os, json
import numpy as np
sys.path.insert(0, 'tools/hybrid')
import pixelize as PX, hylib as H
from PIL import Image
R = 'hybrid/S3_editchain/r1'
HEAD_W = float(os.environ.get('HEAD_W', 27))
GUIDE = {}
D8 = ['S','SE','E','NE','N','NW','W','SW']
for d in D8: GUIDE[f'turn_{d}'] = f'hybrid/guide/p2/turn/{d}/f00'
for k in range(4):
    GUIDE[f'walk_SE_k{k}'] = f'hybrid/guide/p2/walk_SE_keys/SE/f{k:02d}'
    GUIDE[f'slash_SE_k{k}'] = f'hybrid/guide/p2/slash_SE_keys/SE/f{k:02d}'
for k, n in enumerate(['crouch','apex','land']): GUIDE[f'jump_E_{n}'] = f'hybrid/guide/p2/jump_E_keys/E/f{k:02d}'

def head_width(rgb, mask):
    ys, xs = np.nonzero(mask); y0, y1 = ys.min(), ys.max()
    k = 2; sm = rgb[::k, ::k].astype(float); m = mask[::k, ::k]
    cls, _ = H.classify(sm)
    hair = (cls == H.BASE.index('hair')) & m
    hair[int((y0 + 0.55 * (y1 - y0)) / k):] = False      # head zone only
    lab, sz = PX.label_cc(hair, 8)
    i = int(np.argmax(sz[1:]) + 1)
    hy, hx = np.nonzero(lab == i)
    # robust width: 95th-5th percentile of x over rows of the main hair blob
    return (np.percentile(hx, 99.5) - np.percentile(hx, 0.5)) * k

def run(name, out_dir='sprite_px'):
    inp = f'{R}/hires/{name}.png'
    img = Image.open(inp)
    rgb, mask, _ = PX.remove_bg(img, 'auto', 11.0)
    geo = PX.body_rows(rgb, mask)
    hw = head_width(rgb, mask)
    s = HEAD_W / hw
    tgt_h = int(round((geo['bottom'] - geo['top'] + 1) * s))
    g = H.Guide(GUIDE[name]) if hasattr(H, 'Guide') else None
    orig = PX.guide_geom
    def gg(gd):
        d = orig(gd); d['top'] = d['bottom'] - tgt_h + 1; return d
    PX.guide_geom = gg
    os.makedirs(f'{R}/{out_dir}', exist_ok=True)
    out = f'{R}/{out_dir}/{name}.png'
    res = PX.pixelize(inp, g, fit='none', verbose=False)
    PX.guide_geom = orig
    return res, hw, tgt_h, out

if __name__ == '__main__':
    for n in sys.argv[1:]:
        (spr, cls, meta, hi), hw, th, out = run(n)
        print(n, 'head_w_hi', round(hw), 'tgt_h', th, type(spr))
