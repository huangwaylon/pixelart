"""qa_r5.py : round-5 head QA sheet -> rig/qa/r5_head_QA.png : row 1 = 8-direction rest at 4x (R QA chain, standard pixelization, no projection);
rows 2-4 = head poses (tilt +-15, nod, turn, bangs/side/back/bun/bow swings at the spring limits, blink) for SE/S/E at 4x; bottom = all at 1x"""
import sys, json
sys.path.insert(0, '/Users/waylonhuang/Documents/other/pixelart/REVIEW/exp/2026-10-28_sw_hires3d/scripts'); import hx
from PIL import Image, ImageDraw
Q = 'rig/qa/'; M = json.load(open(Q + 'r5_head.json')); keys = [f['key'] for f in M['frames']]
def t4(p): return hx.render(hx.read_grid(p), 4).crop((140, 60, 380, 300))
def t1(p): return hx.render(hx.read_grid(p), 2).crop((70, 30, 190, 150))
rows = []; labs = []
r = [t4(f'{Q}r5r8/rest_{v}_rq/f00.txt') for v in ('S', 'SE', 'E', 'NE', 'N', 'NW', 'W', 'SW')]; rows.append(r); labs.append(['rest ' + v for v in ('S', 'SE', 'E', 'NE', 'N', 'NW', 'W', 'SW')])
for v in ('SE', 'S', 'E'):
    rows.append([t4(f'{Q}r5h/r5_head_{v}_rq/f{i:02d}.txt') for i in range(1, len(keys))]); labs.append([f'{v} {k}' for k in keys[1:]])
w, h = 240, 240; cols = max(len(r) for r in rows); W = Image.new('RGB', (w * cols, (h + 14) * len(rows) + 300), (40, 40, 44)); d = ImageDraw.Draw(W)
for j, (r, l) in enumerate(zip(rows, labs)):
    for i, (im, s) in enumerate(zip(r, l)): W.paste(im, (i * w, j * (h + 14) + 14)); d.text((i * w + 3, j * (h + 14) + 1), s, fill=(240, 230, 120))
y0 = len(rows) * (h + 14) + 10; d.text((4, y0), '1x (shown 2x): rest 8 dirs | SE head poses', fill=(255, 255, 255))
x = 0
for v in ('S', 'SE', 'E', 'NE', 'N', 'NW', 'W', 'SW'): W.paste(t1(f'{Q}r5r8/rest_{v}_rq/f00.txt'), (x, y0 + 16)); x += 120
x = 0
for i in range(1, len(keys)): W.paste(t1(f'{Q}r5h/r5_head_SE_rq/f{i:02d}.txt'), (x, y0 + 150)); x += 120
W.save(Q + 'r5_head_QA.png'); print(W.size)
