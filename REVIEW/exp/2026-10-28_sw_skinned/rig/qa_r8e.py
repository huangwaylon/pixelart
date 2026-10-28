"""qa_r8e.py : round-5 head rebalance QA -> rig/qa/r8e_QA.png + r8e_QA.json
rows: master | before (r8c) | after (r8e) for S/SE/E/W rest at 4x; walk SE/E f0,f2,f4,f6 after at 4x; 1x strips.
Metrics: head-silhouette centre vs neck base (+ = toward her front, px at 1x) and the face-skin dark-band share (S among s/S/k cells above the neck)."""
import sys, json, numpy as np
sys.path.insert(0, '/Users/waylonhuang/Documents/other/pixelart/REVIEW/exp/2026-10-28_sw_hires3d/scripts'); import hx
from PIL import Image, ImageDraw
AL = json.load(open('rig/align.json')); FRONT = {'E': 1, 'W': -1, 'S': 0, 'SE': 1}
def grid(d, act, v, i): return hx.read_grid(f'{d}/{act}_{v}_rq/f{i:02d}.txt'), json.load(open(f'{d}/{act}_{v}.json'))
def metrics(g, info, i):
    fr = info['frames'][i]; dx, dy = info['out_dxdy']; nx, ny = fr['pts']['neck'][0] - 32 + dx, fr['pts']['neck'][1] - 32 + dy
    a = g != '.'; rows = np.arange(128) < ny - 1; cols = np.nonzero((a & rows[:, None]).any(0))[0]; c = (cols.min() + cols.max() + 1) / 2
    hd = g[:int(ny) - 1]; sk = np.isin(hd, list('sSk')); dark = float((hd == 'S').sum() / max(1, sk.sum()))
    return round(float(c - nx), 2), round(dark, 3), c, nx, ny
def tile(g, c=None, nx=None, ny=None, lab=''):
    im = hx.render(g, 4).convert('RGB'); d = ImageDraw.Draw(im)
    if c is not None: d.line((c * 4, 40, c * 4, ny * 4), fill=(255, 230, 0), width=2); d.line((nx * 4, ny * 4 - 30, nx * 4, ny * 4 + 30), fill=(0, 230, 255), width=3)
    d.text((6, 4), lab, fill=(255, 255, 0)); return im.crop((96, 0, 416, 330))
SRC_B = {'S': ('rig/qa/r5c', 'r5_head'), 'SE': ('rig/qa/r5c', 'r5_head'), 'E': ('rig/qa/r8prof_before', 'rest'), 'W': ('rig/qa/r8prof_before', 'rest')}
tiles, M = [], {}
for v in ('S', 'SE', 'E', 'W'):
    src = {'W': 'E'}.get(v, v); m = hx.read_grid(hx.SW + f'v2/m96/masters/EC0_{src}_96.txt')
    if v == 'W': m = m[:, ::-1]
    L = AL[v]['lift_px']; mm = np.full_like(m, '.'); mm[:128 - L] = m[L:]
    hd = mm[:60]; sk = np.isin(hd, list('sSk')); M[f'master_{v}_dark'] = round(float((hd == 'S').sum() / max(1, sk.sum())), 3)
    tiles.append(tile(mm, lab=f'{v} master  dark-skin {M[f"master_{v}_dark"]:.2f}'))
    for tag, (d, act) in (('before', SRC_B[v]), ('after', ('rig/qa/r8e', 'rest'))):
        g, info = grid(d, act, v, 0); off, dark, c, nx, ny = metrics(g, info, 0); M[f'{tag}_{v}'] = {'centre_minus_neck_front_px': round(off * (FRONT[v] or 1), 2), 'face_dark_share': dark}
        tiles.append(tile(g, c, nx, ny, f'{v} {tag}  c-n {off * (FRONT[v] or 1):+.1f}  dark {dark:.2f}'))
for v in ('SE', 'E'):
    for i in (0, 2, 4, 6):
        g, info = grid('rig/qa/r8e', 'walk', v, i); off, dark, c, nx, ny = metrics(g, info, i); M.setdefault(f'walk_{v}', []).append([round(off * FRONT[v], 2), dark])
        tiles.append(tile(g, c, nx, ny, f'walk {v} f{i} c-n {off * FRONT[v]:+.1f} dark {dark:.2f}'))
cols = 6; rows = (len(tiles) + cols - 1) // cols; W = Image.new('RGB', (320 * cols, 330 * rows + 130), (40, 40, 44))
for k, t in enumerate(tiles): W.paste(t, ((k % cols) * 320, (k // cols) * 330))
x = 0
for v in ('S', 'SE', 'E', 'W'):
    g, _ = grid('rig/qa/r8e', 'rest', v, 0); W.paste(hx.render(g, 1).crop((14, 12, 114, 122)), (x, 330 * rows + 10)); x += 105
for i in range(8):
    g, _ = grid('rig/qa/r8e', 'walk', 'E', i); W.paste(hx.render(g, 1).crop((14, 12, 114, 122)), (x, 330 * rows + 10)); x += 105
W.save('rig/qa/r8e_QA.png'); json.dump(M, open('rig/qa/r8e_QA.json', 'w'), indent=1); print(json.dumps(M))
