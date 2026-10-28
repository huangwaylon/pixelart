"""ab_board.py ACT [VIEW] : motion/out/ab_<act>_<view>_old_vs_new.png -- row A = OLD rig H2 walk (hires3d cel_kc_hs grids), row B = NEW
(skinned rig + M motion, motion/prev/px/<act>/<act>_<view>_px_hs grids from final.sh), labelled with frame keys and ms. 3x on mid-grey."""
import sys, os, json, glob
sys.path.insert(0, '/Users/waylonhuang/Documents/other/pixelart/REVIEW/exp/2026-10-28_sw_hires3d/scripts')
import hx
from PIL import Image, ImageDraw
act = sys.argv[1]; view = sys.argv[2] if len(sys.argv) > 2 else 'SE'
EXP = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); S = 3; BG = (110, 110, 110)
old = sorted(glob.glob(hx.EXP + f'out/{act}_{view}/cel_kc_hs/f??.txt'))
new = sorted(glob.glob(f'{EXP}/motion/prev/px/{act}/{act}_{view}_px_hs/f??.txt'))
M = json.load(open(f'{EXP}/motion/{act}.json')); ms = M.get('timing_ms') or [100] * len(new)
def tile(p): return hx.render(hx.read_grid(p), S, BG).crop((20 * S, 18 * S, 104 * S, 126 * S))
n = max(len(old), len(new)); w, h = tile(new[0]).size
W = Image.new('RGB', (w * n, 2 * (h + 30)), (40, 40, 44)); d = ImageDraw.Draw(W)
d.text((4, 2), f'A = OLD {act} (rig H2, rejected: stiff)  frames f0..f{len(old)-1}', fill=(240, 240, 240))
d.text((4, h + 32), f'B = NEW {act} (skinned rig r4 + M motion)  ms {ms}', fill=(240, 240, 240))
for i, p in enumerate(old): W.paste(tile(p), (i * w, 28)); d.text((i * w + 4, 15), f'A f{i}', fill=(255, 255, 0))
for i, p in enumerate(new):
    W.paste(tile(p), (i * w, h + 58)); d.text((i * w + 4, h + 45), f"B f{i} {M['frames'][i].get('key', '')}", fill=(255, 255, 0))
W.save(f'{EXP}/motion/out/ab_{act}_{view}_old_vs_new.png'); print('ab', act, len(old), len(new))
