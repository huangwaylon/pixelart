"""qa_profile.py : before/after profile balance sheet -> rig/qa/r8d_profile_QA.png + r8d_profile.json
For E/W/NE rest + walk (8 frames): head silhouette horizontal centre (opaque cells above the neck row, 1x) vs the neck-base x (neck bone head,
projected). Marked on the 4x tiles: yellow = silhouette centre, cyan = neck base. offset = centre - neck, signed toward her FRONT (+ = forward)."""
import sys, json, numpy as np
sys.path.insert(0, '/Users/waylonhuang/Documents/other/pixelart/REVIEW/exp/2026-10-28_sw_hires3d/scripts'); import hx
from PIL import Image, ImageDraw
FRONT = {'E': 1, 'W': -1, 'NE': 1}  # screen direction of her front (E: faces screen-right; W: left; NE: front-right side away -> her front is screen-right)
def meas(d, act, v, i):
    info = json.load(open(f'{d}/{act}_{v}.json')); fr = info['frames'][i]; dx, dy = info['out_dxdy']
    g = hx.read_grid(f'{d}/{act}_{v}_rq/f{i:02d}.txt'); nk = fr['pts']['neck']; nx, ny = nk[0] - 32 + dx, nk[1] - 32 + dy
    a = g != '.'; rows = np.arange(128) < ny - 1; cols = np.nonzero((a & rows[:, None]).any(0))[0]
    c = (cols.min() + cols.max() + 1) / 2.0; return g, c, nx, ny, round(float((c - nx) * FRONT[v]), 2)
out = {}; tiles = []
for tag in ('before', 'after'):
    d = f'rig/qa/r8prof_{tag}'
    for v in ('E', 'W', 'NE'):
        for act, frs in (('rest', [0]), ('walk', range(8))):
            for i in frs:
                g, c, nx, ny, off = meas(d, act, v, i); out.setdefault(tag, {}).setdefault(f'{v}', []).append(off)
                if act == 'rest' or i in (0, 3, 5):
                    im = hx.render(g, 4).convert('RGB'); dr = ImageDraw.Draw(im)
                    dr.line((c * 4, 40, c * 4, ny * 4), fill=(255, 230, 0), width=2); dr.line((nx * 4, ny * 4 - 30, nx * 4, ny * 4 + 30), fill=(0, 230, 255), width=3)
                    dr.text((6, 4), f'{tag} {v} {act} f{i}  centre-neck {off:+.1f} px', fill=(255, 255, 0)); tiles.append(im.crop((96, 0, 416, 330)))
summ = {t: {v: {'mean_px': round(float(np.mean(x)), 2), 'min_px': round(float(np.min(x)), 2)} for v, x in d.items()} for t, d in out.items()}
json.dump({'doc': __doc__, 'summary': summ, 'per_frame': out}, open('rig/qa/r8d_profile.json', 'w'), indent=1)
n = len(tiles) // 2; W = Image.new('RGB', (320 * n, 330 * 2), (40, 40, 44))
for k, t in enumerate(tiles): W.paste(t, ((k % n) * 320, (k // n) * 330))
W.save('rig/qa/r8d_profile_QA.png'); print(summ)
