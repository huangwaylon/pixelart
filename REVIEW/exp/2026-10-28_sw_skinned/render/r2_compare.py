"""r2_compare.py ACT VIEW : round 1 vs round 2 side-by-side GIF + sheet -> render/out/r2/compare_<act>_<view>.gif / _sheet.png
cols: round 1 (render/out/<act>, r4 rig + rigid m96 head stamp) | round 2 R QA chain (r5 rig, projected master head) |
      round 2 P chain (render/out/p2/<act>, if present) | round 2 smooth preview"""
import sys, os, json, glob
sys.path.insert(0, '/Users/waylonhuang/Documents/other/pixelart/REVIEW/exp/2026-10-28_sw_hires3d/scripts'); import hx
from PIL import Image, ImageDraw
act, view = sys.argv[1], sys.argv[2]; E = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); O = f'{E}/render/out'; S = 3; BG = (110, 110, 110)
info = json.load(open(f'{O}/r2/{act}/{act}_{view}.json')); fr = info['frames']; n = len(fr)
r1 = sorted(glob.glob(f'{O}/{act}/{act}_{view}_px_hs/f??.txt')); p2 = sorted(glob.glob(f'{O}/p2/{act}/{act}_{view}_px/f??.txt'))
def tile(p): return hx.render(hx.read_grid(p), S, BG).crop((16 * S, 14 * S, 108 * S, 128 * S)) if p else Image.new('RGB', (92 * S, 114 * S), BG)
frames = []
for k in range(max(n, len(r1))):
    i = fr[k % n]['i']
    cols = [tile(r1[k % len(r1)] if r1 else None), tile(f'{O}/r2/{act}/{act}_{view}_rq/f{i:02d}.txt'), tile(p2[k % len(p2)] if p2 else None)]
    pv = Image.open(f'{O}/r2/{act}/{act}_{view}_f{i:02d}_pv.png').convert('RGBA'); kk = pv.size[0] // 192
    pv = pv.crop((48 * kk, 46 * kk, 140 * kk, 160 * kk)).resize(cols[0].size, Image.LANCZOS); bg = Image.new('RGBA', pv.size, BG + (255,)); bg.alpha_composite(pv); cols.append(bg.convert('RGB'))
    w, h = cols[0].size; F = Image.new('RGB', (w * 4, h + 16), (40, 40, 44)); d = ImageDraw.Draw(F)
    for j, (c, lab) in enumerate(zip(cols, ['round 1 (stamp head)', 'round 2 rig, R QA chain', 'round 2 P chain' if p2 else '(P chain: n/a)', 'round 2 preview'])):
        F.paste(c, (j * w, 16)); d.text((j * w + 4, 2), f'{lab}  f{i}', fill=(240, 230, 120))
    frames.append(F)
ms = [int(f['ms']) for f in fr]
q = [f.quantize(colors=255, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE) for f in frames]
q[0].save(f'{O}/r2/compare_{act}_{view}.gif', save_all=True, append_images=q[1:], duration=[ms[k % n] for k in range(len(q))], loop=0)
m = min(4, len(frames)); W = Image.new('RGB', (frames[0].width, frames[0].height * m))
for k in range(m): W.paste(frames[k * max(1, len(frames) // m)], (0, k * frames[0].height))
W.save(f'{O}/r2/compare_{act}_{view}_sheet.png'); print('ok', act, view, len(frames))
