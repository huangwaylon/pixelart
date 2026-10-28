"""r_qa_chain.py (R QA only; P owns the production pixel_chain.py) = round-1 chain + projected master head (r_tex_head). Was pixel_chain.py STEM.json [--stamp]  (pixtools venv)  -- post stage of render_motion.py
preview: <stem>_fNN_pv.png (192 cell at 2x) -> 128-cell crop at 2x on mid-grey -> <stem>_preview.gif + <stem>_preview_sheet.png
full:    <stem>_fNN_{guide,lum,dep}.png (192 cell at 8x) -> crop the in-game 128 cell (8 hi-res px per sprite px) -> hires3d best chain:
         cel (per-material locked-palette ramps from smoothed lum) + hi-res lines (silhouette band, depth steps, material groups)
         -> E2 k-centroid (k=3, line-aware) -> palette lock constrained to the cell's rig material -> fix (outline_sil, orphans,
         bare-K crumbs, largest component) [-> --stamp: m96 neutral head pasted at the rig head offset]
         -> <stem>_px/fNN.{txt,png,json} (pzlib) + <stem>_4x.gif (mid-grey) + <stem>_sheet.png
Alignment: one integer shift per view from the rest frame (soles -> master bottom row, feet centre -> master feet centre), as hires3d."""
import sys, os, json, numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, '/Users/waylonhuang/Documents/other/pixelart/REVIEW/exp/2026-10-28_sw_hires3d/scripts')
import hx  # noqa: E402
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from r_tex_head import tex_head  # noqa: E402
P, N, OFF = 8, 128, 256
BG = (110, 110, 110)
DTHR = float(os.environ.get('DTHR', '0.025'))
MAST = hx.SW + 'v2/m96/masters/EC0_{}_96.txt'


def gif(ims, durs, path):
    pal = [im.convert('RGB').quantize(colors=255, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE) for im in ims]
    pal[0].save(path, save_all=True, append_images=pal[1:], duration=durs, loop=0, disposal=1)


