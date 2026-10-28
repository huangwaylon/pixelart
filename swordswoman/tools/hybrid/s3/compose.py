"""S3 compose: pixelize the Gemini body (scaled so chin->sole matches the guide), erase the Gemini head,
paste the locked pixel head stamp (hybrid/lock/pixel/head_<DIR>.png) on the chin.
usage: compose.py NAME[:sink] ...  -> r1/sprite_px/NAME.png (+_4x, _hires, _meta)"""
import sys, os, json
import numpy as np
sys.path.insert(0, 'tools/hybrid'); sys.path.insert(0, 'tools/hybrid/s3')
import pixelize as PX, hylib as H
from PIL import Image
from s3guides import GUIDE
R = 'hybrid/S3_editchain/r1'
HEADDIR = lambda n: n.split('_')[1] if n.startswith('turn_') else ('E' if n.startswith('jump_E') else 'SE')

def head_mask_hi(rgb, mask, chin):
    k = 2; sm = rgb[::k, ::k].astype(float); m = mask[::k, ::k]
    cls, _ = H.classify(sm)
    ys, xs = np.nonzero(m); y0, y1 = ys.min(), ys.max()
    hair = (cls == H.BASE.index('hair')) & m
    hz = hair.copy(); hz[int(y0 + 0.6 * (y1 - y0)):] = False
    lab, sz = PX.label_cc(hz, 8); i = int(np.argmax(sz[1:]) + 1)
    hb = lab == i
    hy, hx = np.nonzero(hb)
    x0, x1, t = hx.min(), hx.max(), hy.min()
    c = chin // k
    box = np.zeros_like(m); box[max(0, t - int(0.35 * (c - t))):c, x0:x1 + 1] = True
    hm = box & m & ~((cls == H.BASE.index('steel')) | (cls == H.BASE.index('pink')))
    full = np.repeat(np.repeat(hm, k, 0), k, 1)[:mask.shape[0], :mask.shape[1]]
    return full

LIFT = {'jump_E_apex': 12}
SCALE_MUL = json.load(open('hybrid/S3_editchain/r1/scale_mul.json')) if os.path.exists('hybrid/S3_editchain/r1/scale_mul.json') else {}
STEEL = {(0x5f, 0x66, 0x78), (0xa8, 0xb0, 0xc0), (0xee, 0xf0, 0xf5)}
PINK = {(0xf4, 0x9a, 0xb0), (0xf8, 0xb5, 0xc8)}
def postfix(spr, bottom):
    a = spr[..., 3] > 0
    lab, sz = PX.label_cc(a, 8)
    dy = 0
    for i in range(1, len(sz)):
        if sz[i] < 8:
            m = lab == i
            cols = {tuple(c) for c in spr[m][:, :3]}
            if not cols <= (STEEL | PINK):
                spr[m] = 0
    a = spr[..., 3] > 0
    body = a & ~np.array([[tuple(spr[y, x, :3]) in STEEL | PINK for x in range(128)] for y in range(128)])
    lab, sz = PX.label_cc(body, 8)
    keep = np.isin(lab, [i for i in range(1, len(sz)) if sz[i] >= 15])
    low = np.nonzero(keep.any(1))[0].max()
    dy = int(bottom - low)
    if dy:
        out = np.zeros_like(spr)
        if dy > 0: out[dy:] = spr[:-dy]
        else: out[:dy] = spr[-dy:]
        spr = out
    return spr, dy

def run(name, sink=0, out_dir='sprite_px'):
    inp = f'{R}/hires/{name}.png'
    img = Image.open(inp); rgb, mask, _ = PX.remove_bg(img, 'auto', 11.0)
    ch = json.load(open(f'{R}/hires/{name}_chin.json'))
    geo = PX.body_rows(rgb, mask)
    g = H.load_guide(GUIDE[name])
    gj = json.load(open(GUIDE[name] + '_joints.json'))['joints']
    gg = PX.guide_geom(g)
    gchin = gj['chin']['cell'][1]
    s = float(os.environ.get('BODY_PX', 28)) / (geo['bottom'] - ch['chin'])
    REF = {'walk_SE': 'turn_SE', 'slash_SE': 'turn_SE', 'jump_E': 'turn_E'}
    HW_OVERRIDE = {'slash_SE_k1': 320.0}; HH_FIX = {}
    ref = next((v for k, v in REF.items() if name.startswith(k)), None)
    if ref:   # same-chain frames: keep the turn's scale, normalised by the drawn head width
        rm = json.load(open(f'{R}/sprite_px/{ref}_meta.json'))
        rc = json.load(open(f'{R}/hires/{ref}_chin.json'))
        hw = HW_OVERRIDE.get(name, ch['head_w']); hh = ch['chin'] - ch['hair_top']
        s = rm['scale'] * 0.5 * (rc['head_w'] / hw + (rc['chin'] - rc['hair_top']) / hh)
    s *= SCALE_MUL.get(name, 1.0)
    tgt_h = int(round(s * (geo['bottom'] - geo['top'] + 1)))
    orig = PX.guide_geom
    PX.guide_geom = lambda gd: dict(orig(gd), top=orig(gd)['bottom'] - tgt_h + 1)
    spr, cls, meta, hi = PX.pixelize(inp, g, fit='none', verbose=False, down=os.environ.get('DOWN', 'box'), quant=os.environ.get('QUANT', 'material'), penalty=float(os.environ.get('PEN', 6)))
    PX.guide_geom = orig
    ys, xs = np.nonzero(mask); bx0, by0 = xs.min(), ys.min()
    sc, (ox, oy) = meta['scale'], meta['offset']
    to_cell = lambda X, Y: (ox + (X - bx0) * sc, oy + (Y - by0) * sc)
    # erase Gemini head in the cell
    hm = head_mask_hi(rgb, mask, ch['chin'])
    yy, xx = np.nonzero(hm)
    cx, cy = to_cell(xx, yy)
    spr = spr.copy()
    ci = np.clip(np.round(cy - 0.5).astype(int), 0, 127); cj = np.clip(np.round(cx - 0.5).astype(int), 0, 127)
    er = np.zeros((128, 128), bool); er[ci, cj] = True
    spr[er] = 0
    # paste stamp
    st = np.array(Image.open(os.environ.get('STAMPS', 'hybrid/lock/pixel') + f'/head_{HEADDIR(name)}.png').convert('RGBA'))
    hcx, hcy = to_cell(ch['head_cx'], ch['chin'])
    top = int(round(hcy)) + sink - (st.shape[0] - 1) - 1
    left = int(round(hcx - 13))
    a = st[..., 3] > 0
    sub = spr[top:top + st.shape[0], left:left + st.shape[1]]
    sub[a] = st[a]
    spr, dy = postfix(spr, 105 - LIFT.get(name, 0)); top += dy
    os.makedirs(f'{R}/{out_dir}', exist_ok=True)
    out = f'{R}/{out_dir}/{name}.png'
    meta.update(s3=dict(chin_cell=hcy, head_cx_cell=hcx, stamp_top=top, stamp_left=left, sink=sink, tgt_h=tgt_h))
    PX.write_outputs(out, spr, cls, meta, hi, g, True)
    json.dump(meta, open(out.replace('.png', '_meta.json'), 'w'), indent=1, default=float)
    print(name, 'scale', round(sc, 4), 'stamp at', left, top, 'h', meta.get('height'))

if __name__ == '__main__':
    for a in sys.argv[1:]:
        n, _, sk = a.partition(':'); run(n, int(sk or 0))
