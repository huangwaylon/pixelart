"""f_preview.py (F) -- smooth preview with the face following the head.
  python f_preview.py <act> <view>
Input: face/out/<act>/pv/<act>_<V>_fNN_pv.png (f_render.py --preview: R's EEVEE preview with the FACELESS projected head), the full-mode
face plan (same pose -> same anchors) and the faceless 8x head pass.  The face parts of the pixel layer are composited as 2x2 blocks at the
projected anchors, with the face offset at half-pixel precision (the continuous 3D anchor offset, rounded to the 2x preview grid), so the
face glides with the head.  Output: face/out/<act>/<act>_<V>_preview_face.gif (+ cmp with R's preview, loop=0, frames >= 20 ms) + sheet.
"""
import os, sys, json
import numpy as np
from PIL import Image, ImageDraw
HERE = os.path.dirname(os.path.abspath(__file__)); EXP = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import face_layer as FLY  # noqa: E402
hx = FLY.hx
RGB = {k: tuple(int(c) for c in hx.RGB[i]) for i, k in enumerate(hx.KEYS)}
BGC = (82, 82, 87)


def main(act, V):
    od = f'{EXP}/face/out/{act}'; pd = f'{od}/pv'
    info = json.load(open(f'{pd}/{act}_{V}.json')); SC = info['scale']
    fj = f'{od}/{act}_{V}_face.json'; d = json.load(open(fj)); DX, DY = d['align']['dx'], d['align']['dy']
    C = FLY.plan_clip(fj, act, act != 'jump')
    r2 = f'{EXP}/render/out/r2/{act}'
    ims, cmp_, durs = [], [], []
    for k, fr in enumerate(d['frames']):
        i = fr['i']; pl = C['plan'][k]
        T, gn = FLY.tex_cells(FLY.load_ftex(f'{od}/{act}_{V}_f{i:02d}_tex.png', DX, DY))
        g1 = FLY.draw(gn, gn, T, V, C['parts'], pl)
        im = Image.open(f'{pd}/{act}_{V}_f{i:02d}_pv.png').convert('RGBA'); a = np.array(im)
        # sub-pixel face offset (continuous anchor offset - integer offset), at the preview resolution
        G0 = (pl['G'][0] - d['tex_off'][0], pl['G'][1] - d['tex_off'][1])
        sx = int(round((pl['g_cont'][0] - G0[0]) * SC)); sy = int(round((pl['g_cont'][1] - G0[1]) * SC))
        ys, xs = np.nonzero((g1 != gn) & (g1 != 's'))
        for y, x in zip(ys, xs):
            X = (x + 32 - DX) * SC + sx; Y = (y + 32 - DY) * SC + sy
            blk = a[Y:Y + SC, X:X + SC]
            if blk.size and (blk[..., 3] > 0).all(): blk[..., :3] = RGB[g1[y, x]]
        # blush/eye clears: preview already faceless
        out = Image.new('RGBA', im.size, BGC + (255,)); out.alpha_composite(Image.fromarray(a))
        ims.append(out.convert('RGB').resize((im.width * 2, im.height * 2), Image.NEAREST))
        rp = f'{r2}/{act}_{V}_f{i:02d}_pv.png'
        c = Image.new('RGB', (im.width * 3, im.height * 2), BGC)
        if os.path.exists(rp):
            o = Image.new('RGBA', im.size, BGC + (255,)); o.alpha_composite(Image.open(rp).convert('RGBA')); c.paste(o.convert('RGB'), (0, im.height // 2))
        c.paste(ims[-1], (im.width, 0)); dr = ImageDraw.Draw(c)
        dr.text((4, 4), 'R preview (projected master face)', fill=(230, 230, 120)); dr.text((im.width + 4, 4), f'F face layer: {pl["expr"]}' + (f'/{pl["blink"]}' if pl['blink'] else ''), fill=(230, 230, 120))
        cmp_.append(c); durs.append(max(20, int(info['frames'][k]['ms'])))
    kw = dict(save_all=True, duration=durs, loop=0, disposal=1)
    ims[0].save(f'{od}/{act}_{V}_preview_face.gif', append_images=ims[1:], **kw)
    cmp_[0].save(f'{od}/cmp_preview_face_{act}_{V}.gif', append_images=cmp_[1:], **kw)
    # head-crop sheet (face close-up at 2x preview res, x2)
    hb = [int((np.mean([f['anchors']['eye.0']['xy'][0] for f in d['frames']]) + 32 - DX) * SC), int((np.mean([f['anchors']['eye.0']['xy'][1] for f in d['frames']]) + 32 - DY) * SC)]
    cw = 46 * SC
    tiles = [im.crop(tuple(2 * v for v in (hb[0] - cw // 2 + 4 * SC, hb[1] - 28 * SC, hb[0] + cw // 2 + 4 * SC, hb[1] + 18 * SC))) for im in ims]
    S = Image.new('RGB', (sum(t.width for t in tiles), tiles[0].height), BGC); x = 0
    for t in tiles: S.paste(t, (x, 0)); x += t.width
    S.save(f'{od}/sheet_preview_face_{act}_{V}.png')
    print('preview', act, V)


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