def sheet(ims, path, labels=None, cols=None):
    cols = cols or len(ims); w, h = ims[0].size; rows = (len(ims) + cols - 1) // cols
    S = Image.new('RGB', (w * cols, (h + 14) * rows), (40, 40, 44)); d = ImageDraw.Draw(S)
    for i, im in enumerate(ims):
        x, y = (i % cols) * w, (i // cols) * (h + 14); S.paste(im.convert('RGB'), (x, y + 14))
        if labels: d.text((x + 3, y + 1), labels[i], fill=(230, 230, 120))
    S.save(path)


def load(stem, i, dx, dy, tag=None):
    st = f'{stem}_f{i:02d}_' if tag is None else f'{stem}_{tag}_'
    out = {}
    for k in (('guide', 'lum', 'dep', 'tex') if tag is None else ('guide',)):
        if not os.path.exists(st + k + '.png'): continue
        a = hx.rd16(st + k + '.png')[OFF:OFF + N * P, OFF:OFF + N * P]
        out[k] = hx.shift(a, dx, dy)
    g = out['guide']; al = g[..., 3] > 0.5
    d = ((g[..., None, :3] * 255 - hx.MC[None, None]) ** 2).sum(-1); mid = d.argmin(-1); mid[~al] = -1
    out['mid'] = mid; out['alpha'] = al
    return out


def feet(a):
    ys = np.where(a.any(1))[0]; yb = ys.max(); xs = np.where(a[yb - 4:yb + 1].any(0))[0]; return yb, (xs.min() + xs.max()) / 2


def align(stem, view):
    F = load(stem, 0, 0, 0, tag='rest'); a = hx.cells(F['alpha'].astype(float)).mean((2, 3)) > 0.5
    m = hx.read_grid(MAST.format(view)) != '.'
    yb, xc = feet(a); mb, mc = feet(m); return {'dx': int(round(mc - xc)), 'dy': int(mb - yb)}


def celo(F):
    img, al = hx.style_cel(F); img = img.copy(); img[hx.edges_hi(F, w=6, dthr=DTHR)] = hx.hexc('K'); return img, al


def head_clear(F, mg, neck_row):
    rows = np.arange(N)[:, None] < neck_row + 1
    return np.isin(mg, [hx.MN.index(k) for k in ('hair', 'skin', 'eyes', 'bow')]) & rows


def main():
    jp = sys.argv[1]; stamp = '--stamp' in sys.argv; info = json.load(open(jp)); stem = jp[:-5]; view = info['view']
    frs = info['frames']; durs = [int(f['ms']) for f in frs]
    if info['preview']:
        ims = []
        for f in frs:
            a = Image.open(f"{stem}_f{f['i']:02d}_pv.png").convert('RGBA'); k = a.size[0] // 192
            a = a.crop((32 * k, 32 * k, 160 * k, 160 * k)); bg = Image.new('RGBA', a.size, BG + (255,)); bg.alpha_composite(a); ims.append(bg.convert('RGB'))
        gif(ims, durs, stem + '_preview.gif'); sheet(ims, stem + '_preview_sheet.png', [f"f{f['i']:02d}" for f in frs], cols=min(8, len(ims)))
        print('preview', stem + '_preview.gif'); return
    AL_ = json.load(open('/Users/waylonhuang/Documents/other/pixelart/REVIEW/exp/2026-10-28_sw_skinned/rig/align.json')); sh = {k: AL_[view][k] for k in ('dx', 'dy')} if view in AL_ else align(stem, view); od = stem + '_rq'; os.makedirs(od, exist_ok=True)
    R = info['rest']['head']
    if stamp: t, x0s, y0s = hx.stamp_of(view)
    ims, grids, ims_h, grids_h = [], [], [], []
    if stamp: os.makedirs(od + '_hs', exist_ok=True)
    for f in frs:
        i = f['i']; F = load(stem, i, sh['dx'], sh['dy']); mg = hx.mat_grid(F)
        img, al = celo(F); lo, a = hx.ds_kc(img, al)
        mgx = np.where(a & (mg < 0), hx.MN.index('dress'), mg)
        g = hx.snap_mat(lo, a, mgx); g = hx.fix(g, F, mg, lines=False); g = hx.main_comp(hx.drop_bare_k(g))
        if 'tex' in F: g = hx.main_comp(hx.Z.clean_orphans(tex_head(F['tex'], g), keep='WK'))
        hx.save(g, f'{od}/f{i:02d}', view); grids.append(g); ims.append(hx.render(g, 4, BG))
        if stamp:
            H = f['pts']['head']; x0 = x0s + int(round(H[0] - R[0])); y0 = y0s + int(round(H[1] - R[1]))
            nk = int(round(f['pts']['neck'][1] - 32 + sh['dy']))
            g2 = g.copy(); g2[head_clear(F, mg, nk)] = '.'; g2 = hx.paste(g2, t, x0, y0); g2 = hx.main_comp(hx.Z.clean_orphans(g2, keep='WK'))
            hx.save(g2, f'{od}_hs/f{i:02d}', view); grids_h.append(g2); ims_h.append(hx.render(g2, 4, BG))
        print('px', i, flush=True)
    res = {'align': sh}
    for tag, I_, G_ in (('', ims, grids), ('_hs', ims_h, grids_h)):
        if not I_: continue
        gif(I_, durs, f'{stem}{tag}_4x.gif'); sheet(I_, f'{stem}{tag}_sheet.png', [f"f{f['i']:02d}" for f in frs], cols=min(8, len(I_)))
        res['band_churn' + tag] = hx.band_churn(G_) if len(G_) > 1 else None
        print('full', f'{stem}{tag}_4x.gif', sh)
    json.dump(res, open(f'{stem}_px.json', 'w'))


if __name__ == '__main__':
    main()
