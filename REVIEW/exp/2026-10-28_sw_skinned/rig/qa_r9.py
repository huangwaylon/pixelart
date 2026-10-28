"""qa_r9.py : round-6 head QA -> rig/qa/r9_QA.png + r9_QA.json : master | before (r8e) | after (r9) for S/SE/E/N/SW rest, walk SE f0/2/4/6, 4x + 1x.
Bangs gate (as I's): skin px (s/S/k) above the brow line (min brow-anchor row, 1x) inside the head; 0 = pass."""
import sys, json, numpy as np
sys.path.insert(0, '/Users/waylonhuang/Documents/other/pixelart/REVIEW/exp/2026-10-28_sw_hires3d/scripts'); import hx
from PIL import Image, ImageDraw
AL = json.load(open('rig/align.json')); OUT = {}
def gate(d, act, v, i):
    g = hx.read_grid(f'{d}/{act}_{v}_rq/f{i:02d}.txt'); info = json.load(open(f'{d}/{act}_{v}.json')); fa = info['frames'][i]['face']
    br = [a['px'][1] for n, a in fa.items() if n.startswith('brow') and a.get('facing', 0) > 0]
    if not br: return g, None
    yb = int(np.floor(min(br))) - 1; return g, int(np.isin(g[:max(yb, 0)], list('sSk')).sum())
def master(v):
    src = {'SW': 'SE'}.get(v, v); m = hx.read_grid(hx.SW + f'v2/m96/masters/EC0_{src}_96.txt')
    if v == 'SW': m = m[:, ::-1]
    L = AL[v]['lift_px']; mm = np.full_like(m, '.'); mm[:128 - L] = m[L:]; return mm
tiles = []
for v in ('S', 'SE', 'SW', 'E', 'N'):
    tiles.append((hx.render(master(v), 4), f'{v} master'))
    for tag, d in (('before r8e', 'rig/qa/r8e' if v in ('S', 'SE', 'E') else None), ('after r9', 'rig/qa/r9')):
        if d is None: tiles.append((Image.new('RGB', (512, 512), (60, 60, 60)), f'{v} {tag}: n/a')); continue
        g, n = gate(d, 'rest', v, 0); OUT[f'{tag}_{v}_skin_above_brow'] = n; tiles.append((hx.render(g, 4), f'{v} {tag} skin>brow {n}'))
for i in (0, 2, 4, 6):
    g, n = gate('rig/qa/r9', 'walk', 'SE', i); OUT.setdefault('walk_SE_skin_above_brow', []).append(n); tiles.append((hx.render(g, 4), f'walk SE f{i} skin>brow {n}'))
cols = 6; rows = (len(tiles) + cols - 1) // cols; W = Image.new('RGB', (280 * cols, 290 * rows + 130), (40, 40, 44)); dr = ImageDraw.Draw(W)
for k, (im, lab) in enumerate(tiles):
    x, y = (k % cols) * 280, (k // cols) * 290; W.paste(im.convert('RGB').crop((116, 60, 396, 330)), (x, y + 14)); dr.text((x + 3, y + 1), lab, fill=(240, 230, 120))
x = 0
for v in ('S', 'SE', 'SW', 'E', 'N'):
    W.paste(hx.render(master(v), 1).crop((14, 12, 114, 122)), (x, 290 * rows + 10)); x += 102
    W.paste(hx.render(hx.read_grid(f'rig/qa/r9/rest_{v}_rq/f00.txt'), 1).crop((14, 12, 114, 122)), (x, 290 * rows + 10)); x += 108
W.save('rig/qa/r9_QA.png'); json.dump(OUT, open('rig/qa/r9_QA.json', 'w'), indent=1); print(OUT)
