"""compare_h2.py ACT VIEW : side-by-side GIF  [old rig H2 celo_kc_hs (hires3d)] | [skinned rig celo_kc_hs] | [skinned raw] | [skinned preview]
-> render/out/compare_<act>_<view>.gif + _sheet.png (3x, mid-grey)"""
import sys, os, json, glob
sys.path.insert(0, '/Users/waylonhuang/Documents/other/pixelart/REVIEW/exp/2026-10-28_sw_hires3d/scripts')
import hx
from PIL import Image, ImageDraw
act, view = sys.argv[1], sys.argv[2]; EXP = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); O = f'{EXP}/render/out/{act}'
old = sorted(glob.glob(hx.EXP + f'out/{act}_{view}/celo_kc_hs/f??.txt'))
info = json.load(open(f'{O}/{act}_{view}.json')); n = len(info['frames']); S = 3; BG = (110, 110, 110)
def crop(im): return im.crop((20 * S, 18 * S, 108 * S, 128 * S))
frames = []
for k in range(max(n, len(old))):
    i = info['frames'][k % n]['i']
    cols = [hx.render(hx.read_grid(old[k % len(old)]), S, BG) if old else Image.new('RGB', (128 * S, 128 * S), BG),
            hx.render(hx.read_grid(f'{O}/{act}_{view}_px_hs/f{i:02d}.txt'), S, BG), hx.render(hx.read_grid(f'{O}/{act}_{view}_px/f{i:02d}.txt'), S, BG)]
    pv = Image.open(f'{O}/{act}_{view}_f{i:02d}_pv.png').convert('RGBA'); kk = pv.size[0] // 192
    pv = pv.crop((32 * kk, 32 * kk, 160 * kk, 160 * kk)).resize((128 * S, 128 * S), Image.LANCZOS); bg = Image.new('RGBA', pv.size, BG + (255,)); bg.alpha_composite(pv); cols.append(bg.convert('RGB'))
    cols = [crop(c) for c in cols]; w, h = cols[0].size
    F = Image.new('RGB', (w * 4, h + 16), (40, 40, 44)); d = ImageDraw.Draw(F)
    for j, (c, lab) in enumerate(zip(cols, ['old rig H2 (rigid parts)', 'skinned + head stamp', 'skinned, rig head', 'skinned preview'])):
        F.paste(c, (j * w, 16)); d.text((j * w + 4, 2), lab, fill=(240, 230, 120))
    frames.append(F)
ms = [int(f['ms']) for f in info['frames']]
q = [f.quantize(colors=255, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE) for f in frames]
q[0].save(f'{EXP}/render/out/compare_{act}_{view}.gif', save_all=True, append_images=q[1:], duration=[ms[k % n] for k in range(len(q))], loop=0)
W = Image.new('RGB', (frames[0].size[0], frames[0].size[1] * min(4, len(frames))))
for k in range(min(4, len(frames))): W.paste(frames[k * max(1, len(frames) // 4)], (0, k * frames[0].size[1]))
W.save(f'{EXP}/render/out/compare_{act}_{view}_sheet.png'); print('ok', len(frames), 'old', len(old))
